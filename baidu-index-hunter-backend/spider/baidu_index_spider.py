"""
百度指数爬虫主类
作为所有爬虫任务的统一接口
"""
import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import log
from spider.search_index_crawler import search_index_crawler
from spider.feed_index_crawler import feed_index_crawler
from spider.word_graph_crawler import word_graph_crawler
from spider.demographic_attributes_crawler import demographic_attributes_crawler
from spider.interest_profile_crawler import interest_profile_crawler
from spider.region_distribution_crawler import region_distribution_crawler


class BaiduIndexSpider:
    """百度指数爬虫类，统一接口调用各种爬虫任务"""
    
    def __init__(self):
        """初始化爬虫类"""
        self.search_index_crawler = search_index_crawler
        self.feed_index_crawler = feed_index_crawler
        self.word_graph_crawler = word_graph_crawler
        self.demographic_attributes_crawler = demographic_attributes_crawler
        self.interest_profile_crawler = interest_profile_crawler
        self.region_distribution_crawler = region_distribution_crawler
        
        log.info("百度指数爬虫初始化完成")
    
    def get_search_index(self, keyword, start_date, end_date, area="0", cookie=None):
        """
        获取搜索指数
        
        参数:
            keyword (str/list): 关键词或关键词列表
            start_date (str): 开始日期，格式为YYYY-MM-DD
            end_date (str): 结束日期，格式为YYYY-MM-DD
            area (str): 地区代码，默认为"0"(全国)
            cookie (dict): Cookie字典，如果不提供则从cookie_rotator获取
            
        返回:
            dict: 搜索指数数据
        """
        log.info(f"开始获取搜索指数: 关键词={keyword}, 地区={area}, 日期={start_date}至{end_date}")
        
        try:
            # 如果keyword是字符串，转换为列表
            if isinstance(keyword, str):
                keywords = [keyword]
            else:
                keywords = keyword
                
            # 将area转换为字符串
            area = str(area)
            
            # 构建城市字典
            if area == "0":
                cities = {0: "全国"}
            else:
                cities = {int(area): f"地区{area}"}
                
            # 构建日期范围
            date_ranges = [(start_date, end_date)]
            
            # 调用爬虫获取数据
            result = self.search_index_crawler._get_search_index(area, keywords, start_date, end_date)
            
            if not result:
                log.error("获取搜索指数失败")
                return None
                
            # 返回结果
            return result[0]  # 只返回数据部分，不返回cookie
            
        except Exception as e:
            log.error(f"获取搜索指数出错: {str(e)}")
            return None
    
    def get_feed_index(self, keyword, start_date, end_date, area="0", cookie=None):
        """
        获取资讯指数
        
        参数:
            keyword (str/list): 关键词或关键词列表
            start_date (str): 开始日期，格式为YYYY-MM-DD
            end_date (str): 结束日期，格式为YYYY-MM-DD
            area (str): 地区代码，默认为"0"(全国)
            cookie (dict): Cookie字典，如果不提供则从cookie_rotator获取
            
        返回:
            dict: 资讯指数数据
        """
        log.info(f"开始获取资讯指数: 关键词={keyword}, 地区={area}, 日期={start_date}至{end_date}")
        
        try:
            # 这里调用feed_index_crawler的相应方法
            # 当前为占位实现
            result = {"status": 10000, "data": {"feed_index": "示例资讯指数数据"}}
            return result
        except Exception as e:
            log.error(f"获取资讯指数出错: {str(e)}")
            return None
    
    def get_word_graph(self, keyword, area="0", cookie=None):
        """
        获取需求图谱
        
        参数:
            keyword (str): 关键词
            area (str): 地区代码，默认为"0"(全国)
            cookie (dict): Cookie字典，如果不提供则从cookie_rotator获取
            
        返回:
            dict: 需求图谱数据
        """
        log.info(f"开始获取需求图谱: 关键词={keyword}, 地区={area}")
        
        try:
            # 这里调用word_graph_crawler的相应方法
            # 当前为占位实现
            result = {"status": 10000, "data": {"word_graph": "示例需求图谱数据"}}
            return result
        except Exception as e:
            log.error(f"获取需求图谱出错: {str(e)}")
            return None
    
    def get_demographic_attributes(self, keyword, area="0", cookie=None):
        """
        获取人群属性
        
        参数:
            keyword (str): 关键词
            area (str): 地区代码，默认为"0"(全国)
            cookie (dict): Cookie字典，如果不提供则从cookie_rotator获取
            
        返回:
            dict: 人群属性数据
        """
        log.info(f"开始获取人群属性: 关键词={keyword}, 地区={area}")
        
        try:
            # 这里调用demographic_attributes_crawler的相应方法
            # 当前为占位实现
            result = {"status": 10000, "data": {"demographic_attributes": "示例人群属性数据"}}
            return result
        except Exception as e:
            log.error(f"获取人群属性出错: {str(e)}")
            return None
    
    def get_interest_profile(self, keyword, area="0", cookie=None):
        """
        获取兴趣分布
        
        参数:
            keyword (str): 关键词
            area (str): 地区代码，默认为"0"(全国)
            cookie (dict): Cookie字典，如果不提供则从cookie_rotator获取
            
        返回:
            dict: 兴趣分布数据
        """
        log.info(f"开始获取兴趣分布: 关键词={keyword}, 地区={area}")
        
        try:
            # 这里调用interest_profile_crawler的相应方法
            # 当前为占位实现
            result = {"status": 10000, "data": {"interest_profile": "示例兴趣分布数据"}}
            return result
        except Exception as e:
            log.error(f"获取兴趣分布出错: {str(e)}")
            return None
    
    def get_region_distribution(self, keyword, area="0", cookie=None):
        """
        获取地域分布
        
        参数:
            keyword (str): 关键词
            area (str): 地区代码，默认为"0"(全国)
            cookie (dict): Cookie字典，如果不提供则从cookie_rotator获取
            
        返回:
            dict: 地域分布数据
        """
        log.info(f"开始获取地域分布: 关键词={keyword}, 地区={area}")
        
        try:
            # 这里调用region_distribution_crawler的相应方法
            # 当前为占位实现
            result = {"status": 10000, "data": {"region_distribution": "示例地域分布数据"}}
            return result
        except Exception as e:
            log.error(f"获取地域分布出错: {str(e)}")
            return None


# 创建爬虫实例
baidu_index_spider = BaiduIndexSpider() 