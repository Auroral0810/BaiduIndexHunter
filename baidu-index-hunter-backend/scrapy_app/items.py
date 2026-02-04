"""
Scrapy Items 数据模型定义

定义所有爬虫数据的结构化模型
"""
import scrapy
from scrapy import Field


class BaseItem(scrapy.Item):
    """基础数据项"""
    # 任务相关
    task_id = Field()
    # 爬取时间
    crawl_time = Field()


class SearchIndexDailyItem(BaseItem):
    """搜索指数日度数据项"""
    keyword = Field()          # 关键词
    city_code = Field()        # 城市代码
    city_name = Field()        # 城市名称
    date = Field()             # 日期 (YYYY-MM-DD)
    data_type = Field()        # 数据类型 (日度/周度)
    data_interval = Field()    # 数据间隔(天)
    year = Field()             # 所属年份
    all_index = Field()        # PC+移动指数
    wise_index = Field()       # 移动指数
    pc_index = Field()         # PC指数


class SearchIndexStatsItem(BaseItem):
    """搜索指数统计数据项"""
    keyword = Field()          # 关键词
    city_code = Field()        # 城市代码
    city_name = Field()        # 城市名称
    date_range = Field()       # 时间范围
    # 整体数据
    all_avg = Field()          # 整体日均值
    all_yoy = Field()          # 整体同比
    all_qoq = Field()          # 整体环比
    all_sum = Field()          # 整体总值
    # 移动数据
    wise_avg = Field()         # 移动日均值
    wise_yoy = Field()         # 移动同比
    wise_qoq = Field()         # 移动环比
    wise_sum = Field()         # 移动总值
    # PC数据
    pc_avg = Field()           # PC日均值
    pc_yoy = Field()           # PC同比
    pc_qoq = Field()           # PC环比
    pc_sum = Field()           # PC总值


class FeedIndexDailyItem(BaseItem):
    """资讯指数日度数据项"""
    keyword = Field()          # 关键词
    city_code = Field()        # 城市代码
    city_name = Field()        # 城市名称
    date = Field()             # 日期 (YYYY-MM-DD)
    data_type = Field()        # 数据类型 (日度/周度)
    data_interval = Field()    # 数据间隔(天)
    year = Field()             # 所属年份
    feed_index = Field()       # 资讯指数


class FeedIndexStatsItem(BaseItem):
    """资讯指数统计数据项"""
    keyword = Field()          # 关键词
    city_code = Field()        # 城市代码
    city_name = Field()        # 城市名称
    date_range = Field()       # 时间范围
    feed_avg = Field()         # 资讯日均值
    feed_yoy = Field()         # 资讯同比
    feed_qoq = Field()         # 资讯环比
    feed_sum = Field()         # 资讯总值


class WordGraphItem(BaseItem):
    """需求图谱数据项"""
    keyword = Field()          # 主关键词
    date = Field()             # 日期
    related_word = Field()     # 相关词
    word_type = Field()        # 词类型 (来源检索词/去向检索词)
    period = Field()           # 时间周期
    pv = Field()               # 搜索量
    ratio = Field()            # 占比


class DemographicItem(BaseItem):
    """人群属性数据项"""
    keyword = Field()          # 关键词
    # 年龄分布
    age_distribution = Field() # 年龄分布 (JSON格式)
    # 性别分布
    gender_distribution = Field()  # 性别分布 (JSON格式)
    # TGI指数
    age_tgi = Field()          # 年龄TGI指数 (JSON格式)
    gender_tgi = Field()       # 性别TGI指数 (JSON格式)


class InterestItem(BaseItem):
    """兴趣分布数据项"""
    keyword = Field()          # 关键词
    interest_category = Field()  # 兴趣分类
    interest_name = Field()    # 兴趣名称
    ratio = Field()            # 占比
    tgi = Field()              # TGI指数


class RegionDistributionItem(BaseItem):
    """地域分布数据项"""
    keyword = Field()          # 关键词
    date = Field()             # 日期
    province_code = Field()    # 省份代码
    province_name = Field()    # 省份名称
    city_code = Field()        # 城市代码
    city_name = Field()        # 城市名称
    ratio = Field()            # 占比
    rank = Field()             # 排名


class DecryptKeyItem(scrapy.Item):
    """解密密钥项（内部使用）"""
    uniqid = Field()           # 唯一标识
    key = Field()              # 解密密钥
    original_data = Field()    # 原始数据
    meta_info = Field()        # 元信息
