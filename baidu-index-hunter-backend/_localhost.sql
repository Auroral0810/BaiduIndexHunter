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
) ENGINE=InnoDB AUTO_INCREMENT=1847 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `city_code` (`city_code`),
  KEY `idx_city_code` (`city_code`)
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



CREATE EVENT reset_daily
ON SCHEDULE EVERY 1 DAY STARTS TIMESTAMP(CURRENT_DATE) + INTERVAL 1 DAY
DO
  UPDATE cookies
  SET is_available = 1,
      temp_ban_until = NULL
  WHERE is_permanently_banned = 0;


CREATE EVENT check_temp_ban
ON SCHEDULE EVERY 10 MINUTE
DO
  UPDATE cookies
  SET is_available = 1,
      temp_ban_until = NULL
  WHERE temp_ban_until < CURRENT_TIMESTAMP
    AND is_available = 0;
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
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-07-01 20:47:06
