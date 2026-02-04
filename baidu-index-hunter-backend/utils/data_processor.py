"""
百度指数数据处理模块
"""
import pandas as pd
import os
from datetime import datetime, timedelta
from utils.logger import log
from region_manager.region_manager import get_region_manager
import json
import traceback

# 获取region_manager实例
region_manager = get_region_manager()

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
            city_name = region_manager.get_city_name_by_code(city_number) or f"未知城市({city_number})"
            
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
            
            # 简化日志输出，减少IO操作
            # log.info(f"成功处理 {word} 在 {city_name} {year}年 的搜索指数数据")
            
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
            city_name = region_manager.get_city_name_by_code(area) or f"未知城市({area})"
            
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
            
            # 简化日志输出，减少IO操作
            # log.info(f"成功处理 {keyword} 在 {city_name} {year}年 的趋势指数数据")
            
            return df
            
        except Exception as e:
            log.error(f"处理趋势指数数据失败: {e}")
            return pd.DataFrame()  # 返回空DataFrame表示处理失败
    
    def process_word_graph_data(self, data, keyword, datelist):
        """
        处理需求图谱数据
        :param data: API返回的原始数据
        :param keyword: 关键词
        :param datelist: 日期，格式为YYYYMMDD
        :return: 处理后的DataFrame或None（如果处理失败）
        """
        try:
            # 检查数据是否为空
            if data is None:
                log.error(f"处理需求图谱数据失败: 接收到的数据为None")
                return pd.DataFrame()
            
            # 检查数据结构是否完整
            if 'status' not in data or data['status'] != 0:
                error_msg = data.get('message', '未知错误') if data else '未知错误'
                log.error(f"处理需求图谱数据失败: API返回错误: {error_msg}")
                return pd.DataFrame()
            
            if 'data' not in data:
                log.error(f"处理需求图谱数据失败: 数据中缺少'data'字段")
                return pd.DataFrame()
            
            # 获取数据
            api_data = data['data']
            period_raw = api_data.get('period', '')
            
            # Format period: 20250126|20251214 -> 2025-01-26-2025-12-14 (Logic from test.py)
            if '|' in period_raw:
                try:
                    p_start = period_raw.split('|')[0]
                    p_end = period_raw.split('|')[1]
                    period = f"{p_start[:4]}-{p_start[4:6]}-{p_start[6:]}-{p_end[:4]}-{p_end[4:6]}-{p_end[6:]}"
                except:
                    period = period_raw
            else:
                period = period_raw
            
            # 初始化结果列表
            results = []
            
            # 处理每个关键词的数据
            for word_item in api_data.get('wordlist', []):
                item_keyword = word_item.get('keyword', keyword)
                word_graph = word_item.get('wordGraph', [])
                
                # 如果没有相关词数据，添加一个空行
                if not word_graph:
                    results.append({
                        '关键词': item_keyword,
                        '相关词': '',
                        '搜索量': 0,
                        '变化率': 0,
                        '相关度': 0,
                        '数据周期': period,
                        '日期': datelist,
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    continue
                
                # 处理每个相关词
                for item in word_graph:
                    related_word = item.get('word', '')
                    pv = item.get('pv', 0)
                    ratio = item.get('ratio', 0)
                    sim = item.get('sim', 0)
                    
                    results.append({
                        '关键词': item_keyword,
                        '相关词': related_word,
                        '搜索量': pv,
                        '变化率': ratio,
                        '相关度': sim,
                        '数据周期': period,
                        '日期': datelist,
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            # 创建DataFrame
            df = pd.DataFrame(results)
            
            # 打印日志
            log.info(f"成功处理 {keyword} 的需求图谱数据，共 {len(df)} 条相关词记录")
            
            return df
            
        except Exception as e:
            log.error(f"处理需求图谱数据失败: {e}")
            return pd.DataFrame()  # 返回空DataFrame表示处理失败
    
    def process_demographic_data(self, data, query_keyword=None):
        """
        处理人群属性数据
        :param data: API返回的原始数据
        :param query_keyword: 查询的关键词，用于日志记录
        :return: 处理后的数据记录DataFrame
        """
        try:
            # 检查数据是否为空或结构不完整
            if data is None or 'status' not in data or data['status'] != 0:
                log.error(f"处理人群属性数据失败: 数据为空或API返回错误")
                return pd.DataFrame()
            
            if 'data' not in data or 'result' not in data['data']:
                log.error(f"处理人群属性数据失败: 数据结构不完整")
                return pd.DataFrame()
            
            # 获取数据
            api_data = data['data']
            result = api_data.get('result', [])
            start_date = api_data.get('startDate', '')
            end_date = api_data.get('endDate', '')
            period = f"{start_date} 至 {end_date}"
            
            # 初始化结果列表
            data_records = []
            
            # 分离关键词数据和全网分布数据
            keyword_items = []
            overall_item = None
            
            for item in result:
                if item.get('word') == "全网分布":
                    overall_item = item
                else:
                    keyword_items.append(item)
            
            # 处理关键词数据
            for item in keyword_items:
                word = item.get('word', query_keyword)
                
                # 处理性别分布
                gender_data = item.get('gender', [])
                for gender in gender_data:
                    desc = gender.get('desc', '')
                    tgi = gender.get('tgi', '')
                    rate = gender.get('rate', 0)
                    
                    data_records.append({
                        '关键词': word,
                        '属性类型': '性别',
                        '属性值': desc,
                        '比例': rate,
                        'TGI': tgi,
                        '数据周期': period,
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                # 处理年龄分布
                age_data = item.get('age', [])
                for age in age_data:
                    desc = age.get('desc', '')
                    tgi = age.get('tgi', '')
                    rate = age.get('rate', 0)
                    
                    data_records.append({
                        '关键词': word,
                        '属性类型': '年龄',
                        '属性值': f"{desc}岁",
                        '比例': rate,
                        'TGI': tgi,
                        '数据周期': period,
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                # 处理学历分布（如果有）
                education_data = item.get('education', [])
                for edu in education_data:
                    desc = edu.get('desc', '')
                    tgi = edu.get('tgi', '')
                    rate = edu.get('rate', 0)
                    
                    data_records.append({
                        '关键词': word,
                        '属性类型': '学历',
                        '属性值': desc,
                        '比例': rate,
                        'TGI': tgi,
                        '数据周期': period,
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                # 处理兴趣分布（如果有）
                interest_data = item.get('interest', [])
                for interest in interest_data:
                    desc = interest.get('desc', '')
                    tgi = interest.get('tgi', '')
                    rate = interest.get('rate', 0)
                    
                    data_records.append({
                        '关键词': word,
                        '属性类型': '兴趣',
                        '属性值': desc,
                        '比例': rate,
                        'TGI': tgi,
                        '数据周期': period,
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            # 处理全网分布数据（如果有）
            if overall_item:
                # 处理性别分布
                gender_data = overall_item.get('gender', [])
                for gender in gender_data:
                    desc = gender.get('desc', '')
                    tgi = gender.get('tgi', '')
                    rate = gender.get('rate', 0)
                    
                    data_records.append({
                        '关键词': '全网分布',
                        '属性类型': '性别',
                        '属性值': desc,
                        '比例': rate,
                        'TGI': tgi,
                        '数据周期': period,
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                # 处理年龄分布
                age_data = overall_item.get('age', [])
                for age in age_data:
                    desc = age.get('desc', '')
                    tgi = age.get('tgi', '')
                    rate = age.get('rate', 0)
                    
                    data_records.append({
                        '关键词': '全网分布',
                        '属性类型': '年龄',
                        '属性值': f"{desc}岁",
                        '比例': rate,
                        'TGI': tgi,
                        '数据周期': period,
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                # 处理学历分布（如果有）
                education_data = overall_item.get('education', [])
                for edu in education_data:
                    desc = edu.get('desc', '')
                    tgi = edu.get('tgi', '')
                    rate = edu.get('rate', 0)
                    
                    data_records.append({
                        '关键词': '全网分布',
                        '属性类型': '学历',
                        '属性值': desc,
                        '比例': rate,
                        'TGI': tgi,
                        '数据周期': period,
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                # 处理兴趣分布（如果有）
                interest_data = overall_item.get('interest', [])
                for interest in interest_data:
                    desc = interest.get('desc', '')
                    tgi = interest.get('tgi', '')
                    rate = interest.get('rate', 0)
                    
                    data_records.append({
                        '关键词': '全网分布',
                        '属性类型': '兴趣',
                        '属性值': desc,
                        '比例': rate,
                        'TGI': tgi,
                        '数据周期': period,
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            # 创建DataFrame
            df = pd.DataFrame(data_records)
            
            # 打印日志
            if query_keyword:
                log.info(f"成功处理 {query_keyword} 的人群属性数据，共 {len(df)} 条记录")
            else:
                log.info(f"成功处理人群属性数据，共 {len(df)} 条记录")
            
            return df
            
        except Exception as e:
            log.error(f"处理人群属性数据失败: {e}")
            return pd.DataFrame()  # 返回空DataFrame表示处理失败
    
    def process_interest_profile_data(self, data, specific_typeid=None):
        """
        处理兴趣分布数据
        :param data: API返回的原始数据
        :param specific_typeid: 特定的兴趣类型ID，用于日志记录
        :return: 处理后的数据记录DataFrame
        """
        try:
            # 检查数据是否为空或结构不完整
            if data is None or 'status' not in data or data['status'] != 0:
                log.error(f"处理兴趣分布数据失败: 数据为空或API返回错误")
                return pd.DataFrame()
            
            if 'data' not in data or 'result' not in data['data']:
                log.error(f"处理兴趣分布数据失败: 数据结构不完整")
                return pd.DataFrame()
            
            # 获取数据
            api_data = data['data']
            result = api_data.get('result', [])
            start_date = api_data.get('startDate', '')
            end_date = api_data.get('endDate', '')
            period = f"{start_date} 至 {end_date}"
            
            # 初始化结果列表
            data_records = []
            
            # 分离关键词数据和全网分布数据
            keyword_items = []
            overall_item = None
            
            for item in result:
                if item.get('word') == "全网分布":
                    overall_item = item
                else:
                    keyword_items.append(item)
            
            # 处理关键词数据
            # API返回的interest数组已经是top10，直接使用，不需要排序和限制
            for item in keyword_items:
                word = item.get('word', '')
                
                # 直接使用API返回的interest数组（已经是top10）
                interest_data = item.get('interest', [])
                
                for interest in interest_data:
                    desc = interest.get('desc', '')
                    tgi = interest.get('tgi', '')
                    # 处理TGI为空字符串的情况
                    if tgi == '' or tgi is None:
                        tgi = '-'
                    rate = interest.get('rate', 0)
                    type_id = interest.get('typeId', '')
                    
                    data_records.append({
                        '关键词': word,
                        '兴趣类型': desc,
                        '比例': rate,
                        'TGI': tgi,
                        '类型ID': type_id,
                        '数据周期': period,
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            # 处理全网分布数据（如果有）
            # API返回的interest数组已经是top10，直接使用，不需要排序和限制
            if overall_item:
                interest_data = overall_item.get('interest', [])
                
                for interest in interest_data:
                    desc = interest.get('desc', '')
                    tgi = interest.get('tgi', '')
                    # 处理TGI为空字符串的情况（全网分布的TGI通常为空）
                    if tgi == '' or tgi is None:
                        tgi = '-'
                    rate = interest.get('rate', 0)
                    type_id = interest.get('typeId', '')
                    
                    data_records.append({
                        '关键词': '全网分布',
                        '兴趣类型': desc,
                        '比例': rate,
                        'TGI': tgi,
                        '类型ID': type_id,
                        '数据周期': period,
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            # 创建DataFrame
            df = pd.DataFrame(data_records)
            
            # 打印日志
            type_info = f"类型ID: {specific_typeid}" if specific_typeid else "所有兴趣类型"
            log.info(f"成功处理兴趣分布数据，{type_info}，共 {len(df)} 条记录")
            
            return df
            
        except Exception as e:
            log.error(f"处理兴趣分布数据失败: {e}")
            return pd.DataFrame()  # 返回空DataFrame表示处理失败
    
    def process_region_distribution_data(self, data, region_code=0, keyword=None, start_date=None, end_date=None):
        """
        处理地域分布数据
        :param data: API返回的原始数据
        :param region_code: 地区代码，0表示全国
        :param keyword: 关键词（用于空数据构造）
        :param start_date: 开始日期（用于空数据构造）
        :param end_date: 结束日期（用于空数据构造）
        :return: 处理后的DataFrame
        """
        try:
            # 检查数据是否为空或结构不完整
            if data is None or 'status' not in data or data['status'] != 0:
                log.warning(f"处理地域分布数据失败: 数据为空或API返回错误, keyword={keyword}, region={region_code}")
                # 如果提供了keyword和日期，构造空数据记录
                if keyword and start_date:
                    return self._create_empty_region_data(keyword, region_code, start_date, end_date)
                return pd.DataFrame()
            
            if 'data' not in data or 'region' not in data['data']:
                log.warning(f"处理地域分布数据失败: 数据结构不完整, keyword={keyword}, region={region_code}")
                # 如果提供了keyword和日期，构造空数据记录
                if keyword and start_date:
                    return self._create_empty_region_data(keyword, region_code, start_date, end_date)
                return pd.DataFrame()
            
            # 获取数据
            region_data = data['data']['region']
            
            # 如果region_data为空，构造空数据记录
            if not region_data or len(region_data) == 0:
                log.warning(f"地域分布数据为空，构造空数据记录: keyword={keyword}, region={region_code}, date={start_date} 至 {end_date}")
                if keyword and start_date:
                    return self._create_empty_region_data(keyword, region_code, start_date, end_date)
                return pd.DataFrame()
            
            # 初始化结果列表
            results = []
            
            # 处理每个关键词的数据
            for item in region_data:
                item_keyword = item.get('key', keyword or '')
                period = item.get('period', '')
                # 如果没有period，使用start_date和end_date构造
                if not period and start_date and end_date:
                    period = f"{start_date}|{end_date}"
                elif not period and start_date:
                    period = start_date
                
                area = item.get('area', region_code)
                area_name = item.get('areaName', self._get_region_name(region_code))
                
                # 获取所有数据
                prov_data = item.get('prov', {})
                prov_real_data = item.get('provReal', {}) or item.get('prov_real', {})
                city_data = item.get('city', {})
                city_real_data = item.get('cityReal', {}) or item.get('city_real', {})
                
                # 处理省份数据（prov和provReal）
                all_prov_codes = set(prov_data.keys()) | set(prov_real_data.keys())
                for prov_code in all_prov_codes:
                    prov_name = self._get_province_name(prov_code)
                    prov_value = prov_data.get(prov_code, 0)
                    prov_real_value = prov_real_data.get(prov_code, 0.0)
                    if isinstance(prov_real_value, str) or prov_real_value is None:
                        prov_real_value = 0.0
                    
                    results.append({
                        '关键词': item_keyword,
                        '地区代码': region_code,
                        '地区名称': area_name,
                        '时间范围': period,
                        '地区级别': 'province',
                        '地区代码（具体）': prov_code,
                        '地区名称（具体）': prov_name,
                        '指数': prov_value,
                        '占比': prov_real_value,
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                
                # 处理城市数据（city和cityReal）
                all_city_codes = set(city_data.keys()) | set(city_real_data.keys())
                for city_code in all_city_codes:
                    city_name = region_manager.get_city_name_by_code(city_code) or f"未知城市({city_code})"
                    city_value = city_data.get(city_code, 0)
                    city_real_value = city_real_data.get(city_code, 0.0)
                    if isinstance(city_real_value, str) or city_real_value is None:
                        city_real_value = 0.0
                    
                    results.append({
                        '关键词': item_keyword,
                        '地区代码': region_code,
                        '地区名称': area_name,
                        '时间范围': period,
                        '地区级别': 'city',
                        '地区代码（具体）': city_code,
                        '地区名称（具体）': city_name,
                        '指数': city_value,
                        '占比': city_real_value,
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            # 如果结果为空，构造空数据记录
            if not results:
                log.warning(f"处理后的地域分布数据为空，构造空数据记录: keyword={keyword}, region={region_code}, date={start_date} 至 {end_date}")
                if keyword and start_date:
                    return self._create_empty_region_data(keyword, region_code, start_date, end_date)
                return pd.DataFrame()
            
            # 创建DataFrame
            df = pd.DataFrame(results)
            
            # 打印日志
            log.info(f"成功处理地域分布数据: keyword={keyword}, region={region_code}, date={start_date} 至 {end_date}, 共 {len(df)} 条记录")
            
            return df
            
        except Exception as e:
            log.error(f"处理地域分布数据失败: {e}")
            log.error(traceback.format_exc())
            # 如果提供了keyword和日期，构造空数据记录
            if keyword and start_date:
                return self._create_empty_region_data(keyword, region_code, start_date, end_date)
            return pd.DataFrame()  # 返回空DataFrame表示处理失败
    
    def _create_empty_region_data(self, keyword, region_code, start_date, end_date=None):
        """
        创建空的地域分布数据记录（用于保持数据维度一致性）
        :param keyword: 关键词
        :param region_code: 地区代码
        :param start_date: 开始日期
        :param end_date: 结束日期（可选）
        :return: 包含空数据记录的DataFrame
        """
        region_name = self._get_region_name(region_code)
        # 构造period字段
        if start_date and end_date:
            period = f"{start_date}|{end_date}"
        elif start_date:
            period = start_date
        else:
            period = datetime.now().strftime('%Y-%m-%d')
        
        empty_record = {
            '关键词': keyword,
            '地区代码': region_code,
            '地区名称': region_name,
            '时间范围': period,
            '地区级别': '',
            '地区代码（具体）': '',
            '地区名称（具体）': '',
            '指数': 0,
            '占比': 0.0,
            '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return pd.DataFrame([empty_record])
    
    def _get_region_name(self, region_code):
        """
        获取地区名称
        :param region_code: 地区代码
        :return: 地区名称
        """
        if region_code == 0:
            return "全国"
        
        # 尝试从region_manager获取省份名称
        province_name = self._get_province_name(region_code)
        if province_name:
            return province_name
        
        # 尝试从region_manager获取城市名称
        city_name = region_manager.get_city_name_by_code(region_code)
        if city_name:
            return city_name
        
        return f"未知地区({region_code})"
    
    def _get_province_name(self, prov_code):
        """
        获取省份名称
        :param prov_code: 省份代码
        :return: 省份名称
        """
        # 省份代码到名称的映射
        province_map = {
            '901': '北京',
            '902': '上海',
            '903': '天津',
            '904': '重庆',
            '905': '广东',
            '906': '福建',
            '907': '浙江',
            '908': '江苏',
            '909': '湖南',
            '910': '湖北',
            '911': '河南',
            '912': '河北',
            '913': '山东',
            '914': '山西',
            '915': '陕西',
            '916': '安徽',
            '917': '江西',
            '918': '广西',
            '919': '海南',
            '920': '四川',
            '921': '云南',
            '922': '贵州',
            '923': '青海',
            '924': '甘肃',
            '925': '宁夏',
            '926': '内蒙古',
            '927': '黑龙江',
            '928': '吉林',
            '929': '辽宁',
            '930': '西藏',
            '931': '新疆',
            '932': '香港',
            '933': '澳门',
            '934': '台湾'
        }
        
        return province_map.get(str(prov_code), f"未知省份({prov_code})")
    
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
    
    def save_to_csv(self, df, output_file='百度指数数据.csv'):
        """
        将数据保存到CSV文件
        :param df: 要保存的DataFrame
        :param output_file: 输出文件名
        :return: 是否保存成功
        """
        try:
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            log.info(f"数据已保存到 {output_file}")
            return True
        except Exception as e:
            log.error(f"保存数据到CSV失败: {e}")
            return False
    
    def append_to_csv(self, df, output_file='百度指数数据.csv'):
        """
        将数据追加到现有CSV文件
        :param df: 要追加的DataFrame
        :param output_file: 输出文件名
        :return: 是否保存成功
        """
        try:
            # 检查文件是否存在，决定是否写入表头
            file_exists = os.path.exists(output_file) and os.path.getsize(output_file) > 0
            
            # 追加到CSV文件
            df.to_csv(output_file, mode='a', header=not file_exists, index=False, encoding='utf-8-sig')
            log.info(f"数据已追加到 {output_file}")
            return True
        except Exception as e:
            log.error(f"追加数据到CSV失败: {e}")
            return False
    
    def process_search_index_daily_data(self, data, cookie, keyword, city_code, city_name, start_date, end_date, decrypted_all, decrypted_wise, decrypted_pc):
        """
        处理搜索指数的日度数据和统计数据
        :param data: API返回的原始数据
        :param cookie: 用于请求的cookie
        :param keyword: 关键词
        :param city_code: 城市代码
        :param city_name: 城市名称
        :param start_date: 开始日期
        :param end_date: 结束日期
        :param decrypted_all: 解密后的全部指数数据
        :param decrypted_wise: 解密后的移动指数数据
        :param decrypted_pc: 解密后的PC指数数据
        :return: (daily_data, stats_record) 元组，分别为日度数据列表和统计数据记录
        """
        try:
            # 检查数据完整性
            if not data or not isinstance(data, dict):
                log.warning(f"数据为空或格式不正确: {data}")
                return None, None
                
            if not data.get('data'):
                log.warning(f"数据中缺少data字段: {data}")
                return None, None
                
            if not data['data'].get('userIndexes'):
                log.warning(f"数据中缺少userIndexes字段: {data['data']}")
                return None, None
                
            if not data['data']['userIndexes'] or len(data['data']['userIndexes']) == 0:
                log.warning(f"userIndexes为空列表: {data['data']['userIndexes']}")
                return None, None
                
            # 获取统计数据
            if not data['data'].get('generalRatio'):
                log.warning(f"数据中缺少generalRatio字段: {data['data']}")
                return None, None
                
            if len(data['data']['generalRatio']) == 0:
                log.warning(f"generalRatio为空列表: {data['data']['generalRatio']}")
                return None, None
                
            general_ratio = data['data']['generalRatio'][0]
            
            # 安全获取统计数据字段，提供默认值
            all_stats = general_ratio.get('all', {})
            wise_stats = general_ratio.get('wise', {})
            pc_stats = general_ratio.get('pc', {})
            
            if not all_stats:
                log.warning(f"缺少all统计数据: {general_ratio}")
                all_stats = {'avg': 0, 'yoy': '-', 'qoq': '-'}
                
            if not wise_stats:
                log.warning(f"缺少wise统计数据: {general_ratio}")
                wise_stats = {'avg': 0, 'yoy': '-', 'qoq': '-'}
                
            if not pc_stats:
                log.warning(f"缺少pc统计数据: {general_ratio}")
                pc_stats = {'avg': 0, 'yoy': '-', 'qoq': '-'}
            
            # 将解密后的数据转换为列表，并确保数据有效
            all_values = decrypted_all.split(',') if decrypted_all else []
            wise_values = decrypted_wise.split(',') if decrypted_wise else []
            pc_values = decrypted_pc.split(',') if decrypted_pc else []
            
            # 验证数据长度是否一致，如果不一致则使用最长的长度
            max_length = max(len(all_values), len(wise_values), len(pc_values))
            # print(f"all_values: {all_values}, wise_values: {wise_values}, pc_values: {pc_values}")
            # 如果所有数据都为空，创建默认数据
            if max_length == 0:
                # log.warning(f"解密后的数据为空: all={len(all_values)}, wise={len(wise_values)}, pc={len(pc_values)}")
                # 创建默认的日度数据
                daily_data = [{
                    '关键词': keyword,
                    '城市代码': city_code,
                    '城市': city_name,
                    '日期': start_date,
                    '数据类型': '日度',
                    '数据间隔(天)': 1,
                    '所属年份': start_date[:4],
                    'PC+移动指数': '0',
                    '移动指数': '0',
                    'PC指数': '0',
                    '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }]
                
                # 创建默认的统计数据
                stats_record = {
                    '关键词': keyword,
                    '城市代码': city_code,
                    '城市': city_name,
                    '时间范围': f"{start_date} 至 {end_date}",
                    '整体日均值': all_stats.get('avg', 0),
                    '整体同比': all_stats.get('yoy', '-'),
                    '整体环比': all_stats.get('qoq', '-'),
                    '移动日均值': wise_stats.get('avg', 0),
                    '移动同比': wise_stats.get('yoy', '-'),
                    '移动环比': wise_stats.get('qoq', '-'),
                    'PC日均值': pc_stats.get('avg', 0),
                    'PC同比': pc_stats.get('yoy', '-'),
                    'PC环比': pc_stats.get('qoq', '-'),
                    '整体总值': 0,
                    '移动总值': 0,
                    'PC总值': 0,
                    '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                return daily_data, stats_record
                
            # 如果数据长度不一致，按照最长的为准，缺少的补0
            if len(all_values) != max_length or len(wise_values) != max_length or len(pc_values) != max_length:
                # log.warning(f"解密后的数据长度不一致，将使用最长长度并补0: all={len(all_values)}, wise={len(wise_values)}, pc={len(pc_values)}, max={max_length}")
                # 补齐all_values
                if len(all_values) < max_length:
                    all_values.extend(['0'] * (max_length - len(all_values)))
                # 补齐wise_values
                if len(wise_values) < max_length:
                    wise_values.extend(['0'] * (max_length - len(wise_values)))
                # 补齐pc_values
                if len(pc_values) < max_length:
                    pc_values.extend(['0'] * (max_length - len(pc_values)))
            
            # 计算日期间隔
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                total_days = (end - start).days + 1
            except Exception as e:
                log.warning(f"日期格式错误: {start_date} - {end_date}, 错误: {e}")
                return None, None
            
            # 判断数据粒度
            data_length = max_length
            
            # 确定数据间隔
            if data_length == total_days:
                # 每天一个数据点 - 日度数据
                interval = 1
                data_type = '日度'
                expected_data_points = total_days
            elif abs(total_days - data_length * 7) <= 7:
                # 每周一个数据点 - 周度数据
                interval = 7
                data_type = '周度'
                expected_data_points = (total_days + 6) // 7  # 向上取整
            else:
                # 其他间隔 - 可能是月度数据或自定义间隔
                interval = total_days // data_length if data_length > 0 else 1
                data_type = '自定义'
                expected_data_points = data_length
            
            # 检查数据维度一致性：如果返回的数据点数量少于预期，需要补齐
            if data_length < expected_data_points:
                log.warning(f"数据点数量不足，预期 {expected_data_points} 个，实际 {data_length} 个，将补齐空数据: {keyword}, {city_name}, {start_date} - {end_date}")
                # 补齐数据到预期数量
                missing_count = expected_data_points - data_length
                all_values.extend(['0'] * missing_count)
                wise_values.extend(['0'] * missing_count)
                pc_values.extend(['0'] * missing_count)
                data_length = expected_data_points
            
            # 生成日期列表 - 确保覆盖完整的日期范围
            date_range = []
            for i in range(expected_data_points):
                current_date = (start + timedelta(days=i*interval)).strftime('%Y-%m-%d')
                # 确保不超过结束日期
                if current_date > end_date:
                    break
                date_range.append(current_date)
                
            # 准备日度/周度数据
            daily_data = []
            for i in range(len(date_range)):
                # 获取对应的值，如果索引越界则使用 '0'
                all_val = all_values[i] if i < len(all_values) else '0'
                wise_val = wise_values[i] if i < len(wise_values) else '0'
                pc_val = pc_values[i] if i < len(pc_values) else '0'
                
                daily_record = {
                    '关键词': keyword,
                    '城市代码': city_code,
                    '城市': city_name,
                    '日期': date_range[i],
                    '数据类型': data_type,
                    '数据间隔(天)': interval,
                    '所属年份': date_range[i][:4],
                    'PC+移动指数': all_val,
                    '移动指数': wise_val,
                    'PC指数': pc_val,
                    '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                daily_data.append(daily_record)
                
            # 如果没有有效数据，创建默认数据
        
            if not daily_data:
                print(f"daily_data: {daily_data}")
                log.warning(f"处理后没有有效的日度数据: {keyword}, {city_name}")
                daily_data = [{
                    '关键词': keyword,
                    '城市代码': city_code,
                    '城市': city_name,
                    '日期': start_date,
                    '数据类型': '日度',
                    '数据间隔(天)': 1,
                    '所属年份': start_date[:4],
                    'PC+移动指数': '0',
                    '移动指数': '0',
                    'PC指数': '0',
                    '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }]
                
            # 准备统计数据
            try:
                # 安全获取统计数据字段，提供默认值
                stats_record = {
                    '关键词': keyword,
                    '城市代码': city_code,
                    '城市': city_name,
                    '时间范围': f"{start_date} 至 {end_date}",
                    '整体日均值': all_stats.get('avg', 0),
                    '整体同比': all_stats.get('yoy', '-'),
                    '整体环比': all_stats.get('qoq', '-'),
                    '移动日均值': wise_stats.get('avg', 0),
                    '移动同比': wise_stats.get('yoy', '-'),
                    '移动环比': wise_stats.get('qoq', '-'),
                    'PC日均值': pc_stats.get('avg', 0),
                    'PC同比': pc_stats.get('yoy', '-'),
                    'PC环比': pc_stats.get('qoq', '-'),
                    '整体总值': sum(int(v) for v in all_values if v.isdigit()),
                    '移动总值': sum(int(v) for v in wise_values if v.isdigit()),
                    'PC总值': sum(int(v) for v in pc_values if v.isdigit()),
                    '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            except Exception as e:
                log.warning(f"处理统计数据时出错: {e}")
                # 提供一个基本的统计记录
                stats_record = {
                    '关键词': keyword,
                    '城市代码': city_code,
                    '城市': city_name,
                    '时间范围': f"{start_date} 至 {end_date}",
                    '整体日均值': 0,
                    '整体同比': '-',
                    '整体环比': '-',
                    '移动日均值': 0,
                    '移动同比': '-',
                    '移动环比': '-',
                    'PC日均值': 0,
                    'PC同比': '-',
                    'PC环比': '-',
                    '整体总值': 0,
                    '移动总值': 0,
                    'PC总值': 0,
                    '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            
            return daily_data, stats_record
        except Exception as e:
            log.error(f"处理搜索指数日度数据时出错: {str(e)}")
            log.error(traceback.format_exc())
            
            # 出错时创建默认数据
            daily_data = [{
                '关键词': keyword,
                '城市代码': city_code,
                '城市': city_name,
                '日期': start_date,
                '数据类型': '日度',
                '数据间隔(天)': 1,
                '所属年份': start_date[:4],
                'PC+移动指数': '0',
                '移动指数': '0',
                'PC指数': '0',
                '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }]
            
            stats_record = {
                '关键词': keyword,
                '城市代码': city_code,
                '城市': city_name,
                '时间范围': f"{start_date} 至 {end_date}",
                '整体日均值': 0,
                '整体同比': '-',
                '整体环比': '-',
                '移动日均值': 0,
                '移动同比': '-',
                '移动环比': '-',
                'PC日均值': 0,
                'PC同比': '-',
                'PC环比': '-',
                '整体总值': 0,
                '移动总值': 0,
                'PC总值': 0,
                '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return daily_data, stats_record
    
    def process_feed_index_data(self, data, cookie, keyword, city_code, city_name, start_date, end_date, decrypted_data, data_type='day'):
        """
        处理资讯指数数据
        :param data: API返回的原始数据
        :param cookie: 用于请求的cookie
        :param keyword: 关键词
        :param city_code: 城市代码
        :param city_name: 城市名称
        :param start_date: 开始日期 
        :param end_date: 结束日期
        :param decrypted_data: 解密后的数据
        :param data_type: 数据类型，'day'或'week'
        :return: (daily_data, stats_record) 元组，分别为日度数据列表和统计数据记录
        """
        try:
            if not data or not data.get('data') or not data['data'].get('index'):
                log.warning(f"数据为空或格式不正确: {data}")
                return None, None
            
            # 获取统计数据
            index_data = data['data']['index'][0]
            general_ratio = index_data.get('generalRatio', {})
            
            # 获取均值、同比、环比数据
            avg_value = general_ratio.get('avg', 0)
            yoy_value = general_ratio.get('yoy', '-')  # 同比
            qoq_value = general_ratio.get('qoq', '-')  # 环比
            
            log.debug(f"统计数据: avg={avg_value}, yoy={yoy_value}, qoq={qoq_value}")
            
            # 获取起止日期
            api_start_date = index_data.get('startDate', start_date)
            api_end_date = index_data.get('endDate', end_date)
            
            # 计算日期间隔
            start = datetime.strptime(api_start_date, '%Y-%m-%d')
            end = datetime.strptime(api_end_date, '%Y-%m-%d')
            total_days = (end - start).days + 1
            
            # 验证解密数据
            if not decrypted_data or not isinstance(decrypted_data, str) or not decrypted_data.strip():
                # 如果解密数据为空，说明该时间段内所有值都是0，需要根据时间范围生成空数据
                log.info(f"解密数据为空，为该时间段生成空数据: keyword={keyword}, city={city_name}, start={api_start_date}, end={api_end_date}, data_type={data_type}")
                
                # 确定数据间隔和频率
                if data_type == 'week':
                    interval = 7
                    data_frequency = '周度'
                    # 计算周数
                    data_length = (total_days + 6) // 7  # 向上取整
                else:
                    interval = 1
                    data_frequency = '日度'
                    data_length = total_days
                
                # 生成日期列表
                date_range = []
                for i in range(data_length):
                    current_date = (start + timedelta(days=i*interval)).strftime('%Y-%m-%d')
                    # 确保不超过结束日期
                    if current_date > api_end_date:
                        break
                    date_range.append(current_date)
                
                # 生成空数据记录（所有值都是0）
                daily_data = []
                for date_str in date_range:
                    daily_record = {
                        '关键词': keyword,
                        '城市代码': city_code,
                        '城市': city_name,
                        '日期': date_str,
                        '数据类型': data_frequency,
                        '数据间隔(天)': interval,
                        '所属年份': date_str[:4],
                        '资讯指数': '0',
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    daily_data.append(daily_record)
                
                # 准备统计数据
                stats_record = {
                    '关键词': keyword,
                    '城市代码': city_code,
                    '城市': city_name,
                    '时间范围': f"{api_start_date} 至 {api_end_date}",
                    '日均值': avg_value,
                    '同比': yoy_value,
                    '环比': qoq_value,
                    '总值': 0,
                    '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                
                log.info(f"成功生成空数据: {keyword} - {city_name}, {data_frequency}, 共 {len(daily_data)} 条记录")
                return daily_data, stats_record
            
            # 将解密后的数据转换为列表，保留空值并替换为'0'
            raw_values = decrypted_data.split(',')
            values = [v if v.strip() else '0' for v in raw_values]
            
            # 如果列表为空，返回错误
            if not values:
                log.error(f"解密数据分割后为空, keyword: {keyword}, city: {city_name}")
                return None, None
            
            log.debug(f"解密数据分割后共 {len(values)} 个值")
            
            # 判断数据粒度（start 和 end 已在上面计算过）
            data_length = len(values)
            
            # 确定数据间隔 - 优先使用API返回的data_type
            if data_type == 'week':
                # API明确返回week类型，使用周度数据
                interval = 7
                data_frequency = '周度'
                expected_data_points = (total_days + 6) // 7  # 向上取整
                log.info(f"{city_name} - {keyword}: API返回周度数据, 共 {data_length} 周")
            elif data_type == 'day' or (data_length == total_days):
                # 每天一个数据点 - 日度数据
                interval = 1
                data_frequency = '日度'
                expected_data_points = total_days
            elif abs(total_days - data_length * 7) <= 7:
                # 每周一个数据点 - 周度数据（通过数据量推断）
                interval = 7
                data_frequency = '周度'
                expected_data_points = (total_days + 6) // 7
            else:
                # 其他间隔 - 可能是月度数据或自定义间隔
                interval = total_days // data_length if data_length > 0 else 1
                data_frequency = '自定义'
                expected_data_points = data_length
                
            log.debug(f"{city_name} - {keyword} 数据粒度: {data_frequency} (每{interval}天一个数据点, 共{data_length}个数据点)")
            
            # 检查数据维度一致性：如果返回的数据点数量少于预期，需要补齐
            if data_length < expected_data_points:
                log.warning(f"资讯指数数据点数量不足，预期 {expected_data_points} 个，实际 {data_length} 个，将补齐空数据: {keyword}, {city_name}, {api_start_date} - {api_end_date}")
                # 补齐数据到预期数量
                missing_count = expected_data_points - data_length
                values.extend(['0'] * missing_count)
                data_length = expected_data_points
            
            # 生成日期列表 - 确保覆盖完整的日期范围
            date_range = []
            for i in range(expected_data_points):
                current_date = (start + timedelta(days=i*interval)).strftime('%Y-%m-%d')
                # 确保不超过结束日期
                if current_date > api_end_date:
                    break
                date_range.append(current_date)
                
            # 准备日度/周度数据
            daily_data = []
            for i in range(len(date_range)):
                # 获取对应的值，如果索引越界则使用 '0'
                value = values[i] if i < len(values) else '0'
                daily_record = {
                    '关键词': keyword,
                    '城市代码': city_code,
                    '城市': city_name,
                    '日期': date_range[i],
                    '数据类型': data_frequency,
                    '数据间隔(天)': interval,
                    '所属年份': date_range[i][:4],
                    '资讯指数': value,
                    '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                daily_data.append(daily_record)
            
            # 计算总值
            total_value = 0
            for v in values:
                try:
                    total_value += int(v)
                except (ValueError, TypeError):
                    pass
                
            # 准备统计数据 - 使用与默认数据一致的字段名
            stats_record = {
                '关键词': keyword,
                '城市代码': city_code,
                '城市': city_name,
                '时间范围': f"{api_start_date} 至 {api_end_date}",
                '日均值': avg_value,
                '同比': yoy_value,
                '环比': qoq_value,
                '总值': total_value,
                '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            log.info(f"成功处理资讯指数数据: {keyword} - {city_name}, {data_frequency}, 共 {len(daily_data)} 条记录, 日均值: {avg_value}")
            
            return daily_data, stats_record
            
        except Exception as e:
            log.error(f"处理资讯指数日度数据时出错: {str(e)}")
            import traceback
            log.error(traceback.format_exc())
            return None, None


# 创建数据处理器单例
data_processor = BaiduIndexDataProcessor() 