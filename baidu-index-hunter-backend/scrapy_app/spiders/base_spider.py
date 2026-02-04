"""
百度指数爬虫基类

提供所有爬虫的公共功能：
- 参数解析
- 数据解密
- 日期处理
- 状态管理
"""
import os
import json
import scrapy
from datetime import datetime, timedelta
from urllib.parse import quote


class BaseBaiduIndexSpider(scrapy.Spider):
    """百度指数爬虫基类"""
    
    # 基础属性
    allowed_domains = ['index.baidu.com']
    
    # 任务相关属性
    task_id = None
    total_items = 0
    completed_items = 0
    failed_items = 0
    output_files = []
    
    def __init__(self, task_id=None, keywords=None, cities=None, 
                 date_ranges=None, days=None, year_range=None,
                 resume=False, *args, **kwargs):
        """
        初始化爬虫
        
        Args:
            task_id: 任务ID
            keywords: 关键词列表 (JSON字符串或列表)
            cities: 城市字典 (JSON字符串或字典) {code: name}
            date_ranges: 日期范围列表 (JSON字符串或列表) [(start, end), ...]
            days: 预定义天数 (7, 30, 90, 180)
            year_range: 年份范围 (JSON字符串或列表) [start_year, end_year]
            resume: 是否为断点续传
        """
        super().__init__(*args, **kwargs)
        
        self.task_id = task_id or datetime.now().strftime('%Y%m%d%H%M%S')
        self.resume = self._parse_bool(resume)
        
        # 解析参数
        self.keywords = self._parse_list(keywords) or []
        self.cities = self._parse_dict(cities) or {'0': '全国'}
        self.date_ranges = self._parse_date_ranges(date_ranges, days, year_range)
        
        # 计算总任务数
        self._calculate_total_items()
        
        self.logger.info(
            f"Spider initialized - Task: {self.task_id}, "
            f"Keywords: {len(self.keywords)}, "
            f"Cities: {len(self.cities)}, "
            f"DateRanges: {len(self.date_ranges)}, "
            f"TotalItems: {self.total_items}"
        )
    
    def _calculate_total_items(self):
        """计算总任务数（子类可覆盖）"""
        self.total_items = len(self.keywords) * len(self.cities) * len(self.date_ranges)
    
    @classmethod
    def update_settings(cls, settings):
        """更新设置，设置 JobDir 用于断点续传"""
        super().update_settings(settings)
        
        # JobDir 会在实例化时根据 task_id 设置
        # 这里只做基础设置
    
    def _setup_jobdir(self):
        """设置 JobDir 目录"""
        jobdir_base = self.settings.get('JOBDIR_BASE', 'output/scrapy_jobs')
        jobdir = os.path.join(jobdir_base, f'{self.name}_{self.task_id}')
        
        # 动态设置 JOBDIR
        self.settings.set('JOBDIR', jobdir, priority='spider')
        
        # 确保目录存在
        os.makedirs(jobdir, exist_ok=True)
        
        self.logger.info(f"JobDir set to: {jobdir}")
    
    # ==================== 参数解析方法 ====================
    
    def _parse_bool(self, value):
        """解析布尔值"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes')
        return bool(value)
    
    def _parse_list(self, value):
        """解析列表参数"""
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                # 尝试按逗号分割
                return [v.strip() for v in value.split(',') if v.strip()]
        return [value]
    
    def _parse_dict(self, value):
        """解析字典参数"""
        if value is None:
            return {}
        if isinstance(value, dict):
            # 处理嵌套的城市格式 {code: {name, code}}
            result = {}
            for k, v in value.items():
                if isinstance(v, dict) and 'name' in v:
                    code = v.get('code', k)
                    result[str(code)] = v['name']
                else:
                    result[str(k)] = str(v)
            return result
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return self._parse_dict(parsed)
            except json.JSONDecodeError:
                pass
        return {}
    
    def _parse_date_ranges(self, date_ranges, days, year_range):
        """解析日期范围参数"""
        # 优先使用 date_ranges
        if date_ranges:
            if isinstance(date_ranges, str):
                try:
                    date_ranges = json.loads(date_ranges)
                except json.JSONDecodeError:
                    pass
            
            if isinstance(date_ranges, list) and len(date_ranges) > 0:
                result = []
                for dr in date_ranges:
                    if isinstance(dr, (list, tuple)) and len(dr) >= 2:
                        result.append((str(dr[0]), str(dr[1])))
                    elif isinstance(dr, str):
                        # 假设格式为 "start,end"
                        parts = dr.split(',')
                        if len(parts) >= 2:
                            result.append((parts[0].strip(), parts[1].strip()))
                if result:
                    return result
        
        # 使用 days 参数
        if days:
            try:
                days = int(days)
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=days-1)).strftime('%Y-%m-%d')
                return [(start_date, end_date)]
            except (ValueError, TypeError):
                pass
        
        # 使用 year_range 参数
        if year_range:
            return self._process_year_range(year_range)
        
        # 默认使用最近 30 天
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=29)).strftime('%Y-%m-%d')
        return [(start_date, end_date)]
    
    def _process_year_range(self, year_range):
        """处理年份范围，生成每年的日期范围"""
        if isinstance(year_range, str):
            try:
                year_range = json.loads(year_range)
            except json.JSONDecodeError:
                return []
        
        if not isinstance(year_range, list) or len(year_range) == 0:
            return []
        
        # 支持 [[start, end]] 或 [start, end] 格式
        if isinstance(year_range[0], list):
            start_year = int(year_range[0][0])
            end_year = int(year_range[0][1]) if len(year_range[0]) > 1 else start_year
        else:
            start_year = int(year_range[0])
            end_year = int(year_range[1]) if len(year_range) > 1 else start_year
        
        current_year = datetime.now().year
        date_ranges = []
        
        for year in range(start_year, end_year + 1):
            if year < current_year:
                # 完整年份
                start_date = f"{year}-01-01"
                end_date = f"{year}-12-31"
            else:
                # 当年截止到今天
                start_date = f"{year}-01-01"
                end_date = datetime.now().strftime('%Y-%m-%d')
            
            date_ranges.append((start_date, end_date))
        
        return date_ranges
    
    # ==================== 数据解密方法 ====================
    
    def decrypt_data(self, key, data):
        """
        解密百度指数数据
        
        Args:
            key: 解密密钥
            data: 加密的数据字符串
            
        Returns:
            解密后的字符串
        """
        if not key or not data:
            return ""
        
        key_list = list(key)
        data_list = list(data)
        
        # 构建映射字典
        mapping = {}
        half = len(key_list) // 2
        for i in range(half):
            mapping[key_list[i]] = key_list[half + i]
        
        # 解密
        result = [mapping.get(c, c) for c in data_list]
        return ''.join(result)
    
    # ==================== 日期处理方法 ====================
    
    def generate_dates(self, start_date, end_date):
        """
        生成日期列表
        
        Args:
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            日期字符串列表
        """
        dates = []
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            
            current = start
            while current <= end:
                dates.append(current.strftime('%Y-%m-%d'))
                current += timedelta(days=1)
        except Exception as e:
            self.logger.error(f"Error generating dates: {e}")
        
        return dates
    
    # ==================== URL 构建方法 ====================
    
    def build_word_param(self, keywords):
        """
        构建 word 参数
        
        Args:
            keywords: 关键词列表
            
        Returns:
            URL 编码后的 word 参数
        """
        word_list = [[{"name": kw, "wordType": 1}] for kw in keywords]
        word_json = json.dumps(word_list, ensure_ascii=False)
        return quote(word_json)
    
    def build_ptbk_url(self, uniqid):
        """构建获取解密密钥的 URL"""
        return f'https://index.baidu.com/Interface/ptbk?uniqid={uniqid}'
    
    # ==================== 请求构建辅助方法 ====================
    
    def make_request(self, url, callback, meta=None, **kwargs):
        """
        创建请求的辅助方法
        
        Args:
            url: 请求 URL
            callback: 回调函数
            meta: 元数据
            **kwargs: 其他 scrapy.Request 参数
            
        Returns:
            scrapy.Request 对象
        """
        meta = meta or {}
        meta.setdefault('dont_redirect', True)
        
        return scrapy.Request(
            url=url,
            callback=callback,
            meta=meta,
            dont_filter=kwargs.pop('dont_filter', True),
            **kwargs
        )
