"""
Cookie健康检查模块，定期检查Cookie的有效性
"""
from datetime import datetime, timedelta
from utils.logger import log
from db.mysql_manager import mysql_manager
from db.redis_manager import redis_manager
from cookie_manager.cookie_validator import cookie_validator
from config.settings import COOKIE_MIN_AVAILABLE_COUNT, COOKIE_BLOCK_COOLDOWN


class HealthChecker:
    """Cookie健康检查器，定期检查所有Cookie的有效性"""
    
    def __init__(self):
        self.last_check_time = datetime.now()
    
    def check_all_cookies(self):
        """检查所有缓存的Cookie的有效性"""
        log.info("开始执行Cookie健康检查...")
        
        # 获取所有缓存的Cookie ID
        cached_cookie_ids = redis_manager.get_all_cached_cookie_ids()
        
        if not cached_cookie_ids:
            log.warning("缓存中没有Cookie，尝试从数据库加载")
            self._load_cookies_from_db()
            cached_cookie_ids = redis_manager.get_all_cached_cookie_ids()
        
        valid_count = 0
        blocked_count = 0
        
        # 检查每个Cookie
        for cookie_id in cached_cookie_ids:
            cookie_data = redis_manager.get_cookie(cookie_id)
            if not cookie_data:
                continue
                
            # 验证Cookie
            is_valid, reason = cookie_validator.validate_cookie(cookie_data.get('cookie_value', ''))
            
            if is_valid:
                valid_count += 1
            else:
                blocked_count += 1
                log.warning(f"Cookie {cookie_id} 已被锁定: {reason}")
                
                # 从缓存中移除
                redis_manager.remove_cookie(cookie_id)
                
                # 更新数据库状态
                mysql_manager.update_cookie_status(cookie_id, False)
        
        # 检查被锁定的Cookie是否可以解锁
        self._check_blocked_cookies()
        
        # 检查可用Cookie数量是否足够
        self._check_available_count()
        
        log.info(f"Cookie健康检查完成: 有效 {valid_count}, 锁定 {blocked_count}")
        self.last_check_time = datetime.now()
    
    def _check_blocked_cookies(self):
        """检查被锁定的Cookie是否可以解锁"""
        # 获取所有不可用的Cookie
        with mysql_manager.get_cursor() as cursor:
            # 查找被锁定超过冷却时间的Cookie
            cooldown_time = datetime.now() - timedelta(seconds=COOKIE_BLOCK_COOLDOWN)
            sql = """
                SELECT * FROM cookies 
                WHERE is_available = FALSE 
                AND last_updated < %s
            """
            cursor.execute(sql, (cooldown_time,))
            blocked_cookies = cursor.fetchall()
        
        if blocked_cookies:
            log.info(f"发现 {len(blocked_cookies)} 个被锁定的Cookie可能可以解锁")
            
            unblocked_count = 0
            for cookie in blocked_cookies:
                # 尝试验证Cookie
                is_valid, reason = cookie_validator.validate_cookie(cookie['cookie_value'])
                
                if is_valid:
                    # 更新数据库状态
                    mysql_manager.update_cookie_status(cookie['id'], True)
                    
                    # 添加到缓存
                    cookie_data = {
                        'id': cookie['id'],
                        'account_id': cookie['account_id'],
                        'cookie_name': cookie['cookie_name'],
                        'cookie_value': cookie['cookie_value'],
                        'expire_time': None,  # 百度指数Cookie不会过期
                    }
                    redis_manager.cache_cookie(cookie['id'], cookie_data)
                    
                    unblocked_count += 1
                    log.info(f"Cookie {cookie['id']} 已解锁")
            
            if unblocked_count > 0:
                log.info(f"共解锁了 {unblocked_count} 个Cookie")
    
    def _check_available_count(self):
        """检查可用Cookie数量是否足够"""
        available_cookies = mysql_manager.get_available_cookies()
        
        if len(available_cookies) < COOKIE_MIN_AVAILABLE_COUNT:
            log.error(f"可用Cookie数量不足: {len(available_cookies)}/{COOKIE_MIN_AVAILABLE_COUNT}")
            # 这里可以添加告警逻辑，如发送邮件或短信
    
    def _load_cookies_from_db(self):
        """从数据库加载可用的Cookie到Redis缓存"""
        cookies = mysql_manager.get_available_cookies()
        loaded_count = 0
        
        for cookie in cookies:
            # 缓存到Redis
            cookie_data = {
                'id': cookie['id'],
                'account_id': cookie['account_id'],
                'cookie_name': cookie['cookie_name'],
                'cookie_value': cookie['cookie_value'],
                'expire_time': None,  # 百度指数Cookie不会过期
            }
            
            if redis_manager.cache_cookie(cookie['id'], cookie_data):
                loaded_count += 1
                
        log.info(f"从数据库加载了 {loaded_count} 个Cookie到缓存")


# 创建健康检查器单例
health_checker = HealthChecker() 