/**
 * 统一 API 地址配置
 * 通过环境变量 VITE_API_BASE_URL、VITE_SOCKET_URL 配置，避免硬编码
 * 未设置时：开发环境使用 Vite 代理 /api，WebSocket 指向同主机 5001 端口
 */
const envApi = import.meta.env.VITE_API_BASE_URL
const envSocket = import.meta.env.VITE_SOCKET_URL

/** REST API 基础地址，如 '/api' 或 'http://127.0.0.1:5001/api' */
export const apiBaseUrl = envApi ?? '/api'

/** WebSocket 服务地址，如 'http://127.0.0.1:5001' */
export function getSocketUrl() {
  if (envSocket) return envSocket
  if (typeof window === 'undefined') return 'http://127.0.0.1:5001'
  if (import.meta.env.DEV && window.location.port === '5173') {
    return `${window.location.protocol}//${window.location.hostname}:5001`
  }
  return window.location.origin
}
export const socketUrl = getSocketUrl()

/** 后端服务根地址（用于 fetch 等需要完整 URL 的场景，如 DirPicker） */
export function getApiBase() {
  if (envApi && envApi.startsWith('http')) return envApi.replace(/\/api\/?$/, '')
  if (envSocket) return envSocket
  if (typeof window === 'undefined') return 'http://127.0.0.1:5001'
  if (import.meta.env.DEV && window.location.port === '5173') {
    return `${window.location.protocol}//${window.location.hostname}:5001`
  }
  return window.location.origin
}
export const apiBase = getApiBase()
