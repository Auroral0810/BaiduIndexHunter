"""
百度指数爬取主程序
"""
import os
import argparse
import json
import time
import threading
from pathlib import Path
from utils.logger import log
from spider.task_manager import task_manager
from cookie_manager.cookie_rotator import cookie_rotator
from utils.city_manager import city_manager
from db.mysql_manager import mysql_manager
from db.redis_manager import redis_manager


# 定义全局路径配置
PATHS = {
    'cities_file': '/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/data/275个城市及代码.xlsx',
    'keywords_file': '/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/data/数字设备和服务关键词.xlsx',
    'progress_file': '/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/data/crawler_progress.csv',
    'result_file': '/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/data/result_data.csv',
    'output_dir': '/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/output'
}


def init_database():
    """初始化数据库连接"""
    # 连接MySQL数据库
    if not mysql_manager.connect():
        log.error("MySQL数据库连接失败")
        return False
    
    # 连接Redis数据库
    if not redis_manager.connect():
        log.error("Redis数据库连接失败")
        return False
    
    # 强制同步Cookie状态，确保Redis和MySQL数据一致
    log.info("强制同步MySQL和Redis中的Cookie数据...")
    cookie_rotator._sync_cookie_status()
    
    # 检查可用cookie数量
    all_ids = redis_manager.get_all_cached_cookie_ids()
    
    # 获取锁定的Cookie ID集合
    locked_ids = set(cookie_rotator.blocked_accounts)
    available_count = len([aid for aid in all_ids if aid not in locked_ids])
    
    log.info(f"已初始化数据库连接，可用Cookie数量: {available_count}/{len(all_ids)}")
    
    # 验证Redis和MySQL的一致性
    verify_db_consistency()
    
    return True


def verify_db_consistency():
    """验证Redis和MySQL数据一致性"""
    try:
        log.info("验证Redis和MySQL数据一致性...")
        
        # 获取MySQL中的所有cookie状态
        with mysql_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT account_id, is_available 
                FROM cookies
            """)
            mysql_cookies = {row['account_id']: row['is_available'] == 1 for row in cursor.fetchall()}
        
        # 获取Redis中的所有cookie ID
        redis_ids = set(redis_manager.get_all_cached_cookie_ids())
        
        # 获取Redis中的锁定状态
        redis_status = {}
        for account_id in redis_ids:
            redis_status[account_id] = not redis_manager.is_cookie_locked(account_id)
        
        # 检查MySQL中存在但Redis中不存在的cookie
        mysql_only = set(mysql_cookies.keys()) - redis_ids
        if mysql_only:
            log.warning(f"发现 {len(mysql_only)} 个账号在MySQL中存在但Redis中不存在")
            
        # 检查Redis中存在但MySQL中不存在的cookie
        redis_only = redis_ids - set(mysql_cookies.keys())
        if redis_only:
            log.warning(f"发现 {len(redis_only)} 个账号在Redis中存在但MySQL中不存在，将从Redis中移除")
            for account_id in redis_only:
                redis_manager.remove_cookie(account_id)
        
        # 检查状态不一致的cookie
        inconsistent = []
        for account_id in set(mysql_cookies.keys()) & redis_ids:
            if mysql_cookies[account_id] != redis_status.get(account_id, False):
                inconsistent.append(account_id)
        
        if inconsistent:
            log.warning(f"发现 {len(inconsistent)} 个账号的状态在MySQL和Redis中不一致，将进行修复")
            # 修复不一致的cookie状态
            for account_id in inconsistent:
                is_available = mysql_cookies[account_id]
                if is_available:
                    redis_manager.mark_cookie_available(account_id)
                    if account_id in cookie_rotator.blocked_accounts:
                        cookie_rotator.blocked_accounts.remove(account_id)
                        if account_id in cookie_rotator.block_times:
                            del cookie_rotator.block_times[account_id]
                else:
                    redis_manager.mark_cookie_locked(account_id)
                    cookie_rotator.blocked_accounts.add(account_id)
                    cookie_rotator.block_times[account_id] = time.time()
            
        log.info("Redis和MySQL数据一致性验证完成")
        return len(inconsistent) == 0
    except Exception as e:
        log.error(f"验证数据一致性失败: {e}")
        return False


def load_keywords_from_excel(keywords_file=None):
    """
    从Excel文件加载关键词列表
    :param keywords_file: 关键词文件路径
    :return: 关键词列表
    """
    try:
        import pandas as pd
        # 使用指定或默认的关键词文件
        if not keywords_file:
            keywords_file = PATHS['keywords_file']
        
        # 如果文件不存在
        if not os.path.exists(keywords_file):
            log.error(f"关键词Excel文件不存在: {keywords_file}")
            return []
        
        # 读取Excel文件
        df = pd.read_excel(keywords_file)
        
        # 获取第一列数据作为关键词
        if len(df.columns) > 0:
            keywords_col = df.iloc[:, 0]
            keywords = [str(keyword).strip() for keyword in keywords_col if str(keyword).strip()]
            log.info(f"已从Excel文件加载 {len(keywords)} 个关键词: {keywords_file}")
            return keywords
        else:
            log.error(f"关键词Excel文件格式错误: {keywords_file}")
            return []
    except Exception as e:
        log.error(f"加载Excel关键词文件失败: {e}")
        return []


def load_keywords(keywords_file=None, keywords_list=None):
    """
    加载关键词列表
    :param keywords_file: 关键词文件路径
    :param keywords_list: 直接传入的关键词列表
    :return: 关键词列表
    """
    if keywords_list:
        return keywords_list
    
    # 如果关键词文件是Excel文件，使用Excel加载方法
    if keywords_file and keywords_file.endswith(('.xlsx', '.xls')):
        return load_keywords_from_excel(keywords_file)
    
    # 使用默认Excel关键词文件
    if not keywords_file and os.path.exists(PATHS['keywords_file']):
        return load_keywords_from_excel(PATHS['keywords_file'])
    
    # 使用默认文本关键词文件
    if not keywords_file:
        keywords_file = Path(__file__).parent / 'data' / 'keywords.txt'
    
    # 如果文件不存在
    if not os.path.exists(keywords_file):
        log.error(f"关键词文件不存在: {keywords_file}")
        return []
    
    try:
        with open(keywords_file, 'r', encoding='utf-8') as f:
            keywords = [line.strip() for line in f if line.strip()]
        log.info(f"已从文件加载 {len(keywords)} 个关键词: {keywords_file}")
        return keywords
    except Exception as e:
        log.error(f"加载关键词文件失败: {e}")
        return []


def load_areas(areas_file=None, areas_list=None):
    """
    加载地区代码列表
    :param areas_file: 地区代码文件路径
    :param areas_list: 直接传入的地区代码列表
    :return: 地区代码列表
    """
    if areas_list:
        return [int(area) for area in areas_list]
    
    # 从城市配置文件加载
    if not areas_file and os.path.exists(PATHS['cities_file']):
        # 更新城市管理器的城市文件
        city_manager.city_file = PATHS['cities_file']
        city_manager.load_city_data()
        
        # 获取所有城市代码
        all_areas = city_manager.get_all_city_codes()
        log.info(f"已从城市配置文件加载 {len(all_areas)} 个城市代码")
        return all_areas
    
    # 使用默认地区代码文件
    if not areas_file:
        areas_file = Path(__file__).parent / 'data' / 'areas.txt'
    
    # 如果文件不存在，使用全国代码
    if not os.path.exists(areas_file):
        log.warning(f"地区代码文件不存在: {areas_file}，使用默认值（全国）")
        return [0]
    
    try:
        with open(areas_file, 'r', encoding='utf-8') as f:
            areas = [int(line.strip()) for line in f if line.strip() and line.strip().isdigit()]
        
        # 检查地区代码是否存在对应的城市名称
        valid_areas = []
        for area in areas:
            city_name = city_manager.get_city_name(area)
            if city_name:
                valid_areas.append(area)
            else:
                log.warning(f"未知的地区代码: {area}，跳过")
        
        log.info(f"已从文件加载 {len(valid_areas)} 个有效地区代码: {areas_file}")
        return valid_areas
    except Exception as e:
        log.error(f"加载地区代码文件失败: {e}")
        return [0]  # 默认返回全国


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='百度指数数据爬虫')
    
    # 基本参数
    parser.add_argument('-k', '--keywords', nargs='+', help='关键词列表，多个关键词用空格分隔')
    parser.add_argument('-kf', '--keywords-file', help='关键词文件路径，每行一个关键词')
    parser.add_argument('-a', '--areas', nargs='+', help='地区代码列表，多个地区用空格分隔')
    parser.add_argument('-af', '--areas-file', help='地区代码文件路径，每行一个地区代码')
    parser.add_argument('-y', '--years', nargs='+', type=int, default=[2016, 2025], 
                        help='年份列表，多个年份用空格分隔，默认为2016和2025年')
    parser.add_argument('-t', '--index-types', nargs='+', default=['search'], 
                        choices=['search', 'trend'], help='指数类型，可选值：search, trend，默认为search')
    
    # 系统参数
    parser.add_argument('-w', '--workers', type=int, help='最大工作线程数，默认根据CPU核心数和可用Cookie数量自动设置')
    parser.add_argument('-o', '--output', help='输出目录，默认为output')
    parser.add_argument('-v', '--verbose', action='store_true', help='输出详细日志')
    parser.add_argument('-p', '--progress-file', help='爬取进度文件路径')
    
    return parser.parse_args()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_args()
    
    # 设置日志级别
    if args.verbose:
        log.setLevel('DEBUG')
    
    # 设置进度文件路径
    if args.progress_file:
        progress_file = args.progress_file
    else:
        progress_file = PATHS['progress_file']
    
    # 确保数据目录存在
    os.makedirs(os.path.dirname(progress_file), exist_ok=True)
    
    # 初始化进度管理器，使用自定义进度文件路径
    from spider.progress_manager import ProgressManager
    progress_manager = ProgressManager(progress_file)
    log.info(f"使用进度文件: {progress_file}")
    
    # 设置输出目录
    output_dir = args.output or PATHS['output_dir']
    os.makedirs(output_dir, exist_ok=True)
    
    # 初始化数据库连接
    if not init_database():
        log.error("数据库初始化失败，程序退出")
        return
    
    # 启动定期数据一致性检查
    start_periodic_consistency_check()
    
    # 加载关键词
    keywords = load_keywords(args.keywords_file, args.keywords)
    if not keywords:
        log.error("未指定关键词，程序退出")
        return
    
    # 加载地区代码
    areas = load_areas(args.areas_file, args.areas)
    if not areas:
        log.error("未指定有效地区代码，程序退出")
        return
    
    # 设置年份
    years = args.years
    if len(years) == 2:
        # 如果只有起止年份，生成完整年份列表
        years = list(range(min(years), max(years) + 1))
    log.info(f"设置爬取年份: {years}")
    
    # 设置指数类型
    index_types = args.index_types
    log.info(f"设置爬取指数类型: {index_types}")
    
    # 确保全局progress_manager的实例与当前实例一致
    from spider.progress_manager import progress_manager as global_progress_manager
    global_progress_manager.progress_df = progress_manager.progress_df
    global_progress_manager.progress_file = progress_manager.progress_file
    
    # 设置最大工作线程数
    if args.workers:
        task_manager.max_workers = args.workers
        log.info(f"设置最大工作线程数: {args.workers}")
    
    # 设置输出目录
    task_manager.output_dir = Path(output_dir)
    os.makedirs(task_manager.output_dir, exist_ok=True)
    log.info(f"设置输出目录: {output_dir}")
    
    # 确保结果文件路径正确
    task_manager.results_file = Path(PATHS['result_file'])
    log.info(f"设置结果文件: {task_manager.results_file}")
    
    # 启动爬取任务
    log.info(f"开始爬取 {len(keywords)} 个关键词, {len(areas)} 个地区, {len(years)} 个年份, {len(index_types)} 种指数类型")
    if task_manager.start(keywords, areas, years, index_types):
        # 等待任务完成，并处理键盘中断
        try:
            # 打印初始状态
            time.sleep(2)  # 等待任务初始化
            
            # 等待任务完成
            while task_manager.running:
                time.sleep(5)
            
            log.info("所有爬取任务已完成")
        except KeyboardInterrupt:
            log.info("收到中断信号，正在停止爬取...")
            task_manager.stop()
    
    # 关闭数据库连接
    mysql_manager.close()
    log.info("程序执行完成")


def start_periodic_consistency_check():
    """启动定期数据一致性检查"""
    def consistency_check_task():
        while True:
            try:
                # 每30分钟检查一次数据一致性
                time.sleep(1800)
                log.info("执行定期MySQL和Redis数据一致性检查...")
                verify_db_consistency()
            except Exception as e:
                log.error(f"定期数据一致性检查任务出错: {e}")
                time.sleep(60)  # 出错后等待1分钟再重试
    
    # 启动检查线程
    check_thread = threading.Thread(target=consistency_check_task, daemon=True)
    check_thread.start()
    log.info("已启动定期MySQL和Redis数据一致性检查任务")


if __name__ == "__main__":
    main() 