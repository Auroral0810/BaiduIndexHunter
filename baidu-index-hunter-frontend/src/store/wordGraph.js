import { defineStore } from 'pinia'
import request from '../utils/request'

/**
 * 需求图谱时间范围缓存 Store
 * 用于缓存从百度指数获取的需求图谱可用时间范围，避免重复请求
 */
export const useWordGraphStore = defineStore('wordGraph', {
    state: () => ({
        // 时间范围数据
        startDate: null,        // 格式: "YYYY-MM-DD"
        endDate: null,          // 格式: "YYYY-MM-DD"
        startDateRaw: null,     // 格式: "YYYYMMDD"
        endDateRaw: null,       // 格式: "YYYYMMDD"

        // 缓存控制
        fetchedAt: 0,         // 上次获取时间戳（0表示未获取）
        cacheMaxAge: 21600000,  // 缓存有效期：6小时（毫秒）

        // 加载状态
        loading: false,
        error: ''  // 错误信息，空字符串表示无错误
    }),

    getters: {
        /**
         * 检查缓存是否有效
         */
        isCacheValid: (state) => {
            if (!state.startDate || !state.endDate || state.fetchedAt === 0) {
                return false
            }
            const now = Date.now()
            return (now - state.fetchedAt) < state.cacheMaxAge
        },

        /**
         * 获取格式化的时间范围
         */
        getTimeRange: (state) => ({
            startDate: state.startDate,
            endDate: state.endDate,
            startDateRaw: state.startDateRaw,
            endDateRaw: state.endDateRaw
        }),

        /**
         * 生成周选择列表
         * 从 startDate 开始，每隔7天生成一个可选日期，直到 endDate
         * 显示格式：周开始日期 ~ 周结束日期
         */
        getWeeklyDates: (state) => {
            if (!state.startDate || !state.endDate) {
                return []
            }

            const dates = []
            const start = new Date(state.startDate)
            const end = new Date(state.endDate)

            let current = new Date(start)
            while (current <= end) {
                // 格式化为 YYYYMMDD (作为值)
                const year = current.getFullYear()
                const month = String(current.getMonth() + 1).padStart(2, '0')
                const day = String(current.getDate()).padStart(2, '0')
                const dateRaw = `${year}${month}${day}`
                const dateFormatted = `${year}-${month}-${day}`

                // 计算这周的结束日期 (开始日期 + 6天)
                const weekEnd = new Date(current)
                weekEnd.setDate(weekEnd.getDate() + 6)
                const endYear = weekEnd.getFullYear()
                const endMonth = String(weekEnd.getMonth() + 1).padStart(2, '0')
                const endDay = String(weekEnd.getDate()).padStart(2, '0')
                const weekEndFormatted = `${endYear}-${endMonth}-${endDay}`

                // 显示格式：起始日期 ~ 结束日期
                const label = `${dateFormatted} ~ ${weekEndFormatted}`

                dates.push({
                    value: dateRaw,
                    label: label
                })

                // 下一周
                current.setDate(current.getDate() + 7)
            }

            return dates
        }
    },

    actions: {
        /**
         * 获取时间范围（带缓存）
         */
        async fetchTimeRange(forceRefresh = false) {
            // 如果缓存有效且不强制刷新，直接返回
            if (this.isCacheValid && !forceRefresh) {
                return this.getTimeRange
            }

            this.loading = true
            this.error = ''

            try {
                const response = await request.get('/word-graph/time-range')

                // 更新状态
                this.startDate = response.data.startDate
                this.endDate = response.data.endDate
                this.startDateRaw = response.data.startDateRaw
                this.endDateRaw = response.data.endDateRaw
                this.fetchedAt = Date.now()

                return this.getTimeRange
            } catch (err) {
                const errorMessage = err instanceof Error ? err.message : '获取时间范围失败'
                console.error('获取需求图谱时间范围失败:', err)
                this.error = errorMessage
                throw err
            } finally {
                this.loading = false
            }
        },

        /**
         * 清除缓存
         */
        clearCache() {
            this.startDate = null
            this.endDate = null
            this.startDateRaw = null
            this.endDateRaw = null
            this.fetchedAt = 0
            this.error = ''
        }
    }
})
