"""
兴趣分布爬虫（人群兴趣画像）
"""
import time
from typing import List, Dict, Any, Optional
import pandas as pd
from src.core.logger import log
from src.utils.decorators import retry
from src.engine.spider.base_crawler import BaseCrawler
from src.services.processor_service import data_processor

class InterestProfileCrawler(BaseCrawler):
    """兴趣分布爬虫，负责获取百度指数的人群兴趣画像数据"""
    
    def __init__(self):
        """初始化兴趣分布爬虫"""
        super().__init__(task_type="interest_profile")
        # 直接使用 config 中的 URL 配置，或者硬编码如果不常变
        from src.core.config import BAIDU_INDEX_API
        self.interest_api_url = BAIDU_INDEX_API.get('interest_api_url', 'https://index.baidu.com/api/SocialApi/interest')
        
    def _prepare_tasks(self, keywords: List[str], **kwargs) -> List[List[str]]:
        """
        准备任务：将关键词分批，每批作为一个任务单元
        :param keywords: 关键词列表
        :param batch_size: 每批大小，默认5
        :return: 批次列表
        """
        if isinstance(keywords, str):
            keywords = [keywords]
            
        batch_size = kwargs.get('batch_size', 5) # 官方API支持批量，但建议不要太大
        
        # 将关键词分批
        batches = [keywords[i:i + batch_size] for i in range(0, len(keywords), batch_size)]
        return batches

    def _process_task(self, batch_keywords: List[str]) -> Any:
        """
        处理单个任务（一批关键词）
        :param batch_keywords: 关键词列表
        :return: 处理后的数据 DataFrame
        """
        # 获取兴趣分布数据
        result = self.get_interest_profiles(batch_keywords)
        
        if not result:
            raise Exception("Failed to get interest profiles from API")
            
        # 使用数据处理器处理
        # 注意：这里我们使用 process_interest_profile_data
        df = data_processor.process_interest_profile_data(result)
        
        if df is None or df.empty:
             log.warning(f"[{self.task_type}] 批次 {batch_keywords} 获取到数据但处理结果为空")
             return None
             
        return df

    @retry(max_retries=3)
    def get_interest_profiles(self, keywords: List[str], typeid: Optional[str] = None) -> Optional[Dict]:
        """
        获取兴趣分布数据 API 请求
        """
        try:
            # 获取可用Cookie (使用基类方法)
            account_id, cookie_dict = self._get_cookie_dict()
            if not cookie_dict:
                return None
                
            # 构造URL参数
            url_params = [f'wordlist[]={kw}' for kw in keywords]
            
            # TypeID (虽然很少用到，API似乎默认返回全部)
            url = f'{self.interest_api_url}?{"&".join(url_params)}'
            if typeid:
                url += f'&typeid={typeid}'
                
            # 获取通用的加密参数 (Headers)
            # 注意：Interest API 可能不需要 cipher-text，或者使用的是第一个关键词的？
            # 百度指数 Social API (Demographic/Interest) 图谱类通常不需要 Cipher-Text，只需要 Cookie 和 Referer
            # 但为了保险，我们可以带上。如果不需要，带上也无妨。
            # 另外，RateLimiter 在基类没强制，这里手动调用
            from src.utils.rate_limiter import rate_limiter
            rate_limiter.wait()
            
            import requests
            headers = self._get_common_headers("") # Cipher-Text 为空
            # 覆盖 Referer 确保正确
            headers['Referer'] = self.interest_api_url
            
            log.info(f"[{self.task_type}] Requesting: {keywords}")
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

    def crawl(self, keywords: List[str], **kwargs):
        """
        执行爬取任务
        :param keywords: 关键词列表
        :param kwargs: 其他参数 (resume, task_id 等)
        """
        # 1. 初始化任务
        self.task_id = kwargs.get('task_id') or kwargs.get('checkpoint_task_id') or self._generate_task_id()
        self.output_path = self._init_output_dir(kwargs.get('output_dir')) # BaseCrawler 需要这个吗？
        # BaseCrawler 没有 _init_output_dir，我们需要自己设置 self.output_path
        
        # 设置输出路径 (BaseCrawler 的 _flush_buffer 会用到 self.output_path)
        import os
        from src.core.config import OUTPUT_DIR
        self.output_path = os.path.join(OUTPUT_DIR, "interest_profiles", self.task_id)
        os.makedirs(self.output_path, exist_ok=True)
        self.checkpoint_path = os.path.join(OUTPUT_DIR, "checkpoints", f"{self.task_type}_checkpoint_{self.task_id}.pkl")
        
        # 2. 准备任务
        tasks = self._prepare_tasks(keywords, **kwargs)
        self.total_tasks = len(tasks)
        
        # 3. 恢复检查点 (如果需要)
        start_index = 0
        if kwargs.get('resume'):
            checkpoint = self._load_global_checkpoint(self.task_id)
            if checkpoint:
                self.completed_tasks = checkpoint.get('completed_tasks', 0)
                # 简单处理：对于分批任务，如果我们只记录了数量，可能很难精确恢复到具体哪一批
                # 假设 tasks 列表生成是确定性的 (List[List[str]])
                # 我们跳过已完成数量的批次
                start_index = self.completed_tasks
                log.info(f"[{self.task_type}] Resuming from batch index {start_index}")
        
        # 4. 执行循环
        self._update_task_db_status('running', 0)
        
        try:
            for i in range(start_index, len(tasks)):
                batch = tasks[i]
                
                try:
                    df = self._process_task(batch)
                    
                    with self.task_lock:
                        if df is not None and not df.empty:
                            self.data_cache.extend(df.to_dict('records'))
                        
                        self.completed_tasks += 1
                        # 记录完成的关键词 (拆分batch)
                        for kw in batch:
                            self.completed_keywords.add(kw)
                            
                    # 触发缓存刷新和检查点保存
                    self._flush_buffer()
                    
                    # 更新进度
                    progress = (self.completed_tasks / self.total_tasks) * 100
                    self._update_task_db_status('running', progress)
                    
                except Exception as e:
                    self.failed_tasks += 1
                    log.error(f"[{self.task_type}] Batch failed: {batch}, Error: {e}")
                    # 也是一种推进
                    self._update_task_db_status('running', error_message=str(e))
                
                # 简单的流控，避免过快
                time.sleep(1)

            # 5. 完成
            self._finalize_crawl('completed')
            
        except Exception as e:
            log.error(f"[{self.task_type}] Critical Error: {e}")
            self._finalize_crawl('failed', str(e))
            return False
            
        return True

# 单例实例
interest_profile_crawler = InterestProfileCrawler()
