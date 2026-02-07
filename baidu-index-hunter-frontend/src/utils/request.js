import axios from 'axios'
import { ElMessage } from 'element-plus'
import { apiBaseUrl } from '@/config/api'

// 创建axios实例
const service = axios.create({
  baseURL: apiBaseUrl,
  timeout: 30000, // 请求超时时间
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    // 在发送请求之前做一些处理
    return config
  },
  error => {
    // 处理请求错误
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

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
    ElMessage({
      message: error.message || '网络错误，请稍后重试',
      type: 'error',
      duration: 5 * 1000
    })
    return Promise.reject(error)
  }
)

export default service 