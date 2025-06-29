"""
Cookie轮换管理模块，负责获取、验证和轮换Cookie
"""
import time
import random
import json
import threading
from datetime import datetime, timedelta
from utils.logger import log
from db.redis_manager import redis_manager
from db.mysql_manager import mysql_manager
from config.settings import COOKIE_BLOCK_COOLDOWN


class CookieRotator:
    """Cookie轮换管理器，负责Cookie的获取、验证和轮换"""
    
    def __init__(self):
        """初始化Cookie轮换管理器"""
        self.lock = threading.RLock()
        self.cookie_cache = {}  # 本地Cookie缓存
        self.blocked_accounts = set()  # 被锁定的账号ID集合
        self.block_times = {}  # 账号被锁定的时间记录
        self.last_check_time = time.time()
        self.first_cookie_printed = False  # 是否已打印首次获取的cookie
        self.all_cookies_blocked_time = None  # 记录所有cookie被锁定的时间
        self.usage_counts = {}  # 记录每个cookie的使用次数，用于负载均衡
        self.cookies_available_event = threading.Event()  # 用于通知线程cookie可用状态
        self.cookies_available_event.set()  # 初始状态设为可用
        self.last_sync_time = time.time()  # 上次同步时间
        
        # 初始化时同步Cookie状态
        self._sync_cookie_status()
        
        # 启动定期同步任务
        self._start_periodic_sync()
    
    def _sync_cookie_status(self):
        """同步MySQL和Redis中的Cookie状态"""
        try:
            log.info("正在同步Cookie状态...")
            
            # 先清空Redis中的所有cookie数据，确保不会有残留数据
            self._clear_redis_cookies()
            
            # 从MySQL获取所有Cookie的状态
            with mysql_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT account_id, is_available, last_updated 
                    FROM cookies
                """)
                cookies = cursor.fetchall()
            
            if not cookies:
                log.warning("MySQL中没有Cookie记录")
                return
            
            # 清空内存中的锁定状态
            self.blocked_accounts.clear()
            self.block_times.clear()
            
            # 获取唯一的account_id集合
            unique_account_ids = set()
            available_account_ids = set()
            locked_account_ids = set()
            
            # 同步每个Cookie的状态
            for cookie in cookies:
                account_id = cookie['account_id']
                is_available = cookie['is_available'] == 1
                last_updated = cookie['last_updated']
                
                unique_account_ids.add(account_id)
                
                if not is_available:
                    # 标记为锁定状态
                    self.blocked_accounts.add(account_id)
                    locked_account_ids.add(account_id)
                    
                    # 计算已锁定时间
                    if last_updated:
                        lock_time = (datetime.now() - last_updated.replace(tzinfo=None)).total_seconds()
                        # 如果已锁定时间小于冷却时间，则设置block_time
                        if lock_time < COOKIE_BLOCK_COOLDOWN:
                            self.block_times[account_id] = time.time() - lock_time
                    else:
                        self.block_times[account_id] = time.time()
                    
                    # 在Redis中标记为锁定
                    redis_manager.mark_cookie_locked(account_id)
                else:
                    # 记录可用的账号ID
                    available_account_ids.add(account_id)
                    # 在Redis中标记为可用
                    redis_manager.mark_cookie_available(account_id)
            
            # 只缓存可用的cookie到Redis
            if available_account_ids:
                # 获取所有可用的cookie
                available_cookies = mysql_manager.get_all_valid_cookies()
                
                # 检查是否所有可用账号都有对应的cookie数据
                missing_accounts = available_account_ids - set(available_cookies.keys())
                if missing_accounts:
                    log.warning(f"发现 {len(missing_accounts)} 个账号在MySQL中标记为可用，但没有对应的cookie数据: {missing_accounts}")
                
                # 缓存到Redis
                for account_id, cookie_dict in available_cookies.items():
                    if account_id in available_account_ids:  # 确保只缓存MySQL中标记为可用的账号
                        redis_manager.cache_cookie(account_id, cookie_dict)
                
                log.info(f"已缓存 {len(available_cookies)} 个可用Cookie到Redis")
            
            # 验证Redis和MySQL的一致性
            self._verify_redis_mysql_consistency(available_account_ids, locked_account_ids)
            
            log.info(f"已同步 {len(unique_account_ids)} 个账号的Cookie状态，其中 {len(locked_account_ids)} 个被锁定，{len(available_account_ids)} 个可用")
        
        except Exception as e:
            log.error(f"同步Cookie状态失败: {e}")
    
    def _clear_redis_cookies(self):
        """清空Redis中的所有cookie数据"""
        try:
            # 获取所有缓存的cookie ID
            all_ids = redis_manager.get_all_cached_cookie_ids()
            
            # 删除每个cookie的相关数据
            for account_id in all_ids:
                # 删除cookie数据
                redis_manager.client.delete(f"cookie:{account_id}")
                
                # 删除状态数据
                redis_manager.client.hdel("cookie_status", account_id)
                redis_manager.client.hdel("cookie_lock_time", account_id)
                redis_manager.client.hdel("cookie_last_updated", account_id)
                
                # 删除使用统计数据
                usage_key = f"{redis_manager.cookie_usage_key_prefix}{account_id}"
                success_key = f"{redis_manager.cookie_success_key_prefix}{account_id}:success"
                fail_key = f"{redis_manager.cookie_success_key_prefix}{account_id}:fail"
                
                redis_manager.client.delete(usage_key)
                redis_manager.client.delete(success_key)
                redis_manager.client.delete(fail_key)
            
            # 清空cookie ID集合
            redis_manager.client.delete("cookie_ids")
            
            log.info(f"已清空Redis中的 {len(all_ids)} 个cookie数据")
        except Exception as e:
            log.error(f"清空Redis cookie数据失败: {e}")
            
    def _verify_redis_mysql_consistency(self, available_account_ids, locked_account_ids):
        """验证Redis和MySQL的cookie状态一致性"""
        try:
            # 获取Redis中所有cookie ID
            redis_ids = set(redis_manager.get_all_cached_cookie_ids())
            
            # 检查是否所有可用账号都在Redis中
            missing_in_redis = available_account_ids - redis_ids
            if missing_in_redis:
                log.warning(f"发现 {len(missing_in_redis)} 个可用账号未缓存到Redis: {missing_in_redis}")
                
            # 检查Redis中的cookie是否都应该在可用列表中
            extra_in_redis = redis_ids - available_account_ids - locked_account_ids
            if extra_in_redis:
                log.warning(f"发现 {len(extra_in_redis)} 个账号在Redis中但不在MySQL的可用或锁定列表中: {extra_in_redis}")
                # 从Redis中移除这些多余的cookie
                for account_id in extra_in_redis:
                    redis_manager.remove_cookie(account_id)
                    redis_manager.client.hdel("cookie_status", account_id)
                    redis_manager.client.hdel("cookie_lock_time", account_id)
                    redis_manager.client.hdel("cookie_last_updated", account_id)
                
            # 检查Redis中的cookie状态是否与MySQL一致
            for account_id in redis_ids:
                redis_locked = redis_manager.is_cookie_locked(account_id)
                mysql_locked = account_id in locked_account_ids
                
                if redis_locked != mysql_locked:
                    log.warning(f"账号 {account_id} 的锁定状态不一致: Redis={redis_locked}, MySQL={mysql_locked}")
                    # 更新Redis中的状态以匹配MySQL
                    if mysql_locked:
                        redis_manager.mark_cookie_locked(account_id)
                    else:
                        redis_manager.mark_cookie_available(account_id)
            
            log.info(f"Redis和MySQL的cookie状态一致性验证完成")
        except Exception as e:
            log.error(f"验证Redis和MySQL一致性失败: {e}")
    
    def get_cookie(self):
        """
        获取一个可用的Cookie，使用负载均衡策略
        :return: (account_id, cookie_dict) 元组，如果没有可用Cookie则返回 (None, None)
        """
        with self.lock:
            # 检查是否需要执行定期同步
            current_time = time.time()
            if current_time - self.last_sync_time > 600:  # 每10分钟同步一次
                log.info("执行定期MySQL和Redis数据同步...")
                self._sync_cookie_status()
                self.last_sync_time = current_time
            
            # 尝试解除已冷却的Cookie
            self._try_unblock_cookies()
            
            # 从Redis获取所有可用的账号ID
            available_ids = redis_manager.client.smembers("cookie_ids")
            if not available_ids:
                log.warning("Redis中没有缓存的Cookie，尝试从数据库刷新")
                self._refresh_cookies_from_db()
                available_ids = redis_manager.client.smembers("cookie_ids")
                
                if not available_ids:
                    # 当没有任何Cookie时，调用等待方法
                    if not self._wait_if_all_cookies_blocked():
                        # 如果等待方法返回False，表示已经在等待中或刚等待过，短暂等待避免频繁重试
                        time.sleep(10)
                    return None, None
            
            # 过滤掉被锁定的账号ID
            available_ids = [aid for aid in available_ids if aid not in self.blocked_accounts]
            
            log.debug(f"当前可用Cookie数量: {len(available_ids)}/{len(redis_manager.client.smembers('cookie_ids'))}")
            
            if not available_ids:
                # 如果Redis中没有可用Cookie，尝试从MySQL获取
                log.warning("所有Cookie都已被锁定，尝试从数据库刷新")
                self._refresh_cookies_from_db()
                
                # 重新获取可用的账号ID
                available_ids = redis_manager.client.smembers("cookie_ids")
                available_ids = [aid for aid in available_ids if aid not in self.blocked_accounts]
                
                if not available_ids:
                    # 所有cookie都被锁定，等待一段时间
                    log.warning(f"刷新后仍无可用Cookie，共有 {len(redis_manager.client.smembers('cookie_ids'))} 个Cookie全部被锁定")
                    
                    # 打印每个被锁定Cookie的状态
                    all_ids = redis_manager.client.smembers("cookie_ids")
                    for aid in all_ids:
                        is_available, last_updated = mysql_manager.get_cookie_status(aid)
                        in_blocked_set = aid in self.blocked_accounts
                        redis_locked = redis_manager.is_cookie_locked(aid)
                        log.info(f"Cookie {aid} 状态: MySQL可用={is_available}, 内存锁定={in_blocked_set}, Redis锁定={redis_locked}")
                        
                        # 如果MySQL和Redis状态不一致，立即修复
                        if is_available and (in_blocked_set or redis_locked):
                            log.warning(f"发现Cookie {aid} 状态不一致，MySQL显示可用但Redis或内存中被锁定，尝试修复...")
                            if in_blocked_set:
                                self.blocked_accounts.remove(aid)
                                if aid in self.block_times:
                                    del self.block_times[aid]
                            if redis_locked:
                                redis_manager.mark_cookie_available(aid)
                    
                    # 清除事件标志，通知所有线程cookie不可用
                    self.cookies_available_event.clear()
                    
                    # 使用_wait_if_all_cookies_blocked方法等待
                    log.warning("开始等待Cookie冷却...")
                    wait_result = self._wait_if_all_cookies_blocked()
                    
                    if not wait_result:
                        # 如果等待方法返回False，表示已经在等待中或刚等待过，短暂等待避免频繁重试
                        log.debug("等待中或刚等待过，短暂休眠10秒")
                        time.sleep(10)
                    
                    # 重新检查是否有可用的Cookie
                    available_ids = [aid for aid in redis_manager.client.smembers("cookie_ids") if aid not in self.blocked_accounts]
                    if not available_ids:
                        log.error("等待后仍无可用Cookie，返回None")
                        return None, None
                    else:
                        log.info(f"等待后有 {len(available_ids)} 个可用Cookie")
                        self.cookies_available_event.set()  # 设置事件标志，通知所有线程cookie已可用
                else:
                    # 如果刷新后有可用cookie，设置事件标志
                    self.cookies_available_event.set()
            
            # 使用负载均衡策略选择账号ID
            account_id = self._select_least_used_cookie(available_ids)
            
            # 从Redis获取Cookie字典
            cookie_dict = redis_manager.get_cookie(account_id)
            
            # 如果Redis中没有，尝试从MySQL获取
            if not cookie_dict:
                log.warning(f"Redis中没有账号 {account_id} 的Cookie，尝试从MySQL获取")
                cookies = mysql_manager.get_all_valid_cookies()
                if account_id in cookies:
                    cookie_dict = cookies[account_id]
                    # 缓存到Redis
                    redis_manager.cache_cookie(account_id, cookie_dict)
                    log.info(f"已从MySQL获取账号 {account_id} 的Cookie并缓存到Redis")
                else:
                    log.error(f"MySQL中也没有账号 {account_id} 的Cookie")
            
            # 如果仍然没有获取到Cookie值，返回None
            if not cookie_dict:
                log.error(f"无法获取账号 {account_id} 的Cookie")
                # 短暂等待避免频繁重试
                time.sleep(5)
                return None, None
            
            # 将account_id添加到cookie字典中，以便API调用时能够识别cookie属于哪个账号
            if cookie_dict:
                cookie_dict[f'account_id={account_id}'] = account_id
                    
            # 记录使用情况
            redis_manager.record_cookie_usage(account_id)
            
            # 更新本地使用计数
            self._update_usage_count(account_id)
            
            # 重置所有cookie被锁定的时间
            self.all_cookies_blocked_time = None
            
            return account_id, cookie_dict
    
    def _select_least_used_cookie(self, available_ids):
        """
        选择使用次数最少的Cookie
        :param available_ids: 可用的Cookie账号ID列表
        :return: 选择的账号ID
        """
        # 获取可用cookie的使用次数
        usage_data = {}
        for aid in available_ids:
            # 优先使用Redis中记录的使用次数
            redis_usage = redis_manager.get_cookie_metrics(aid).get('usage_count', 0)
            # 如果Redis中没有记录，使用本地记录
            local_usage = self.usage_counts.get(aid, 0)
            # 取两者中的最大值作为实际使用次数
            usage_data[aid] = max(redis_usage, local_usage)
        
        # 如果没有使用记录，或者所有cookie使用次数相同，则随机选择
        if not usage_data or len(set(usage_data.values())) <= 1:
            selected_id = random.choice(list(available_ids))
            log.debug(f"随机选择账号 {selected_id} 的Cookie，当前无使用记录或所有Cookie使用次数相同")
            return selected_id
        
        # 找出使用次数最少的cookie
        min_usage = min(usage_data.values())
        least_used_ids = [aid for aid, count in usage_data.items() if count == min_usage]
        
        # 如果有多个使用次数相同的cookie，随机选择一个
        selected_id = random.choice(least_used_ids)
        log.debug(f"选择使用次数最少的账号 {selected_id} 的Cookie，已使用 {min_usage} 次")
        
        return selected_id
    
    def _update_usage_count(self, account_id):
        """
        更新cookie的使用次数
        :param account_id: 账号ID
        """
        if account_id not in self.usage_counts:
            self.usage_counts[account_id] = 0
        self.usage_counts[account_id] += 1
    
    def _wait_if_all_cookies_blocked(self):
        """
        当所有cookie都被锁定时，等待一段时间
        :return: 是否在等待后有可用cookie
        """
        current_time = time.time()
        wait_time = 1800  # 30分钟，单位秒
        
        # 如果是首次发现所有cookie被锁定，记录时间
        if self.all_cookies_blocked_time is None:
            self.all_cookies_blocked_time = current_time
            
            # 打印清晰的提示信息
            log.warning(f"所有Cookie都已被锁定，将等待30分钟后重试")
            
            # 清除事件标志，通知所有线程cookie不可用
            self.cookies_available_event.clear()
            
            # 显示等待进度条
            self._display_wait_progress(wait_time)
            
            # 尝试解除已冷却的Cookie
            self._try_unblock_cookies(force=True)
            
            # 检查是否有可用cookie
            available_ids = redis_manager.get_all_cached_cookie_ids()
            available_ids = [aid for aid in available_ids if aid not in self.blocked_accounts]
            
            if available_ids:
                log.info(f"等待后有 {len(available_ids)} 个可用Cookie")
                # 设置事件标志，通知所有线程cookie已可用
                self.cookies_available_event.set()
                return True
            else:
                log.warning("等待30分钟后仍无可用Cookie，将继续等待")
                return False
        else:
            # 如果已经记录了所有cookie被锁定的时间，检查是否应该再次等待
            elapsed = current_time - self.all_cookies_blocked_time
            
            # 如果距离上次等待已超过30分钟，再次等待
            if elapsed >= wait_time:
                log.warning(f"所有Cookie仍被锁定，已等待 {int(elapsed/60)} 分钟，将再等待30分钟后重试")
                self.all_cookies_blocked_time = current_time
                
                # 显示等待进度条
                self._display_wait_progress(wait_time)
                
                # 尝试解除已冷却的Cookie
                self._try_unblock_cookies(force=True)
                
                # 检查是否有可用cookie
                available_ids = redis_manager.get_all_cached_cookie_ids()
                available_ids = [aid for aid in available_ids if aid not in self.blocked_accounts]
                
                if available_ids:
                    log.info(f"等待后有 {len(available_ids)} 个可用Cookie")
                    # 设置事件标志，通知所有线程cookie已可用
                    self.cookies_available_event.set()
                    return True
                else:
                    log.warning("再次等待30分钟后仍无可用Cookie")
                    return False
            else:
                # 如果距离上次等待不足30分钟，不再等待
                remaining_mins = int((wait_time-elapsed)/60)
                remaining_secs = int((wait_time-elapsed)%60)
                log.warning(f"所有Cookie仍被锁定，距离上次等待已过 {int(elapsed/60)} 分钟 {int(elapsed%60)} 秒，"
                           f"将在 {remaining_mins} 分钟 {remaining_secs} 秒后重试")
                return False
                
    def _display_wait_progress(self, wait_time):
        """
        显示等待进度条
        :param wait_time: 等待总时间（秒）
        """
        start_time = time.time()
        end_time = start_time + wait_time
        
        # 进度条长度
        bar_length = 50
        
        # 先清空当前行
        print("\r" + " " * 100, end="\r", flush=True)
        
        # 显示等待开始信息
        print(f"所有Cookie都被锁定，需要等待 {int(wait_time/60)} 分钟后重试...", flush=True)
        
        try:
            while time.time() < end_time:
                # 计算已经过去的时间和剩余时间
                elapsed = time.time() - start_time
                remaining = wait_time - elapsed
                
                # 计算进度百分比
                progress = elapsed / wait_time
                
                # 构建进度条
                arrow = '=' * int(progress * bar_length)
                spaces = ' ' * (bar_length - len(arrow))
                
                # 计算剩余时间（分:秒）
                mins = int(remaining // 60)
                secs = int(remaining % 60)
                
                # 打印进度条，确保清除整行
                print(f"\r等待Cookie冷却: [{arrow}{spaces}] {progress*100:.1f}% 剩余时间: {mins}分{secs}秒", end='', flush=True)
                
                # 每秒更新一次
                time.sleep(1)
                
                # 检查是否有可用cookie
                if self._check_for_available_cookies():
                    print("\r等待Cookie冷却: 检测到可用Cookie，中断等待" + " " * 50, flush=True)
                    return
                
            # 完成后打印100%进度
            print(f"\r等待Cookie冷却: [{'=' * bar_length}] 100% 完成" + " " * 20, flush=True)
        except Exception as e:
            log.error(f"显示等待进度条时出错: {e}")
            # 出错时也需要等待，但不显示进度条
            time.sleep(wait_time)
            
    def _check_for_available_cookies(self):
        """
        检查是否有可用的Cookie
        :return: 是否有可用Cookie
        """
        try:
            # 尝试解除已冷却的Cookie
            self._try_unblock_cookies(force=True)
            
            # 检查是否有可用cookie
            available_ids = redis_manager.get_all_cached_cookie_ids()
            available_ids = [aid for aid in available_ids if aid not in self.blocked_accounts]
            
            if available_ids:
                log.info(f"检测到 {len(available_ids)} 个可用Cookie")
                # 设置事件标志，通知所有线程cookie已可用
                self.cookies_available_event.set()
                return True
            return False
        except Exception as e:
            log.error(f"检查可用Cookie时出错: {e}")
            return False
    
    def wait_for_available_cookie(self, timeout=None):
        """
        等待直到有可用的cookie或超时
        :param timeout: 超时时间（秒），None表示无限等待
        :return: 是否有可用cookie
        """
        return self.cookies_available_event.wait(timeout)
    
    def report_cookie_status(self, account_id, is_valid, permanent=False):
        """
        报告Cookie的状态
        :param account_id: 账号ID
        :param is_valid: 是否有效
        :param permanent: 是否永久不可用，True表示永久不可用，不会被解锁
        """
        if not account_id:
            return
            
        with self.lock:
            if not is_valid:
                # 标记账号为锁定状态
                self.blocked_accounts.add(account_id)
                
                if permanent:
                    # 永久不可用，设置一个特殊值表示永久锁定
                    self.block_times[account_id] = -1
                    log.warning(f"账号 {account_id} 的Cookie已被永久锁定，不会自动解锁")
                else:
                    # 临时锁定，设置冷却时间
                    self.block_times[account_id] = time.time()
                    log.warning(f"账号 {account_id} 的Cookie已被锁定，设置冷却时间 {COOKIE_BLOCK_COOLDOWN} 秒")
                
                # 在Redis中标记cookie为锁定状态
                redis_manager.mark_cookie_locked(account_id)
                
                # 在MySQL中更新cookie的可用状态
                mysql_manager.update_cookie_status(account_id, False, permanent=permanent)
                
                # 检查是否所有cookie都被锁定
                self._check_if_all_cookies_blocked()
            else:
                # 如果cookie有效，且之前被锁定，则解除锁定
                if account_id in self.blocked_accounts:
                    self.blocked_accounts.remove(account_id)
                    if account_id in self.block_times:
                        del self.block_times[account_id]
                    log.info(f"账号 {account_id} 的Cookie已恢复有效状态")
                    
                    # 在Redis中标记cookie为可用状态
                    redis_manager.mark_cookie_available(account_id)
                    
                    # 在MySQL中更新cookie的可用状态
                    mysql_manager.update_cookie_status(account_id, True)
                    
                    # 如果之前所有cookie都被锁定，现在有可用的了，设置事件标志
                    if self.all_cookies_blocked_time is not None:
                        self.all_cookies_blocked_time = None
                        self.cookies_available_event.set()
                        log.info("检测到有Cookie恢复可用，通知所有等待线程")
    
    def _check_if_all_cookies_blocked(self):
        """检查是否所有cookie都被锁定"""
        try:
            # 获取所有cookie ID
            all_ids = redis_manager.get_all_cached_cookie_ids()
            if not all_ids:
                return True  # 没有cookie，视为全部锁定
                
            # 检查是否所有cookie都被锁定
            available_ids = [aid for aid in all_ids if aid not in self.blocked_accounts]
            if not available_ids:
                log.warning("所有Cookie都已被锁定")
                if self.all_cookies_blocked_time is None:
                    self.all_cookies_blocked_time = time.time()
                self.cookies_available_event.clear()
                return True
            return False
        except Exception as e:
            log.error(f"检查Cookie锁定状态失败: {e}")
            return False
    
    def _try_unblock_cookies(self, force=False):
        """
        尝试解除已冷却完成的Cookie锁定
        :param force: 是否强制检查，忽略时间间隔限制
        """
        current_time = time.time()
        
        # 每5分钟检查一次，或者强制检查
        if not force and current_time - self.last_check_time < 300:
            return
        
        self.last_check_time = current_time
        
        # 检查每个被锁定的账号
        for account_id in list(self.blocked_accounts):
            if account_id in self.block_times:
                # 跳过永久锁定的cookie
                if self.block_times[account_id] == -1:
                    continue
                    
                # 计算已冷却时间
                cooldown_time = current_time - self.block_times[account_id]
                
                # 如果已冷却时间超过设定值，解除锁定
                if cooldown_time >= COOKIE_BLOCK_COOLDOWN:
                    self.blocked_accounts.remove(account_id)
                    if account_id in self.block_times:
                        del self.block_times[account_id]
                    log.info(f"账号 {account_id} 的Cookie已冷却 {int(cooldown_time / 60)} 分钟，解除锁定")
                    
                    # 在Redis中标记cookie为可用状态
                    redis_manager.mark_cookie_available(account_id)
                    
                    # 在MySQL中更新cookie的可用状态
                    mysql_manager.update_cookie_status(account_id, True)
    
    def _refresh_cookies_from_db(self):
        """从数据库刷新Cookie缓存"""
        try:
            log.info("从数据库刷新Cookie缓存...")
            
            # 先清空Redis中的cookie数据，确保不会有残留数据
            self._clear_redis_cookies()
            
            # 从MySQL获取所有有效的Cookie
            cookies_dict = mysql_manager.get_all_valid_cookies()
            
            if not cookies_dict:
                log.warning("数据库中没有有效的Cookie")
                return
            
            # 清空内存中的锁定状态，以便与数据库同步
            self.blocked_accounts.clear()
            self.block_times.clear()
            
            # 同步数据库中所有cookie的状态
            with mysql_manager.get_cursor() as cursor:
                cursor.execute("""
                    SELECT account_id, is_available, last_updated 
                    FROM cookies
                """)
                all_cookies = cursor.fetchall()
            
            # 获取所有锁定的账号ID
            locked_account_ids = set()
            available_account_ids = set()
            
            for cookie in all_cookies:
                account_id = cookie['account_id']
                is_available = cookie['is_available'] == 1
                last_updated = cookie['last_updated']
                
                if not is_available:
                    locked_account_ids.add(account_id)
                    self.blocked_accounts.add(account_id)
                    self.block_times[account_id] = time.time() - COOKIE_BLOCK_COOLDOWN / 2  # 设置为已冷却一半时间
                    redis_manager.mark_cookie_locked(account_id)
                else:
                    available_account_ids.add(account_id)
            
            # 缓存到Redis并同步可用状态
            cached_count = 0
            for account_id, cookie_dict in cookies_dict.items():
                if account_id in locked_account_ids:
                    # 跳过锁定的账号
                    continue
                    
                if not isinstance(cookie_dict, dict):
                    log.warning(f"账号 {account_id} 的Cookie不是字典格式: {type(cookie_dict)}")
                    continue
                
                if not cookie_dict:
                    log.warning(f"账号 {account_id} 的Cookie字典为空")
                    continue
                
                # 缓存到Redis
                redis_manager.cache_cookie(account_id, cookie_dict)
                # 确保Redis中标记为可用
                redis_manager.mark_cookie_available(account_id)
                cached_count += 1
            
            # 验证Redis和MySQL的一致性
            self._verify_redis_mysql_consistency(available_account_ids, locked_account_ids)
            
            total_accounts = len(set(c['account_id'] for c in all_cookies))
            log.info(f"从数据库刷新了 {total_accounts} 个账号的Cookie状态，其中 {len(locked_account_ids)} 个被锁定，{cached_count} 个可用Cookie已缓存到Redis")
            
        except Exception as e:
            log.error(f"从数据库刷新Cookie失败: {e}")
            
    def _start_periodic_sync(self):
        """启动定期同步任务"""
        def sync_task():
            while True:
                try:
                    # 每10分钟同步一次
                    time.sleep(600)
                    log.info("执行定期MySQL和Redis数据同步...")
                    self._sync_cookie_status()
                except Exception as e:
                    log.error(f"定期同步任务出错: {e}")
                    time.sleep(60)  # 出错后等待1分钟再重试
        
        # 启动同步线程
        sync_thread = threading.Thread(target=sync_task, daemon=True)
        sync_thread.start()
        log.info("已启动定期MySQL和Redis数据同步任务")
    
    def get_status(self):
        """
        获取Cookie管理器状态
        :return: 状态字典
        """
        with self.lock:
            # 获取所有可用的账号ID
            all_ids = redis_manager.get_all_cached_cookie_ids()
            
            # 计算被锁定的账号数量和可用账号数量
            blocked_count = len(self.blocked_accounts)
            available_count = len([aid for aid in all_ids if aid not in self.blocked_accounts])
            
            # 计算每个被锁定账号的冷却状态
            current_time = time.time()
            cooldown_status = {}
            
            for account_id in self.blocked_accounts:
                if account_id in self.block_times:
                    elapsed = current_time - self.block_times[account_id]
                    remaining = max(0, COOKIE_BLOCK_COOLDOWN - elapsed)
                    
                    cooldown_status[account_id] = {
                        'elapsed_seconds': int(elapsed),
                        'remaining_seconds': int(remaining),
                        'elapsed_minutes': int(elapsed / 60),
                        'remaining_minutes': int(remaining / 60)
                    }
            
            # 添加所有cookie被锁定的等待状态
            all_blocked_wait_info = None
            wait_time = 1800  # 30分钟，单位秒
            if self.all_cookies_blocked_time is not None:
                elapsed = current_time - self.all_cookies_blocked_time
                remaining = max(0, wait_time - elapsed)
                all_blocked_wait_info = {
                    'elapsed_seconds': int(elapsed),
                    'remaining_seconds': int(remaining),
                    'elapsed_minutes': int(elapsed / 60),
                    'remaining_minutes': int(remaining / 60)
                }
            
            return {
                'total': len(all_ids),
                'blocked': blocked_count,
                'available': available_count,
                'blocked_ids': list(self.blocked_accounts),
                'cooldown_status': cooldown_status,
                'all_blocked_wait_info': all_blocked_wait_info,
                'wait_time_minutes': int(wait_time / 60)  # 添加等待时间（分钟）
            }
    
    def get_usage_statistics(self):
        """
        获取所有cookie的使用统计信息
        :return: 使用统计信息字典
        """
        with self.lock:
            # 从Redis获取所有账号ID
            all_ids = redis_manager.get_all_cached_cookie_ids()
            
            # 初始化统计数据
            stats = {
                'total_cookies': len(all_ids),
                'cookie_usage': {},
                'max_usage': 0,
                'min_usage': 0,
                'avg_usage': 0,
                'std_dev': 0  # 标准差，用于衡量负载均衡效果
            }
            
            # 如果没有cookie，直接返回空统计
            if not all_ids:
                return stats
            
            # 获取每个cookie的使用次数
            total_usage = 0
            usage_counts = []
            
            for aid in all_ids:
                # 优先使用Redis中记录的使用次数
                redis_metrics = redis_manager.get_cookie_metrics(aid)
                redis_usage = redis_metrics.get('usage_count', 0)
                # 获取本地记录的使用次数
                local_usage = self.usage_counts.get(aid, 0)
                # 取两者中的最大值作为实际使用次数
                actual_usage = max(redis_usage, local_usage)
                
                # 记录统计信息
                stats['cookie_usage'][aid] = {
                    'usage_count': actual_usage,
                    'success_count': redis_metrics.get('success_count', 0),
                    'fail_count': redis_metrics.get('fail_count', 0),
                    'success_rate': redis_metrics.get('success_rate', 0),
                    'is_blocked': aid in self.blocked_accounts
                }
                
                total_usage += actual_usage
                usage_counts.append(actual_usage)
            
            # 计算统计指标
            if usage_counts:
                stats['max_usage'] = max(usage_counts)
                stats['min_usage'] = min(usage_counts)
                stats['avg_usage'] = total_usage / len(usage_counts)
                
                # 计算标准差
                if len(usage_counts) > 1:
                    variance = sum((x - stats['avg_usage']) ** 2 for x in usage_counts) / len(usage_counts)
                    stats['std_dev'] = variance ** 0.5
            
            return stats
    
    def refresh_cookies_from_db(self):
        """
        从数据库刷新Cookie缓存的公共方法
        """
        self._refresh_cookies_from_db()
        
    def get_all_valid_cookies(self):
        """
        获取所有有效的cookies
        :return: 所有有效的cookie字典，格式为 {account_id: cookie_dict}
        """
        with self.lock:
            # 获取所有可用的账号ID
            available_ids = redis_manager.client.smembers("cookie_ids")
            if not available_ids:
                log.warning("Redis中没有缓存的Cookie，尝试从数据库刷新")
                self._refresh_cookies_from_db()
                available_ids = redis_manager.client.smembers("cookie_ids")
                
                if not available_ids:
                    log.error("没有可用的cookie")
                    return {}
            
            # 过滤掉被锁定的账号ID
            available_ids = [aid for aid in available_ids if aid not in self.blocked_accounts]
            
            # 如果没有可用cookie
            if not available_ids:
                log.warning("所有cookie都已被锁定")
                return {}
                
            # 获取所有可用cookie
            result = {}
            for account_id in available_ids:
                cookie_dict = redis_manager.get_cookie(account_id)
                if cookie_dict:
                    result[account_id] = cookie_dict
                    # 添加account_id到cookie字典中
                    cookie_dict[f'account_id={account_id}'] = account_id
            
            return result


# 创建Cookie轮换管理器单例
cookie_rotator = CookieRotator() 