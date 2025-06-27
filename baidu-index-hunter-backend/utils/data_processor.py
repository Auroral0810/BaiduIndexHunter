"""
百度指数数据处理模块
"""
import pandas as pd
from datetime import datetime
from utils.logger import log
from utils.city_manager import city_manager
import json


class BaiduIndexDataProcessor:
    """百度指数数据处理器，处理API返回的原始数据"""
    
    def __init__(self):
        # 添加一个标志来跟踪是否已经打印过第一次请求的数据
        self._first_data_printed = False
    
    def process_search_index_data(self, data, city_number, word, year=None, 
                                 data_frequency='year', data_source_type='all', data_type='trend'):
        """
        处理搜索指数数据
        :param data: API返回的原始数据
        :param city_number: 城市代码
        :param word: 搜索关键词
        :param year: 年份，如果为None则使用当前年份
        :param data_frequency: 数据频率，可选值：day, week, month, year
        :param data_source_type: 数据源类型，可选值：all, pc, mobile
        :param data_type: 数据类型，可选值：all, trend, map, portrait, news
        :return: 处理后的DataFrame或None（如果处理失败）
        """
        try:
            # 检查数据是否为空
            if data is None:
                log.error(f"处理搜索指数数据失败: 接收到的数据为None")
                return pd.DataFrame()
            
            # 检查数据结构是否完整
            if 'data' not in data:
                log.error(f"处理搜索指数数据失败: 数据中缺少'data'字段")
                return pd.DataFrame()
            
            if 'generalRatio' not in data['data'] or not data['data']['generalRatio']:
                log.error(f"处理搜索指数数据失败: 数据中缺少'generalRatio'字段或为空")
                return pd.DataFrame()
            
            if len(data['data']['generalRatio']) == 0:
                log.error(f"处理搜索指数数据失败: 'generalRatio'列表为空")
                return pd.DataFrame()
            
            # 获取城市名称
            city_name = city_manager.get_city_name(city_number) or f"未知城市({city_number})"
            
            # 如果未指定年份，使用当前年份
            if year is None:
                year = datetime.now().year
            
            # 获取统计数据
            general_ratio = data['data']['generalRatio'][0]
            
            # 检查general_ratio是否包含所需字段
            if 'all' not in general_ratio:
                log.error(f"处理搜索指数数据失败: 'generalRatio'中缺少'all'字段")
                return pd.DataFrame()
            
            if 'avg' not in general_ratio['all']:
                log.error(f"处理搜索指数数据失败: 'all'中缺少'avg'字段")
                return pd.DataFrame()
            
            all_avg = general_ratio['all']['avg']  # 整体日均值
            wise_avg = general_ratio.get('wise', {}).get('avg', 0)  # 移动日均值
            pc_avg = general_ratio.get('pc', {}).get('avg', 0)  # PC日均值
            
            # 计算年份的天数
            days_in_year = self._get_days_in_year(year)
            
            # 创建数据框
            df = pd.DataFrame({
                '搜索关键词': [word],
                '城市': [city_name],
                '城市编号': [city_number],
                '年份': [year],
                '整体日均值': [all_avg],
                '移动日均值': [wise_avg],
                'PC日均值': [pc_avg],
                '整体年总值': [all_avg * days_in_year],
                '移动年总值': [wise_avg * days_in_year],
                'PC年总值': [pc_avg * days_in_year],
                '爬取时间': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
            })
            
            # 打印第一次处理的DataFrame
            if self._first_data_printed and not hasattr(self, '_first_df_printed'):
                log.info("第一次处理的DataFrame:")
                log.info(f"\n{df.to_string()}")
                self._first_df_printed = True
            
            # 简化日志输出格式
            log.info(f"成功处理 {word} 在 {city_name} {year}年 的搜索指数数据")
            
            return df
            
        except Exception as e:
            log.error(f"处理搜索指数数据失败: {e}")
            return pd.DataFrame()  # 返回空DataFrame表示处理失败
    
    def process_trend_index_data(self, data, area, keyword, year=None,
                                data_frequency='week', data_source_type='all', data_type='all'):
        """
        处理趋势指数数据
        :param data: 原始数据
        :param area: 地区代码
        :param keyword: 关键词
        :param year: 年份
        :param data_frequency: 数据频率，可选值：day, week, month, year
        :param data_source_type: 数据源类型，可选值：all, pc, mobile
        :param data_type: 数据类型，可选值：all, trend, map, portrait, news
        :return: 处理后的DataFrame
        """
        try:
            # 检查数据是否为空
            if data is None:
                log.error(f"处理趋势指数数据失败: 接收到的数据为None")
                return pd.DataFrame()
            
            # 检查数据结构是否完整
            if 'data' not in data:
                log.error(f"处理趋势指数数据失败: 数据中缺少'data'字段")
                return pd.DataFrame()
            
            if 'index' not in data['data'] or not data['data']['index']:
                log.error(f"处理趋势指数数据失败: 数据中缺少'index'字段或为空")
                return pd.DataFrame()
            
            if len(data['data']['index']) == 0:
                log.error(f"处理趋势指数数据失败: 'index'列表为空")
                return pd.DataFrame()
            
            # 获取城市名称
            city_name = city_manager.get_city_name(area) or f"未知城市({area})"
            
            # 获取统计数据
            trend_data = data['data']['index'][0]
            
            # 检查trend_data是否包含所需字段
            if 'avg' not in trend_data:
                log.error(f"处理趋势指数数据失败: 'index'中缺少'avg'字段")
                trend_avg = 0  # 如果没有avg字段，使用0作为默认值
            else:
                trend_avg = trend_data.get('avg', 0)  # 趋势平均值
            
            # 计算年份的天数
            if year is None:
                year = datetime.now().year
            days_in_year = self._get_days_in_year(year)
            
            # 创建数据框
            df = pd.DataFrame({
                '搜索关键词': [keyword],
                '城市': [city_name],
                '城市编号': [area],
                '年份': [year],
                '趋势日均值': [trend_avg],
                '趋势年总值': [trend_avg * days_in_year],
                '爬取时间': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
            })
            
            # 打印第一次处理的DataFrame
            if self._first_data_printed and not hasattr(self, '_first_df_printed'):
                log.info("第一次处理的DataFrame:")
                log.info(f"\n{df.to_string()}")
                self._first_df_printed = True
            
            # 简化日志输出格式
            log.info(f"成功处理 {keyword} 在 {city_name} {year}年 的趋势指数数据")
            
            return df
            
        except Exception as e:
            log.error(f"处理趋势指数数据失败: {e}")
            return pd.DataFrame()  # 返回空DataFrame表示处理失败
    
    def _get_days_in_year(self, year):
        """
        计算指定年份的天数
        :param year: 年份
        :return: 天数
        """
        if year == 2025:  # 2025年只统计到6月23日
            return (datetime(2025, 6, 23) - datetime(2025, 1, 1)).days + 1
        elif (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):  # 闰年
            return 366
        else:  # 平年
            return 365
    
    def save_to_excel(self, df, output_file='百度指数数据.xlsx'):
        """
        将数据保存到Excel文件
        :param df: 要保存的DataFrame
        :param output_file: 输出文件名
        :return: 是否保存成功
        """
        try:
            df.to_excel(output_file, index=False)
            log.info(f"数据已保存到 {output_file}")
            return True
        except Exception as e:
            log.error(f"保存数据到Excel失败: {e}")
            return False
    
    def append_to_excel(self, df, output_file='百度指数数据.xlsx'):
        """
        将数据追加到现有Excel文件
        :param df: 要追加的DataFrame
        :param output_file: 输出文件名
        :return: 是否保存成功
        """
        try:
            # 尝试读取现有文件
            try:
                existing_df = pd.read_excel(output_file)
                # 合并数据
                combined_df = pd.concat([existing_df, df], ignore_index=True)
            except FileNotFoundError:
                # 如果文件不存在，直接使用新数据
                combined_df = df
            
            # 保存合并后的数据
            combined_df.to_excel(output_file, index=False)
            log.info(f"数据已追加到 {output_file}")
            return True
        except Exception as e:
            log.error(f"追加数据到Excel失败: {e}")
            return False


# 创建数据处理器单例
data_processor = BaiduIndexDataProcessor() 