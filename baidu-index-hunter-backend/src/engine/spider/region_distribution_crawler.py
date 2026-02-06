"""
地域分布爬虫（人群画像的地域分布）
"""
import time
from typing import List, Dict, Any, Optional, Union, Tuple
import pandas as pd
from datetime import datetime, timedelta
from src.core.logger import log
from src.utils.decorators import retry
from src.engine.spider.base_crawler import BaseCrawler
from src.engine.processors.region_processor import region_processor

class RegionDistributionCrawler(BaseCrawler):
    """地域分布爬虫，负责获取百度指数的地域分布数据"""
    
    # 预定义的天数选项
    DAYS_OPTIONS = [7, 30, 90, 180, 365]

    def __init__(self):
        """初始化地域分布爬虫"""
        super().__init__(task_type="region")
        from src.core.config import BAIDU_INDEX_API
        self.region_api_url = BAIDU_INDEX_API.get('region_api_url', 'https://index.baidu.com/api/Region/getregion')
        
    def _prepare_tasks(self, keywords: List[str], regions: List[int], date_ranges: List[Tuple[str, str]], **kwargs) -> List[Dict]:
        """
        准备任务：生成 (keyword, region, start_date, end_date) 的组合
        """
        tasks = []
        for keyword in keywords:
            for region in regions:
                for start_date, end_date in date_ranges:
                    tasks.append({
                        'keyword': keyword,
                        'region': region,
                        'start_date': start_date,
                        'end_date': end_date
                    })
        return tasks

    def _process_task(self, task_item: Dict) -> Any:
        """
        处理单个任务
        """
        result = self.get_region_distribution(
            keywords=[task_item['keyword']], 
            region=task_item['region'],
            start_date=task_item['start_date'],
            end_date=task_item['end_date']
        )
        
        if not result:
             raise Exception(f"Failed to get region distribution for {task_item['keyword']}")
             
        # 使用地域分布数据处理器处理
        df = region_processor.process_region_distribution_data(
            result, 
            task_item['region'], 
            task_item['keyword'], 
            task_item['start_date'], 
            task_item['end_date']
        )
        
        return df

    @retry(max_retries=2)
    def get_region_distribution(self, keywords: List[str], region: int = 0, days: Optional[int] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Optional[Dict]:
        """
        获取地域分布数据 API 请求
        """
        try:
            account_id, cookie_dict = self._get_cookie_dict()
            if not cookie_dict:
                return None
            
            # 地域分布API不支持批量，虽然参数叫word且逗号分隔，但通常建议单个
            keywords_str = ','.join(keywords)
            
            url_params = {
                'region': str(region),
                'word': keywords_str,
                'startDate': start_date or "",
                'endDate': end_date or "",
                'days': str(days) if days else ""
            }
            
            import urllib.parse
            query_string = urllib.parse.urlencode(url_params)
            url = f'{self.region_api_url}?{query_string}'
            
            from src.utils.rate_limiter import rate_limiter
            rate_limiter.wait()
            
            import requests
            
            # Generate Cipher-Text using the first keyword (or primary keyword)
            # This is critical for getting correct non-duplicated data from Baidu
            cipher_text = self._get_cipher_text(keywords[0])
            headers = self._get_common_headers(cipher_text)
            
            headers['Referer'] = self.region_api_url
            
            log.info(f"[{self.task_type}] Requesting: {keywords_str} Region:{region} Date:{start_date}-{end_date}")
            response = requests.get(
                url=url,
                headers=headers,
                cookies=cookie_dict,
                timeout=15
            )
            
            if response.status_code != 200:
                self.cookie_rotator.report_cookie_status(account_id, False)
                return None
                
            result = response.json()
            log.info(f"[{self.task_type}] API Response: {result}")
            if result.get('status') != 0:
                msg = result.get('message', '')
                log.error(f"[{self.task_type}] API Error: {msg}")
                if "not login" in msg:
                    self.cookie_rotator.report_cookie_status(account_id, False, permanent=True)
                else:
                    self.cookie_rotator.report_cookie_status(account_id, False)
                return None
                
            self.cookie_rotator.report_cookie_status(account_id, True)
            return result
            
        except Exception as e:
            log.error(f"[{self.task_type}] Request Error: {e}")
            return None

    def _generate_date_ranges(self, days=None, start_date=None, end_date=None, year_range=None) -> List[Tuple[str, str]]:
        """
        生成日期范围
        地域分布 API 返回的是聚合数据，不需要按天拆分
        直接返回一个完整的日期范围即可
        """
        # 如果同时指定了 start/end，直接作为一个整体范围
        if start_date and end_date:
            return [(start_date, end_date)]
        
        # 如果指定了天数
        if days:
            end = datetime.now()
            start = end - timedelta(days=days)
            return [(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))]
        
        # 如果指定了年份范围
        if year_range:
            if isinstance(year_range, (list, tuple)) and len(year_range) >= 2:
                # 年份范围转换为日期范围
                start_year = int(year_range[0])
                end_year = int(year_range[1])
                return [(f"{start_year}-01-01", f"{end_year}-12-31")]
        
        # 默认返回最近 90 天（地域分布通常需要更长时间来聚合数据）
        end = datetime.now()
        start = end - timedelta(days=90)
        return [(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))]


    def crawl(self, keywords: Union[List[str], str], 
              regions: Optional[Union[List[int], int]] = None,
              days: Optional[int] = None,
              start_date: Optional[str] = None, 
              end_date: Optional[str] = None,
              year_range: Optional[List[int]] = None,
              **kwargs):
        """
        执行爬取任务
        """
        if isinstance(keywords, str):
            keywords = keywords.split(',') if ',' in keywords else [keywords]
            
        if regions is None:
            regions = [0]
        elif isinstance(regions, int):
            regions = [regions]

        # 生成日期范围
        # 优先使用传入的 date_ranges (如果 kwargs 有)
        date_ranges = kwargs.get('date_ranges')
        if not date_ranges:
            date_ranges = self._generate_date_ranges(days, start_date, end_date, year_range)

        # 1. 初始化任务
        if kwargs.get('resume') and (kwargs.get('task_id') or kwargs.get('checkpoint_task_id')):
            self.task_id = kwargs.get('task_id') or kwargs.get('checkpoint_task_id')
            if not self._load_global_checkpoint(self.task_id):
                log.warning(f"Failed to load checkpoint {self.task_id}, creating new task.")
                self.task_id = self._generate_task_id()
                self._prepare_initial_state()
        else:
            self.task_id = kwargs.get('task_id') or self._generate_task_id()
            self._prepare_initial_state()

        import os
        from src.core.config import OUTPUT_DIR
        self.output_path = os.path.join(OUTPUT_DIR, "region_distributions", self.task_id)
        os.makedirs(self.output_path, exist_ok=True)
        self.checkpoint_path = os.path.join(OUTPUT_DIR, "checkpoints", f"{self.task_type}_checkpoint_{self.task_id}.pkl")
        
        # 2. 准备任务
        tasks = self._prepare_tasks(keywords, regions, date_ranges)
        self.total_tasks = len(tasks)
        
        # 3. 恢复后的起始索引
        start_index = self.completed_tasks
        
        self._update_task_db_status('running', 0)
        
        try:
            for i in range(start_index, len(tasks)):
                task_item = tasks[i]
                try:
                    df = self._process_task(task_item)
                    
                    with self.task_lock:
                        if df is not None and not df.empty:
                            self.data_cache.extend(df.to_dict('records'))
                        
                        self.completed_tasks += 1
                        self.completed_keywords.add(f"{task_item['keyword']}_{task_item['region']}_{task_item['start_date']}")
                    
                    self._flush_buffer()
                    
                    progress = (self.completed_tasks / self.total_tasks) * 100
                    self._update_task_db_status('running', progress)
                    
                except Exception as e:
                    self.failed_tasks += 1
                    log.error(f"[{self.task_type}] Task failed: {task_item}, Error: {e}")
                    self._update_task_db_status('running', error_message=str(e))
                
                time.sleep(1)

            return self._finalize_crawl('completed')
            
        except Exception as e:
            log.error(f"[{self.task_type}] Critical Error: {e}")
            return self._finalize_crawl('failed', str(e))

region_distribution_crawler = RegionDistributionCrawler()
