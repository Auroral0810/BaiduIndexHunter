<p align="center">
  <img src="static/github-header-banner-zh.png" alt="BaiduIndexHunter Banner" style="border:none;box-shadow:none;outline:none;width:100%;max-width:900px;" />
</p>
<p align="center">
  <a href="./README.md">中文文档</a> | <a href="./README_EN.md">English</a>
</p>
<p align="center">
  <!-- 技术栈、版本、License、PR、Fork、Watch、Star、Issue、Last Commit —— 所有徽章聚合到同一行 -->
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/Vue.js-3.4-4FC08D?style=flat-square&logo=vue.js&logoColor=white" alt="Vue.js" />
  <img src="https://img.shields.io/badge/Flask-3.1-000000?style=flat-square&logo=flask&logoColor=white" alt="Flask" />
  <img src="https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat-square&logo=mysql&logoColor=white" alt="MySQL" />
  <img src="https://img.shields.io/badge/Redis-7.x-DC382D?style=flat-square&logo=redis&logoColor=white" alt="Redis" />
  <img src="https://img.shields.io/badge/version-2.0.0-blue?style=flat-square" alt="Version" />
  <img src="https://img.shields.io/badge/license-Custom%20@LICENSE-blue?style=flat-square" alt="License" />
  <img src="https://img.shields.io/github/issues-pr/Auroral0810/BaiduIndexHunter?style=flat-square" alt="Pull Requests" />
  <img src="https://img.shields.io/github/forks/Auroral0810/BaiduIndexHunter?style=flat-square" alt="GitHub Forks" />
  <img src="https://img.shields.io/github/watchers/Auroral0810/BaiduIndexHunter?style=flat-square" alt="Watchers" />
  <img src="https://img.shields.io/github/stars/Auroral0810/BaiduIndexHunter?style=flat-square" alt="GitHub Stars" />
  <img src="https://img.shields.io/github/issues/Auroral0810/BaiduIndexHunter?style=flat-square" alt="Issues" />
  <img src="https://img.shields.io/github/last-commit/Auroral0810/BaiduIndexHunter?style=flat-square" alt="Last Commit" />
</p>

---

> [!IMPORTANT]
> 
> 本项目**仅供学习与技术交流**，<span style="color: #e53935; font-weight:600;">严禁将本项目用于任何商业用途或非法行为！</span>  
> 
> 1. 使用者需遵守所属国家和地区的法律法规，**因违反政策、法规或他人权益而导致的任何后果，由使用者自行承担全部责任**。
> 2. 作者对由此项目引发的任何直接或间接损失、法律责任与风险不承担任何法律责任。
> 3. 若对免责声明条款有疑问或无法接受，请立即停止下载和使用本项目。
> 4. 本项目源码及其衍生内容，请勿在未获授权情况下转载或发布于其他平台。

---
## ⚡️ 项目概述

**BaiduIndexHunter 2.0** 是一套面向百度指数数据的采集、存储与可视化平台，采用前后端分离架构，基于 **Flask + Vue 3 + Element Plus** 构建。系统支持**搜索指数**、**资讯指数**、**需求图谱**、**人群属性**、**兴趣分布**、**地域分布** 六大维度数据采集，集成任务调度、Cookie 轮换、断点续爬、实时进度推送与数据大屏等核心能力。

项目面向学术研究、市场分析与舆情监测等场景，支持批量关键词与多地域采集、多格式导出（CSV / Excel / Parquet 等），并内置 API 鉴权、环境校验等安全机制，适用于单机或小规模团队部署使用。

---

## 📺 演示视频

<p align="center">
  <video src="https://private-user-images.githubusercontent.com/140379943/546603232-70b973f0-141f-4dd8-a4ea-fa026048a263.mp4" controls autoplay muted loop width="95%" poster="static/首页-门面.png">
    您的浏览器不支持 HTML5 视频播放，请 <a href="static/github演示视频.mp4">点击此处下载</a> 观看。
  </video>
</p>

---

## ✨ 功能特性

<div align="center">

| 核心能力             | 详细描述                                                                                                    |
| :------------------- | :--------------------------------------------------------------------------------------------------------- |
| 六大模块全覆盖       | 深度集成搜索指数、资讯指数、需求图谱、人群属性、兴趣分布、地域分布六大数据接口。                              |
| 实时状态监控         | 基于 WebSocket 技术，秒级同步采集进度与系统日志，实时监控项目运行状态。                                       |
| 高效并发采集         | 采用分布式消息队列设计，支持多任务同时运行，高效应对海量关键词采集场景。                                      |
| 智能账号池           | 内置账号状态自动巡检机制，支持 Cookie 自动轮换，封禁预警和用量可视化统计。                                   |
| 任务断点续存         | 支持任务检查点（Checkpoint）机制，意外中断后可一键恢复，杜绝重复流量消耗。                                    |
| 结构化数据导出       | 采集结果自动清洗为 CSV / Excel / Parquet / dta / json 等六种主流数据结构，并支持结构化数据库存储。            |
| 多语言与国际化       | 完整支持九种语言界面切换，满足多语种全球用户的需求。                                                        |
| 深色模式支持         | 适配现代 IDE 审美，支持 Dark Mode 一键切换，保护长时间工作下的视觉体验。                                    |
| 全面数据可视化支持   | 内置丰富的数据分析与可视化展示，助力数据洞察与业务决策。                                                    |
</div>

---

## 🏗️ 系统架构

### 整体架构图

<div align="center">
  <img src="static/整体架构图.png" alt="系统整体架构图" width="100%" style="border-radius:12px; box-shadow:0 4px 20px rgba(0,0,0,0.10); margin: 24px 0;" />
  <br />
  <span style="color: #888; font-size: 15px;">BaiduIndexHunter 2.0 系统整体架构图</span>
</div>


## 📸 系统界面模块化展示


### 1️⃣ 首页

<div align="center">
  <img src="static/首页-门面.png" width="47%" />
  <img src="static/首页-流畅的操作体验.png" width="47%" />
  <br />
  <img src="static/首页-数据来源说明.png" width="47%" />
  <img src="static/首页-为什么选择我们.png" width="47%" />
</div>

- 提供产品入口、数据来源、产品优势展示，以及引导性操作体验和导航。

---

### 2️⃣ 数据采集页

<div align="center">
  <img src="static/数据采集-搜索指数.png" width="47%" />
  <img src="static/数据采集-任务列表.png" width="47%" />
</div>

- 支持批量关键词采集任务，展示任务列表、采集维度，实时采集进度与即时反馈。

---

### 3️⃣ Cookie 管理页

<div align="center">
  <img src="static/cookie管理.png" width="47%" />
  <img src="static/cookie用量可视化.png" width="47%" />
</div>

- 支持账号与 Cookie 的导入、轮换、状态监控，提供用量统计及状态可视化。

---

### 4️⃣ 数据可视化页

<div align="center">
  <img src="static/数据大屏-总览.png" width="100%" />
  <br />
  <img src="static/数据大屏-关键词分析.png" width="47%" />
  <img src="static/数据大屏-任务完成率.png" width="47%" />
</div>

- 多维展示采集与分析结果，包含关键词分析、任务进展、趋势图等可视化面板。

---

### 5️⃣ 日志和配置页

<div align="center">
  <img src="static/系统配置.png" width="47%" />
  <img src="static/实时日志.png" width="47%" />
</div>

- 系统配置修改、环境信息校验，采集与系统运行日志实时监控。

---

### 6️⃣ 主题与国际化

<div align="center">
  <img src="static/深色模式.png" width="47%" />
  <img src="static/多语言国际化.png" width="47%" />
</div>

- 一键切换暗色/亮色主题，内置多语言界面，支持国际化无障碍体验。

---

### 7️⃣ 采集数据示例

<div align="center">
  <img src="static/年度数据示例.png" width="47%" />
  <img src="static/日度数据示例.png" width="47%" />
</div>

- 展示年度、日度等不同粒度的数据样例，辅助理解采集与分析能力。

---

## 一次完整分析流程

| 步骤 | 环节 | 操作说明 |
| :---: | :--- | :--- |
| 1 | **环境部署** | 按照「快速开始」完成 MySQL/Redis 安装、数据库初始化、`.env` 配置、后端与前端依赖安装并启动服务。 |
| 2 | **Cookie 准备** | 登录百度指数，从浏览器开发者工具复制 Cookie，在「Cookie 管理」页面添加并确保状态为可用。 |
| 3 | **关键词与地域** | 在「数据采集」对应模块（如搜索指数、资讯指数）中，输入关键词（支持批量或文件上传）、选择地域（省/市）和日期范围。 |
| 4 | **创建任务** | 设置输出格式（CSV/Excel/Parquet 等）、输出目录与文件名，点击「创建任务」提交。 |
| 5 | **监控执行** | 在「任务列表」查看任务状态，在「实时日志」查看进度条、速度与 ETA；支持暂停/恢复、断点续爬。 |
| 6 | **获取数据** | 任务完成后，在输出目录获取数据文件（或通过任务详情中的下载入口），数据已按选定格式导出。 |
| 7 | **可视化分析** | 在「数据大屏」查看总览、关键词分析、地域分析等；也可将数据导入 Excel/Stata/Python 等进行深度分析。 |

---

## 项目代码结构树

> [!IMPORTANT]  
> 以下结构已排除 `node_modules`、`venv`、`logs`、`output`、`.env` 等被 `.gitignore` 忽略的内容。

```
BaiduIndexHunter2.0/
├── baidu-index-hunter-backend/                 # 后端 Flask 应用
│   ├── app.py                                  # Flask 主入口，蓝图注册、WebSocket 初始化
│   ├── config/                                 # 配置目录
│   │   ├── __init__.py
│   │   └── .env.example                        # 环境变量示例（MySQL/Redis/API 等）
│   ├── scripts/                                # 脚本与 SQL
│   │   ├── BaiduIndexHunter.sql                # 数据库建表与初始化脚本
│   │   ├── fix_db_schema.py                    # 数据库结构修复脚本
│   │   └── import_region_data.py               # 区域数据导入脚本
│   ├── src/                                    # 核心源码
│   │   ├── api/                                # REST API 层
│   │   │   ├── schemas/                        # Pydantic 请求/响应模型
│   │   │   │   ├── base.py                     # 响应格式化
│   │   │   │   ├── config.py                   # 配置相关 Schema
│   │   │   │   ├── cookie.py                   # Cookie 相关 Schema
│   │   │   │   ├── region.py                   # 区域相关 Schema
│   │   │   │   ├── statistics.py               # 统计相关 Schema
│   │   │   │   ├── task.py                     # 任务相关 Schema
│   │   │   │   └── word_check.py               # 关键词校验 Schema
│   │   │   ├── utils/                          # Swagger 文档、校验工具
│   │   │   └── v1/                             # API v1 控制器
│   │   │       ├── config_api.py               # 配置、路径浏览、目录校验
│   │   │       ├── cookie_controller.py        # Cookie CRUD、状态管理
│   │   │       ├── region_controller.py        # 省份/城市数据
│   │   │       ├── statistics_controller.py    # 统计与 dashboard 数据
│   │   │       ├── task_controller.py          # 任务创建、启停、列表
│   │   │       └── word_graph_controller.py    # 需求图谱接口
│   │   ├── core/                               # 核心模块
│   │   │   ├── auth.py                         # Bearer Token API 鉴权
│   │   │   ├── config.py                       # 配置加载与 MySQL/Redis 连接
│   │   │   ├── env_validator.py                # 启动时环境变量校验
│   │   │   ├── logger.py                       # Loguru 日志配置
│   │   │   ├── redis.py                        # Redis 客户端
│   │   │   └── constants/                      # 响应码等常量
│   │   ├── data/                               # 数据层
│   │   │   ├── database.py                     # SQLModel 引擎与会话
│   │   │   ├── models/                         # ORM 模型（Task/Cookie/Config 等）
│   │   │   ├── repositories/                   # 数据仓库（TaskRepo/CookieRepo 等）
│   │   │   └── static/                         # 静态数据（城市/省份/层级 JSON）
│   │   ├── engine/                             # 爬虫引擎
│   │   │   ├── crypto/                         # 百度指数加密 Token
│   │   │   │   ├── cipher_generator.py         # Cipher-Text 生成（execjs 调用 JS）
│   │   │   │   ├── Cipher-Text.js              # 加密算法实现
│   │   │   │   ├── ab_sr_updater.py            # ab_sr Cookie 更新
│   │   │   │   └── ab_sr.js
│   │   │   ├── processors/                     # 数据解析与格式化
│   │   │   │   ├── search_processor.py         # 搜索指数
│   │   │   │   ├── feed_processor.py           # 资讯指数
│   │   │   │   ├── demographic_processor.py    # 人群属性
│   │   │   │   ├── region_processor.py         # 地域分布
│   │   │   │   └── word_graph_processor.py     # 需求图谱
│   │   │   └── spider/                         # 爬虫实现
│   │   │       ├── base_crawler.py             # 抽象基类：进度、断点续爬、格式转换
│   │   │       ├── search_index_crawler.py     # 搜索指数爬虫
│   │   │       ├── feed_index_crawler.py       # 资讯指数爬虫
│   │   │       ├── word_graph_crawler.py       # 需求图谱爬虫
│   │   │       ├── demographic_attributes_crawler.py  # 人群属性爬虫
│   │   │       ├── interest_profile_crawler.py # 兴趣画像爬虫
│   │   │       ├── region_distribution_crawler.py     # 地域分布爬虫
│   │   │       └── word_check_spider.py        # 关键词校验爬虫
│   │   ├── scheduler/                          # 任务调度
│   │   │   ├── scheduler.py                    # 优先级队列、并发控制
│   │   │   └── executor.py                     # 爬虫实例化与执行
│   │   ├── services/                           # 业务服务层
│   │   │   ├── task_service.py                 # 任务参数解析与路由
│   │   │   ├── cookie_service.py               # Cookie CRUD、Redis 同步
│   │   │   ├── cookie_rotator.py               # Cookie 轮换策略
│   │   │   ├── config_service.py               # 配置管理
│   │   │   ├── storage_service.py              # CSV/Excel 存储与格式转换
│   │   │   ├── progress_manager.py             # SQLite 检查点管理
│   │   │   ├── websocket_service.py            # 实时日志与进度推送
│   │   │   ├── region_service.py               # 区域数据服务
│   │   │   ├── statistics_service.py           # 统计服务
│   │   │   └── ...
│   │   └── utils/                              # 工具函数
│   │       ├── decorators.py                   # 通用装饰器
│   │       └── rate_limiter.py                 # 请求频率限制
│   ├── tests/                                  # 单元测试与集成测试
│   │   ├── conftest.py                         # pytest 配置、fixture
│   │   ├── test_config_api.py                  # 配置 API 测试
│   │   ├── test_cookie_api.py                  # Cookie API 测试
│   │   ├── test_demographic_crawler.py         # 人群属性爬虫测试
│   │   └── ...
│   ├── requirements.txt                        # Python 依赖清单
│   └── scrapy.cfg                              # Scrapy 配置文件
├── baidu-index-hunter-frontend/                # 前端 Vue 3 SPA
│   ├── index.html                              # 入口 HTML
│   ├── package.json                            # npm 依赖与脚本
│   ├── vite.config.js                          # Vite 构建配置
│   ├── .env.example                            # 前端环境变量示例
│   ├── public/                                 # 静态资源
│   │   └── vite.svg
│   └── src/
│       ├── main.js                             # Vue 应用入口
│       ├── App.vue                             # 根组件
│       ├── router/                             # Vue Router
│       │   └── index.js                        # 路由配置
│       ├── store/                              # Pinia 状态管理
│       │   ├── app.js                          # 主题、语言
│       │   ├── config.js                       # 配置
│       │   ├── region.js                       # 区域数据
│       │   └── wordGraph.js                    # 需求图谱时间范围
│       ├── views/                              # 页面视图
│       │   ├── Home.vue                        # 首页
│       │   ├── DataCollection.vue              # 数据采集（任务创建 Hub）
│       │   ├── CookieManager.vue               # Cookie 管理
│       │   ├── Logs.vue                        # 实时日志
│       │   ├── Settings.vue                    # 系统配置
│       │   ├── About.vue                       # 关于
│       │   ├── Privacy.vue                     # 隐私政策
│       │   ├── NotFound.vue                    # 404
│       │   └── dashboard/                      # 数据大屏
│       │       ├── Dashboard.vue               # 大屏容器
│       │       └── components/                 # 大屏 Tab 组件
│       │           ├── OverviewTab.vue         # 总览
│       │           ├── SpiderHealthTab.vue     # 爬虫健康
│       │           ├── KeywordAnalysisTab.vue  # 关键词分析
│       │           └── RegionAnalysisTab.vue   # 地域分析
│       ├── components/                         # 公共组件
│       │   ├── DirPicker.vue                   # 目录选择器
│       │   ├── RegionCitySelector.vue          # 城市选择器
│       │   ├── RegionProvinceSelector.vue      # 省份选择器
│       │   ├── CookieUsageChart.vue            # Cookie 用量图表
│       │   └── tasks/                          # 任务创建组件
│       │       ├── SearchIndexTask.vue         # 搜索指数
│       │       ├── FeedIndexTask.vue           # 资讯指数
│       │       ├── WordGraphTask.vue           # 需求图谱
│       │       ├── DemographicAttributesTask.vue  # 人群属性
│       │       ├── InterestProfileTask.vue     # 兴趣画像
│       │       ├── RegionDistributionTask.vue  # 地域分布
│       │       └── TaskList.vue                # 任务列表
│       ├── api/                                # API 调用封装
│       │   ├── task.js                         # 任务 API
│       │   └── statistics.js                   # 统计 API
│       ├── config/                             # 前端配置
│       │   └── api.js                          # API 地址、WebSocket 地址
│       ├── i18n/                               # 国际化
│       │   ├── index.js                        # Vue I18n 配置
│       │   └── locales/                        # 9 种语言
│       │       ├── zh_CN.js
│       │       ├── zh-TW.js
│       │       ├── en.js
│       │       └── ...
│       ├── utils/                              # 工具函数
│       │   ├── request.js                      # Axios 封装、鉴权拦截器
│       │   └── websocket.js                    # WebSocket 服务
│       └── assets/                             # 样式与图片
│           ├── main.scss
│           ├── logo.svg
│           └── ...
├── static/                                     # README 图片与演示资源
│   ├── github-header-banner-zh.png             # 项目横幅
│   ├── 整体架构图.png
│   ├── 数据采集-搜索指数.png
│   ├── 数据大屏-总览.png
│   ├── cookie管理.png
│   └── ...
├── start.sh                                    # 一键启动脚本（后端+前端）
├── README.md                                   # 中文说明文档
├── README_EN.md                                # 英文说明文档
├── CONTRIBUTING.md                             # 贡献指南
├── LICENSE                                     # 非商业许可协议
└── .gitignore                                  # Git 忽略规则
```

---

## 🚀 快速开始

> [!IMPORTANT]  
> 本项目为个人在百度指数实证研究过程中，为方便批量采集关键词数据而构建的工具，**仅供学习交流使用，严禁用于商业用途**。因商业用途产生的一切后果由使用者自行承担。

### 一、环境要求

#### 1.1 操作系统

| 平台 | 要求 |
| :--- | :--- |
| Windows | 10 / 11 |
| macOS | 10.14 或更高版本 |
| Linux | Ubuntu 18.04+ / CentOS 7+ / Debian 9+ |

#### 1.2 必需软件

| 软件 | 最低版本 | 推荐版本 |
| :--- | :--- | :--- |
| Python | 3.11 | 3.11.x |
| Node.js | 18.0 | 18.x 或 21.x |
| MySQL | 8.0 | 8.x |
| Redis | 7.4 | 7.4 |

> **Windows 用户说明**：  
> - Node.js 推荐使用 [nvm-windows](https://github.com/coreybutler/nvm-windows) 管理多版本，安装后执行 `nvm install 21`、`nvm use 21` 使用 Node 21。  
> - Redis 在 Windows 下可使用 [Memurai](https://www.memurai.com/) 替代，安装后需确保 `memurai-cli ping` 返回 `PONG`。

#### 1.3 环境验证

```bash
# 验证 Python
python --version   # 应为 3.11.x

# 验证 Node.js
node --version     # 应为 v18.x 或 v21.x

# 验证 MySQL
mysql --version    # 应为 8.x

# 验证 Redis（Linux/macOS 为 redis-cli，Windows 为 memurai-cli）
redis-cli ping     # 或 memurai-cli ping，应返回 PONG
```

---

### 二、配置

#### 2.1 初始化数据库

在项目根目录下执行：

```bash
# 登录 MySQL（输入密码）
mysql -u root -p

# 在 MySQL 命令行中执行（注意路径，从项目根目录执行时使用以下路径）
source baidu-index-hunter-backend/scripts/BaiduIndexHunter.sql

# 执行成功后退出
exit
```

若已进入 `baidu-index-hunter-backend` 目录，则使用：

```sql
source scripts/BaiduIndexHunter.sql
```

#### 2.2 配置环境变量

1. 进入后端目录 `baidu-index-hunter-backend/config/`
2. 复制 `.env.example` 为 `.env`
3. 编辑 `.env`，**至少修改以下必填项**：

| 配置项 | 说明 |
| :--- | :--- |
| `MYSQL_PASSWORD` | 替换为你的 MySQL 登录密码，禁止使用占位符 |
| `API_SECRET_KEY` | 替换为随机生成的复杂密钥（用于 API 鉴权），禁止使用「请修改此密钥」等占位文字 |

4. 其他配置（Redis、Flask 端口、爬虫参数等）可按需调整，完整说明见 `config/.env.example`。

> **重要**：启动前会校验 `MYSQL_PASSWORD` 和 `API_SECRET_KEY`，若使用占位值会导致启动失败。

---

### 三、安装依赖

#### 3.1 后端依赖

```bash
# 进入后端目录
cd baidu-index-hunter-backend

# 创建 Python 虚拟环境（推荐）
python -m venv baiduindexhunter

# 激活虚拟环境
# Windows (CMD)
baiduindexhunter\Scripts\activate

# Windows (PowerShell)
baiduindexhunter\Scripts\Activate.ps1

# macOS / Linux
source baiduindexhunter/bin/activate

# 安装依赖
pip install -r requirements.txt

# 若安装较慢，可使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

#### 3.2 前端依赖

```bash
# 进入前端目录
cd baidu-index-hunter-frontend

# 安装依赖
npm install

# 若安装较慢，可先切换国内镜像
npm config set registry https://registry.npmmirror.com
npm install
```

---

### 四、启动服务

需同时启动后端和前端，建议使用两个终端窗口。

#### 4.1 启动后端

**终端一**：

```bash
cd baidu-index-hunter-backend

# 激活虚拟环境（若未激活）
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# 启动后端服务
python app.py
```

**启动成功标志**：终端输出类似以下内容：

```
成功连接到MySQL和Redis
任务调度器启动成功
启动应用，地址: http://0.0.0.0:5001
API文档地址: http://0.0.0.0:5001/api/docs/
```

#### 4.2 启动前端

**终端二**：

```bash
cd baidu-index-hunter-frontend

# 启动前端开发服务器
npm run dev
```

**启动成功标志**：终端输出类似：

```
VITE v5.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
```

---

### 五、验证安装

| 步骤 | 操作 | 预期结果 |
| :--- | :--- | :--- |
| 1 | 浏览器访问 `http://localhost:5001/api/health` | 返回 JSON，包含 `status: "UP"` |
| 2 | 浏览器访问 `http://localhost:5173/` | 显示项目首页 |
| 3 | 前端 → 左侧菜单「系统配置」 | 能正常加载配置项（说明数据库连接正常） |
| 4 | 前端 → 「Cookie 管理」→ 添加 Cookie | 能成功添加（需先登录百度指数，从浏览器开发者工具复制 Cookie） |
| 5 | 前端 → 「搜索指数采集」→ 测试一个简单关键词 | 任务能创建并执行，有进度反馈 |

#### Cookie 获取方式

1. 登录 [百度指数](https://index.baidu.com/)
2. 按 F12 打开浏览器开发者工具
3. 切到「Application」或「存储」→ Cookies → 选择 `index.baidu.com`
4. 复制所有 Cookie 键值对，粘贴到项目前端的 Cookie 管理页面

---

### 六、常见问题

| 问题 | 可能原因 | 处理建议 |
| :--- | :--- | :--- |
| 后端启动失败，提示环境变量校验错误 | `MYSQL_PASSWORD` 或 `API_SECRET_KEY` 使用占位值 | 修改 `config/.env`，填写真实密码和随机密钥 |
| 无法连接 MySQL | 密码错误、MySQL 未启动、端口非 3306 | 检查 MySQL 服务、密码、端口配置 |
| 无法连接 Redis | Redis 未启动、Windows 未安装 Memurai | 启动 Redis 服务；Windows 用户安装并启动 Memurai |
| 前端请求 401 | 前端未配置 `API_SECRET_KEY` | 在「系统配置」→「API 连接」中填写与后端一致的密钥，或在前端 `.env` 中配置 `VITE_API_SECRET_KEY` |

---

## ⚠️ 免责声明

**重要提醒：本项目仅供学习、学术研究和教育目的使用**

1. **合规性声明**：

   - 本项目中的所有代码、工具和功能均仅供学习、学术研究和教育目的使用。
   - 严禁将本项目用于任何商业用途或盈利性活动。
   - 严禁将本项目用于任何违法、违规或侵犯他人权益的行为。

2. **爬虫功能免责**：

   - 项目中的爬虫功能仅用于技术学习和研究目的。
   - 使用者必须遵守目标网站的 robots.txt 协议和使用条款。
   - 使用者必须遵守相关法律法规，不得进行恶意爬取或数据滥用。
   - 因使用爬虫功能产生的任何法律后果由使用者自行承担。

3. **数据使用免责**：

   - 项目涉及的数据分析功能仅供学术研究使用。
   - 严禁将分析结果用于商业决策或盈利目的。
   - 使用者应确保所分析数据的合法性和合规性。

4. **技术免责**：

   - 本项目按“现状”提供，不提供任何明示或暗示的保证。
   - 作者不对使用本项目造成的任何直接或间接损失承担责任。
   - 使用者应自行评估项目的适用性和风险。

5. **责任限制**：

   - 使用者在使用本项目前应充分了解相关法律法规。
   - 使用者应确保其使用行为符合当地法律法规要求。
   - 因违反法律法规使用本项目而产生的任何后果由使用者自行承担。

**请在使用本项目前仔细阅读并理解上述免责声明。使用本项目即表示您已同意并接受上述所有条款。**

---

## 📄 许可证

本项目采用 [**EULA 非商业许可协议**](LICENSE)。详细信息请参阅 LICENSE 文件。

---

## 📞 联系作者

<table align="center">
  <tr>
    <td align="center"><b>微信</b></td>
    <td align="center"><b>QQ</b></td>
  </tr>
  <tr>
    <td align="center"><img src="static/wechat.jpg" width="180" /></td>
    <td align="center"><img src="static/QQ.jpg" width="180" /></td>
  </tr>
  <tr>
    <td align="center">微信: Lucky_ff0810</td>
    <td align="center">QQ: 1957689514</td>
  </tr>
</table>

<p align="center">
  📧 <strong>Email:</strong> <a href="mailto:15968588744@163.com">15968588744@163.com</a>
</p>

---

## 📈 项目统计

<a href="https://www.star-history.com/#Auroral0810/BaiduIndexHunter&type=date&legend=bottom-right">
  <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=Auroral0810/BaiduIndexHunter&type=date&theme=light&legend=bottom-right" style="vertical-align:middle;display:inline-block;" />
</a>


![Alt](https://repobeats.axiom.co/api/embed/1f0334fb444a74a291d3eeb3bf381df5bf6619e3.svg "Repobeats analytics image")

<p align="center" style="margin-top:2em;">
  <b>如果这个项目对你有帮助，请点击右上角给一个 ⭐ Star 支持一下！感谢！</b>
</p>
