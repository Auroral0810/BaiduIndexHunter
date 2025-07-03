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
    url: '/api/statistics/spider_statistics',
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
    url: '/api/statistics/task_statistics',
    method: 'get',
    params
  })
} 