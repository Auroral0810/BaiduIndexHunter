"""
存储服务 - 负责各种格式（CSV, Excel, Pickle）的数据保存和加载
"""
import pandas as pd
import os
import pickle
from datetime import datetime
from src.core.logger import log

class StorageService:
    """数据存储服务"""
    
    def __init__(self):
        pass

    def save_to_excel(self, df, output_file):
        """将数据保存到Excel文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            df.to_excel(output_file, index=False)
            log.info(f"数据已保存到 {output_file}")
            return True
        except Exception as e:
            log.error(f"保存数据到Excel失败: {e}")
            return False

    def append_to_excel(self, df, output_file):
        """将数据追加到现有Excel文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            if os.path.exists(output_file):
                existing_df = pd.read_excel(output_file)
                combined_df = pd.concat([existing_df, df], ignore_index=True)
            else:
                combined_df = df
            
            combined_df.to_excel(output_file, index=False)
            log.info(f"数据已追加到 {output_file}")
            return True
        except Exception as e:
            log.error(f"追加数据到Excel失败: {e}")
            return False

    def save_to_csv(self, df, output_file):
        """将数据保存到CSV文件"""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            log.info(f"数据已保存到 {output_file}")
            return True
        except Exception as e:
            log.error(f"保存数据到CSV失败: {e}")
            return False

    def append_to_csv(self, df, output_file):
        """将数据追加到现有CSV文件"""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            file_exists = os.path.exists(output_file) and os.path.getsize(output_file) > 0
            df.to_csv(output_file, mode='a', header=not file_exists, index=False, encoding='utf-8-sig')
            log.info(f"数据已追加到 {output_file}")
            return True
        except Exception as e:
            log.error(f"追加数据到CSV失败: {e}")
            return False

    def save_pickle(self, data, file_path):
        """保存数据到 Pickle 文件"""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            with open(file_path, 'wb') as f:
                pickle.dump(data, f)
            return True
        except Exception as e:
            log.error(f"保存 Pickle 失败: {e}")
            return False

    def load_pickle(self, file_path):
        """从 Pickle 文件加载数据"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    return pickle.load(f)
            return None
        except Exception as e:
            log.error(f"加载 Pickle 失败: {e}")
            return None

# 全局单例
storage_service = StorageService()
