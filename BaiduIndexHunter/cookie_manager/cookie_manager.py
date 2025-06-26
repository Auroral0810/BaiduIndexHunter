class CookieManager:
    """Cookie管理器，负责Cookie的获取、验证和轮换"""
    
    def __init__(self, cookie_list=None):
        """
        初始化Cookie管理器
        :param cookie_list: 初始Cookie列表
        """
        self.cookie_list = cookie_list or []
        self.current_index = 0
        self.blocked_indices = set()  # 存储被锁定的cookie索引
        self.block_times = {}  # 记录cookie被锁定的时间
        self.last_check_time = time.time()
        self.lock = threading.RLock()
        
        # 添加一个变量来跟踪是否已经打印过首次cookie信息
        self._first_cookie_printed = False
    
    def add_cookie(self, cookie):
        """
        添加Cookie到管理器
        :param cookie: Cookie字典
        """
        with self.lock:
            if cookie not in self.cookie_list:
                self.cookie_list.append(cookie)
                log.info(f"添加新Cookie，当前Cookie数量: {len(self.cookie_list)}")
    
    def get_cookie(self):
        """
        获取一个可用的Cookie
        :return: Cookie字典或None
        """
        with self.lock:
            if not self.cookie_list:
                log.error("Cookie列表为空")
                return None
            
            # 检查是否所有Cookie都被锁定
            if len(self.blocked_indices) >= len(self.cookie_list):
                log.error("所有Cookie都已被锁定")
                return None
            
            # 尝试解除冷却时间已到的Cookie
            self._try_unblock_cookies()
            
            # 找到一个未被锁定的Cookie
            attempts = 0
            while attempts < len(self.cookie_list):
                if self.current_index in self.blocked_indices:
                    self.current_index = (self.current_index + 1) % len(self.cookie_list)
                    attempts += 1
                    continue
                
                cookie = self.cookie_list[self.current_index]
                cookie_index = self.current_index + 1  # 索引从1开始更直观
                
                # 打印首次使用的cookie信息
                if not self._first_cookie_printed:
                    log.info(f"===== 首次使用的Cookie信息 =====")
                    log.info(f"Cookie索引: {cookie_index}/{len(self.cookie_list)}")
                    log.info(f"Cookie内容: {cookie}")
                    self._first_cookie_printed = True
                
                # 更新索引，下次使用下一个Cookie
                self.current_index = (self.current_index + 1) % len(self.cookie_list)
                
                return cookie
            
            log.error("无法获取可用的Cookie")
            return None
    
    def block_cookie(self, cookie):
        """
        标记Cookie为锁定状态
        :param cookie: 被锁定的Cookie
        """
        with self.lock:
            for i, c in enumerate(self.cookie_list):
                if c == cookie:
                    self.blocked_indices.add(i)
                    self.block_times[i] = time.time()
                    log.warning(f"Cookie {i+1}/{len(self.cookie_list)} 已被锁定，设置冷却时间")
                    break
    
    def _try_unblock_cookies(self):
        """尝试解除已冷却完成的Cookie锁定"""
        current_time = time.time()
        
        # 每5分钟检查一次
        if current_time - self.last_check_time < 300:
            return
        
        self.last_check_time = current_time
        
        for idx in list(self.blocked_indices):
            if idx in self.block_times:
                # 计算冷却时间（秒）
                cooldown_time = current_time - self.block_times[idx]
                
                # 如果冷却时间超过设定值，解除锁定
                if cooldown_time >= COOKIE_BLOCK_COOLDOWN:
                    self.blocked_indices.remove(idx)
                    log.info(f"Cookie {idx+1}/{len(self.cookie_list)} 冷却完成，已解除锁定")
    
    def get_status(self):
        """
        获取Cookie管理器状态
        :return: 状态字典
        """
        with self.lock:
            total = len(self.cookie_list)
            blocked = len(self.blocked_indices)
            available = total - blocked
            
            # 计算每个被锁定Cookie的冷却状态
            current_time = time.time()
            cooldown_status = {}
            
            for idx in self.blocked_indices:
                if idx in self.block_times:
                    elapsed = current_time - self.block_times[idx]
                    remaining = max(0, COOKIE_BLOCK_COOLDOWN - elapsed)
                    
                    cooldown_status[idx] = {
                        'elapsed_seconds': int(elapsed),
                        'remaining_seconds': int(remaining),
                        'elapsed_minutes': int(elapsed / 60),
                        'remaining_minutes': int(remaining / 60)
                    }
            
            return {
                'total': total,
                'blocked': blocked,
                'available': available,
                'blocked_indices': list(self.blocked_indices),
                'cooldown_status': cooldown_status
            }
    
    def print_cookie_info(self, cookie=None, index=None):
        """
        打印Cookie信息，用于调试
        :param cookie: 要打印的Cookie，如果为None则打印当前使用的Cookie
        :param index: Cookie的索引，如果为None则自动查找
        """
        if cookie is None:
            cookie = self.get_cookie()
            
        if cookie is None:
            log.warning("没有可用的Cookie可供打印")
            return
            
        if index is None:
            for i, c in enumerate(self.cookie_list):
                if c == cookie:
                    index = i + 1
                    break
        
        log.info(f"===== Cookie信息 =====")
        log.info(f"Cookie索引: {index}/{len(self.cookie_list)}")
        log.info(f"Cookie内容: {cookie}")
        log.info(f"Cookie是否被锁定: {'是' if index-1 in self.blocked_indices else '否'}")
        
        if index-1 in self.block_times:
            elapsed = time.time() - self.block_times[index-1]
            remaining = max(0, COOKIE_BLOCK_COOLDOWN - elapsed)
            log.info(f"已冷却时间: {int(elapsed/60)}分钟, 剩余冷却时间: {int(remaining/60)}分钟")
            
        return cookie