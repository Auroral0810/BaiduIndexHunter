"""
数据库连接配置模块 (SQLModel/SQLAlchemy)
使用 SQLAlchemy QueuePool 连接池实现高效的数据库连接管理
"""
import os
from typing import Generator
from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager

from src.core.config import MYSQL_CONFIG
from src.core.logger import log

# 构建数据库连接 URL
# 格式: mysql+pymysql://user:password@host:port/dbname?charset=utf8mb4
DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}"
    f"@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG.get('port', 3306)}/{MYSQL_CONFIG['db']}"
    f"?charset={MYSQL_CONFIG.get('charset', 'utf8mb4')}"
)

# ============================================================
# 连接池配置参数 (可通过环境变量覆盖)
# ============================================================

# pool_size: 连接池保持的固定连接数，默认 10
POOL_SIZE = int(os.getenv('DB_POOL_SIZE', 10))

# max_overflow: 超出 pool_size 后允许临时创建的额外连接数，默认 20
# 总最大连接数 = pool_size + max_overflow = 30
MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', 20))

# pool_timeout: 等待获取连接的超时时间(秒)，默认 30 秒
POOL_TIMEOUT = int(os.getenv('DB_POOL_TIMEOUT', 30))

# pool_recycle: 连接回收时间(秒)，防止 MySQL 自动断开空闲连接
# MySQL 默认 wait_timeout=28800(8小时)，这里设置为 1 小时以确保连接活跃
POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', 3600))

# pool_pre_ping: 每次获取连接前检测连接有效性，防止使用已断开的连接
POOL_PRE_PING = os.getenv('DB_POOL_PRE_PING', 'true').lower() == 'true'

# echo: 是否打印 SQL 语句（调试用）
SQL_ECHO = os.getenv('DB_SQL_ECHO', 'false').lower() == 'true'

# ============================================================
# 创建数据库引擎
# ============================================================
engine = create_engine(
    DATABASE_URL,
    echo=SQL_ECHO,
    poolclass=QueuePool,          # 使用队列池，支持高并发
    pool_size=POOL_SIZE,          # 连接池大小
    max_overflow=MAX_OVERFLOW,    # 最大溢出连接数
    pool_timeout=POOL_TIMEOUT,    # 获取连接超时
    pool_recycle=POOL_RECYCLE,    # 连接回收时间
    pool_pre_ping=POOL_PRE_PING,  # 连接有效性检测
)

def init_db():
    """
    初始化数据库表结构 (如果需要)
    注意：在现有项目中，表结构通常由 SQL 脚本管理，此函数仅用于测试或新表生成
    """
    SQLModel.metadata.create_all(engine)

def get_session() -> Generator[Session, None, None]:
    """
    获取数据库会话 (Dependency Injection 用)
    用法: with get_session() as session: ...
    """
    with Session(engine) as session:
        yield session

@contextmanager
def session_scope():
    """
    上下文管理器形式的 Session 获取
    用法: with session_scope() as session: ...
    """
    session = Session(engine, expire_on_commit=False)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
