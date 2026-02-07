<div align="center">
  <img src="baidu-index-hunter-frontend/src/assets/logo.svg" alt="BaiduIndexHunter Logo" width="150">
  <h1>🎯 BaiduIndexHunter 2.0</h1>
  <p><strong>专业的百度指数采集与分析平台</strong></p>
  <img src="baidu-index-hunter-frontend/src/assets/slogn_logo.jpg" alt="Slogan" width="80%">
</div>

<p align="center">
  <a href="./README.md">🇨🇳 简体中文</a> | <a href="./README_EN.md">🇺🇸 English</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Vue.js-3.4-4FC08D?style=for-the-badge&logo=vue.js&logoColor=white" alt="Vue.js">
  <img src="https://img.shields.io/badge/Flask-3.1-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white" alt="MySQL">
  <img src="https://img.shields.io/badge/Redis-7.x-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis">
</p>

<p align="center">
  <img src="https://img.shields.io/github/stars/Auroral0810/BaiduIndexHunter?style=social" alt="GitHub Stars">
  <img src="https://img.shields.io/github/forks/Auroral0810/BaiduIndexHunter?style=social" alt="GitHub Forks">
  <img src="https://img.shields.io/github/issues/Auroral0810/BaiduIndexHunter" alt="Issues">
  <img src="https://img.shields.io/github/license/Auroral0810/BaiduIndexHunter" alt="License">
  <img src="https://img.shields.io/github/last-commit/Auroral0810/BaiduIndexHunter" alt="Last Commit">
</p>

---

## 📺 演示视频

<p align="center">
  <a href="static/github演示视频.mp4">
    <img src="static/首页-门面.png" alt="点击观看演示视频" width="80%">
  </a>
</p>

> 👆 点击上方图片观看完整演示视频

---

## ⚠️ 免责声明

> **本项目仅供学习交流使用，严禁用于任何商业用途。**
> 使用者需遵守相关法律法规，因使用本项目而产生的任何法律责任由使用者自行承担。
> 请勿将本项目用于任何可能侵犯他人权益的行为。

---

## 📖 目录

- [项目简介](#-项目简介)
- [功能特性](#-功能特性)
- [系统架构](#-系统架构)
- [技术栈](#-技术栈)
- [界面展示](#-界面展示)
- [快速开始](#-快速开始)
- [使用示例](#-使用示例)
- [爬虫模块](#-爬虫模块)
- [环境要求](#-环境要求)
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)
- [联系作者](#-联系作者)
- [Star 历史](#-star-历史)

---

## 🎯 项目简介

**BaiduIndexHunter 2.0** 是一个全功能的百度指数采集与分析系统，旨在帮助用户高效获取百度搜索、资讯、人群画像等核心数据。

系统采用现代化的 **前后端分离架构**，支持：

- 🚀 多用户并发任务
- 📊 实时状态监控与数据可视化大屏
- 🔐 强大的 Cookie 池管理
- 🔄 断点续传与自动恢复
- 🌍 多语言国际化支持

无论是学术研究、市场分析还是竞品调研，BaiduIndexHunter 都能为您提供稳定可靠的数据支持。

---

## ✨ 功能特性

<table>
  <tr>
    <td align="center" width="25%">
      <img src="https://img.icons8.com/color/48/000000/search--v1.png" width="40"><br>
      <strong>六大模块覆盖</strong><br>
      <sub>搜索指数、资讯指数、需求图谱<br>人群属性、兴趣分布、地域分布</sub>
    </td>
    <td align="center" width="25%">
      <img src="https://img.icons8.com/color/48/000000/parallel-tasks.png" width="40"><br>
      <strong>高效并发采集</strong><br>
      <sub>分布式任务队列<br>多用户同时采集</sub>
    </td>
    <td align="center" width="25%">
      <img src="https://img.icons8.com/color/48/000000/real-time.png" width="40"><br>
      <strong>实时状态监控</strong><br>
      <sub>WebSocket 实时推送<br>数据大屏可视化</sub>
    </td>
    <td align="center" width="25%">
      <img src="https://img.icons8.com/color/48/000000/cookie.png" width="40"><br>
      <strong>智能 Cookie 管理</strong><br>
      <sub>自动轮换、封禁检测<br>用量统计可视化</sub>
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="https://img.icons8.com/color/48/000000/resume.png" width="40"><br>
      <strong>断点续传</strong><br>
      <sub>任务中断自动恢复<br>检查点持久化</sub>
    </td>
    <td align="center">
      <img src="https://img.icons8.com/color/48/000000/export.png" width="40"><br>
      <strong>灵活数据导出</strong><br>
      <sub>CSV / Excel 格式<br>自动持久化存储</sub>
    </td>
    <td align="center">
      <img src="https://img.icons8.com/color/48/000000/language.png" width="40"><br>
      <strong>国际化多语言</strong><br>
      <sub>中文 / 英文 界面切换</sub>
    </td>
    <td align="center">
      <img src="https://img.icons8.com/color/48/000000/moon-satellite.png" width="40"><br>
      <strong>深色模式</strong><br>
      <sub>护眼深色主题<br>一键切换</sub>
    </td>
  </tr>
</table>

---

## 🏗️ 系统架构

### 整体架构图

```mermaid
graph TB
    subgraph Frontend["🎨 前端 (Vue.js 3)"]
        UI[Element Plus UI]
        Charts[ECharts 图表]
        WS_Client[WebSocket 客户端]
        Router[Vue Router]
        Store[Pinia 状态管理]
    end

    subgraph Backend["⚙️ 后端 (Flask)"]
        API[RESTful API]
        WS_Server[Socket.IO 服务]
        Scheduler[APScheduler 调度器]
        CookiePool[Cookie 池管理]
    end

    subgraph Engine["🕷️ 爬虫引擎"]
        SearchCrawler[搜索指数爬虫]
        FeedCrawler[资讯指数爬虫]
        RegionCrawler[地域分布爬虫]
        DemoCrawler[人群属性爬虫]
        GraphCrawler[需求图谱爬虫]
    end

    subgraph Storage["💾 数据存储"]
        MySQL[(MySQL 8.0)]
        Redis[(Redis 7.x)]
        FileSystem[文件系统<br>CSV/Excel]
    end

    Frontend --> |HTTP/WebSocket| Backend
    Backend --> Engine
    Backend --> Storage
    Engine --> |数据持久化| Storage
    Engine --> |Cookie 轮换| CookiePool
```

### 爬虫任务流程图

```mermaid
sequenceDiagram
    participant U as 用户
    participant F as 前端
    participant B as 后端 API
    participant Q as 任务队列
    participant C as 爬虫引擎
    participant DB as 数据库

    U->>F: 创建采集任务
    F->>B: POST /api/v1/tasks
    B->>DB: 保存任务信息
    B->>Q: 加入任务队列
    B-->>F: 返回任务 ID

    loop 任务执行
        Q->>C: 分发任务
        C->>C: 获取 Cookie
        C->>C: 请求百度 API
        C->>DB: 保存采集数据
        C-->>F: WebSocket 推送进度
    end

    C->>DB: 更新任务状态
    C-->>F: 任务完成通知
    F-->>U: 显示结果
```

---

## 🛠️ 技术栈

### 后端技术

|                                                       技术                                                       | 版本  | 说明              |
| :--------------------------------------------------------------------------------------------------------------: | :---: | :---------------- |
|       ![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white)       | 3.11+ | 核心编程语言      |
|        ![Flask](https://img.shields.io/badge/-Flask-000000?style=flat-square&logo=flask&logoColor=white)         | 3.1.2 | Web API 框架      |
| ![SQLAlchemy](https://img.shields.io/badge/-SQLAlchemy-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white) |  2.0  | ORM 框架 (连接池) |
|        ![Redis](https://img.shields.io/badge/-Redis-DC382D?style=flat-square&logo=redis&logoColor=white)         |  7.x  | 缓存与消息队列    |
|        ![MySQL](https://img.shields.io/badge/-MySQL-4479A1?style=flat-square&logo=mysql&logoColor=white)         |  8.0  | 关系型数据库      |
|    ![Selenium](https://img.shields.io/badge/-Selenium-43B02A?style=flat-square&logo=selenium&logoColor=white)    |  4.x  | 浏览器自动化      |
|  ![Socket.IO](https://img.shields.io/badge/-Socket.IO-010101?style=flat-square&logo=socket.io&logoColor=white)   |  5.x  | 实时通信          |

### 前端技术

|                                                        技术                                                         | 版本 | 说明                  |
| :-----------------------------------------------------------------------------------------------------------------: | :--: | :-------------------- |
|        ![Vue.js](https://img.shields.io/badge/-Vue.js-4FC08D?style=flat-square&logo=vue.js&logoColor=white)         | 3.4  | 前端框架 (组合式 API) |
|           ![Vite](https://img.shields.io/badge/-Vite-646CFF?style=flat-square&logo=vite&logoColor=white)            | 5.1  | 构建工具              |
| ![Element Plus](https://img.shields.io/badge/-Element%20Plus-409EFF?style=flat-square&logo=element&logoColor=white) | 2.4  | UI 组件库             |
|          ![Pinia](https://img.shields.io/badge/-Pinia-F7D336?style=flat-square&logo=pinia&logoColor=black)          | 2.x  | 状态管理              |
|   ![ECharts](https://img.shields.io/badge/-ECharts-AA344D?style=flat-square&logo=apache-echarts&logoColor=white)    | 5.6  | 数据可视化            |
|          ![Axios](https://img.shields.io/badge/-Axios-5A29E4?style=flat-square&logo=axios&logoColor=white)          | 1.6  | HTTP 客户端           |

---

## 📸 界面展示

### 🏠 首页

<table>
  <tr>
    <td><img src="static/首页-门面.png" alt="首页门面"></td>
    <td><img src="static/首页-为什么选择我们.png" alt="为什么选择我们"></td>
  </tr>
  <tr>
    <td><img src="static/首页-数据来源说明.png" alt="数据来源说明"></td>
    <td><img src="static/首页-流畅的操作体验.png" alt="流畅的操作体验"></td>
  </tr>
</table>

### 📊 数据大屏

<table>
  <tr>
    <td colspan="2"><img src="static/数据大屏-总览.png" alt="数据大屏总览" width="100%"></td>
  </tr>
  <tr>
    <td><img src="static/数据大屏-任务完成率.png" alt="任务完成率"></td>
    <td><img src="static/数据大屏-关键词分析.png" alt="关键词分析"></td>
  </tr>
</table>

### 🕷️ 数据采集

<table>
  <tr>
    <td><img src="static/数据采集-任务列表.png" alt="任务列表"></td>
    <td><img src="static/数据采集-搜索指数.png" alt="搜索指数采集"></td>
  </tr>
</table>

### 🍪 Cookie 管理

<table>
  <tr>
    <td><img src="static/cookie管理.png" alt="Cookie 管理"></td>
    <td><img src="static/cookie用量可视化.png" alt="Cookie 用量可视化"></td>
  </tr>
</table>

### ⚙️ 系统设置

<table>
  <tr>
    <td><img src="static/系统配置.png" alt="系统配置"></td>
    <td><img src="static/多语言国际化.png" alt="多语言国际化"></td>
  </tr>
  <tr>
    <td><img src="static/深色模式.png" alt="深色模式"></td>
    <td><img src="static/实时日志.png" alt="实时日志"></td>
  </tr>
</table>

### ℹ️ 关于页面

<table>
  <tr>
    <td><img src="static/关于-总览.png" alt="关于总览"></td>
    <td><img src="static/关于-项目愿景.png" alt="项目愿景"></td>
  </tr>
</table>

---

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/Auroral0810/BaiduIndexHunter.git
cd BaiduIndexHunter
```

### 2. 后端配置

```bash
cd baidu-index-hunter-backend

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp config/.env.example config/.env
# 编辑 config/.env 填写数据库等配置

# 初始化数据库
mysql -u root -p < scripts/BaiduIndexHunter.sql

# 启动后端服务
python app.py
```

### 3. 前端配置

```bash
cd baidu-index-hunter-frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 生产环境构建
npm run build
```

### 4. 访问系统

- 前端地址: `http://localhost:5173`
- 后端 API: `http://localhost:5001`
- API 文档: `http://localhost:5001/apidocs`

---

## 📈 使用示例

### 数据输出示例

#### 日度数据

<img src="static/日度数据示例.png" alt="日度数据示例" width="100%">

#### 年度数据

<img src="static/年度数据示例.avif" alt="年度数据示例" width="100%">

### 输出文件格式

数据文件存储在 `output/` 目录下，按模块组织：

```
output/
├── search_index/           # 搜索指数
│   ├── {task_id}_daily.csv
│   └── {task_id}_stats.csv
├── feed_index/             # 资讯指数
├── word_graph/             # 需求图谱
├── demographic/            # 人群属性
├── interest/               # 兴趣分布
├── region/                 # 地域分布
└── checkpoints/            # 断点文件
```

---

## 🕷️ 爬虫模块

|      模块       | 功能                        | API 端点                          |
| :-------------: | :-------------------------- | :-------------------------------- |
| 🔍 **搜索指数** | 日度/周度搜索趋势、统计数据 | `/api/SearchApi/index`            |
| 📰 **资讯指数** | 日度/周度资讯趋势           | `/api/FeedSearchApi/getFeedIndex` |
| 🗺️ **需求图谱** | 关键词关联关系              | `/api/WordGraph/multi`            |
| 👥 **人群属性** | 性别、年龄、学历分布        | `/api/SocialApi/baseAttributes`   |
| 💡 **兴趣分布** | 人群兴趣画像                | `/api/SocialApi/interest`         |
| 📍 **地域分布** | 各省市搜索指数              | `/api/SearchApi/region`           |

---

## 💻 环境要求

|     软件     |                最低版本                 |   推荐版本    |
| :----------: | :-------------------------------------: | :-----------: |
| **操作系统** | Windows 10 / macOS 10.15 / Ubuntu 20.04 |  最新稳定版   |
|  **Python**  |                 3.11.0                  |    3.11.13    |
| **Node.js**  |                 18.0.0                  | 18.20.8 (LTS) |
|  **MySQL**   |                  8.0.0                  |    8.0.36     |
|  **Redis**   |                  7.0.0                  |     7.2.7     |
|  **Chrome**  |                 最新版                  |    最新版     |

> ⚠️ **注意**: Python 必须使用 3.11.x 版本，暂不支持 3.12+

---

## 🤝 贡献指南

我们欢迎任何形式的贡献！请查阅 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

### 贡献流程

1. 🍴 Fork 本仓库
2. 🔨 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 📝 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 📤 推送分支 (`git push origin feature/AmazingFeature`)
5. 🎉 创建 Pull Request

---

## 📄 许可证

本项目采用 **EULA 非商业许可协议**。

- ✅ 允许个人学习和学术研究
- ✅ 允许非商业目的的技术交流
- ❌ 禁止任何商业用途

详情请查阅 [LICENSE](LICENSE) 文件。

---

## 📞 联系作者

如有任何问题或建议，欢迎通过以下方式联系：

<table>
  <tr>
    <td align="center">
      <strong>📧 邮箱</strong><br>
      <a href="mailto:15968588744@163.com">15968588744@163.com</a>
    </td>
    <td align="center">
      <strong>💬 QQ</strong><br>
      1957689514<br>
      <img src="static/QQ.jpg" alt="QQ二维码" width="150">
    </td>
    <td align="center">
      <strong>💚 微信</strong><br>
      扫码添加<br>
      <img src="static/wechat.jpg" alt="微信二维码" width="150">
    </td>
  </tr>
</table>

---

## ⭐ Star 历史

<p align="center">
  <a href="https://star-history.com/#Auroral0810/BaiduIndexHunter&Date">
    <img src="https://api.star-history.com/svg?repos=Auroral0810/BaiduIndexHunter&type=Date" alt="Star History Chart" width="70%">
  </a>
</p>

---

<p align="center">
  <strong>如果这个项目对你有帮助，请给一个 ⭐ Star 支持一下！</strong>
</p>

<p align="center">
  Made with ❤️ by <a href="https://github.com/Auroral0810">Auroral0810</a>
</p>
