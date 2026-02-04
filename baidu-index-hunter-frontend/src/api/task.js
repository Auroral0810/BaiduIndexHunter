import request from '@/utils/request'

/**
 * 获取任务列表
 * @param {Object} params 查询参数
 * @returns {Promise} 请求Promise
 */
export function getTaskList(params) {
    return request({
        url: '/task/list',
        method: 'get',
        params
    })
}

/**
 * 获取任务详情
 * @param {string} taskId 任务ID
 * @returns {Promise} 请求Promise
 */
export function getTaskDetail(taskId) {
    return request({
        url: `/task/${taskId}`,
        method: 'get'
    })
}
