"""
合并批次结果脚本，用于合并所有批次的数据
"""
import os
import pandas as pd
import glob
from datetime import datetime
# import sys
# 添加项目根目录到Python路径
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import log
from config.settings import OUTPUT_DIR


def merge_excel_files():
    """
    合并data_batches目录下的所有Excel文件
    """
    # 获取data_batches目录下的所有Excel文件
    data_batches_dir = os.path.join('data', 'data_batches')
    excel_files = glob.glob(os.path.join(data_batches_dir, 'batch_*.xlsx'))
    
    if not excel_files:
        log.warning("未找到Excel文件")
        return
    
    log.info(f"找到{len(excel_files)}个Excel文件，开始合并...")
    
    # 创建空的DataFrame列表，用于存储每个文件的数据
    dfs = []
    
    # 读取每个Excel文件并添加到列表中
    for file in excel_files:
        try:
            df = pd.read_excel(file)
            dfs.append(df)
            log.info(f"已读取: {file}")
        except Exception as e:
            log.error(f"读取{file}时出错: {e}")
    
    # 合并所有DataFrame
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        log.info(f"合并完成，共{len(combined_df)}行数据")
        
        # 创建输出目录
        merged_dir = os.path.join(OUTPUT_DIR, 'merged_results')
        if not os.path.exists(merged_dir):
            os.makedirs(merged_dir)
        
        # 检查列名
        log.info(f"数据列名: {list(combined_df.columns)}")
        
        # 确定排序列名
        sort_columns = []
        if '搜索关键词' in combined_df.columns:
            sort_columns.append('搜索关键词')
        elif 'keyword' in combined_df.columns:
            sort_columns.append('keyword')
            
        if '城市' in combined_df.columns:
            sort_columns.append('城市')
        elif 'area_code' in combined_df.columns:
            sort_columns.append('area_code')
        elif 'area_name' in combined_df.columns:
            sort_columns.append('area_name')
            
        if '年份' in combined_df.columns:
            sort_columns.append('年份')
        elif 'date' in combined_df.columns:
            sort_columns.append('date')
        
        # 按照确定的列名排序
        if sort_columns:
            log.info(f"正在按照以下列排序: {sort_columns}")
            combined_df = combined_df.sort_values(by=sort_columns)
        else:
            log.warning("未找到合适的排序列，跳过排序步骤")
        
        # 生成统计信息
        log.info("正在生成统计信息...")
        
        # 确定关键词列名
        keyword_column = '搜索关键词' if '搜索关键词' in combined_df.columns else 'keyword'
        area_column = '城市' if '城市' in combined_df.columns else ('area_code' if 'area_code' in combined_df.columns else 'area_name')
        year_column = '年份' if '年份' in combined_df.columns else 'date'
        
        # 统计关键词数量
        keywords = combined_df[keyword_column].unique()
        keyword_count = len(keywords)
        
        # 创建统计信息DataFrame
        stats_data = []
        
        # 统计每个关键词的数据
        for keyword in keywords:
            keyword_df = combined_df[combined_df[keyword_column] == keyword]
            
            # 获取地区数量
            if area_column in combined_df.columns:
                areas = keyword_df[area_column].unique()
                area_count = len(areas)
            else:
                area_count = 0
            
            # 获取年份或日期数量
            if year_column in combined_df.columns:
                if year_column == 'date' and pd.api.types.is_datetime64_any_dtype(combined_df[year_column]):
                    # 如果是日期类型，提取年份
                    years = keyword_df[year_column].dt.year.unique()
                else:
                    years = keyword_df[year_column].unique()
                year_count = len(years)
                
                # 统计每个关键词每年的数据条数
                for year in years:
                    if year_column == 'date' and pd.api.types.is_datetime64_any_dtype(combined_df[year_column]):
                        year_data = keyword_df[keyword_df[year_column].dt.year == year]
                    else:
                        year_data = keyword_df[keyword_df[year_column] == year]
                        
                    year_data_count = len(year_data)
                    
                    stats_data.append({
                        '关键词': keyword,
                        '年份': year,
                        '数据条数': year_data_count,
                        '地区数量': area_count,
                        '总年份数': year_count
                    })
            else:
                # 如果没有年份列，只统计总数
                stats_data.append({
                    '关键词': keyword,
                    '数据条数': len(keyword_df),
                    '地区数量': area_count
                })
        
        # 创建统计信息DataFrame并排序
        stats_df = pd.DataFrame(stats_data)
        if '年份' in stats_df.columns:
            stats_df = stats_df.sort_values(by=['关键词', '年份'])
        else:
            stats_df = stats_df.sort_values(by=['关键词'])
        
        # 将合并后的数据保存到一个总表中
        output_file = os.path.join(merged_dir, f"百度指数数据_{datetime.now().strftime('%Y%m%d')}.xlsx")
        combined_df.to_excel(output_file, index=False)
        log.info(f"已将合并后的总数据保存到 {output_file}")
        
        # 保存统计信息
        stats_file = os.path.join(merged_dir, "统计信息.xlsx")
        stats_df.to_excel(stats_file, index=False)
        log.info(f"已将统计信息保存到 {stats_file}")
        
        # 输出总体统计信息
        log.info("\n=== 统计信息摘要 ===")
        log.info(f"总关键词数量: {keyword_count}")
        log.info(f"总数据条数: {len(combined_df)}")
        
        # 按关键词统计地区数和年份/日期数
        if area_column in combined_df.columns and year_column in combined_df.columns:
            keyword_stats = combined_df.groupby(keyword_column).agg({
                area_column: 'nunique',
                year_column: 'nunique' if year_column != 'date' else lambda x: x.dt.year.nunique()
            }).reset_index()
            keyword_stats.columns = ['关键词', '地区数量', '年份数量']
            
            log.info("\n关键词统计:")
            for _, row in keyword_stats.iterrows():
                log.info(f"关键词: {row['关键词']} - 地区数: {row['地区数量']} - 年份数: {row['年份数量']}")
        
        log.info(f"\n处理完成，结果已保存到 {merged_dir} 目录")
    else:
        log.warning("没有成功读取任何数据")


if __name__ == "__main__":
    merge_excel_files() 