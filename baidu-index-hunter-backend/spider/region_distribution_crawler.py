"""
地域分布爬虫（人群画像的地域分布）
"""
import pandas as pd
import requests
import json
import time
import os
import pickle
import signal
import atexit
from datetime import datetime, timedelta
import threading
import sys
import os
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.logger import log
from utils.rate_limiter import rate_limiter
from utils.retry_decorator import retry
from utils.cipher_text import cipher_text_generator
from cookie_manager.cookie_rotator import cookie_rotator
from config.settings import BAIDU_INDEX_API, OUTPUT_DIR
from utils.data_processor import data_processor
from fake_useragent import UserAgent


class RegionDistributionCrawler:
    """地域分布爬虫，负责获取百度指数的地域分布数据"""
    
    # 预定义的天数选项
    DAYS_OPTIONS = [7, 30, 90, 180, 365]
    
    def __init__(self):
        """初始化地域分布爬虫"""
        self.region_api_url = BAIDU_INDEX_API['region_api_url']
        self.referer = BAIDU_INDEX_API['referer']
        self.ua = UserAgent()
        self.checkpoint_dir = os.path.join(OUTPUT_DIR, 'checkpoints')
        self.output_dir = os.path.join(OUTPUT_DIR, 'region_distributions')
        
        # 创建必要的目录
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 初始化任务状态
        self.task_status = {}
        self.lock = threading.RLock()
        
        # 初始化数据缓存
        self.data_cache = []
        self.data_cache_size = 100  # 每收集100条数据就保存一次
        
        # 注册退出处理函数
        atexit.register(self._save_on_exit)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, sig, frame):
        """
        处理程序中断信号
        :param sig: 信号类型
        :param frame: 当前帧
        """
        log.info(f"接收到中断信号 {sig}，正在保存数据和检查点...")
        self._save_on_exit()
        sys.exit(0)
    
    def _save_on_exit(self):
        """在程序退出时保存数据和检查点"""
        log.info("程序即将退出，保存数据和检查点...")
        # 保存数据缓存
        self._save_data_cache(force=True)
        # 保存当前任务状态作为检查点
        task_id = self._get_current_task_id()
        if task_id:
            self._save_global_checkpoint(task_id)
    
    def _save_data_cache(self, force=False):
        """
        保存数据缓存到CSV文件
        :param force: 是否强制保存，即使缓存未达到阈值
        :return: 是否保存成功
        """
        with self.lock:
            # 如果缓存为空，不保存
            if not self.data_cache:
                return False
            
            # 如果缓存未达到阈值且非强制保存，不保存
            if len(self.data_cache) < self.data_cache_size and not force:
                return False
            
            # 获取当前任务ID
            task_id = self._get_current_task_id()
            if not task_id:
                log.warning("无法获取当前任务ID，使用时间戳作为文件名")
                task_id = datetime.now().strftime('%Y%m%d%H%M%S')
            
            # 创建DataFrame
            df = pd.DataFrame(self.data_cache)
            
            # 构建输出文件路径
            output_path = os.path.join(self.output_dir,task_id, f"region_distributions_{task_id}.csv")
            
            # 保存数据
            try:
                if os.path.exists(output_path):
                    # 追加到现有文件
                    data_processor.append_to_csv(df, output_path)
                else:
                    # 创建新文件
                    data_processor.save_to_csv(df, output_path)
                
                log.info(f"成功保存 {len(self.data_cache)} 条数据到 {output_path}")
                
                # 更新任务状态中的输出文件路径
                if task_id in self.task_status:
                    self.task_status[task_id]['output_file'] = output_path
                
                # 清空缓存
                self.data_cache = []
                return True
            except Exception as e:
                log.error(f"保存数据缓存失败: {e}")
                return False
    
    def _get_checkpoint_path(self, task_id):
        """
        获取全局检查点文件路径
        :param task_id: 任务ID
        :return: 检查点文件路径
        """
        return os.path.join(self.checkpoint_dir, f"region_distributions_checkpoint_{task_id}.pkl")
    
    def _save_global_checkpoint(self, task_id):
        """
        保存全局检查点
        :param task_id: 任务ID
        """
        checkpoint_path = self._get_checkpoint_path(task_id)
        try:
            with self.lock:
                with open(checkpoint_path, 'wb') as f:
                    pickle.dump(self.task_status[task_id], f)
            log.info(f"已保存全局检查点: {checkpoint_path}")
        except Exception as e:
            log.error(f"保存全局检查点失败: {e}")
    
    def _load_global_checkpoint(self, task_id):
        """
        加载全局检查点
        :param task_id: 任务ID
        :return: 任务状态，如果不存在则返回None
        """
        checkpoint_path = self._get_checkpoint_path(task_id)
        if not os.path.exists(checkpoint_path):
            return None
        
        try:
            with open(checkpoint_path, 'rb') as f:
                status = pickle.load(f)
            log.info(f"已加载全局检查点: {checkpoint_path}")
            return status
        except Exception as e:
            log.error(f"加载全局检查点失败: {e}")
            return None
    
    def _get_output_path(self, task_id, file_type='csv'):
        """
        获取输出文件路径
        :param task_id: 任务ID
        :param file_type: 文件类型，默认为csv
        :return: 输出文件路径
        """
        return os.path.join(self.output_dir, f"region_distributions_{task_id}.{file_type}")
    
    def _get_current_task_id(self):
        """
        获取当前正在执行的任务ID
        :return: 任务ID，如果没有当前任务则返回None
        """
        with self.lock:
            # 查找状态为'running'的任务
            for task_id, status in self.task_status.items():
                if status.get('status') == 'running':
                    return task_id
        return None
    
    def _calculate_date_range(self, days=None, start_date=None, end_date=None):
        """
        计算日期范围
        :param days: 天数，可选值：7, 30, 90, 180, 365
        :param start_date: 开始日期，格式：YYYY-MM-DD
        :param end_date: 结束日期，格式：YYYY-MM-DD
        :return: (start_date, end_date, days)
        """
        # 如果指定了开始和结束日期，则使用自定义日期范围
        if start_date and end_date:
            return start_date, end_date, None
        
        # 如果指定了天数，则计算开始日期
        if days in self.DAYS_OPTIONS:
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            return start_date, end_date, days
        
        # 默认使用30天
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        return start_date, end_date, 30
    
    @retry(max_retries=2)
    def get_region_distribution(self, keywords, region=0, days=None, start_date=None, end_date=None):
        """
        获取地域分布数据
        :param keywords: 关键词列表或字符串（逗号分隔）
        :param region: 地区代码，0表示全国
        :param days: 天数，可选值：7, 30, 90, 180, 365
        :param start_date: 开始日期，格式：YYYY-MM-DD
        :param end_date: 结束日期，格式：YYYY-MM-DD
        :return: 地域分布数据字典或None（请求失败）
        """
        try:
            # 确保关键词是字符串
            if isinstance(keywords, list):
                keywords = ','.join(keywords)
            
            # 计算日期范围
            start_date, end_date, days_param = self._calculate_date_range(days, start_date, end_date)
            
            # 获取一个可用的cookie
            account_id, cookie_dict = cookie_rotator.get_cookie()
            if not cookie_dict:
                log.warning(f"无法获取可用Cookie进行请求 {keywords}，所有Cookie可能都被锁定")
                # 等待有可用的cookie (最多等待30秒)
                if cookie_rotator.wait_for_available_cookie(timeout=30):
                    log.info(f"检测到有可用Cookie，重试获取 {keywords}")
                    # 重新尝试获取cookie
                    account_id, cookie_dict = cookie_rotator.get_cookie()
                    if not cookie_dict:
                        log.error(f"尽管收到可用Cookie通知，但仍无法获取Cookie，放弃请求 {keywords}")
                        return None
                else:
                    log.error(f"等待可用Cookie超时，放弃请求 {keywords}")
                    return None
            
            # 构建请求URL
            url_params = [f'region={region}', f'word={keywords}', f'startDate={start_date}', f'endDate={end_date}']
            
            # 如果指定了天数，添加到URL参数中
            if days_param:
                url_params.append(f'days={days_param}')
            
            url = f'{self.region_api_url}?{"&".join(url_params)}'
            
            # 构建请求头
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Pragma': 'no-cache',
                'Referer': self.referer,
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': self.ua.random,
                'sec-ch-ua': '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
            }
            
            # 频率控制
            rate_limiter.wait()
            
            # 发送请求
            region_name = "全国" if region == 0 else f"地区ID: {region}"
            log.info(f"请求地域分布: {keywords}, {region_name}, 日期范围: {start_date} 至 {end_date}")
            response = requests.get(
                url=url,
                headers=headers,
                cookies=cookie_dict,
                timeout=10
            )
            
            # 检查响应状态
            if response.status_code != 200:
                log.error(f"请求失败，状态码: {response.status_code}, 响应内容: {response.text}")
                cookie_rotator.report_cookie_status(account_id, False)
                return None
            
            # 解析响应内容
            result = response.json()
            
            # 检查API返回的状态码
            if result.get('status') != 0:
                error_msg = result.get('message', '未知错误')
                log.error(f"API返回错误: {error_msg}")
                
                # 如果是"not login"错误，将cookie标记为永久封禁
                if error_msg == "not login":
                    log.error(f"检测到'not login'错误，账号 {account_id} 的Cookie已失效，将被永久封禁")
                    cookie_rotator.report_cookie_status(account_id, False, permanent=True)
                    
                    # 等待看是否有其他可用Cookie
                    if cookie_rotator.wait_for_available_cookie(timeout=10):
                        log.info(f"检测到有其他可用Cookie，重试获取 {keywords}")
                        # 递归调用自身重试
                        return self.get_region_distribution(keywords, region, days, start_date, end_date)
                else:
                    # 其他错误，临时锁定cookie
                    cookie_rotator.report_cookie_status(account_id, False)
                
                return None
            
            # 如果请求成功，标记cookie为有效
            cookie_rotator.report_cookie_status(account_id, True)
            
            log.info(f"成功获取 {keywords} 的地域分布数据")
            return result
            
        except Exception as e:
            log.error(f"获取地域分布数据失败: {e}")
            # 如果是因为cookie问题，将其标记为无效
            if account_id:
                cookie_rotator.report_cookie_status(account_id, False)
            return None
    
    def crawl(self, task_id=None, keywords=None, regions=None, days=None, start_date=None, end_date=None, 
              output_format='csv', resume=True, checkpoint_task_id=None):
        """
        爬取多个关键词的地域分布数据
        :param task_id: 任务ID，如果为None则自动生成
        :param keywords: 关键词列表或字符串（逗号分隔）
        :param regions: 地区代码列表，默认为[0]（全国）
        :param days: 天数，可选值：7, 30, 90, 180, 365
        :param start_date: 开始日期，格式：YYYY-MM-DD
        :param end_date: 结束日期，格式：YYYY-MM-DD
        :param output_format: 输出格式，可选值：csv, excel
        :param resume: 是否从上次中断的地方继续爬取
        :param checkpoint_task_id: 检查点任务ID，如果为None则自动生成
        :return: 是否全部爬取成功
        """
        # 确保输入是列表
        if isinstance(keywords, str):
            if ',' in keywords:
                keywords = keywords.split(',')
            else:
                keywords = [keywords]
        
        # 确保regions是列表
        if regions is None:
            regions = [0]  # 默认为全国
        elif not isinstance(regions, list):
            regions = [regions]
        
        # 确定任务ID
        if task_id is None:
            task_id = datetime.now().strftime('%Y%m%d%H%M%S')
        
        log.info(f"开始爬取 {len(keywords)} 个关键词在 {len(regions)} 个地区的地域分布数据，任务ID: {task_id}")
        
        # 初始化任务状态
        with self.lock:
            # 检查是否有检查点数据
            checkpoint_status = None
            if resume:
                checkpoint_status = self._load_global_checkpoint(checkpoint_task_id)
            
            if checkpoint_status:
                log.info(f"从检查点恢复任务: {checkpoint_task_id}")
                self.task_status[task_id] = checkpoint_status
                
                # 检查数据文件是否存在
                output_file = checkpoint_status.get('output_file')
                if output_file and os.path.exists(output_file):
                    log.info(f"找到已存在的数据文件: {output_file}")
                else:
                    log.warning(f"未找到数据文件，将创建新文件")
                    self.task_status[task_id]['output_file'] = self._get_output_path(task_id, output_format)
            else:
                # 创建新任务状态
                log.info(f"创建新任务: {task_id}")
                self.task_status[task_id] = {
                    'task_id': task_id,
                    'status': 'running',
                    'total': len(regions),  # 总任务数是地区数量
                    'completed': 0,
                    'failed': 0,
                    'progress': 0,
                    'start_time': datetime.now(),
                    'last_update_time': datetime.now(),
                    'keywords': keywords,
                    'regions': regions,
                    'days': days,
                    'start_date': start_date,
                    'end_date': end_date,
                    'output_format': output_format,
                    'output_file': self._get_output_path(task_id, output_format),
                    'results': {},  # 存储已完成任务的状态，格式：{region: {'status': 'success|failed', ...}}
                    'checkpoint_time': datetime.now(),
                    'processed_regions': []  # 存储已处理的地区
                }
                
                # 保存初始检查点
                self._save_global_checkpoint(task_id)
        
        # 计算总任务数和已完成任务数
        total_tasks = len(regions)
        completed_tasks = 0
        
        # 如果有检查点，计算已完成的任务数
        if checkpoint_status:
            completed_tasks = checkpoint_status.get('completed', 0)
            log.info(f"从检查点恢复：总任务数 {total_tasks}，已完成 {completed_tasks}，进度 {completed_tasks/total_tasks*100:.2f}%")
        
        # 获取已处理的地区
        processed_regions = self.task_status[task_id].get('processed_regions', [])
        
        # 遍历每个地区
        for region in regions:
            # 检查这个地区是否已经处理过
            if region in processed_regions:
                log.info(f"跳过已处理的地区: {region}")
                continue
            
            log.info(f"处理地区: {region}")
            
            # 获取地域分布数据
            result = None
            max_retries = 3  # 最大重试次数
            retry_count = 0
            
            while result is None and retry_count < max_retries:
                result = self.get_region_distribution(
                    keywords=keywords, 
                    region=region,
                    days=days,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if result is None:
                    retry_count += 1
                    # 检查是否所有Cookie都被锁定
                    cookie_status = cookie_rotator.get_status()
                    all_cookies_blocked = cookie_status.get('available', 0) == 0 and cookie_status.get('blocked', 0) > 0
                    
                    if all_cookies_blocked:
                        log.warning(f"所有Cookie都被锁定，等待可用Cookie后重试 (尝试 {retry_count}/{max_retries})")
                        # 等待Cookie可用，最多等待60秒
                        if cookie_rotator.wait_for_available_cookie(timeout=60):
                            log.info(f"检测到有可用Cookie，重试获取地区 {region}")
                        else:
                            log.warning(f"等待可用Cookie超时，尝试继续重试 (尝试 {retry_count}/{max_retries})")
                    else:
                        # 如果不是因为所有Cookie都被锁定，则短暂等待后重试
                        wait_time = retry_count * 5  # 逐渐增加等待时间
                        log.info(f"请求失败，等待 {wait_time} 秒后重试 (尝试 {retry_count}/{max_retries})")
                        time.sleep(wait_time)
            
            # 处理结果
            if result:
                # 使用data_processor处理数据
                df = data_processor.process_region_distribution_data(result, region)
                
                # 将数据添加到缓存
                with self.lock:
                    self.data_cache.extend(df.to_dict('records'))
                    
                    # 如果缓存达到阈值，保存数据
                    if len(self.data_cache) >= self.data_cache_size:
                        self._save_data_cache()
                
                # 更新任务状态
                with self.lock:
                    # 标记地区为已完成
                    self.task_status[task_id]['completed'] += 1
                    self.task_status[task_id]['results'][region] = {
                        'status': 'success',
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    # 标记地区为已处理
                    self.task_status[task_id]['processed_regions'].append(region)
                    
                    # 更新进度
                    self.task_status[task_id]['progress'] = round(self.task_status[task_id]['completed'] / self.task_status[task_id]['total'] * 100, 2)
                    self.task_status[task_id]['last_update_time'] = datetime.now()
                
                # 定期保存检查点
                self._save_global_checkpoint(task_id)
                self.task_status[task_id]['checkpoint_time'] = datetime.now()
                
                log.info(f"成功爬取地区 {region} 的数据，共 {len(df)} 条记录，"
                       f"总进度：{self.task_status[task_id]['progress']}%")
            else:
                # 更新任务状态
                with self.lock:
                    # 标记地区为失败
                    self.task_status[task_id]['failed'] += 1
                    self.task_status[task_id]['results'][region] = {
                        'status': 'failed',
                        'error': '请求失败或数据处理失败',
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    self.task_status[task_id]['last_update_time'] = datetime.now()
                
                log.error(f"爬取地区 {region} 失败")
        
        # 保存剩余的数据缓存
        self._save_data_cache(force=True)
        
        # 更新任务完成状态
        with self.lock:
            self.task_status[task_id]['status'] = 'completed'
            self.task_status[task_id]['end_time'] = datetime.now()
            elapsed_time = (self.task_status[task_id]['end_time'] - self.task_status[task_id]['start_time']).total_seconds()
            success_rate = round(self.task_status[task_id]['completed'] / self.task_status[task_id]['total'] * 100, 2)
            
            log.info(f"任务 {task_id} 完成: 总计 {self.task_status[task_id]['total']} 个地区，"
                   f"成功 {self.task_status[task_id]['completed']} 个，"
                   f"失败 {self.task_status[task_id]['failed']} 个，"
                   f"成功率 {success_rate}%，"
                   f"耗时 {elapsed_time:.2f} 秒")
            
            # 保存最终检查点
            self._save_global_checkpoint(task_id)
            
            return self.task_status[task_id]['failed'] == 0
    
    def resume_task(self, task_id):
        """
        恢复指定的任务
        :param task_id: 任务ID
        :return: 是否成功恢复并完成任务
        """
        # 加载检查点
        checkpoint_status = self._load_global_checkpoint(task_id)
        if not checkpoint_status:
            log.error(f"无法恢复任务 {task_id}，检查点不存在")
            return False
        
        # 获取任务参数
        keywords = checkpoint_status.get('keywords', [])
        regions = checkpoint_status.get('regions', [0])
        days = checkpoint_status.get('days')
        start_date = checkpoint_status.get('start_date')
        end_date = checkpoint_status.get('end_date')
        output_format = checkpoint_status.get('output_format', 'csv')
        
        # 恢复任务
        return self.crawl(
            keywords=keywords, 
            regions=regions,
            days=days,
            start_date=start_date,
            end_date=end_date,
            output_format=output_format, 
            resume=True, 
            task_id=task_id
        )
    
    def get_task_status(self, task_id=None):
        """
        获取任务状态
        :param task_id: 任务ID，如果为None则返回最新的任务状态
        :return: 任务状态字典
        """
        with self.lock:
            if not self.task_status:
                return None
            
            if task_id is None:
                # 返回最新的任务状态
                return self.task_status[list(self.task_status.keys())[-1]]
            
            return self.task_status.get(task_id)
    
    def list_tasks(self):
        """
        列出所有任务
        :return: 任务摘要列表
        """
        tasks = []
        with self.lock:
            for task_id, status in self.task_status.items():
                tasks.append({
                    'task_id': task_id,
                    'status': status.get('status', 'unknown'),
                    'total': status.get('total', 0),
                    'completed': status.get('completed', 0),
                    'failed': status.get('failed', 0),
                    'progress': status.get('progress', 0),
                    'start_time': status.get('start_time'),
                    'last_update_time': status.get('last_update_time'),
                    'output_file': status.get('output_file')
                })
        return tasks


# 创建地域分布爬虫单例
region_distribution_crawler = RegionDistributionCrawler()


if __name__ == "__main__":
    # 示例用法
    keywords = ["电脑", "手机", "平板"]
    regions = [0, 916]  # 0表示全国，916表示江苏
    
    # 爬取数据
    region_distribution_crawler.crawl(keywords, regions=regions, days=30, output_format='csv', resume=True)
