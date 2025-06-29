# 百度指数爬虫 - 搜索指数模块

## 功能介绍

搜索指数爬虫模块是百度指数爬虫系统的核心组件之一，用于抓取百度搜索指数的各类数据，包括：

1. **日度数据**：每天的搜索指数变化
2. **周度数据**：每周的搜索指数变化（当时间跨度较大时）
3. **统计数据**：包括整体日均值、移动日均值、整体同比、整体环比、移动同比、移动环比等

## 主要特点

- **统一数据存储**：所有爬取的数据保存在以任务ID命名的单一文件中
- **检查点管理**：支持断点续爬，可以从上次中断的位置继续爬取
- **自动保存**：每爬取100条记录自动保存一次，防止数据丢失
- **中断处理**：优雅处理用户中断和程序崩溃，自动保存当前进度
- **多种输入方式**：支持直接输入关键词列表、从文件加载关键词等多种方式
- **灵活的时间设置**：支持预定义天数（7/30/90/180天）或自定义日期范围
- **多城市支持**：可以指定爬取全国或特定城市的数据
- **Cookie管理**：从MySQL和Redis获取Cookie，自动处理Cookie锁定情况

## 安装依赖

```bash
pip install pandas requests fake_useragent python-dotenv
```

## 基本用法

### 示例1：爬取单个关键词的最近30天数据

```python
from spider.search_index_crawler import search_index_crawler

keywords = ["电脑"]
search_index_crawler.crawl(keywords=keywords)
```

### 示例2：爬取多个关键词的数据

```python
keywords = ["电脑", "手机", "平板"]
search_index_crawler.crawl(keywords=keywords)
```

### 示例3：自定义日期范围

```python
keywords = ["电脑"]
date_ranges = [("2023-01-01", "2023-12-31")]
search_index_crawler.crawl(keywords=keywords, date_ranges=date_ranges)
```

### 示例4：多城市数据

```python
keywords = ["电脑"]
cities = {0: "全国", 514: "北京", 57: "上海", 95: "广州", 94: "深圳"}
search_index_crawler.crawl(keywords=keywords, cities=cities)
```

### 示例5：按年份范围爬取

```python
keywords = ["电脑"]
year_range = (2022, 2023)  # 爬取2022年到2023年的数据
search_index_crawler.crawl(keywords=keywords, year_range=year_range)
```

### 示例6：使用预定义天数

```python
keywords = ["电脑"]
days = 90  # 爬取最近90天的数据
search_index_crawler.crawl(keywords=keywords, days=days)
```

### 示例7：恢复中断的任务

```python
task_id = "20240101123456"  # 替换为实际的任务ID
search_index_crawler.resume_task(task_id)
```

### 示例8：列出所有任务及其状态

```python
tasks = search_index_crawler.list_tasks()
for task in tasks:
    print(f"任务ID: {task['task_id']}, 进度: {task['progress']}")
```

### 示例9：从文件加载关键词和城市

```python
search_index_crawler.crawl(
    keywords_file="data/keywords.txt",
    cities_file="data/cities.csv",
    days=30
)
```

### 示例10：综合示例

```python
keywords = ["电脑", "手机", "平板"]
cities = {0: "全国", 514: "北京", 57: "上海"}
date_ranges = [
    ("2023-01-01", "2023-06-30"),
    ("2023-07-01", "2023-12-31")
]
search_index_crawler.crawl(
    keywords=keywords,
    cities=cities,
    date_ranges=date_ranges
)
```

## 输出文件

爬虫会在 `output/search_index` 目录下生成两类文件：

1. **{task_id}_daily_data.csv**：包含日度/周度搜索指数数据
2. **{task_id}_stats_data.csv**：包含统计数据（日均值、同比、环比等）

检查点文件保存在 `output/checkpoints/{task_id}_checkpoint.pkl`

## 注意事项

1. 当所有Cookie被锁定时，程序会等待30分钟后重试
2. 爬取大量数据时请注意控制速率，避免IP被封
3. 任务ID格式为YYYYMMDDHHmmss，可用于恢复特定任务

## 高级配置

可以在 `config/settings.py` 中调整以下参数：

- `SPIDER_CONFIG['min_interval']`：请求间隔最小秒数
- `SPIDER_CONFIG['max_interval']`：请求间隔最大秒数
- `SPIDER_CONFIG['retry_times']`：请求失败重试次数
- `SPIDER_CONFIG['timeout']`：请求超时时间
- `COOKIE_BLOCK_COOLDOWN`：Cookie被锁后的冷却时间
