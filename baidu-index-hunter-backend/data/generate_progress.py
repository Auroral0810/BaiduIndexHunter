import os
import pandas as pd
import datetime

# 文件路径
result_file = '/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/data/result_data.csv'
progress_file = '/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/data/crawler_progress.csv'

def generate_progress_file():
    """
    根据result_data.csv生成crawler_progress.csv
    """
    print("开始生成爬虫进度文件...")
    
    # 检查result_data.csv是否存在
    if not os.path.exists(result_file):
        print(f"结果数据文件 {result_file} 不存在")
        return
    
    try:
        # 读取result_data.csv
        result_df = pd.read_csv(result_file)
        print(f"读取到结果数据，共{len(result_df)}行")
        
        # 创建progress_df数据框
        progress_data = []
        
        # 处理每一行数据
        for _, row in result_df.iterrows():
            keyword = row['搜索关键词']
            area = row['城市编号']
            year = row['年份']
            
            # 生成task_key
            task_key = f"{keyword}_{area}_{year}"
            
            # 获取时间戳，如果有爬取时间则使用，否则使用当前时间
            if '爬取时间' in row and pd.notna(row['爬取时间']):
                try:
                    # 尝试将爬取时间转换为ISO格式
                    timestamp = pd.to_datetime(row['爬取时间']).isoformat()
                except:
                    # 如果转换失败，使用当前时间
                    timestamp = datetime.datetime.now().isoformat()
            else:
                timestamp = datetime.datetime.now().isoformat()
            
            # 添加到progress_data
            progress_data.append({
                'task_key': task_key,
                'keyword': keyword,
                'area': area,
                'year': year,
                'index_type': 'search',
                'status': 'success',
                'timestamp': timestamp
            })
        
        # 创建progress_df数据框
        progress_df = pd.DataFrame(progress_data)
        
        # 写入CSV文件
        progress_df.to_csv(progress_file, index=False)
        print(f"爬虫进度文件已生成，共{len(progress_df)}行数据")
        print(f"保存路径: {progress_file}")
        
    except Exception as e:
        print(f"生成爬虫进度文件时出错: {e}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    generate_progress_file() 