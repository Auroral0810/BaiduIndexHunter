<template>
  <div class="overview-wrapper">
    <!-- Filters (Localized Premium) -->
    <div class="dashboard-filter-bar glass-panel">
      <div class="filter-controls">
        <div class="control-item">
          <el-select v-model="selectedTaskType" class="premium-select" @change="handleTaskTypeChange">
            <el-option :label="$t('dashboard.dashboard.o0v3d0')" value="all" />
            <el-option v-for="type in taskTypes" :key="type" :label="$t(`task.type.${type}`)" :value="type" />
          </el-select>
        </div>
        <div class="control-item">
          <el-select v-model="selectedDays" class="premium-select days-select" @change="handleDaysChange">
            <el-option :label="$t('dashboard.dashboard.22s42m')" :value="1" />
            <el-option :label="$t('dashboard.dashboard.bl75nm')" :value="3" />
            <el-option :label="$t('dashboard.dashboard.2a174n')" :value="7" />
            <el-option :label="$t('dashboard.dashboard.zk61g6')" :value="30" />
            <el-option :label="$t('dashboard.dashboard.o64878')" :value="-1" />
            <el-option :label="$t('dashboard.dashboard.tt8075')" value="custom" />
          </el-select>
        </div>
        <el-date-picker
          v-if="selectedDays === 'custom'"
          v-model="dateRange"
          type="daterange"
          class="premium-date-picker"
          @change="loadDashboardData"
          value-format="YYYY-MM-DD"
        />
        <el-button class="refresh-action" @click="loadDashboardData" :loading="statusLoading" circle>
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <div class="dashboard-grid">
      <!-- Left Column: KPIs and Main Trend -->
      <div class="main-content">
        <!-- KPI Row -->
        <div class="kpi-container">
          <div v-for="(stat, index) in metricStats" :key="index" class="kpi-card glass-panel" :style="{'--accent': stat.color}">
            <div class="kpi-icon">
              <el-icon><component :is="stat.icon" /></el-icon>
            </div>
            <div class="kpi-info">
              <span class="kpi-label">{{ stat.label }}</span>
              <div class="kpi-value-row">
                <span class="kpi-value">{{ stat.formattedValue }}</span>
              </div>
            </div>
            <div class="kpi-chart" :ref="el => setSparklineRef(el, index)"></div>
          </div>
        </div>

        <!-- Central Trend Chart -->
        <div class="trend-section glass-panel">
          <div class="panel-header">
            <h3 class="panel-title">{{ $t('dashboard.dashboard.execution_trends') }}</h3>
            <div class="panel-actions">
              <el-radio-group v-model="trendMode" size="small" class="premium-radio">
                <el-radio-button value="task">{{ $t('dashboard.dashboard.total_tasks') }}</el-radio-button>
                <el-radio-button value="success">{{ $t('dashboard.dashboard.crawled_items') }}</el-radio-button>
              </el-radio-group>
            </div>
          </div>
          <div ref="mainChartRef" class="main-echart"></div>
        </div>

        <!-- Bottom Insights -->
        <div class="insights-grid">
          <div class="insight-card glass-panel">
            <h4 class="insight-title">{{ $t('dashboard.dashboard.success_comparison') }}</h4>
            <div ref="distributionChartRef" class="insight-echart"></div>
          </div>
          <div class="insight-card glass-panel">
            <h4 class="insight-title">{{ $t('dashboard.dashboard.duration_comparison') }}</h4>
            <div ref="durationChartRef" class="insight-echart"></div>
          </div>
          <div class="insight-card glass-panel">
            <h4 class="insight-title">{{ $t('dashboard.dashboard.volume_comparison') }}</h4>
            <div ref="volumeChartRef" class="insight-echart"></div>
          </div>
        </div>
      </div>

      <!-- Right Column: Real-time Terminal -->
      <aside class="activity-terminal glass-panel">
        <div class="panel-header">
          <h3 class="panel-title">{{ $t('tasks-TaskList-19c298d949224c78d-1') }}</h3>
          <span class="terminal-badge">{{ $t('dashboard.dashboard.logs_badge') }}</span>
        </div>
        <div class="terminal-body" ref="terminalBody">
          <div v-if="recentTasks.length === 0" class="terminal-empty">
            {{ $t('dashboard.dashboard.waiting_data') }}
          </div>
          <transition-group name="terminal-list">
            <div v-for="task in recentTasks" :key="task.taskId" class="terminal-line">
              <span class="timestamp">[{{ formatTime(task.createdAt) }}]</span>
              <span class="task-type">{{ $t(`task.type.${task.taskType}`) || task.taskType }}</span>
              <span class="task-id">{{ task.taskId.slice(0, 8) }}</span>
              <span class="task-status" :class="task.status">{{ task.status.toUpperCase() }}</span>
              <div class="progress-mini" v-if="task.status === 'running'">
                <div class="progress-bar" :style="{width: task.progress + '%'}"></div>
              </div>
            </div>
          </transition-group>
        </div>
        <div class="terminal-footer">
          <div class="system-stats">
            <span>{{ $t('dashboard.dashboard.data_packets') }}: {{ recentTasks.length }}</span>
            <span>{{ $t('dashboard.dashboard.ws_status') }}: <span class="ws-indicator" :class="{active: wsConnected}"></span></span>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick, computed, watch, markRaw } from 'vue'
import { getDashboardData } from '@/api/statistics'
import { getTaskList } from '@/api/task'
import { webSocketService } from '@/utils/websocket'
import { ElMessage } from 'element-plus'
import { 
  TrendCharts, 
  Refresh, 
  List, 
  CircleCheck, 
  CircleClose,
  Warning, 
  Timer, 
  Connection,
  Promotion,
  DataAnalysis
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/store/app'

const { t: $t, locale } = useI18n()
const appStore = useAppStore()
const isDark = computed(() => appStore.theme === 'dark')

// --- State Management ---
const selectedTaskType = ref('all')
const selectedDays = ref(30)
const dateRange = ref([])
// Use static list or fetch from API. The original fetched from API but now we want to support i18n
// The API returns 'task_types' list.
const taskTypes = ref([]) 
const trendMode = ref('task')
const statusLoading = ref(false)
const wsConnected = ref(false)

const dashboardData = reactive({
  overall: {},
  by_task_type: [],
  daily_trend: [],
  task_type_trends: {},
  success_rate_comparison: [],
  avg_duration_comparison: [],
  data_volume_comparison: []
})

const recentTasks = ref([])
const terminalBody = ref(null)

// Chart Instances
let mainChartInstance = null
let distributionChartInstance = null
let durationChartInstance = null
let volumeChartInstance = null
let sparklineInstances = []

// DOM Refs
const mainChartRef = ref(null)
const distributionChartRef = ref(null)
const durationChartRef = ref(null)
const volumeChartRef = ref(null)
const sparklineRefs = reactive([])


const currentStats = computed(() => {
  if (selectedTaskType.value === 'all') return dashboardData.overall || {}
  return dashboardData.by_task_type.find(it => it.task_type === selectedTaskType.value) || {}
})

const metricStats = computed(() => {
  const stats = [
    { label: $t('dashboard.dashboard.total_tasks'), value: currentStats.value.total_tasks || 0, icon: List, color: '#6366f1' },
    { label: $t('dashboard.dashboard.completed_tasks'), value: currentStats.value.completed_tasks || 0, icon: CircleCheck, color: '#10b981' },
    { label: $t('dashboard.dashboard.failed_tasks'), value: currentStats.value.failed_tasks || 0, icon: CircleClose, color: '#ef4444' },
    { label: $t('dashboard.dashboard.data_volume'), value: currentStats.value.total_items || 0, icon: Connection, color: '#8b5cf6' },
    { label: $t('dashboard.dashboard.crawled_items'), value: currentStats.value.total_crawled_items || 0, icon: DataAnalysis, color: '#3b82f6' },
    { label: $t('dashboard.dashboard.success_rate'), value: currentStats.value.success_rate || 0, icon: Promotion, color: '#f59e0b', isPercent: true },
    { label: $t('dashboard.dashboard.avg_duration'), value: currentStats.value.avg_duration || 0, icon: Timer, color: '#06b6d4', isSecond: true, isPrecise: true }
  ]
  
  return stats.map(s => {
    const numValue = Number(s.value) || 0
    return {
      ...s,
      formattedValue: s.isPercent ? numValue.toFixed(2) + '%' : s.isSecond ? numValue.toFixed(s.isPrecise ? 2 : 1) + 's' : Math.floor(numValue).toLocaleString()
    }
  })
})

// --- Logic & Helpers ---
const formatTaskType = (type) => $t(`task.type.${type}`) || type
const formatTime = (timeStr) => {
  if (!timeStr) return '--:--:--'
  const date = new Date(timeStr)
  return date.toLocaleTimeString('zh-CN', { hour12: false })
}

const setSparklineRef = (el, index) => {
  if (el) sparklineRefs[index] = el
}

const handleTaskTypeChange = () => {
  loadDashboardData()
}

const handleDaysChange = (val) => {
  if (val !== 'custom') {
    dateRange.value = []
    loadDashboardData()
  }
}

// --- API Integration ---
const loadDashboardData = async () => {
  statusLoading.value = true
  try {
    const params = { days: selectedDays.value === 'custom' ? 30 : selectedDays.value }
    if (selectedDays.value === 'custom' && dateRange.value?.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    
    const res = await getDashboardData(params)
    if (res.code === 10000) {
      Object.assign(dashboardData, res.data)
      taskTypes.value = res.data.task_types || []
      initCharts()
    }
  } catch (err) {
    ElMessage.error($t('dashboard.dashboard.1co67w'))
  } finally {
    statusLoading.value = false
  }
}

const loadRecentTasks = async () => {
  try {
    const res = await getTaskList({ limit: 20 })
    if (res.code === 10000) {
      recentTasks.value = res.data.tasks.map(t => ({
        ...t,
        taskId: t.task_id || t.taskId,
        taskType: t.task_type || t.taskType,
        createdAt: t.create_time || t.createdAt,
        status: t.status || 'pending',
        progress: t.progress || 0
      }))
    }
  } catch (err) {
    console.error('Failed to fetch recent tasks', err)
  }
}

// --- WebSocket Setup ---
const handleWsUpdate = (data) => {
  const index = recentTasks.value.findIndex(t => t.taskId === data.taskId)
  if (index !== -1) {
    recentTasks.value[index] = { ...recentTasks.value[index], ...data }
  } else {
    recentTasks.value.unshift({
      taskId: data.taskId,
      taskType: data.taskType,
      status: data.status,
      progress: data.progress,
      createdAt: new Date().toISOString()
    })
    if (recentTasks.value.length > 50) recentTasks.value.pop()
  }
}

// Auto-scroll terminal
watch(recentTasks, () => {
  nextTick(() => {
    if (terminalBody.value) {
      terminalBody.value.scrollTop = 0 
    }
  })
}, { deep: true })

// --- ECharts Logic ---

const commonOptions = computed(() => ({
  backgroundColor: 'transparent',
  textStyle: { 
    fontFamily: 'Inter, system-ui', 
    color: isDark.value ? '#94a3b8' : '#64748b' 
  },
}))

const disposeCharts = () => {
  mainChartInstance?.dispose()
  mainChartInstance = null
  distributionChartInstance?.dispose()
  distributionChartInstance = null
  durationChartInstance?.dispose()
  durationChartInstance = null
  volumeChartInstance?.dispose()
  volumeChartInstance = null
  sparklineInstances.forEach(i => i?.dispose())
  sparklineInstances = []
}

const initCharts = () => {
  nextTick(() => {
    // Check if component is still mounted and visible
    if (!mainChartRef.value) return
    
    initMainChart()
    initDistributionChart()
    initDurationChart()
    initVolumeChart()
    initSparklines()
  })
}

const initMainChart = () => {
  if (!mainChartRef.value || mainChartRef.value.clientWidth === 0) return
  if (mainChartInstance) mainChartInstance.dispose()
  mainChartInstance = markRaw(echarts.init(mainChartRef.value))
  
  const trendData = selectedTaskType.value === 'all' 
    ? dashboardData.daily_trend 
    : (dashboardData.task_type_trends[selectedTaskType.value] || [])
    
  const xAxisData = trendData.map(it => it.stat_date)
  let series = []
  
  if (trendMode.value === 'task') {
    series = [
      {
        name: $t('dashboard.dashboard.total_tasks'), type: 'line', smooth: true, showSymbol: false,
        data: trendData.map(it => Number(it.total_tasks) || 0),
        lineStyle: { width: 3, color: '#6366f1' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(99, 102, 241, 0.2)' },
            { offset: 1, color: 'rgba(99, 102, 241, 0)' }
          ])
        }
      },
      {
        name: $t('dashboard.dashboard.completed_tasks'), type: 'line', smooth: true, showSymbol: false,
        data: trendData.map(it => Number(it.completed_tasks) || 0),
        lineStyle: { width: 3, color: '#10b981' },
      },
      {
        name: $t('dashboard.dashboard.failed_tasks'), type: 'line', smooth: true, showSymbol: false,
        data: trendData.map(it => Number(it.failed_tasks) || 0),
        lineStyle: { width: 3, color: '#ef4444' },
      }
    ]
  } else {
    series = [{
      name: $t('dashboard.dashboard.crawled_items'), type: 'line', smooth: true,
      data: trendData.map(it => Number(it.total_crawled_items) || 0),
      lineStyle: { width: 4, color: '#3b82f6' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(59, 130, 246, 0.2)' },
          { offset: 1, color: 'rgba(59, 130, 246, 0)' }
        ])
      }
    }]
  }

  mainChartInstance.setOption({
    ...commonOptions.value,
    tooltip: { 
      trigger: 'axis', 
      backgroundColor: isDark.value ? 'rgba(15, 23, 42, 0.9)' : 'rgba(255, 255, 255, 0.9)', 
      borderColor: isDark.value ? '#334155' : '#e2e8f0',
      textStyle: { color: isDark.value ? '#f8fafc' : '#0f172a' }
    },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { 
      type: 'category', 
      data: xAxisData, 
      axisLine: { lineStyle: { color: isDark.value ? '#334155' : '#e2e8f0' } },
      axisLabel: { color: isDark.value ? '#94a3b8' : '#64748b' }
    },
    yAxis: { 
      type: 'value', 
      splitLine: { lineStyle: { color: isDark.value ? '#1e293b' : '#f1f5f9' } },
      axisLabel: { color: isDark.value ? '#94a3b8' : '#64748b' }
    },
    series
  }, true)
}

const initDistributionChart = () => {
  if (!distributionChartRef.value) return
  if (distributionChartInstance) distributionChartInstance.dispose()
  distributionChartInstance = markRaw(echarts.init(distributionChartRef.value))
  
  const sourceData = dashboardData.success_rate_comparison && dashboardData.success_rate_comparison.length > 0 
    ? dashboardData.success_rate_comparison 
    : (dashboardData.by_task_type || [])
    
  const data = sourceData.map(it => ({
    name: formatTaskType(it.task_type || it.taskType), 
    value: parseFloat(Number(it.success_rate || it.successRate || 0).toFixed(2))
  }))
  
  distributionChartInstance.setOption({
    ...commonOptions.value,
    tooltip: { 
      trigger: 'item',
      formatter: '{b}: <b>{c}%</b>'
    },
    series: [{
      type: 'pie', radius: ['40%', '70%'], avoidLabelOverlap: false,
      itemStyle: { 
        borderRadius: 10, 
        borderColor: isDark.value ? '#0f172a' : '#ffffff', 
        borderWidth: 2 
      },
      label: { show: false },
      data
    }],
    color: ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981']
  }, true)
}

const initDurationChart = () => {
  if (!durationChartRef.value) return
  if (durationChartInstance) durationChartInstance.dispose()
  durationChartInstance = markRaw(echarts.init(durationChartRef.value))
  
  const sourceData = dashboardData.avg_duration_comparison && dashboardData.avg_duration_comparison.length > 0
    ? dashboardData.avg_duration_comparison
    : (dashboardData.by_task_type || [])
    
  const data = sourceData.map(it => Number(it.avg_duration || it.avgDuration) || 0)
  const names = sourceData.map(it => formatTaskType(it.task_type || it.taskType))
  
  durationChartInstance.setOption({
    ...commonOptions.value,
    tooltip: { 
      trigger: 'axis',
      backgroundColor: isDark.value ? 'rgba(15, 23, 42, 0.9)' : 'rgba(255, 255, 255, 0.9)',
      borderColor: isDark.value ? '#334155' : '#e2e8f0',
      textStyle: { color: isDark.value ? '#f8fafc' : '#0f172a' },
      formatter: (params) => {
        const item = params[0]
        return `${item.name}: <b>${Number(item.value).toFixed(2)}s</b>`
      }
    },
    grid: { left: '5%', right: '12%', top: '5%', bottom: '5%', containLabel: true },
    xAxis: { 
      type: 'value', 
      splitNumber: 4,
      splitLine: { show: true, lineStyle: { color: isDark.value ? '#1e293b' : '#f1f5f9' } },
      axisLabel: { 
        formatter: '{value}s',
        hideOverlap: true,
        fontSize: 10
      }
    },
    yAxis: { 
      type: 'category', 
      data: names, 
      axisLabel: { 
        fontSize: 11,
        width: 100,
        overflow: 'truncate',
        color: isDark.value ? '#94a3b8' : '#64748b'
      }
    },
    series: [{
      type: 'bar',
      data: data,
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#6366f1' },
          { offset: 1, color: '#a855f7' }
        ]),
        borderRadius: [0, 4, 4, 0]
      },
      label: {
        show: true,
        position: 'right',
        formatter: (params) => Number(params.value).toFixed(2) + 's',
        color: isDark.value ? '#94a3b8' : '#64748b',
        fontSize: 10
      }
    }]
  }, true)
}

const initVolumeChart = () => {
  if (!volumeChartRef.value) return
  if (volumeChartInstance) volumeChartInstance.dispose()
  volumeChartInstance = markRaw(echarts.init(volumeChartRef.value))
  
  let sourceData = []
  if (dashboardData.data_volume_comparison && dashboardData.data_volume_comparison.length > 0) {
    sourceData = dashboardData.data_volume_comparison
  } else if (dashboardData.by_task_type && dashboardData.by_task_type.length > 0) {
    sourceData = dashboardData.by_task_type
  } else {
    sourceData = dashboardData.success_rate_comparison || []
  }
  
  const data = sourceData.map(it => Number(it.total_crawled_items || it.totalCrawledItems || it.count || 0))
  const names = sourceData.map(it => formatTaskType(it.task_type || it.taskType))
  
  volumeChartInstance.setOption({
    ...commonOptions.value,
    tooltip: { 
      trigger: 'axis',
      backgroundColor: isDark.value ? 'rgba(15, 23, 42, 0.9)' : 'rgba(255, 255, 255, 0.9)',
      borderColor: isDark.value ? '#334155' : '#e2e8f0',
      textStyle: { color: isDark.value ? '#f8fafc' : '#0f172a' },
      formatter: (params) => {
        const item = params[0]
        return `${item.name}: <b>${Number(item.value).toLocaleString()}</b>`
      }
    },
    grid: { left: '5%', right: '12%', top: '5%', bottom: '5%', containLabel: true },
    xAxis: { 
      type: 'value', 
      splitNumber: 3,
      splitLine: { show: true, lineStyle: { color: isDark.value ? '#1e293b' : '#f1f5f9' } },
      axisLabel: { 
        formatter: (value) => value >= 10000 ? (value / 10000).toFixed(1) + 'w' : value,
        hideOverlap: true,
        fontSize: 10
      }
    },
    yAxis: { 
      type: 'category', 
      data: names, 
      axisLabel: { 
        fontSize: 11,
        width: 100,
        overflow: 'truncate',
        color: isDark.value ? '#94a3b8' : '#64748b' 
      }
    },
    series: [{
      type: 'bar',
      data: data,
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#8b5cf6' },
          { offset: 1, color: '#d946ef' }
        ]),
        borderRadius: [0, 4, 4, 0]
      },
      label: {
        show: true,
        position: 'right',
        formatter: (params) => Math.floor(params.value).toLocaleString(),
        color: isDark.value ? '#94a3b8' : '#64748b',
        fontSize: 10
      }
    }]
  }, true)
}

const initSparklines = () => {
  sparklineRefs.forEach((el, i) => {
    if (!el) return
    if (sparklineInstances[i]) sparklineInstances[i].dispose()
    sparklineInstances[i] = markRaw(echarts.init(el))
    const mockData = Array.from({ length: 15 }, () => Math.random() * 10)
    sparklineInstances[i].setOption({
      grid: { left: 0, right: 0, top: 0, bottom: 0 },
      xAxis: { type: 'category', show: false },
      yAxis: { type: 'value', show: false },
      series: [{
        type: 'line', data: mockData, symbol: 'none', smooth: true,
        lineStyle: { width: 2, color: metricStats.value[i]?.color || (isDark.value ? '#fff' : '#000') }
      }]
    }, true)
  })
}

onMounted(() => {
  loadDashboardData()
  loadRecentTasks()
  
  webSocketService.connect()
  webSocketService.on('task_update', handleWsUpdate)
  webSocketService.on('connect', () => wsConnected.value = true)
  webSocketService.on('disconnect', () => wsConnected.value = false)
  
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  webSocketService.off('task_update', handleWsUpdate)
  disposeCharts()
})

const handleResize = () => {
  mainChartInstance?.resize()
  distributionChartInstance?.resize()
  durationChartInstance?.resize()
  volumeChartInstance?.resize()
  sparklineInstances.forEach(i => i?.resize())
}

watch(trendMode, initMainChart)
watch(locale, () => {
  disposeCharts()
  initCharts()
})
watch(isDark, () => {
  disposeCharts()
  initCharts()
})
</script>

<style scoped>
/* Reuse styles from Dashboard.vue but adjust for containment */
.overview-wrapper {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.dashboard-filter-bar {
  padding: 16px 24px;
  border-radius: 16px;
  margin-bottom: 4px;
}

.filter-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* Premium UI Scales */
.premium-select :deep(.el-input__wrapper) {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  box-shadow: none !important;
  border-radius: 12px;
  padding-left: 12px;
  height: 40px;
  transition: all 0.3s ease;
}

.days-select {
  width: 160px;
}

.premium-select {
  width: 220px;
}

.premium-date-picker {
  width: 280px !important;
  background: var(--glass-bg) !important;
  border-radius: 12px !important;
  border: 1px solid var(--glass-border) !important;
  height: 40px !important;
}

.premium-date-picker :deep(.el-range-input) {
  background: transparent;
  color: var(--color-text-main);
}

.refresh-action {
  width: 40px;
  height: 40px;
  border: 1px solid var(--glass-border);
  background: var(--glass-bg);
  color: var(--color-text-main);
  font-size: 18px;
  transition: all 0.3s ease;
}

.refresh-action:hover {
  background: #6366f1;
  color: white;
  border-color: #6366f1;
  transform: rotate(180deg);
}

/* Copy relevant styles from Dashboard.vue */
.glass-panel {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  box-shadow: var(--shadow-lg);
}

.dashboard-header {
  height: 60px; /* Smaller header inside tab */
  display: flex;
  align-items: center;
  padding: 0 20px;
  border-radius: 16px;
  justify-content: flex-end; /* Just filters */
}

.filter-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* Grid Layout */
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 24px;
}

/* KPI Cards */
.kpi-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.kpi-card {
  padding: 20px;
  border-radius: 20px;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
  height: 120px;
}

.kpi-icon {
  position: absolute;
  top: 15px;
  right: 15px;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: var(--accent);
  opacity: 0.15;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: var(--accent);
}

.kpi-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  z-index: 2;
}

.kpi-label {
  font-size: 13px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.kpi-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text-main);
  letter-spacing: -0.5px;
}

.kpi-chart {
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 40px;
  opacity: 0.5;
  pointer-events: none;
}

/* Trend Panel */
.trend-section {
  padding: 24px;
  border-radius: 24px;
  margin-bottom: 24px;
  height: 400px;
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.panel-title {
  font-size: 16px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.main-echart {
  flex: 1;
  width: 100%;
}

/* Insights Grid */
.insights-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.insight-card {
  padding: 20px;
  border-radius: 20px;
  height: 280px;
  display: flex;
  flex-direction: column;
}

.insight-title {
  font-size: 14px;
  margin: 0 0 16px 0;
  font-weight: 600;
  text-align: center;
}

.insight-echart {
  flex: 1;
  width: 100%;
}

/* Terminal */
.activity-terminal {
  border-radius: 24px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 140px); /* Adjust height to fit better */
  position: sticky;
  top: 20px;
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  border: 1px solid var(--glass-border);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.terminal-badge {
  font-size: 11px;
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
  padding: 4px 10px;
  border-radius: 20px;
  font-weight: 600;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  border: 1px solid rgba(16, 185, 129, 0.2);
  box-shadow: 0 0 10px rgba(16, 185, 129, 0.1);
}

.terminal-body {
  flex: 1;
  background: var(--glass-bg); /* Match global glass theme */
  border-radius: 16px;
  padding: 16px;
  overflow-y: auto;
  overflow-x: hidden; /* Prevent horizontal scroll bars */
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 11px; /* Slightly smaller for better fit */
  margin-bottom: 16px;
  border: 1px solid var(--glass-border);
  box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.05);
}

/* Custom Scrollbar */
.terminal-body::-webkit-scrollbar {
  width: 6px;
}
.terminal-body::-webkit-scrollbar-track {
  background: transparent;
}
.terminal-body::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.3); /* Lighter scrollbar */
  border-radius: 3px;
}
.terminal-body::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.5);
}

.terminal-empty {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
  opacity: 0.6;
  gap: 12px;
}

.terminal-line {
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 8px; /* Reduce gap to fit more */
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(125, 125, 125, 0.05); /* Very subtle adaptation */
  border-left: 2px solid transparent;
  transition: background 0.2s ease; /* Remove transform */
  cursor: default; /* Not really clickable */
}

.terminal-line:hover {
  background: rgba(125, 125, 125, 0.1);
  /* Removed transform shift */
}

/* Status Colors & Borders */
.terminal-line:has(.task-status.completed) { border-left-color: #10b981; }
.terminal-line:has(.task-status.failed) { border-left-color: #ef4444; }
.terminal-line:has(.task-status.running) { border-left-color: #f59e0b; background: linear-gradient(90deg, rgba(245, 158, 11, 0.05), transparent); }

.timestamp { color: var(--color-text-secondary); opacity: 0.8; font-size: 11px; min-width: 65px; }
.task-type { color: #8b5cf6; font-weight: 600; min-width: 70px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.task-id { color: #06b6d4; opacity: 0.8; font-size: 11px; flex: 1; /* Allow flexible width */ white-space: nowrap; overflow: hidden; text-overflow: ellipsis;} 

.task-status { 
  font-weight: 700; 
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 4px;
  margin-left: auto;
  letter-spacing: 0.5px;
  min-width: 55px;
  text-align: center;
}
.task-status.completed { color: #10b981; background: rgba(16, 185, 129, 0.1); }
.task-status.failed { color: #ef4444; background: rgba(239, 68, 68, 0.1); }
.task-status.running { color: #f59e0b; background: rgba(245, 158, 11, 0.1); }
.task-status.pending { color: #94a3b8; background: rgba(148, 163, 184, 0.1); }

/* Progress Animation */
.progress-mini {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: rgba(255, 255, 255, 0.05);
  overflow: hidden;
  border-radius: 0 0 8px 8px;
}

.progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
  box-shadow: 0 0 8px rgba(245, 158, 11, 0.5);
  transition: width 0.3s ease;
}

.terminal-footer {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--color-text-secondary);
  font-weight: 500;
  padding: 0 4px;
}

.system-stats {
  display: flex;
  gap: 16px;
}

.ws-indicator {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #cbd5e1;
  transition: all 0.3s;
}

.ws-indicator.active {
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
}

.premium-select, .days-select { 
  /* Improve Select Styles override */
  --el-input-bg-color: rgba(255,255,255,0.05);
  --el-input-border-color: rgba(255,255,255,0.1);
  --el-input-text-color: var(--color-text-main);
  backdrop-filter: blur(10px);
}
</style>
