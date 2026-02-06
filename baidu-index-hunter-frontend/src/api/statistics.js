import request from '@/utils/request'

/**
 * 获取爬虫统计数据
 * @param {Object} params 查询参数
 * @param {string} params.date 日期（格式：YYYY-MM-DD）
 * @param {string} params.taskType 任务类型
 * @returns {Promise} 请求Promise
 */
export function getSpiderStatistics(params) {
  return request({
    url: '/statistics/spider_statistics',
    method: 'get',
    params
  })
}

/**
 * 获取任务统计数据
 * @param {Object} params 查询参数
 * @returns {Promise} 请求Promise
 */
export function getTaskStatistics(params) {
  return request({
    url: '/statistics/task_statistics',
    method: 'get',
    params
  })
}

/**
 * 获取关键词统计数据
 * @param {Object} params 查询参数
 * @param {string} params.task_id 任务ID (可选)
 * @param {number} params.limit 限制数量，默认20
 * @returns {Promise} 请求Promise
 */
export function getKeywordStatistics(params) {
  return request({
    url: '/statistics/keyword_statistics',
    method: 'get',
    params
  })
}

/**
 * 获取城市统计数据
 * @param {Object} params 查询参数
 * @param {string} params.city_name 城市名称 (可选)
 * @param {string} params.task_type 任务类型 (可选)
 * @param {number} params.limit 限制数量，默认100
 * @returns {Promise} 请求Promise
 */
export function getCityStatistics(params) {
  return request({
    url: '/statistics/city_statistics',
    method: 'get',
    params
  })
}

/**
 * 获取大屏展示数据
 * @param {Object} params 查询参数
 * @param {number} params.days 统计天数，默认30天
 * @param {string} params.start_date 开始日期
 * @param {string} params.end_date 结束日期
 * @returns {Promise} 请求Promise
 */
export function getDashboardData(params) {
  return request({
    url: '/statistics/dashboard',
    method: 'get',
    params
  })
} 