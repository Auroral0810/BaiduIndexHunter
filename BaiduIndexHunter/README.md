# 百度指数爬虫项目 (BaiduIndexHunter)

## 项目简介

BaiduIndexHunter 是一个专门用于爬取百度指数数据的项目，提供了完善的 Cookie 池管理功能。项目特点包括：

- 自动登录获取新 Cookie
- 定期检测 Cookie 有效性
- 智能轮换分配 Cookie
- Cookie 失效监控告警

## 技术架构

- **后端语言**: Python 3.8+
- **数据库**: MySQL (存储 Cookie 基础信息)
- **缓存**: Redis (存储活跃 Cookie)
- **定时任务**: APScheduler
- **日志管理**: Loguru

## 模块说明

### 配置模块 (config)

- **settings.py**: 全局配置文件，包含数据库连接、Redis缓存、任务调度和百度指数 API 等配置

### 数据库模块 (db)

- **mysql_manager.py**: MySQL 数据库管理器，负责 Cookie 的持久化存储和查询
- **redis_manager.py**: Redis 缓存管理器，用于缓存活跃 Cookie 并记录使用情况

### Cookie 管理模块 (cookie_manager)

- **cookie_validator.py**: Cookie 验证器，检测百度指数 Cookie 是否有效
- **cookie_rotator.py**: Cookie 轮换器，根据使用频率和成功率智能分配 Cookie
- **health_checker.py**: Cookie 健康检查器，定期检查所有 Cookie 的有效性

### 爬虫模块 (spider)

- **baidu_index_api.py**: 百度指数 API 封装，提供搜索指数和趋势数据获取接口

### 调度模块 (scheduler)

- **task_scheduler.py**: 任务调度器，管理 Cookie 更新、健康检查等定时任务

### 工具模块 (utils)

- **logger.py**: 日志工具，统一日志格式和输出

## 安装与配置

### 环境要求

- Python 3.8+
- MySQL 5.7+
- Redis 5.0+

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置文件

项目使用 `.env` 文件进行配置，主要包含：

- 数据库连接信息
- Redis 连接信息
- 任务调度间隔
- 日志级别

## 使用方法

### 初始化数据库

项目使用以下数据库结构：

```sql
CREATE DATABASE cookie_pool;
USE cookie_pool;

CREATE TABLE cookies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL,
    cookie_name VARCHAR(255) NOT NULL,
    cookie_value TEXT NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    expire_time TIMESTAMP NULL,
    is_available BOOLEAN DEFAULT TRUE
);
```

### 启动项目

```bash
python main.py
```

## 开发计划

- [ ] 添加前端管理界面
- [ ] 支持多种验证码识别
- [ ] 添加更多数据源支持
- [ ] 完善监控告警机制
