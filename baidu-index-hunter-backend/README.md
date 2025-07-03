## 更新日志

### 2023-12-25
- 添加了spider_statistics表的total_crawled_items字段，用于记录累计爬取的数据条数
- 优化了spider_statistics统计页面，添加了日期和任务类型的筛选功能
- 修复了task_queue表与spider_tasks表同步问题
- 改进了任务统计数据的计算逻辑，提高了统计准确性 