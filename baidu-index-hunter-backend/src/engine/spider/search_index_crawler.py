"""
搜索指数爬虫（日度、周度数据和整体统计数据）
"""
import urllib.parse
import os
import json
import requests
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.core.logger import log
from src.utils.rate_limiter import rate_limiter
from src.utils.decorators import retry
from src.engine.crypto.cipher_generator import cipher_text_generator
from src.services.processor_service import data_processor
from src.core.config import BAIDU_INDEX_API, OUTPUT_DIR
from src.engine.spider.base_crawler import BaseCrawler, CrawlerInterrupted

# 自定义异常类
class NoCookieAvailableError(Exception):
    """当没有可用Cookie时抛出的异常"""
    pass

class SearchIndexCrawler(BaseCrawler):
    """百度搜索指数爬虫类（并行版本）"""
    
    def __init__(self):
        """初始化爬虫"""
        super().__init__(task_type="search_index")
        
        # 爬虫特定配置
        from src.services.config_service import config_manager
        self.max_workers = int(config_manager.get('spider.max_workers', 5))
        self.timeout = int(config_manager.get('spider.timeout', 15))
        self.retry_times = int(config_manager.get('spider.retry_times', 2))
        
        self.current_keyword_index = 0
        self.current_city_index = 0
        self.current_date_range_index = 0
        self.city_dict = {}
        
        log.info(f"SearchIndexCrawler 爬虫配置已加载: max_workers={self.max_workers}, timeout={self.timeout}, retry_times={self.retry_times}")
        
    # --- 覆盖基类方法以处理特定的状态 ---

    def _get_checkpoint_data(self) -> dict:
        """获取需要持久化的检查点数据 (扩展基类，添加 city_dict 等)"""
        data = super()._get_checkpoint_data()
        data.update({
            'city_dict': self.city_dict,
            'current_keyword_index': self.current_keyword_index,
            'current_city_index': self.current_city_index,
            'current_date_range_index': self.current_date_range_index,
        })
        return data

    def _load_global_checkpoint(self, task_id):
        """加载全局检查点 (覆盖基类以处理 city_dict)"""
        checkpoint = super()._load_global_checkpoint(task_id)
        if checkpoint:
            self.city_dict = checkpoint.get('city_dict', {})
            self.current_keyword_index = checkpoint.get('current_keyword_index', 0)
            self.current_city_index = checkpoint.get('current_city_index', 0)
            self.current_date_range_index = checkpoint.get('current_date_range_index', 0)
            return True
        return False
    
    @retry(max_retries=3, delay=2)
    def _get_search_index(self, area, keywords, start_date, end_date):
        """获取搜索指数数据"""
        # 使用rate_limiter来限制请求频率
        rate_limiter.wait()
        
        # 构建word参数
        word_list = []
        for keyword in keywords:
            word_list.append([{"name": keyword, "wordType": 1}])
        
        # 将word_list转换为JSON字符串
        word_param = json.dumps(word_list, ensure_ascii=False)
        
        # 构造参数
        params = {
            "area": area,
            "word": word_param,
            "startDate": start_date,
            "endDate": end_date
        }
        
        # 构造URL
        encoded_word = urllib.parse.quote(params["word"])
        url = f"{BAIDU_INDEX_API['search_url']}?area={params['area']}&word={encoded_word}&startDate={params['startDate']}&endDate={params['endDate']}"
        
        # 获取有效的Cookie
        account_id, cookie_dict = self._get_cookie_dict()
        if not cookie_dict:
            raise NoCookieAvailableError("所有Cookie均被锁定，无法继续爬取")
            
        # 获取Cipher-Text (使用第一个关键词)
        cipher_text = self._get_cipher_text(keywords[0])
        headers = self._get_common_headers(cipher_text)
        
        response = requests.get(url, cookies=cookie_dict, headers=headers)
        
        if response.status_code != 200:
            log.error(f"请求失败: {response.status_code}")
            return None
            
        data = response.json()
        
        # 检查响应状态
        status = data.get('status')
        if status == 10001:  # 请求被锁定
            log.warning(f"Cookie被临时锁定: {account_id}")
            self._report_cookie_status(account_id, False)
            return None
        elif status == 10000:  # 未登录
            log.warning(f"Cookie无效或已过期: {account_id}")
            self._report_cookie_status(account_id, False, permanent=True)
            return None
        elif status != 0:
            log.error(f"请求失败: {data}")
            return None
            
        return data, cookie_dict
    
    def _process_search_index_data(self, data, cookie, keyword, city_code, city_name, start_date, end_date):
        """处理搜索指数数据 (单关键词)"""
        daily_list, stats_list = data_processor.process_multi_search_index_data(
            data, cookie, [keyword], city_code, city_name, start_date, end_date
        )
        log.debug(f"Processed single keyword data. Daily items: {len(daily_list) if daily_list else 0}")
        # Return the full list for daily_data, but stats is one record per keyword range
        return daily_list, (stats_list[0] if stats_list else None)

    def _process_multi_search_index_data(self, data, cookie, keywords, city_code, city_name, start_date, end_date):
        """处理多关键词搜索指数数据"""
        return data_processor.process_multi_search_index_data(
            data, cookie, keywords, city_code, city_name, start_date, end_date
        )
    
    # _process_year_range, _load_keywords_from_file, _load_cities_from_file, _load_date_ranges_from_file 均由 BaseCrawler 统一提供
    
    def _process_task(self, task_data):
        """
        处理单个任务的函数，用于线程池
        """
        self.check_running()
        rate_limiter.wait()
        
        # 判断第一个参数是单个关键词还是关键词列表
        if isinstance(task_data[0], list):
            keywords = task_data[0]
            city_code, city_name, start_date, end_date = task_data[1:]
            is_batch = True
        else:
            keyword = task_data[0]
            keywords = [keyword]
            city_code, city_name, start_date, end_date = task_data[1:]
            is_batch = False
        
        # 检查任务是否已完成（成功完成的任务跳过，失败的任务需要重试）
        if not is_batch:
            task_key = f"{keyword}_{city_code}_{start_date}_{end_date}"
            if task_key in self.completed_keywords:
                # 如果任务已完成，直接返回None，不增加completed_tasks计数
                return None
            # 如果任务之前失败过，从失败集合中移除（准备重试）
            if task_key in self.failed_keywords:
                with self.task_lock:
                    self.failed_keywords.discard(task_key)
        else:
            # 批量模式下，检查所有关键词是否都已完成
            all_completed = True
            for keyword in keywords:
                task_key = f"{keyword}_{city_code}_{start_date}_{end_date}"
                if task_key not in self.completed_keywords:
                    all_completed = False
                    break
                # 如果任务之前失败过，从失败集合中移除（准备重试）
                if task_key in self.failed_keywords:
                    with self.task_lock:
                        self.failed_keywords.discard(task_key)
            
            if all_completed:
                return None
        
        try:
            # 获取数据
            result = self._get_search_index(city_code, keywords, start_date, end_date)
            if not result:
                log.warning(f"获取数据失败，标记为失败任务: {city_code}, {start_date}-{end_date}, 关键词数量: {len(keywords)}")
                
                # 返回失败标记，不保存空数据
                if not is_batch:
                    # 单关键词模式 - 返回失败标记
                    return task_key, None, None, False
                else:
                    # 批量模式 - 返回失败标记
                    return [f"{kw}_{city_code}_{start_date}_{end_date}" for kw in keywords], None, None, False
        except NoCookieAvailableError:
            # 向上层抛出异常，通知主线程暂停任务
            raise
        except Exception as e:
            log.error(f"处理任务时出错: {e}")
            # 返回失败标记，不保存空数据
            if not is_batch:
                # 单关键词模式 - 返回失败标记
                return task_key, None, None, False
            else:
                # 批量模式 - 返回失败标记
                return [f"{kw}_{city_code}_{start_date}_{end_date}" for kw in keywords], None, None, False
        
        data, cookie = result
        
        # 处理数据
        if not is_batch:
            # 单关键词处理
            daily_data, stats_record = self._process_search_index_data(
                data, cookie, keyword, city_code, city_name, start_date, end_date
            )
            
            # 如果处理结果为None，标记为失败
            if daily_data is None or stats_record is None:
                log.warning(f"处理数据失败，标记为失败任务: {task_key}")
                return task_key, None, None, False
            
            # 成功获取数据
            return task_key, daily_data, stats_record, True
        else:
            # 批量处理多个关键词
            daily_data_list, stats_records_list = self._process_multi_search_index_data(
                data, cookie, keywords, city_code, city_name, start_date, end_date
            )
            
            # 如果处理结果为空，标记为失败
            if not daily_data_list or not stats_records_list:
                log.warning(f"批量处理数据失败，标记为失败任务: {city_code}, {start_date}-{end_date}, 关键词数量: {len(keywords)}")
                return [f"{kw}_{city_code}_{start_date}_{end_date}" for kw in keywords], None, None, False
            
            # 成功获取数据
            return [f"{kw}_{city_code}_{start_date}_{end_date}" for kw in keywords], daily_data_list, stats_records_list, True

    
    def crawl(self, task_id=None, keywords=None, cities=None, date_ranges=None, days=None, 
              keywords_file=None, cities_file=None, date_ranges_file=None,
              year_range=None, resume=False, checkpoint_task_id=None, total_tasks=None, batch_size=5, **kwargs):
        """
        爬取百度搜索指数数据
        
        参数:
            task_id (str): 任务ID
            keywords (list): 关键词列表
            cities (dict): 城市代码和名称的字典 {城市代码: 城市名称}
            date_ranges (list): 日期范围列表，每个元素为 (start_date, end_date) 元组
            days (int): 预定义的天数，可以是7、30、90、180
            keywords_file (str): 关键词文件路径
            cities_file (str): 城市代码文件路径
            date_ranges_file (str): 日期范围文件路径
            year_range (tuple): 年份范围，格式为 (start_year, end_year)
            resume (bool): 是否恢复上次任务
            checkpoint_task_id (str): 要恢复的任务ID
            total_tasks (int): 总任务数（从task_executor传入）
            batch_size (int): 每批处理的关键词数量，默认为5，最大不超过5个
        """
        # 设置任务ID和检查点路径
        if resume and checkpoint_task_id:
            self.task_id = checkpoint_task_id
            loaded = self._load_global_checkpoint(checkpoint_task_id)
            if not loaded:
                log.warning(f"未找到任务ID为 {checkpoint_task_id} 的检查点，将创建新任务")
                self.task_id = self._generate_task_id()
                self._prepare_initial_state()
                resume = False
            else:
                # 如果成功加载了检查点，使用检查点中的城市字典
                cities = self.city_dict
                log.info(f"从检查点恢复任务: {checkpoint_task_id}, 已完成任务数: {self.completed_tasks}")
        else:
            self.task_id = task_id if task_id else self._generate_task_id()
            self._prepare_initial_state()
            
        # 如果没有从检查点恢复，则需要设置输出路径和检查点路径
        if not resume:
            self.output_path = os.path.join(OUTPUT_DIR, 'search_index', self.task_id)
            os.makedirs(self.output_path, exist_ok=True)
            self.checkpoint_path = os.path.join(OUTPUT_DIR, f"checkpoints/{self.task_type}_checkpoint_{self.task_id}.db")
            os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)
            self._init_progress_manager(self.checkpoint_path)

        # 加载关键词
        if keywords_file:
            keywords = self._load_keywords_from_file(keywords_file)
        
        if not keywords:
            log.error("未提供关键词列表")
            return False
            
        if not resume:
            if cities_file:
                self.city_dict = self._load_cities_from_file(cities_file)
            elif cities:
                # 统一处理城市参数为 {code: name} 字典格式
                if isinstance(cities, dict):
                    processed_cities = {}
                    for code, city_info in cities.items():
                        if isinstance(city_info, dict) and 'name' in city_info and 'code' in city_info:
                            processed_cities[str(city_info['code'])] = city_info['name']
                        else:
                            processed_cities[str(code)] = str(city_info)
                    self.city_dict = processed_cities
                elif isinstance(cities, list):
                    self.city_dict = {str(c): f"地区{c}" for c in cities}
                    if '0' in self.city_dict: self.city_dict['0'] = "全国"
                elif isinstance(cities, str):
                    self.city_dict = {cities: f"地区{cities}"}
                    if cities == '0': self.city_dict['0'] = "全国"
                else:
                    self.city_dict = {"0": "全国"}
            else:
                self.city_dict = {"0": "全国"}
        
        # 处理日期范围
        log.info(f"爬虫接收到的 date_ranges 参数: {date_ranges}, 类型: {type(date_ranges)}, 长度: {len(date_ranges) if date_ranges else 0}")
        
        if date_ranges_file:
            date_ranges = self._load_date_ranges_from_file(date_ranges_file)
        elif year_range:
            date_ranges = self._process_year_range(year_range[0][0], year_range[0][1])
        elif days:
            # 使用预定义的天数，百度指数数据通常延迟2天
            end_date_obj = datetime.now() - timedelta(days=2)
            end_date = end_date_obj.strftime('%Y-%m-%d')
            # 按照用户要求：从 (今天-2-days) 到 (今天-2)
            start_date = (datetime.now() - timedelta(days=days+1)).strftime('%Y-%m-%d')
            date_ranges = [(start_date, end_date)]
        elif not date_ranges:
            # 默认使用最近30天，同样延迟2天
            end_date_obj = datetime.now() - timedelta(days=2)
            end_date = end_date_obj.strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=31)).strftime('%Y-%m-%d')
            date_ranges = [(start_date, end_date)]
        
        log.info(f"最终使用的 date_ranges 长度: {len(date_ranges)}")
        
        
        
        theoretical_total_tasks = len(keywords) * len(self.city_dict) * len(date_ranges)
        # log.info(f"理论总任务数: {theoretical_total_tasks} (关键词: {len(keywords)}, 城市: {len(self.city_dict)}, 日期范围: {len(date_ranges)})")
        # 初始设置，后面会根据实际任务列表更新
        self.total_tasks = theoretical_total_tasks
        # # 计算总任务数
        # if not resume:
        #     # 如果没有从task_executor传入总任务数，则自行计算
        #     if total_tasks is None:
        #         # 计算理论上的总任务数，但实际执行时会根据all_tasks的长度重新设置
        #         theoretical_total_tasks = len(keywords) * len(self.city_dict) * len(date_ranges)
        #         # log.info(f"理论总任务数: {theoretical_total_tasks} (关键词: {len(keywords)}, 城市: {len(self.city_dict)}, 日期范围: {len(date_ranges)})")
        #         # 初始设置，后面会根据实际任务列表更新
        #         self.total_tasks = theoretical_total_tasks
        #     else:
        #         # 如果传入了总任务数，使用传入的值
        #         self.total_tasks = total_tasks*len(date_ranges)
        #         # log.info(f"使用传入的总任务数: {self.total_tasks}")
        # else:
        #     # 如果是恢复模式且传入了总任务数，检查是否需要更新总任务数
        #     if total_tasks is not None and total_tasks > self.total_tasks:
        #         log.info(f"更新总任务数: {self.total_tasks} -> {total_tasks}")
        #         self.total_tasks = total_tasks
            
        log.info(f"任务ID: {self.task_id}")
        log.info(f"总任务数: {self.total_tasks} (关键词: {len(keywords)}, 城市: {len(self.city_dict)}, 日期范围: {len(date_ranges)})")
        
        # 上次进度更新的百分比，用于每增加5%进度时更新一次数据库
        last_progress_percent = 0
        
        # 记录上次更新ab_sr的任务数
        last_ab_sr_update_task_count = 0
        
        # 开始爬取前先更新一次ab_sr cookie
        # self._update_ab_sr_cookies()
        
        # 开始爬取
        try:
            # 准备所有任务
            all_tasks = []
            
            # 强制限制batch_size最大为5
            batch_size = min(batch_size, 5)
            log.info(f"批量处理关键词，每批次最多 {batch_size} 个关键词")
            
            # 按batch_size将关键词分组
            keyword_batches = []
            for i in range(0, len(keywords), batch_size):
                keyword_batches.append(keywords[i:i+batch_size])
            
            # 如果batch_size为1或者只有一个关键词，使用原来的方式
            if batch_size == 1 or len(keywords) == 1:
                for keyword in keywords:
                    for city_code, city_name in self.city_dict.items():
                        for start_date, end_date in date_ranges:
                            task_key = f"{keyword}_{city_code}_{start_date}_{end_date}"
                            # 检查任务是否已完成
                            if task_key in self.completed_keywords:
                                log.debug(f"跳过已完成的任务: {task_key}")
                                continue
                            all_tasks.append((keyword, city_code, city_name, start_date, end_date))
            else:
                # 批量处理模式
                for keyword_batch in keyword_batches:
                    for city_code, city_name in self.city_dict.items():
                        for start_date, end_date in date_ranges:
                            # 检查该批次中的所有关键词是否都已完成
                            all_completed = True
                            for keyword in keyword_batch:
                                task_key = f"{keyword}_{city_code}_{start_date}_{end_date}"
                                if task_key not in self.completed_keywords:
                                    all_completed = False
                                    break
                            
                            if all_completed:
                                log.debug(f"跳过已完成的批次任务: {city_code}, {start_date}-{end_date}, 关键词数量: {len(keyword_batch)}")
                                continue
                                    
                            all_tasks.append((keyword_batch, city_code, city_name, start_date, end_date))
            
            # 更新实际总任务数为需要执行的任务数量
            # self.total_tasks = len(all_tasks)
            log.info(f"准备执行 {len(all_tasks)} 个任务，使用 {self.max_workers} 个线程")
            
            # 如果所有任务都已完成
            if not all_tasks:
                log.info("所有任务都已完成，无需执行")
                self._update_task_db_status('completed', progress=100)
                return True
            
            # 使用线程池执行任务
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_task = {executor.submit(self._process_task, task): task for task in all_tasks}
                
                for future in as_completed(future_to_task):
                    # 每次结果返回前检查是否停止
                    self.check_running()
                    try:
                        result = future.result()
                        if not result: continue
                        
                        is_batch = isinstance(result[0], list)
                        task_keys, daily_data, stats_records, is_success = result # 此时应统一为4个返回值
                        
                        with self.task_lock:
                            if is_success:
                                keys = task_keys if is_batch else [task_keys]
                                self._mark_items_completed(keys)
                                if daily_data: self.data_cache.extend(daily_data)
                                if stats_records:
                                    if isinstance(stats_records, list): self.stats_cache.extend(stats_records)
                                    else: self.stats_cache.append(stats_records)
                            else:
                                keys = task_keys if is_batch else [task_keys]
                                self._mark_items_failed(keys)
                            
                            if self.completed_tasks % 20 == 0: self._save_global_checkpoint()

                        if len(self.data_cache) >= 200:
                            self._flush_buffer()
                            prog = (self.completed_tasks + self.failed_tasks) / self.total_tasks * 100
                            self._update_task_db_status('running', progress=prog)

                    except NoCookieAvailableError:
                        log.error("Cookie 耗尽，暂停任务")
                        self._flush_buffer(force=True)
                        self._update_task_db_status('paused', error_message="所有 Cookie 均被锁定，等待自动恢复")
                        for f in future_to_task: f.cancel()
                        return False
                    except Exception as e:
                        log.error(f"子任务异常: {e}")

            status = 'failed' if self.failed_tasks > 0 else 'completed'
            msg = f"完成但有 {self.failed_tasks} 项失败" if status == 'failed' else "所有任务已完成"
            return self._finalize_crawl(status, msg)

        except CrawlerInterrupted:
            log.warning(f"[{self.task_type}] 任务被用户或系统中断")
            # 尝试取消还没开始的任务
            try:
                for f in future_to_task: f.cancel()
            except: pass
            return self._finalize_crawl('cancelled', "Task interrupted")
        except Exception as e:
            log.error(f"爬取主流程失败: {e}")
            self._flush_buffer(force=True)
            if self.progress_manager:
                self.progress_manager.close()
                self.progress_manager = None
            self._update_task_db_status('failed', error_message=str(e))
            return False
    
# 创建爬虫实例
search_index_crawler = SearchIndexCrawler()

 