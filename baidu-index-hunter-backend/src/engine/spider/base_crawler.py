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
from src.services.progress_manager import ProgressManager
from src.core.config import BAIDU_INDEX_API, OUTPUT_DIR
from src.engine.crypto.cipher_generator import cipher_text_generator
import traceback

class CrawlerInterrupted(Exception):
    """爬虫任务被中断异常"""
    pass

class BaseCrawler:
    """所有百度指数爬虫的基类"""
    
    def __init__(self, task_type: str = "unknown"):
        self.task_type = task_type
        self.task_id = None
        self.output_path = None
        self.checkpoint_path = None
        self.start_time = None
        self.output_files = []
        
        # 进度管理器 (SQLite-based, 替代 pkl)
        self.progress_manager: Optional[ProgressManager] = None
        
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
        self.is_running = True # 运行状态标志
        
        # Cookie 统计
        self.cookie_usage_count = 0
        self.cookie_ban_count = 0
        
        self.setup_signal_handlers()

    def _report_cookie_status(self, account_id: str, is_valid: bool, permanent: bool = False):
        """报告Cookie状态并更新统计"""
        if not is_valid:
            self.cookie_ban_count += 1
        return self.cookie_rotator.report_cookie_status(account_id, is_valid, permanent)


    def _prepare_initial_state(self):
        """初始化进度监控变量（新任务开始前调用）"""
        # 关闭旧的进度管理器
        if self.progress_manager:
            self.progress_manager.close()
            self.progress_manager = None
        self.completed_keywords = set()
        self.failed_keywords = set()
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.start_time = None
        self.output_files = []
        self.data_cache = []
        self.stats_cache = []
        self.is_running = True

    # --- 基础设施 (Infrastructure) ---

    def setup_signal_handlers(self):
        """设置信号处理器以捕获中断"""
        # 仅在主线程中设置信号处理器
        if threading.current_thread() is not threading.main_thread():
            return
            
        # 在测试环境下跳过信号处理器设置，避免干扰测试框架
        if 'pytest' in sys.modules or os.environ.get('PYTEST_CURRENT_TEST'):
            return

        try:
            signal.signal(signal.SIGINT, self.handle_exit)
            signal.signal(signal.SIGTERM, self.handle_exit)
        except (ValueError, RuntimeError):
            # 在某些非主线程或受限环境下可能无法设置信号
            pass

    def handle_exit(self, signum, frame):
        """处理退出信号，保存数据和检查点"""
        log.info(f"[{self.task_type}] 接收到退出信号，正在保存数据...")
        self.is_running = False # 设置停止标志
        self._flush_buffer(force=True)
        if self.progress_manager:
            self.progress_manager.close()
        log.info(f"数据和检查点已保存。任务ID: {self.task_id}")
        sys.exit(0)

    def check_running(self):
        """检查爬虫是否应当继续运行，如果已停止则抛出异常"""
        if not self.is_running:
            log.info(f"[{self.task_type}] 检查到停止信号，中断执行。任务ID: {self.task_id}")
            raise CrawlerInterrupted("Task cancelled or interrupted")

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

        return account_id, cookie_dict

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

    def _get_cookie_dict(self) -> Tuple[Optional[str], Optional[Dict]]:
        """通过轮换器获取可用的 Cookie"""
        account_id, cookie_dict = self.cookie_rotator.get_cookie()
        if not cookie_dict:
            log.warning(f"[{self.task_type}] 所有 Cookie 均被锁定")
            return None, None
        self.cookie_usage_count += 1
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
                if (force or len(self.stats_cache) >= 1) and self.stats_cache: # 统计数据及时入库
                    stats_to_save, self.stats_cache = list(self.stats_cache), []
            
            if not data_to_save and not stats_to_save: return
                
            try:
                from src.data.repositories.statistics_repository import statistics_repo
                
                if data_to_save:
                    path = os.path.join(self.output_path, f"{self.task_type}_{self.task_id}_data.csv")
                    storage_service.append_to_csv(pd.DataFrame(data_to_save), path)
                    self._update_spider_statistics(len(data_to_save))
                    if path not in self.output_files:
                        self.output_files.append(path)
                
                if stats_to_save:
                    # 持久化到 CSV
                    path = os.path.join(self.output_path, f"{self.task_type}_{self.task_id}_stats.csv")
                    storage_service.append_to_csv(pd.DataFrame(stats_to_save), path)
                    if path not in self.output_files:
                        self.output_files.append(path)
                    
                    # 持久化到数据库
                    for item in stats_to_save:
                        item['task_id'] = self.task_id # 确保有 task_id
                    statistics_repo.save_task_statistics_batch(stats_to_save)
                
                # 每次执行 flush 都尝试保存检查点
                self._save_global_checkpoint()
            except Exception as e:
                log.error(f"Flush Buffer Error: {e}")

    def _add_task_log(self, level: str, message: str, details: Optional[Dict] = None):
        """记录任务日志到数据库"""
        try:
            from src.data.repositories.log_repository import log_repo
            log_repo.add_log(self.task_id, level, message, details)
        except Exception as e:
            log.error(f"Add Task Log Error: {e}")

    def _get_checkpoint_data(self) -> Dict:
        """获取需要持久化的检查点数据，子类可扩展"""
        return {
            'completed_keywords': list(self.completed_keywords),
            'failed_keywords': list(self.failed_keywords),
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'total_tasks': self.total_tasks,
            'task_id': self.task_id,
            'task_type': self.task_type,
            'output_path': self.output_path,
            'output_files': self.output_files,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S') if self.start_time else None,
            'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

    def _init_progress_manager(self, db_path: str):
        """创建或重新初始化 ProgressManager (SQLite 进度管理器)"""
        if self.progress_manager:
            self.progress_manager.close()
        self.progress_manager = ProgressManager(db_path, self.task_id)

    def _save_global_checkpoint(self):
        """
        保存检查点。
        优先使用 ProgressManager (SQLite)，向后兼容 pkl。
        """
        if self.progress_manager:
            # 新方式: SQLite
            try:
                checkpoint_data = self._get_checkpoint_data()
                self.progress_manager.save_checkpoint(checkpoint_data)
                log.info(f"[{self.task_type}] 检查点已保存: {self.completed_tasks}/{self.total_tasks}")
            except Exception as e:
                log.error(f"Save Checkpoint Error: {e}")
        elif self.checkpoint_path:
            # 旧方式: Pickle (兼容未迁移的爬虫)
            try:
                checkpoint_data = self._get_checkpoint_data()
                storage_service.save_pickle(checkpoint_data, self.checkpoint_path)
                log.info(f"[{self.task_type}] 检查点已保存(pkl): {self.completed_tasks}/{self.total_tasks}")
            except Exception as e:
                log.error(f"Save Checkpoint Error: {e}")

    def _load_global_checkpoint(self, task_id: str) -> Optional[Dict]:
        """
        加载检查点 (SQLite 优先, pkl 兜底并自动迁移)。
        
        查找顺序:
        1. .db 文件 (新格式, SQLite)
        2. .pkl 文件 (旧格式, 自动迁移到 SQLite)
        """
        # --- 1. 检查 .db 文件 (新格式) ---
        db_paths = [
            os.path.join(OUTPUT_DIR, 'checkpoints', f"{self.task_type}_checkpoint_{task_id}.db"),
        ]
        
        for db_path in db_paths:
            if os.path.exists(db_path):
                try:
                    self._init_progress_manager(db_path)
                    data = self.progress_manager.load_checkpoint()
                    if data:
                        self._restore_from_checkpoint(data)
                        self.checkpoint_path = db_path
                        log.info(f"[{self.task_type}] 从 SQLite 检查点恢复: {self.completed_tasks} 已完成, {self.failed_tasks} 失败")
                        return data
                except Exception as e:
                    log.error(f"Load SQLite Checkpoint Error: {e}")
        
        # --- 2. 检查 .pkl 文件 (旧格式, 自动迁移) ---
        pkl_paths = [
            os.path.join(OUTPUT_DIR, 'checkpoints', f"{self.task_type}_checkpoint_{task_id}.pkl"),
            os.path.join(OUTPUT_DIR, task_id, "checkpoint.pkl")
        ]
        
        for pkl_path in pkl_paths:
            if os.path.exists(pkl_path):
                try:
                    data = storage_service.load_pickle(pkl_path)
                    if data:
                        log.info(f"[{self.task_type}] 发现旧 pkl 检查点，自动迁移到 SQLite...")
                        
                        # 创建新的 .db 并迁移数据
                        new_db_path = os.path.join(
                            OUTPUT_DIR, 'checkpoints', 
                            f"{self.task_type}_checkpoint_{task_id}.db"
                        )
                        self._init_progress_manager(new_db_path)
                        self.progress_manager.migrate_from_dict(data)
                        
                        # 恢复实例状态
                        self._restore_from_checkpoint(data)
                        self.checkpoint_path = new_db_path
                        
                        # 将旧 pkl 重命名为备份
                        backup_path = pkl_path + '.migrated'
                        try:
                            os.rename(pkl_path, backup_path)
                            log.info(f"旧 pkl 检查点已备份为: {backup_path}")
                        except Exception:
                            pass
                        
                        return data
                except Exception as e:
                    log.error(f"Load/Migrate pkl Checkpoint Error: {e}")
        
        return None

    def _restore_from_checkpoint(self, data: Dict):
        """从检查点字典恢复实例状态（通用逻辑，子类可调用 super 后提取额外字段）"""
        completed_keywords = data.get('completed_keywords', [])
        self.completed_keywords = set(completed_keywords) if isinstance(completed_keywords, list) else completed_keywords
        
        failed_keywords = data.get('failed_keywords', [])
        self.failed_keywords = set(failed_keywords) if isinstance(failed_keywords, list) else failed_keywords
        
        # 使用实际集合大小，比存储的计数器更准确（防止崩溃导致计数器不一致）
        self.completed_tasks = len(self.completed_keywords)
        self.failed_tasks = len(self.failed_keywords)
        self.total_tasks = data.get('total_tasks', 0)
        self.task_id = data.get('task_id') or self.task_id
        self.output_path = data.get('output_path')
        self.output_files = data.get('output_files', [])
        
        # 恢复开始时间
        start_time_str = data.get('start_time')
        if start_time_str:
            try:
                self.start_time = datetime.strptime(start_time_str, '%Y-%m-%d %H:%M:%S')
            except Exception:
                pass
        elif data.get('update_time'):  # 兼容旧版或兜底
            try:
                self.start_time = datetime.strptime(data.get('update_time'), '%Y-%m-%d %H:%M:%S')
            except Exception:
                pass

    def _mark_items_completed(self, keys: List[str]):
        """
        标记任务项为完成（更新内存集合 + 持久化到 SQLite）。
        应在 task_lock 保护下调用。
        """
        self.completed_keywords.update(keys)
        self.completed_tasks += len(keys)
        if self.progress_manager:
            self.progress_manager.mark_completed(keys)

    def _mark_items_failed(self, keys: List[str]):
        """
        标记任务项为失败（更新内存集合 + 持久化到 SQLite）。
        应在 task_lock 保护下调用。
        """
        self.failed_keywords.update(keys)
        self.failed_tasks += len(keys)
        if self.progress_manager:
            self.progress_manager.mark_failed(keys)

    def list_tasks(self) -> List[Dict]:
        """列出所有属于当前爬虫类型的任务及其状态（支持 .db 和 .pkl 格式）"""
        checkpoint_dir = os.path.join(OUTPUT_DIR, "checkpoints")
        if not os.path.exists(checkpoint_dir):
            return []
            
        tasks = []
        seen_task_ids = set()
        pattern = f"{self.task_type}_checkpoint_"
        
        for file in os.listdir(checkpoint_dir):
            if not file.startswith(pattern):
                continue
            
            # 支持 .db (新格式) 和 .pkl (旧格式)
            if file.endswith(".db"):
                task_id = file.replace(pattern, "").replace(".db", "")
                if task_id in seen_task_ids:
                    continue
                seen_task_ids.add(task_id)
                checkpoint_path = os.path.join(checkpoint_dir, file)
                try:
                    pm = ProgressManager(checkpoint_path, task_id)
                    checkpoint = pm.load_checkpoint()
                    pm.close()
                    if checkpoint:
                        completed = len(checkpoint.get('completed_keywords', []))
                        total = checkpoint.get('total_tasks', 0)
                        tasks.append({
                            'task_id': task_id,
                            'completed': completed,
                            'total': total,
                            'progress': f"{(completed/total*100):.2f}%" if total > 0 else "0%",
                            'update_time': checkpoint.get('update_time', 'unknown'),
                            'format': 'sqlite'
                        })
                except Exception:
                    pass
            elif file.endswith(".pkl"):
                task_id = file.replace(pattern, "").replace(".pkl", "")
                if task_id in seen_task_ids:
                    continue
                seen_task_ids.add(task_id)
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
                            'update_time': checkpoint.get('update_time', 'unknown'),
                            'format': 'pkl'
                        })
                except Exception:
                    pass
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
        
        # 关闭进度管理器（确保所有数据已持久化）
        if self.progress_manager:
            self.progress_manager.close()
            self.progress_manager = None
        
        # 更新数据库中的任务状态
        self._update_task_db_status(status, progress=100, error_message=message)
        
        # 记录汇总统计到 spider_statistics
        try:
            from src.data.repositories.statistics_repository import statistics_repo
            duration = 0
            if self.start_time:
                duration = (datetime.now() - self.start_time).total_seconds()
            
            # 这里的 total_delta 等是相对于该任务的
            statistics_repo.update_spider_summary(
                task_type=self.task_type,
                total_delta=1, # 一个任务实例
                completed_delta=1 if status == 'completed' else 0,
                failed_delta=1 if status == 'failed' else 0,
                duration=duration,
                cookie_usage=self.cookie_usage_count, 
                cookie_ban_count=self.cookie_ban_count
            )
        except Exception as e:
            log.error(f"Finalize Crawl Stats Error: {e}")

        # 记录任务结束日志
        log_msg = f"任务 {self.task_id} 结束，状态: {status}"
        if message:
            log_msg += f", 消息: {message}"
        self._add_task_log('info' if status == 'completed' else 'warning', log_msg)
        
        log.info(f"[{self.task_type}] {log_msg}")
        return status == 'completed'
