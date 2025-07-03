"""
任务执行器模块
负责执行不同类型的爬虫任务
"""
import os
import sys
import json
import time
import traceback
from datetime import datetime, timedelta
import pickle

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import log
from db.mysql_manager import MySQLManager
from cookie_manager.cookie_rotator import CookieRotator
from region_manager.region_manager import get_region_manager
from spider.baidu_index_spider import BaiduIndexSpider
from spider.search_index_crawler import search_index_crawler
from config.settings import OUTPUT_DIR

class TaskExecutor:
    """任务执行器，负责执行不同类型的爬虫任务"""
    
    def __init__(self):
        """初始化任务执行器"""
        self.mysql = MySQLManager()
        self.cookie_rotator = CookieRotator()
        self.city_manager = get_region_manager()
        self.running_tasks = {}  # 记录正在运行的任务 {task_id: is_running}
    
    def execute_task(self, task_id, task_type, parameters, checkpoint_path=None):
        """
        执行任务
        :param task_id: 任务ID
        :param task_type: 任务类型
        :param parameters: 任务参数
        :param checkpoint_path: 断点续传数据路径
        :return: 是否成功
        """
        log.info(f"开始执行任务 {task_id}，类型: {task_type}")
        
        # 标记任务为运行中
        self.running_tasks[task_id] = True
        
        try:
            # 解析参数
            if isinstance(parameters, str):
                parameters = json.loads(parameters)
            
            if checkpoint_path and isinstance(checkpoint_path, str):
                checkpoint_path = json.loads(checkpoint_path)
            
            # 根据任务类型执行不同的爬虫任务
            if task_type == 'search_index':
                return self._execute_search_index_task(task_id, parameters, checkpoint_path)
            elif task_type == 'feed_index':
                return self._execute_feed_index_task(task_id, parameters, checkpoint_path)
            elif task_type == 'word_graph':
                return self._execute_word_graph_task(task_id, parameters, checkpoint_path)
            elif task_type == 'demographic_attributes':
                return self._execute_demographic_attributes_task(task_id, parameters, checkpoint_path)
            elif task_type == 'interest_profile':
                return self._execute_interest_profile_task(task_id, parameters, checkpoint_path)
            elif task_type == 'region_distribution':
                return self._execute_region_distribution_task(task_id, parameters, checkpoint_path)
            else:
                log.error(f"未知的任务类型: {task_type}")
                self._update_task_status(task_id, 'failed', error_message=f"未知的任务类型: {task_type}")
                return False
        except Exception as e:
            log.error(f"执行任务 {task_id} 失败: {e}")
            log.error(traceback.format_exc())
            self._update_task_status(task_id, 'failed', error_message=str(e))
            return False
        finally:
            # 移除任务运行标记
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
    
    def stop_task(self, task_id):
        """
        停止任务
        :param task_id: 任务ID
        :return: 是否成功
        """
        if task_id in self.running_tasks:
            self.running_tasks[task_id] = False
            log.info(f"已标记任务 {task_id} 为停止状态")
            return True
        return False
    
    def is_task_running(self, task_id):
        """
        检查任务是否正在运行
        :param task_id: 任务ID
        :return: 是否正在运行
        """
        return task_id in self.running_tasks and self.running_tasks[task_id]
    
    def _update_task_status(self, task_id, status, progress=None, total_items=None, 
                           completed_items=None, failed_items=None, error_message=None, 
                           checkpoint_path=None, output_files=None):
        """
        更新任务状态
        :param task_id: 任务ID
        :param status: 任务状态
        :param progress: 进度百分比
        :param total_items: 总项目数
        :param completed_items: 已完成项目数
        :param failed_items: 失败项目数
        :param error_message: 错误信息
        :param checkpoint_path: 断点续传数据
        :param output_files: 输出文件列表
        :return: 是否成功
        """
        try:
            # 构建更新数据
            update_data = {'status': status, 'update_time': datetime.now()}
            
            if progress is not None:
                update_data['progress'] = progress
            
            if total_items is not None:
                update_data['total_items'] = total_items
            
            if completed_items is not None:
                update_data['completed_items'] = completed_items
            
            if failed_items is not None:
                update_data['failed_items'] = failed_items
            
            if error_message is not None:
                update_data['error_message'] = error_message
            
            if checkpoint_path is not None:
                if isinstance(checkpoint_path, dict):
                    update_data['checkpoint_path'] = json.dumps(checkpoint_path)
                else:
                    update_data['checkpoint_path'] = checkpoint_path
            
            if output_files is not None:
                if isinstance(output_files, list):
                    update_data['output_files'] = json.dumps(output_files)
                else:
                    update_data['output_files'] = output_files
            
            # 如果状态是已完成或失败，设置结束时间
            if status in ['completed', 'failed', 'cancelled']:
                update_data['end_time'] = datetime.now()
            
            # 如果状态是运行中且没有开始时间，设置开始时间
            if status == 'running':
                # 检查任务是否有开始时间
                query = "SELECT start_time FROM spider_tasks WHERE task_id = %s"
                result = self.mysql.fetch_one(query, (task_id,))
                
                if result and result['start_time'] is None:
                    update_data['start_time'] = datetime.now()
            
            # 构建SQL更新语句
            set_clause = ", ".join([f"{key} = %s" for key in update_data.keys()])
            values = list(update_data.values())
            values.append(task_id)
            
            query = f"UPDATE spider_tasks SET {set_clause} WHERE task_id = %s"
            self.mysql.execute_query(query, values)
            
            # 如果任务状态为完成、失败或取消，更新task_queue表中的状态
            if status in ['completed', 'failed', 'cancelled']:
                now = datetime.now()
                queue_status = 'completed' if status == 'completed' else 'failed' if status == 'failed' else 'cancelled'
                queue_query = """
                    UPDATE task_queue 
                    SET status = %s, complete_time = %s 
                    WHERE task_id = %s
                """
                self.mysql.execute_query(queue_query, (queue_status, now, task_id))
                
                # 如果任务完成或失败，更新spider_statistics表
                self._update_spider_statistics(task_id, status)
            
            # 如果任务状态为running，更新task_queue表中的状态为processing
            if status == 'running':
                queue_query = """
                    UPDATE task_queue 
                    SET status = 'processing', start_time = %s 
                    WHERE task_id = %s AND start_time IS NULL
                """
                self.mysql.execute_query(queue_query, (datetime.now(), task_id))
            
            # 记录任务日志
            log_message = f"任务状态更新为: {status}"
            if progress is not None:
                log_message += f", 进度: {progress}%"
            if error_message is not None:
                log_message += f", 错误: {error_message}"
            
            self._log_task(task_id, "INFO", log_message)
            
            return True
        except Exception as e:
            log.error(f"更新任务状态失败: {e}")
            return False
    
    def _log_task(self, task_id, level, message):
        """
        记录任务日志
        :param task_id: 任务ID
        :param level: 日志级别
        :param message: 日志消息
        :return: 是否成功
        """
        try:
            query = """
                INSERT INTO task_logs (task_id, log_level, message, timestamp)
                VALUES (%s, %s, %s, %s)
            """
            self.mysql.execute_query(query, (task_id, level, message, datetime.now()))
            return True
        except Exception as e:
            log.error(f"记录任务日志失败: {e}")
            return False
    
    def _update_task_statistics(self, task_id, task_type, statistics_data):
        """
        更新任务统计数据
        :param task_id: 任务ID
        :param task_type: 任务类型
        :param statistics_data: 统计数据
        :return: 是否成功
        """
        try:
            # 插入或更新统计数据
            for item in statistics_data:
                query = """
                    INSERT INTO task_statistics 
                    (task_id, task_type, keyword, city_code, city_name, data_type, data_date, 
                     item_count, success_count, fail_count, create_time, update_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    item_count = VALUES(item_count),
                    success_count = VALUES(success_count),
                    fail_count = VALUES(fail_count),
                    update_time = VALUES(update_time)
                """
                
                now = datetime.now()
                values = (
                    task_id, task_type, 
                    item.get('keyword', ''),
                    item.get('city_code', ''),
                    item.get('city_name', ''),
                    item.get('data_type', ''),
                    item.get('data_date', ''),
                    item.get('item_count', 0),
                    item.get('success_count', 0),
                    item.get('fail_count', 0),
                    now, now
                )
                
                self.mysql.execute_query(query, values)
            
            # 在完成任务后获取任务执行的统计数据并保存到task_statistics表
            task = self._get_task_summary(task_id)
            if task:
                self._save_task_statistics(task)
            
            return True
        except Exception as e:
            log.error(f"更新任务统计数据失败: {e}")
            log.error(traceback.format_exc())
            return False
            
    def _get_task_summary(self, task_id):
        """
        获取任务摘要信息
        :param task_id: 任务ID
        :return: 任务摘要信息
        """
        try:
            query = """
                SELECT 
                    task_id, task_type, parameters, total_items, completed_items, 
                    failed_items, create_time, start_time, end_time, status
                FROM 
                    spider_tasks 
                WHERE 
                    task_id = %s
            """
            
            task = self.mysql.fetch_one(query, (task_id,))
            
            # 解析parameters
            if task and 'parameters' in task and task['parameters']:
                try:
                    if isinstance(task['parameters'], str):
                        task['parameters'] = json.loads(task['parameters'])
                except:
                    pass
                    
            return task
        except Exception as e:
            log.error(f"获取任务摘要信息失败: {e}")
            return None
            
    def _save_task_statistics(self, task):
        """
        保存任务统计数据到task_statistics表
        :param task: 任务信息
        """
        try:
            task_id = task['task_id']
            task_type = task['task_type']
            parameters = task['parameters']
            
            # 提取任务参数中的关键数据
            if isinstance(parameters, dict):
                keywords = parameters.get('keywords', [])
                if not isinstance(keywords, list):
                    keywords = [keywords]
                
                # 获取城市或地区信息
                cities = parameters.get('cities', {})
                regions = parameters.get('regions', [])
                
                # 如果有日期范围，提取日期信息
                date_range = None
                if 'date_ranges' in parameters and parameters['date_ranges']:
                    date_ranges = parameters['date_ranges']
                    if isinstance(date_ranges, list) and len(date_ranges) > 0:
                        if isinstance(date_ranges[0], list) and len(date_ranges[0]) >= 2:
                            date_range = f"{date_ranges[0][0]} - {date_ranges[0][1]}"
                elif 'start_date' in parameters and 'end_date' in parameters:
                    date_range = f"{parameters['start_date']} - {parameters['end_date']}"
                
                # 为每个关键词创建统计记录
                now = datetime.now()
                for keyword in keywords:
                    # 处理城市/地区统计
                    if task_type in ['search_index', 'feed_index']:
                        # 处理城市字典情况
                        if isinstance(cities, dict):
                            for city_code, city_name in cities.items():
                                self._insert_task_stat(task_id, task_type, keyword, city_code, city_name, date_range, now)
                        # 处理城市列表情况
                        elif isinstance(cities, list):
                            for city in cities:
                                if isinstance(city, dict) and 'code' in city and 'name' in city:
                                    self._insert_task_stat(task_id, task_type, keyword, city['code'], city['name'], date_range, now)
                                else:
                                    self._insert_task_stat(task_id, task_type, keyword, city, f"城市{city}", date_range, now)
                    elif task_type == 'region_distribution':
                        # 处理地区列表情况
                        if isinstance(regions, list):
                            for region in regions:
                                self._insert_task_stat(task_id, task_type, keyword, region, f"地区{region}", date_range, now)
                    else:
                        # 对于其他类型任务，创建一个通用统计记录
                        self._insert_task_stat(task_id, task_type, keyword, None, None, date_range, now)
            
        except Exception as e:
            log.error(f"保存任务统计数据失败: {e}")
            log.error(traceback.format_exc())
            
    def _insert_task_stat(self, task_id, task_type, keyword, city_code=None, city_name=None, date_range=None, now=None):
        """
        插入任务统计记录
        """
        if now is None:
            now = datetime.now()
            
        query = """
            INSERT INTO task_statistics (
                task_id, task_type, keyword, city_code, city_name, date_range, create_time
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            update_time = %s
        """
        
        values = (
            task_id, task_type, keyword, 
            city_code, city_name, date_range, now, now
        )
        
        try:
            self.mysql.execute_query(query, values)
        except Exception as e:
            log.error(f"插入任务统计记录失败: {e}")
            log.error(traceback.format_exc())
    
    def _execute_search_index_task(self, task_id, parameters, checkpoint_path=None):
        """
        执行搜索指数任务
        :param task_id: 任务ID
        :param parameters: 任务参数
        :param checkpoint_path: 断点续传数据路径
        :return: 是否成功
        """
        log.info(f"执行搜索指数任务: {task_id}")
        
        # 验证必要参数
        if 'keywords' not in parameters or not parameters['keywords']:
            self._update_task_status(task_id, 'failed', error_message="缺少必要参数: keywords")
            return False
        
        if 'cities' not in parameters or not parameters['cities']:
            self._update_task_status(task_id, 'failed', error_message="缺少必要参数: cities")
            return False
        
        # 获取参数
        keywords = parameters['keywords']
        cities = parameters['cities']
        resume = parameters.get('resume', False)
        if resume:
            checkpoint_task_id = parameters.get('task_id')
        
        # 处理关键词
        if not isinstance(keywords, list):
            keywords = [keywords]
        
        # 处理城市
        city_dict = {}
        if isinstance(cities, dict):
            for code, city_info in cities.items():
                if isinstance(city_info, dict) and 'name' in city_info and 'code' in city_info:
                    city_dict[city_info['code']] = city_info['name']
                else:
                    city_dict[code] = f"城市{code}"
        elif isinstance(cities, list):
            for city in cities:
                if isinstance(city, dict) and 'name' in city and 'code' in city:
                    city_dict[city['code']] = city['name']
                elif isinstance(city, str):
                    city_dict[city] = f"城市{city}"
        
        if not city_dict:
            self._update_task_status(task_id, 'failed', error_message="无效的城市参数")
            return False
        
        # 处理时间参数
        start_date = None
        end_date = None
        
        if 'days' in parameters:
            # 使用预定义的天数
            days = int(parameters['days'])
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days-1)).strftime('%Y-%m-%d')
        elif 'date_ranges' in parameters and parameters['date_ranges']:
            # 使用自定义日期范围
            date_ranges = parameters['date_ranges']
            if isinstance(date_ranges, list) and len(date_ranges) > 0:
                if isinstance(date_ranges[0], list) and len(date_ranges[0]) >= 2:
                    start_date = date_ranges[0][0]
                    end_date = date_ranges[0][1]
        elif 'year_range' in parameters and parameters['year_range']:
            # 使用年份范围
            year_range = parameters['year_range']
            if isinstance(year_range, list) and len(year_range) >= 2:
                start_date = f"{year_range[0]}-01-01"
                end_date = f"{year_range[1]}-12-31"
        else:
            # 默认使用全部数据范围（2011年至今）
            start_date = "2011-01-01"
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        if not start_date or not end_date:
            self._update_task_status(task_id, 'failed', error_message="无效的时间参数")
            return False
        
        # 获取输出目录和检查点文件路径
        output_dir = os.path.join(OUTPUT_DIR, 'search_index', task_id)
        checkpoint_path = os.path.join(OUTPUT_DIR, f"checkpoints/{task_id}_checkpoint.pkl")
        os.makedirs(output_dir, exist_ok=True)
        
        # 初始化检查点数据
        checkpoint_data = {
            'completed_keywords': [],
            'failed_keywords': [],
            'current_keyword_index': 0,
            'current_city_index': 0
        }
        
        # 如果是恢复任务，尝试从检查点文件加载数据
        if resume and os.path.exists(checkpoint_path):
            try:
                with open(checkpoint_path, 'rb') as f:
                    checkpoint = pickle.load(f)
                    completed_tasks = checkpoint.get('completed_tasks', 0)
                    total_tasks = checkpoint.get('total_tasks', 0)
                    log.info(f"已加载检查点数据: {checkpoint_path}, 已完成任务: {completed_tasks}/{total_tasks}")
                    checkpoint_data.update({
                        'completed_tasks': completed_tasks,
                        'total_tasks': total_tasks
                    })
            except Exception as e:
                log.error(f"加载检查点文件失败: {e}")
        
        # 初始化统计数据
        total_items = len(keywords) * len(city_dict)
        completed_items = len(checkpoint_data.get('completed_keywords', []))
        failed_items = len(checkpoint_data.get('failed_keywords', []))
        
        # 更新任务状态
        self._update_task_status(
            task_id, 'running',
            total_items=total_items,
            completed_items=completed_items,
            failed_items=failed_items,
            progress=round((completed_items + failed_items) / total_items * 100, 2) if total_items > 0 else 0
        )
        
        output_files = []
        
        try:
            # 准备爬虫参数
            spider_params = {
                'task_id': task_id,
                'keywords': keywords,
                'cities': city_dict,
                'date_ranges': [(start_date, end_date)],
                'resume': resume,
                'checkpoint_task_id': checkpoint_task_id if resume else None
            }
            
            # 启动爬虫
            success = search_index_crawler.crawl(**spider_params)
            
            if success:
                # 获取输出文件路径
                daily_path = os.path.join(output_dir, f"{task_id}_daily_data.csv")
                stats_path = os.path.join(output_dir, f"{task_id}_stats_data.csv")
                output_files.append(daily_path)
                output_files.append(stats_path)

                # 更新任务状态为已完成
                self._update_task_status(
                    task_id, 'completed',
                    progress=100,
                    completed_items=total_items,
                    checkpoint_path=checkpoint_path,
                    output_files=output_files
                )
                
                return True
            else:
                # 更新任务状态为失败
                self._update_task_status(
                    task_id, 'failed',
                    error_message="爬虫执行失败",
                    checkpoint_path=checkpoint_path,
                    output_files=output_files
                )
                
                return False
            
        except Exception as e:
            log.error(f"执行搜索指数任务失败: {e}")
            log.error(traceback.format_exc())
            
            # 更新任务状态
            self._update_task_status(
                task_id, 'failed',
                error_message=str(e),
                checkpoint_path=checkpoint_path,
                output_files=output_files
            )
            
            return False
    
    def _execute_feed_index_task(self, task_id, parameters, checkpoint_path=None):
        """
        执行资讯指数任务
        :param task_id: 任务ID
        :param parameters: 任务参数
        :param checkpoint_path: 断点续传数据
        :return: 是否成功
        """
        log.info(f"执行资讯指数任务: {task_id}")
        
        # 验证必要参数
        if 'keywords' not in parameters or not parameters['keywords']:
            self._update_task_status(task_id, 'failed', error_message="缺少必要参数: keywords")
            return False
        
        if 'cities' not in parameters or not parameters['cities']:
            self._update_task_status(task_id, 'failed', error_message="缺少必要参数: cities")
            return False
        
        # 获取参数
        keywords = parameters['keywords']
        cities = parameters['cities']
        resume = parameters.get('resume', False)
        if resume:
            checkpoint_task_id = parameters.get('task_id')
        
        # 处理关键词
        if not isinstance(keywords, list):
            keywords = [keywords]
        
        # 处理城市
        city_dict = {}
        if isinstance(cities, dict):
            for code, city_info in cities.items():
                if isinstance(city_info, dict) and 'name' in city_info and 'code' in city_info:
                    city_dict[city_info['code']] = city_info['name']
                else:
                    city_dict[code] = f"城市{code}"
        elif isinstance(cities, list):
            for city in cities:
                if isinstance(city, dict) and 'name' in city and 'code' in city:
                    city_dict[city['code']] = city['name']
                elif isinstance(city, str):
                    city_dict[city] = f"城市{city}"
        
        if not city_dict:
            self._update_task_status(task_id, 'failed', error_message="无效的城市参数")
            return False
        
        # 处理时间参数
        start_date = None
        end_date = None
        days = None
        date_ranges = None
        year_range = None
        
        if 'days' in parameters:
            # 使用预定义的天数
            days = int(parameters['days'])
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days-1)).strftime('%Y-%m-%d')
        elif 'date_ranges' in parameters and parameters['date_ranges']:
            # 使用自定义日期范围
            date_ranges = parameters['date_ranges']
            if isinstance(date_ranges, list) and len(date_ranges) > 0:
                if isinstance(date_ranges[0], list) and len(date_ranges[0]) >= 2:
                    start_date = date_ranges[0][0]
                    end_date = date_ranges[0][1]
        elif 'year_range' in parameters and parameters['year_range']:
            # 使用年份范围
            year_range = parameters['year_range']
            if isinstance(year_range, list) and len(year_range) >= 2:
                start_date = f"{year_range[0]}-01-01"
                end_date = f"{year_range[1]}-12-31"
                # 保存年份范围用于爬虫参数
                year_range = (int(year_range[0]), int(year_range[1]))
        else:
            # 默认使用全部数据范围（2011年至今）
            start_date = "2011-01-01"
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        if not start_date or not end_date:
            self._update_task_status(task_id, 'failed', error_message="无效的时间参数")
            return False
        
        # 获取输出目录和检查点文件路径
        output_dir = os.path.join(OUTPUT_DIR, 'feed_index', task_id)
        checkpoint_path = os.path.join(OUTPUT_DIR, f"checkpoints/feed_index_{task_id}_checkpoint.pkl")
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
        
        # 初始化统计数据
        total_items = len(keywords) * len(city_dict)
        completed_items = 0
        failed_items = 0
        
        # 更新任务状态
        self._update_task_status(
            task_id, 'running',
            total_items=total_items,
            completed_items=completed_items,
            failed_items=failed_items,
            progress=0
        )
        
        output_files = []
        
        try:
            # 准备爬虫参数
            spider_params = {
                'task_id': task_id,
                'keywords': keywords,
                'cities': city_dict,
                'resume': resume,
                'checkpoint_task_id': checkpoint_task_id if resume else None
            }
            
            # 根据不同的时间参数类型添加相应的参数
            if days:
                spider_params['days'] = days
            elif date_ranges:
                spider_params['date_ranges'] = date_ranges
            elif year_range:
                spider_params['year_range'] = year_range
            else:
                spider_params['date_ranges'] = [(start_date, end_date)]
            
            # 启动爬虫
            from spider.feed_index_crawler import feed_index_crawler
            success = feed_index_crawler.crawl(**spider_params)
            
            if success:
                # 获取输出文件路径
                daily_path = os.path.join(output_dir, f"{task_id}_daily_data.csv")
                stats_path = os.path.join(output_dir, f"{task_id}_stats_data.csv")
                output_files.append(daily_path)
                output_files.append(stats_path)

                # 更新任务状态为已完成
                self._update_task_status(
                    task_id, 'completed',
                    progress=100,
                    completed_items=total_items,
                    checkpoint_path=checkpoint_path,
                    output_files=output_files
                )
                
                return True
            else:
                # 更新任务状态为失败
                self._update_task_status(
                    task_id, 'failed',
                    error_message="爬虫执行失败",
                    checkpoint_path=checkpoint_path,
                    output_files=output_files
                )
                
                return False
            
        except Exception as e:
            log.error(f"执行资讯指数任务失败: {e}")
            log.error(traceback.format_exc())
            
            # 更新任务状态
            self._update_task_status(
                task_id, 'failed',
                error_message=str(e),
                checkpoint_path=checkpoint_path,
                output_files=output_files
            )
            
            return False
    
    def _execute_word_graph_task(self, task_id, parameters, checkpoint_path=None):
        """
        执行需求图谱任务
        :param task_id: 任务ID
        :param parameters: 任务参数
        :param checkpoint_path: 断点续传数据
        :return: 是否成功
        """
        log.info(f"执行需求图谱任务: {task_id}")
        
        # 验证必要参数
        if 'keywords' not in parameters or not parameters['keywords']:
            self._update_task_status(task_id, 'failed', error_message="缺少必要参数: keywords")
            return False
        
        if 'datelists' not in parameters or not parameters['datelists']:
            self._update_task_status(task_id, 'failed', error_message="缺少必要参数: datelists")
            return False
        
        # 获取参数
        keywords = parameters['keywords']
        datelists = parameters['datelists']
        output_format = parameters.get('output_format', 'csv')
        resume = parameters.get('resume', False)
        if resume:
            checkpoint_task_id = parameters.get('task_id')
        
        # 处理关键词
        if not isinstance(keywords, list):
            keywords = [keywords]
        
        # 处理日期列表
        if not isinstance(datelists, list):
            datelists = [datelists]
        
        # 获取输出目录和检查点文件路径
        output_dir = os.path.join(OUTPUT_DIR, 'word_graph', task_id)
        checkpoint_path = os.path.join(OUTPUT_DIR, f"checkpoints/word_graph_{task_id}_checkpoint.pkl")
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
        
        # 初始化统计数据
        total_items = len(keywords) * len(datelists)
        completed_items = 0
        failed_items = 0
        
        # 更新任务状态
        self._update_task_status(
            task_id, 'running',
            total_items=total_items,
            completed_items=completed_items,
            failed_items=failed_items,
            progress=0
        )
        
        output_files = []
        
        try:
            # 准备爬虫参数
            spider_params = {
                'task_id': task_id,
                'keywords': keywords,
                'datelists': datelists,
                'output_format': output_format,
                'resume': resume,
                'checkpoint_task_id': checkpoint_task_id if resume else None
            }
            
            # 启动爬虫
            from spider.word_graph_crawler import word_graph_crawler
            success = word_graph_crawler.crawl(**spider_params)
            
            if success:
                # 获取输出文件路径
                output_file = os.path.join(output_dir, f"word_graph_{task_id}.{output_format}")
                output_files.append(output_file)
                
                # 更新任务状态为已完成
                self._update_task_status(
                    task_id, 'completed',
                    progress=100,
                    completed_items=total_items,
                    checkpoint_path=checkpoint_path,
                    output_files=output_files
                )
                
                return True
            else:
                # 更新任务状态为失败
                self._update_task_status(
                    task_id, 'failed',
                    error_message="爬虫执行失败",
                    checkpoint_path=checkpoint_path,
                    output_files=output_files
                )
                
                return False
            
        except Exception as e:
            log.error(f"执行需求图谱任务失败: {e}")
            log.error(traceback.format_exc())
            
            # 更新任务状态
            self._update_task_status(
                task_id, 'failed',
                error_message=str(e),
                checkpoint_path=checkpoint_path,
                output_files=output_files
            )
            
            return False
    
    def _execute_demographic_attributes_task(self, task_id, parameters, checkpoint_path=None):
        """
        执行人群属性任务
        :param task_id: 任务ID
        :param parameters: 任务参数
        :param checkpoint_path: 断点续传数据
        :return: 是否成功
        """
        log.info(f"执行人群属性任务: {task_id}")
        
        # 验证必要参数
        if 'keywords' not in parameters or not parameters['keywords']:
            self._update_task_status(task_id, 'failed', error_message="缺少必要参数: keywords")
            return False
        
        # 获取参数
        keywords = parameters['keywords']
        output_format = parameters.get('output_format', 'csv')
        batch_size = parameters.get('batch_size', 10)
        resume = parameters.get('resume', False)
        if resume:
            checkpoint_task_id = parameters.get('task_id')
        
        # 处理关键词
        if not isinstance(keywords, list):
            keywords = [keywords]
        
        # 获取输出目录和检查点文件路径
        output_dir = os.path.join(OUTPUT_DIR, 'demographic_attributes', task_id)
        checkpoint_path = os.path.join(OUTPUT_DIR, f"checkpoints/demographic_attributes_{task_id}_checkpoint.pkl")
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
        
        # 初始化统计数据
        total_items = len(keywords)
        completed_items = 0
        failed_items = 0
        
        # 更新任务状态
        self._update_task_status(
            task_id, 'running',
            total_items=total_items,
            completed_items=completed_items,
            failed_items=failed_items,
            progress=0
        )
        
        output_files = []
        
        try:
            # 准备爬虫参数
            spider_params = {
                'task_id': task_id,
                'keywords': keywords,
                'output_format': output_format,
                'batch_size': batch_size,
                'resume': resume,
                'checkpoint_task_id': checkpoint_task_id if resume else None
            }
            
            # 启动爬虫
            from spider.demographic_attributes_crawler import demographic_attributes_crawler
            success = demographic_attributes_crawler.crawl(**spider_params)
            
            if success:
                # 获取输出文件路径
                output_file = os.path.join(output_dir, f"demographic_attributes_{task_id}.{output_format}")
                output_files.append(output_file)
                
                # 更新任务状态为已完成
                self._update_task_status(
                    task_id, 'completed',
                    progress=100,
                    completed_items=total_items,
                    checkpoint_path=checkpoint_path,
                    output_files=output_files
                )
                
                return True
            else:
                # 更新任务状态为失败
                self._update_task_status(
                    task_id, 'failed',
                    error_message="爬虫执行失败",
                    checkpoint_path=checkpoint_path,
                    output_files=output_files
                )
                
                return False
            
        except Exception as e:
            log.error(f"执行人群属性任务失败: {e}")
            log.error(traceback.format_exc())
            
            # 更新任务状态
            self._update_task_status(
                task_id, 'failed',
                error_message=str(e),
                checkpoint_path=checkpoint_path,
                output_files=output_files
            )
            
            return False
    
    def _execute_interest_profile_task(self, task_id, parameters, checkpoint_path=None):
        """
        执行兴趣分布任务
        :param task_id: 任务ID
        :param parameters: 任务参数
        :param checkpoint_path: 断点续传数据
        :return: 是否成功
        """
        log.info(f"执行兴趣分布任务: {task_id}")
        
        # 验证必要参数
        if 'keywords' not in parameters or not parameters['keywords']:
            self._update_task_status(task_id, 'failed', error_message="缺少必要参数: keywords")
            return False
        
        # 获取参数
        keywords = parameters['keywords']
        output_format = parameters.get('output_format', 'csv')
        batch_size = parameters.get('batch_size', 10)
        resume = parameters.get('resume', False)
        if resume:
            checkpoint_task_id = parameters.get('task_id')
        
        # 处理关键词
        if not isinstance(keywords, list):
            keywords = [keywords]
        
        # 获取输出目录和检查点文件路径
        output_dir = os.path.join(OUTPUT_DIR, 'interest_profiles', task_id)
        checkpoint_path = os.path.join(OUTPUT_DIR, f"checkpoints/interest_profiles_{task_id}_checkpoint.pkl")
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
        
        # 初始化统计数据
        total_items = len(keywords)
        completed_items = 0
        failed_items = 0
        
        # 更新任务状态
        self._update_task_status(
            task_id, 'running',
            total_items=total_items,
            completed_items=completed_items,
            failed_items=failed_items,
            progress=0
        )
        
        output_files = []
        
        try:
            # 准备爬虫参数
            spider_params = {
                'task_id': task_id,
                'keywords': keywords,
                'output_format': output_format,
                'batch_size': batch_size,
                'resume': resume,
                'checkpoint_task_id': checkpoint_task_id if resume else None
            }
            
            # 启动爬虫
            from spider.interest_profile_crawler import interest_profile_crawler
            success = interest_profile_crawler.crawl(**spider_params)
            
            if success:
                # 获取输出文件路径
                output_file = os.path.join(output_dir, f"interest_profiles_{task_id}.{output_format}")
                output_files.append(output_file)
                
                # 更新任务状态为已完成
                self._update_task_status(
                    task_id, 'completed',
                    progress=100,
                    completed_items=total_items,
                    checkpoint_path=checkpoint_path,
                    output_files=output_files
                )
                
                return True
            else:
                # 更新任务状态为失败
                self._update_task_status(
                    task_id, 'failed',
                    error_message="爬虫执行失败",
                    checkpoint_path=checkpoint_path,
                    output_files=output_files
                )
                
                return False
            
        except Exception as e:
            log.error(f"执行兴趣分布任务失败: {e}")
            log.error(traceback.format_exc())
            
            # 更新任务状态
            self._update_task_status(
                task_id, 'failed',
                error_message=str(e),
                checkpoint_path=checkpoint_path,
                output_files=output_files
            )
            
            return False
    
    def _execute_region_distribution_task(self, task_id, parameters, checkpoint_path=None):
        """
        执行地域分布任务
        :param task_id: 任务ID
        :param parameters: 任务参数
        :param checkpoint_path: 断点续传数据
        :return: 是否成功
        """
        log.info(f"执行地域分布任务: {task_id}")
        
        # 验证必要参数
        if 'keywords' not in parameters or not parameters['keywords']:
            self._update_task_status(task_id, 'failed', error_message="缺少必要参数: keywords")
            return False
        
        if 'regions' not in parameters or not parameters['regions']:
            self._update_task_status(task_id, 'failed', error_message="缺少必要参数: regions")
            return False
        
        # 获取参数
        keywords = parameters['keywords']
        regions = parameters['regions']
        output_format = parameters.get('output_format', 'csv')
        resume = parameters.get('resume', False)
        if resume:
            checkpoint_task_id = parameters.get('task_id')
        region_level = parameters.get('region_level', 'province')
        
        # 处理关键词
        if not isinstance(keywords, list):
            keywords = [keywords]
        
        # 处理地区
        if not isinstance(regions, list):
            regions = [regions]
        
        # 转换地区代码为整数
        try:
            regions = [int(region) for region in regions]
        except ValueError:
            self._update_task_status(task_id, 'failed', error_message="无效的地区代码")
            return False
        
        # 处理时间参数
        start_date = None
        end_date = None
        days = None
        
        if 'days' in parameters:
            # 使用预定义的天数
            days = int(parameters['days'])
        elif 'date_ranges' in parameters and parameters['date_ranges']:
            # 使用自定义日期范围
            date_ranges = parameters['date_ranges']
            if isinstance(date_ranges, list) and len(date_ranges) > 0:
                if isinstance(date_ranges[0], list) and len(date_ranges[0]) >= 2:
                    start_date = date_ranges[0][0]
                    end_date = date_ranges[0][1]
        elif 'year_range' in parameters and parameters['year_range']:
            # 使用年份范围
            year_range = parameters['year_range']
            if isinstance(year_range, list) and len(year_range) >= 2:
                start_date = f"{year_range[0]}-01-01"
                end_date = f"{year_range[1]}-12-31"
        elif 'start_date' in parameters and 'end_date' in parameters:
            # 使用明确的开始和结束日期
            start_date = parameters['start_date']
            end_date = parameters['end_date']
        
        # 获取输出目录和检查点文件路径
        output_dir = os.path.join(OUTPUT_DIR, 'region_distributions', task_id)
        checkpoint_path = os.path.join(OUTPUT_DIR, f"checkpoints/region_distributions_{task_id}_checkpoint.pkl")
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.dirname(checkpoint_path), exist_ok=True)
        
        # 初始化统计数据
        total_items = len(keywords) * len(regions)
        completed_items = 0
        failed_items = 0
        
        # 更新任务状态
        self._update_task_status(
            task_id, 'running',
            total_items=total_items,
            completed_items=completed_items,
            failed_items=failed_items,
            progress=0
        )
        
        output_files = []
        
        try:
            # 准备爬虫参数
            spider_params = {
                'task_id': task_id,
                'keywords': keywords,
                'regions': regions,
                'output_format': output_format,
                'resume': resume,
                'checkpoint_task_id': checkpoint_task_id if resume else None
            }
            
            # 添加时间相关参数
            if days:
                spider_params['days'] = days
            elif start_date and end_date:
                spider_params['start_date'] = start_date
                spider_params['end_date'] = end_date
            
            # 启动爬虫
            from spider.region_distribution_crawler import region_distribution_crawler
            success = region_distribution_crawler.crawl(**spider_params)
            
            if success:
                # 获取输出文件路径
                output_file = os.path.join(output_dir, f"region_distributions_{task_id}.{output_format}")
                output_files.append(output_file)
                
                # 更新任务状态为已完成
                self._update_task_status(
                    task_id, 'completed',
                    progress=100,
                    completed_items=total_items,
                    checkpoint_path=checkpoint_path,
                    output_files=output_files
                )
                
                return True
            else:
                # 更新任务状态为失败
                self._update_task_status(
                    task_id, 'failed',
                    error_message="爬虫执行失败",
                    checkpoint_path=checkpoint_path,
                    output_files=output_files
                )
                
                return False
            
        except Exception as e:
            log.error(f"执行地域分布任务失败: {e}")
            log.error(traceback.format_exc())
            
            # 更新任务状态
            self._update_task_status(
                task_id, 'failed',
                error_message=str(e),
                checkpoint_path=checkpoint_path,
                output_files=output_files
            )
            
            return False
    
    def _update_spider_statistics(self, task_id, status):
        """
        更新爬虫统计数据
        :param task_id: 任务ID
        :param status: 任务状态
        """
        try:
            # 获取任务信息
            task_query = """
                SELECT task_type, create_time, start_time, end_time, total_items, 
                       completed_items, failed_items 
                FROM spider_tasks 
                WHERE task_id = %s
            """
            task = self.mysql.fetch_one(task_query, (task_id,))
            
            if not task:
                log.warning(f"更新统计数据失败：任务 {task_id} 不存在")
                return
            
            task_type = task['task_type']
            stat_date = datetime.now().date()
            
            # 计算任务执行时间（秒）
            duration = 0
            if task['start_time'] and task['end_time']:
                duration = (task['end_time'] - task['start_time']).total_seconds()
            
            # 获取本次任务实际爬取的数据条数
            crawled_items = task['completed_items'] or 0
            
            # 检查今天的统计数据是否存在
            check_query = "SELECT id, total_crawled_items FROM spider_statistics WHERE stat_date = %s AND task_type = %s"
            stats = self.mysql.fetch_one(check_query, (stat_date, task_type))
            
            if stats:
                # 当前累计爬取数据条数
                current_total_crawled = stats.get('total_crawled_items', 0) or 0
                # 更新后的累计爬取数据条数
                new_total_crawled = current_total_crawled + crawled_items
                
                # 更新已有的统计数据
                update_query = """
                    UPDATE spider_statistics 
                    SET total_tasks = total_tasks + 1,
                        completed_tasks = completed_tasks + %s,
                        failed_tasks = failed_tasks + %s,
                        total_items = total_items + %s,
                        total_crawled_items = %s,
                        success_rate = (completed_tasks + %s) / (total_tasks + 1) * 100,
                        avg_duration = ((avg_duration * total_tasks) + %s) / (total_tasks + 1)
                    WHERE stat_date = %s AND task_type = %s
                """
                is_completed = 1 if status == 'completed' else 0
                is_failed = 1 if status == 'failed' else 0
                total_items = task['total_items'] or 0
                
                self.mysql.execute_query(
                    update_query, 
                    (is_completed, is_failed, total_items, new_total_crawled, is_completed, duration, stat_date, task_type)
                )
                
                log.info(f"更新累计爬取数据条数: {current_total_crawled} -> {new_total_crawled}")
            else:
                # 创建新的统计数据
                insert_query = """
                    INSERT INTO spider_statistics (
                        stat_date, task_type, total_tasks, completed_tasks, 
                        failed_tasks, total_items, total_crawled_items, success_rate, avg_duration
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                is_completed = 1 if status == 'completed' else 0
                is_failed = 1 if status == 'failed' else 0
                total_items = task['total_items'] or 0
                success_rate = 100.0 if status == 'completed' else 0.0
                
                self.mysql.execute_query(
                    insert_query, 
                    (stat_date, task_type, 1, is_completed, is_failed, total_items, crawled_items, success_rate, duration)
                )
                
                log.info(f"创建新统计记录，初始爬取数据条数: {crawled_items}")
                
            log.info(f"已更新任务 {task_id} 的统计数据")
            
        except Exception as e:
            log.error(f"更新统计数据失败: {e}")
            log.error(traceback.format_exc())


# 创建任务执行器实例
task_executor = TaskExecutor() 