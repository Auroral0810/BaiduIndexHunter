<!-- 数据大屏展示页面 -->
<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <h1 class="dashboard-title">百度指数爬虫数据大屏</h1>
      <div class="dashboard-filters">
        <el-select v-model="selectedTaskType" placeholder="选择任务类型" @change="handleTaskTypeChange">
          <el-option label="全部统计" value="all" />
          <el-option v-for="type in taskTypes" :key="type" :label="formatTaskType(type)" :value="type" />
        </el-select>
        <el-select v-model="selectedDays" placeholder="统计周期" @change="loadDashboardData">
          <el-option label="最近7天" :value="7" />
          <el-option label="最近30天" :value="30" />
          <el-option label="最近90天" :value="90" />
        </el-select>
        <el-button type="primary" @click="loadDashboardData">刷新数据</el-button>
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
              <div class="stat-label">总任务数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ formatNumber(currentStats.completed_tasks || 0) }}</div>
              <div class="stat-label">完成任务</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ formatNumber(currentStats.failed_tasks || 0) }}</div>
              <div class="stat-label">失败任务</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ formatNumber(currentStats.total_items || 0) }}</div>
              <div class="stat-label">数据总量</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ formatNumber(currentStats.total_crawled_items || 0) }}</div>
              <div class="stat-label">爬取条数</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ formatNumber(currentStats.success_rate || 0, 2) }}%</div>
              <div class="stat-label">成功率</div>
            </div>
            <div class="stat-item">
              <div class="stat-value">{{ formatNumber(currentStats.avg_duration || 0, 2) }}s</div>
              <div class="stat-label">平均耗时</div>
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
              <span>任务执行趋势</span>
            </div>
          </template>
          <div ref="taskTrendChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card class="dashboard-card">
          <template #header>
            <div class="card-header">
              <span>数据爬取趋势</span>
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
              <span>任务成功率对比</span>
            </div>
          </template>
          <div ref="successRateChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="dashboard-card">
          <template #header>
            <div class="card-header">
              <span>平均执行时间对比</span>
            </div>
          </template>
          <div ref="avgDurationChart" class="chart-container"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="dashboard-card">
          <template #header>
            <div class="card-header">
              <span>数据爬取量对比</span>
            </div>
          </template>
          <div ref="dataVolumeChart" class="chart-container"></div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, nextTick } from 'vue'
import { getDashboardData } from '@/api/statistics'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'

// 任务类型映射
const taskTypeMap = {
  'search_index': '搜索指数',
  'feed_index': '资讯指数',
  'word_graph': '需求图谱',
  'region_distribution': '地域分布',
  'demographic_attributes': '人群属性',
  'interest_profile': '兴趣分布'
}

// 格式化任务类型
const formatTaskType = (type) => {
  return taskTypeMap[type] || type
}

// 格式化数字
const formatNumber = (num, decimals = 0) => {
  if (num === null || num === undefined) return '0'
  return Number(num).toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ',')
}

// 状态定义
const selectedTaskType = ref('all')
const selectedDays = ref(30)
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
    const res = await getDashboardData({ days: selectedDays.value })
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

// 监听任务类型和统计天数变化
watch([selectedTaskType, selectedDays], () => {
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
  padding: 20px;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.dashboard-title {
  font-size: 24px;
  color: var(--text-primary);
  margin: 0;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.dashboard-filters {
  display: flex;
  gap: 10px;
}

.dashboard-card {
  margin-bottom: 20px;
  box-shadow: var(--shadow-light);
  transition: all 0.3s ease;
}

.dashboard-card:hover {
  box-shadow: var(--shadow-hover);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-row {
  margin-top: 20px;
}

.chart-container {
  height: 350px;
  width: 100%;
}

.overview-card {
  background: linear-gradient(to right, #f6f9fc, #f0f9ff);
}

.overview-stats {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 20px;
}

.stat-item {
  flex: 1;
  min-width: 120px;
  text-align: center;
  padding: 20px 10px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--primary-color);
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
}

@media screen and (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .dashboard-filters {
    width: 100%;
    flex-wrap: wrap;
  }
  
  .overview-stats {
    flex-direction: column;
  }
  
  .stat-item {
    width: 100%;
  }
  
  .chart-container {
    height: 250px;
  }
}
</style> 