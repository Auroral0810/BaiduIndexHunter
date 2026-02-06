"""
资讯指数爬虫（趋势数据）
"""
import urllib.parse
import os
import json
import requests
import traceback
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import pickle
import traceback

from src.core.logger import log
from src.utils.rate_limiter import rate_limiter
from src.utils.decorators import retry
from src.engine.crypto.cipher_generator import cipher_text_generator
from src.services.processor_service import data_processor
from src.services.storage_service import storage_service
from src.core.config import BAIDU_INDEX_API, OUTPUT_DIR
from fake_useragent import UserAgent
from src.engine.spider.base_crawler import BaseCrawler

# 自定义异常类
class NoCookieAvailableError(Exception):
    """当没有可用Cookie时抛出的异常"""
    pass

class FeedIndexCrawler(BaseCrawler):
    """百度资讯指数爬虫类"""
    
    def __init__(self):
        """初始化爬虫"""
        super().__init__(task_type="feed_index")
        
        # FeedIndexCrawler特有的初始化
        self.current_keyword_index = 0
        self.current_city_index = 0
        self.current_date_range_index = 0
        self.city_dict = {}  # 城市代码到名称的映射
        self.ua = UserAgent()
        
        # 设置线程池最大工作线程数 (从配置服务加载，如果基类未提供)
        from src.services.config_service import config_manager
        self.max_workers = int(config_manager.get('spider.max_workers', 5))
        self.timeout = int(config_manager.get('spider.timeout', 15))
        self.retry_times = int(config_manager.get('spider.retry_times', 2))
        log.info(f"爬虫配置已加载: max_workers={self.max_workers}, timeout={self.timeout}, retry_times={self.retry_times}")
        
    # setup_signal_handlers, handle_exit, _generate_task_id, _update_task_db_status, _update_spider_statistics, _flush_buffer 均由 BaseCrawler 提供
    
    # _get_feed_index 包含特定的解析逻辑，处理过程委托给 data_processor

    def _save_global_checkpoint(self):
        """保存全局检查点 (覆盖基类以包含 city_dict)"""
        if not self.checkpoint_path: return
        try:
            checkpoint_data = {
                'completed_keywords': list(self.completed_keywords),
                'failed_keywords': list(self.failed_keywords),
                'completed_tasks': self.completed_tasks,
                'failed_tasks': self.failed_tasks,
                'total_tasks': self.total_tasks,
                'task_id': self.task_id,
                'output_path': self.output_path,
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'city_dict': self.city_dict,
                'current_keyword_index': self.current_keyword_index,
                'current_city_index': self.current_city_index,
                'current_date_range_index': self.current_date_range_index,
            }
            storage_service.save_pickle(checkpoint_data, self.checkpoint_path)
            log.info(f"检查点已更新: {self.completed_tasks}/{self.total_tasks}")
        except Exception as e:
            log.error(f"Save Checkpoint Error: {e}")
            
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
    def _get_cipher_text(self, keyword):
        """获取Cipher-Text参数"""
        encoded_keyword = keyword.replace(' ', '%20')
        cipher_url = f'{BAIDU_INDEX_API["referer"]}#/trend/{encoded_keyword}?words={encoded_keyword}'
        return cipher_text_generator.generate(cipher_url)
    
    @retry(max_retries=3, delay=2)
    
    @retry(max_retries=3, delay=2)
    def _get_feed_index(self, area, keywords, start_date=None, end_date=None, days=None):
        """获取资讯指数数据"""
        # 使用rate_limiter来限制请求频率
        rate_limiter.wait()
        
        # 构建word参数
        word_param_list = []
        for keyword in keywords:
            word_param_list.append([{"name": keyword, "wordType": 1}])
        
        # 构建请求URL - 使用separators去除空格，ensure_ascii=False保留中文(让quote处理编码)
        json_str = json.dumps(word_param_list, separators=(',', ':'), ensure_ascii=False)
        encoded_word_param = urllib.parse.quote(json_str)
        
        log.debug(f"构建的word参数: {json_str}")
        log.debug(f"编码后的word参数: {encoded_word_param}")
        
        if days:
            url = f"{BAIDU_INDEX_API['trend_url']}?area={area}&word={encoded_word_param}&days={days}"
        else:
            url = f"{BAIDU_INDEX_API['trend_url']}?area={area}&word={encoded_word_param}&startDate={start_date}&endDate={end_date}"
            
        log.debug(f"请求URL: {url}")
        
        # 获取有效的Cookie - cookie_rotator.get_cookie()方法内部会记录使用量，不需要额外记录
        account_id, cookie_dict = self.cookie_rotator.get_cookie()
        if not cookie_dict:
            # 修改这里：不再等待，而是抛出特定异常，以便上层处理
            log.warning("所有Cookie均被锁定，无法继续爬取")
            raise NoCookieAvailableError("所有Cookie均被锁定，无法继续爬取")
            
        # 获取Cipher-Text
        cipher_text = self._get_cipher_text(keywords[0])
        
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Cipher-Text': cipher_text,
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': BAIDU_INDEX_API['referer'],
            'User-Agent': self.ua.random,
        }
        
        response = requests.get(url, cookies=cookie_dict, headers=headers)
        
        if response.status_code != 200:
            log.error(f"请求失败: {response.status_code}")
            return None
            
        data = response.json()
        res_data = data.get('data', {})
        
        # 检查响应状态
        status = data.get('status')
        if status == 10001:  # 请求被锁定
            log.warning(f"Cookie被临时锁定: {account_id}")
            self.cookie_rotator.report_cookie_status(account_id, False)
            return None
        elif status == 10000:  # 未登录
            log.warning(f"Cookie无效或已过期: {account_id}")
            self.cookie_rotator.report_cookie_status(account_id, False, permanent=True)
            return None
        elif status == 1:  # 无数据 (正常情况，如日期太早)
            log.info(f"关键词 {keywords} 在城市 {area} 无数据 (status: 1)")
            return data, cookie_dict
        elif status != 0:
            log.error(f"请求失败: {data}")
            return None
        
        # 打印调试信息：检查返回的数据结构
        log.debug(f"API响应状态: status={status}, 关键词数量: {len(keywords)}, 城市代码: {area}")
        if res_data and res_data.get('index'):
            index_list = res_data.get('index', [])
            log.debug(f"返回的index数组长度: {len(index_list)}")
            for idx, index_item in enumerate(index_list):
                key_info = index_item.get('key', [])
                data_type = index_item.get('type', 'unknown')
                raw_data_len = len(index_item.get('data', ''))
                log.debug(f"index[{idx}]: key={json.dumps(key_info, ensure_ascii=False)}, type={data_type}, data长度={raw_data_len}")
                if raw_data_len == 0:
                    log.warning(f"警告: index[{idx}] 的data字段为空! key={json.dumps(key_info, ensure_ascii=False)}")
        else:
            log.warning(f"API返回数据格式异常: data字段={data.get('data')}, message={data.get('message', '')}")
            
        return data, cookie_dict
    
    def _process_feed_index_data(self, data, cookie, keyword, city_code, city_name, start_date, end_date):
        """处理资讯指数数据（单个关键词）"""
        daily_list, stats_list = data_processor.process_multi_feed_index_data(
            data, cookie, [keyword], city_code, city_name, start_date, end_date
        )
        return daily_list, (stats_list[0] if stats_list else None)
    
    def _process_multi_feed_index_data(self, data, cookie, keywords, city_code, city_name, start_date, end_date):
        """处理多个关键词的资讯指数数据"""
        return data_processor.process_multi_feed_index_data(
            data, cookie, keywords, city_code, city_name, start_date, end_date
        )
    
    def _process_task(self, task_data):
        """
        处理单个任务的函数，用于线程池
        
        参数:
            task_data (tuple): (keyword, city_code, city_name, start_date, end_date)
        或者 (keywords, city_code, city_name, start_date, end_date) 其中keywords是关键词列表
        
        返回值:
            对于单关键词模式: (task_key, daily_data, stats_record, is_success)
            对于批量模式: ([task_keys], daily_data_list, stats_records_list, is_success)
            其中 is_success 表示是否成功获取到有效数据
        """
        rate_limiter.wait()
        
        # 判断第一个参数是单个关键词还是关键词列表
        if isinstance(task_data[0], list):
            keywords = task_data[0]
            city_code, city_name, start_date, end_date = task_data[1:]
            is_batch = True
            task_desc = f"Batch[{len(keywords)}]: {keywords[0]}... - {city_name}"
        else:
            keyword = task_data[0]
            keywords = [keyword]
            city_code, city_name, start_date, end_date = task_data[1:]
            is_batch = False
            task_desc = f"Single: {keyword} - {city_name}"
        
        log.debug(f"开始处理任务: {task_desc}, 日期: {start_date} 至 {end_date}")
        
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
            result = self._get_feed_index(city_code, keywords, start_date, end_date)
            if not result:
                log.warning(f"获取数据失败，标记为失败任务: {task_desc}")
                
                # 返回失败标记，不保存空数据
                if not is_batch:
                    return task_key, None, None, False
                else:
                    return [f"{kw}_{city_code}_{start_date}_{end_date}" for kw in keywords], None, None, False
        except NoCookieAvailableError:
            # 向上层抛出异常，通知主线程暂停任务
            raise
        except Exception as e:
            log.error(f"处理任务时出错: {e}")
            # 返回失败标记，不保存空数据
            if not is_batch:
                return task_key, None, None, False
            else:
                return [f"{kw}_{city_code}_{start_date}_{end_date}" for kw in keywords], None, None, False
        
        data, cookie = result
        
        # 处理数据
        if not is_batch:
            # 单关键词处理
            daily_data, stats_record = self._process_feed_index_data(
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
            daily_data_list, stats_records_list = self._process_multi_feed_index_data(
                data, cookie, keywords, city_code, city_name, start_date, end_date
            )
            
            # 如果处理结果为空，标记为失败
            if not daily_data_list or not stats_records_list:
                log.warning(f"批量处理数据失败，标记为失败任务: {city_code}, {start_date}-{end_date}, 关键词数量: {len(keywords)}")
                return [f"{kw}_{city_code}_{start_date}_{end_date}" for kw in keywords], None, None, False
            
            # 成功获取数据
            return [f"{kw}_{city_code}_{start_date}_{end_date}" for kw in keywords], daily_data_list, stats_records_list, True
    
    # _process_year_range, _load_keywords_from_file, _load_cities_from_file, _load_date_ranges_from_file, _save_data_to_file(_flush_buffer), _fast_count_csv_rows 均由 BaseCrawler 提供
    
    def crawl(self, task_id=None, keywords=None, cities=None, date_ranges=None, days=None, 
              keywords_file=None, cities_file=None, date_ranges_file=None,
              year_range=None, resume=False, checkpoint_task_id=None, total_tasks=None, batch_size=5, **kwargs):
        """爬取百度资讯指数任务"""
        try:
            # 1. 初始化
            if resume and checkpoint_task_id:
                self.task_id = checkpoint_task_id
                if not self._load_global_checkpoint(checkpoint_task_id):
                    log.warning(f"Failed to load checkpoint {checkpoint_task_id}, creating new task.")
                    self.task_id = self._generate_task_id()
                    resume = False
            else:
                self.task_id = task_id if task_id else self._generate_task_id()
                self._prepare_initial_state()

            if not resume:
                self.output_path = os.path.join(OUTPUT_DIR, 'feed_index', self.task_id)
                os.makedirs(self.output_path, exist_ok=True)
                self.checkpoint_path = os.path.join(OUTPUT_DIR, f"checkpoints/feed_index_checkpoint_{self.task_id}.pkl")
                os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)

            # 2. 准备参数
            keywords = keywords or (self._load_keywords_from_file(keywords_file) if keywords_file else [])
            if not keywords: return log.error("No keywords provided") or False

            if not resume:
                if cities_file: 
                    self.city_dict = self._load_cities_from_file(cities_file)
                elif cities:
                    if isinstance(cities, dict):
                        self.city_dict = {}
                        for k, info in cities.items():
                            if isinstance(info, dict):
                                code = str(info.get('code', k))
                                name = info.get('name', str(info))
                                self.city_dict[code] = name
                            else:
                                self.city_dict[str(k)] = str(info)
                    else: 
                        self.city_dict = cities
                else: 
                    self.city_dict = {"0": "全国"}

            # 处理日期范围
            log.info(f"爬虫接收到的 date_ranges 参数: {date_ranges}, 类型: {type(date_ranges)}, 长度: {len(date_ranges) if date_ranges else 0}")
            
            if date_ranges_file: date_ranges = self._load_date_ranges_from_file(date_ranges_file)
            elif year_range: 
                start_y = year_range[0][0] if isinstance(year_range[0], (list, tuple)) else year_range[0]
                end_y = year_range[0][1] if isinstance(year_range[0], (list, tuple)) else year_range[1]
                date_ranges = self._process_year_range(start_y, end_y)
            elif days:
                end_date_obj = datetime.now() - timedelta(days=2)
                end_date = end_date_obj.strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=days+1)).strftime('%Y-%m-%d')
                date_ranges = [(start_date, end_date)]
            
            if not date_ranges:
                log.info("Using default 30 days")
                end_date_obj = datetime.now() - timedelta(days=2)
                end_date = end_date_obj.strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=31)).strftime('%Y-%m-%d')
                date_ranges = [(start_date, end_date)]
            
            log.info(f"最终使用的 date_ranges 长度: {len(date_ranges)}")

            self.total_tasks = len(keywords) * len(self.city_dict) * len(date_ranges)
            log.info(f"Task ID: {self.task_id}, Total: {self.total_tasks}")

            # 3. 准备子任务
            all_tasks = []
            batch_size = min(batch_size, 5)
            for i in range(0, len(keywords), batch_size):
                batch = keywords[i:i+batch_size]
                for city_code, city_name in self.city_dict.items():
                    for start_date, end_date in date_ranges:
                        task_keys = [f"{kw}_{city_code}_{start_date}_{end_date}" for kw in batch]
                        if all(tk in self.completed_keywords for tk in task_keys): continue
                        all_tasks.append((batch if batch_size > 1 else batch[0], city_code, city_name, start_date, end_date))

            if not all_tasks:
                log.info("All tasks completed")
                self._update_task_db_status('completed', progress=100)
                return True

            # 4. 执行抓取
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_task = {executor.submit(self._process_task, task): task for task in all_tasks}
                for future in as_completed(future_to_task):
                    try:
                        result = future.result()
                        if not result: continue
                        
                        # result: (keys, daily, stats, success) or similar
                        if len(result) == 4:
                            task_keys, daily_data, stats_records, success = result
                            is_batch = isinstance(task_keys, list)
                            keys = task_keys if is_batch else [task_keys]
                            
                            if success and daily_data:
                                if is_batch:
                                    self.data_cache.extend(daily_data)
                                    self.stats_cache.extend(stats_records)
                                else:
                                    self.data_cache.extend(daily_data)
                                    self.stats_cache.append(stats_records)
                                
                                for tk in keys:
                                    self.completed_keywords.add(tk)
                                    self.completed_tasks += 1
                            else:
                                for tk in keys:
                                    self.failed_keywords.add(tk)
                                    self.failed_tasks += 1
                        
                        if (self.completed_tasks + self.failed_tasks) % 10 == 0:
                            self._save_global_checkpoint()
                            prog = (self.completed_tasks + self.failed_tasks) / self.total_tasks * 100
                            self._update_task_db_status('running', progress=prog)
                            if len(self.data_cache) >= 100: self._flush_buffer()

                    except NoCookieAvailableError:
                        log.error("No cookies available, pausing task")
                        self._flush_buffer(force=True)
                        self._update_task_db_status('paused', error_message="No cookies available")
                        return False
                    except Exception as e:
                        log.error(f"Task error: {e}")
                        log.error(traceback.format_exc())

            # 5. 完成
            self._flush_buffer(force=True)
            status = 'completed' if self.failed_tasks == 0 else 'failed'
            msg = f"Completed with {self.failed_tasks} failed items" if status == 'failed' else None
            self._update_task_db_status(status, progress=100, error_message=msg)
            return status == 'completed'

        except Exception as e:
            log.error(f"Crawl master loop failed: {e}")
            log.error(traceback.format_exc())
            self._flush_buffer(force=True)
            self._update_task_db_status('failed', error_message=str(e))
            return False
    

# 创建爬虫实例
feed_index_crawler = FeedIndexCrawler()