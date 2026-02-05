"""
模型层功能验证脚本
验证 MySQLManager.fetch_model 能否正确将数据库行映射为 Pydantic 模型。
"""
import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from src.data.repositories.mysql_manager import mysql_manager
from src.data.models.cookie import CookieModel
from src.data.models.task import SpiderTaskModel
from src.core.logger import log

def test_cookie_mapping():
    log.info("测试 Cookie 模型映射...")
    try:
        # 查询一个可用 Cookie
        query = "SELECT * FROM cookies LIMIT 1"
        cookie = mysql_manager.fetch_model(CookieModel, query)
        
        if cookie:
            log.info(f"成功获取模型对象: {cookie.account_id}")
            log.info(f"模型属性示例 - 是否可用: {cookie.is_available} (类型: {type(cookie.is_available)})")
            log.info(f"模型属性示例 - 最后更新: {cookie.last_updated}")
            
            # 测试转为数据库字典
            db_dict = cookie.to_db_dict()
            log.info(f"成功转换回字典，字段 [is_available]: {db_dict['is_available']}")
        else:
            log.warning("数据库中没有 Cookie 记录，跳过详细测试")
            
    except Exception as e:
        log.error(f"Cookie 映射测试失败: {e}")
        import traceback
        log.error(traceback.format_exc())

def test_task_mapping():
    log.info("\n测试 Task 模型映射与 JSON 解析...")
    try:
        query = "SELECT * FROM spider_tasks LIMIT 1"
        task = mysql_manager.fetch_model(SpiderTaskModel, query)
        
        if task:
            log.info(f"成功获取任务对象: {task.task_id}")
            log.info(f"任务参数类型: {type(task.parameters)}")
            if isinstance(task.parameters, dict):
                log.info("JSON 字段 [parameters] 已成功自动反序列化为字典")
            
            # 测试入库前的序列化
            db_dict = task.to_db_dict()
            log.info(f"入库字典 [parameters] 类型: {type(db_dict['parameters'])} (应为字符串)")
        else:
            log.warning("数据库中没有任务记录，跳过详细测试")
    except Exception as e:
        log.error(f"Task 映射测试失败: {e}")

if __name__ == "__main__":
    test_cookie_mapping()
    test_task_mapping()
    log.info("\n所有模型层基础功能验证完成")
