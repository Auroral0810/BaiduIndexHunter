"""
应用初始化服务 - 处理区域数据同步、Cookie同步和配置初始化
"""
from src.core.logger import log
from src.services.config_service import config_manager
from src.services.region_service import get_region_manager
from src.services.cookie_service import CookieManager

# 全局状态标识，确保只初始化一次
_initialized = False

def init_app_data(force=False):
    """初始化应用数据 (配置、区域、Cookie)"""
    global _initialized
    if _initialized and not force:
        return True
    
    try:
        # 1. 初始化系统配置
        log.info("正在初始化系统配置...")
        config_manager.refresh_cache()
        config_manager.init_default_configs()

        # 2. 同步区域数据到Redis
        log.info("正在同步区域数据到Redis...")
        region_manager = get_region_manager()
        region_manager.sync_to_redis()

        # 3. 同步Cookie数据到Redis
        log.info("正在同步Cookie数据到Redis...")
        cookie_manager = CookieManager()
        cookie_manager.sync_to_redis()
        cookie_manager.close()

        _initialized = True
        log.info("应用数据初始化全量完成")
        return True
    except Exception as e:
        log.error(f"应用数据初始化失败: {e}")
        import traceback
        log.error(traceback.format_exc())
        return False
