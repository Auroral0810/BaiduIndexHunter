-- MySQL dump 10.13  Distrib 8.0.36, for macos14 (arm64)
--
-- Host: 127.0.0.1    Database: BaiduIndexHunter
-- ------------------------------------------------------
-- Server version	8.0.36

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `cookies`
--

DROP TABLE IF EXISTS `cookies`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cookies` (
  `id` int NOT NULL AUTO_INCREMENT,
  `account_id` varchar(50) NOT NULL,
  `cookie_name` varchar(255) NOT NULL,
  `cookie_value` text NOT NULL,
  `last_updated` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `expire_time` timestamp NULL DEFAULT NULL,
  `is_available` tinyint(1) DEFAULT '1' COMMENT '是否可用，1表示可用，0表示不可用',
  `is_permanently_banned` tinyint(1) DEFAULT '0' COMMENT '是否永久封禁，1表示永久封禁，0表示未封禁',
  `temp_ban_until` timestamp NULL DEFAULT NULL COMMENT '临时封禁到期时间，为NULL表示未临时封禁',
  PRIMARY KEY (`id`),
  KEY `idx_account_id` (`account_id`),
  KEY `idx_cookie_status` (`is_available`,`is_permanently_banned`,`temp_ban_until`)
) ENGINE=InnoDB AUTO_INCREMENT=1977 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `prefecture_city`
--

DROP TABLE IF EXISTS `prefecture_city`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `prefecture_city` (
  `id` int NOT NULL AUTO_INCREMENT,
  `city_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '地级市代码',
  `city_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '地级市名称',
  `province_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '所属省份代码',
  `province_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '所属省份名称',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `city_code` (`city_code`),
  KEY `idx_city_code` (`city_code`),
  KEY `idx_province_code` (`province_code`)
) ENGINE=InnoDB AUTO_INCREMENT=370 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='地级市表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `province_region`
--

DROP TABLE IF EXISTS `province_region`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `province_region` (
  `id` int NOT NULL AUTO_INCREMENT,
  `province_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '省份代码',
  `province_name` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '省份名称',
  `region_name` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '所属大区（华东、华北等）',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `province_code` (`province_code`),
  KEY `idx_province_code` (`province_code`),
  KEY `idx_region_name` (`region_name`)
) ENGINE=InnoDB AUTO_INCREMENT=35 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='省份大区对应表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `region_children`
--

DROP TABLE IF EXISTS `region_children`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `region_children` (
  `id` int NOT NULL AUTO_INCREMENT,
  `parent_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '父级区域代码',
  `child_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '子级区域代码',
  `sort_order` int DEFAULT '0' COMMENT '排序序号',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_parent_child` (`parent_code`,`child_code`),
  KEY `idx_parent_code` (`parent_code`),
  KEY `idx_child_code` (`child_code`)
) ENGINE=InnoDB AUTO_INCREMENT=3375 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='区域父子关系表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `region_hierarchy`
--

DROP TABLE IF EXISTS `region_hierarchy`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `region_hierarchy` (
  `id` int NOT NULL AUTO_INCREMENT,
  `region_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '区域代码',
  `region_name` varchar(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '区域名称',
  `layer_level` int NOT NULL COMMENT '层级：1-省级，2-地级市，3-区县级，4-更细分级',
  `parent_code` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT '父级区域代码',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `region_code` (`region_code`),
  KEY `idx_region_code` (`region_code`),
  KEY `idx_parent_code` (`parent_code`),
  KEY `idx_layer_level` (`layer_level`),
  CONSTRAINT `region_hierarchy_ibfk_1` FOREIGN KEY (`parent_code`) REFERENCES `region_hierarchy` (`region_code`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=3377 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='区域层级表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `spider_statistics`
--

DROP TABLE IF EXISTS `spider_statistics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `spider_statistics` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '统计ID',
  `stat_date` date NOT NULL COMMENT '统计日期',
  `task_type` varchar(50) NOT NULL COMMENT '任务类型',
  `total_tasks` int DEFAULT '0' COMMENT '总任务数',
  `completed_tasks` int DEFAULT '0' COMMENT '完成任务数',
  `failed_tasks` int DEFAULT '0' COMMENT '失败任务数',
  `total_items` int DEFAULT '0' COMMENT '总数据项',
  `total_crawled_items` bigint DEFAULT '0' COMMENT '累计爬取数据条数',
  `success_rate` float DEFAULT '0' COMMENT '成功率',
  `avg_duration` float DEFAULT '0' COMMENT '平均执行时间(秒)',
  `cookie_usage` int DEFAULT '0' COMMENT 'Cookie使用次数',
  `cookie_ban_count` int DEFAULT '0' COMMENT 'Cookie封禁次数',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_date_type` (`stat_date`,`task_type`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='爬虫统计汇总表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `spider_tasks`
--

DROP TABLE IF EXISTS `spider_tasks`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `spider_tasks` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '任务ID',
  `task_id` varchar(32) NOT NULL COMMENT '任务唯一标识符',
  `task_name` varchar(255) DEFAULT NULL COMMENT '任务名称',
  `task_type` varchar(50) NOT NULL COMMENT '任务类型(search_index/feed_index/word_graph/demographic_attributes/interest_profile/region_distribution)',
  `status` varchar(20) NOT NULL DEFAULT 'pending' COMMENT '任务状态(pending/running/paused/completed/failed)',
  `parameters` text COMMENT '任务参数(JSON格式)',
  `progress` float DEFAULT '0' COMMENT '任务进度(0-100)',
  `total_items` int DEFAULT '0' COMMENT '总项目数',
  `completed_items` int DEFAULT '0' COMMENT '已完成项目数',
  `failed_items` int DEFAULT '0' COMMENT '失败项目数',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `start_time` datetime DEFAULT NULL COMMENT '开始执行时间',
  `update_time` datetime DEFAULT NULL COMMENT '最后更新时间',
  `end_time` datetime DEFAULT NULL COMMENT '结束时间',
  `error_message` text COMMENT '错误信息',
  `checkpoint_path` mediumtext COMMENT '检查点数据(JSON格式)',
  `output_files` text COMMENT '输出文件路径(JSON格式)',
  `created_by` varchar(50) DEFAULT NULL COMMENT '创建者',
  `priority` int DEFAULT '5' COMMENT '任务优先级(1-10，数字越大优先级越高)',
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_id` (`task_id`),
  KEY `idx_task_type` (`task_type`),
  KEY `idx_status` (`status`),
  KEY `idx_create_time` (`create_time`)
) ENGINE=InnoDB AUTO_INCREMENT=138 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='爬虫任务表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `system_config`
--

DROP TABLE IF EXISTS `system_config`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `system_config` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '配置ID',
  `config_key` varchar(50) NOT NULL COMMENT '配置键',
  `config_value` text COMMENT '配置值',
  `description` varchar(255) DEFAULT NULL COMMENT '描述',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `config_key` (`config_key`)
) ENGINE=InnoDB AUTO_INCREMENT=747 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='系统配置表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `task_logs`
--

DROP TABLE IF EXISTS `task_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `task_logs` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '日志ID',
  `task_id` varchar(32) NOT NULL COMMENT '关联的任务ID',
  `log_level` varchar(10) NOT NULL COMMENT '日志级别(info/warning/error/debug)',
  `message` text NOT NULL COMMENT '日志消息',
  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '记录时间',
  `details` text COMMENT '详细信息(JSON格式)',
  PRIMARY KEY (`id`),
  KEY `idx_task_id` (`task_id`),
  KEY `idx_timestamp` (`timestamp`),
  KEY `idx_log_level` (`log_level`)
) ENGINE=InnoDB AUTO_INCREMENT=255 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='任务日志表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `task_queue`
--

DROP TABLE IF EXISTS `task_queue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `task_queue` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '队列ID',
  `task_id` varchar(32) NOT NULL COMMENT '关联的任务ID',
  `priority` int DEFAULT '0' COMMENT '优先级(数字越大优先级越高)',
  `status` varchar(20) NOT NULL DEFAULT 'waiting' COMMENT '状态(waiting/processing/completed/failed)',
  `worker_id` varchar(50) DEFAULT NULL COMMENT '处理该任务的工作节点ID',
  `enqueue_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '入队时间',
  `start_time` datetime DEFAULT NULL COMMENT '开始处理时间',
  `complete_time` datetime DEFAULT NULL COMMENT '完成时间',
  `retry_count` int DEFAULT '0' COMMENT '重试次数',
  `max_retries` int DEFAULT '3' COMMENT '最大重试次数',
  `next_retry_time` datetime DEFAULT NULL COMMENT '下次重试时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `task_id` (`task_id`),
  KEY `idx_status` (`status`),
  KEY `idx_priority` (`priority`),
  KEY `idx_worker_id` (`worker_id`)
) ENGINE=InnoDB AUTO_INCREMENT=94 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='任务队列表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `task_statistics`
--

DROP TABLE IF EXISTS `task_statistics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `task_statistics` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '统计ID',
  `task_id` varchar(32) NOT NULL COMMENT '关联的任务ID',
  `keyword` varchar(255) DEFAULT NULL COMMENT '关键词',
  `city_code` varchar(50) DEFAULT NULL COMMENT '城市代码',
  `date_range` varchar(50) DEFAULT NULL COMMENT '日期范围',
  `data_type` varchar(50) DEFAULT NULL COMMENT '数据类型',
  `item_count` int DEFAULT '0' COMMENT '数据项数量',
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='任务统计表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary view structure for view `v_region_full_info`
--

DROP TABLE IF EXISTS `v_region_full_info`;
/*!50001 DROP VIEW IF EXISTS `v_region_full_info`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_region_full_info` AS SELECT 
 1 AS `region_code`,
 1 AS `region_name`,
 1 AS `layer_level`,
 1 AS `parent_code`,
 1 AS `parent_name`,
 1 AS `province_region`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_region_with_children`
--

DROP TABLE IF EXISTS `v_region_with_children`;
/*!50001 DROP VIEW IF EXISTS `v_region_with_children`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_region_with_children` AS SELECT 
 1 AS `parent_code`,
 1 AS `parent_name`,
 1 AS `child_code`,
 1 AS `child_name`,
 1 AS `child_level`,
 1 AS `sort_order`*/;
SET character_set_client = @saved_cs_client;

--
-- Final view structure for view `v_region_full_info`
--

/*!50001 DROP VIEW IF EXISTS `v_region_full_info`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_region_full_info` AS select `rh`.`region_code` AS `region_code`,`rh`.`region_name` AS `region_name`,`rh`.`layer_level` AS `layer_level`,`rh`.`parent_code` AS `parent_code`,`parent`.`region_name` AS `parent_name`,`pr`.`region_name` AS `province_region` from ((`region_hierarchy` `rh` left join `region_hierarchy` `parent` on((`rh`.`parent_code` = `parent`.`region_code`))) left join `province_region` `pr` on((`rh`.`region_code` = `pr`.`province_code`))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_region_with_children`
--

/*!50001 DROP VIEW IF EXISTS `v_region_with_children`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_0900_ai_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_region_with_children` AS select `rc`.`parent_code` AS `parent_code`,`parent`.`region_name` AS `parent_name`,`rc`.`child_code` AS `child_code`,`child`.`region_name` AS `child_name`,`child`.`layer_level` AS `child_level`,`rc`.`sort_order` AS `sort_order` from ((`region_children` `rc` join `region_hierarchy` `parent` on((`rc`.`parent_code` = `parent`.`region_code`))) join `region_hierarchy` `child` on((`rc`.`child_code` = `child`.`region_code`))) order by `rc`.`parent_code`,`rc`.`sort_order` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

-- 创建cookie每日用量表
CREATE TABLE `cookie_daily_usage` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `account_id` varchar(64) NOT NULL COMMENT 'Cookie账号ID',
  `usage_date` date NOT NULL COMMENT '使用日期',
  `usage_count` int(11) NOT NULL DEFAULT '0' COMMENT '当日使用次数',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `idx_account_date` (`account_id`,`usage_date`),
  KEY `idx_usage_date` (`usage_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='Cookie每日使用量统计';

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-07-04  3:26:57
