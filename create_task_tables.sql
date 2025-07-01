-- 爬虫任务表
CREATE TABLE `spider_tasks` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '任务ID',
  `task_id` varchar(32) NOT NULL COMMENT '任务唯一标识符',
  `task_name` varchar(255) DEFAULT NULL COMMENT '任务名称',
  `task_type` varchar(50) NOT NULL COMMENT '任务类型(search_index/feed_index/word_graph/demographic_attributes/interest_profile/region_distribution)',
  `status` varchar(20) NOT NULL DEFAULT 'pending' COMMENT '任务状态(pending/running/paused/completed/failed)',
  `parameters` text COMMENT '任务参数(JSON格式)',
  `progress` float DEFAULT '0' COMMENT '任务进度(0-100)',
  `total_items` int(11) DEFAULT '0' COMMENT '总项目数',
  `completed_items` int(11) DEFAULT '0' COMMENT '已完成项目数',
  `failed_items` int(11) DEFAULT '0' COMMENT '失败项目数',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `start_time` datetime DEFAULT NULL COMMENT '开始执行时间',
  `update_time` datetime DEFAULT NULL COMMENT '最后更新时间',
  `end_time` datetime DEFAULT NULL COMMENT '结束时间',
  `error_message` text COMMENT '错误信息',
  `checkpoint_data` mediumtext COMMENT '检查点数据(JSON格式)',
  `output_files` text COMMENT '输出文件路径(JSON格式)',
  `created_by` varchar(50) DEFAULT NULL COMMENT '创建者',
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_id` (`task_id`),
  KEY `idx_task_type` (`task_type`),
  KEY `idx_status` (`status`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='爬虫任务表';

-- 任务日志表
CREATE TABLE `task_logs` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `task_id` varchar(32) NOT NULL COMMENT '关联的任务ID',
  `log_level` varchar(10) NOT NULL COMMENT '日志级别(info/warning/error/debug)',
  `message` text NOT NULL COMMENT '日志消息',
  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
  `details` text COMMENT '详细信息(JSON格式)',
  PRIMARY KEY (`id`),
  KEY `idx_task_id` (`task_id`),
  KEY `idx_timestamp` (`timestamp`),
  KEY `idx_log_level` (`log_level`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务日志表';

-- 任务统计表
CREATE TABLE `task_statistics` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '统计ID',
  `task_id` varchar(32) NOT NULL COMMENT '关联的任务ID',
  `keyword` varchar(255) DEFAULT NULL COMMENT '关键词',
  `city_code` varchar(50) DEFAULT NULL COMMENT '城市代码',
  `date_range` varchar(50) DEFAULT NULL COMMENT '日期范围',
  `data_type` varchar(50) DEFAULT NULL COMMENT '数据类型',
  `item_count` int(11) DEFAULT '0' COMMENT '数据项数量',
  `avg_value` float DEFAULT NULL COMMENT '平均值',
  `max_value` float DEFAULT NULL COMMENT '最大值',
  `min_value` float DEFAULT NULL COMMENT '最小值',
  `sum_value` float DEFAULT NULL COMMENT '总和',
  `extra_data` text COMMENT '额外数据(JSON格式)',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_task_id` (`task_id`),
  KEY `idx_keyword` (`keyword`),
  KEY `idx_city_code` (`city_code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务统计表';

-- 任务队列表
CREATE TABLE `task_queue` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '队列ID',
  `task_id` varchar(32) NOT NULL COMMENT '关联的任务ID',
  `priority` int(11) DEFAULT '0' COMMENT '优先级(数字越大优先级越高)',
  `status` varchar(20) NOT NULL DEFAULT 'waiting' COMMENT '状态(waiting/processing/completed/failed)',
  `worker_id` varchar(50) DEFAULT NULL COMMENT '处理该任务的工作节点ID',
  `enqueue_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入队时间',
  `start_time` datetime DEFAULT NULL COMMENT '开始处理时间',
  `complete_time` datetime DEFAULT NULL COMMENT '完成时间',
  `retry_count` int(11) DEFAULT '0' COMMENT '重试次数',
  `max_retries` int(11) DEFAULT '3' COMMENT '最大重试次数',
  `next_retry_time` datetime DEFAULT NULL COMMENT '下次重试时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_id` (`task_id`),
  KEY `idx_status` (`status`),
  KEY `idx_priority` (`priority`),
  KEY `idx_worker_id` (`worker_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务队列表';

-- 爬虫系统配置表
CREATE TABLE `system_config` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '配置ID',
  `config_key` varchar(50) NOT NULL COMMENT '配置键',
  `config_value` text COMMENT '配置值',
  `description` varchar(255) DEFAULT NULL COMMENT '描述',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `config_key` (`config_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';

-- 爬虫统计汇总表
CREATE TABLE `spider_statistics` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '统计ID',
  `stat_date` date NOT NULL COMMENT '统计日期',
  `task_type` varchar(50) NOT NULL COMMENT '任务类型',
  `total_tasks` int(11) DEFAULT '0' COMMENT '总任务数',
  `completed_tasks` int(11) DEFAULT '0' COMMENT '完成任务数',
  `failed_tasks` int(11) DEFAULT '0' COMMENT '失败任务数',
  `total_items` int(11) DEFAULT '0' COMMENT '总数据项',
  `success_rate` float DEFAULT '0' COMMENT '成功率',
  `avg_duration` float DEFAULT '0' COMMENT '平均执行时间(秒)',
  `cookie_usage` int(11) DEFAULT '0' COMMENT 'Cookie使用次数',
  `cookie_ban_count` int(11) DEFAULT '0' COMMENT 'Cookie封禁次数',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_date_type` (`stat_date`,`task_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='爬虫统计汇总表'; 