import pandas as pd
from datetime import datetime

# 读取 CSV 文件
file_path = '/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/output/search_index/20250710020050_3f755bfb/search_index_20250710020050_3f755bfb_daily_data.csv'  # 请替换为您的实际文件路径
df = pd.read_csv(file_path)

# 确保日期列是datetime格式
df['日期'] = pd.to_datetime(df['日期'])

print("="*60)
print("百度指数数据分析报告")
print("="*60)

# 1. 统计不同的关键词数量
unique_keywords = df['关键词'].unique()
num_unique_keywords = len(unique_keywords)
print(f"共有 {num_unique_keywords} 个不同的关键词")

# 2. 统计每个关键词下的不同城市数量
keyword_city_counts = df.groupby('关键词')['城市'].nunique()
print("\n每个关键词的不同城市数量：")
print(keyword_city_counts)

# 3. 检查每个城市下是否有重复数据（相同的关键词、城市和日期组合）
grouped = df.groupby(['关键词', '城市', '日期'])
duplicate_counts = grouped.size().reset_index(name='counts')
duplicates = duplicate_counts[duplicate_counts['counts'] > 1]

if not duplicates.empty:
    print("\n存在重复数据：")
    print(duplicates)
else:
    print("\n没有重复数据")

# 4. 剔除重复记录，保留第一个出现的记录
df_unique = df.drop_duplicates(subset=['关键词', '城市', '日期'], keep='first')
print(f"\n原始数据行数: {len(df)}")
print(f"去重后数据行数: {len(df_unique)}")

# 5. 新增：统计每个关键词在各城市的日期数量和范围
print("\n" + "="*60)
print("日期覆盖范围分析")
print("="*60)

# 整体数据的日期范围
overall_min_date = df_unique['日期'].min()
overall_max_date = df_unique['日期'].max()
print(f"整体数据日期范围: {overall_min_date.strftime('%Y-%m-%d')} 到 {overall_max_date.strftime('%Y-%m-%d')}")

# 计算理论上应有的总天数（从最早到最晚）
total_days_expected = (overall_max_date - overall_min_date).days + 1
print(f"理论总天数: {total_days_expected} 天")

# 按关键词和城市分组统计日期信息
keyword_city_date_stats = df_unique.groupby(['关键词', '城市']).agg({
    '日期': ['count', 'min', 'max']
}).reset_index()

# 简化列名
keyword_city_date_stats.columns = ['关键词', '城市', '日期数量', '最早日期', '最晚日期']

# 计算每个关键词-城市组合的日期跨度
keyword_city_date_stats['日期跨度天数'] = (keyword_city_date_stats['最晚日期'] - keyword_city_date_stats['最早日期']).dt.days + 1

# 计算覆盖率（实际天数/理论天数）
keyword_city_date_stats['覆盖率'] = keyword_city_date_stats['日期数量'] / keyword_city_date_stats['日期跨度天数']

print("\n每个关键词在各城市的日期统计:")
print(keyword_city_date_stats.to_string(index=False))

# 6. 检查是否包含2011-2025年的数据
print("\n" + "="*60)
print("2011-2025年数据覆盖情况")
print("="*60)

# 定义目标年份范围
target_start_year = 2011
target_end_year = 2025

# 提取年份
df_unique['年份'] = df_unique['日期'].dt.year

# 统计实际包含的年份
actual_years = sorted(df_unique['年份'].unique())
print(f"实际包含的年份: {actual_years}")

# 检查目标年份范围的覆盖情况
target_years = list(range(target_start_year, target_end_year + 1))
missing_years = [year for year in target_years if year not in actual_years]
extra_years = [year for year in actual_years if year not in target_years]

print(f"目标年份范围: {target_start_year}-{target_end_year}")
if missing_years:
    print(f"缺失的年份: {missing_years}")
else:
    print("✓ 包含了目标年份范围内的所有年份")

if extra_years:
    print(f"超出目标范围的年份: {extra_years}")

# 7. 按关键词统计年份覆盖情况
print("\n按关键词统计年份覆盖情况:")
keyword_year_stats = df_unique.groupby('关键词').agg({
    '年份': ['min', 'max', 'nunique']
}).reset_index()
keyword_year_stats.columns = ['关键词', '最早年份', '最晚年份', '年份数量']
keyword_year_stats['年份跨度'] = keyword_year_stats['最晚年份'] - keyword_year_stats['最早年份'] + 1

print(keyword_year_stats.to_string(index=False))

# 8. 数据完整性总结
print("\n" + "="*60)
print("数据完整性总结")
print("="*60)

total_combinations = len(keyword_city_date_stats)
complete_coverage = keyword_city_date_stats[keyword_city_date_stats['覆盖率'] >= 0.95]
incomplete_coverage = keyword_city_date_stats[keyword_city_date_stats['覆盖率'] < 0.95]

print(f"总关键词-城市组合数: {total_combinations}")
print(f"覆盖率≥95%的组合数: {len(complete_coverage)} ({len(complete_coverage)/total_combinations*100:.1f}%)")
print(f"覆盖率<95%的组合数: {len(incomplete_coverage)} ({len(incomplete_coverage)/total_combinations*100:.1f}%)")

if len(incomplete_coverage) > 0:
    print(f"\n覆盖率较低的组合:")
    low_coverage = incomplete_coverage.sort_values('覆盖率')[['关键词', '城市', '覆盖率']].head(10)
    print(low_coverage.to_string(index=False))

# 可选：将去重后的数据保存到新的 CSV 文件
df_unique.to_csv('unique_sample_data.csv', index=False)
print(f"\n去重后的数据已保存到 'unique_sample_data.csv'")

# 可选：将统计结果保存到Excel文件
with pd.ExcelWriter('baidu_index_analysis.xlsx') as writer:
    keyword_city_date_stats.to_excel(writer, sheet_name='关键词城市日期统计', index=False)
    keyword_year_stats.to_excel(writer, sheet_name='关键词年份统计', index=False)
    
print("详细统计结果已保存到 'baidu_index_analysis.xlsx'")