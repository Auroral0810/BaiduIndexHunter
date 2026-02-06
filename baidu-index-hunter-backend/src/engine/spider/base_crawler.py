"""
基础爬虫抽象类 (BaseCrawler)
通过提取公共逻辑（信号处理、检查点、任务生成等）来减少样板代码。
"""
import os
import sys
import json
import signal
import threading
import pandas as pd
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional, Any, Set, Tuple
from src.core.logger import log
from src.services.storage_service import storage_service
from src.services.cookie_rotator import cookie_rotator
from src.core.config import BAIDU_INDEX_API, OUTPUT_DIR
from src.engine.crypto.cipher_generator import cipher_text_generator
import pickle
import traceback

class BaseCrawler:
    """所有百度指数爬虫的基类"""
    
    def __init__(self, task_type: str = "unknown"):
        self.task_type = task_type
        self.task_id = None
        self.output_path = None
        self.checkpoint_path = None
        self.start_time = None
        self.output_files = []
        
        # 缓存与锁
        self.data_cache = []
        self.stats_cache = []
        self.cache_limit = 1000
        self.task_lock = threading.Lock()
        self.save_lock = threading.Lock()
        
        # 进度统计
        self.total_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.completed_keywords = set()
        self.failed_keywords = set()
        
        self.cookie_rotator = cookie_rotator
        self.setup_signal_handlers()

    def _prepare_initial_state(self):
        """初始化进度监控变量（新任务开始前调用）"""
        self.completed_keywords = set()
        self.failed_keywords = set()
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.start_time = None
        self.output_files = []
        self.data_cache = []
        self.stats_cache = []

    # --- 基础设施 (Infrastructure) ---

    def setup_signal_handlers(self):
        """设置信号处理器以捕获中断"""
        signal.signal(signal.SIGINT, self.handle_exit)
        signal.signal(signal.SIGTERM, self.handle_exit)

    def handle_exit(self, signum, frame):
        """处理退出信号，保存数据和检查点"""
        log.info(f"[{self.task_type}] 接收到退出信号，正在保存数据...")
        self._flush_buffer(force=True)
        log.info(f"数据和检查点已保存。任务ID: {self.task_id}")
        sys.exit(0)

    def _generate_task_id(self):
        """生成唯一的任务ID"""
        import uuid
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        random_str = uuid.uuid4().hex[:8]
        return f"{timestamp}_{random_str}"

    # --- 数据库与统计 (DB & Stats) ---

    def _update_task_db_status(self, status: str, progress: Optional[float] = None, error_message: Optional[str] = None):
        """更新数据库中的任务状态、进度和错误信息"""
        try:
            from src.data.repositories.task_repository import task_repo
            
            # 首次记录开始时间
            if status == 'running' and self.start_time is None:
                self.start_time = datetime.now()

            success = task_repo.update_task_progress(
                task_id=self.task_id,
                status=status,
                progress=min(float(progress or 0), 100.0) if progress is not None else None,
                completed_items=self.completed_tasks,
                failed_items=self.failed_tasks,
                total_items=self.total_tasks,
                start_time=self.start_time,
                checkpoint_path=self.checkpoint_path,
                output_files=self.output_files if self.output_files else None,
                error_message=error_message
            )
            
            if not success:
                log.error(f"DB Status Update Error: Task {self.task_id} not found")
                return

            try:
                from src.services.websocket_service import emit_task_update
                emit_task_update(self.task_id, {
                    'status': status, 
                    'progress': progress or 0,
                    'completed_items': self.completed_tasks, 
                    'failed_items': self.failed_tasks,
                    'total_items': self.total_tasks, 
                    'error_message': error_message or ""
                })
            except: pass
        except Exception as e:
            log.error(f"DB Status Update Error: {e}")

    def _update_spider_statistics(self, data_count: int):
        """更新当日爬虫抓取总量统计"""
        if data_count <= 0: return
        try:
            from src.data.repositories.statistics_repository import statistics_repo
            statistics_repo.increment_crawled_count(self.task_type, data_count)
        except Exception as e:
            log.error(f"Stats Update Error: {e}")

    # --- 输入加载 (Input Loading) ---

    def _load_keywords_from_file(self, file_path: str) -> List[str]:
        """从文件加载关键词列表"""
        if not os.path.exists(file_path):
            log.error(f"关键词文件不存在: {file_path}")
            return []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except Exception as e:
            log.error(f"加载关键词文件失败: {e}")
            return []

    def _load_cities_from_file(self, file_path: str) -> Dict[str, str]:
        """从文件加载城市代码列表 {code: name}"""
        if not os.path.exists(file_path):
            log.error(f"城市文件不存在: {file_path}")
            return {}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                cities = {}
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) >= 2:
                        cities[parts[0]] = parts[1]
                return cities
        except Exception as e:
            log.error(f"加载城市文件失败: {e}")
            return {}

    def _load_date_ranges_from_file(self, file_path: str) -> List[Dict]:
        """从文件加载日期范围列表 [{'start_date': '...', 'end_date': '...'}]"""
        if not os.path.exists(file_path):
            log.error(f"日期范围文件不存在: {file_path}")
            return []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                ranges = []
                for line in f:
                    parts = line.strip().split(',')
                    if len(parts) >= 2:
                        ranges.append({'start_date': parts[0], 'end_date': parts[1]})
                return ranges
        except Exception as e:
            log.error(f"加载日期文件失败: {e}")
            return []

    def _process_year_range(self, start_year: int, end_year: int) -> List[Tuple[str, str]]:
        """生成年份范围内的年度请求参数 (start_date, end_date)"""
        current_year = datetime.now().year
        ranges = []
        for year in range(start_year, end_year + 1):
            if year < current_year:
                ranges.append((f"{year}-01-01", f"{year}-12-31"))
            else:
                # 百度指数数据通常延迟2天，所以结束日期设为前天
                end_date = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
                ranges.append((f"{year}-01-01", end_date))
        return ranges

    # --- HTTP & Cookie Utils ---

    def _get_common_headers(self, cipher_text: str) -> Dict[str, str]:
        """获取通用的百度指数请求头"""
        return {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cipher-Text': cipher_text,
            'Referer': 'https://index.baidu.com/v2/main/index.html',
            'User-Agent': BAIDU_INDEX_API['user_agent'],
            'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
        }

    def _get_cookie_dict(self) -> Tuple[Optional[str], Optional[Dict]]:
        """通过轮换器获取可用的 Cookie"""
        account_id, cookie_dict = self.cookie_rotator.get_cookie()
        if not cookie_dict:
            log.warning(f"[{self.task_type}] 所有 Cookie 均被锁定")
            return None, None
        return account_id, cookie_dict

    def _get_cipher_text(self, keyword: str) -> str:
        """获取 Cipher-Text 参数 (通用)"""
        encoded_keyword = keyword.replace(' ', '%20')
        cipher_url = f'{BAIDU_INDEX_API["referer"]}#/trend/{encoded_keyword}?words={encoded_keyword}'
        return cipher_text_generator.generate(cipher_url)

    def _update_ab_sr_cookies(self) -> bool:
        """更新所有账号的 ab_sr cookie (通用)"""
        try:
            from src.services.cookie_service import CookieManager
            cookie_manager = CookieManager()
            result = cookie_manager.update_ab_sr_for_all_accounts()
            cookie_manager.close()
            
            if 'error' in result:
                log.error(f"[{self.task_type}] 更新 ab_sr cookie 失败: {result['error']}")
                return False
            
            self.cookie_rotator.reset_cache()
            return True
        except Exception as e:
            log.error(f"[{self.task_type}] 更新 ab_sr cookie 时出错: {e}")
            return False

    # --- 持久化与缓存 (Persistence & Caching) ---

    def _flush_buffer(self, force: bool = False):
        """将缓存数据持久化到文件并同步数据库统计"""
        with self.save_lock:
            data_to_save, stats_to_save = [], []
            with self.task_lock:
                if (force or len(self.data_cache) >= self.cache_limit) and self.data_cache:
                    data_to_save, self.data_cache = list(self.data_cache), []
                if (force or len(self.stats_cache) >= self.cache_limit) and self.stats_cache:
                    stats_to_save, self.stats_cache = list(self.stats_cache), []
            
            if not data_to_save and not stats_to_save: return
                
            try:
                if data_to_save:
                    path = os.path.join(self.output_path, f"{self.task_type}_{self.task_id}_data.csv")
                    storage_service.append_to_csv(pd.DataFrame(data_to_save), path)
                    self._update_spider_statistics(len(data_to_save))
                    if path not in self.output_files:
                        self.output_files.append(path)
                
                if stats_to_save:
                    path = os.path.join(self.output_path, f"{self.task_type}_{self.task_id}_stats.csv")
                    storage_service.append_to_csv(pd.DataFrame(stats_to_save), path)
                    if path not in self.output_files:
                        self.output_files.append(path)
                
                # 每次执行 flush 都尝试保存检查点
                self._save_global_checkpoint()
            except Exception as e:
                log.error(f"Flush Buffer Error: {e}")

    def _get_checkpoint_data(self) -> Dict:
        """获取需要持久化的检查点数据，子类可扩展"""
        return {
            'completed_keywords': list(self.completed_keywords),
            'failed_keywords': list(self.failed_keywords),
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'total_tasks': self.total_tasks,
            'task_id': self.task_id,
            'output_path': self.output_path,
            'output_files': self.output_files,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def _save_global_checkpoint(self):
        """保存检查点"""
        if not self.checkpoint_path: return
        try:
            checkpoint_data = self._get_checkpoint_data()
            storage_service.save_pickle(checkpoint_data, self.checkpoint_path)
            log.info(f"检查点已更新: {self.completed_tasks}/{self.total_tasks}")
        except Exception as e:
            log.error(f"Save Checkpoint Error: {e}")

    def _load_global_checkpoint(self, task_id: str) -> Optional[Dict]:
        """加载检查点 (通用的查找逻辑)"""
        # 尝试多个可能的检查点位置
        possible_paths = [
            os.path.join(OUTPUT_DIR, 'checkpoints', f"{self.task_type}_checkpoint_{task_id}.pkl"),
            os.path.join(OUTPUT_DIR, task_id, "checkpoint.pkl")
        ]
        
        path = None
        for p in possible_paths:
            if os.path.exists(p):
                path = p
                break
                
        if not path:
            return None
            
        try:
            data = storage_service.load_pickle(path)
            if data:
                completed_keywords = data.get('completed_keywords', [])
                self.completed_keywords = set(completed_keywords) if isinstance(completed_keywords, list) else completed_keywords
                
                failed_keywords = data.get('failed_keywords', [])
                self.failed_keywords = set(failed_keywords) if isinstance(failed_keywords, list) else failed_keywords
                
                self.completed_tasks = data.get('completed_tasks', 0)
                self.failed_tasks = data.get('failed_tasks', 0)
                self.total_tasks = data.get('total_tasks', 0)
                self.task_id = data.get('task_id')
                self.output_path = data.get('output_path')
                self.checkpoint_path = path # 记录当前使用的检查点路径
            return data
        except Exception as e:
            log.error(f"Load Checkpoint Error: {e}")
            return None

    def list_tasks(self) -> List[Dict]:
        """列出所有属于当前爬虫类型的任务及其状态"""
        checkpoint_dir = os.path.join(OUTPUT_DIR, "checkpoints")
        if not os.path.exists(checkpoint_dir):
            return []
            
        tasks = []
        pattern = f"{self.task_type}_checkpoint_"
        for file in os.listdir(checkpoint_dir):
            if file.startswith(pattern) and file.endswith(".pkl"):
                task_id = file.replace(pattern, "").replace(".pkl", "")
                checkpoint_path = os.path.join(checkpoint_dir, file)
                
                try:
                    checkpoint = storage_service.load_pickle(checkpoint_path)
                    if checkpoint:
                        completed = checkpoint.get('completed_tasks', 0)
                        total = checkpoint.get('total_tasks', 0)
                        tasks.append({
                            'task_id': task_id,
                            'completed': completed,
                            'total': total,
                            'progress': f"{(completed/total*100):.2f}%" if total > 0 else "0%",
                            'update_time': checkpoint.get('update_time', 'unknown')
                        })
                except: pass
        return tasks

    def resume_task(self, task_id: str) -> bool:
        """通用任务恢复流程"""
        log.info(f"[{self.task_type}] 尝试恢复任务: {task_id}")
        
        # 检查数据库状态
        try:
            from src.data.repositories.task_repository import task_repo
            task_info = task_repo.get_by_task_id(task_id)
            if not task_info:
                log.warning(f"数据库中未找到任务 {task_id}")
                return False
                
            # 更新状态为运行中
            task_repo.update_task_progress(
                task_id=task_id,
                status='running',
                error_message=f"任务于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} 恢复执行"
            )
            
            # 这里依赖具体的子类实现 crawl(resume=True, checkpoint_task_id=task_id)
            if hasattr(self, 'crawl'):
                return self.crawl(resume=True, checkpoint_task_id=task_id)
            return False
            
        except Exception as e:
            log.error(f"[{self.task_type}] Resume Task Error: {e}")
            return False
    def _process_task(self, task_data: Any) -> Any:
        """
        [Template Method] 处理单个任务项的通用流程。
        子类应实现此方法来执行具体的业务逻辑。
        """
        raise NotImplementedError("Subclasses must implement _process_task")

    def _prepare_tasks(self, **kwargs) -> List[Any]:
        """
        [Template Method] 准备所有待抓取的任务项列表。
        """
        return []

    def _finalize_crawl(self, status: str, message: Optional[str] = None) -> bool:
        """爬取结束后的通用清理逻辑"""
        self._flush_buffer(force=True)
        self._update_task_db_status(status, progress=100, error_message=message)
        log.info(f"[{self.task_type}] 任务 {self.task_id} 结束，状态: {status}")
        return status == 'completed'
