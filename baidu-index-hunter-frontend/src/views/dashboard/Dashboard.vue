<!-- 数据大屏展示页面 -->
<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <h1 class="dashboard-title">{{ t('dashboard.title') }}</h1>
      <div class="dashboard-filters">
        <el-select v-model="selectedTaskType" :placeholder="t('dashboard.selectTaskType')" @change="handleTaskTypeChange" class="task-type-select">
          <el-option :label="t('dashboard.allStats')" value="all" />
          <el-option v-for="type in taskTypes" :key="type" :label="formatTaskType(type)" :value="type" />
        </el-select>
        <el-select v-model="selectedDays" :placeholder="t('dashboard.selectPeriod')" @change="handleDaysChange" class="time-select">
          <el-option :label="t('dashboard.periods.last24h')" :value="1" />
          <el-option :label="t('dashboard.periods.last3d')" :value="3" />
          <el-option :label="t('dashboard.periods.last7d')" :value="7" />
          <el-option :label="t('dashboard.periods.last30d')" :value="30" />
          <el-option :label="t('dashboard.periods.last90d')" :value="90" />
          <el-option :label="t('dashboard.periods.last180d')" :value="180" />
          <el-option :label="t('dashboard.periods.last365d')" :value="365" />
          <el-option :label="t('dashboard.periods.allTime')" :value="-1" />
          <el-option :label="t('dashboard.periods.custom')" value="custom" />
        </el-select>
        
        <el-date-picker
          v-if="selectedDays === 'custom'"
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          @change="loadDashboardData"
          class="date-range-picker"
        />
        
        <el-button type="primary" @click="loadDashboardData">{{ t('common.refresh') }}</el-button>
      </div>
    </div>

    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="dashboard-card overview-card">
          <template #header>
            <div class="card-header">
              <span>{{ selectedTaskType === 'all' ? '总体统计' : formatTaskType(selectedTaskType) + ' 统计' }}</span>
            </div>
          </template>
          <div class="overview-stats">
            <div class="stat-item">
              <div class="stat-value">{{ formatNumber(currentStats.total_tasks || 0) }}</div>
              <div class="stat-label">{{ t('dashboard.stats.totalTasks') }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ formatNumber(currentStats.completed_tasks || 0) }}</div>
              <div class="stat-label">{{ t('dashboard.stats.completedTasks') }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ formatNumber(currentStats.failed_tasks || 0) }}</div>
              <div class="stat-label">{{ t('dashboard.stats.failedTasks') }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ formatNumber(currentStats.total_items || 0) }}</div>
              <div class="stat-label">{{ t('dashboard.stats.totalItems') }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ formatNumber(currentStats.total_crawled_items || 0) }}</div>
              <div class="stat-label">{{ t('dashboard.stats.crawledItems') }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ formatNumber(currentStats.success_rate || 0, 2) }}%</div>
              <div class="stat-label">{{ t('dashboard.stats.successRate') }}</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ formatNumber(currentStats.avg_duration || 0, 2) }}s</div>
              <div class="stat-label">{{ t('dashboard.stats.avgDuration') }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card class="dashboard-card">
          <template #header>
            <div class="card-header">
              <span>{{ t('dashboard.charts.taskTrend') }}</span>
            </div>
          </template>
          <div ref="taskTrendChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="dashboard-card">
          <template #header>
            <div class="card-header">
              <span>{{ t('dashboard.charts.dataTrend') }}</span>
            </div>
          </template>
          <div ref="dataTrendChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="8">
        <el-card class="dashboard-card">
          <template #header>
            <div class="card-header">
              <span>{{ t('dashboard.charts.successRate') }}</span>
            </div>
          </template>
          <div ref="successRateChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="dashboard-card">
          <template #header>
            <div class="card-header">
              <span>{{ t('dashboard.charts.avgDuration') }}</span>
            </div>
          </template>
          <div ref="avgDurationChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="dashboard-card">
          <template #header>
            <div class="card-header">
              <span>{{ t('dashboard.charts.dataVolume') }}</span>
            </div>
          </template>
          <div ref="dataVolumeChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, nextTick, computed } from 'vue'
import { getDashboardData } from '@/api/statistics'
import { ElMessage } from 'element-plus'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'

const { t } = useI18n()

// 任务类型映射 - 使用国际化
const getTaskTypeMap = () => ({
  'search_index': t('dataCollection.tabs.searchIndex'),
  'feed_index': t('dataCollection.tabs.feedIndex'),
  'word_graph': t('dataCollection.tabs.wordGraph'),
  'region_distribution': t('dataCollection.tabs.regionDistribution'),
  'demographic_attributes': t('dataCollection.tabs.demographicAttributes'),
  'interest_profile': t('dataCollection.tabs.interestProfile')
})

// 格式化任务类型
const formatTaskType = (type) => {
  return getTaskTypeMap()[type] || type
}

// 格式化数字
const formatNumber = (num, decimals = 0) => {
  if (num === null || num === undefined) return '0'
  return Number(num).toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

// 状态定义
const selectedTaskType = ref('all')
const selectedDays = ref(30)
const dateRange = ref([])
const taskTypes = ref([])
const dashboardData = reactive({
  overall: {},
  by_task_type: [],
  daily_trend: [],
  task_type_trends: {},
  success_rate_comparison: [],
  avg_duration_comparison: [],
  data_volume_comparison: []
})
const currentStats = reactive({})

// 图表引用
const taskTrendChart = ref(null)
const dataTrendChart = ref(null)
const successRateChart = ref(null)
const avgDurationChart = ref(null)
const dataVolumeChart = ref(null)

// 图表实例
let taskTrendChartInstance = null
let dataTrendChartInstance = null
let successRateChartInstance = null
let avgDurationChartInstance = null
let dataVolumeChartInstance = null

// 加载大屏数据
const loadDashboardData = async () => {
  try {
    const params = {}
    
    if (selectedDays.value === 'custom') {
      if (dateRange.value && dateRange.value.length === 2) {
        params.start_date = dateRange.value[0]
        params.end_date = dateRange.value[1]
      } else {
        // 如果选择了自定义但没有选日期，默认显示最近30天
        params.days = 30
      }
    } else {
      params.days = selectedDays.value
    }
    
    const res = await getDashboardData(params)
    if (res.code === 10000) {
      // 更新数据
      Object.assign(dashboardData, res.data)
      taskTypes.value = res.data.task_types || []
      
      // 更新当前统计数据
      updateCurrentStats()
      
      // 初始化或更新图表
      nextTick(() => {
        initCharts()
      })
    } else {
      ElMessage.error(res.msg || '获取大屏数据失败')
    }
  } catch (error) {
    console.error('加载大屏数据失败:', error)
    ElMessage.error('加载大屏数据失败')
  }
}

// 处理统计周期变更
const handleDaysChange = (val) => {
  if (val !== 'custom') {
    dateRange.value = [] // 清空自定义日期
    loadDashboardData()
  }
  // 如果是 custom，等待用户选择日期后再加载，或者用户手动点击刷新
}

// 更新当前统计数据
const updateCurrentStats = () => {
  if (selectedTaskType.value === 'all') {
    Object.assign(currentStats, dashboardData.overall || {})
  } else {
    const taskStats = dashboardData.by_task_type.find(item => item.task_type === selectedTaskType.value)
    Object.assign(currentStats, taskStats || {})
  }
}

// 处理任务类型变更
const handleTaskTypeChange = () => {
  updateCurrentStats()
  initCharts()
}

// 初始化图表
const initCharts = () => {
  initTaskTrendChart()
  initDataTrendChart()
  initSuccessRateChart()
  initAvgDurationChart()
  initDataVolumeChart()
}

// 初始化任务执行趋势图表
const initTaskTrendChart = () => {
  if (!taskTrendChart.value) return
  
  if (!taskTrendChartInstance) {
    taskTrendChartInstance = echarts.init(taskTrendChart.value)
  }
  
  let dates = []
  let totalTasks = []
  let completedTasks = []
  let failedTasks = []
  
  if (selectedTaskType.value === 'all') {
    // 使用总体趋势数据
    dates = dashboardData.daily_trend.map(item => item.stat_date)
    totalTasks = dashboardData.daily_trend.map(item => item.total_tasks)
    completedTasks = dashboardData.daily_trend.map(item => item.completed_tasks)
    failedTasks = dashboardData.daily_trend.map(item => item.failed_tasks)
  } else {
    // 使用特定任务类型的趋势数据
    const trendData = dashboardData.task_type_trends[selectedTaskType.value] || []
    dates = trendData.map(item => item.stat_date)
    totalTasks = trendData.map(item => item.total_tasks)
    completedTasks = trendData.map(item => item.completed_tasks)
    failedTasks = trendData.map(item => item.failed_tasks)
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['总任务数', '完成任务', '失败任务']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '总任务数',
        type: 'line',
        data: totalTasks,
        smooth: true,
        lineStyle: {
          width: 3
        }
      },
      {
        name: '完成任务',
        type: 'line',
        data: completedTasks,
        smooth: true,
        lineStyle: {
          width: 3
        }
      },
      {
        name: '失败任务',
        type: 'line',
        data: failedTasks,
        smooth: true,
        lineStyle: {
          width: 3
        }
      }
    ]
  }
  
  taskTrendChartInstance.setOption(option)
}

// 初始化数据爬取趋势图表
const initDataTrendChart = () => {
  if (!dataTrendChart.value) return
  
  if (!dataTrendChartInstance) {
    dataTrendChartInstance = echarts.init(dataTrendChart.value)
  }
  
  let dates = []
  let totalItems = []
  let crawledItems = []
  
  if (selectedTaskType.value === 'all') {
    // 使用总体趋势数据
    dates = dashboardData.daily_trend.map(item => item.stat_date)
    totalItems = dashboardData.daily_trend.map(item => item.total_items)
    crawledItems = dashboardData.daily_trend.map(item => item.total_crawled_items)
  } else {
    // 使用特定任务类型的趋势数据
    const trendData = dashboardData.task_type_trends[selectedTaskType.value] || []
    dates = trendData.map(item => item.stat_date)
    totalItems = trendData.map(item => item.total_items)
    crawledItems = trendData.map(item => item.total_crawled_items)
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    legend: {
      data: ['数据总量', '爬取条数']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: dates
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '数据总量',
        type: 'bar',
        data: totalItems
      },
      {
        name: '爬取条数',
        type: 'bar',
        data: crawledItems
      }
    ]
  }
  
  dataTrendChartInstance.setOption(option)
}

// 初始化任务成功率对比图表
const initSuccessRateChart = () => {
  if (!successRateChart.value) return
  
  if (!successRateChartInstance) {
    successRateChartInstance = echarts.init(successRateChart.value)
  }
  
  const taskTypes = dashboardData.success_rate_comparison.map(item => formatTaskType(item.task_type))
  const successRates = dashboardData.success_rate_comparison.map(item => item.success_rate)
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}%'
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: '#fff',
          borderWidth: 2
        },
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: '18',
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: taskTypes.map((name, index) => ({
          name,
          value: successRates[index]
        }))
      }
    ]
  }
  
  successRateChartInstance.setOption(option)
}

// 初始化平均执行时间对比图表
const initAvgDurationChart = () => {
  if (!avgDurationChart.value) return
  
  if (!avgDurationChartInstance) {
    avgDurationChartInstance = echarts.init(avgDurationChart.value)
  }
  
  const taskTypes = dashboardData.avg_duration_comparison.map(item => formatTaskType(item.task_type))
  const durations = dashboardData.avg_duration_comparison.map(item => item.avg_duration)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: '{b}: {c}秒'
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}秒'
      }
    },
    yAxis: {
      type: 'category',
      data: taskTypes
    },
    series: [
      {
        type: 'bar',
        data: durations
      }
    ]
  }
  
  avgDurationChartInstance.setOption(option)
}

// 初始化数据爬取量对比图表
const initDataVolumeChart = () => {
  if (!dataVolumeChart.value) return
  
  if (!dataVolumeChartInstance) {
    dataVolumeChartInstance = echarts.init(dataVolumeChart.value)
  }
  
  const taskTypes = dashboardData.data_volume_comparison.map(item => formatTaskType(item.task_type))
  const volumes = dashboardData.data_volume_comparison.map(item => item.total_crawled_items)
  
  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    series: [
      {
        type: 'pie',
        radius: '70%',
        center: ['50%', '50%'],
        data: taskTypes.map((name, index) => ({
          name,
          value: volumes[index]
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }
  
  dataVolumeChartInstance.setOption(option)
}

// 监听窗口大小变化，调整图表大小
window.addEventListener('resize', () => {
  if (taskTrendChartInstance) taskTrendChartInstance.resize()
  if (dataTrendChartInstance) dataTrendChartInstance.resize()
  if (successRateChartInstance) successRateChartInstance.resize()
  if (avgDurationChartInstance) avgDurationChartInstance.resize()
  if (dataVolumeChartInstance) dataVolumeChartInstance.resize()
})

// 监听任务类型变化，更新当前显示数据和图表
watch(selectedTaskType, () => {
  updateCurrentStats()
  nextTick(() => {
    initCharts()
  })
})

// 页面加载时获取数据
onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.dashboard-container {
  padding: 0 0 20px 0;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  background: var(--bg-card);
  padding: 24px 32px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

.dashboard-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.dashboard-title::before {
  content: '';
  display: block;
  width: 4px;
  height: 24px;
  background: var(--primary-gradient);
  border-radius: 2px;
}

.dashboard-filters {
  display: flex;
  gap: 16px;
  align-items: center;
}

.dashboard-filters .task-type-select {
  width: 160px;
}

.dashboard-filters .time-select {
  width: 140px;
}

.date-range-picker {
  width: 260px !important;
}

:deep(.el-select .el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--border-color) inset !important;
  border-radius: var(--radius-md);
  padding: 4px 12px;
}

:deep(.el-select .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--primary-color) inset !important;
}

:deep(.el-button) {
  border-radius: var(--radius-md);
  padding: 8px 20px;
  font-weight: 500;
}

/* 统计卡片区域 */
.overview-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
}

.stat-item {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow-sm);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.stat-item:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
}

/* 为每个统计项设置不同的强调色 */
.stat-item:nth-child(1) { --accent-color: #3b82f6; } /* 蓝色 */
.stat-item:nth-child(2) { --accent-color: #10b981; } /* 绿色 */
.stat-item:nth-child(3) { --accent-color: #ef4444; } /* 红色 */
.stat-item:nth-child(4) { --accent-color: #8b5cf6; } /* 紫色 */
.stat-item:nth-child(5) { --accent-color: #f59e0b; } /* 橙色 */
.stat-item:nth-child(6) { --accent-color: #06b6d4; } /* 青色 */
.stat-item:nth-child(7) { --accent-color: #ec4899; } /* 粉色 */

.stat-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background-color: var(--accent-color);
  opacity: 0.8;
}

.stat-item::after {
  content: '';
  position: absolute;
  top: -10%;
  right: -10%;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background-color: var(--accent-color);
  opacity: 0.05;
  z-index: 0;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
  position: relative;
  z-index: 1;
  font-family: 'Inter', sans-serif;
  letter-spacing: -1px;
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-weight: 500;
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 图表区域 */
.chart-row {
  margin-bottom: 24px;
}

.dashboard-card {
  background: var(--bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
  height: 100%;
  transition: box-shadow 0.3s ease;
}

.dashboard-card:hover {
  box-shadow: var(--shadow-md);
}

:deep(.el-card__header) {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color);
}

:deep(.el-card__body) {
  padding: 24px;
}

.card-header {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
}

.chart-container {
  height: 380px;
  width: 100%;
}

/* 响应式适配 */
@media screen and (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
    padding: 20px;
  }
  
  .dashboard-filters {
    width: 100%;
    flex-wrap: wrap;
  }
  
  .dashboard-filters .el-select {
    flex: 1;
    min-width: 120px;
  }

  .overview-stats {
    grid-template-columns: 1fr 1fr;
  }
  
  .chart-container {
    height: 300px;
  }
}

@media screen and (max-width: 480px) {
  .overview-stats {
    grid-template-columns: 1fr;
  }
}
</style> 