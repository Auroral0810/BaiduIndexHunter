import sys
import os

# 将项目根目录添加到 python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from src.data.database import session_scope
from src.core.logger import log

def fix_task_statistics_schema():
    """
    修复 task_statistics 表缺失字段的问题
    """
    log.info("开始检查并修复数据库表结构...")
    
    # 需要添加的字段定义
    columns_to_add = [
        ("keyword", "VARCHAR(255) NULL COMMENT '关键词'"),
        ("city_code", "VARCHAR(50) NULL COMMENT '城市代码'"),
        ("city_name", "VARCHAR(100) NULL COMMENT '城市名称'"),
        ("date_range", "VARCHAR(100) NULL COMMENT '数据日期范围'"),
        ("data_type", "VARCHAR(50) NULL COMMENT '数据类型'"),
        ("item_count", "INT NOT NULL DEFAULT 0 COMMENT '数据项数量'"),
        ("success_count", "INT NOT NULL DEFAULT 0 COMMENT '成功数量'"),
        ("fail_count", "INT NOT NULL DEFAULT 0 COMMENT '失败数量'"),
        ("avg_value", "FLOAT NULL COMMENT '平均值'"),
        ("max_value", "FLOAT NULL COMMENT '最大值'"),
        ("min_value", "FLOAT NULL COMMENT '最小值'"),
        ("sum_value", "FLOAT NULL COMMENT '总和'"),
        ("extra_data", "TEXT NULL COMMENT '额外数据(JSON)'"),
        ("create_time", "DATETIME NULL COMMENT '创建时间'")
    ]
    
    with session_scope() as session:
        # 1. 检查表是否存在
        try:
            session.exec(text("DESCRIBE task_statistics"))
        except Exception as e:
            log.error(f"表 task_statistics 不存在? {e}")
            return

        # 2. 获取现有列
        existing_columns = []
        try:
            result = session.exec(text("SHOW COLUMNS FROM task_statistics")).all()
            existing_columns = [row[0] for row in result]
            log.info(f"现有列: {existing_columns}")
        except Exception as e:
            log.error(f"无法获取列信息: {e}")
            return

        # 3. 添加缺失列
        for col_name, col_def in columns_to_add:
            if col_name not in existing_columns:
                try:
                    alter_sql = f"ALTER TABLE task_statistics ADD COLUMN {col_name} {col_def}"
                    log.info(f"正在添加列: {col_name} -> {alter_sql}")
                    session.exec(text(alter_sql))
                    session.commit() # 每次添加提交一次，防止错误的语法导致回滚
                    log.info(f"列 {col_name} 添加成功")
                except Exception as e:
                    log.error(f"添加列 {col_name} 失败: {e}")
            else:
                log.info(f"列 {col_name} 已存在，跳过")

    log.info("数据库表结构修复完成")

if __name__ == "__main__":
    fix_task_statistics_schema()
