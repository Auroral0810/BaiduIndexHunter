# 百度指数爬虫 - 资讯指数模块

## 功能介绍

资讯指数爬虫模块用于抓取百度资讯指数的相关数据，包括日度数据、周度数据以及统计数据。资讯指数反映了特定关键词在百度资讯平台上的热度变化趋势。

## 主要特点

1. **统一数据存储**：所有爬取的数据存储在单个文件中，便于后续分析处理。
2. **检查点管理**：支持任务中断后的恢复功能，避免重复爬取。
3. **自动保存**：每爬取100条数据自动保存一次，防止数据丢失。
4. **中断处理**：能够优雅地处理用户中断和程序崩溃，确保数据和进度不丢失。
5. **多种输入方式**：支持直接传入关键词列表、从文件加载关键词等多种方式。
6. **灵活的时间设置**：支持预定义天数（7天、30天、90天、180天）、自定义日期范围、年份范围等多种时间设置。
7. **多城市支持**：支持爬取全国和各个城市的数据。
8. **Cookie管理**：从MySQL和Redis获取Cookie，实现负载均衡和状态管理。

## 安装依赖

确保已安装以下Python包：

```bash
pip install pandas requests fake_useragent python-dotenv
```

## 基本用法

### 示例1：爬取单个关键词最近30天的资讯指数

```python
from spider.feed_index_crawler import feed_index_crawler

# 爬取单个关键词的资讯指数（默认最近30天，全国范围）
feed_index_crawler.crawl(keywords=["电脑"])
```

### 示例2：爬取多个关键词的资讯指数

```python
# 爬取多个关键词的资讯指数
feed_index_crawler.crawl(keywords=["电脑", "手机", "平板"])
```

### 示例3：爬取指定日期范围的资讯指数

```python
# 爬取指定日期范围的资讯指数
date_ranges = [
    ("2023-01-01", "2023-12-31"),
    ("2024-01-01", "2024-06-30")
]
feed_index_crawler.crawl(keywords=["电脑"], date_ranges=date_ranges)
```

### 示例4：爬取指定城市的资讯指数

```python
# 爬取指定城市的资讯指数
cities = {
    0: "全国",
    1: "济南",
    77: "青岛",
    514: "北京",
    57: "上海"
}
feed_index_crawler.crawl(keywords=["电脑"], cities=cities)
```

### 示例5：爬取多个年份的资讯指数

```python
# 爬取多个年份的资讯指数
feed_index_crawler.crawl(keywords=["电脑"], year_range=(2022, 2023))
```

### 示例6：爬取最近90天的资讯指数

```python
# 爬取最近90天的资讯指数
feed_index_crawler.crawl(keywords=["电脑"], days=90)
```

### 示例7：恢复之前中断的任务

```python
# 恢复之前中断的任务
task_id = "20240101123456"  # 格式为YYYYMMDDHHmmss
feed_index_crawler.resume_task(task_id)
```

### 示例8：列出所有任务及其状态

```python
# 列出所有任务及其状态
tasks = feed_index_crawler.list_tasks()
for task in tasks:
    print(f"任务ID: {task['task_id']}, 进度: {task['progress']}")
```

### 示例9：从文件加载关键词和城市

```python
# 从文件加载关键词和城市
feed_index_crawler.crawl(
    keywords_file="data/keywords.xlsx",
    cities_file="data/cities.xlsx"
)
```

### 示例10：综合示例

```python
# 综合示例
cities = {
    0: "全国",
    514: "北京",
    57: "上海"
}
date_ranges = [
    ("2023-01-01", "2023-06-30"),
    ("2023-07-01", "2023-12-31")
]
feed_index_crawler.crawl(
    keywords=["电脑", "手机", "平板"],
    cities=cities,
    date_ranges=date_ranges
)
```

## 输出文件

爬虫会生成两个主要的输出文件：

1. **日度/周度数据文件**：`{task_id}_daily_data.csv`
   - 包含关键词、城市、日期、资讯指数等详细数据
   - 字段：关键词、城市、城市代码、日期、数据类型、数据间隔(天)、所属年份、资讯指数、爬取时间

2. **统计数据文件**：`{task_id}_stats_data.csv`
   - 包含关键词在特定城市和时间范围内的统计数据
   - 字段：关键词、城市、城市代码、时间范围、资讯日均值、资讯同比、资讯环比、资讯总值、爬取时间

3. **检查点文件**：`checkpoints/feed_index_{task_id}_checkpoint.pkl`
   - 保存任务的进度信息，用于恢复中断的任务

## 注意事项

1. **Cookie锁定**：如果返回状态码为10001，表示Cookie被临时锁定，系统会自动将该Cookie锁定30分钟。
2. **Cookie无效**：如果返回状态码为10000，表示Cookie无效或已过期，系统会永久锁定该Cookie。
3. **所有Cookie锁定**：如果所有Cookie都被锁定，爬虫会暂停30分钟，并显示进度条，等待Cookie可用后自动恢复。
4. **爬取频率**：为避免IP被封，系统设置了请求间隔，默认为1.8-2秒/次。
5. **数据保存**：每爬取100条数据会自动保存一次，程序中断时也会保存当前数据和进度。

## 高级配置

可以在`config/settings.py`文件中调整以下参数：

- `COOKIE_BLOCK_COOLDOWN`: Cookie被锁定后的冷却时间（秒）
- `SPIDER_CONFIG.min_interval`: 请求最小间隔时间（秒）
- `SPIDER_CONFIG.max_workers`: 最大工作线程数
- `OUTPUT_DIR`: 输出目录路径

## 文件格式要求

### 关键词文件格式

支持以下格式的关键词文件：

1. **Excel文件 (.xlsx)**：
   - 第一列应包含关键词列表
   - 不需要表头，直接从第一行开始填写关键词

2. **CSV文件 (.csv)**：
   - 第一列应包含关键词列表
   - 不需要表头，直接从第一行开始填写关键词

3. **文本文件 (.txt)**：
   - 每行一个关键词

### 城市文件格式

支持以下格式的城市文件：

1. **Excel文件 (.xlsx)**：
   - 第一列：城市代码（整数）
   - 第二列：城市名称（字符串）

2. **CSV文件 (.csv)**：
   - 第一列：城市代码（整数）
   - 第二列：城市名称（字符串）

### 日期范围文件格式

支持以下格式的日期范围文件：

1. **Excel文件 (.xlsx)**：
   - 必须包含名为'start_date'和'end_date'的列
   - 日期格式为：YYYY-MM-DD

2. **CSV文件 (.csv)**：
   - 必须包含名为'start_date'和'end_date'的列
   - 日期格式为：YYYY-MM-DD

3. **文本文件 (.txt)**：
   - 每行一个日期范围
   - 格式为：start_date,end_date
   - 例如：2023-01-01,2023-12-31 