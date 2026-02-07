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
    <td align="center">扫码添加作者</td>
    <td align="center">QQ: 1957689514</td>
  </tr>
</table>

<p align="center">
  📧 <strong>Email:</strong> <a href="mailto:15968588744@163.com">15968588744@163.com</a>
</p>

---

## 📈 项目统计

<a href="https://www.star-history.com/#Auroral0810/BaiduIndexHunter&type=date&legend=top-left">
  <picture>
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=Auroral0810/BaiduIndexHunter&type=date&theme=dark&legend=top-left" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=Auroral0810/BaiduIndexHunter&type=date&legend=top-left" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=Auroral0810/BaiduIndexHunter&type=date&legend=top-left" style="vertical-align:middle;display:inline-block;" />
  </picture>
</a>

![Alt](https://repobeats.axiom.co/api/embed/1f0334fb444a74a291d3eeb3bf381df5bf6619e3.svg "Repobeats analytics image")

<p align="center" style="margin-top:2em;">
  <b>如果这个项目对你有帮助，请点击右上角给一个 ⭐ Star 支持一下！感谢！</b>
</p>
