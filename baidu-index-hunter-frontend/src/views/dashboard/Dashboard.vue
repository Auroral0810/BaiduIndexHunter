<template>
  <div class="dashboard-wrapper">
    <!-- Animated Background Layer -->
    <div class="canvas-bg">
      <div class="glow-orb orb-1"></div>
      <div class="glow-orb orb-2"></div>
      <div class="grid-overlay"></div>
    </div>

    <!-- Main Navigation / Header -->
    <header class="dashboard-header glass-panel">
      <div class="brand">
        <div class="logo-icon">
          <el-icon><TrendCharts /></el-icon>
        </div>
        <div class="title-group">
          <h1 class="main-title">{{ $t('dashboard.dashboard.2dwsg6') }}</h1>
          <div class="live-status">
            <span class="pulse-dot" :class="{ 'is-active': wsConnected }"></span>
            <span class="status-text">{{ wsConnected ? $t('dashboard.dashboard.status_ok') : $t('dashboard.dashboard.status_disconnected') }}</span>
          </div>
        </div>
      </div>

      <div class="filter-controls">
        <div class="control-item">
          <el-select v-model="selectedTaskType" class="premium-select" @change="handleTaskTypeChange">
            <el-option :label="$t('dashboard.dashboard.o0v3d0')" value="all" />
            <el-option v-for="type in taskTypes" :key="type" :label="formatTaskType(type)" :value="type" />
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
        />
        <el-button class="refresh-action" @click="loadDashboardData" :loading="statusLoading" circle>
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </header>

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
                <el-radio-button label="task">{{ $t('dashboard.dashboard.total_tasks') }}</el-radio-button>
                <el-radio-button label="success">{{ $t('dashboard.dashboard.crawled_items') }}</el-radio-button>
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
              <span class="task-type">{{ formatTaskType(task.taskType) }}</span>
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
import { ref, reactive, onMounted, onUnmounted, nextTick, computed, watch } from 'vue'
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
const sparklineInstances = []

// DOM Refs
const mainChartRef = ref(null)
const distributionChartRef = ref(null)
const durationChartRef = ref(null)
const volumeChartRef = ref(null)
const sparklineRefs = reactive([])

// --- Computed ---
const taskTypeMap = computed(() => ({
  'search_index': $t('views.datacollection.2ncis3'),
  'feed_index': $t('views.datacollection.653q6s'),
  'word_graph': $t('views.datacollection.k08266'),
  'region_distribution': $t('views.datacollection.sciq8u'),
  'demographic_attributes': $t('views.datacollection.i19rq5'),
  'interest_profile': $t('dashboard.dashboard.py2bk3')
}))

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
const formatTaskType = (type) => taskTypeMap.value[type] || type
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
      terminalBody.value.scrollTop = 0 // Since I'm unshifting, new ones are at top. 
      // Wait, if I'm unshifting, the newest is at the top. So scrollTop = 0 is correct.
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

const initCharts = () => {
  nextTick(() => {
    initMainChart()
    initDistributionChart()
    initDurationChart()
    initVolumeChart()
    initSparklines()
  })
}

const initMainChart = () => {
  if (!mainChartRef.value) return
  if (!mainChartInstance) mainChartInstance = echarts.init(mainChartRef.value)
  
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
  if (!distributionChartInstance) distributionChartInstance = echarts.init(distributionChartRef.value)
  
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
  if (!durationChartInstance) durationChartInstance = echarts.init(durationChartRef.value)
  
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
  if (!volumeChartInstance) volumeChartInstance = echarts.init(volumeChartRef.value)
  
  // Fallback to data_volume_comparison then by_task_type
  let sourceData = []
  if (dashboardData.data_volume_comparison && dashboardData.data_volume_comparison.length > 0) {
    sourceData = dashboardData.data_volume_comparison
  } else if (dashboardData.by_task_type && dashboardData.by_task_type.length > 0) {
    sourceData = dashboardData.by_task_type
  } else {
    // Last resort: use success_rate_comparison which might have volume info
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
    if (!sparklineInstances[i]) sparklineInstances[i] = echarts.init(el)
    
    // Simple path animation
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

// --- Lifecycle ---
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
  mainChartInstance?.dispose()
  distributionChartInstance?.dispose()
  durationChartInstance?.dispose()
  volumeChartInstance?.dispose()
  sparklineInstances.forEach(i => i?.dispose())
})

const handleResize = () => {
  mainChartInstance?.resize()
  distributionChartInstance?.resize()
  durationChartInstance?.resize()
  volumeChartInstance?.resize()
  sparklineInstances.forEach(i => i?.resize())
}

watch(trendMode, initMainChart)
watch(locale, initCharts)
watch(isDark, initCharts)
</script>

<style scoped>
.dashboard-wrapper {
  position: relative;
  min-height: calc(100vh - 100px);
  background: var(--color-bg-body);
  color: var(--color-text-main);
  padding: 24px;
  overflow-x: hidden;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  transition: all 0.3s ease;
}

/* Background effects */
.canvas-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  opacity: 0.15;
}

.orb-1 { width: 600px; height: 600px; top: -10%; right: -5%; background: #6366f1; }
.orb-2 { width: 500px; height: 500px; bottom: 5%; left: -5%; background: #8b5cf6; }

.grid-overlay {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(30, 41, 59, 0.2) 1px, transparent 1px),
    linear-gradient(90deg, rgba(30, 41, 59, 0.2) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: radial-gradient(circle at center, black, transparent 90%);
}

/* Panels */
.glass-panel {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  box-shadow: var(--shadow-lg);
}

/* Header */
.dashboard-header {
  height: 80px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 32px;
  border-radius: 20px;
  margin-bottom: 24px;
  position: relative;
  z-index: 10;
}

.brand {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
}

.main-title {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.5px;
  margin: 0;
}

.live-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.65rem;
  font-weight: 700;
  color: #10b981;
  letter-spacing: 1px;
}

.pulse-dot {
  width: 6px;
  height: 6px;
  background: #94a3b8;
  border-radius: 50%;
  opacity: 0.5;
  transition: all 0.3s;
}

.pulse-dot.is-active {
  background: #10b981;
  opacity: 1;
  box-shadow: 0 0 8px #10b981;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(1.5); }
  100% { opacity: 1; transform: scale(1); }
}

.filter-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.premium-select {
  width: 180px !important;
}

.days-select {
  width: 160px !important;
}

/* Grid Layout */
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 380px;
  gap: 24px;
  position: relative;
  z-index: 1;
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
}

.kpi-card::before {
  content: '';
  position: absolute;
  top: 10px;
  right: 10px;
  width: 40px;
  height: 40px;
  background: var(--accent);
  opacity: 0.05;
  border-radius: 50%;
}

.kpi-icon {
  font-size: 20px;
  color: var(--accent);
  margin-bottom: 12px;
}

.kpi-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  margin-bottom: 4px;
}

.kpi-value-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.kpi-value {
  font-size: 1.75rem;
  font-weight: 800;
  letter-spacing: -1px;
}

.kpi-trend {
  font-size: 0.7rem;
  font-weight: 700;
}

.kpi-trend.up { color: #10b981; }
.kpi-trend.down { color: #ef4444; }

.kpi-chart {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40px;
  opacity: 0.3;
}

/* Trend Section */
.trend-section {
  padding: 24px;
  border-radius: 24px;
  margin-bottom: 24px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.panel-title {
  font-size: 1rem;
  font-weight: 700;
  margin: 0;
  color: var(--color-text-main);
}

.main-echart {
  height: 380px;
  width: 100%;
}

/* Insights Section */
.insights-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.insight-card {
  padding: 20px;
  border-radius: 20px;
}

.insight-title {
  font-size: 0.9rem;
  font-weight: 700;
  margin: 0 0 16px 0;
  color: var(--color-text-secondary);
}

.insight-echart {
  height: 240px;
  width: 100%;
}

/* Terminal Aside */
.activity-terminal {
  border-radius: 24px;
  display: flex;
  flex-direction: column;
  padding: 24px 0;
}

.activity-terminal .panel-header {
  padding: 0 24px;
}

.terminal-badge {
  background: rgba(99, 102, 241, 0.1);
  color: #818cf8;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.6rem;
  font-weight: 800;
  border: 1px solid rgba(99, 102, 241, 0.2);
}

.terminal-body {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px;
  scrollbar-width: none;
}

.terminal-line {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.7rem;
  padding: 10px;
  border-radius: 8px;
  background: var(--color-bg-surface);
  margin-bottom: 8px;
  border: 1px solid var(--color-border);
  display: grid;
  grid-template-columns: 75px 1fr 60px 70px;
  gap: 8px;
  align-items: center;
}

.terminal-line:hover {
  background: var(--color-bg-subtle);
  border-color: var(--color-primary-light);
}

.terminal-line .timestamp { color: var(--color-text-tertiary); }
.terminal-line .task-type { color: var(--color-text-main); font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.terminal-line .task-id { color: var(--color-primary); opacity: 0.8; }
.terminal-line .task-status { 
  font-weight: 800; 
  padding: 2px 4px; 
  border-radius: 4px;
  text-align: center;
}

.task-status.completed { color: #10b981; }
.task-status.running { color: #f59e0b; }
.task-status.failed { color: #ef4444; }

.progress-mini {
  grid-column: 1 / span 4;
  height: 2px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 2px;
  margin-top: 4px;
}

.progress-bar {
  height: 100%;
  background: #f59e0b;
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.5);
  transition: width 0.3s ease;
}

.terminal-footer {
  padding: 16px 24px 0 24px;
  border-top: 1px solid var(--color-border);
}

.system-stats {
  display: flex;
  justify-content: space-between;
  font-size: 0.6rem;
  font-weight: 700;
  color: #64748b;
  letter-spacing: 0.5px;
}

.ws-indicator {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #64748b;
}

.ws-indicator.active {
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
}

/* Animations */
.terminal-list-enter-active {
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.terminal-list-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

/* Element overrides */
:deep(.premium-select) .el-input__wrapper {
  background: rgba(30, 41, 59, 0.5) !important;
  box-shadow: none !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 12px;
}

:deep(.premium-select) .el-input__inner {
  color: #fff !important;
  font-weight: 600;
}

.refresh-action {
  background: rgba(99, 102, 241, 0.1) !important;
  border-color: rgba(99, 102, 241, 0.2) !important;
  color: #818cf8 !important;
}

.premium-radio :deep(.el-radio-button__inner) {
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #94a3b8;
}

.premium-radio :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background: #6366f1;
  border-color: #6366f1;
}

/* Responsive */
@media screen and (max-width: 1400px) {
  .dashboard-grid { grid-template-columns: 1fr; }
  .activity-terminal { height: 400px; }
  .kpi-container { grid-template-columns: 1fr 1fr; }
}

@media screen and (max-width: 768px) {
  .kpi-container { grid-template-columns: 1fr; }
  .insights-grid { grid-template-columns: 1fr; }
  .dashboard-header { flex-direction: column; height: auto; padding: 20px; gap: 16px; }
}
</style>
