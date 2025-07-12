#show_pkl.py
 
import pickle
path='/Users/auroral/ProjectDevelopment/BaiduIndexHunter/baidu-index-hunter-backend/output/checkpoints/search_index_checkpoint_20250713001942_ddd3e734.pkl'   #path='/root/……/aus_openface.pkl'   pkl文件所在路径
	   
f=open(path,'rb')
data=pickle.load(f)
 
print(data)
print(len(data))
