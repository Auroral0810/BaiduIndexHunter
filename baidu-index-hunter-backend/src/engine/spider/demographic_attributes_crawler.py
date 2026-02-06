"""
人群属性爬虫（性别、年龄等基础属性）
"""
import time
from typing import List, Dict, Any, Optional
import pandas as pd
from src.core.logger import log
from src.utils.decorators import retry
from src.engine.spider.base_crawler import BaseCrawler
from src.services.processor_service import data_processor

class DemographicAttributesCrawler(BaseCrawler):
    """人群属性爬虫，负责获取百度指数的人群属性数据（性别、年龄等）"""
    
    def __init__(self):
        """初始化人群属性爬虫"""
        super().__init__(task_type="demographic")
        from src.core.config import BAIDU_INDEX_API
        self.social_api_url = BAIDU_INDEX_API.get('social_api_url', 'https://index.baidu.com/api/SocialApi/base')
        
    def _prepare_tasks(self, keywords: List[str], **kwargs) -> List[List[str]]:
        """
        准备任务：将关键词分批
        """
        if isinstance(keywords, str):
            keywords = [keywords]
            
        batch_size = kwargs.get('batch_size', 5)
        batches = [keywords[i:i + batch_size] for i in range(0, len(keywords), batch_size)]
        return batches

    def _process_task(self, batch_keywords: List[str]) -> Any:
        """
        处理单个任务（一批关键词）
        """
        result = self.get_demographic_attributes(batch_keywords)
        
        if not result:
            raise Exception("Failed to get demographic attributes from API")
            
        # 使用数据处理器处理
        df = data_processor.process_demographic_data(result)
        
        if df is None or df.empty:
             log.warning(f"[{self.task_type}] 批次 {batch_keywords} 获取到数据但处理结果为空")
             return None
             
        return df

    @retry(max_retries=3)
    def get_demographic_attributes(self, keywords: List[str]) -> Optional[Dict]:
        """
        获取人群属性数据 API 请求
        使用 wordlist[] 参数格式批量查询关键词
        """
        try:
            account_id, cookie_dict = self._get_cookie_dict()
            if not cookie_dict:
                return None
            
            from src.utils.rate_limiter import rate_limiter
            rate_limiter.wait()
            
            import requests
            
            # 生成 Cipher-Text (使用第一个关键词)
            cipher_text = self._get_cipher_text(keywords[0])
            headers = self._get_common_headers(cipher_text)
            headers['Referer'] = 'https://index.baidu.com/v2/main/index.html'
            
            # 使用 params 参数让 requests 正确构造 wordlist[] 格式
            # requests 会自动将列表转换为 wordlist[]=a&wordlist[]=b 格式
            params = [('wordlist[]', kw) for kw in keywords]
            
            log.info(f"[{self.task_type}] Requesting demographic attributes: {keywords}")
            response = requests.get(
                url=self.social_api_url,
                headers=headers,
                cookies=cookie_dict,
                params=params,
                timeout=15
            )
            
            if response.status_code != 200:
                log.error(f"[{self.task_type}] HTTP Error: {response.status_code}")
                self.cookie_rotator.report_cookie_status(account_id, False)
                return None
            
            result = response.json()
            log.info(f"[{self.task_type}] API Response status: {result.get('status')}")
            
            if result.get('status') != 0:
                msg = result.get('message', '')
                log.error(f"[{self.task_type}] API Error: {msg}")
                if "not login" in msg.lower():
                    self.cookie_rotator.report_cookie_status(account_id, False, permanent=True)
                else:
                    self.cookie_rotator.report_cookie_status(account_id, False)
                return None
                
            self.cookie_rotator.report_cookie_status(account_id, True)
            return result
            
        except Exception as e:
            log.error(f"[{self.task_type}] Request Error: {e}")
            return None

    def crawl(self, keywords: List[str], **kwargs):
        """
        执行爬取任务
        """
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
            
        # 整个任务只保留一次“全网分布”数据
        self.all_network_processed = False

        import os
        from src.core.config import OUTPUT_DIR
        self.output_path = os.path.join(OUTPUT_DIR, "demographic_attributes", self.task_id)
        os.makedirs(self.output_path, exist_ok=True)
        self.checkpoint_path = os.path.join(OUTPUT_DIR, "checkpoints", f"{self.task_type}_checkpoint_{self.task_id}.pkl")
        
        # 2. 准备任务
        tasks = self._prepare_tasks(keywords, **kwargs)
        self.total_tasks = len(tasks)
        
        # 3. 恢复后的起始索引
        start_index = self.completed_tasks
        
        self._update_task_db_status('running', 0)
        
        try:
            for i in range(start_index, len(tasks)):
                batch = tasks[i]
                try:
                    df = self._process_task(batch)
                    
                    with self.task_lock:
                        if df is not None and not df.empty:
                            # 整个任务只保留一次“全网分布”数据
                            if self.all_network_processed:
                                df = df[df['关键词'] != '全网分布']
                            elif '全网分布' in df['关键词'].values:
                                self.all_network_processed = True
                                
                            if not df.empty:
                                self.data_cache.extend(df.to_dict('records'))
                                
                        self.completed_tasks += 1
                        for kw in batch:
                            self.completed_keywords.add(kw)
                            
                    self._flush_buffer()
                    
                    progress = (self.completed_tasks / self.total_tasks) * 100
                    self._update_task_db_status('running', progress)
                    
                except Exception as e:
                    self.failed_tasks += 1
                    log.error(f"[{self.task_type}] Batch failed: {batch}, Error: {e}")
                    self._update_task_db_status('running', error_message=str(e))
                
                time.sleep(1)

            return self._finalize_crawl('completed')
            
        except Exception as e:
            log.error(f"[{self.task_type}] Critical Error: {e}")
            return self._finalize_crawl('failed', str(e))

demographic_attributes_crawler = DemographicAttributesCrawler()
