# 读取pkl文件
import pickle

with open('/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/output/checkpoints/search_index_checkpoint_20250714013422_d33f852e.pkl', 'rb') as f:
    data = pickle.load(f)

print(data)
