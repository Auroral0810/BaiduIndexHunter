"""
关键词检查爬虫

检查百度指数中关键词是否存在
继承自 BaseBaiduIndexSpider，使用 Scrapy 框架
"""
import json
import scrapy
from datetime import datetime

from .base_spider import BaseBaiduIndexSpider
from scrapy_app.items import WordCheckItem


class WordCheckSpider(BaseBaiduIndexSpider):
    """关键词检查爬虫"""
    
    name = 'word_check'
    
    # 关键词检查 API
    CHECK_URL = "https://index.baidu.com/api/AddWordApi/checkWordsExists"
    
    # 自定义设置
    custom_settings = {
        'CONCURRENT_REQUESTS': 10,  # 并发请求数
        'DOWNLOAD_DELAY': 0.5,      # 下载延迟
    }
    
    def __init__(self, *args, **kwargs):
        """
        初始化关键词检查爬虫
        
        Args:
            task_id: 任务ID
            keywords: 要检查的关键词列表 (JSON字符串或列表)
        """
        # 调用父类初始化
        super().__init__(*args, **kwargs)
    
    def _calculate_total_items(self):
        """计算总任务数（覆盖父类方法）"""
        self.total_items = len(self.keywords)
    
    async def start(self):
        """生成所有请求（Scrapy 2.13+ 新 API）"""
        for keyword in self.keywords:
            url = f"{self.CHECK_URL}?word={keyword}"
            
            yield self.make_request(
                url=url,
                callback=self.parse,
                meta={
                    'keyword': keyword,
                },
                priority=1,
            )
    
    def parse(self, response):
        """解析关键词检查响应"""
        keyword = response.meta['keyword']
        crawl_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            data = json.loads(response.text)
            
            # 检查响应状态
            status = data.get('status')
            
            if status == 0:
                # 状态码为0表示请求成功
                result = data.get('data', {}).get('result', [])
                # 如果result为空列表，说明关键词存在
                exists = len(result) == 0
                
                item = WordCheckItem()
                item['task_id'] = self.task_id
                item['keyword'] = keyword
                item['exists'] = exists
                item['crawl_time'] = crawl_time
                
                self.completed_items += 1
                self.logger.info(f"关键词检查完成: {keyword}, 结果: {'存在' if exists else '不存在'}")
                
                yield item
                
            elif status == 10000:
                # 未登录
                self.logger.warning(f"Cookie无效或已过期，关键词: {keyword}")
                
                item = WordCheckItem()
                item['task_id'] = self.task_id
                item['keyword'] = keyword
                item['exists'] = False
                item['error'] = 'Cookie无效或已过期'
                item['crawl_time'] = crawl_time
                
                self.failed_items += 1
                yield item
                
            elif status == 10001:
                # 请求被锁定
                self.logger.warning(f"Cookie被临时锁定，关键词: {keyword}")
                
                item = WordCheckItem()
                item['task_id'] = self.task_id
                item['keyword'] = keyword
                item['exists'] = False
                item['error'] = 'Cookie被临时锁定'
                item['crawl_time'] = crawl_time
                
                self.failed_items += 1
                yield item
                
            else:
                # 其他状态码
                message = data.get('message', '未知错误')
                self.logger.error(f"检查关键词失败: {keyword}, 错误: {message}")
                
                item = WordCheckItem()
                item['task_id'] = self.task_id
                item['keyword'] = keyword
                item['exists'] = False
                item['error'] = message
                item['crawl_time'] = crawl_time
                
                self.failed_items += 1
                yield item
                
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析错误: {keyword}, 错误: {e}")
            
            item = WordCheckItem()
            item['task_id'] = self.task_id
            item['keyword'] = keyword
            item['exists'] = False
            item['error'] = f'JSON解析错误: {str(e)}'
            item['crawl_time'] = crawl_time
            
            self.failed_items += 1
            yield item
            
        except Exception as e:
            self.logger.error(f"处理关键词时出错: {keyword}, 错误: {e}")
            
            item = WordCheckItem()
            item['task_id'] = self.task_id
            item['keyword'] = keyword
            item['exists'] = False
            item['error'] = str(e)
            item['crawl_time'] = crawl_time
            
            self.failed_items += 1
            yield item