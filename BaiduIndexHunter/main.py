#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
百度指数爬虫主程序
"""
import os
import sys
import argparse
import pandas as pd
from datetime import datetime
from utils.logger import log
from spider.parallel_crawler import parallel_crawler
from utils.merge_batch_results import merge_excel_files
from utils.deduplicate import deduplicate_and_update_progress
from config.settings import SPIDER_CONFIG
from utils.city_manager import city_manager


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='百度指数爬虫')
    
    # 添加子命令
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # 爬取命令
    crawl_parser = subparsers.add_parser('crawl', help='爬取百度指数数据')
    crawl_parser.add_argument('-k', '--keywords_file', type=str, default='data/数字设备和服务关键词.xlsx',
                            help='关键词文件路径，默认为data/数字设备和服务关键词.xlsx')
    crawl_parser.add_argument('-c', '--city_file', type=str, default='data/275个城市及代码.xlsx',
                            help='城市代码文件路径，默认为data/275个城市及代码.xlsx')
    crawl_parser.add_argument('-y', '--years', type=str, default=str(datetime.now().year),
                            help='年份，多个年份用逗号分隔，默认为当前年份')
    crawl_parser.add_argument('-t', '--types', type=str, default='search',
                            help='指数类型，多个类型用逗号分隔，可选值: search, trend，默认为search')
    crawl_parser.add_argument('-w', '--workers', type=int, default=SPIDER_CONFIG.get('max_workers', 5),
                            help=f'工作线程数，默认为{SPIDER_CONFIG.get("max_workers", 5)}')
    crawl_parser.add_argument('-b', '--batch_size', type=int, default=10,
                            help='每个批次的任务数量，默认为10')
    
    # 合并命令
    merge_parser = subparsers.add_parser('merge', help='合并批次结果')
    
    # 去重复命令
    dedup_parser = subparsers.add_parser('deduplicate', help='去除重复数据并更新进度文件')
    
    # 测试命令
    test_parser = subparsers.add_parser('test', help='测试爬虫')
    test_parser.add_argument('-k', '--keyword', type=str, default='百度',
                           help='测试用的关键词，默认为"百度"')
    
    return parser.parse_args()


def load_cities(city_file):
    """
    从Excel文件加载城市代码
    :param city_file: 城市代码文件路径
    :return: 城市代码列表
    """
    try:
        df = pd.read_excel(city_file)
        if 'citycode' in df.columns and 'city' in df.columns:
            city_codes = df['citycode'].astype(int).tolist()
            # log.info(f"从 {city_file} 加载了 {len(city_codes)} 个城市代码")
            return city_codes
        else:
            log.error(f"城市代码文件格式不正确，需要包含'citycode'和'city'列")
            return [0]  # 默认返回全国代码
    except Exception as e:
        log.error(f"加载城市代码文件失败: {e}")
        return [0]  # 默认返回全国代码


def print_progress_info(progress_file):
    """
    打印爬取进度信息
    :param progress_file: 进度文件路径
    """
    import json
    import os
    
    if not os.path.exists(progress_file):
        log.info(f"进度文件 {progress_file} 不存在，将创建新的进度文件")
        return
    
    try:
        # 获取文件大小
        file_size = os.path.getsize(progress_file) / (1024 * 1024)  # 转换为MB
        # log.info(f"进度文件大小: {file_size:.2f} MB")
        
        # 读取进度文件的前10行和后10行来估计总任务数
        with open(progress_file, 'r', encoding='utf-8') as f:
            # 读取文件的第一行和最后一行来判断文件格式
            first_line = f.readline().strip()
            
            # 如果是空文件或只有{}，则没有进度
            if first_line == "{}" or not first_line:
                log.info("进度文件为空，没有已完成的任务")
                return
            
            # 重新打开文件计算任务数
            completed_tasks = 0
            successful_tasks = 0
            with open(progress_file, 'r', encoding='utf-8') as f:
                try:
                    progress_data = json.load(f)
                    completed_tasks = len(progress_data)
                    
                    # 统计成功的任务数量
                    for key, task_info in progress_data.items():
                        if task_info.get('status') == 'success':
                            successful_tasks += 1
                            
                    log.info(f"已完成任务数: {completed_tasks}")
                    log.info(f"其中成功任务数: {successful_tasks}")
                except json.JSONDecodeError:
                    log.error("进度文件格式错误，无法解析")
                    return
        
        return successful_tasks  # 返回成功的任务数量，而不是总任务数
    except Exception as e:
        log.error(f"读取进度文件失败: {e}")
        return None


def main():
    """主函数"""
    args = parse_arguments()
    
    if args.command == 'crawl':
        # 爬取百度指数数据
        log.info("开始爬取百度指数数据")
        
        # 解析参数
        keywords_file = args.keywords_file
        city_file = args.city_file
        
        # 解析年份，支持多年份爬取
        years_input = args.years.split(',')
        years = []
        for year_str in years_input:
            year_str = year_str.strip()
            # 检查是否是范围（例如：2016-2025）
            if '-' in year_str:
                start_year, end_year = map(int, year_str.split('-'))
                years.extend(range(start_year, end_year + 1))
            else:
                years.append(int(year_str))
        
        index_types = [t.strip() for t in args.types.split(',')]
        
        # 检查关键词文件是否存在
        if not os.path.exists(keywords_file):
            log.error(f"关键词文件不存在: {keywords_file}")
            return
            
        # 检查城市代码文件是否存在
        if not os.path.exists(city_file):
            log.error(f"城市代码文件不存在: {city_file}")
            return
        
        # 加载城市代码
        areas = load_cities(city_file)
        if not areas:
            log.error("未加载到城市代码，请检查城市代码文件")
            return
        
        # 加载关键词
        keywords = parallel_crawler.load_keywords(keywords_file)
        if not keywords:
            log.error("未加载到关键词，请检查关键词文件")
            return
        
        # 打印进度信息
        progress_file = os.path.join('data', 'crawler_progress.json')
        completed_tasks = print_progress_info(progress_file)
        
        # 计算理论总任务数
        total_tasks = len(keywords) * len(areas) * len(years) * len(index_types)
        log.info(f"理论总任务数: {total_tasks}")
        
        if completed_tasks is not None:
            remaining_tasks = total_tasks - completed_tasks
            progress_percentage = (completed_tasks / total_tasks) * 100 if total_tasks > 0 else 0
            # log.info(f"剩余任务数: {remaining_tasks}")
            log.info(f"当前进度: {progress_percentage:.2f}%")
        
        # 设置并行爬虫参数
        parallel_crawler.max_workers = args.workers
        parallel_crawler.batch_size = args.batch_size
        
        # 创建任务
        task_count = parallel_crawler.create_tasks(keywords, areas, years, index_types)
        if task_count == 0:
            log.warning("没有需要爬取的任务，可能所有任务已完成")
            return
        
        # 运行爬虫
        parallel_crawler.run()
        
        log.info("爬取完成")
        
    elif args.command == 'merge':
        # 合并批次结果
        log.info("开始合并批次结果")
        merge_excel_files()
        log.info("合并完成")
        
    elif args.command == 'deduplicate':
        # 去除重复数据并更新进度文件
        log.info("开始去除重复数据并更新进度文件")
        kept, removed, progress_count = deduplicate_and_update_progress()
        log.info(f"去重完成，保留 {kept} 条记录，删除 {removed} 条重复记录，进度文件包含 {progress_count} 条记录")
        
    elif args.command == 'test':
        # 测试爬虫
        from spider.baidu_index_api import baidu_index_api
        
        log.info(f"测试爬取关键词: {args.keyword}")
        
        # 获取当前年份
        current_year = datetime.now().year
        
        # 测试搜索指数API
        df = baidu_index_api.get_search_index(args.keyword, area=0, days=30)
        if df is not None and not df.empty:
            log.info(f"搜索指数API测试成功，获取到 {len(df)} 条数据")
        else:
            log.error("搜索指数API测试失败")
        
    else:
        # 显示帮助信息
        log.info("使用 -h 或 --help 查看帮助信息")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log.info("程序被用户中断")
        sys.exit(0)
    except Exception as e:
        log.error(f"程序异常: {e}")
        sys.exit(1)
