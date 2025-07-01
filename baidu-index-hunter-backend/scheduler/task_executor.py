"""
任务执行器模块
负责执行不同类型的爬虫任务
"""
import os
import sys
import json
import time
import traceback
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import log
from db.mysql_manager import MySQLManager
from cookie_manager.cookie_rotator import CookieRotator
from region_manager.region_manager import get_region_manager
from spider.baidu_index_spider import BaiduIndexSpider


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
                INSERT INTO task_logs (task_id, log_level, log_message, create_time)
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
        
        if 'start_date' not in parameters or not parameters['start_date']:
            self._update_task_status(task_id, 'failed', error_message="缺少必要参数: start_date")
            return False
        
        if 'end_date' not in parameters or not parameters['end_date']:
            self._update_task_status(task_id, 'failed', error_message="缺少必要参数: end_date")
            return False
        
        # 获取参数
        keywords = parameters['keywords']
        if isinstance(keywords, str):
            keywords = [keyword.strip() for keyword in keywords.split(',')]
        
        start_date = parameters['start_date']
        end_date = parameters['end_date']
        area_codes = parameters.get('area_codes', [])
        
        if isinstance(area_codes, str):
            area_codes = [code.strip() for code in area_codes.split(',')]
        
        # 如果没有指定地区，则默认为全国
        if not area_codes:
            area_codes = ['0']
        
        # 初始化断点续传数据
        if not checkpoint_data:
            checkpoint_data = {
                'current_keyword_index': 0,
                'current_area_index': 0,
                'completed_keywords': [],
                'failed_keywords': []
            }
        
        # 初始化统计数据
        total_items = len(keywords) * len(area_codes)
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
        
        # 初始化爬虫
        spider = BaiduIndexSpider()
        
        # 获取输出目录
        output_dir = os.path.join('output', 'search_index', task_id)
        os.makedirs(output_dir, exist_ok=True)
        
        output_files = []
        statistics_data = []
        
        # 从断点继续执行
        current_keyword_index = checkpoint_data.get('current_keyword_index', 0)
        current_area_index = checkpoint_data.get('current_area_index', 0)
        
        try:
            # 遍历关键词
            for i in range(current_keyword_index, len(keywords)):
                keyword = keywords[i]
                
                # 如果关键词已经完成或失败，跳过
                if keyword in checkpoint_data.get('completed_keywords', []) or keyword in checkpoint_data.get('failed_keywords', []):
                    continue
                
                # 遍历地区
                for j in range(current_area_index, len(area_codes)):
                    area_code = area_codes[j]
                    
                    # 检查任务是否被停止
                    if not self.is_task_running(task_id):
                        log.info(f"任务 {task_id} 已被停止")
                        
                        # 更新断点续传数据
                        checkpoint_data['current_keyword_index'] = i
                        checkpoint_data['current_area_index'] = j
                        
                        self._update_task_status(
                            task_id, 'paused',
                            checkpoint_data=checkpoint_data,
                            output_files=output_files
                        )
                        return True
                    
                    # 获取地区名称
                    area_name = "全国"
                    if area_code != '0':
                        area_info = self.city_manager.get_city_by_code(area_code)
                        if area_info:
                            area_name = area_info.get('name', f"地区{area_code}")
                    
                    # 记录日志
                    self._log_task(task_id, "INFO", f"开始爬取关键词: {keyword}, 地区: {area_name}")
                    
                    try:
                        # 获取Cookie
                        cookie = self.cookie_rotator.get_available_cookie()
                        if not cookie:
                            self._log_task(task_id, "ERROR", "没有可用的Cookie")
                            raise Exception("没有可用的Cookie")
                        
                        # 爬取搜索指数
                        result = spider.get_search_index(
                            keyword=keyword,
                            start_date=start_date,
                            end_date=end_date,
                            area=area_code,
                            cookie=cookie
                        )
                        
                        if not result or 'data' not in result:
                            self._log_task(task_id, "ERROR", f"爬取失败: {keyword}, 地区: {area_name}")
                            
                            # 标记Cookie为无效
                            self.cookie_rotator.mark_cookie_invalid(cookie.get('cookie_id'))
                            
                            # 记录失败统计
                            statistics_data.append({
                                'keyword': keyword,
                                'city_code': area_code,
                                'city_name': area_name,
                                'data_type': 'search_index',
                                'data_date': f"{start_date}~{end_date}",
                                'item_count': 1,
                                'success_count': 0,
                                'fail_count': 1
                            })
                            
                            # 更新失败项目数
                            failed_items += 1
                            
                            # 添加到失败关键词列表
                            if keyword not in checkpoint_data.get('failed_keywords', []):
                                if 'failed_keywords' not in checkpoint_data:
                                    checkpoint_data['failed_keywords'] = []
                                checkpoint_data['failed_keywords'].append(keyword)
                            
                            # 更新任务状态
                            self._update_task_status(
                                task_id, 'running',
                                failed_items=failed_items,
                                progress=round((completed_items + failed_items) / total_items * 100, 2) if total_items > 0 else 0,
                                checkpoint_data=checkpoint_data
                            )
                            
                            continue
                        
                        # 保存结果
                        output_file = os.path.join(output_dir, f"{keyword}_{area_code}_{start_date}_{end_date}.json")
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(result, f, ensure_ascii=False, indent=2)
                        
                        output_files.append(output_file)
                        
                        # 记录成功统计
                        statistics_data.append({
                            'keyword': keyword,
                            'city_code': area_code,
                            'city_name': area_name,
                            'data_type': 'search_index',
                            'data_date': f"{start_date}~{end_date}",
                            'item_count': 1,
                            'success_count': 1,
                            'fail_count': 0
                        })
                        
                        self._log_task(task_id, "INFO", f"爬取成功: {keyword}, 地区: {area_name}")
                        
                        # 标记Cookie为有效
                        self.cookie_rotator.mark_cookie_valid(cookie.get('cookie_id'))
                        
                    except Exception as e:
                        self._log_task(task_id, "ERROR", f"爬取异常: {keyword}, 地区: {area_name}, 错误: {e}")
                        
                        # 记录失败统计
                        statistics_data.append({
                            'keyword': keyword,
                            'city_code': area_code,
                            'city_name': area_name,
                            'data_type': 'search_index',
                            'data_date': f"{start_date}~{end_date}",
                            'item_count': 1,
                            'success_count': 0,
                            'fail_count': 1
                        })
                        
                        # 更新失败项目数
                        failed_items += 1
                        
                        # 添加到失败关键词列表
                        if keyword not in checkpoint_data.get('failed_keywords', []):
                            if 'failed_keywords' not in checkpoint_data:
                                checkpoint_data['failed_keywords'] = []
                            checkpoint_data['failed_keywords'].append(keyword)
                        
                        # 更新任务状态
                        self._update_task_status(
                            task_id, 'running',
                            failed_items=failed_items,
                            progress=round((completed_items + failed_items) / total_items * 100, 2) if total_items > 0 else 0,
                            checkpoint_data=checkpoint_data
                        )
                
                # 添加到已完成关键词列表
                if keyword not in checkpoint_data.get('completed_keywords', []) and keyword not in checkpoint_data.get('failed_keywords', []):
                    if 'completed_keywords' not in checkpoint_data:
                        checkpoint_data['completed_keywords'] = []
                    checkpoint_data['completed_keywords'].append(keyword)
                    
                    # 更新已完成项目数
                    completed_items += 1
                
                # 重置地区索引
                current_area_index = 0
                
                # 更新任务状态
                self._update_task_status(
                    task_id, 'running',
                    completed_items=completed_items,
                    progress=round((completed_items + failed_items) / total_items * 100, 2) if total_items > 0 else 0,
                    checkpoint_data=checkpoint_data,
                    output_files=output_files
                )
            
            # 更新统计数据
            self._update_task_statistics(task_id, 'search_index', statistics_data)
            
            # 更新任务状态为已完成
            self._update_task_status(
                task_id, 'completed',
                completed_items=completed_items,
                failed_items=failed_items,
                progress=100,
                output_files=output_files
            )
            
            return True
            
        except Exception as e:
            log.error(f"执行搜索指数任务失败: {e}")
            log.error(traceback.format_exc())
            
            # 更新断点续传数据
            checkpoint_data['current_keyword_index'] = current_keyword_index
            checkpoint_data['current_area_index'] = current_area_index
            
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