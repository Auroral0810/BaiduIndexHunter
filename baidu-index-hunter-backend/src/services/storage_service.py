"""
存储服务 - 负责各种格式（CSV, Excel, Pickle 等）的数据保存、加载和格式转换
"""
import pandas as pd
import os
import pickle
import sqlite3
from datetime import datetime
from src.core.logger import log

# 支持的输出格式及其文件扩展名
SUPPORTED_FORMATS = {
    'csv':     '.csv',
    'excel':   '.xlsx',
    'dta':     '.dta',
    'json':    '.json',
    'parquet': '.parquet',
    'sql':     '.sqlite',
}

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

    # --- 格式转换 (Format Conversion) ---

    def convert_csv_to_format(self, csv_path: str, target_format: str, table_name: str = 'data') -> str:
        """
        将 CSV 文件转换为指定格式。
        
        :param csv_path: 源 CSV 文件路径
        :param target_format: 目标格式 ('excel', 'dta', 'json', 'parquet', 'sql')
        :param table_name: SQL 格式时的表名
        :return: 转换后的文件路径，失败返回原始 csv_path
        """
        if target_format == 'csv' or target_format not in SUPPORTED_FORMATS:
            return csv_path
        
        if not os.path.exists(csv_path):
            log.warning(f"CSV 文件不存在，跳过转换: {csv_path}")
            return csv_path
        
        try:
            df = pd.read_csv(csv_path, encoding='utf-8-sig')
            if df.empty:
                log.warning(f"CSV 文件为空，跳过转换: {csv_path}")
                return csv_path
            
            # 构建输出路径（替换扩展名）
            base_path = os.path.splitext(csv_path)[0]
            ext = SUPPORTED_FORMATS[target_format]
            output_path = base_path + ext
            
            # 根据格式调用对应方法
            success = False
            if target_format == 'excel':
                success = self._convert_to_excel(df, output_path)
            elif target_format == 'dta':
                success = self._convert_to_dta(df, output_path)
            elif target_format == 'json':
                success = self._convert_to_json(df, output_path)
            elif target_format == 'parquet':
                success = self._convert_to_parquet(df, output_path)
            elif target_format == 'sql':
                success = self._convert_to_sql(df, output_path, table_name)
            
            if success:
                log.info(f"文件已转换: {csv_path} → {output_path}")
                return output_path
            else:
                return csv_path
                
        except Exception as e:
            log.error(f"格式转换失败 ({target_format}): {e}")
            return csv_path

    def _convert_to_excel(self, df: pd.DataFrame, output_path: str) -> bool:
        """转换为 Excel (.xlsx)"""
        try:
            df.to_excel(output_path, index=False, engine='openpyxl')
            return True
        except Exception as e:
            log.error(f"转换 Excel 失败: {e}")
            return False

    def _convert_to_dta(self, df: pd.DataFrame, output_path: str) -> bool:
        """转换为 Stata (.dta)"""
        try:
            # Stata 要求列名符合规范（不超过32字符，仅含字母/数字/下划线）
            import re
            df_copy = df.copy()
            new_cols = {}
            for col in df_copy.columns:
                clean = re.sub(r'[^\w]', '_', str(col))[:32]
                new_cols[col] = clean
            df_copy.rename(columns=new_cols, inplace=True)
            
            # 将 object 列转为 str，避免 Stata 类型错误
            for col in df_copy.select_dtypes(include=['object']).columns:
                df_copy[col] = df_copy[col].astype(str)
            
            df_copy.to_stata(output_path, write_index=False, version=118)
            return True
        except Exception as e:
            log.error(f"转换 DTA 失败: {e}")
            return False

    def _convert_to_json(self, df: pd.DataFrame, output_path: str) -> bool:
        """转换为 JSON (.json)"""
        try:
            df.to_json(output_path, orient='records', force_ascii=False, indent=2)
            return True
        except Exception as e:
            log.error(f"转换 JSON 失败: {e}")
            return False

    def _convert_to_parquet(self, df: pd.DataFrame, output_path: str) -> bool:
        """转换为 Parquet (.parquet)"""
        try:
            df.to_parquet(output_path, index=False, engine='pyarrow')
            return True
        except Exception as e:
            log.error(f"转换 Parquet 失败: {e}")
            return False

    def _convert_to_sql(self, df: pd.DataFrame, output_path: str, table_name: str = 'data') -> bool:
        """转换为 SQLite 数据库 (.sqlite)"""
        try:
            conn = sqlite3.connect(output_path)
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            conn.close()
            return True
        except Exception as e:
            log.error(f"转换 SQLite 失败: {e}")
            return False


# 全局单例
storage_service = StorageService()
