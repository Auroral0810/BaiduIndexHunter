"""
配置仓储类
处理系统配置的数据库操作
"""
from typing import List, Optional, Any, Dict
from sqlmodel import select
from src.data.database import session_scope
from src.data.repositories.base_repository import BaseRepository
from src.data.models.config import SystemConfigModel
from sqlalchemy import func
from sqlalchemy.dialects.mysql import insert as mysql_insert

class ConfigRepository(BaseRepository[SystemConfigModel]):
    def __init__(self):
        super().__init__(SystemConfigModel)

    def get_by_key(self, key: str) -> Optional[SystemConfigModel]:
        """根据配置键获取配置"""
        with session_scope() as session:
            statement = select(SystemConfigModel).where(SystemConfigModel.config_key == key)
            return session.exec(statement).first()

    def set_config(self, key: str, value: str) -> None:
        """
        设置配置项 (Insert or Update)
        由于 SQLModel 默认不支持 ON DUPLICATE KEY UPDATE，这里使用 SQLAlchemy 的方言特性
        """
        with session_scope() as session:
            # 使用 MySQL 特有的 UPSERT 语法
            insert_stmt = mysql_insert(SystemConfigModel.__table__).values(
                config_key=key,
                config_value=value,
                description="" # 默认为空
            )
            on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
                config_value=insert_stmt.inserted.config_value,
                update_time=func.now()
            )
            session.exec(on_duplicate_key_stmt)
            session.commit()

    def get_all_as_dict(self) -> Dict[str, str]:
        """获取所有配置并返回字典格式"""
        with session_scope() as session:
            statement = select(SystemConfigModel)
            results = session.exec(statement).all()
            # 在会话关闭前提取数据，防止 DetachedInstanceError
            return {c.config_key: c.config_value for c in results}

    def delete_by_key(self, key: str) -> bool:
        """根据键删除配置"""
        with session_scope() as session:
            statement = select(SystemConfigModel).where(SystemConfigModel.config_key == key)
            results = session.exec(statement).all()
            if not results:
                return False
            for obj in results:
                session.delete(obj)
            session.commit()
            return True


# 全局单例
config_repo = ConfigRepository()
