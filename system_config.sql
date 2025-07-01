-- 系统配置表
CREATE TABLE IF NOT EXISTS `system_config` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `config_key` varchar(100) NOT NULL COMMENT '配置键',
  `config_value` text COMMENT '配置值',
  `description` varchar(255) DEFAULT NULL COMMENT '配置描述',
  `create_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_config_key` (`config_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';

-- 插入API配置
INSERT INTO `system_config` (`config_key`, `config_value`, `description`) VALUES
('api.host', '0.0.0.0', '服务器监听的主机地址'),
('api.port', '5001', '服务器监听的端口'),
('api.debug', 'true', '是否启用调试模式'),
('api.cors_origins', '*', '允许的跨域来源');

-- 插入任务配置
INSERT INTO `system_config` (`config_key`, `config_value`, `description`) VALUES
('task.max_concurrent_tasks', '5', '最大并发任务数'),
('task.queue_check_interval', '10', '任务队列检查间隔（秒）'),
('task.default_priority', '5', '默认任务优先级（1-10）'),
('task.max_retry_count', '3', '任务最大重试次数'),
('task.retry_delay', '300', '任务重试延迟（秒）');

-- 插入爬虫配置
INSERT INTO `system_config` (`config_key`, `config_value`, `description`) VALUES
('spider.min_interval', '1.8', '请求间隔最小秒数'),
('spider.max_interval', '2.0', '请求间隔最大秒数'),
('spider.retry_times', '2', '请求失败重试次数'),
('spider.timeout', '15', '请求超时时间（秒）'),
('spider.max_workers', '10', '最大工作线程数'),
('spider.user_agent_rotation', 'true', '是否轮换User-Agent'),
('spider.proxy_enabled', 'false', '是否启用代理');

-- 插入Cookie配置
INSERT INTO `system_config` (`config_key`, `config_value`, `description`) VALUES
('cookie.min_available_count', '3', '最小可用Cookie数量'),
('cookie.block_cooldown', '1800', 'Cookie被锁后的冷却时间（秒）'),
('cookie.rotation_strategy', 'round_robin', 'Cookie轮换策略：round_robin, random, least_used'),
('cookie.max_usage_per_day', '1000', '每个Cookie每天最大使用次数');

-- 插入输出配置
INSERT INTO `system_config` (`config_key`, `config_value`, `description`) VALUES
('output.default_format', 'csv', '默认输出格式：csv, excel'),
('output.csv_encoding', 'utf-8-sig', 'CSV文件编码'),
('output.excel_sheet_name', 'BaiduIndex', 'Excel工作表名称');

-- 插入日志配置
INSERT INTO `system_config` (`config_key`, `config_value`, `description`) VALUES
('log.level', 'INFO', '日志级别'),
('log.retention', '7', '日志保留天数'),
('log.format', '%(asctime)s - %(levelname)s - %(name)s - %(message)s', '日志格式'),
('log.file_size', '10485760', '单个日志文件大小限制，默认10MB'),
('log.backup_count', '5', '日志文件备份数量');

-- 插入UI配置
INSERT INTO `system_config` (`config_key`, `config_value`, `description`) VALUES
('ui.theme', 'light', 'UI主题：light, dark'),
('ui.language', 'zh_CN', 'UI语言'),
('ui.items_per_page', '10', '每页显示的项目数'),
('ui.auto_refresh', 'true', '是否自动刷新数据'),
('ui.refresh_interval', '30', '自动刷新间隔（秒）');

-- 插入系统配置
INSERT INTO `system_config` (`config_key`, `config_value`, `description`) VALUES
('system.version', '1.0.0', '系统版本'),
('system.name', '百度指数爬虫', '系统名称'),
('system.admin_email', 'admin@example.com', '管理员邮箱'),
('system.maintenance_mode', 'false', '是否处于维护模式');
