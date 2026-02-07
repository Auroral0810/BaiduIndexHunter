import axios from 'axios'
import { ElMessage } from 'element-plus'
import { apiBaseUrl } from '@/config/api'

/** API 密钥 localStorage 键名（用于存储用户在设置中填写的密钥） */
const API_KEY_STORAGE_KEY = 'baidu_index_hunter_api_key'

/**
 * 获取 API 密钥（优先级：环境变量 > localStorage）
 * 在项目根目录 .env 中配置 VITE_API_SECRET_KEY 可与后端 API_SECRET_KEY 保持一致，一次配置永久生效
 */
export function getApiSecretKey() {
  const envKey = import.meta.env.VITE_API_SECRET_KEY
  if (envKey && typeof envKey === 'string' && envKey.trim()) {
    return envKey.trim()
  }
  try {
    return localStorage.getItem(API_KEY_STORAGE_KEY) || ''
  } catch {
    return ''
  }
}

/** 设置 API 密钥 */
export function setApiSecretKey(key) {
  try {
    if (key) {
      localStorage.setItem(API_KEY_STORAGE_KEY, String(key).trim())
    } else {
      localStorage.removeItem(API_KEY_STORAGE_KEY)
    }
    return true
  } catch {
    return false
  }
}

/** 为 axios 添加鉴权头的拦截器 */
function addAuthInterceptor(instance) {
  instance.interceptors.request.use(
    config => {
      const apiKey = getApiSecretKey()
      if (apiKey) {
        config.headers = config.headers || {}
        config.headers.Authorization = `Bearer ${apiKey}`
      }
      return config
    },
    err => Promise.reject(err)
  )
}

// 为全局 axios 默认实例添加鉴权头（CookieManager、TaskList、DataCollection 等使用原生 axios）
addAuthInterceptor(axios)

// 创建axios实例
const service = axios.create({
  baseURL: apiBaseUrl,
  timeout: 30000, // 请求超时时间
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器（鉴权头由 addAuthInterceptor 统一处理）
addAuthInterceptor(service)

// 响应拦截器
service.interceptors.response.use(
  response => {
    const res = response.data
    
    // 如果返回的状态码不是10000，则判断为错误
    if (res.code !== 10000) {
      ElMessage({
        message: res.msg || '系统错误',
        type: 'error',
        duration: 5 * 1000
      })
      
      return Promise.reject(new Error(res.msg || '系统错误'))
    } else {
      return res
    }
  },
  error => {
    console.error('响应错误:', error)
    const msg = error?.response?.data?.msg || error.message || '网络错误，请稍后重试'
    if (error?.response?.status === 401) {
      ElMessage({
        message: msg + '，请在设置中配置正确的 API 密钥',
        type: 'warning',
        duration: 5 * 1000
      })
    } else {
      ElMessage({
        message: msg,
        type: 'error',
        duration: 5 * 1000
      })
    }
    return Promise.reject(error)
  }
)

export default service 