"""
基础爬虫抽象类 (BaseCrawler)
通过提取公共逻辑（信号处理、检查点、任务生成等）来减少样板代码。
"""
import os
import sys
import json
import time
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
        self.output_format = 'csv'  # 最终输出格式（爬取时始终用 CSV，结束后转换）
        self.output_name = None     # 自定义文件名前缀（为空时使用 {task_type}_{task_id}）
        self.custom_output_dir = None  # 每任务自定义输出目录（为空时使用全局配置）
        
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
        
        # 进度报告器状态（控制输出频率，\r 覆盖式进度条）
        self._progress_start_time = 0.0       # 会话开始时间（延迟初始化）
        self._session_start_done = 0          # 会话开始时已完成数（用于计算增量速度）
        self._last_report_time = 0.0
        self._last_report_percent = -1.0
        self._last_db_update_time = 0.0
        self._progress_report_interval = 5    # 秒：进度报告最小间隔
        self._progress_min_change = 0.01      # %：进度变化最小阈值
        self._db_update_interval = 5          # 秒：DB 更新最小间隔
        
        self.setup_signal_handlers()

    def _report_cookie_status(self, account_id: str, is_valid: bool, permanent: bool = False):
        """报告Cookie状态并更新统计"""
        if not is_valid:
            self.cookie_ban_count += 1
        return self.cookie_rotator.report_cookie_status(account_id, is_valid, permanent)


    def _apply_output_format(self, output_format=None, **kwargs):
        """从参数或全局配置中读取并设置输出格式"""
        if output_format and output_format in ('csv', 'excel', 'dta', 'json', 'parquet', 'sql'):
            self.output_format = output_format
        else:
            # 从全局配置读取默认格式
            try:
                from src.services.config_service import config_manager
                default_fmt = config_manager.get('output.default_format', 'csv')
                if default_fmt in ('csv', 'excel', 'dta', 'json', 'parquet', 'sql'):
                    self.output_format = default_fmt
            except Exception:
                self.output_format = 'csv'

    def _apply_output_settings(self, output_dir=None, output_name=None):
        """
        应用输出目录和文件名设置。
        
        :param output_dir: 每任务自定义输出目录（绝对路径）。为空则使用全局配置。
        :param output_name: 自定义文件名前缀。为空则使用 {task_type}_{task_id}。
        """
        # 1. 输出目录
        if output_dir and isinstance(output_dir, str) and output_dir.strip():
            self.custom_output_dir = output_dir.strip()
        
        # 2. 文件名前缀
        if output_name and isinstance(output_name, str) and output_name.strip():
            self.output_name = output_name.strip()

    def _get_output_base_dir(self) -> str:
        """
        获取输出基础目录。
        优先级：每任务自定义 > 全局配置 output.default_dir > 硬编码 OUTPUT_DIR。
        """
        # 1. 每任务自定义
        if self.custom_output_dir:
            return self.custom_output_dir
        
        # 2. 全局配置
        try:
            from src.services.config_service import config_manager
            config_dir = config_manager.get('output.default_dir')
            if config_dir and isinstance(config_dir, str) and config_dir.strip():
                return config_dir.strip()
        except Exception:
            pass
        
        # 3. 默认
        return OUTPUT_DIR

    def _get_file_prefix(self) -> str:
        """
        获取输出文件名前缀。
        如果设置了自定义 output_name 则使用，否则使用默认 {task_type}_{task_id}。
        """
        return self.output_name or f"{self.task_type}_{self.task_id}"

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
        # 重置进度报告器（延迟初始化，首次 _maybe_report_progress 时设置实际起始时间）
        self._progress_start_time = 0.0
        self._session_start_done = 0
        self._last_report_time = 0.0
        self._last_report_percent = -1.0
        self._last_db_update_time = 0.0

    def _setup_output_paths(self, task_type_subdir: str = None):
        """
        统一设置输出目录和检查点路径。所有爬虫子类在非 resume 模式下调用此方法。
        
        :param task_type_subdir: 任务类型子目录名（默认使用 self.task_type）
        """
        subdir = task_type_subdir or self.task_type
        base_dir = self._get_output_base_dir()
        self.output_path = os.path.join(base_dir, subdir, self.task_id)
        os.makedirs(self.output_path, exist_ok=True)
        
        # 检查点始终放在默认 OUTPUT_DIR 下（避免检查点散落到用户自定义路径）
        self.checkpoint_path = os.path.join(OUTPUT_DIR, 'checkpoints', f"{self.task_type}_checkpoint_{self.task_id}.db")
        os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)
        self._init_progress_manager(self.checkpoint_path)

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
        self._finish_progress_bar()
        log.info(f"[{self.task_type}] 接收到退出信号，正在保存数据并强制退出...")
        self.is_running = False # 设置停止标志
        self._flush_buffer(force=True)
        if self.progress_manager:
            self.progress_manager.close()
        log.info(f"数据和检查点已保存。任务ID: {self.task_id}")
        # 使用 os._exit(1) 确保在多线程环境下也能强制终止终端
        import os
        os._exit(1)

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
                # 如果更新失败（任务不存在），尝试创建任务
                log.warning(f"Task {self.task_id} not found in DB, creating it now...")
                from src.data.models.task import SpiderTaskModel
                new_task = SpiderTaskModel(
                    task_id=self.task_id,
                    task_type=self.task_type,
                    task_name=f"{self.task_type}_{self.task_id}",
                    status=status,
                    create_time=datetime.now(),
                    update_time=datetime.now()
                )
                task_repo.add_task(new_task)
                
                # 再次尝试更新 (以应用进度和其他详细信息)
                task_repo.update_task_progress(
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
                
                file_prefix = self._get_file_prefix()
                
                if data_to_save:
                    path = os.path.join(self.output_path, f"{file_prefix}_data.csv")
                    storage_service.append_to_csv(pd.DataFrame(data_to_save), path)
                    self._update_spider_statistics(len(data_to_save))
                    if path not in self.output_files:
                        self.output_files.append(path)
                
                if stats_to_save:
                    # 持久化到 CSV
                    path = os.path.join(self.output_path, f"{file_prefix}_stats.csv")
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
        data = {
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
        # 保存自定义输出设置（断点续爬时恢复）
        if self.output_name:
            data['output_name'] = self.output_name
        if self.custom_output_dir:
            data['custom_output_dir'] = self.custom_output_dir
        return data

    def _init_progress_manager(self, db_path: str):
        """创建或重新初始化 ProgressManager (SQLite 进度管理器)"""
        if self.progress_manager:
            self.progress_manager.close()
        self.progress_manager = ProgressManager(db_path, self.task_id)

    def _save_global_checkpoint(self):
        """
        保存检查点（静默操作，不输出日志，仅在失败时报错）。
        优先使用 ProgressManager (SQLite)，向后兼容 pkl。
        """
        if self.progress_manager:
            try:
                checkpoint_data = self._get_checkpoint_data()
                self.progress_manager.save_checkpoint(checkpoint_data)
            except Exception as e:
                log.error(f"Save Checkpoint Error: {e}")
        elif self.checkpoint_path:
            try:
                checkpoint_data = self._get_checkpoint_data()
                storage_service.save_pickle(checkpoint_data, self.checkpoint_path)
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
        
        # 恢复自定义输出设置
        if data.get('output_name'):
            self.output_name = data['output_name']
        if data.get('custom_output_dir'):
            self.custom_output_dir = data['custom_output_dir']

    def _mark_items_completed(self, keys: List[str]):
        """
        标记任务项为完成（更新内存集合 + 持久化到 SQLite + 进度报告）。
        应在 task_lock 保护下调用。
        """
        self.completed_keywords.update(keys)
        self.completed_tasks += len(keys)
        if self.progress_manager:
            self.progress_manager.mark_completed(keys)
        self._maybe_report_progress()

    def _mark_items_failed(self, keys: List[str]):
        """
        标记任务项为失败（更新内存集合 + 持久化到 SQLite + 进度报告）。
        应在 task_lock 保护下调用。
        """
        self.failed_keywords.update(keys)
        self.failed_tasks += len(keys)
        if self.progress_manager:
            self.progress_manager.mark_failed(keys)
        self._maybe_report_progress()

    # --- 进度报告 (Progress Reporting) ---

    def _calc_speed_and_eta(self, now: float, total_done: int):
        """计算基于本次会话增量的速度和 ETA"""
        elapsed = now - self._progress_start_time if self._progress_start_time > 0 else 0
        session_done = total_done - self._session_start_done
        speed = session_done / elapsed if elapsed > 0 else 0
        remaining = self.total_tasks - total_done
        eta_seconds = remaining / speed if speed > 0 else 0
        return elapsed, speed, eta_seconds

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """将秒数格式化为人类可读的时间字符串"""
        if seconds > 3600:
            return f"{seconds / 3600:.1f}h"
        elif seconds > 60:
            return f"{seconds / 60:.1f}min"
        else:
            return f"{seconds:.0f}s"

    def _maybe_report_progress(self):
        """
        检查是否应该输出进度报告（节流控制）。
        使用 \\r 覆盖式进度条，终端中始终只显示一行。
        
        触发条件（满足任一即报告）:
        - 时间条件: 距上次报告 >= 5 秒 且 进度变化 >= 0.01%
        - 100% 完成时
        """
        if self.total_tasks <= 0:
            return
        
        now = time.time()
        total_done = self.completed_tasks + self.failed_tasks
        current_percent = total_done / self.total_tasks * 100
        
        # 延迟初始化：首次调用时记录会话起始基准
        if self._progress_start_time == 0:
            self._progress_start_time = now
            self._session_start_done = total_done
        
        should_report = False
        
        # 首次报告
        if self._last_report_time == 0:
            should_report = True
        # 时间 + 进度双重条件
        elif (now - self._last_report_time >= self._progress_report_interval
              and current_percent - self._last_report_percent >= self._progress_min_change):
            should_report = True
        # 完成时强制报告
        elif current_percent >= 100 and self._last_report_percent < 100:
            should_report = True
        
        if should_report:
            self._report_progress(now, total_done, current_percent)
        
        # DB 更新节流（独立于终端报告，保持前端同步）
        if now - self._last_db_update_time >= self._db_update_interval:
            self._last_db_update_time = now
            self._update_task_db_status_with_speed('running', current_percent)

    def _report_progress(self, now: float, total_done: int, current_percent: float):
        """
        使用 \\r 覆盖终端当前行输出进度条（不产生新行）。
        
        输出示例:
        [search_index] ████████████░░░░░░░░░░░░░░░░░░ 40.20% | 52920 done, 80 fail / 131733 | 85.3/s | ETA: 15.4min | elapsed: 4.7min
        """
        elapsed, speed, eta_seconds = self._calc_speed_and_eta(now, total_done)
        eta_str = self._format_duration(eta_seconds)
        elapsed_str = self._format_duration(elapsed)
        
        # 进度条 (30 字符宽)
        bar_width = 30
        filled = int(bar_width * current_percent / 100)
        bar = chr(9608) * filled + chr(9617) * (bar_width - filled)  # █ and ░
        
        progress_line = (
            f"\r[{self.task_type}] {bar} {current_percent:.2f}% "
            f"| {self.completed_tasks} done, {self.failed_tasks} fail / {self.total_tasks} "
            f"| {speed:.1f}/s | ETA: {eta_str} | elapsed: {elapsed_str}"
        )
        
        # \r 覆盖 + \033[K 清除行尾残余字符
        sys.stdout.write(progress_line + '\033[K')
        sys.stdout.flush()
        
        # 同时推送到前端日志控制台（标记 type=progress，前端覆盖式显示）
        try:
            from src.services.websocket_service import push_system_log
            clean_msg = (
                f"[{self.task_type}] {bar} {current_percent:.2f}% "
                f"| {self.completed_tasks} done, {self.failed_tasks} fail / {self.total_tasks} "
                f"| {speed:.1f}/s | ETA: {eta_str} | elapsed: {elapsed_str}"
            )
            push_system_log(
                "INFO", clean_msg, name="Progress",
                type="progress", task_id=self.task_id or ""
            )
        except Exception:
            pass
        
        self._last_report_time = now
        self._last_report_percent = current_percent

    def _finish_progress_bar(self):
        """结束进度条行（打印换行符），以便后续日志正常输出"""
        if self._last_report_time > 0:
            sys.stdout.write('\n')
            sys.stdout.flush()

    def _update_task_db_status_with_speed(self, status: str, progress: float):
        """更新数据库状态，包含速度和 ETA 信息（通过 WebSocket 推送给前端）"""
        try:
            from src.data.repositories.task_repository import task_repo
            
            if status == 'running' and self.start_time is None:
                self.start_time = datetime.now()
            
            task_repo.update_task_progress(
                task_id=self.task_id,
                status=status,
                progress=min(float(progress), 100.0),
                completed_items=self.completed_tasks,
                failed_items=self.failed_tasks,
                total_items=self.total_tasks,
                start_time=self.start_time,
                checkpoint_path=self.checkpoint_path,
                output_files=self.output_files if self.output_files else None,
            )
            
            # WebSocket 推送增强数据（速度和 ETA 基于会话增量）
            try:
                from src.services.websocket_service import emit_task_update
                now = time.time()
                total_done = self.completed_tasks + self.failed_tasks
                _, speed, eta_seconds = self._calc_speed_and_eta(now, total_done)
                
                emit_task_update(self.task_id, {
                    'status': status,
                    'progress': round(progress, 2),
                    'completed_items': self.completed_tasks,
                    'failed_items': self.failed_tasks,
                    'total_items': self.total_tasks,
                    'speed': round(speed, 1),
                    'eta_seconds': round(eta_seconds),
                    'error_message': ''
                })
            except Exception:
                pass
        except Exception as e:
            log.error(f"DB Status Update Error: {e}")

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

    def _convert_output_files(self):
        """
        将输出文件从 CSV 转换为用户指定的格式。
        仅在 output_format != 'csv' 且任务有输出文件时执行。
        """
        if self.output_format == 'csv' or not self.output_files:
            return
        
        log.info(f"[{self.task_type}] 正在将输出文件转换为 {self.output_format.upper()} 格式...")
        converted_files = []
        for file_path in self.output_files:
            if file_path.endswith('.csv'):
                # 根据文件名推断 SQL 表名
                table_name = os.path.splitext(os.path.basename(file_path))[0]
                new_path = storage_service.convert_csv_to_format(
                    file_path, self.output_format, table_name=table_name
                )
                converted_files.append(new_path)
            else:
                converted_files.append(file_path)
        
        self.output_files = converted_files

    def _finalize_crawl(self, status: str, message: Optional[str] = None) -> bool:
        """爬取结束后的通用清理逻辑"""
        self._flush_buffer(force=True)
        
        # 格式转换（CSV → 用户指定格式）
        if status in ('completed', 'failed'):
            self._convert_output_files()
        
        # 结束覆盖式进度条（换行），然后用 log.info 输出最终汇总
        self._finish_progress_bar()
        
        now = time.time()
        total_done = self.completed_tasks + self.failed_tasks
        elapsed, speed, _ = self._calc_speed_and_eta(now, total_done)
        elapsed_str = self._format_duration(elapsed)
        
        bar = chr(9608) * 30  # 完成时满格
        log.info(
            f"[{self.task_type}] {bar} 100.00% "
            f"| {self.completed_tasks} done, {self.failed_tasks} fail / {self.total_tasks} "
            f"| avg: {speed:.1f}/s | total: {elapsed_str} | status: {status}"
        )
        
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
