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
            log.debug(f"数据已保存到 {output_file}")
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
            log.debug(f"数据已追加到 {output_file}")
            return True
        except Exception as e:
            log.error(f"追加数据到Excel失败: {e}")
            return False

    def save_to_csv(self, df, output_file):
        """将数据保存到CSV文件"""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            log.debug(f"数据已保存到 {output_file}")
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
            log.debug(f"数据已追加到 {output_file}")
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

    def count_csv_rows(self, filepath):
        """快速统计CSV文件行数（不包含表头）"""
        try:
            if not os.path.exists(filepath):
                return 0
            # 方式：使用缓冲区读取，适合大文件
            with open(filepath, 'rb') as f:
                # 跳过可能的BOM
                if f.read(3) != b'\xef\xbb\xbf':
                    f.seek(0)
                
                # 统计换行符数量
                lines = 0
                buffer_size = 8192
                while True:
                    buffer = f.read(buffer_size)
                    if not buffer:
                        break
                    lines += buffer.count(b'\n')
                
                # 减去表头行
                return max(0, lines - 1) if lines > 0 else 0
        except Exception as e:
            log.error(f"统计CSV行数失败: {e}")
            return 0

# 全局单例
storage_service = StorageService()
