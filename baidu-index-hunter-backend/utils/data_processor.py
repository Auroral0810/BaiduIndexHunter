"""
百度指数数据处理模块
"""
import pandas as pd
from datetime import datetime, timedelta
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
            period = api_data.get('period', '')
            
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
            for item in keyword_items:
                word = item.get('word', '')
                
                # 处理兴趣分布
                interest_data = item.get('interest', [])
                for interest in interest_data:
                    desc = interest.get('desc', '')
                    tgi = interest.get('tgi', '')
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
            if overall_item:
                # 处理兴趣分布
                interest_data = overall_item.get('interest', [])
                for interest in interest_data:
                    desc = interest.get('desc', '')
                    tgi = interest.get('tgi', '')
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
    
    def process_region_distribution_data(self, data, region_code=0):
        """
        处理地域分布数据
        :param data: API返回的原始数据
        :param region_code: 地区代码，0表示全国
        :return: 处理后的DataFrame
        """
        try:
            # 检查数据是否为空或结构不完整
            if data is None or 'status' not in data or data['status'] != 0:
                log.error(f"处理地域分布数据失败: 数据为空或API返回错误")
                return pd.DataFrame()
            
            if 'data' not in data or 'region' not in data['data']:
                log.error(f"处理地域分布数据失败: 数据结构不完整")
                return pd.DataFrame()
            
            # 获取数据
            region_data = data['data']['region']
            
            # 初始化结果列表
            results = []
            
            # 处理每个关键词的数据
            for item in region_data:
                keyword = item.get('key', '')
                period = item.get('period', '')
                area = item.get('area', region_code)
                area_name = item.get('areaName', self._get_region_name(region_code))
                
                # 处理省份数据（如果有）
                if 'prov' in item and item['prov']:
                    prov_data = item['prov']
                    prov_real_data = item.get('provReal', {}) or item.get('prov_real', {})
                    
                    for prov_code, value in prov_data.items():
                        real_value = prov_real_data.get(prov_code, value)
                        prov_name = self._get_province_name(prov_code)
                        
                        results.append({
                            '关键词': keyword,
                            '地区类型': '省份',
                            '地区代码': prov_code,
                            '地区名称': prov_name,
                            '指数值': value,
                            '真实指数值': real_value,
                            '所属地区代码': area,
                            '所属地区名称': area_name,
                            '数据周期': period,
                            '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                
                # 处理城市数据（如果有）
                if 'city' in item and item['city']:
                    city_data = item['city']
                    city_real_data = item.get('cityReal', {}) or item.get('city_real', {})
                    
                    for city_code, value in city_data.items():
                        real_value = city_real_data.get(city_code, value)
                        city_name = city_manager.get_city_name(city_code) or f"未知城市({city_code})"
                        
                        results.append({
                            '关键词': keyword,
                            '地区类型': '城市',
                            '地区代码': city_code,
                            '地区名称': city_name,
                            '指数值': value,
                            '真实指数值': real_value,
                            '所属地区代码': area,
                            '所属地区名称': area_name,
                            '数据周期': period,
                            '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
            
            # 创建DataFrame
            df = pd.DataFrame(results)
            
            # 打印日志
            log.info(f"成功处理地域分布数据，地区代码: {region_code}，共 {len(df)} 条记录")
            
            return df
            
        except Exception as e:
            log.error(f"处理地域分布数据失败: {e}")
            return pd.DataFrame()  # 返回空DataFrame表示处理失败
    
    def _get_region_name(self, region_code):
        """
        获取地区名称
        :param region_code: 地区代码
        :return: 地区名称
        """
        if region_code == 0:
            return "全国"
        
        # 尝试从city_manager获取省份名称
        province_name = self._get_province_name(region_code)
        if province_name:
            return province_name
        
        # 尝试从city_manager获取城市名称
        city_name = city_manager.get_city_name(region_code)
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
            # 尝试读取现有文件
            try:
                existing_df = pd.read_csv(output_file, encoding='utf-8-sig')
                # 合并数据
                combined_df = pd.concat([existing_df, df], ignore_index=True)
            except FileNotFoundError:
                # 如果文件不存在，直接使用新数据
                combined_df = df
            
            # 保存合并后的数据
            combined_df.to_csv(output_file, index=False, encoding='utf-8-sig')
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
            if not data or not data.get('data') or not data['data'].get('userIndexes'):
                log.warning(f"数据为空或格式不正确: {data}")
                return None, None
                
            # 获取统计数据
            general_ratio = data['data']['generalRatio'][0]
            all_stats = general_ratio['all']
            wise_stats = general_ratio['wise']
            pc_stats = general_ratio['pc']
            
            # 将解密后的数据转换为列表
            all_values = decrypted_all.split(',')
            wise_values = decrypted_wise.split(',')
            pc_values = decrypted_pc.split(',')
            
            # 计算日期间隔
            start = datetime.strptime(start_date, '%Y-%m-%d')
            end = datetime.strptime(end_date, '%Y-%m-%d')
            total_days = (end - start).days + 1
            
            # 判断数据粒度
            data_length = len(all_values)
            
            # 确定数据间隔
            if data_length == total_days:
                # 每天一个数据点 - 日度数据
                interval = 1
                data_type = '日度'
            elif abs(total_days - data_length * 7) <= 7:
                # 每周一个数据点 - 周度数据
                interval = 7
                data_type = '周度'
            else:
                # 其他间隔 - 可能是月度数据或自定义间隔
                interval = total_days // data_length if data_length > 0 else 1
                data_type = '自定义'
                
            log.info(f"{city_name} - {keyword} 数据粒度: {data_type}数据 (每{interval}天一个数据点)")
            
            # 生成日期列表
            date_range = []
            for i in range(data_length):
                current_date = (start + timedelta(days=i*interval)).strftime('%Y-%m-%d')
                date_range.append(current_date)
                
            # 准备日度/周度数据
            daily_data = []
            for i in range(len(date_range)):
                daily_record = {
                    '关键词': keyword,
                    '城市代码': city_code,
                    '城市': city_name,
                    '日期': date_range[i],
                    '数据类型': data_type,
                    '数据间隔(天)': interval,
                    '所属年份': date_range[i][:4],
                    'PC+移动指数': all_values[i],
                    '移动指数': wise_values[i],
                    'PC指数': pc_values[i],
                    '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                daily_data.append(daily_record)
                
            # 准备统计数据
            stats_record = {
                '关键词': keyword,
                '城市代码': city_code,
                '城市': city_name,
                '时间范围': f"{start_date} 至 {end_date}",
                '整体日均值': all_stats['avg'],
                '整体同比': all_stats['yoy'],
                '整体环比': all_stats['qoq'],
                '移动日均值': wise_stats['avg'],
                '移动同比': wise_stats['yoy'],
                '移动环比': wise_stats['qoq'],
                'PC日均值': pc_stats['avg'],
                'PC同比': pc_stats['yoy'],
                'PC环比': pc_stats['qoq'],
                '整体总值': sum(int(v) for v in all_values if v.isdigit()),
                '移动总值': sum(int(v) for v in wise_values if v.isdigit()),
                'PC总值': sum(int(v) for v in pc_values if v.isdigit()),
                '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return daily_data, stats_record
            
        except Exception as e:
            log.error(f"处理搜索指数日度数据时出错: {str(e)}")
            return None, None
    
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
            
            # 获取起止日期
            api_start_date = index_data.get('startDate', start_date)
            api_end_date = index_data.get('endDate', end_date)
            
            # 将解密后的数据转换为列表
            values = decrypted_data.split(',')
            
            # 计算日期间隔
            start = datetime.strptime(api_start_date, '%Y-%m-%d')
            end = datetime.strptime(api_end_date, '%Y-%m-%d')
            total_days = (end - start).days + 1
            
            # 判断数据粒度
            data_length = len(values)
            
            # 确定数据间隔
            if data_type == 'day' or (data_length == total_days):
                # 每天一个数据点 - 日度数据
                interval = 1
                data_frequency = '日度'
            elif data_type == 'week' or abs(total_days - data_length * 7) <= 7:
                # 每周一个数据点 - 周度数据
                interval = 7
                data_frequency = '周度'
            else:
                # 其他间隔 - 可能是月度数据或自定义间隔
                interval = total_days // data_length if data_length > 0 else 1
                data_frequency = '自定义'
                
            log.info(f"{city_name} - {keyword} 数据粒度: {data_frequency}数据 (每{interval}天一个数据点)")
            
            # 生成日期列表
            date_range = []
            for i in range(data_length):
                current_date = (start + timedelta(days=i*interval)).strftime('%Y-%m-%d')
                date_range.append(current_date)
                
            # 准备日度/周度数据
            daily_data = []
            for i in range(len(date_range)):
                daily_record = {
                    '关键词': keyword,
                    '城市代码': city_code,
                    '城市': city_name,
                    '日期': date_range[i],
                    '数据类型': data_frequency,
                    '数据间隔(天)': interval,
                    '所属年份': date_range[i][:4],
                    '资讯指数': values[i],
                    '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                daily_data.append(daily_record)
                
            # 准备统计数据
            stats_record = {
                '关键词': keyword,
                '城市代码': city_code,
                '城市': city_name,
                '时间范围': f"{api_start_date} 至 {api_end_date}",
                '资讯日均值': avg_value,
                '资讯同比': yoy_value,
                '资讯环比': qoq_value,
                '资讯总值': sum(int(v) for v in values if v.isdigit()),
                '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            return daily_data, stats_record
            
        except Exception as e:
            log.error(f"处理资讯指数日度数据时出错: {str(e)}")
            return None, None


# 创建数据处理器单例
data_processor = BaiduIndexDataProcessor() 