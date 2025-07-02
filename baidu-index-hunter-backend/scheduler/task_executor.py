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

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import log
from db.mysql_manager import MySQLManager
from cookie_manager.cookie_rotator import CookieRotator
from region_manager.region_manager import get_region_manager
from spider.baidu_index_spider import BaiduIndexSpider
from spider.search_index_crawler import search_index_crawler


class TaskExecutor:
    """任务执行器，负责执行不同类型的爬虫任务"""
    
    def __init__(self):
        """初始化任务执行器"""
        self.mysql = MySQLManager()
        self.cookie_rotator = CookieRotator()
        self.city_manager = get_region_manager()
        self.running_tasks = {}  # 记录正在运行的任务 {task_id: is_running}
    
    def execute_task(self, task_id, task_type, parameters, checkpoint_data=None):
        """
        执行任务
        :param task_id: 任务ID
        :param task_type: 任务类型
        :param parameters: 任务参数
        :param checkpoint_data: 断点续传数据
        :return: 是否成功
        """
        log.info(f"开始执行任务 {task_id}，类型: {task_type}")
        
        # 标记任务为运行中
        self.running_tasks[task_id] = True
        
        try:
            # 解析参数
            if isinstance(parameters, str):
                parameters = json.loads(parameters)
            
            if checkpoint_data and isinstance(checkpoint_data, str):
                checkpoint_data = json.loads(checkpoint_data)
            
            # 根据任务类型执行不同的爬虫任务
            if task_type == 'search_index':
                return self._execute_search_index_task(task_id, parameters, checkpoint_data)
            elif task_type == 'feed_index':
                return self._execute_feed_index_task(task_id, parameters, checkpoint_data)
            elif task_type == 'word_graph':
                return self._execute_word_graph_task(task_id, parameters, checkpoint_data)
            elif task_type == 'demographic_attributes':
                return self._execute_demographic_attributes_task(task_id, parameters, checkpoint_data)
            elif task_type == 'interest_profile':
                return self._execute_interest_profile_task(task_id, parameters, checkpoint_data)
            elif task_type == 'region_distribution':
                return self._execute_region_distribution_task(task_id, parameters, checkpoint_data)
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
                           checkpoint_data=None, output_files=None):
        """
        更新任务状态
        :param task_id: 任务ID
        :param status: 任务状态
        :param progress: 进度百分比
        :param total_items: 总项目数
        :param completed_items: 已完成项目数
        :param failed_items: 失败项目数
        :param error_message: 错误信息
        :param checkpoint_data: 断点续传数据
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
            
            if checkpoint_data is not None:
                if isinstance(checkpoint_data, dict):
                    update_data['checkpoint_data'] = json.dumps(checkpoint_data)
                else:
                    update_data['checkpoint_data'] = checkpoint_data
            
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
            
            return True
        except Exception as e:
            log.error(f"更新任务统计数据失败: {e}")
            return False
    
    def _execute_search_index_task(self, task_id, parameters, checkpoint_data=None):
        """
        执行搜索指数任务
        :param task_id: 任务ID
        :param parameters: 任务参数
        :param checkpoint_data: 断点续传数据
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
        
        # 初始化断点续传数据
        if not checkpoint_data:
            checkpoint_data = {
                'current_keyword_index': 0,
                'current_city_index': 0,
                'completed_keywords': [],
                'failed_keywords': []
            }
        
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
        
        # 获取输出目录
        output_dir = os.path.join('output', 'search_index', task_id)
        os.makedirs(output_dir, exist_ok=True)
        
        output_files = []
        
        # 从断点继续执行
        current_keyword_index = checkpoint_data.get('current_keyword_index', 0)
        current_city_index = checkpoint_data.get('current_city_index', 0)
        
        try:
            # 准备爬虫参数
            spider_params = {
                'keywords': keywords,
                'cities': city_dict,
                'date_ranges': [(start_date, end_date)],
                'resume': resume,
                'task_id': task_id if resume else None
            }
            
            # 启动爬虫
            success = search_index_crawler.crawl(**spider_params)
            
            if success:
                # 获取输出文件
                for file in os.listdir(output_dir):
                    if file.endswith('.csv'):
                        output_files.append(os.path.join(output_dir, file))
                
                # 更新任务状态为已完成
                self._update_task_status(
                    task_id, 'completed',
                    progress=100,
                    completed_items=total_items,
                    output_files=output_files
                )
                
                return True
            else:
                # 更新任务状态为失败
                self._update_task_status(
                    task_id, 'failed',
                    error_message="爬虫执行失败",
                    checkpoint_data=checkpoint_data,
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
                checkpoint_data=checkpoint_data,
                output_files=output_files
            )
            
            return False
    
    def _execute_feed_index_task(self, task_id, parameters, checkpoint_data=None):
        """
        执行资讯指数任务
        :param task_id: 任务ID
        :param parameters: 任务参数
        :param checkpoint_data: 断点续传数据
        :return: 是否成功
        """
        log.info(f"执行资讯指数任务: {task_id}")
        self._update_task_status(task_id, 'running', progress=0)
        
        # TODO: 实现资讯指数爬取逻辑
        # 这里只是一个示例，实际实现需要根据百度指数的API和页面结构来完成
        
        time.sleep(2)  # 模拟任务执行
        self._update_task_status(task_id, 'completed', progress=100)
        return True
    
    def _execute_word_graph_task(self, task_id, parameters, checkpoint_data=None):
        """
        执行需求图谱任务
        :param task_id: 任务ID
        :param parameters: 任务参数
        :param checkpoint_data: 断点续传数据
        :return: 是否成功
        """
        log.info(f"执行需求图谱任务: {task_id}")
        self._update_task_status(task_id, 'running', progress=0)
        
        # TODO: 实现需求图谱爬取逻辑
        
        time.sleep(2)  # 模拟任务执行
        self._update_task_status(task_id, 'completed', progress=100)
        return True
    
    def _execute_demographic_attributes_task(self, task_id, parameters, checkpoint_data=None):
        """
        执行人群属性任务
        :param task_id: 任务ID
        :param parameters: 任务参数
        :param checkpoint_data: 断点续传数据
        :return: 是否成功
        """
        log.info(f"执行人群属性任务: {task_id}")
        self._update_task_status(task_id, 'running', progress=0)
        
        # TODO: 实现人群属性爬取逻辑
        
        time.sleep(2)  # 模拟任务执行
        self._update_task_status(task_id, 'completed', progress=100)
        return True
    
    def _execute_interest_profile_task(self, task_id, parameters, checkpoint_data=None):
        """
        执行兴趣分布任务
        :param task_id: 任务ID
        :param parameters: 任务参数
        :param checkpoint_data: 断点续传数据
        :return: 是否成功
        """
        log.info(f"执行兴趣分布任务: {task_id}")
        self._update_task_status(task_id, 'running', progress=0)
        
        # TODO: 实现兴趣分布爬取逻辑
        
        time.sleep(2)  # 模拟任务执行
        self._update_task_status(task_id, 'completed', progress=100)
        return True
    
    def _execute_region_distribution_task(self, task_id, parameters, checkpoint_data=None):
        """
        执行地域分布任务
        :param task_id: 任务ID
        :param parameters: 任务参数
        :param checkpoint_data: 断点续传数据
        :return: 是否成功
        """
        log.info(f"执行地域分布任务: {task_id}")
        self._update_task_status(task_id, 'running', progress=0)
        
        # TODO: 实现地域分布爬取逻辑
        
        time.sleep(2)  # 模拟任务执行
        self._update_task_status(task_id, 'completed', progress=100)
        return True


# 创建任务执行器实例
task_executor = TaskExecutor() 