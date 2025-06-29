# 百度指数猎手前端

百度指数猎手是一个高效、稳定的百度指数数据采集和分析工具。通过简单的界面操作，可以快速获取关键词的搜索指数、媒体指数等数据。

## 功能特点

- 多关键词支持：支持单个或批量输入关键词，也可以从文件导入
- 多维度数据：支持搜索指数、媒体指数、需求图谱等多种数据类型
- 丰富的时间维度：支持日度、周度数据，可灵活选择时间范围
- 多终端支持：区分PC和移动端数据，全面了解用户行为
- 智能导出：支持多种格式导出，方便后续分析处理
- 稳定可靠：智能Cookie池管理，保障长时间稳定采集

## 技术栈

- Vue 3 + Composition API
- Vite
- Element Plus
- Pinia 状态管理
- Vue Router
- Axios
- ECharts 数据可视化

## 安装与运行

1. 克隆项目到本地

```bash
git clone https://github.com/yourusername/baidu-index-hunter.git
cd baidu-index-hunter/baidu-index-hunter-frontend
```

2. 安装依赖

```bash
# 由于存在依赖冲突，使用以下命令安装
npm install --legacy-peer-deps
# 或者
yarn install --ignore-engines
```

3. 启动开发服务器

```bash
npm run dev
# 或者
yarn dev
```

4. 构建生产版本

```bash
npm run build
# 或者
yarn build
```

## 项目结构

```
baidu-index-hunter-frontend/
├── public/              # 静态资源
├── src/
│   ├── assets/          # 项目资源文件
│   ├── components/      # 组件
│   ├── router/          # 路由配置
│   ├── views/           # 页面视图
│   ├── App.vue          # 根组件
│   └── main.js          # 入口文件
├── package.json         # 项目依赖
└── vite.config.js       # Vite配置
```

## 页面说明

- 主页：项目介绍和功能概览
- 数据采集：核心功能页面，用于配置和执行数据采集任务
- 配置信息：设置API、Cookie和爬虫参数
- 关于我们：项目和团队信息
- 隐私政策：数据使用和隐私保护说明

## 联系方式

- GitHub: [github.com/yourusername/baidu-index-hunter](https://github.com/yourusername/baidu-index-hunter)
- 邮箱: support@baiduindexhunter.com
