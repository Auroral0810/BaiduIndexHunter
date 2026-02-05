"""
基础仓储类 (Repository Pattern)
提供基于 SQLModel 的通用 CRUD 操作
"""
from typing import Type, TypeVar, Generic, Optional, List, Any, Union, Dict
from sqlmodel import Session, select, func
from src.data.database import session_scope
from src.data.models.base import BaseDataModel

# 定义泛型 T，必须是 BaseDataModel 的子类
T = TypeVar("T", bound=BaseDataModel)

class BaseRepository(Generic[T]):
    def __init__(self, model_cls: Type[T]):
        self.model_cls = model_cls

    def add(self, model: T) -> T:
        """添加新记录"""
        with session_scope() as session:
            session.add(model)
            session.commit()
            session.refresh(model)
            return model

    def add_all(self, models: List[T]) -> List[T]:
        """批量添加记录"""
        with session_scope() as session:
            session.add_all(models)
            session.commit()
            for model in models:
                session.refresh(model)
            return models

    def get(self, id: Any) -> Optional[T]:
        """根据主键获取记录"""
        with session_scope() as session:
            return session.get(self.model_cls, id)

    def update(self, id: Any, data: Union[Dict, T]) -> Optional[T]:
        """更新记录"""
        with session_scope() as session:
            db_obj = session.get(self.model_cls, id)
            if not db_obj:
                return None
            
            obj_data = data if isinstance(data, dict) else data.model_dump(exclude_unset=True)
            
            for key, value in obj_data.items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)
            
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
            return db_obj

    def delete(self, id: Any) -> bool:
        """删除记录"""
        with session_scope() as session:
            db_obj = session.get(self.model_cls, id)
            if not db_obj:
                return False
            session.delete(db_obj)
            session.commit()
            return True

    def list_all(self) -> List[T]:
        """获取所有记录"""
        with session_scope() as session:
            statement = select(self.model_cls)
            return session.exec(statement).all()

    def count(self) -> int:
        """获取总记录数"""
        with session_scope() as session:
            statement = select(func.count()).select_from(self.model_cls)
            return session.exec(statement).one()
