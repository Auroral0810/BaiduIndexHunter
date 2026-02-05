"""
数据库连接配置模块 (SQLModel/SQLAlchemy)
"""
from typing import Generator
from sqlmodel import create_engine, Session, SQLModel
from contextlib import contextmanager

from src.core.config import MYSQL_CONFIG

# 构建数据库连接 URL
# 格式: mysql+pymysql://user:password@host:port/dbname?charset=utf8mb4
DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_CONFIG['user']}:{MYSQL_CONFIG['password']}"
    f"@{MYSQL_CONFIG['host']}:{MYSQL_CONFIG.get('port', 3306)}/{MYSQL_CONFIG['db']}"
    f"?charset={MYSQL_CONFIG.get('charset', 'utf8mb4')}"
)

# 创建数据库引擎
# pool_recycle=3600: 每小时回收连接，防止 MySQL 自动断开
# echo=False: 生产环境关闭 SQL 日志，调试时可开启
engine = create_engine(
    DATABASE_URL, 
    echo=False, 
    pool_recycle=3600,
    pool_pre_ping=True  # 每次获取连接前 ping 一下，防止连接断开错误
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
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
