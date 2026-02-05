"""
资讯指数爬虫（趋势数据）
"""
import pandas as pd
import requests
import json
import time
import urllib.parse

# 添加项目根目录到Python路径
from src.core.logger import log
from src.utils.rate_limiter import rate_limiter
from src.utils.decorators import retry
from src.engine.crypto.cipher_generator import cipher_text_generator
from src.services.cookie_rotator import cookie_rotator
from src.core.config import BAIDU_INDEX_API, OUTPUT_DIR
from fake_useragent import UserAgent
from src.engine.spider.base_crawler import BaseCrawler
from datetime import datetime
from src.services.storage_service import storage_service

# 自定义异常类
class NoCookieAvailableError(Exception):
    """当没有可用Cookie时抛出的异常"""
    pass

class FeedIndexCrawler(BaseCrawler):
    """百度资讯指数爬虫类"""
    
    def __init__(self):
        """初始化爬虫"""
        super().__init__(task_type="feed_index")
        
        # FeedIndexCrawler特有的初始化
        self.current_keyword_index = 0
        self.current_city_index = 0
        self.current_date_range_index = 0
        self.city_dict = {}  # 城市代码到名称的映射
        self.ua = UserAgent()
        
        # 设置线程池最大工作线程数 (从配置服务加载，如果基类未提供)
        from src.services.config_service import config_manager
        self.max_workers = int(config_manager.get('spider.max_workers', 5))
        self.timeout = int(config_manager.get('spider.timeout', 15))
        self.retry_times = int(config_manager.get('spider.retry_times', 2))
        log.info(f"爬虫配置已加载: max_workers={self.max_workers}, timeout={self.timeout}, retry_times={self.retry_times}")
        
    # setup_signal_handlers, handle_exit, _generate_task_id, _save_data_cache, _update_task_db_status, _update_spider_statistics, _flush_buffer 均由 BaseCrawler 提供
    
    # _get_feed_index, _process_feed_index_data, _process_multi_feed_index_data 保持现状，因为它们包含特定的解析逻辑

    def _save_global_checkpoint(self):
        """保存全局检查点 (覆盖基类以包含 city_dict)"""
        if not self.checkpoint_path: return
        try:
            checkpoint_data = {
                'completed_keywords': list(self.completed_keywords),
                'failed_keywords': list(self.failed_keywords),
                'completed_tasks': self.completed_tasks,
                'failed_tasks': self.failed_tasks,
                'total_tasks': self.total_tasks,
                'task_id': self.task_id,
                'output_path': self.output_path,
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'city_dict': self.city_dict,
                'current_keyword_index': self.current_keyword_index,
                'current_city_index': self.current_city_index,
                'current_date_range_index': self.current_date_range_index,
            }
            storage_service.save_pickle(checkpoint_data, self.checkpoint_path)
            log.info(f"检查点已更新: {self.completed_tasks}/{self.total_tasks}")
        except Exception as e:
            log.error(f"Save Checkpoint Error: {e}")
            
    def _load_global_checkpoint(self, task_id):
        """加载全局检查点 (覆盖基类以处理 city_dict)"""
        checkpoint = super()._load_global_checkpoint(task_id)
        if checkpoint:
            self.city_dict = checkpoint.get('city_dict', {})
            self.current_keyword_index = checkpoint.get('current_keyword_index', 0)
            self.current_city_index = checkpoint.get('current_city_index', 0)
            self.current_date_range_index = checkpoint.get('current_date_range_index', 0)
            return True
        return False
    
    def _decrypt(self, key, data):
        """解密百度指数数据"""
        if not key or not data:
            log.warning(f"解密失败: key为空={not key}, data为空={not data}")
            return ""
        
        try:
            i = list(key)
            n = list(data)
            a = {}
            r = []
            
            # 构建映射字典
            for A in range(len(i) // 2):
                a[i[A]] = i[len(i) // 2 + A]
            
            # 根据映射解密数据
            for o in range(len(n)):
                r.append(a.get(n[o], n[o]))
            
            result = ''.join(r)
            
            # 验证解密结果
            if result and ',' in result:
                log.debug(f"解密成功, 输入长度: {len(data)}, 输出长度: {len(result)}, 数据点数量: {result.count(',') + 1}")
            else:
                log.warning(f"解密结果可能不正确: 输入长度={len(data)}, 输出长度={len(result)}, 包含逗号={(',' in result) if result else False}")
            
            return result
            
        except Exception as e:
            log.error(f"解密时发生异常: {str(e)}")
            return ""
    
    @retry(max_retries=3, delay=2)
    def _get_cipher_text(self, keyword):
        """获取Cipher-Text参数"""
        encoded_keyword = keyword.replace(' ', '%20')
        cipher_url = f'{BAIDU_INDEX_API["referer"]}#/trend/{encoded_keyword}?words={encoded_keyword}'
        return cipher_text_generator.generate(cipher_url)
    
    @retry(max_retries=3, delay=2)
    def _get_key(self, uniqid, cookie):
        """获取解密密钥"""
        params = {'uniqid': uniqid}
        
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': BAIDU_INDEX_API['referer'],
            'User-Agent': self.ua.random,
        }
        
        try:
            response = requests.get(
                'https://index.baidu.com/Interface/ptbk', 
                params=params, 
                cookies=cookie, 
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                log.error(f"获取解密密钥失败, HTTP状态码: {response.status_code}, uniqid: {uniqid}")
                return None
                
            data = response.json()
            if data.get('status') != 0:
                log.error(f"获取解密密钥失败, API返回: {data}, uniqid: {uniqid}")
                return None
            
            key = data.get('data')
            if not key:
                log.error(f"获取解密密钥失败, data字段为空, uniqid: {uniqid}")
                return None
            
            log.debug(f"成功获取解密密钥, 长度: {len(key)}, uniqid: {uniqid}")
            return key
            
        except Exception as e:
            log.error(f"获取解密密钥时发生异常: {str(e)}, uniqid: {uniqid}")
            return None
    
    @retry(max_retries=3, delay=2)
    def _get_feed_index(self, area, keywords, start_date=None, end_date=None, days=None):
        """获取资讯指数数据"""
        # 使用rate_limiter来限制请求频率
        rate_limiter.wait()
        
        # 构建word参数
        word_param_list = []
        for keyword in keywords:
            word_param_list.append([{"name": keyword, "wordType": 1}])
        
        # 构建请求URL - 使用separators去除空格，ensure_ascii=False保留中文(让quote处理编码)
        json_str = json.dumps(word_param_list, separators=(',', ':'), ensure_ascii=False)
        encoded_word_param = urllib.parse.quote(json_str)
        
        log.debug(f"构建的word参数: {json_str}")
        log.debug(f"编码后的word参数: {encoded_word_param}")
        
        if days:
            url = f"{BAIDU_INDEX_API['trend_url']}?area={area}&word={encoded_word_param}&days={days}"
        else:
            url = f"{BAIDU_INDEX_API['trend_url']}?area={area}&word={encoded_word_param}&startDate={start_date}&endDate={end_date}"
            
        log.debug(f"请求URL: {url}")
        
        # 获取有效的Cookie - cookie_rotator.get_cookie()方法内部会记录使用量，不需要额外记录
        account_id, cookie_dict = self.cookie_rotator.get_cookie()
        if not cookie_dict:
            # 修改这里：不再等待，而是抛出特定异常，以便上层处理
            log.warning("所有Cookie均被锁定，无法继续爬取")
            raise NoCookieAvailableError("所有Cookie均被锁定，无法继续爬取")
            
        # 获取Cipher-Text
        cipher_text = self._get_cipher_text(keywords[0])
        
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Cache-Control': 'no-cache',
            'Cipher-Text': cipher_text,
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': BAIDU_INDEX_API['referer'],
            'User-Agent': self.ua.random,
        }
        
        response = requests.get(url, cookies=cookie_dict, headers=headers)
        
        if response.status_code != 200:
            log.error(f"请求失败: {response.status_code}")
            return None
            
        data = response.json()
        
        # 检查响应状态
        status = data.get('status')
        if status == 10001:  # 请求被锁定
            log.warning(f"Cookie被临时锁定: {account_id}")
            self.cookie_rotator.report_cookie_status(account_id, False)
            return None
        elif status == 10000:  # 未登录
            log.warning(f"Cookie无效或已过期: {account_id}")
            self.cookie_rotator.report_cookie_status(account_id, False, permanent=True)
            return None
        elif status != 0:
            log.error(f"请求失败: {data}")
            return None
        
        # 打印调试信息：检查返回的数据结构
        log.debug(f"API响应状态: status={status}, 关键词数量: {len(keywords)}, 城市代码: {area}")
        if data.get('data') and data['data'].get('index'):
            index_list = data['data']['index']
            log.debug(f"返回的index数组长度: {len(index_list)}")
            for idx, index_item in enumerate(index_list):
                key_info = index_item.get('key', [])
                data_type = index_item.get('type', 'unknown')
                raw_data_len = len(index_item.get('data', ''))
                log.debug(f"index[{idx}]: key={json.dumps(key_info, ensure_ascii=False)}, type={data_type}, data长度={raw_data_len}")
                if raw_data_len == 0:
                    log.warning(f"警告: index[{idx}] 的data字段为空! key={json.dumps(key_info, ensure_ascii=False)}")
        else:
            log.warning(f"API返回数据格式异常: data字段={data.get('data')}, message={data.get('message', '')}")
            
        return data, cookie_dict
    
    def _process_feed_index_data(self, data, cookie, keyword, city_code, city_name, start_date, end_date):
        """处理资讯指数数据（单个关键词）"""
        if not data or not data.get('data') or not data['data'].get('index'):
            log.warning(f"数据为空或格式不正确: {data}")
            return None, None
            
        try:
            index_data = data['data']['index'][0]
            uniqid = data['data']['uniqid']
            
            # 打印调试信息
            log.debug(f"处理数据: keyword={keyword}, city={city_name}, uniqid={uniqid}")
            log.debug(f"index_data keys: {list(index_data.keys())}")
            
            # 获取解密密钥
            key = self._get_key(uniqid, cookie)
            if not key:
                log.error(f"获取解密密钥失败, uniqid: {uniqid}, keyword: {keyword}, city: {city_name}")
                return None, None
            
            log.debug(f"获取到解密密钥, 长度: {len(key)}")
                
            # 获取数据类型和原始数据
            data_type = index_data.get('type', 'day')  # 'day'或'week'
            raw_data = index_data.get('data', '')
            
            log.debug(f"原始数据类型: {data_type}, 原始数据长度: {len(raw_data) if raw_data else 0}")
            
            # 如果原始数据为空，打印更多调试信息
            if not raw_data:
                log.warning(f"原始数据为空! keyword: {keyword}, city: {city_name}, data_type: {data_type}")
                log.warning(f"index_data完整内容: {json.dumps(index_data, ensure_ascii=False)}")
                log.warning(f"API返回的完整data结构: status={data.get('status')}, message={data.get('message', '')}")
                if data.get('data', {}).get('generalRatio'):
                    log.warning(f"generalRatio: {data['data']['generalRatio']}")
            
            # 解密数据
            decrypted_data = self._decrypt(key, raw_data)
            
            # 如果解密数据为空，仍然调用data_processor处理（它会根据时间范围生成空数据）
            if not decrypted_data:
                log.info(f"解密数据为空，将生成空数据记录: keyword: {keyword}, city: {city_name}, raw_data长度: {len(raw_data) if raw_data else 0}, key长度: {len(key) if key else 0}")
                # 将空字符串传递给data_processor，让它处理空数据情况
                decrypted_data = ""
            
            # 检查解密后是否包含逗号（正确解密的数据应该包含逗号分隔的数字）
            if decrypted_data and ',' not in decrypted_data:
                log.warning(f"解密数据可能不正确（不包含逗号）, keyword: {keyword}, data_length: {len(decrypted_data)}")
            
            if decrypted_data:
                log.debug(f"解密数据长度: {len(decrypted_data)}, 前100字符: {decrypted_data[:100] if len(decrypted_data) > 100 else decrypted_data}")
            
            # 调用data_processor处理数据（即使decrypted_data为空，也会生成对应时间范围的空数据）
            return data_processor.process_feed_index_data(
                data, cookie, keyword, city_code, city_name, 
                start_date, end_date, decrypted_data, data_type
            )
            
        except Exception as e:
            log.error(f"处理数据时出错: {str(e)}")
            import traceback
            log.error(traceback.format_exc())
            return None, None
    
    def _process_multi_feed_index_data(self, data, cookie, keywords, city_code, city_name, start_date, end_date):
        """
        处理多个关键词的资讯指数数据
        :param data: API返回的原始数据
        :param cookie: 用于请求的cookie
        :param keywords: 关键词列表
        :param city_code: 城市代码
        :param city_name: 城市名称
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: (daily_data_list, stats_record_list) 元组，分别为日度数据列表和统计数据记录列表的列表
        """
        if not data or not data.get('data') or not data['data'].get('index'):
            log.warning(f"数据为空或格式不正确: {data}")
            return [], []
            
        try:
            # 获取uniqid用于解密
            uniqid = data['data']['uniqid']
            
            # 获取解密密钥
            key = self._get_key(uniqid, cookie)
            if not key:
                log.error("获取解密密钥失败")
                return [], []
            
            # 用于存储每个关键词的处理结果
            all_daily_data = []
            all_stats_records = []
            
            # 确保索引数据和关键词列表长度一致
            index_list = data['data']['index']
            
            # 检查数据完整性
            if len(index_list) != len(keywords):
                log.warning(f"关键词数量与返回的数据不匹配: keywords={len(keywords)}, index={len(index_list)}")
                # 打印返回的数据结构，帮助调试
                if len(index_list) > 0:
                    try:
                        key_info = index_list[0].get('key', [])
                        log.warning(f"返回的第一个index数据的key信息: {json.dumps(key_info, ensure_ascii=False)}")
                    except:
                        pass
                
                # 为缺少的关键词构造空数据
                if len(index_list) < len(keywords):
                    # 构造空的索引数据
                    empty_index = {'type': 'day', 'data': ''}
                    # 补充缺少的索引数据
                    for _ in range(len(keywords) - len(index_list)):
                        index_list.append(empty_index.copy())
                
                # 确保数据长度一致
                max_length = len(keywords)
                if len(index_list) > max_length:
                    index_list = index_list[:max_length]
                
                log.info(f"数据补齐后: keywords={len(keywords)}, index={len(index_list)}")
            
            # 处理每个关键词的数据
            for i, keyword in enumerate(keywords):
                try:
                    # 获取数据类型和原始数据，确保即使数据为空也能创建默认值
                    index_data = index_list[i] if i < len(index_list) else {'type': 'day', 'data': ''}
                    data_type = index_data.get('type', 'day')
                    raw_data = index_data.get('data', '')
                    
                    # 打印调试信息
                    log.debug(f"处理关键词[{i}]: {keyword}, data_type: {data_type}, raw_data长度: {len(raw_data) if raw_data else 0}")
                    
                    # 如果原始数据为空，打印更多调试信息
                    if not raw_data:
                        log.warning(f"关键词 '{keyword}' 的原始数据为空! index_data: {json.dumps(index_data, ensure_ascii=False)}")
                    
                    # 解密数据
                    decrypted_data = self._decrypt(key, raw_data)
                    
                    # 创建单个关键词的数据
                    single_data = {
                        'data': {
                            'index': [index_data],
                            'uniqid': uniqid
                        },
                        'status': 0
                    }
                    
                    # 如果解密数据为空，仍然调用data_processor处理（它会根据时间范围生成空数据）
                    if not decrypted_data or decrypted_data.strip() == '':
                        log.info(f"关键词 '{keyword}' 的解密数据为空，将生成空数据记录")
                        decrypted_data = ""  # 确保是空字符串，让data_processor处理
                    
                    # 调用data_processor处理数据（即使decrypted_data为空，也会生成对应时间范围的空数据）
                    daily_data, stats_record = data_processor.process_feed_index_data(
                        single_data, cookie, keyword, city_code, city_name, 
                        start_date, end_date, decrypted_data, data_type
                    )
                    
                    # 如果处理结果为空，创建默认的空数据
                    if not daily_data or not stats_record:
                        log.warning(f"为关键词 '{keyword}' 创建默认空数据")
                        
                        # 创建默认的日度数据
                        default_daily_data = [{
                            '关键词': keyword,
                            '城市代码': city_code,
                            '城市': city_name,
                            '日期': start_date,
                            '数据类型': '日度',
                            '数据间隔(天)': 1,
                            '所属年份': start_date[:4],
                            '资讯指数': '0',
                            '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }]
                        
                        # 创建默认的统计数据
                        default_stats_record = {
                            '关键词': keyword,
                            '城市代码': city_code,
                            '城市': city_name,
                            '时间范围': f"{start_date} 至 {end_date}",
                            '日均值': 0,
                            '同比': '-',
                            '环比': '-',
                            '总值': 0,
                            '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        all_daily_data.extend(default_daily_data)
                        all_stats_records.append(default_stats_record)
                    else:
                        all_daily_data.extend(daily_data)
                        all_stats_records.append(stats_record)
                    
                except Exception as e:
                    log.error(f"处理关键词 '{keyword}' 的数据时出错: {e}")
                    # 创建默认的空数据
                    default_daily_data = [{
                        '关键词': keyword,
                        '城市代码': city_code,
                        '城市': city_name,
                        '日期': start_date,
                        '数据类型': '日度',
                        '数据间隔(天)': 1,
                        '所属年份': start_date[:4],
                        '资讯指数': '0',
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }]
                    
                    default_stats_record = {
                        '关键词': keyword,
                        '城市代码': city_code,
                        '城市': city_name,
                        '时间范围': f"{start_date} 至 {end_date}",
                        '日均值': 0,
                        '同比': '-',
                        '环比': '-',
                        '总值': 0,
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    all_daily_data.extend(default_daily_data)
                    all_stats_records.append(default_stats_record)
                    continue
            
            # 确保即使处理结果为空，也返回有效的数据
            if not all_daily_data or not all_stats_records:
                log.warning(f"处理后没有有效数据，为所有关键词创建默认数据")
                all_daily_data = []
                all_stats_records = []
                
                for keyword in keywords:
                    all_daily_data.append({
                        '关键词': keyword,
                        '城市代码': city_code,
                        '城市': city_name,
                        '日期': start_date,
                        '数据类型': '日度',
                        '数据间隔(天)': 1,
                        '所属年份': start_date[:4],
                        '资讯指数': '0',
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    
                    all_stats_records.append({
                        '关键词': keyword,
                        '城市代码': city_code,
                        '城市': city_name,
                        '时间范围': f"{start_date} 至 {end_date}",
                        '日均值': 0,
                        '同比': '-',
                        '环比': '-',
                        '总值': 0,
                        '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            return all_daily_data, all_stats_records
            
        except Exception as e:
            log.error(f"处理多关键词资讯指数数据时出错: {str(e)}")
            log.error(traceback.format_exc())
            
            # 出错时也创建默认数据
            all_daily_data = []
            all_stats_records = []
            
            for keyword in keywords:
                all_daily_data.append({
                    '关键词': keyword,
                    '城市代码': city_code,
                    '城市': city_name,
                    '日期': start_date,
                    '数据类型': '日度',
                    '数据间隔(天)': 1,
                    '所属年份': start_date[:4],
                    '资讯指数': '0',
                    '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
                
                all_stats_records.append({
                    '关键词': keyword,
                    '城市代码': city_code,
                    '城市': city_name,
                    '时间范围': f"{start_date} 至 {end_date}",
                    '日均值': 0,
                    '同比': '-',
                    '环比': '-',
                    '总值': 0,
                    '爬取时间': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                })
            
            return all_daily_data, all_stats_records
    
    def _process_task(self, task_data):
        """
        处理单个任务的函数，用于线程池
        
        参数:
            task_data (tuple): (keyword, city_code, city_name, start_date, end_date)
        或者 (keywords, city_code, city_name, start_date, end_date) 其中keywords是关键词列表
        
        返回值:
            对于单关键词模式: (task_key, daily_data, stats_record, is_success)
            对于批量模式: ([task_keys], daily_data_list, stats_records_list, is_success)
            其中 is_success 表示是否成功获取到有效数据
        """
        rate_limiter.wait()
        
        # 判断第一个参数是单个关键词还是关键词列表
        if isinstance(task_data[0], list):
            keywords = task_data[0]
            city_code, city_name, start_date, end_date = task_data[1:]
            is_batch = True
            task_desc = f"Batch[{len(keywords)}]: {keywords[0]}... - {city_name}"
        else:
            keyword = task_data[0]
            keywords = [keyword]
            city_code, city_name, start_date, end_date = task_data[1:]
            is_batch = False
            task_desc = f"Single: {keyword} - {city_name}"
        
        log.debug(f"开始处理任务: {task_desc}, 日期: {start_date} 至 {end_date}")
        
        # 检查任务是否已完成（成功完成的任务跳过，失败的任务需要重试）
        if not is_batch:
            task_key = f"{keyword}_{city_code}_{start_date}_{end_date}"
            if task_key in self.completed_keywords:
                # 如果任务已完成，直接返回None，不增加completed_tasks计数
                return None
            # 如果任务之前失败过，从失败集合中移除（准备重试）
            if task_key in self.failed_keywords:
                with self.task_lock:
                    self.failed_keywords.discard(task_key)
        else:
            # 批量模式下，检查所有关键词是否都已完成
            all_completed = True
            for keyword in keywords:
                task_key = f"{keyword}_{city_code}_{start_date}_{end_date}"
                if task_key not in self.completed_keywords:
                    all_completed = False
                    break
                # 如果任务之前失败过，从失败集合中移除（准备重试）
                if task_key in self.failed_keywords:
                    with self.task_lock:
                        self.failed_keywords.discard(task_key)
            
            if all_completed:
                return None
        
        try:
            # 获取数据
            result = self._get_feed_index(city_code, keywords, start_date, end_date)
            if not result:
                log.warning(f"获取数据失败，标记为失败任务: {task_desc}")
                
                # 返回失败标记，不保存空数据
                if not is_batch:
                    return task_key, None, None, False
                else:
                    return [f"{kw}_{city_code}_{start_date}_{end_date}" for kw in keywords], None, None, False
        except NoCookieAvailableError:
            # 向上层抛出异常，通知主线程暂停任务
            raise
        except Exception as e:
            log.error(f"处理任务时出错: {e}")
            # 返回失败标记，不保存空数据
            if not is_batch:
                return task_key, None, None, False
            else:
                return [f"{kw}_{city_code}_{start_date}_{end_date}" for kw in keywords], None, None, False
        
        data, cookie = result
        
        # 处理数据
        if not is_batch:
            # 单关键词处理
            daily_data, stats_record = self._process_feed_index_data(
                data, cookie, keyword, city_code, city_name, start_date, end_date
            )
            
            # 如果处理结果为None，标记为失败
            if daily_data is None or stats_record is None:
                log.warning(f"处理数据失败，标记为失败任务: {task_key}")
                return task_key, None, None, False
            
            # 成功获取数据
            return task_key, daily_data, stats_record, True
        else:
            # 批量处理多个关键词
            daily_data_list, stats_records_list = self._process_multi_feed_index_data(
                data, cookie, keywords, city_code, city_name, start_date, end_date
            )
            
            # 如果处理结果为空，标记为失败
            if not daily_data_list or not stats_records_list:
                log.warning(f"批量处理数据失败，标记为失败任务: {city_code}, {start_date}-{end_date}, 关键词数量: {len(keywords)}")
                return [f"{kw}_{city_code}_{start_date}_{end_date}" for kw in keywords], None, None, False
            
            # 成功获取数据
            return [f"{kw}_{city_code}_{start_date}_{end_date}" for kw in keywords], daily_data_list, stats_records_list, True
    
    # _process_year_range, _load_keywords_from_file, _load_cities_from_file, _load_date_ranges_from_file, _save_data_to_file(_flush_buffer), _fast_count_csv_rows 均由 BaseCrawler 提供
    
    def crawl(self, task_id=None, keywords=None, cities=None, date_ranges=None, days=None, 
              keywords_file=None, cities_file=None, date_ranges_file=None,
              year_range=None, resume=False, checkpoint_task_id=None, total_tasks=None, batch_size=5):
        """
        爬取百度资讯指数数据
        
        参数:
            task_id (str): 任务ID，如果为None则自动生成
            keywords (list): 关键词列表
            cities (dict): 城市代码和名称的字典 {城市代码: 城市名称}
            date_ranges (list): 日期范围列表，每个元素为 (start_date, end_date) 元组
            days (int): 预定义的天数，可以是7、30、90、180
            keywords_file (str): 关键词文件路径
            cities_file (str): 城市代码文件路径
            date_ranges_file (str): 日期范围文件路径
            year_range (tuple): 年份范围，格式为 (start_year, end_year)
            resume (bool): 是否恢复上次任务
            checkpoint_task_id (str): 检查点任务ID
            total_tasks (int): 总任务数（从task_executor传入）
            batch_size (int): 每批处理的关键词数量，默认为5，最大不超过5个
        """
        # 加载关键词
        if keywords_file:
            keywords = self._load_keywords_from_file(keywords_file)
        
        if not keywords:
            log.error("未提供关键词列表")
            return False
            
        # 加载城市
        if cities_file:
            self.city_dict = self._load_cities_from_file(cities_file)
            cities = self.city_dict
        elif cities:
            self.city_dict = cities
        else:
            # 默认使用全国
            cities = {0: "全国"}
            self.city_dict = cities
            
        # 处理日期范围
        log.info(f"爬虫接收到的 date_ranges 参数: {date_ranges}, 类型: {type(date_ranges)}, 长度: {len(date_ranges) if date_ranges else 0}")
        
        if date_ranges_file:
            date_ranges = self._load_date_ranges_from_file(date_ranges_file)
        elif year_range:
            # 处理嵌套列表格式 [[start, end]] 或直接列表格式 [start, end]
            # 支持 list 和 tuple
            if isinstance(year_range, (list, tuple)) and len(year_range) > 0:
                first_elem = year_range[0]
                # 检查首元素是否也是序列 (list/tuple)，且长度>=2
                if isinstance(first_elem, (list, tuple)) and len(first_elem) >= 2:
                    # 嵌套格式 [[start, end]]
                    date_ranges = self._process_year_range(first_elem[0], first_elem[1])
                elif len(year_range) >= 2:
                    # 直接格式 [start, end]
                    date_ranges = self._process_year_range(year_range[0], year_range[1])
                else:
                    log.warning(f"year_range 格式错误 (长度不足): {year_range}")
                    date_ranges = None
            else:
                log.warning(f"year_range 为空或格式错误: {year_range}")
                date_ranges = None
        elif days:
            # 使用预定义的天数
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days-1)).strftime('%Y-%m-%d')
            date_ranges = [(start_date, end_date)]
            
        # 如果经过上述处理后 date_ranges 仍为空（包括传入为None的情况，或者year_range解析失败），使用默认值
        if not date_ranges:
            # 默认使用最近30天
            log.info("未检测到有效的日期范围，使用默认最近30天")
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=29)).strftime('%Y-%m-%d')
            date_ranges = [(start_date, end_date)]
        
        log.info(f"最终使用的 date_ranges 长度: {len(date_ranges)}")
            
        # 设置任务ID和检查点路径
        if resume and checkpoint_task_id:
            self.task_id = checkpoint_task_id
            loaded = self._load_global_checkpoint(checkpoint_task_id)
            if not loaded:
                log.warning(f"未找到任务ID为 {checkpoint_task_id} 的检查点，将创建新任务")
                self.task_id = self._generate_task_id()
                resume = False
            else:
                # 如果成功加载了检查点，使用检查点中的城市字典
                cities = self.city_dict
                log.info(f"从检查点恢复任务: {checkpoint_task_id}, 已完成任务数: {self.completed_tasks}")
        else:
            self.task_id = task_id if task_id else self._generate_task_id()
            # 初始化进度追踪变量
            self.completed_keywords = set()  # 改为使用set而不是list
            self.failed_keywords = set()  # 新增：追踪失败的任务
            # 重置任务计数器
            self.completed_tasks = 0
            self.failed_tasks = 0  # 新增：失败任务计数
            self.current_keyword_index = 0
            self.current_city_index = 0
            self.current_date_range_index = 0
            
        # 如果没有从检查点恢复，则需要设置输出路径和检查点路径
        if not resume:
            self.output_path = os.path.join(OUTPUT_DIR, 'feed_index', self.task_id)
            os.makedirs(self.output_path, exist_ok=True)
            self.checkpoint_path = os.path.join(OUTPUT_DIR, f"checkpoints/feed_index_{self.task_id}_checkpoint.pkl")
            os.makedirs(os.path.dirname(self.checkpoint_path), exist_ok=True)
            # 确保非恢复模式下重置完成任务计数
            self.completed_tasks = 0
            self.failed_tasks = 0  # 新增：重置失败任务计数

        # 加载关键词
        if keywords_file:
            keywords = self._load_keywords_from_file(keywords_file)
        
        if not keywords:
            log.error("未提供关键词列表")
            return False
            
        # 加载城市（如果没有从检查点恢复）
        if not resume:
            if cities_file:
                self.city_dict = self._load_cities_from_file(cities_file)
                cities = self.city_dict
            elif cities:
                # 处理前端传来的城市参数格式
                if isinstance(cities, dict):
                    processed_cities = {}
                    for code, city_info in cities.items():
                        if isinstance(city_info, dict) and 'name' in city_info and 'code' in city_info:
                            processed_cities[city_info['code']] = city_info['name']
                        else:
                            processed_cities[code] = str(city_info)
                    self.city_dict = processed_cities
                else:
                    self.city_dict = cities
            else:
                # 默认使用全国
                cities = {0: "全国"}
                self.city_dict = cities
        
        # 处理日期范围
        log.info(f"爬虫接收到的 date_ranges 参数: {date_ranges}, 类型: {type(date_ranges)}, 长度: {len(date_ranges) if date_ranges else 0}")
        
        if date_ranges_file:
            date_ranges = self._load_date_ranges_from_file(date_ranges_file)
        elif year_range:
            # 处理嵌套列表格式 [[start, end]] 或直接列表格式 [start, end]
            # 支持 list 和 tuple
            if isinstance(year_range, (list, tuple)) and len(year_range) > 0:
                first_elem = year_range[0]
                # 检查首元素是否也是序列 (list/tuple)，且长度>=2
                if isinstance(first_elem, (list, tuple)) and len(first_elem) >= 2:
                    # 嵌套格式 [[start, end]]
                    date_ranges = self._process_year_range(first_elem[0], first_elem[1])
                elif len(year_range) >= 2:
                    # 直接格式 [start, end]
                    date_ranges = self._process_year_range(year_range[0], year_range[1])
                else:
                    log.warning(f"year_range 格式错误 (长度不足): {year_range}")
                    date_ranges = None
            else:
                log.warning(f"year_range 为空或格式错误: {year_range}")
                date_ranges = None
        elif days:
            # 使用预定义的天数
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days-1)).strftime('%Y-%m-%d')
            date_ranges = [(start_date, end_date)]
            
        # 如果经过上述处理后 date_ranges 仍为空（包括传入为None的情况，或者year_range解析失败），使用默认值
        if not date_ranges:
            # 默认使用最近30天
            log.info("未检测到有效的日期范围，使用默认最近30天")
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=29)).strftime('%Y-%m-%d')
            date_ranges = [(start_date, end_date)]
        
        log.info(f"最终使用的 date_ranges 长度: {len(date_ranges)}")
        
        
        
        theoretical_total_tasks = len(keywords) * len(self.city_dict) * len(date_ranges)
        # 初始设置，后面会根据实际任务列表更新
        self.total_tasks = theoretical_total_tasks
            
        log.info(f"任务ID: {self.task_id}")
        log.info(f"总任务数: {self.total_tasks} (关键词: {len(keywords)}, 城市: {len(self.city_dict)}, 日期范围: {len(date_ranges)})")
        
        # 上次进度更新的百分比，用于每增加0.05%进度时更新一次数据库
        last_progress_percent = 0
        # 上次WebSocket推送的进度百分比，用于控制推送频率
        last_ws_progress_percent = 0
        
        # 开始爬取
        try:
            # 准备所有任务
            all_tasks = []
            
            # 强制限制batch_size最大为5
            batch_size = min(batch_size, 5)
            log.info(f"批量处理关键词，每批次最多 {batch_size} 个关键词")
            
            # 按batch_size将关键词分组
            keyword_batches = []
            for i in range(0, len(keywords), batch_size):
                keyword_batches.append(keywords[i:i+batch_size])
            
            # 如果batch_size为1或者只有一个关键词，使用原来的方式
            if batch_size == 1 or len(keywords) == 1:
                log.info(f"使用单任务模式生成任务 (batch_size={batch_size}, keywords={len(keywords)})")
                for keyword in keywords:
                    for city_code, city_name in self.city_dict.items():
                        for start_date, end_date in date_ranges:
                            task_key = f"{keyword}_{city_code}_{start_date}_{end_date}"
                            # 检查任务是否已完成
                            if task_key in self.completed_keywords:
                                log.debug(f"跳过已完成的任务: {task_key}")
                                continue
                            all_tasks.append((keyword, city_code, city_name, start_date, end_date))
            else:
                # 批量处理模式
                log.info(f"使用批量模式生成任务 (batch_size={batch_size}, batches={len(keyword_batches)})")
                for keyword_batch in keyword_batches:
                    for city_code, city_name in self.city_dict.items():
                        for start_date, end_date in date_ranges:
                            # 检查该批次中的所有关键词是否都已完成
                            all_completed = True
                            for keyword in keyword_batch:
                                task_key = f"{keyword}_{city_code}_{start_date}_{end_date}"
                                if task_key not in self.completed_keywords:
                                    all_completed = False
                                    break
                            
                            if all_completed:
                                log.debug(f"跳过已完成的批次任务: {city_code}, {start_date}-{end_date}, 关键词数量: {len(keyword_batch)}")
                                continue
                                    
                            all_tasks.append((keyword_batch, city_code, city_name, start_date, end_date))
            
            # 更新实际总任务数为需要执行的任务数量
            log.info(f"准备执行 {len(all_tasks)} 个任务，使用 {self.max_workers} 个线程")
            
            # 如果所有任务都已完成
            if not all_tasks:
                log.info("所有任务都已完成，无需执行")
                # 更新数据库中的最终状态
                try:
                    from src.data.repositories.mysql_manager import MySQLManager
                    mysql = MySQLManager()
                    
                    update_query = """
                        UPDATE spider_tasks 
                        SET progress = 100, completed_items = %s, status = 'completed', update_time = %s, end_time = %s
                        WHERE task_id = %s
                    """
                    now = datetime.now()
                    mysql.execute_query(update_query, (self.total_tasks, now, now, self.task_id))
                    
                    log.info(f"任务完成! 总共处理了 {self.completed_tasks}/{self.total_tasks} 个任务")
                except Exception as e:
                    log.error(f"更新最终任务状态失败: {e}")
                
                return True
            
            # 使用线程池执行任务
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有任务
                future_to_task = {executor.submit(self._process_task, task): task for task in all_tasks}
                
                # 收集本地缓存
                local_data_cache = []
                local_stats_cache = []
                
                # 处理完成的任务
                try:
                    for future in as_completed(future_to_task):
                        try:
                            result = future.result()
                            if result:
                                # 解析返回值 - 新格式包含 is_success 标记
                                # 判断是单个任务还是批量任务
                                if isinstance(result[0], list):
                                    # 批量任务: (task_keys, daily_data, stats_records, is_success)
                                    if len(result) == 4:
                                        task_keys, daily_data, stats_records, is_success = result
                                    else:
                                        # 兼容旧格式
                                        task_keys, daily_data, stats_records = result
                                        is_success = daily_data is not None and stats_records is not None
                                    
                                    if is_success and daily_data is not None and stats_records is not None:
                                        # 成功：添加到本地缓存
                                        local_data_cache.extend(daily_data)
                                        local_stats_cache.extend(stats_records)
                                        
                                        # 更新全局任务状态并计算进度
                                        current_progress_percent = 0
                                        current_completed_tasks = 0
                                        with self.task_lock:
                                            for task_key in task_keys:
                                                self.completed_keywords.add(task_key)
                                                self.completed_tasks += 1
                                            # 每完成10个任务保存一次检查点
                                            if self.completed_tasks % 10 == 0:
                                                self._save_global_checkpoint()
                                            
                                            # 保存当前值用于锁外使用
                                            current_completed_tasks = self.completed_tasks
                                            # 计算当前进度百分比（包含成功和失败的任务）
                                            total_processed = self.completed_tasks + self.failed_tasks
                                            current_progress_percent = ((total_processed / self.total_tasks) * 100) if self.total_tasks > 0 else 0
                                        
                                        # 在锁外推送WebSocket，避免阻塞
                                        # 每完成5个任务或进度增加0.1%时推送WebSocket更新
                                        if current_progress_percent >= last_ws_progress_percent + 0.1 or current_completed_tasks % 5 == 0:
                                            last_ws_progress_percent = current_progress_percent
                                            # 立即推送 WebSocket 更新（不等待数据库更新）
                                            try:
                                                from src.services.websocket_service import emit_task_update
                                                emit_task_update(self.task_id, {
                                                    'progress': min(current_progress_percent, 100),
                                                    'completed_items': current_completed_tasks,
                                                    'failed_items': self.failed_tasks,
                                                    'total_items': self.total_tasks,
                                                    'status': 'running'
                                                })
                                            except Exception as ws_error:
                                                log.debug(f"推送 WebSocket 更新失败: {ws_error}")
                                    else:
                                        # 失败：标记为失败任务
                                        with self.task_lock:
                                            for task_key in task_keys:
                                                self.failed_keywords.add(task_key)
                                                self.failed_tasks += 1
                                            log.warning(f"批量任务失败，已标记 {len(task_keys)} 个任务为失败状态")
                                else:
                                    # 单个任务: (task_key, daily_data, stats_record, is_success)
                                    if len(result) == 4:
                                        task_key, daily_data, stats_record, is_success = result
                                    else:
                                        # 兼容旧格式
                                        task_key, daily_data, stats_record = result
                                        is_success = daily_data is not None and stats_record is not None
                                    
                                    if is_success and daily_data is not None and stats_record is not None:
                                        # 成功：添加到本地缓存
                                        local_data_cache.extend(daily_data)
                                        local_stats_cache.append(stats_record)
                                        
                                        # 更新全局任务状态并计算进度
                                        current_progress_percent = 0
                                        current_completed_tasks = 0
                                        with self.task_lock:
                                            self.completed_keywords.add(task_key)
                                            self.completed_tasks += 1
                                            # 每完成10个任务保存一次检查点
                                            if self.completed_tasks % 10 == 0:
                                                self._save_global_checkpoint()
                                            
                                            # 保存当前值用于锁外使用
                                            current_completed_tasks = self.completed_tasks
                                            # 计算当前进度百分比（包含成功和失败的任务）
                                            total_processed = self.completed_tasks + self.failed_tasks
                                            current_progress_percent = ((total_processed / self.total_tasks) * 100) if self.total_tasks > 0 else 0
                                        
                                        # 在锁外推送WebSocket，避免阻塞
                                        # 每完成5个任务或进度增加0.1%时推送WebSocket更新
                                        if current_progress_percent >= last_ws_progress_percent + 0.1 or current_completed_tasks % 5 == 0:
                                            last_ws_progress_percent = current_progress_percent
                                            # 立即推送 WebSocket 更新（不等待数据库更新）
                                            try:
                                                from src.services.websocket_service import emit_task_update
                                                emit_task_update(self.task_id, {
                                                    'progress': min(current_progress_percent, 100),
                                                    'completed_items': current_completed_tasks,
                                                    'failed_items': self.failed_tasks,
                                                    'total_items': self.total_tasks,
                                                    'status': 'running'
                                                })
                                            except Exception as ws_error:
                                                log.debug(f"推送 WebSocket 更新失败: {ws_error}")
                                    else:
                                        # 失败：标记为失败任务
                                        with self.task_lock:
                                            self.failed_keywords.add(task_key)
                                            self.failed_tasks += 1
                                            log.warning(f"任务失败: {task_key}")
                                
                                # 定期保存数据
                                if len(local_data_cache) >= 200:
                                    with self.save_lock:
                                        self._save_data_to_file(local_data_cache, local_stats_cache)
                                    local_data_cache = []
                                    local_stats_cache = []
                                    
                                    # 计算当前进度百分比
                                    current_progress_percent = ((self.completed_tasks / self.total_tasks) * 100)
                                    # 每完成0.05%的任务更新一次数据库进度
                                    if current_progress_percent >= last_progress_percent + 0.05:
                                        last_progress_percent = current_progress_percent
                                        try:
                                            # 连接数据库
                                            from src.data.repositories.mysql_manager import MySQLManager
                                            mysql = MySQLManager()
                                            
                                            # 更新任务进度
                                            update_query = """
                                                UPDATE spider_tasks 
                                                SET progress = %s, completed_items = %s, update_time = %s
                                                WHERE task_id = %s
                                            """
                                            affected_rows = mysql.execute_query(
                                                update_query, 
                                                (min(current_progress_percent, 100), self.completed_tasks, datetime.now(), self.task_id)
                                            )
                                            
                                            if affected_rows > 0:
                                                log.info(f"已更新数据库进度: {min(current_progress_percent, 100)}%, 完成任务: {self.completed_tasks}/{self.total_tasks}")
                                            else:
                                                log.warning(f"数据库进度更新失败: 影响行数为0, task_id: {self.task_id}")
                                        except Exception as e:
                                            log.error(f"更新数据库进度失败: {e}")
                                            log.error(traceback.format_exc())
                                    
                        except NoCookieAvailableError:
                            # 处理没有可用Cookie的情况
                            log.error("没有可用的Cookie，暂停任务并保存当前进度")
                            
                            # 保存当前进度
                            self._save_data_cache(force=True)
                            self._save_global_checkpoint()
                            
                            # 更新数据库中的任务状态为暂停
                            try:
                                from src.data.repositories.mysql_manager import MySQLManager
                                mysql = MySQLManager()
                                
                                update_query = """
                                    UPDATE spider_tasks 
                                    SET status = 'paused', progress = %s, completed_items = %s, 
                                        error_message = %s, update_time = %s
                                    WHERE task_id = %s
                                """
                                progress = min(int((self.completed_tasks / self.total_tasks) * 100) if self.total_tasks > 0 else 0, 100)
                                mysql.execute_query(
                                    update_query, 
                                    (progress, self.completed_tasks, "所有Cookie均被锁定，任务暂停等待可用Cookie", datetime.now(), self.task_id)
                                )
                                
                                log.info(f"任务已暂停，等待Cookie可用: {self.task_id}")
                            except Exception as e:
                                log.error(f"更新任务状态失败: {e}")
                            
                            # 取消所有未完成的任务
                            for f in future_to_task:
                                if not f.done() and not f.cancelled():
                                    f.cancel()
                            
                            # 提前返回，等待定时任务恢复
                            return False
                            
                        except Exception as e:
                            log.error(f"处理任务时出错: {e}")
                            log.error(traceback.format_exc())
                
                    # 保存剩余的数据
                    if local_data_cache:
                        with self.save_lock:
                            self._save_data_to_file(local_data_cache, local_stats_cache)
                
                except Exception as e:
                    log.error(f"任务执行过程中出错: {e}")
                    log.error(traceback.format_exc())
                    
                    # 保存当前进度
                    self._save_data_cache(force=True)
                    self._save_global_checkpoint()
                    log.error(f"任务执行过程中出错: {e}")
                    # 如果是NoCookieAvailableError，更新任务状态为暂停
                    if isinstance(e, NoCookieAvailableError):
                        log.warning("没有可用的Cookie，任务将被暂停")
                        try:
                            from src.data.repositories.mysql_manager import MySQLManager
                            mysql = MySQLManager()
                            
                            update_query = """
                                UPDATE spider_tasks 
                                SET status = 'paused', progress = %s, completed_items = %s, 
                                    error_message = %s, update_time = %s
                                WHERE task_id = %s
                            """
                            progress = min(int((self.completed_tasks / self.total_tasks) * 100) if self.total_tasks > 0 else 0, 100)
                            mysql.execute_query(
                                update_query, 
                                (progress, self.completed_tasks, "所有Cookie均被锁定，任务暂停等待可用Cookie", datetime.now(), self.task_id)
                            )
                            
                            log.info(f"任务已暂停，等待Cookie可用: {self.task_id}")
                        except Exception as db_error:
                            log.error(f"更新任务状态失败: {db_error}")
                        
                        return False
                    else:
                        log.error("任务因非Cookie问题失败")
                        # 只有非Cookie问题才标记为失败
                        try:
                            from src.data.repositories.mysql_manager import MySQLManager
                            mysql = MySQLManager()
                            
                            update_query = """
                                UPDATE spider_tasks 
                                SET status = 'failed', progress = %s, completed_items = %s, 
                                    error_message = %s, update_time = %s
                                WHERE task_id = %s
                            """
                            progress = min(int((self.completed_tasks / self.total_tasks) * 100) if self.total_tasks > 0 else 0, 100)
                            mysql.execute_query(
                                update_query, 
                                (progress, self.completed_tasks, f"任务执行出错: {str(e)[:500]}", datetime.now(), self.task_id)
                            )
                            
                            log.error(f"任务执行失败: {self.task_id}")
                        except Exception as db_error:
                            log.error(f"更新任务状态失败: {db_error}")
                        
                        return False
            
            # 最后保存所有剩余数据和检查点
            self._save_data_cache(status="completed", force=True)
            self._save_global_checkpoint()
            
            # 更新数据库中的最终状态
            try:
                from src.data.repositories.mysql_manager import MySQLManager
                mysql = MySQLManager()
                
                # 计算完成进度和失败率
                total_processed = self.completed_tasks + self.failed_tasks
                final_progress = min(int((total_processed / self.total_tasks) * 100) if self.total_tasks > 0 else 0, 100)
                final_completed = self.completed_tasks
                
                # 判断任务是否应该标记为失败
                # 如果有失败的任务，将任务标记为失败状态，以便重试
                if self.failed_tasks > 0:
                    fail_rate = (self.failed_tasks / self.total_tasks * 100) if self.total_tasks > 0 else 0
                    error_message = f"任务执行完成但有 {self.failed_tasks} 个子任务失败（失败率: {fail_rate:.2f}%），需要重试"
                    
                    update_query = """
                        UPDATE spider_tasks 
                        SET progress = %s, completed_items = %s, failed_items = %s, 
                            status = 'failed', error_message = %s, update_time = %s, end_time = %s
                        WHERE task_id = %s
                    """
                    now = datetime.now()
                    mysql.execute_query(update_query, (final_progress, final_completed, self.failed_tasks, error_message, now, now, self.task_id))
                    
                    log.warning(f"任务完成但有失败项! 成功: {self.completed_tasks}, 失败: {self.failed_tasks}, 总计: {self.total_tasks}")
                    
                    # 推送 WebSocket 更新
                    try:
                        from src.services.websocket_service import emit_task_update
                        emit_task_update(self.task_id, {
                            'progress': final_progress,
                            'completed_items': final_completed,
                            'failed_items': self.failed_tasks,
                            'total_items': self.total_tasks,
                            'status': 'failed',
                            'error_message': error_message
                        })
                    except Exception as ws_error:
                        log.debug(f"推送 WebSocket 更新失败: {ws_error}")
                    
                    return False
                else:
                    # 全部成功完成
                    update_query = """
                        UPDATE spider_tasks 
                        SET progress = 100, completed_items = %s, failed_items = 0, 
                            status = 'completed', update_time = %s, end_time = %s
                        WHERE task_id = %s
                    """
                    now = datetime.now()
                    mysql.execute_query(update_query, (final_completed, now, now, self.task_id))
                    
                    log.info(f"任务完成! 总共处理了 {self.completed_tasks}/{self.total_tasks} 个任务")
                    
                    # 推送 WebSocket 更新
                    try:
                        from src.services.websocket_service import emit_task_update
                        emit_task_update(self.task_id, {
                            'progress': 100,
                            'completed_items': final_completed,
                            'failed_items': 0,
                            'total_items': self.total_tasks,
                            'status': 'completed'
                        })
                    except Exception as ws_error:
                        log.debug(f"推送 WebSocket 更新失败: {ws_error}")
                    
                    return True
            except Exception as e:
                log.error(f"更新最终任务状态失败: {e}")
                return False
            
        except Exception as e:
            log.error(f"爬取过程中出错: {str(e)}")
            log.error(traceback.format_exc())
            # 保存当前进度和数据
            self._save_data_cache(force=True)
            self._save_global_checkpoint()
            
            # 更新数据库中的错误状态
            try:
                from src.data.repositories.mysql_manager import MySQLManager
                mysql = MySQLManager()
                
                # 如果是NoCookieAvailableError，更新任务状态为暂停
                if isinstance(e, NoCookieAvailableError):
                    update_query = """
                        UPDATE spider_tasks 
                        SET status = 'paused', progress = %s, completed_items = %s, 
                            error_message = %s, update_time = %s
                        WHERE task_id = %s
                    """
                    error_message = "所有Cookie均被锁定，任务暂停等待可用Cookie"
                    
                    progress = min(int((self.completed_tasks / self.total_tasks) * 100) if self.total_tasks > 0 else 0, 100)
                    mysql.execute_query(
                        update_query, 
                        (progress, self.completed_tasks, error_message, datetime.now(), self.task_id)
                    )
                    
                    log.info(f"任务已暂停，等待Cookie可用: {self.task_id}")
                else:
                    update_query = """
                        UPDATE spider_tasks 
                        SET progress = %s, completed_items = %s, status = 'failed', 
                            error_message = %s, update_time = %s
                        WHERE task_id = %s
                    """
                    error_message = str(e)[:500]
                    
                    progress = min(int((self.completed_tasks / self.total_tasks) * 100) if self.total_tasks > 0 else 0, 100)
                    mysql.execute_query(
                        update_query, 
                        (progress, self.completed_tasks, error_message, datetime.now(), self.task_id)
                    )
                    
                    log.error(f"任务执行失败: {self.task_id}")
            except Exception as db_error:
                log.error(f"更新任务错误状态失败: {db_error}")
                
            # 如果是NoCookieAvailableError，返回False但不视为失败
            if isinstance(e, NoCookieAvailableError):
                return False
            else:
                return False
    
    def resume_task(self, task_id):
        """恢复指定的任务"""
        return self.crawl(resume=True, task_id=task_id)
    
    def list_tasks(self):
        """列出所有任务及其状态"""
        checkpoint_dir = os.path.join(OUTPUT_DIR, "checkpoints")
        if not os.path.exists(checkpoint_dir):
            log.info("没有找到任何任务")
            return []
            
        tasks = []
        for file in os.listdir(checkpoint_dir):
            if file.startswith("feed_index_") and file.endswith("_checkpoint.pkl"):
                task_id = file.split("feed_index_")[1].split("_checkpoint.pkl")[0]
                checkpoint_path = os.path.join(checkpoint_dir, file)
                
                with open(checkpoint_path, 'rb') as f:
                    checkpoint = pickle.load(f)
                    completed = checkpoint.get('completed_tasks', 0)
                    total = checkpoint.get('total_tasks', 0)
                    
                tasks.append({
                    'task_id': task_id,
                    'completed': completed,
                    'total': total,
                    'progress': f"{completed}/{total} ({completed/total*100:.2f}%)" if total > 0 else "0%"
                })
                
        return tasks

# 创建爬虫实例
feed_index_crawler = FeedIndexCrawler()