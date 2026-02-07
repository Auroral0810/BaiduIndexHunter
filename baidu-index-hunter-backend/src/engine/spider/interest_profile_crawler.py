"""
兴趣分布爬虫（人群兴趣画像）
"""
import time
from typing import List, Dict, Any, Optional
import pandas as pd
from src.core.logger import log
from src.utils.decorators import retry
from src.engine.spider.base_crawler import BaseCrawler, CrawlerInterrupted
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
            
        batch_size = min(kwargs.get('batch_size', 5), 5) # 官方API支持批量，但建议不要太大
        
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
        使用 wordlist[] 参数格式批量查询关键词
        """
        try:
            # 获取可用Cookie (使用基类方法)
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
            params = [('wordlist[]', kw) for kw in keywords]
            # 添加 typeid 参数 (可以为空)
            params.append(('typeid', typeid or ''))
            
            log.info(f"[{self.task_type}] Requesting interest profiles: {keywords}")
            response = requests.get(
                url=self.interest_api_url,
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

    def crawl(self, keywords: List[str], output_format=None, **kwargs):
        """
        执行爬取任务
        :param keywords: 关键词列表
        :param output_format: 输出格式 (csv/excel/dta/json/parquet/sql)
        :param kwargs: 其他参数 (resume, task_id 等)
        """
        self._apply_output_format(output_format or kwargs.get('output_format'))
        
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
        self.output_path = os.path.join(OUTPUT_DIR, "interest_profiles", self.task_id)
        os.makedirs(self.output_path, exist_ok=True)
        self.checkpoint_path = os.path.join(OUTPUT_DIR, "checkpoints", f"{self.task_type}_checkpoint_{self.task_id}.db")
        self._init_progress_manager(self.checkpoint_path)
        
        # 2. 准备任务
        tasks = self._prepare_tasks(keywords, **kwargs)
        self.total_tasks = len(tasks)
        
        # 3. 恢复后的起始索引
        start_index = self.completed_tasks
        if start_index > 0:
            log.info(f"[{self.task_type}] Resuming from batch index {start_index}")
        
        # 4. 执行循环
        self._update_task_db_status('running', 0)
        self._add_task_log('info', f"开始执行兴趣分布爬取任务，总关键词数: {len(keywords)}")
        
        try:
            for i in range(start_index, len(tasks)):
                # 检查运行状态，支持快速停止
                self.check_running()
                
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
                                
                                # 生成统计信息并存入 stats_cache
                                for kw in batch:
                                    kw_df = df[df['关键词'] == kw]
                                    if not kw_df.empty:
                                        self.stats_cache.append({
                                            'task_id': self.task_id,
                                            '关键词': kw,
                                            '数据类型': self.task_type,
                                            '数据周期': kw_df.iloc[0]['数据周期'],
                                            '数据项数量': len(kw_df),
                                            '成功数量': 1,
                                            '失败数量': 0,
                                        })
                        
                        self._mark_items_completed(list(batch))
                            
                    # 触发缓存刷新和检查点保存
                    self._flush_buffer()
                    
                except Exception as e:
                    self.failed_tasks += 1
                    log.error(f"[{self.task_type}] Batch failed: {batch}, Error: {e}")
                    # 也是一种推进
                    self._update_task_db_status('running', error_message=str(e))
                
                # 简单的流控，避免过快
                time.sleep(1)

            # 5. 完成
            return self._finalize_crawl('completed')
            
        except CrawlerInterrupted:
            log.warning(f"[{self.task_type}] 任务被用户或系统中断")
            return self._finalize_crawl('cancelled', "Task interrupted")
        except Exception as e:
            log.error(f"[{self.task_type}] Critical Error: {e}")
            return self._finalize_crawl('failed', str(e))

# 单例实例
interest_profile_crawler = InterestProfileCrawler()
