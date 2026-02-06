"""
需求图谱爬虫（关键词关联关系）
"""
import time
from typing import List, Dict, Any, Optional, Union
import pandas as pd
from datetime import datetime, timedelta
from src.core.logger import log
from src.utils.decorators import retry
from src.engine.spider.base_crawler import BaseCrawler, CrawlerInterrupted
from src.services.processor_service import data_processor

class WordGraphCrawler(BaseCrawler):
    """需求图谱爬虫，负责获取百度指数的需求图谱数据"""
    
    def __init__(self):
        """初始化需求图谱爬虫"""
        super().__init__(task_type="word_graph")
        from src.core.config import BAIDU_INDEX_API
        self.word_graph_url = BAIDU_INDEX_API.get('word_graph_url', 'https://index.baidu.com/api/WordGraph/multi')
        
    def _prepare_tasks(self, keywords: List[str], datelists: List[str], **kwargs) -> List[Dict]:
        """
        准备任务：生成 (keyword, date) 的组合
        """
        tasks = []
        for keyword in keywords:
            for date in datelists:
                tasks.append({
                    'keyword': keyword,
                    'date': date
                })
        return tasks

    def _process_task(self, task_item: Dict) -> Any:
        """
        处理单个任务
        :param task_item: {'keyword': '...', 'date': '...'}
        """
        keyword = task_item['keyword']
        date = task_item['date']
        
        result = self.get_word_graph(keyword, date)
        
        if not result:
             raise Exception(f"Failed to get word graph for {keyword} at {date}")
             
        # 使用数据处理器处理
        df = data_processor.process_word_graph_data(result, keyword, date)
        
        return df

    @retry(max_retries=2)
    def get_word_graph(self, keyword: str, datelist: str) -> Optional[Dict]:
        """
        获取需求图谱数据 API 请求
        """
        try:
            account_id, cookie_dict = self._get_cookie_dict()
            if not cookie_dict:
                return None
            
            # 构造URL
            url = f'{self.word_graph_url}?wordlist[]={keyword}&datelist={datelist}'
            
            from src.utils.rate_limiter import rate_limiter
            rate_limiter.wait()
            
            import requests
            headers = self._get_common_headers("")
            headers['Referer'] = self.word_graph_url
            
            log.info(f"[{self.task_type}] Requesting: {keyword} @ {datelist}")
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

    def crawl(self, keywords: Union[List[str], str], 
              datelists: Optional[List[str]] = None, 
              start_date: Optional[str] = None, 
              end_date: Optional[str] = None, 
              **kwargs):
        """
        执行爬取任务
        """
        if isinstance(keywords, str):
            keywords = [keywords]
            
        # 生成日期列表
        if start_date and end_date:
            try:
                s_date = datetime.strptime(start_date, "%Y%m%d")
                e_date = datetime.strptime(end_date, "%Y%m%d")
                datelists = []
                current_date = s_date
                while current_date <= e_date:
                    datelists.append(current_date.strftime("%Y%m%d"))
                    current_date += timedelta(days=7) # WordGraph 也可以是一段时间，但这里按周？参考旧逻辑
            except Exception as e:
                log.error(f"日期解析失败: {e}")
                datelists = []
        
        if not datelists:
            datelists = [] # 或者报错?
            
        if isinstance(datelists, str):
            datelists = [datelists]

        # 从 kwargs 中提取参数，防止 UnboundLocalError
        resume = kwargs.get('resume', False)
        checkpoint_task_id = kwargs.get('task_id') or kwargs.get('checkpoint_task_id')

        # 1. 初始化任务
        if resume and checkpoint_task_id:
            self.task_id = checkpoint_task_id
            if not self._load_global_checkpoint(checkpoint_task_id):
                log.warning(f"Failed to load checkpoint {checkpoint_task_id}, creating new task.")
                self.task_id = self._generate_task_id()
                self._prepare_initial_state()
                resume = False
        else:
            self.task_id = kwargs.get('task_id') or self._generate_task_id()
            self._prepare_initial_state()

        import os
        from src.core.config import OUTPUT_DIR
        self.output_path = os.path.join(OUTPUT_DIR, "word_graph", self.task_id)
        os.makedirs(self.output_path, exist_ok=True)
        self.checkpoint_path = os.path.join(OUTPUT_DIR, "checkpoints", f"{self.task_type}_checkpoint_{self.task_id}.db")
        self._init_progress_manager(self.checkpoint_path)
        
        # 2. 准备任务
        tasks = self._prepare_tasks(keywords, datelists)
        self.total_tasks = len(tasks)
        
        # 3. 恢复检查点
        start_index = self.completed_tasks
        
        self._update_task_db_status('running', 0)
        
        try:
            for i in range(start_index, len(tasks)):
                self.check_running()
                task_item = tasks[i]
                try:
                    df = self._process_task(task_item)
                    
                    with self.task_lock:
                        if df is not None and not df.empty:
                            self.data_cache.extend(df.to_dict('records'))
                        
                        self._mark_items_completed([f"{task_item['keyword']}_{task_item['date']}"])
                    
                    self._flush_buffer()
                    
                    progress = (self.completed_tasks / self.total_tasks) * 100
                    self._update_task_db_status('running', progress)
                    
                except Exception as e:
                    self.failed_tasks += 1
                    log.error(f"[{self.task_type}] Task failed: {task_item}, Error: {e}")
                    self._update_task_db_status('running', error_message=str(e))
                
                time.sleep(1)

            return self._finalize_crawl('completed')
            
        except CrawlerInterrupted:
            log.warning(f"[{self.task_type}] 任务被用户或系统中断")
            return self._finalize_crawl('cancelled', "Task interrupted")
        except Exception as e:
            log.error(f"[{self.task_type}] Critical Error: {e}")
            return self._finalize_crawl('failed', str(e))

word_graph_crawler = WordGraphCrawler()
