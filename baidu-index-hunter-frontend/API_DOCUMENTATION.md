# BaiduIndexHunter 前端 API 接口文档

> 本文档详细列出了前端项目中所有的 API 接口、请求参数格式及前端请求样例。

## 目录

- [1. 基础配置](#1-基础配置)
- [2. 健康检查接口](#2-健康检查接口)
- [3. 任务管理接口](#3-任务管理接口)
- [4. 任务创建接口](#4-任务创建接口)
- [5. Cookie 管理接口](#5-cookie-管理接口)
- [6. 配置管理接口](#6-配置管理接口)
- [7. 区域数据接口](#7-区域数据接口)
- [8. 统计数据接口](#8-统计数据接口)
- [9. 关键词检查接口](#9-关键词检查接口)
- [10. WebSocket 事件](#10-websocket-事件)

---

## 1. 基础配置

### API 基础路径

```javascript
// 通过环境变量配置或默认值
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'

// 组件中直接使用的硬编码地址
const API_BASE_URL = 'http://127.0.0.1:5001/api'
```

### Axios 实例配置 (`src/utils/request.js`)

```javascript
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})
```

---

## 2. 健康检查接口

### 2.1 API 服务健康检查

**接口:** `GET /health`

**参数:** 无

**请求示例:**
```javascript
axios.get(`${API_BASE_URL}/health`, { timeout: 3000 })
```

**响应示例:**
```json
{
  "code": 10000,
  "message": "success",
  "data": {
    "status": "healthy"
  }
}
```

---

## 3. 任务管理接口

### 3.1 获取任务列表

**接口:** `GET /task/list`

**参数:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| limit | number | 否 | 每页数量，默认 10 |
| offset | number | 否 | 偏移量，默认 0 |
| keyword | string | 否 | 搜索关键词 |
| task_type | string | 否 | 任务类型筛选 |
| status | string | 否 | 状态筛选 |

**请求示例:**
```javascript
// 示例 1: 基础分页请求
axios.get(`${API_BASE_URL}/task/list`, {
  params: {
    limit: 10,
    offset: 0
  }
})

// 示例 2: 带筛选条件的请求
axios.get(`${API_BASE_URL}/task/list`, {
  params: {
    limit: 20,
    offset: 0,
    keyword: '搜索词',
    task_type: 'search_index',
    status: 'running'
  }
})

// 示例 3: 获取最近任务（Dashboard 使用）
getTaskList({ limit: 20 })
```

---

### 3.2 获取任务详情

**接口:** `GET /task/{taskId}`

**参数:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| taskId | string | 是 | 任务 ID（路径参数） |

**请求示例:**
```javascript
axios.get(`${API_BASE_URL}/task/TASK-12345`)
```

---

### 3.3 重启任务

**接口:** `POST /task/{taskId}/resume`

**参数:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| taskId | string | 是 | 任务 ID（路径参数） |

**请求示例:**
```javascript
axios.post(`${API_BASE_URL}/task/TASK-12345/resume`)
```

---

### 3.4 取消任务

**接口:** `POST /task/{taskId}/cancel`

**参数:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| taskId | string | 是 | 任务 ID（路径参数） |

**请求示例:**
```javascript
axios.post(`${API_BASE_URL}/task/TASK-12345/cancel`)
```

---

## 4. 任务创建接口

### 4.1 创建任务通用接口

**接口:** `POST /task/create`

**基础结构:**
```javascript
{
  taskType: string,       // 任务类型
  parameters: object,     // 任务参数（根据类型不同而不同）
  priority: number        // 优先级
}
```

---

### 4.2 搜索指数任务 (Search Index)

**taskType:** `"search_index"`

**parameters 字段:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| keywords | string[] | 是 | 关键词列表 |
| cities | object | 是 | 城市映射对象 |
| resume | boolean | 是 | 是否断点续传 |
| kind | string | 是 | 设备类型: "all" / "pc" / "wise" |
| days | number | 条件必填 | 预设天数（timeType='preset'时） |
| date_ranges | array | 条件必填 | 自定义日期范围（timeType='custom'或'all'时） |
| year_range | array | 条件必填 | 年份范围（timeType='year'时） |
| task_id | string | 条件必填 | 续传任务ID（resume=true时） |

**请求示例 - 预设天数:**
```javascript
axios.post(`${API_BASE_URL}/task/create`, {
  taskType: "search_index",
  parameters: {
    keywords: ["关键词1", "关键词2", "关键词3"],
    cities: {
      "0": { "name": "全国", "code": "0" }
    },
    resume: false,
    kind: "all",
    days: 30
  },
  priority: 5
})
```

**请求示例 - 自定义日期范围:**
```javascript
axios.post(`${API_BASE_URL}/task/create`, {
  taskType: "search_index",
  parameters: {
    keywords: ["科技", "人工智能"],
    cities: {
      "110000": { "name": "北京", "code": "110000" },
      "310000": { "name": "上海", "code": "310000" }
    },
    resume: false,
    kind: "pc",
    date_ranges: [
      ["2023-01-01", "2023-01-31"],
      ["2023-02-01", "2023-02-28"]
    ]
  },
  priority: 7
})
```

**请求示例 - 年份范围:**
```javascript
axios.post(`${API_BASE_URL}/task/create`, {
  taskType: "search_index",
  parameters: {
    keywords: ["年度热词"],
    cities: {
      "0": { "name": "全国", "code": "0" }
    },
    resume: false,
    kind: "all",
    year_range: ["2020", "2023"]
  },
  priority: 5
})
```

**请求示例 - 断点续传:**
```javascript
axios.post(`${API_BASE_URL}/task/create`, {
  taskType: "search_index",
  parameters: {
    keywords: ["继续采集"],
    cities: {
      "0": { "name": "全国", "code": "0" }
    },
    resume: true,
    kind: "all",
    days: 30,
    task_id: "TASK-PREVIOUS-12345"
  },
  priority: 5
})
```

---

### 4.3 资讯指数任务 (Feed Index)

**taskType:** `"feed_index"`

**parameters 字段:** 与 Search Index 完全相同

**请求示例:**
```javascript
axios.post(`${API_BASE_URL}/task/create`, {
  taskType: "feed_index",
  parameters: {
    keywords: ["热点新闻", "时事"],
    cities: {
      "0": { "name": "全国", "code": "0" }
    },
    resume: false,
    kind: "all",
    days: 7
  },
  priority: 5
})
```

---

### 4.4 需求图谱任务 (Word Graph)

**taskType:** `"word_graph"`

**parameters 字段:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| keywords | string[] | 是 | 关键词列表 |
| start_date | string | 是 | 开始日期，格式 YYYYMMDD |
| end_date | string | 是 | 结束日期，格式 YYYYMMDD |
| output_format | string | 是 | 输出格式: "csv" / "excel" |
| resume | boolean | 是 | 是否断点续传 |
| kind | string | 是 | 设备类型: "all" / "pc" / "wise" |
| task_id | string | 条件必填 | 续传任务ID（resume=true时） |

**请求示例:**
```javascript
axios.post(`${API_BASE_URL}/task/create`, {
  taskType: "word_graph",
  parameters: {
    keywords: ["电商", "直播带货"],
    start_date: "20230101",
    end_date: "20230331",
    output_format: "csv",
    resume: false,
    kind: "all"
  },
  priority: 5
})
```

---

### 4.5 人群属性任务 (Demographic Attributes)

**taskType:** `"demographic_attributes"`

**parameters 字段:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| keywords | string[] | 是 | 关键词列表 |
| output_format | string | 是 | 输出格式: "csv" / "excel" |
| batch_size | number | 是 | 批次大小 |
| resume | boolean | 是 | 是否断点续传 |
| kind | string | 是 | 设备类型: "all" / "pc" / "wise" |
| task_id | string | 条件必填 | 续传任务ID（resume=true时） |

**请求示例:**
```javascript
axios.post(`${API_BASE_URL}/task/create`, {
  taskType: "demographic_attributes",
  parameters: {
    keywords: ["美妆", "护肤品", "化妆品"],
    output_format: "excel",
    batch_size: 20,
    resume: false,
    kind: "all"
  },
  priority: 8
})
```

---

### 4.6 兴趣画像任务 (Interest Profile)

**taskType:** `"interest_profile"`

**parameters 字段:** 与 Demographic Attributes 完全相同

**请求示例:**
```javascript
axios.post(`${API_BASE_URL}/task/create`, {
  taskType: "interest_profile",
  parameters: {
    keywords: ["游戏", "电竞"],
    output_format: "csv",
    batch_size: 10,
    resume: false,
    kind: "all"
  },
  priority: 6
})
```

---

### 4.7 地域分布任务 (Region Distribution)

**taskType:** `"region_distribution"`

**parameters 字段:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| keywords | string[] | 是 | 关键词列表 |
| regions | string[] | 是 | 区域代码列表 |
| regionLevel | string | 是 | 区域级别: "province" / "city" |
| output_format | string | 是 | 输出格式: "csv" / "excel" |
| resume | boolean | 是 | 是否断点续传 |
| kind | string | 是 | 设备类型: "all" / "pc" / "wise" |
| days | number | 条件必填 | 预设天数（timeType='preset'时） |
| start_date | string | 条件必填 | 开始日期 YYYY-MM-DD（timeType='custom'时） |
| end_date | string | 条件必填 | 结束日期 YYYY-MM-DD（timeType='custom'时） |
| yearRange | array | 条件必填 | 年份范围 [startYear, endYear]（timeType='year'时） |
| date_ranges | array | 条件必填 | 日期范围数组（timeType='all'时） |
| task_id | string | 条件必填 | 续传任务ID（resume=true时） |

**请求示例 - 预设天数:**
```javascript
axios.post(`${API_BASE_URL}/task/create`, {
  taskType: "region_distribution",
  parameters: {
    keywords: ["旅游", "景点"],
    regions: ["0"],  // 全国
    regionLevel: "province",
    output_format: "csv",
    resume: false,
    kind: "all",
    days: 7
  },
  priority: 6
})
```

**请求示例 - 自定义日期:**
```javascript
axios.post(`${API_BASE_URL}/task/create`, {
  taskType: "region_distribution",
  parameters: {
    keywords: ["电影"],
    regions: ["110000", "310000", "440100"],
    regionLevel: "province",
    output_format: "excel",
    resume: false,
    kind: "pc",
    start_date: "2023-06-01",
    end_date: "2023-06-30"
  },
  priority: 5
})
```

---

## 5. Cookie 管理接口

### 5.1 获取 Cookie 池状态

**接口:** `GET /admin/cookie/pool-status`

**参数:** 无

**请求示例:**
```javascript
axios.get(`${API_BASE_URL}/admin/cookie/pool-status`)
```

**响应示例:**
```json
{
  "code": 10000,
  "data": {
    "total": 50,
    "available": 35,
    "temp_banned": 10,
    "perm_banned": 5
  }
}
```

---

### 5.2 获取可用账号列表

**接口:** `GET /admin/cookie/available-accounts`

**参数:** 无

**请求示例:**
```javascript
axios.get(`${API_BASE_URL}/admin/cookie/available-accounts`)
```

---

### 5.3 获取封禁账号列表

**接口:** `GET /admin/cookie/banned-accounts`

**参数:** 无

**请求示例:**
```javascript
axios.get(`${API_BASE_URL}/admin/cookie/banned-accounts`)
```

**响应示例:**
```json
{
  "code": 10000,
  "data": {
    "temporarily_banned": ["account1", "account2"],
    "permanently_banned": ["account3"]
  }
}
```

---

### 5.4 获取 Cookie 列表

**接口:** `GET /admin/cookie/list`

**参数:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | number | 否 | 页码 |
| limit | number | 否 | 每页数量 |
| account_id | string | 否 | 账号 ID 筛选 |
| available_only | boolean | 否 | 仅显示可用 |
| status | string | 否 | 状态筛选 |

**请求示例:**
```javascript
// 基础分页请求
axios.get(`${API_BASE_URL}/admin/cookie/list`, {
  params: {
    page: 1,
    limit: 20
  }
})

// 带筛选条件的请求
axios.get(`${API_BASE_URL}/admin/cookie/list`, {
  params: {
    page: 1,
    limit: 10,
    available_only: true,
    status: 'active'
  }
})
```

---

### 5.5 获取账号 Cookie 详情

**接口:** `GET /admin/cookie/account-cookie/{account_id}`

**参数:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| account_id | string | 是 | 账号 ID（路径参数） |

**请求示例:**
```javascript
axios.get(`${API_BASE_URL}/admin/cookie/account-cookie/user123`)
```

---

### 5.6 添加 Cookie

**接口:** `POST /admin/cookie/add`

**请求体:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| account_id | string | 是 | 账号 ID |
| cookie_data | object/string | 是 | Cookie 数据 |
| expire_days | number | 否 | 过期天数 |

**请求示例:**
```javascript
axios.post(`${API_BASE_URL}/admin/cookie/add`, {
  account_id: "new_account_001",
  cookie_data: {
    BDUSS: "xxxxx",
    BAIDUID: "xxxxx"
  },
  expire_days: 30
})
```

---

### 5.7 更新 Cookie

**接口:** `PUT /admin/cookie/update/{id}`

**参数:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | number/string | 是 | Cookie ID（路径参数） |

**请求体:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| account_id | string | 是 | 账号 ID |
| cookie_data | object/string | 是 | Cookie 数据 |
| expire_days | number | 否 | 过期天数 |
| is_available | boolean/number | 否 | 是否可用 |
| is_permanently_banned | boolean/number | 否 | 是否永久封禁 |
| temp_ban_until | string | 否 | 临时封禁截止时间 |

**请求示例:**
```javascript
axios.put(`${API_BASE_URL}/admin/cookie/update/123`, {
  account_id: "account_001",
  cookie_data: {
    BDUSS: "new_value_xxxxx",
    BAIDUID: "new_value_xxxxx"
  },
  is_available: 1,
  is_permanently_banned: 0
})
```

---

### 5.8 删除 Cookie

**接口:** `DELETE /admin/cookie/delete/{account_id}`

**参数:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| account_id | string | 是 | 账号 ID（路径参数） |

**请求示例:**
```javascript
axios.delete(`${API_BASE_URL}/admin/cookie/delete/account_001`)
```

---

### 5.9 解除封禁

**接口:** `POST /admin/cookie/unban/{id}`

**参数:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | number/string | 是 | Cookie ID（路径参数） |

**请求示例:**
```javascript
axios.post(`${API_BASE_URL}/admin/cookie/unban/123`)
```

---

### 5.10 临时封禁

**接口:** `POST /admin/cookie/ban/temporary/{account_id}`

**参数:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| account_id | string | 是 | 账号 ID（路径参数） |

**请求体:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| duration_minutes | number | 是 | 封禁时长（分钟） |

**请求示例:**
```javascript
axios.post(`${API_BASE_URL}/admin/cookie/ban/temporary/account_001`, {
  duration_minutes: 60
})
```

---

### 5.11 永久封禁

**接口:** `POST /admin/cookie/ban/permanent/{account_id}`

**参数:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| account_id | string | 是 | 账号 ID（路径参数） |

**请求示例:**
```javascript
axios.post(`${API_BASE_URL}/admin/cookie/ban/permanent/account_001`)
```

---

### 5.12 强制解封

**接口:** `POST /admin/cookie/force-unban/{account_id}`

**参数:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| account_id | string | 是 | 账号 ID（路径参数） |

**请求示例:**
```javascript
axios.post(`${API_BASE_URL}/admin/cookie/force-unban/account_001`)
```

---

### 5.13 更新账号 ID

**接口:** `PUT /admin/cookie/update-account/{old_account_id}`

**参数:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| old_account_id | string | 是 | 原账号 ID（路径参数） |

**请求体:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| new_account_id | string | 是 | 新账号 ID |

**请求示例:**
```javascript
axios.put(`${API_BASE_URL}/admin/cookie/update-account/old_account`, {
  new_account_id: "new_account"
})
```

---

### 5.14 同步 Cookie 到 Redis

**接口:** `POST /admin/cookie/sync-to-redis`

**参数:** 无

**请求示例:**
```javascript
axios.post(`${API_BASE_URL}/admin/cookie/sync-to-redis`)
```

---

### 5.15 更新平均封禁率和成功率

**接口:** `POST /admin/cookie/update-ab-sr`

**参数:** 无

**请求示例:**
```javascript
axios.post(`${API_BASE_URL}/admin/cookie/update-ab-sr`)
```

---

### 5.16 测试单个账号可用性

**接口:** `POST /admin/cookie/test-account-availability/{account_id}`

**参数:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| account_id | string | 是 | 账号 ID（路径参数） |

**请求示例:**
```javascript
axios.post(`${API_BASE_URL}/admin/cookie/test-account-availability/account_001`)
```

---

### 5.17 测试所有 Cookie 可用性

**接口:** `POST /admin/cookie/test-availability`

**参数:** 无

**请求示例:**
```javascript
axios.post(`${API_BASE_URL}/admin/cookie/test-availability`)
```

---

### 5.18 更新所有 Cookie 状态

**接口:** `POST /admin/cookie/update-status`

**参数:** 无

**请求示例:**
```javascript
axios.post(`${API_BASE_URL}/admin/cookie/update-status`)
```

---

### 5.19 清理过期 Cookie

**接口:** `POST /admin/cookie/cleanup-expired`

**参数:** 无

**请求示例:**
```javascript
axios.post(`${API_BASE_URL}/admin/cookie/cleanup-expired`)
```

---

## 6. 配置管理接口

### 6.1 获取配置列表

**接口:** `GET /config/list`

**参数:** 无

**请求示例:**
```javascript
request.get('/config/list')
```

---

### 6.2 批量保存配置

**接口:** `POST /config/batch_set`

**请求体:** 配置键值对对象

**请求示例:**
```javascript
request.post('/config/batch_set', {
  "spider_concurrent_requests": 16,
  "spider_download_delay": 0.5,
  "spider_retry_times": 3,
  "cookie_pool_size": 10
})
```

---

### 6.3 重置配置为默认值

**接口:** `POST /config/init_defaults`

**参数:** 无

**请求示例:**
```javascript
request.post('/config/init_defaults')
```

---

## 7. 区域数据接口

### 7.1 获取省份列表

**接口:** `GET /region/provinces`

**参数:** 无

**请求示例:**
```javascript
axios.get(`${apiBaseUrl}/region/provinces`)
```

**响应示例:**
```json
{
  "code": 10000,
  "data": [
    { "code": "110000", "name": "北京" },
    { "code": "310000", "name": "上海" },
    { "code": "440000", "name": "广东" }
  ]
}
```

---

### 7.2 获取省份-城市层级数据

**接口:** `GET /region/province/cities`

**参数:** 无

**请求示例:**
```javascript
axios.get(`${apiBaseUrl}/region/province/cities`)
```

**响应示例:**
```json
{
  "code": 10000,
  "data": [
    {
      "code": "440000",
      "name": "广东",
      "cities": [
        { "code": "440100", "name": "广州" },
        { "code": "440300", "name": "深圳" }
      ]
    }
  ]
}
```

---

## 8. 统计数据接口

### 8.1 获取爬虫统计

**接口:** `GET /statistics/spider_statistics`

**参数:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| date | string | 否 | 日期，格式 YYYY-MM-DD |
| taskType | string | 否 | 任务类型 |

**请求示例:**
```javascript
getSpiderStatistics({
  date: '2023-10-26',
  taskType: 'search_index'
})
```

---

### 8.2 获取任务统计

**接口:** `GET /statistics/task_statistics`

**参数:** 通用查询参数

**请求示例:**
```javascript
getTaskStatistics({
  status: 'completed'
})
```

---

### 8.3 获取仪表盘数据

**接口:** `GET /statistics/dashboard`

**参数（两种格式）:**

**格式一 - 预设天数:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| days | number | 是 | 最近 N 天 |

**格式二 - 自定义日期范围:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| start_date | string | 是 | 开始日期，格式 YYYY-MM-DD |
| end_date | string | 是 | 结束日期，格式 YYYY-MM-DD |

**请求示例 - 预设天数:**
```javascript
getDashboardData({ days: 30 })
```

**请求示例 - 自定义日期:**
```javascript
getDashboardData({
  start_date: '2023-01-01',
  end_date: '2023-01-31'
})
```

---

## 9. 关键词检查接口

### 9.1 检查关键词是否存在

**接口:** `POST /word-check/check`

**请求体:**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| words | string[] | 是 | 要检查的关键词列表 |

**请求示例:**
```javascript
axios.post(`${API_BASE_URL}/word-check/check`, {
  words: ["关键词1", "关键词2", "关键词3"]
})
```

**响应示例:**
```json
{
  "code": 10000,
  "data": {
    "valid": ["关键词1", "关键词2"],
    "invalid": ["关键词3"]
  }
}
```

---

## 10. WebSocket 事件

### 10.1 连接配置

```javascript
import { io } from 'socket.io-client'

const SOCKET_URL = 'http://127.0.0.1:5001'

const socket = io(SOCKET_URL, {
  transports: ['websocket', 'polling'],
  reconnection: true
})
```

### 10.2 事件类型

| 事件名 | 方向 | 说明 |
|--------|------|------|
| connect | 服务器→客户端 | 连接成功 |
| disconnect | 服务器→客户端 | 连接断开 |
| task_update | 服务器→客户端 | 任务状态更新 |

### 10.3 使用示例

```javascript
import webSocketService from '@/utils/websocket'

// 连接
webSocketService.connect()

// 监听任务更新
webSocketService.on('task_update', (data) => {
  console.log('任务更新:', data)
  // data 结构示例:
  // {
  //   task_id: "TASK-12345",
  //   status: "running",
  //   progress: 45,
  //   message: "正在采集..."
  // }
})

// 移除监听
webSocketService.off('task_update', handler)

// 断开连接
webSocketService.disconnect()
```

---

## 附录：响应格式说明

### 标准成功响应

```json
{
  "code": 10000,
  "message": "success",
  "data": { ... }
}
```

### 标准错误响应

```json
{
  "code": 40001,
  "message": "错误描述信息",
  "data": null
}
```

### 常见错误码

| 错误码 | 说明 |
|--------|------|
| 10000 | 成功 |
| 40001 | 参数错误 |
| 40003 | 资源不存在 |
| 50001 | 服务器内部错误 |

---

## 附录：任务类型枚举

| 任务类型值 | 说明 |
|------------|------|
| search_index | 搜索指数 |
| feed_index | 资讯指数 |
| word_graph | 需求图谱 |
| demographic_attributes | 人群属性 |
| interest_profile | 兴趣画像 |
| region_distribution | 地域分布 |

---

## 附录：设备类型枚举

| 值 | 说明 |
|----|------|
| all | 全部（PC + 移动） |
| pc | 仅 PC 端 |
| wise | 仅移动端 |

---

*文档生成时间: 2026-02-05*
