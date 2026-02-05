"""
基础模型类
为所有数据模型提供通用功能，并预留 SQLAlchemy 集成接口。
"""
from datetime import datetime
from typing import Any, Dict, Type, TypeVar, Optional
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T", bound="BaseDataModel")

class BaseDataModel(BaseModel):
    """
    所有数据模型的基类
    """
    model_config = ConfigDict(
        from_attributes=True,     # 允许从类属性（如 ORM 对象）初始化
        populate_by_name=True,    # 允许通过别名赋值
        arbitrary_types_allowed=True
    )

    @classmethod
    def from_db_row(cls: Type[T], row: Dict[str, Any]) -> Optional[T]:
        """
        从数据库行（字典）创建一个模型实例
        """
        if not row:
            return None
        return cls(**row)

    def to_db_dict(self, exclude_fields: set = None) -> Dict[str, Any]:
        """
        将模型转换为数据库可用的字典（处理日期等特殊类型）
        """
        data = self.model_dump(exclude=exclude_fields)
        # 处理可能的日期格式化需求
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.strftime("%Y-%m-%d %H:%M:%S")
        return data
