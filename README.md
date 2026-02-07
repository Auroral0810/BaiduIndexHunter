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
  <video src="static/github演示视频.mp4" controls autoplay muted loop width="95%" poster="static/首页-门面.png">
    您的浏览器不支持 HTML5 视频播放，请 <a href="static/github演示视频.mp4">点击此处下载</a> 观看。
  </video>
</p>

---

## ✨ 功能特性

<div align="center">

| 🏷️**核心能力**     | 📝**详细描述**                                                                                                                  |
| :------------------------- | :------------------------------------------------------------------------------------------------------------------------------------ |
| 🔍**六大模块全覆盖** | 深度集成**搜索指数**、**资讯指数**、**需求图谱**、**人群属性**、**兴趣分布**、**地域分布** 接口。 |
| 📊**实时状态监控**   | 基于**WebSocket** 技术，秒级同步采集进度与系统日志，实时监控项目运行状态。                                                      |
| ⚡**高效并发采集**   | 采用分布式消息队列设计，支持多任务同时运行，轻松应对海量关键词采集需求。                                                              |
| 🍪**智能账号池**     | 内置账号状态自动巡检机，支持 Cookie**自动轮换**、封禁预警与用量可视化统计。                                                     |
| 🔄**任务断点续存**   | 支持任务检查点（Checkpoint）机制，意外中断后可一键恢复，杜绝重复流量消耗。                                                            |
| 📤**结构化数据导出** | 自动将采集结果清洗为**CSV / Excel / Parquet** 格式，并提供结构化数据库存储支持。                                                |
| 🌐**多语言与国际化** | 完整支持**中/英 双语** 界面切换，适应多语言工作环境。                                                                           |
| 🌙**深色模式支持**   | 适配现代 IDE 审美，支持**Dark Mode** 一键切换，保护长时间工作下的视觉疲劳。                                                     |

</div>

---

## 🏗️ 系统架构

### 核心处理逻辑

```mermaid
flowchart TD
    subgraph APP["应用层 (API & UI)"]
        UI[Vue3 SPA] <--> API[Flask RESTful]
        UI <--> WS[Socket.IO 实时推送]
    end

    subgraph SCHEDULER["任务调度中心"]
        TASK_QUEUE[任务优先级队列]
        WORKER_MANAGER[执行器管理]
    end

    subgraph ENGINE["采集引擎系统"]
        DIRECTION_C[采集控制逻辑] --> CRAWLER[Spider 集群]
        CRAWLER --> COOKIE_MANAGER[Cookie 动态获取/轮换]
        COOKIE_MANAGER --> BAN_CHECK[封禁智能检测]
    end

    subgraph DATA["持久化层"]
        RDS[(MySQL 8.0 业务数据)]
        CACHE[(Redis 7.x 状态缓存)]
        FS[本地存储 CSV/Excel]
    end

    API -- 下发任务 --> SCHEDULER
    SCHEDULER -- 调度 --> ENGINE
    ENGINE -- 持久化 --> DATA
    ENGINE -- 指令反馈 --> API
```

### 数据流转流程

```mermaid
sequenceDiagram
    autonumber
    participant User as 用户
    participant Frontend as 系统前端
    participant Backend as 后端服务
    participant Queue as 调度队列
    participant Engine as 采集引擎
    participant Baidu as 百度 API

    User->>Frontend: 配置参数并启动任务
    Frontend->>Backend: 提交任务指令
    Backend->>Queue: 任务实例化并压入队列
    Queue->>Engine: 分发采集子任务

    loop 自主采集阶段
        Engine->>Engine: 校验 Cookie 有效性
        Engine->>Baidu: 发起加密数据请求
        Baidu-->>Engine: 返回原始数据包
        Engine->>Engine: 数据清洗与反解
        Engine-->>Frontend: WebSocket 推送实时进度
    end

    Engine->>Backend: 任务完成状态归档
    Backend-->>User: 导出 CSV/Excel 数据文件
```

---

## 📸 界面展示

### 🏛️ 首页控制台

<div align="center">
  <img src="static/首页-门面.png" width="48%" />
  <img src="static/首页-流畅的操作体验.png" width="48%" />
</div>

### 📊 数据大屏可视化

<div align="center">
  <img src="static/数据大屏-总览.png" width="100%" />
  <br />
  <img src="static/数据大屏-关键词分析.png" width="48%" />
  <img src="static/数据大屏-任务完成率.png" width="48%" />
</div>

### 🕷️ 任务与 Cookie 管理

<div align="center">
  <img src="static/数据采集-任务列表.png" width="48%" />
  <img src="static/cookie管理.png" width="48%" />
</div>

---

## 🚀 快速开始

### 1. 基础环境

确保安装了 **Python 3.11**、**Node.js 18**、**MySQL 8** 和 **Redis 7**。

### 2. 后端部署

```bash
# 进入后端目录
cd baidu-index-hunter-backend
# 安装依赖
pip install -r requirements.txt
# 配置 .env (参考 .env.example)
python app.py
```

### 3. 前端部署

```bash
# 进入前端目录
cd baidu-index-hunter-frontend
# 安装并运行
npm install && npm run dev
```

---

## 💻 环境要求

| 软件              | 最低要求 | 推荐版本 |
| :---------------- | :------- | :------- |
| **Python**  | 3.11.0   | 3.11.13  |
| **Node.js** | 18.0.0   | 18.20.x  |
| **MySQL**   | 8.0.0    | 8.0.36   |
| **Redis**   | 7.0.0    | 7.2.x    |

---

## 📄 许可证

本项目采用 **EULA 非商业许可协议**。

---

## 📞 联系作者

<table align="center">
  <tr>
    <td align="center"><b>微信 (WeChat)</b></td>
    <td align="center"><b>QQ (Group)</b></td>
  </tr>
  <tr>
    <td align="center"><img src="static/wechat.jpg" width="180" /></td>
    <td align="center"><img src="static/QQ.jpg" width="180" /></td>
  </tr>
  <tr>
    <td align="center">扫码添加作者</td>
    <td align="center">QQ: 1957689514</td>
  </tr>
</table>

<p align="center">
  📧 <strong>Email:</strong> <a href="mailto:15968588744@163.com">15968588744@163.com</a>
</p>

---

<p align="center">
  <b>如果这个项目对你有帮助，请点击右上角给一个 ⭐ Star 支持一下！感谢！</b>
</p>
