#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
搜索指数爬虫使用示例
"""
import os
import sys
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from spider.search_index_crawler import search_index_crawler
from utils.logger import log

def example_1_basic():
    """基本用法示例：爬取单个关键词的最近30天数据"""
    keywords = ["电脑"]
    search_index_crawler.crawl(keywords=keywords)

def example_2_multiple_keywords():
    """多关键词示例：爬取多个关键词的数据"""
    keywords = ["电脑", "手机", "平板"]
    search_index_crawler.crawl(keywords=keywords)

def example_3_custom_date():
    """自定义日期范围示例"""
    keywords = ["电脑"]
    date_ranges = [("2023-01-01", "2023-12-31")]
    search_index_crawler.crawl(keywords=keywords, date_ranges=date_ranges)

def example_4_multiple_cities():
    """多城市示例：爬取指定城市的数据"""
    keywords = ["电脑"]
    cities = {0: "全国", 514: "北京", 57: "上海", 95: "广州", 94: "深圳"}
    search_index_crawler.crawl(keywords=keywords, cities=cities)

def example_5_year_range():
    """按年份范围爬取数据"""
    keywords = ["电脑"]
    year_range = (2022, 2023)  # 爬取2022年到2023年的数据
    search_index_crawler.crawl(keywords=keywords, year_range=year_range)

def example_6_predefined_days():
    """使用预定义天数爬取数据"""
    keywords = ["电脑"]
    days = 90  # 爬取最近90天的数据
    search_index_crawler.crawl(keywords=keywords, days=days)

def example_7_resume_task():
    """恢复中断的任务"""
    task_id = "20240101123456"  # 替换为实际的任务ID
    search_index_crawler.resume_task(task_id)

def example_8_list_tasks():
    """列出所有任务及其状态"""
    tasks = search_index_crawler.list_tasks()
    for task in tasks:
        print(f"任务ID: {task['task_id']}, 进度: {task['progress']}")

def example_9_from_file():
    """从文件加载关键词和城市"""
    # 假设有以下文件:
    # keywords.txt: 每行一个关键词
    # cities.csv: 两列，第一列为城市代码，第二列为城市名称
    search_index_crawler.crawl(
        keywords_file="data/keywords.txt",
        cities_file="data/cities.csv",
        days=30
    )

def example_10_comprehensive():
    """综合示例：多关键词、多城市、自定义日期范围"""
    keywords = ["电脑", "手机", "平板"]
    cities = {0: "全国", 514: "北京", 57: "上海"}
    date_ranges = [
        ("2023-01-01", "2023-06-30"),
        ("2023-07-01", "2023-12-31")
    ]
    search_index_crawler.crawl(
        keywords=keywords,
        cities=cities,
        date_ranges=date_ranges
    )

if __name__ == "__main__":
    # 选择要运行的示例
    # example_1_basic()
    # example_3_custom_date()
    example_10_comprehensive()
    # 查看任务列表
    # example_8_list_tasks()
    
    # 恢复特定任务
    # example_7_resume_task() 