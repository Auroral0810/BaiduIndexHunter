<table align="center" border="0">
  <tr>
    <td width="45%" align="center">
      <img src="baidu-index-hunter-frontend/src/assets/logo.svg" alt="Logo" width="80">
      <h1>🎯 BaiduIndexHunter 2.0</h1>
      <p><strong>专业的百度指数采集与分析平台</strong></p>
    </td>
    <td width="55%">
      <img src="baidu-index-hunter-frontend/src/assets/slogn_logo.jpg" alt="Slogan" width="100%">
    </td>
  </tr>
</table>

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
  <video src="https://github.com/Auroral0810/BaiduIndexHunter/raw/main/static/github演示视频.mp4" controls autoplay muted loop width="90%">
    您的浏览器不支持视频播放，请<a href="static/github演示视频.mp4">点击此处下载</a>观看。
  </video>
</p>

---

## ⚠️ 免责声明

> **本项目仅供学习交流使用，严禁用于任何商业用途。**
> 使用者需遵守相关法律法规，因使用本项目而产生的任何法律责任由使用者自行承担。

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

---

## ✨ 功能特性

<div align="center">

|     🔍 **六大模块全覆盖**      | ⚡ **高效并发采集** | 📊 **实时状态监控** | 🍪 **智能 Cookie 管理** |
| :----------------------------: | :-----------------: | :-----------------: | :---------------------: |
| 搜索指数 · 资讯指数 · 需求图谱 |   分布式任务队列    | WebSocket 实时推送  |   自动轮换 · 封禁检测   |
| 人群属性 · 兴趣分布 · 地域分布 |   多用户同时采集    |   数据大屏可视化    |     用量统计可视化      |

| 🔄 **断点续传**  | 📤 **灵活数据导出** | 🌐 **国际化多语言**  | 🌙 **深色模式** |
| :--------------: | :-----------------: | :------------------: | :-------------: |
| 任务中断自动恢复 |  CSV / Excel 格式   | 中文 / 英文 界面切换 |  护眼深色主题   |
|   检查点持久化   |   自动持久化存储    |     一键切换语言     |  一键切换主题   |

</div>

---

## 🏗️ 系统架构

### 整体架构图

```mermaid
flowchart TB
    subgraph Client["🖥️ 客户端"]
        Browser["浏览器"]
    end

    subgraph Frontend["🎨 前端 Vue.js 3"]
        direction LR
        UI["Element Plus UI"]
        Charts["ECharts 图表"]
        WS_C["WebSocket"]
    end

    subgraph Backend["⚙️ 后端 Flask"]
        direction LR
        API["RESTful API"]
        WS_S["Socket.IO"]
        Scheduler["APScheduler"]
    end

    subgraph Crawler["🕷️ 爬虫引擎"]
        direction TB
        C1["搜索指数"]
        C2["资讯指数"]
        C3["地域分布"]
        C4["人群属性"]
        C5["需求图谱"]
        C6["兴趣分布"]
    end

    subgraph Storage["💾 数据存储"]
        direction LR
        MySQL[("MySQL")]
        Redis[("Redis")]
        Files["CSV/Excel"]
    end

    Browser --> Frontend
    Frontend <--> Backend
    Backend --> Crawler
    Crawler --> Storage
    Backend <--> Storage
```

### 爬虫任务流程图

```mermaid
flowchart LR
    A([🧑 用户]) -->|1. 创建任务| B[📱 前端]
    B -->|2. POST /api/tasks| C[⚙️ 后端]
    C -->|3. 保存任务| D[(💾 数据库)]
    C -->|4. 加入队列| E[📋 任务队列]
    E -->|5. 分发任务| F[🕷️ 爬虫引擎]
    F -->|6. 请求数据| G[🌐 百度 API]
    G -->|7. 返回数据| F
    F -->|8. 存储结果| D
    F -.->|9. 推送进度| B
    B -.->|10. 显示结果| A

    style A fill:#e1f5fe
    style B fill:#fff3e0
    style C fill:#f3e5f5
    style D fill:#e8f5e9
    style E fill:#fce4ec
    style F fill:#fff8e1
    style G fill:#e3f2fd
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
|         ![Pinia](https://img.shields.io/badge/-Pinia-F7D336?style=flat-square&logo=vue.js&logoColor=black)          | 2.x  | 状态管理              |
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

<table align="center">
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
