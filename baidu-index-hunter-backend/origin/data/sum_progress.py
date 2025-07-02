import os
import pandas as pd
from datetime import datetime
import sys
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import log

def count_progress_data():
    """
    统计crawler_progress.csv和result_data.csv的数据
    """
    # 统计crawler_progress.csv
    progress_file = '/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/data/crawler_progress.csv'
    if os.path.exists(progress_file):
        try:
            progress_df = pd.read_csv(progress_file)
            log.info(f"爬虫进度文件共有{len(progress_df)}行数据")
            
            # 统计关键词数量
            if 'keyword' in progress_df.columns:
                keywords = progress_df['keyword'].unique()
                keyword_count = len(keywords)
                log.info(f"共有{keyword_count}个不同的关键词")
                
                # 统计城市数量
                if 'area_code' in progress_df.columns:
                    areas = progress_df['area_code'].unique()
                    area_count = len(areas)
                    log.info(f"共有{area_count}个不同的城市")
                
                # 统计年份数量
                if 'year' in progress_df.columns:
                    years = progress_df['year'].unique()
                    year_count = len(years)
                    log.info(f"共有{year_count}个不同的年份")
                
                # 统计状态
                if 'status' in progress_df.columns:
                    status_counts = progress_df['status'].value_counts()
                    log.info(f"状态统计: {status_counts.to_dict()}")
        except Exception as e:
            log.error(f"读取爬虫进度文件时出错: {e}")
    else:
        log.warning(f"爬虫进度文件 {progress_file} 不存在")
    
    # 统计result_data.csv
    result_file = '/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/data/result_data.csv'
    if os.path.exists(result_file):
        try:
            result_df = pd.read_csv(result_file)
            log.info(f"结果数据文件共有{len(result_df)}行数据")
            
            # 统计关键词数量
            if '搜索关键词' in result_df.columns:
                keywords = result_df['搜索关键词'].unique()
                keyword_count = len(keywords)
                log.info(f"结果数据共有{keyword_count}个不同的关键词")
                
                # 统计城市数量
                if '城市' in result_df.columns:
                    areas = result_df['城市'].unique()
                    area_count = len(areas)
                    log.info(f"结果数据共有{area_count}个不同的城市")
                
                # 统计年份数量
                if '年份' in result_df.columns:
                    years = result_df['年份'].unique()
                    year_count = len(years)
                    log.info(f"结果数据共有{year_count}个不同的年份")
                
                # 统计每个关键词的数据量
                keyword_stats = result_df.groupby('搜索关键词').size().reset_index(name='数据量')
                keyword_stats = keyword_stats.sort_values('数据量', ascending=False)
                log.info(f"关键词数据量前10名: \n{keyword_stats.head(10)}")
                
                # 增强统计：计算每个关键词的城市和年份覆盖情况
                log.info("正在统计关键词任务状态...")
                
                # 确定列名
                keyword_column = '搜索关键词'
                area_column = '城市'
                year_column = '年份'
                
                # 按关键词统计城市数和年份数
                keyword_coverage = result_df.groupby(keyword_column).agg({
                    area_column: 'nunique',
                    year_column: 'nunique'
                }).reset_index()
                keyword_coverage.columns = ['关键词', '已完成城市数', '已完成年份数']
                
                # 计算每个关键词每年的城市覆盖情况
                keyword_year_stats = []
                for keyword in keywords:
                    keyword_df = result_df[result_df[keyword_column] == keyword]
                    years = keyword_df[year_column].unique()
                    
                    for year in years:
                        year_data = keyword_df[keyword_df[year_column] == year]
                        cities_count = year_data[area_column].nunique()
                        
                        keyword_year_stats.append({
                            '关键词': keyword,
                            '年份': year,
                            '已完成城市数': cities_count
                        })
                
                keyword_year_df = pd.DataFrame(keyword_year_stats)
                if not keyword_year_df.empty:
                    keyword_year_df = keyword_year_df.sort_values(by=['关键词', '年份'])
                    
                    # 保存详细统计结果到Excel
                    stats_dir = os.path.join('/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/data', 'stats')
                    if not os.path.exists(stats_dir):
                        os.makedirs(stats_dir)
                    
                    stats_file = os.path.join(stats_dir, f"关键词统计_{datetime.now().strftime('%Y%m%d')}.xlsx")
                    with pd.ExcelWriter(stats_file) as writer:
                        keyword_coverage.to_excel(writer, sheet_name='关键词覆盖统计', index=False)
                        keyword_year_df.to_excel(writer, sheet_name='关键词年份统计', index=False)
                    
                    log.info(f"已将关键词统计信息保存到 {stats_file}")
                    
                    # 输出部分统计结果
                    log.info("\n=== 关键词覆盖统计摘要 ===")
                    for _, row in keyword_coverage.head(10).iterrows():
                        log.info(f"关键词: {row['关键词']} - 城市数: {row['已完成城市数']} - 年份数: {row['已完成年份数']}")
                    
        except Exception as e:
            log.error(f"读取结果数据文件时出错: {e}")
    else:
        log.warning(f"结果数据文件 {result_file} 不存在")

def count_incomplete_tasks():
    """
    统计未完成的任务数量，对比关键词文件、城市代码文件与结果数据
    """
    log.info("开始统计未完成任务...")
    
    # 文件路径
    keywords_file = '/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/data/数字设备和服务关键词.xlsx'
    cities_file = '/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/data/275个城市及代码.xlsx'
    result_file = '/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/data/result_data.csv'
    
    # 读取关键词文件
    try:
        keywords_df = pd.read_excel(keywords_file)
        if '关键词' not in keywords_df.columns:
            log.error("关键词文件格式不正确，找不到'关键词'列")
            return
        all_keywords = keywords_df['关键词'].unique()
        keywords_count = len(all_keywords)
        log.info(f"关键词文件中共有{keywords_count}个关键词")
    except Exception as e:
        log.error(f"读取关键词文件时出错: {e}")
        return
    
    # 读取城市代码文件
    try:
        cities_df = pd.read_excel(cities_file)
        if 'citycode' not in cities_df.columns or 'city' not in cities_df.columns:
            log.error("城市代码文件格式不正确，找不到'citycode'或'city'列")
            return
        all_cities = cities_df['city'].unique()
        cities_count = len(all_cities)
        log.info(f"城市文件中共有{cities_count}个城市")
    except Exception as e:
        log.error(f"读取城市代码文件时出错: {e}")
        return
    
    # 年份范围
    start_year = 2016
    end_year = 2025
    years = list(range(start_year, end_year + 1))
    years_count = len(years)
    log.info(f"年份范围: {start_year}-{end_year}，共{years_count}年")
    
    # 计算总任务数
    total_tasks = keywords_count * cities_count * years_count
    log.info(f"理论总任务数: {keywords_count}(关键词) × {cities_count}(城市) × {years_count}(年份) = {total_tasks}")
    
    # 读取已有的结果数据
    if not os.path.exists(result_file):
        log.warning(f"结果数据文件 {result_file} 不存在，所有任务都未完成")
        return
    
    try:
        result_df = pd.read_csv(result_file)
        
        # 确定列名
        keyword_column = '搜索关键词' if '搜索关键词' in result_df.columns else None
        area_column = '城市' if '城市' in result_df.columns else None
        year_column = '年份' if '年份' in result_df.columns else None
        
        if not (keyword_column and area_column and year_column):
            log.error("结果数据文件缺少必要的列")
            return
        
        # 获取已完成的关键词、城市、年份组合
        completed_tasks = set()
        for _, row in result_df.iterrows():
            completed_tasks.add((row[keyword_column], row[area_column], row[year_column]))
        
        completed_count = len(completed_tasks)
        incomplete_count = total_tasks - completed_count
        completion_rate = completed_count / total_tasks * 100
        
        log.info(f"已完成任务数: {completed_count}")
        log.info(f"未完成任务数: {incomplete_count}")
        log.info(f"任务完成率: {completion_rate:.2f}%")
        
        # 统计每个关键词的完成情况
        keyword_completion = {}
        for keyword in all_keywords:
            keyword_tasks = sum(1 for task in completed_tasks if task[0] == keyword)
            expected_tasks = cities_count * years_count
            completion_rate = keyword_tasks / expected_tasks * 100
            keyword_completion[keyword] = {
                '已完成任务数': keyword_tasks,
                '总任务数': expected_tasks,
                '完成率': completion_rate
            }
        
        # 转换为DataFrame并排序
        keyword_completion_df = pd.DataFrame.from_dict(keyword_completion, orient='index').reset_index()
        keyword_completion_df.columns = ['关键词', '已完成任务数', '总任务数', '完成率']
        keyword_completion_df = keyword_completion_df.sort_values('完成率')
        
        # 保存统计结果
        stats_dir = os.path.join('/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/data', 'stats')
        if not os.path.exists(stats_dir):
            os.makedirs(stats_dir)
            
        incomplete_file = os.path.join(stats_dir, f"任务完成情况_{datetime.now().strftime('%Y%m%d')}.xlsx")
        keyword_completion_df.to_excel(incomplete_file, index=False)
        log.info(f"已将任务完成情况保存到 {incomplete_file}")
        
        # 输出完成率最低的10个关键词
        log.info("\n=== 完成率最低的关键词 ===")
        for _, row in keyword_completion_df.head(10).iterrows():
            log.info(f"关键词: {row['关键词']} - 完成率: {row['完成率']:.2f}% ({row['已完成任务数']}/{row['总任务数']})")
        
    except Exception as e:
        log.error(f"分析结果数据时出错: {e}")

def remove_duplicate_data():
    """
    删除重复的任务数据，确保每个关键词-城市-年份组合只有一条记录
    首先规范化城市名称，确保与城市代码文件中的格式一致
    """
    log.info("开始处理重复数据...")
    
    # 文件路径
    result_file = '/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/data/result_data.csv'
    cities_file = '/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/data/275个城市及代码.xlsx'
    
    if not os.path.exists(result_file):
        log.warning(f"结果数据文件 {result_file} 不存在，无法处理重复数据")
        return
    
    # 读取城市代码文件以获取有效城市列表
    try:
        cities_df = pd.read_excel(cities_file)
        if 'city' not in cities_df.columns:
            log.error("城市代码文件格式不正确，找不到'city'列")
            return
        valid_cities = set(cities_df['city'].unique())
        log.info(f"有效城市数量: {len(valid_cities)}")
        
        # 创建城市名称映射表（不带"市"到带"市"的映射）
        city_mapping = {}
        for city in valid_cities:
            if city.endswith('市'):
                city_without_suffix = city[:-1]
                city_mapping[city_without_suffix] = city
        
        log.info(f"创建了{len(city_mapping)}个城市名称映射关系")
    except Exception as e:
        log.error(f"读取城市代码文件时出错: {e}")
        return
    
    # 读取结果数据
    try:
        result_df = pd.read_csv(result_file)
        original_count = len(result_df)
        log.info(f"原始数据行数: {original_count}")
        
        # 确定列名
        keyword_column = '搜索关键词' if '搜索关键词' in result_df.columns else None
        area_column = '城市' if '城市' in result_df.columns else None
        year_column = '年份' if '年份' in result_df.columns else None
        
        if not (keyword_column and area_column and year_column):
            log.error("结果数据文件缺少必要的列")
            return
        
        # 1. 规范化城市名称
        log.info("开始规范化城市名称...")
        
        # 统计规范化前的城市数量
        original_cities = set(result_df[area_column].unique())
        log.info(f"规范化前的城市数量: {len(original_cities)}")
        
        # 创建一个新的DataFrame来存储规范化后的数据
        normalized_df = result_df.copy()
        
        # 规范化城市名称（添加"市"后缀）
        city_changes = 0
        for i, row in normalized_df.iterrows():
            city_name = row[area_column]
            if city_name not in valid_cities and city_name in city_mapping:
                normalized_df.at[i, area_column] = city_mapping[city_name]
                city_changes += 1
        
        log.info(f"规范化了{city_changes}行数据的城市名称")
        
        # 统计规范化后的城市数量
        normalized_cities = set(normalized_df[area_column].unique())
        log.info(f"规范化后的城市数量: {len(normalized_cities)}")
        
        # 2. 检查规范化后的城市是否都是有效城市
        invalid_cities = set(normalized_cities) - valid_cities
        if invalid_cities:
            log.info(f"规范化后仍有{len(invalid_cities)}个无效城市: {list(invalid_cities)[:10]}...")
            
            # 过滤出有效城市的数据
            valid_df = normalized_df[normalized_df[area_column].isin(valid_cities)]
            filtered_count = len(valid_df)
            log.info(f"过滤无效城市后的数据行数: {filtered_count}")
            log.info(f"移除了 {len(normalized_df) - filtered_count} 行无效城市数据")
        else:
            valid_df = normalized_df
            log.info("规范化后所有城市都是有效城市")
        
        # 3. 移除重复的关键词-城市-年份组合
        # 检查是否存在重复
        duplicates = valid_df.duplicated(subset=[keyword_column, area_column, year_column], keep=False)
        duplicate_count = duplicates.sum()
        
        if duplicate_count > 0:
            log.info(f"发现{duplicate_count}行重复数据")
            
            # 查看部分重复数据示例
            duplicate_examples = valid_df[duplicates].head(5)
            log.info(f"重复数据示例:\n{duplicate_examples}")
            
            # 获取重复最多的关键词
            duplicate_keywords = valid_df[duplicates][keyword_column].value_counts().head(5)
            log.info(f"重复最多的关键词:\n{duplicate_keywords}")
            
            # 删除重复项，保留第一个出现的记录
            dedup_df = valid_df.drop_duplicates(subset=[keyword_column, area_column, year_column], keep='first')
            dedup_count = len(dedup_df)
            log.info(f"去重后的数据行数: {dedup_count}")
            log.info(f"共删除了 {len(valid_df) - dedup_count} 行重复数据")
            
            # 检查每个关键词的城市数量是否正确
            keyword_city_counts = dedup_df.groupby(keyword_column)[area_column].nunique()
            log.info("去重后每个关键词的城市数量:")
            for keyword, count in keyword_city_counts.head(10).items():
                log.info(f"关键词: {keyword} - 城市数: {count}")
            
            # 保存去重后的数据
            output_dir = os.path.join('/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/data', 'cleaned')
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            output_file = os.path.join(output_dir, f"result_data_cleaned_{datetime.now().strftime('%Y%m%d')}.csv")
            dedup_df.to_csv(output_file, index=False)
            log.info(f"已将去重后的数据保存到 {output_file}")
            
            # 统计去重后的数据
            log.info("\n=== 去重后的数据统计 ===")
            log.info(f"关键词数量: {dedup_df[keyword_column].nunique()}")
            log.info(f"城市数量: {dedup_df[area_column].nunique()}")
            log.info(f"年份数量: {dedup_df[year_column].nunique()}")
            log.info(f"总数据量: {len(dedup_df)}")
            
            # 计算每个关键词的完成率
            keyword_completion = {}
            for keyword in dedup_df[keyword_column].unique():
                keyword_data = dedup_df[dedup_df[keyword_column] == keyword]
                city_year_pairs = keyword_data.groupby([area_column, year_column]).size().reset_index()
                completed_count = len(city_year_pairs)
                expected_count = len(valid_cities) * 10  # 假设10年
                completion_rate = (completed_count / expected_count) * 100
                
                keyword_completion[keyword] = {
                    '已完成数': completed_count,
                    '预期数': expected_count,
                    '完成率': completion_rate
                }
            
            # 转换为DataFrame并排序
            completion_df = pd.DataFrame.from_dict(keyword_completion, orient='index').reset_index()
            completion_df.columns = ['关键词', '已完成数', '预期数', '完成率']
            completion_df = completion_df.sort_values('完成率', ascending=False)
            
            # 保存完成率统计
            completion_file = os.path.join(output_dir, f"关键词完成率_{datetime.now().strftime('%Y%m%d')}.xlsx")
            completion_df.to_excel(completion_file, index=False)
            log.info(f"已将关键词完成率保存到 {completion_file}")
            
        else:
            log.info("未发现重复数据")
            
            # 即使没有重复数据，也保存规范化后的数据
            output_dir = os.path.join('/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/data', 'cleaned')
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            output_file = os.path.join(output_dir, f"result_data_normalized_{datetime.now().strftime('%Y%m%d')}.csv")
            valid_df.to_csv(output_file, index=False)
            log.info(f"已将规范化后的数据保存到 {output_file}")
            
    except Exception as e:
        log.error(f"处理重复数据时出错: {e}")
        import traceback
        log.error(traceback.format_exc())

if __name__ == "__main__":
    count_progress_data()
    count_incomplete_tasks()
    remove_duplicate_data()