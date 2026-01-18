import pandas as pd

# 读取CSV文件
file_path = '/Users/auroral/Desktop/闲鱼/2026-1-18-百度指数(368关键词-周度-全部数据)/20260118200510_431ef895/feed_index_20260118200510_431ef895_daily_data.csv'

# 读取数据
df = pd.read_csv(file_path)

# 打印原始数据的列名，方便确认
print("数据列名:", df.columns.tolist())
print("\n" + "="*50 + "\n")

# 筛选条件：关键词等于"上海"，城市等于"北京"
filtered_df = df[(df['关键词'] == '上海') & (df['城市'] == '北京市')]

# 打印统计信息
print(f"筛选后的数据条数: {len(filtered_df)} 条")
print("\n" + "="*50 + "\n")

# 资讯指数的值分布
if '资讯指数' in df.columns:
    print("资讯指数统计信息:")
    print(filtered_df['资讯指数'].describe())
    print("\n")
    
    print("资讯指数值分布:")
    print(filtered_df['资讯指数'].value_counts().sort_index())
    print("\n")
    
    # 额外的分布信息
    print("资讯指数唯一值个数:", filtered_df['资讯指数'].nunique())
    print("资讯指数最小值:", filtered_df['资讯指数'].min())
    print("资讯指数最大值:", filtered_df['资讯指数'].max())
    print("资讯指数平均值:", filtered_df['资讯指数'].mean())
    print("资讯指数中位数:", filtered_df['资讯指数'].median())
else:
    print("警告: 数据中没有找到'资讯指数'列")
    print("可用的列:", df.columns.tolist())

# 可选：查看前几行数据
print("\n" + "="*50 + "\n")
print("筛选后的数据前5行:")
print(filtered_df.head())