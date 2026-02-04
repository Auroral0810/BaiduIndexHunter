# BaiduIndexHunter 2.0

百度指数数据采集系统 - 基于 Scrapy 框架的学习项目

> **重要声明：本项目仅供个人学习和技术研究使用，严禁用于任何商业用途。如果您将本项目用于商业目的或造成任何损失，由此产生的一切法律责任和后果由使用者自行承担，与项目作者无关。**

## 项目简介

BaiduIndexHunter 是一个用于学习爬虫技术的个人项目，通过采集百度指数数据来演示 Scrapy 框架、任务调度、数据可视化等技术的应用。本项目仅供个人学习交流使用，设计为本地运行，不涉及服务器部署。

### 核心特性

- **Scrapy 框架** - 成熟的爬虫框架，支持高并发、断点续传、安全退出
- **多维度数据采集** - 搜索指数、资讯指数、需求图谱、人群属性、兴趣分布、地域分布
- **智能 Cookie 管理** - 自动轮换、失效检测、冷却恢复
- **实时状态推送** - WebSocket 实时同步任务进度到前端
- **任务调度系统** - 优先级队列、并发控制、自动重试

## 项目结构

```
BaiduIndexHunter2.0/
├── README.md                     # 项目说明文档
├── .gitignore                    # Git 忽略配置
│
├── baidu-index-hunter-backend/   # 后端项目
│   ├── app.py                    # Flask 应用入口
│   ├── scrapy.cfg                # Scrapy 配置文件
│   ├── scrapy_runner.py          # Scrapy 运行器
│   ├── requirements.txt          # Python 依赖
│   ├── .env.example              # 环境变量示例
│   ├── BaiduIndexHunter.sql      # 数据库初始化脚本
│   │
│   ├── api/                      # API 接口层
│   │   ├── task_controller.py    # 任务管理接口
│   │   ├── cookie_controller.py  # Cookie 管理接口
│   │   ├── statistics_controller.py  # 统计接口
│   │   └── ...
│   │
│   ├── scrapy_app/               # Scrapy 爬虫应用
│   │   ├── settings.py           # Scrapy 配置
│   │   ├── items.py              # 数据模型
│   │   ├── spiders/              # 爬虫模块
│   │   │   ├── base_spider.py    # 基础爬虫类
│   │   │   ├── search_index_spider.py   # 搜索指数
│   │   │   ├── feed_index_spider.py     # 资讯指数
│   │   │   ├── word_graph_spider.py     # 需求图谱
│   │   │   ├── demographic_spider.py    # 人群属性
│   │   │   ├── interest_spider.py       # 兴趣分布
│   │   │   └── region_spider.py         # 地域分布
│   │   ├── middlewares/          # 中间件
│   │   │   ├── cookie_middleware.py     # Cookie 轮换
│   │   │   ├── cipher_middleware.py     # Cipher-Text 生成
│   │   │   ├── retry_middleware.py      # 智能重试
│   │   │   └── ...
│   │   ├── pipelines/            # 数据管道
│   │   │   ├── csv_pipeline.py   # CSV 导出
│   │   │   ├── mysql_pipeline.py # MySQL 统计
│   │   │   └── ...
│   │   └── extensions/           # 扩展
│   │       ├── websocket_extension.py   # WebSocket 推送
│   │       ├── checkpoint_extension.py  # 断点续传
│   │       └── ...
│   │
│   ├── scheduler/                # 任务调度
│   │   ├── task_scheduler.py     # 任务调度器
│   │   └── scrapy_task_executor.py  # Scrapy 执行器
│   │
│   ├── cookie_manager/           # Cookie 管理
│   ├── db/                       # 数据库管理
│   ├── utils/                    # 工具函数
│   ├── config/                   # 配置模块
│   ├── region_manager/           # 地区数据
│   └── constant/                 # 常量定义
│
└── baidu-index-hunter-frontend/  # 前端项目
    ├── package.json              # 依赖配置
    ├── vite.config.js            # Vite 配置
    ├── index.html                # 入口页面
    └── src/
        ├── App.vue               # 根组件
        ├── main.js               # 入口文件
        ├── api/                  # API 请求
        ├── components/           # 组件
        ├── views/                # 页面
        ├── router/               # 路由
        ├── store/                # 状态管理
        └── utils/                # 工具函数
```

## 技术栈

### 后端
- **Flask** - Web 框架
- **Scrapy** - 爬虫框架
- **MySQL** - 数据存储
- **Redis** - 缓存和状态管理
- **Flask-SocketIO** - WebSocket 实时通信

### 前端
- **Vue 3** - 前端框架
- **Vite** - 构建工具
- **Element Plus** - UI 组件库
- **ECharts** - 数据可视化
- **Pinia** - 状态管理
- **Socket.io-client** - WebSocket 客户端

## 快速开始

### 1. 环境要求

- Python 3.9+
- Node.js 16+
- MySQL 8.0+
- Redis 6.0+

### 2. 后端安装

```bash
# 进入后端目录
cd baidu-index-hunter-backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等

# 初始化数据库
mysql -u root -p < BaiduIndexHunter.sql

# 启动后端服务
python app.py
```

### 3. 前端安装

```bash
# 进入前端目录
cd baidu-index-hunter-frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 访问应用

- 前端: http://localhost:5173
- 后端 API: http://localhost:5001

## 爬虫使用

### 通过 API 创建任务

前端界面或 API 调用自动创建任务，由调度器分配给 Scrapy 执行。

### 命令行直接运行

```bash
cd baidu-index-hunter-backend

# 搜索指数
scrapy crawl search_index \
    -a task_id=test001 \
    -a keywords='["关键词1","关键词2"]' \
    -a cities='{"0":"全国"}' \
    -a days=30

# 资讯指数
scrapy crawl feed_index \
    -a task_id=test002 \
    -a keywords='["关键词"]' \
    -a year_range='[2023,2025]'

# 需求图谱
scrapy crawl word_graph \
    -a task_id=test003 \
    -a keywords='["关键词"]'

# 人群属性
scrapy crawl demographic \
    -a task_id=test004 \
    -a keywords='["关键词"]'

# 兴趣分布
scrapy crawl interest \
    -a task_id=test005 \
    -a keywords='["关键词"]'

# 地域分布
scrapy crawl region \
    -a task_id=test006 \
    -a keywords='["关键词"]'
```

### 断点续传

按 `Ctrl+C` 安全退出后，Scrapy 会自动保存爬取状态。再次运行相同任务会自动恢复。

## 数据输出

爬取数据保存在 `output/` 目录：

```
output/
├── search_index/         # 搜索指数数据
│   └── {task_id}/
│       ├── *_daily_data.csv   # 日度数据
│       └── *_stats_data.csv   # 统计数据
├── feed_index/           # 资讯指数数据
├── word_graph/           # 需求图谱数据
├── demographic/          # 人群属性数据
├── interest/             # 兴趣分布数据
├── region/               # 地域分布数据
├── scrapy_jobs/          # Scrapy 断点续传状态
└── logs/                 # 日志文件
```

## 配置说明

主要配置在 `.env` 文件中：

```bash
# 数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=BaiduIndexHunter

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379

# Scrapy 爬虫配置
SPIDER_MAX_WORKERS=16          # 并发数
SPIDER_DEFAULT_INTERVAL=0.3    # 请求间隔
SPIDER_TIMEOUT=30              # 超时时间
SPIDER_RETRY_TIMES=3           # 重试次数

# Cookie 配置
COOKIE_BLOCK_COOLDOWN=1800     # Cookie 锁定冷却时间
COOKIE_MAX_USAGE_PER_DAY=1800  # 每日最大使用次数
```

## API 接口

| 接口 | 方法 | 说明 |
|-----|------|-----|
| `/api/task/create` | POST | 创建爬虫任务 |
| `/api/task/list` | GET | 获取任务列表 |
| `/api/task/start/{id}` | POST | 启动任务 |
| `/api/task/pause/{id}` | POST | 暂停任务 |
| `/api/task/cancel/{id}` | POST | 取消任务 |
| `/api/cookie/list` | GET | 获取 Cookie 列表 |
| `/api/statistics/overview` | GET | 获取统计概览 |

## 注意事项

1. **Cookie 管理** - 需要提前在数据库中配置有效的百度账号 Cookie
2. **请求频率** - 建议保持适当的请求间隔，避免被封禁
3. **数据存储** - 大量数据采集时注意磁盘空间
4. **断点续传** - 不要删除 `output/scrapy_jobs/` 目录中的文件

## 免责声明

### 重要提示

**本项目仅供个人学习和技术研究使用，严禁用于任何商业用途。**

### 使用风险

- **账号风险**：频繁请求可能导致百度账号被限制或封禁
- **法律风险**：未经授权采集数据可能违反相关法律法规
- **数据准确性**：采集的数据仅供参考，不保证其准确性和完整性

### 免责条款

1. 本项目按"原样"提供，不提供任何形式的明示或暗示保证
2. 项目作者不对使用本项目造成的任何直接或间接损失负责
3. 项目作者不对数据的准确性、完整性或可用性做任何保证
4. 使用本项目导致的任何法律问题由使用者自行承担
5. 本项目可能随时停止维护，恕不另行通知

### 合规使用

使用本项目时请遵守：

- 中华人民共和国相关法律法规
- 百度指数的使用条款和服务协议
- 合理控制请求频率，避免对目标服务器造成负担
- 仅将采集的数据用于个人学习和研究
- 不得将采集的数据用于任何商业用途

**使用本项目即表示您已阅读、理解并同意上述免责声明。**

## 许可证

MIT License
