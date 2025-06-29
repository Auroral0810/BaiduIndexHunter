#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
资讯指数爬虫使用示例
"""
import sys
import os
import time
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from spider.feed_index_crawler import feed_index_crawler
from utils.logger import log

def example_1_basic():
    """基本使用示例 - 爬取单个关键词最近30天的资讯指数"""
    log.info("示例1: 爬取单个关键词最近30天的资讯指数")
    feed_index_crawler.crawl(keywords=["电脑"])

def example_2_multiple_keywords():
    """多关键词示例 - 爬取多个关键词的资讯指数"""
    log.info("示例2: 爬取多个关键词的资讯指数")
    feed_index_crawler.crawl(keywords=["电脑", "手机", "平板"])

def example_3_custom_date():
    """自定义日期示例 - 爬取指定日期范围的资讯指数"""
    log.info("示例3: 爬取指定日期范围的资讯指数")
    date_ranges = [
        ("2023-01-01", "2023-12-31"),
        ("2024-01-01", "2024-06-30")
    ]
    feed_index_crawler.crawl(keywords=["电脑"], date_ranges=date_ranges)

def example_4_multiple_cities():
    """多城市示例 - 爬取指定城市的资讯指数"""
    log.info("示例4: 爬取指定城市的资讯指数")
    cities = {
        0: "全国",
        1: "济南",
        77: "青岛",
        514: "北京",
        57: "上海"
    }
    feed_index_crawler.crawl(keywords=["电脑"], cities=cities)

def example_5_year_range():
    """年份范围示例 - 爬取多个年份的资讯指数"""
    log.info("示例5: 爬取多个年份的资讯指数")
    feed_index_crawler.crawl(keywords=["电脑"], year_range=(2022, 2023))

def example_6_predefined_days():
    """预定义天数示例 - 爬取最近90天的资讯指数"""
    log.info("示例6: 爬取最近90天的资讯指数")
    feed_index_crawler.crawl(keywords=["电脑"], days=90)

def example_7_resume_task():
    """恢复任务示例 - 恢复之前中断的任务"""
    log.info("示例7: 恢复之前中断的任务")
    # 替换为实际的任务ID
    task_id = "20240101123456"  
    feed_index_crawler.resume_task(task_id)

def example_8_list_tasks():
    """列出任务示例 - 列出所有任务及其状态"""
    log.info("示例8: 列出所有任务及其状态")
    tasks = feed_index_crawler.list_tasks()
    for task in tasks:
        log.info(f"任务ID: {task['task_id']}, 进度: {task['progress']}")

def example_9_from_file():
    """从文件加载示例 - 从文件加载关键词和城市"""
    log.info("示例9: 从文件加载关键词和城市")
    # 替换为实际的文件路径
    keywords_file = "data/keywords.xlsx"
    cities_file = "data/cities.xlsx"
    feed_index_crawler.crawl(keywords_file=keywords_file, cities_file=cities_file)

def example_10_comprehensive():
    """综合示例 - 结合多个参数的复杂爬取任务"""
    log.info("示例10: 综合示例")
    cities = {
        0: "全国",
        514: "北京",
        57: "上海"
    }
    date_ranges = [
        ("2023-01-01", "2023-06-30"),
        ("2023-07-01", "2023-12-31")
    ]
    feed_index_crawler.crawl(
        keywords=["电脑", "手机", "平板"],
        cities=cities,
        date_ranges=date_ranges
    )

if __name__ == "__main__":
    # 执行示例1
    # example_1_basic()
    
    # 取消下面的注释来执行其他示例
    # example_2_multiple_keywords()
    # example_3_custom_date()
    # example_4_multiple_cities()
    # example_5_year_range()
    # example_6_predefined_days()
    # example_7_resume_task()
    # example_8_list_tasks()
    # example_9_from_file()
    example_10_comprehensive() 