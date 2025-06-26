"""
去重复工具，用于去除重复数据并更新爬虫进度文件
"""
import os
import pandas as pd
import json
import glob
from datetime import datetime
import sys
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.logger import log
from config.settings import OUTPUT_DIR


def deduplicate_and_update_progress():
    """
    去除重复数据并更新爬虫进度文件
    """
    # 获取data_batches目录下的所有Excel文件
    data_batches_dir = os.path.join('data', 'data_batches')
    batch_files = sorted(glob.glob(os.path.join(data_batches_dir, 'batch_*.xlsx')))
    
    if not batch_files:
        log.warning("未找到Excel文件")
        return
    
    # 读取所有文件
    log.info(f"正在读取 {len(batch_files)} 个Excel文件...")
    file_data = {}
    for file in batch_files:
        try:
            df = pd.read_excel(file)
            file_data[file] = df
            log.info(f"成功读取 {file}，包含 {len(df)} 行数据")
        except Exception as e:
            log.error(f"读取 {file} 出错: {e}")
    
    if not file_data:
        log.warning("没有找到有效数据文件")
        return
    
    # 检查第一个文件的列名，确定关键字段
    sample_df = next(iter(file_data.values()))
    columns = sample_df.columns.tolist()
    
    # 确定关键列名
    keyword_column = '搜索关键词' if '搜索关键词' in columns else 'keyword'
    area_column = '城市' if '城市' in columns else ('area_name' if 'area_name' in columns else 'area_code')
    area_code_column = '城市编号' if '城市编号' in columns else ('area_code' if 'area_code' in columns else None)
    year_column = '年份' if '年份' in columns else None
    date_column = 'date' if 'date' in columns else None
    
    log.info(f"使用以下列作为唯一标识: 关键词={keyword_column}, 地区={area_column}, 年份/日期={year_column or date_column}")
    
    # 记录每个唯一组合首次出现的文件
    first_occurrence = {}  # (关键词, 地区, 年份/日期) -> 文件
    
    for file, df in file_data.items():
        for i, row in df.iterrows():
            # 构建唯一键
            if year_column:
                key = (row[keyword_column], row[area_column], row[year_column])
            elif date_column and pd.api.types.is_datetime64_any_dtype(df[date_column]):
                # 如果有日期列且为日期类型，使用年份作为键的一部分
                key = (row[keyword_column], row[area_column], row[date_column].year)
            else:
                # 没有年份或日期信息，只用关键词和地区
                key = (row[keyword_column], row[area_column])
            
            if key not in first_occurrence:
                first_occurrence[key] = file
    
    # 过滤每个文件，只保留首次出现的条目
    total_kept = 0
    total_removed = 0
    
    for file, df in file_data.items():
        rows_to_keep = []
        for i, row in df.iterrows():
            # 构建唯一键
            if year_column:
                key = (row[keyword_column], row[area_column], row[year_column])
            elif date_column and pd.api.types.is_datetime64_any_dtype(df[date_column]):
                key = (row[keyword_column], row[area_column], row[date_column].year)
            else:
                key = (row[keyword_column], row[area_column])
            
            if first_occurrence[key] == file:
                rows_to_keep.append(True)
                total_kept += 1
            else:
                rows_to_keep.append(False)
                total_removed += 1
        
        # 更新DataFrame，只包含要保留的行
        file_data[file] = df[rows_to_keep].reset_index(drop=True)
    
    log.info(f"保留了 {total_kept} 条唯一记录，删除了 {total_removed} 条重复记录")
    
    # 从去重后的数据创建进度JSON文件
    progress_data = {}
    now = datetime.now().isoformat()
    progress_file = os.path.join('data', 'crawler_progress.json')
    
    # 如果进度文件存在，先读取现有内容
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r', encoding='utf-8') as f:
                progress_data = json.load(f)
            log.info(f"读取现有进度文件，包含 {len(progress_data)} 条记录")
        except Exception as e:
            log.error(f"读取进度文件出错: {e}")
    
    # 更新进度数据
    for file, df in file_data.items():
        for _, row in df.iterrows():
            # 确定关键词、地区代码和年份
            keyword = row[keyword_column]
            
            # 确定地区代码
            if area_code_column and area_code_column in row:
                area_code = row[area_code_column]
            else:
                area_code = row[area_column] if isinstance(row[area_column], (int, float)) else 0
            
            # 确定年份
            if year_column and year_column in row:
                year = row[year_column]
            elif date_column and date_column in row and pd.api.types.is_datetime64_any_dtype(pd.Series([row[date_column]])):
                year = row[date_column].year
            else:
                year = datetime.now().year
            
            # 构建键
            key = f"{keyword}_{int(area_code)}_{int(year)}"
            
            # 更新进度数据
            progress_data[key] = {
                "keyword": keyword,
                "area": int(area_code),
                "index_type": "search",  # 默认为搜索指数
                "year": int(year),
                "status": "success",
                "timestamp": now
            }
    
    # 保存更新后的进度JSON文件
    try:
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress_data, f, ensure_ascii=False, indent=2)
        log.info(f"更新了进度文件，包含 {len(progress_data)} 条记录")
    except Exception as e:
        log.error(f"保存进度文件出错: {e}")
    
    # 将去重后的数据保存回原始批次文件
    for file, df in file_data.items():
        try:
            if len(df) > 0:
                df.to_excel(file, index=False)
                log.info(f"更新文件 {file}，去重后包含 {len(df)} 行")
            else:
                df.to_excel(file, index=False)
                log.warning(f"文件 {file} 去重后为空（全是重复数据）")
        except Exception as e:
            log.error(f"保存文件 {file} 出错: {e}")
    
    # 汇总报告
    log.info("\n去重完成！")
    log.info(f"总保留记录: {total_kept}")
    log.info(f"总删除重复: {total_removed}")
    log.info(f"更新进度文件记录数: {len(progress_data)}")
    
    return total_kept, total_removed, len(progress_data)


if __name__ == "__main__":
    deduplicate_and_update_progress() 