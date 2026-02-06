"""
基于 SQLite 的爬虫任务进度管理器

替代 pkl 文件方案，提供:
- 崩溃安全：SQLite 事务保证 ACID，WAL 模式写入不丢数据
- 并发友好：WAL 模式支持多线程并发读写
- 增量写入：每次只 INSERT 新完成的项，无需重写整个文件
- 可读性：可用任何 SQLite 工具（DB Browser, sqlite3 CLI）查看进度

文件大小估算（300 关键词 × 400 城市 × 13 年 = 1,560,000 任务）:
- 每条 task_key 约 130 字节（含索引开销）
- 总文件约 150-200MB，单机完全可控

设计:
- checkpoint_meta 表: 1 行/任务，存储统计信息和配置数据
- task_items 表: N 行/任务，每个完成/失败的 task_key 一行
- 内存缓冲: 批量写入减少 I/O，可配置 batch_size
"""
import os
import sqlite3
import json
import threading
from datetime import datetime
from typing import Set, Dict, Optional, List, Any

from src.core.logger import log


class ProgressManager:
    """
    使用 SQLite (WAL 模式) 管理爬虫任务进度。
    
    核心思路:
    - 内存中维护 completed/failed 集合用于 O(1) 查找（爬虫主循环需要高速判重）
    - SQLite 作为持久层，使用批量缓冲减少 I/O 开销
    - WAL 模式允许多个工作线程同时读写，不互相阻塞
    
    使用方式:
        pm = ProgressManager("path/to/checkpoint.db", "task_id_xxx")
        # 恢复进度
        data = pm.load_checkpoint()
        # 标记完成
        pm.mark_completed(["kw1_0_2021-01-01_2021-12-31", ...])
        # 保存检查点元数据
        pm.save_checkpoint(meta_dict)
        # 结束
        pm.close()
    """
    
    def __init__(self, db_path: str, task_id: str, batch_size: int = 500):
        """
        初始化进度管理器
        
        Args:
            db_path: SQLite 数据库文件路径 (如 output/checkpoints/xxx.db)
            task_id: 任务唯一标识
            batch_size: 批量写入的缓冲区大小，达到此数量自动刷盘
        """
        self.db_path = db_path
        self.task_id = task_id
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()
        self._pending_completed: List[str] = []
        self._pending_failed: List[str] = []
        self._batch_size = batch_size
        self._closed = False
        self._init_db()
    
    def _init_db(self):
        """初始化 SQLite 数据库：创建表、设置 WAL 模式和性能参数"""
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        
        # WAL 模式：允许并发读写，写入不阻塞读取
        self._conn.execute("PRAGMA journal_mode=WAL")
        # NORMAL 同步：平衡性能和安全性（极端断电可能丢失最后几个事务）
        self._conn.execute("PRAGMA synchronous=NORMAL")
        # 增大页缓存（约 40MB），减少磁盘 I/O
        self._conn.execute("PRAGMA cache_size=-40000")
        # 临时表放内存
        self._conn.execute("PRAGMA temp_store=MEMORY")
        # 使用 4KB 页面（适合 SSD）
        self._conn.execute("PRAGMA page_size=4096")
        
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS checkpoint_meta (
                task_id TEXT PRIMARY KEY,
                task_type TEXT,
                total_tasks INTEGER DEFAULT 0,
                completed_tasks INTEGER DEFAULT 0,
                failed_tasks INTEGER DEFAULT 0,
                output_path TEXT,
                output_files TEXT,
                start_time TEXT,
                update_time TEXT,
                extra_data TEXT
            );
            
            CREATE TABLE IF NOT EXISTS task_items (
                task_id TEXT NOT NULL,
                task_key TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'completed',
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                PRIMARY KEY (task_id, task_key)
            );
            
            CREATE INDEX IF NOT EXISTS idx_task_items_status 
                ON task_items(task_id, status);
        """)
        self._conn.commit()
    
    def load_checkpoint(self) -> Optional[Dict]:
        """
        从 SQLite 加载检查点数据。
        
        Returns:
            与旧 pkl 格式兼容的字典，包含:
            - completed_keywords: List[str] - 已完成的任务键列表
            - failed_keywords: List[str] - 失败的任务键列表
            - completed_tasks, failed_tasks, total_tasks: int
            - output_path, output_files, start_time, update_time
            - extra_data 中的所有字段会被展开到顶层（如 city_dict, current_keyword_index 等）
            如果没有找到检查点数据返回 None
        """
        with self._lock:
            cursor = self._conn.execute(
                "SELECT * FROM checkpoint_meta WHERE task_id = ?",
                (self.task_id,)
            )
            row = cursor.fetchone()
            if not row:
                return None
            
            columns = [d[0] for d in cursor.description]
            meta = dict(zip(columns, row))
            
            # 加载已完成的 task_keys
            cursor = self._conn.execute(
                "SELECT task_key FROM task_items WHERE task_id = ? AND status = 'completed'",
                (self.task_id,)
            )
            completed_keywords = [r[0] for r in cursor.fetchall()]
            
            # 加载失败的 task_keys
            cursor = self._conn.execute(
                "SELECT task_key FROM task_items WHERE task_id = ? AND status = 'failed'",
                (self.task_id,)
            )
            failed_keywords = [r[0] for r in cursor.fetchall()]
            
            # 解析 output_files (JSON)
            output_files = []
            if meta.get('output_files'):
                try:
                    output_files = json.loads(meta['output_files'])
                except (json.JSONDecodeError, TypeError):
                    output_files = []
            
            # 解析 extra_data (JSON) 并展开到结果中
            extra_data = {}
            if meta.get('extra_data'):
                try:
                    extra_data = json.loads(meta['extra_data'])
                except (json.JSONDecodeError, TypeError):
                    pass
            
            # 构建与旧 pkl 格式兼容的结果字典
            result = {
                'completed_keywords': completed_keywords,
                'failed_keywords': failed_keywords,
                'completed_tasks': meta.get('completed_tasks', 0),
                'failed_tasks': meta.get('failed_tasks', 0),
                'total_tasks': meta.get('total_tasks', 0),
                'task_id': meta.get('task_id'),
                'output_path': meta.get('output_path', ''),
                'output_files': output_files,
                'start_time': meta.get('start_time'),
                'update_time': meta.get('update_time'),
            }
            
            # 展开 extra_data 到顶层（如 city_dict, current_keyword_index 等）
            result.update(extra_data)
            
            return result
    
    def mark_completed(self, keys: List[str]):
        """
        标记 task_keys 为已完成。
        
        使用批量缓冲，当缓冲区满时自动刷盘。
        线程安全，可从多个工作线程并发调用。
        
        Args:
            keys: 要标记为完成的 task_key 列表
        """
        if not keys:
            return
        with self._lock:
            self._pending_completed.extend(keys)
            if len(self._pending_completed) >= self._batch_size:
                self._flush_items()
    
    def mark_failed(self, keys: List[str]):
        """
        标记 task_keys 为失败。
        
        使用批量缓冲，当缓冲区满时自动刷盘。
        
        Args:
            keys: 要标记为失败的 task_key 列表
        """
        if not keys:
            return
        with self._lock:
            self._pending_failed.extend(keys)
            if len(self._pending_failed) >= self._batch_size:
                self._flush_items()
    
    def _flush_items(self):
        """
        将缓冲区中的 task_items 写入 SQLite。
        须在持有 _lock 的情况下调用。
        使用单个事务批量 INSERT，性能优异。
        
        INSERT OR REPLACE 确保：
        - 如果任务之前失败，现在成功 → 状态更新为 completed
        - 如果任务重试后仍然失败 → 状态保持为 failed
        """
        if not self._pending_completed and not self._pending_failed:
            return
        
        try:
            cursor = self._conn.cursor()
            
            if self._pending_completed:
                cursor.executemany(
                    "INSERT OR REPLACE INTO task_items (task_id, task_key, status) VALUES (?, ?, 'completed')",
                    [(self.task_id, key) for key in self._pending_completed]
                )
                self._pending_completed.clear()
            
            if self._pending_failed:
                cursor.executemany(
                    "INSERT OR REPLACE INTO task_items (task_id, task_key, status) VALUES (?, ?, 'failed')",
                    [(self.task_id, key) for key in self._pending_failed]
                )
                self._pending_failed.clear()
            
            self._conn.commit()
        except Exception as e:
            log.error(f"[ProgressManager] 刷盘失败: {e}")
    
    def save_checkpoint(self, meta: Dict):
        """
        保存完整检查点：先刷盘缓冲区，再更新元数据。
        
        标准字段直接存入 checkpoint_meta 表的对应列。
        其余字段（如 city_dict, current_keyword_index 等）自动序列化为 JSON 存入 extra_data 列。
        
        Args:
            meta: 检查点元数据字典。来自 BaseCrawler._get_checkpoint_data()。
        """
        with self._lock:
            # 先刷盘待写入的 task_items
            self._flush_items()
            
            # 分离标准字段和额外数据
            standard_keys = {
                'task_type', 'total_tasks', 'completed_tasks', 'failed_tasks',
                'output_path', 'output_files', 'start_time', 'update_time',
                'task_id', 'completed_keywords', 'failed_keywords'
            }
            
            extra_data = {k: v for k, v in meta.items() if k not in standard_keys}
            output_files = meta.get('output_files', [])
            
            try:
                self._conn.execute("""
                    INSERT OR REPLACE INTO checkpoint_meta 
                    (task_id, task_type, total_tasks, completed_tasks, failed_tasks,
                     output_path, output_files, start_time, update_time, extra_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.task_id,
                    meta.get('task_type', ''),
                    meta.get('total_tasks', 0),
                    meta.get('completed_tasks', 0),
                    meta.get('failed_tasks', 0),
                    meta.get('output_path', ''),
                    json.dumps(output_files, ensure_ascii=False) if isinstance(output_files, list) else (output_files or '[]'),
                    meta.get('start_time', ''),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    json.dumps(extra_data, ensure_ascii=False) if extra_data else '{}',
                ))
                self._conn.commit()
            except Exception as e:
                log.error(f"[ProgressManager] 保存检查点元数据失败: {e}")
    
    def migrate_from_dict(self, data: Dict):
        """
        从旧 pkl 格式的字典迁移数据到 SQLite。
        
        使用分批写入 + 单次提交，保证原子性：要么全部成功，要么全部失败。
        对于 1.56M 条目，迁移约需 2-5 秒。
        
        Args:
            data: 从 pkl 文件加载的检查点字典
        """
        completed = data.get('completed_keywords', [])
        if isinstance(completed, set):
            completed = list(completed)
        failed = data.get('failed_keywords', [])
        if isinstance(failed, set):
            failed = list(failed)
        
        with self._lock:
            try:
                cursor = self._conn.cursor()
                
                # 分批 INSERT 已完成项
                BATCH = 10000
                for i in range(0, len(completed), BATCH):
                    batch = completed[i:i + BATCH]
                    cursor.executemany(
                        "INSERT OR REPLACE INTO task_items (task_id, task_key, status) VALUES (?, ?, 'completed')",
                        [(self.task_id, key) for key in batch]
                    )
                
                # 分批 INSERT 失败项
                for i in range(0, len(failed), BATCH):
                    batch = failed[i:i + BATCH]
                    cursor.executemany(
                        "INSERT OR REPLACE INTO task_items (task_id, task_key, status) VALUES (?, ?, 'failed')",
                        [(self.task_id, key) for key in batch]
                    )
                
                # 保存元数据
                standard_keys = {
                    'task_type', 'total_tasks', 'completed_tasks', 'failed_tasks',
                    'output_path', 'output_files', 'start_time', 'update_time',
                    'task_id', 'completed_keywords', 'failed_keywords'
                }
                extra_data = {k: v for k, v in data.items() if k not in standard_keys}
                output_files = data.get('output_files', [])
                
                cursor.execute("""
                    INSERT OR REPLACE INTO checkpoint_meta 
                    (task_id, task_type, total_tasks, completed_tasks, failed_tasks,
                     output_path, output_files, start_time, update_time, extra_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.task_id,
                    data.get('task_type', ''),
                    data.get('total_tasks', 0),
                    data.get('completed_tasks', len(completed)),
                    data.get('failed_tasks', len(failed)),
                    data.get('output_path', ''),
                    json.dumps(output_files, ensure_ascii=False) if isinstance(output_files, list) else (output_files or '[]'),
                    data.get('start_time', ''),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    json.dumps(extra_data, ensure_ascii=False) if extra_data else '{}',
                ))
                
                # 单次提交保证原子性
                self._conn.commit()
                log.info(f"[ProgressManager] pkl 迁移完成: {len(completed)} 已完成, {len(failed)} 失败")
            except Exception as e:
                self._conn.rollback()
                log.error(f"[ProgressManager] pkl 迁移失败: {e}")
                raise
    
    def flush(self):
        """强制刷盘所有缓冲区"""
        with self._lock:
            self._flush_items()
    
    def get_stats(self) -> Dict:
        """
        获取进度统计信息
        
        Returns:
            包含已持久化和待写入数量的字典
        """
        with self._lock:
            cursor = self._conn.execute(
                "SELECT status, COUNT(*) FROM task_items WHERE task_id = ? GROUP BY status",
                (self.task_id,)
            )
            counts = dict(cursor.fetchall())
            return {
                'db_completed': counts.get('completed', 0),
                'db_failed': counts.get('failed', 0),
                'pending_completed': len(self._pending_completed),
                'pending_failed': len(self._pending_failed),
            }
    
    def close(self):
        """刷盘并关闭数据库连接"""
        if self._closed:
            return
        self._closed = True
        try:
            self.flush()
        except Exception:
            pass
        if self._conn:
            try:
                # 执行 WAL 检查点，合并 WAL 到主数据库文件
                self._conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                self._conn.close()
            except Exception:
                pass
            self._conn = None
    
    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
