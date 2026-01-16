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
 * 获取大屏展示数据
 * @param {Object} params 查询参数
 * @param {number} params.days 统计天数，默认30天
 * @returns {Promise} 请求Promise
 */
export function getDashboardData(params) {
  return request({
    url: '/statistics/dashboard',
    method: 'get',
    params
  })
} 