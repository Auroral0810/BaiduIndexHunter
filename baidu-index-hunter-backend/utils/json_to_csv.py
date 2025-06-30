#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import csv
import os

# 文件路径
json_file = '/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/data/crawler_progress.json'
csv_file = '/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/data/crawler_progress.csv'

# 列名
fieldnames = ['task_key', 'keyword', 'area', 'year', 'index_type', 'status', 'timestamp']

# 确保目标目录存在
os.makedirs(os.path.dirname(csv_file), exist_ok=True)

# 读取JSON文件
with open(json_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 将JSON数据转换为CSV格式
with open(csv_file, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    
    for task_key, values in data.items():
        row = values.copy()
        row['task_key'] = task_key
        writer.writerow(row)

print(f'转换完成！CSV文件已保存到: {csv_file}') 