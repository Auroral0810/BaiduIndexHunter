<div align="center">
  <img src="baidu-index-hunter-frontend/src/assets/logo.svg" alt="BaiduIndexHunter Logo" width="150">
  <h1>🎯 BaiduIndexHunter 2.0</h1>
  <p><strong>Professional Baidu Index Data Collection & Analysis Platform</strong></p>
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

## 📺 Demo Video

<p align="center">
  <a href="static/github演示视频.mp4">
    <img src="static/首页-门面.png" alt="Click to watch demo video" width="80%">
  </a>
</p>

> 👆 Click the image above to watch the full demo video

---

## ⚠️ Disclaimer

> **This project is for educational and research purposes only. Commercial use is strictly prohibited.**
> Users must comply with applicable laws and regulations. Any legal liability arising from the use of this project is the sole responsibility of the user.

---

## 📖 Table of Contents

- [Introduction](#-introduction)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Tech Stack](#-tech-stack)
- [Screenshots](#-screenshots)
- [Quick Start](#-quick-start)
- [Usage Examples](#-usage-examples)
- [Crawler Modules](#-crawler-modules)
- [Requirements](#-requirements)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)
- [Star History](#-star-history)

---

## 🎯 Introduction

**BaiduIndexHunter 2.0** is a full-featured Baidu Index data collection and analysis system designed to help users efficiently obtain core data from Baidu Search, News, User Demographics, and more.

The system uses a modern **front-end and back-end separation architecture**, supporting:

- 🚀 Multi-user concurrent tasks
- 📊 Real-time monitoring & data visualization dashboard
- 🔐 Powerful Cookie pool management
- 🔄 Checkpoint recovery & auto-resume
- 🌍 Multi-language internationalization support

Whether for academic research, market analysis, or competitive research, BaiduIndexHunter provides stable and reliable data support.

---

## ✨ Features

<table>
  <tr>
    <td align="center" width="25%">
      <img src="https://img.icons8.com/color/48/000000/search--v1.png" width="40"><br>
      <strong>Six Module Coverage</strong><br>
      <sub>Search Index, News Index, Demand Graph<br>Demographics, Interest, Region</sub>
    </td>
    <td align="center" width="25%">
      <img src="https://img.icons8.com/color/48/000000/parallel-tasks.png" width="40"><br>
      <strong>Concurrent Collection</strong><br>
      <sub>Distributed task queue<br>Multi-user support</sub>
    </td>
    <td align="center" width="25%">
      <img src="https://img.icons8.com/color/48/000000/real-time.png" width="40"><br>
      <strong>Real-time Monitoring</strong><br>
      <sub>WebSocket push<br>Data dashboard</sub>
    </td>
    <td align="center" width="25%">
      <img src="https://img.icons8.com/color/48/000000/cookie.png" width="40"><br>
      <strong>Smart Cookie Management</strong><br>
      <sub>Auto rotation, ban detection<br>Usage visualization</sub>
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="https://img.icons8.com/color/48/000000/resume.png" width="40"><br>
      <strong>Checkpoint Recovery</strong><br>
      <sub>Auto-resume on interruption<br>Persistent checkpoints</sub>
    </td>
    <td align="center">
      <img src="https://img.icons8.com/color/48/000000/export.png" width="40"><br>
      <strong>Flexible Export</strong><br>
      <sub>CSV / Excel formats<br>Auto-persistence</sub>
    </td>
    <td align="center">
      <img src="https://img.icons8.com/color/48/000000/language.png" width="40"><br>
      <strong>Internationalization</strong><br>
      <sub>Chinese / English UI</sub>
    </td>
    <td align="center">
      <img src="https://img.icons8.com/color/48/000000/moon-satellite.png" width="40"><br>
      <strong>Dark Mode</strong><br>
      <sub>Eye-friendly dark theme<br>One-click toggle</sub>
    </td>
  </tr>
</table>

---

## 🏗️ System Architecture

### Architecture Diagram

```mermaid
graph TB
    subgraph Frontend["🎨 Frontend (Vue.js 3)"]
        UI[Element Plus UI]
        Charts[ECharts Charts]
        WS_Client[WebSocket Client]
        Router[Vue Router]
        Store[Pinia State]
    end

    subgraph Backend["⚙️ Backend (Flask)"]
        API[RESTful API]
        WS_Server[Socket.IO Server]
        Scheduler[APScheduler]
        CookiePool[Cookie Pool]
    end

    subgraph Engine["🕷️ Crawler Engine"]
        SearchCrawler[Search Index Crawler]
        FeedCrawler[News Index Crawler]
        RegionCrawler[Region Crawler]
        DemoCrawler[Demographics Crawler]
        GraphCrawler[Demand Graph Crawler]
    end

    subgraph Storage["💾 Data Storage"]
        MySQL[(MySQL 8.0)]
        Redis[(Redis 7.x)]
        FileSystem[File System<br>CSV/Excel]
    end

    Frontend --> |HTTP/WebSocket| Backend
    Backend --> Engine
    Backend --> Storage
    Engine --> |Data Persistence| Storage
    Engine --> |Cookie Rotation| CookiePool
```

### Task Flow Diagram

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant B as Backend API
    participant Q as Task Queue
    participant C as Crawler Engine
    participant DB as Database

    U->>F: Create crawl task
    F->>B: POST /api/v1/tasks
    B->>DB: Save task info
    B->>Q: Enqueue task
    B-->>F: Return task ID

    loop Task Execution
        Q->>C: Dispatch task
        C->>C: Get Cookie
        C->>C: Request Baidu API
        C->>DB: Save crawled data
        C-->>F: WebSocket progress push
    end

    C->>DB: Update task status
    C-->>F: Task completion notice
    F-->>U: Display results
```

---

## 🛠️ Tech Stack

### Backend

|                                                    Technology                                                    | Version | Description                 |
| :--------------------------------------------------------------------------------------------------------------: | :-----: | :-------------------------- |
|       ![Python](https://img.shields.io/badge/-Python-3776AB?style=flat-square&logo=python&logoColor=white)       |  3.11+  | Core programming language   |
|        ![Flask](https://img.shields.io/badge/-Flask-000000?style=flat-square&logo=flask&logoColor=white)         |  3.1.2  | Web API framework           |
| ![SQLAlchemy](https://img.shields.io/badge/-SQLAlchemy-D71F00?style=flat-square&logo=sqlalchemy&logoColor=white) |   2.0   | ORM with connection pooling |
|        ![Redis](https://img.shields.io/badge/-Redis-DC382D?style=flat-square&logo=redis&logoColor=white)         |   7.x   | Cache & message queue       |
|        ![MySQL](https://img.shields.io/badge/-MySQL-4479A1?style=flat-square&logo=mysql&logoColor=white)         |   8.0   | Relational database         |
|    ![Selenium](https://img.shields.io/badge/-Selenium-43B02A?style=flat-square&logo=selenium&logoColor=white)    |   4.x   | Browser automation          |
|  ![Socket.IO](https://img.shields.io/badge/-Socket.IO-010101?style=flat-square&logo=socket.io&logoColor=white)   |   5.x   | Real-time communication     |

### Frontend

|                                                     Technology                                                      | Version | Description                          |
| :-----------------------------------------------------------------------------------------------------------------: | :-----: | :----------------------------------- |
|        ![Vue.js](https://img.shields.io/badge/-Vue.js-4FC08D?style=flat-square&logo=vue.js&logoColor=white)         |   3.4   | Frontend framework (Composition API) |
|           ![Vite](https://img.shields.io/badge/-Vite-646CFF?style=flat-square&logo=vite&logoColor=white)            |   5.1   | Build tool                           |
| ![Element Plus](https://img.shields.io/badge/-Element%20Plus-409EFF?style=flat-square&logo=element&logoColor=white) |   2.4   | UI component library                 |
|          ![Pinia](https://img.shields.io/badge/-Pinia-F7D336?style=flat-square&logo=pinia&logoColor=black)          |   2.x   | State management                     |
|   ![ECharts](https://img.shields.io/badge/-ECharts-AA344D?style=flat-square&logo=apache-echarts&logoColor=white)    |   5.6   | Data visualization                   |
|          ![Axios](https://img.shields.io/badge/-Axios-5A29E4?style=flat-square&logo=axios&logoColor=white)          |   1.6   | HTTP client                          |

---

## 📸 Screenshots

### 🏠 Home Page

<table>
  <tr>
    <td><img src="static/首页-门面.png" alt="Home"></td>
    <td><img src="static/首页-为什么选择我们.png" alt="Why Choose Us"></td>
  </tr>
</table>

### 📊 Data Dashboard

<table>
  <tr>
    <td colspan="2"><img src="static/数据大屏-总览.png" alt="Dashboard Overview" width="100%"></td>
  </tr>
  <tr>
    <td><img src="static/数据大屏-任务完成率.png" alt="Task Completion"></td>
    <td><img src="static/数据大屏-关键词分析.png" alt="Keyword Analysis"></td>
  </tr>
</table>

### 🕷️ Data Collection

<table>
  <tr>
    <td><img src="static/数据采集-任务列表.png" alt="Task List"></td>
    <td><img src="static/数据采集-搜索指数.png" alt="Search Index Collection"></td>
  </tr>
</table>

### 🍪 Cookie Management

<table>
  <tr>
    <td><img src="static/cookie管理.png" alt="Cookie Management"></td>
    <td><img src="static/cookie用量可视化.png" alt="Cookie Usage Visualization"></td>
  </tr>
</table>

---

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/Auroral0810/BaiduIndexHunter.git
cd BaiduIndexHunter
```

### 2. Backend Setup

```bash
cd baidu-index-hunter-backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp config/.env.example config/.env
# Edit config/.env with your database credentials

# Initialize database
mysql -u root -p < scripts/BaiduIndexHunter.sql

# Start backend
python app.py
```

### 3. Frontend Setup

```bash
cd baidu-index-hunter-frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Production build
npm run build
```

### 4. Access System

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:5001`
- API Docs: `http://localhost:5001/apidocs`

---

## 📈 Usage Examples

### Data Output Examples

#### Daily Data

<img src="static/日度数据示例.png" alt="Daily Data Example" width="100%">

#### Yearly Data

<img src="static/年度数据示例.avif" alt="Yearly Data Example" width="100%">

---

## 🕷️ Crawler Modules

|       Module        | Function                               | API Endpoint                      |
| :-----------------: | :------------------------------------- | :-------------------------------- |
| 🔍 **Search Index** | Daily/weekly search trends, statistics | `/api/SearchApi/index`            |
|  📰 **News Index**  | Daily/weekly news trends               | `/api/FeedSearchApi/getFeedIndex` |
| 🗺️ **Demand Graph** | Keyword associations                   | `/api/WordGraph/multi`            |
| 👥 **Demographics** | Gender, age, education distribution    | `/api/SocialApi/baseAttributes`   |
|   💡 **Interest**   | User interest profile                  | `/api/SocialApi/interest`         |
|    📍 **Region**    | Provincial/city search index           | `/api/SearchApi/region`           |

---

## 💻 Requirements

|  Software   |                 Minimum                 |  Recommended  |
| :---------: | :-------------------------------------: | :-----------: |
|   **OS**    | Windows 10 / macOS 10.15 / Ubuntu 20.04 | Latest stable |
| **Python**  |                 3.11.0                  |    3.11.13    |
| **Node.js** |                 18.0.0                  | 18.20.8 (LTS) |
|  **MySQL**  |                  8.0.0                  |    8.0.36     |
|  **Redis**  |                  7.0.0                  |     7.2.7     |
| **Chrome**  |                 Latest                  |    Latest     |

> ⚠️ **Note**: Python must be 3.11.x, 3.12+ is not yet supported

---

## 🤝 Contributing

We welcome contributions of all kinds! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### How to Contribute

1. 🍴 Fork the repository
2. 🔨 Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. 📝 Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. 📤 Push to branch (`git push origin feature/AmazingFeature`)
5. 🎉 Open a Pull Request

---

## 📄 License

This project is licensed under the **EULA Non-Commercial License**.

- ✅ Personal learning and academic research allowed
- ✅ Non-commercial technical exchange allowed
- ❌ Commercial use prohibited

See [LICENSE](LICENSE) for details.

---

## 📞 Contact

If you have any questions or suggestions, feel free to reach out:

<table>
  <tr>
    <td align="center">
      <strong>📧 Email</strong><br>
      <a href="mailto:15968588744@163.com">15968588744@163.com</a>
    </td>
    <td align="center">
      <strong>💬 QQ</strong><br>
      1957689514<br>
      <img src="static/QQ.jpg" alt="QQ QR Code" width="150">
    </td>
    <td align="center">
      <strong>💚 WeChat</strong><br>
      Scan to add<br>
      <img src="static/wechat.jpg" alt="WeChat QR Code" width="150">
    </td>
  </tr>
</table>

---

## ⭐ Star History

<p align="center">
  <a href="https://star-history.com/#Auroral0810/BaiduIndexHunter&Date">
    <img src="https://api.star-history.com/svg?repos=Auroral0810/BaiduIndexHunter&type=Date" alt="Star History Chart" width="70%">
  </a>
</p>

---

<p align="center">
  <strong>If this project helps you, please give it a ⭐ Star!</strong>
</p>

<p align="center">
  Made with ❤️ by <a href="https://github.com/Auroral0810">Auroral0810</a>
</p>
