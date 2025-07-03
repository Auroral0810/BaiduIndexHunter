-- 添加累计爬取数据条数字段
ALTER TABLE spider_statistics ADD COLUMN IF NOT EXISTS total_crawled_items BIGINT DEFAULT 0 COMMENT '累计爬取数据条数' AFTER total_items;
