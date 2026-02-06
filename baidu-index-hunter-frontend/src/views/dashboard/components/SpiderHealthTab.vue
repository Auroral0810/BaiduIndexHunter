<template>
  <div class="spider-health-wrapper">
    <!-- Filters (Localized Premium) -->
    <div class="dashboard-filter-bar glass-panel">
      <div class="filter-controls">
        <div class="control-item">
          <el-select v-model="selectedTaskType" class="premium-select" @change="handleTaskTypeChange">
            <el-option :label="$t('dashboard.dashboard.o0v3d0')" value="all" />
            <el-option v-for="type in taskTypesList" :key="type" :label="taskTypeMap[type] || type" :value="type" />
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
          @change="loadData"
          value-format="YYYY-MM-DD"
        />
        <el-button class="refresh-action" @click="loadData" :loading="statusLoading" circle>
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- Charts Grid -->
    <div class="charts-grid">
      <!-- Success Rate Trend -->
      <div class="chart-card glass-panel wide">
        <h4 class="chart-title">{{ $t('dashboard.dashboard.success_comparison') }}</h4>
        <div ref="successChartRef" class="echart-container"></div>
      </div>

      <!-- Cookie Usage -->
      <div class="chart-card glass-panel">
        <h4 class="chart-title">{{ $t('dashboard.health.cookie_usage') }}</h4>
        <div ref="cookieUsageRef" class="echart-container"></div>
      </div>

      <!-- Cookie Bans -->
      <div class="chart-card glass-panel">
        <h4 class="chart-title">{{ $t('dashboard.health.cookie_bans') }}</h4>
        <div ref="cookieBanRef" class="echart-container"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { getSpiderStatistics } from '@/api/statistics'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/store/app'

const { t: $t } = useI18n()
const appStore = useAppStore()
const isDark = computed(() => appStore.theme === 'dark')

const selectedTaskType = ref('all')
const selectedDays = ref(30)
const dateRange = ref([])
const statusLoading = ref(false)

const taskTypesList = ['search_index', 'feed_index', 'word_graph', 'region_distribution', 'demographic_attributes', 'interest_profile']

const taskTypeMap = computed(() => ({
  'search_index': $t('views.datacollection.2ncis3'),
  'feed_index': $t('views.datacollection.653q6s'),
  'word_graph': $t('views.datacollection.k08266'),
  'region_distribution': $t('views.datacollection.sciq8u'),
  'demographic_attributes': $t('views.datacollection.i19rq5'),
  'interest_profile': $t('dashboard.dashboard.py2bk3')
}))

const handleTaskTypeChange = () => {
  loadData()
}

const handleDaysChange = (val) => {
  if (val !== 'custom') {
    if (val === -1) {
      dateRange.value = []
    } else {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * val)
      dateRange.value = [
        start.toISOString().split('T')[0],
        end.toISOString().split('T')[0]
      ]
    }
  }
  loadData()
}


const successChartRef = ref(null)
const cookieUsageRef = ref(null)
const cookieBanRef = ref(null)

let successChart = null
let cookieUsageChart = null
let cookieBanChart = null

const loadData = async () => {
  statusLoading.value = true
  try {
    const params = {
      task_type: selectedTaskType.value !== 'all' ? selectedTaskType.value : undefined
    }
    
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    } else if (selectedDays.value !== 'custom' && selectedDays.value !== -1) {
      // Fallback calculation just in case
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * selectedDays.value)
      params.start_date = start.toISOString().split('T')[0]
      params.end_date = end.toISOString().split('T')[0]
    }
    
    const res = await getSpiderStatistics(params)
    if (res.code === 10000) {
      updateCharts(res.data.statistics)
    }
  } catch (e) {
    console.error(e)
  } finally {
    statusLoading.value = false
  }
}

const updateCharts = (data) => {
  if (!data || data.length === 0) return

  // Filter and Sort by date
  // ... (Implementation details for chart data processing)
  
  const processedData = data
    .sort((a, b) => new Date(a.stat_date) - new Date(b.stat_date))

  const dates = processedData.map(d => d.stat_date)
  const successRates = processedData.map(d => d.success_rate)
  const cookieUsages = processedData.map(d => d.cookie_usage)
  const cookieBans = processedData.map(d => d.cookie_ban_count)

  // Success Rate Chart
  const commonOption = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', backgroundColor: isDark.value ? 'rgba(15,23,42,0.9)' : 'rgba(255,255,255,0.9)', textStyle: { color: isDark.value ? '#fff' : '#000' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category', data: dates, axisLine: { lineStyle: { color: isDark.value ? '#334155' : '#ccc' } } },
    yAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed', color: isDark.value ? '#1e293b' : '#eee' } } }
  }

  successChart.setOption({
    ...commonOption,
    series: [{
      name: $t('dashboard.dashboard.success_rate'),
      type: 'line',
      smooth: true,
      data: successRates,
      itemStyle: { color: '#10b981' },
      areaStyle: { color: new echarts.graphic.LinearGradient(0,0,0,1, [{offset:0, color:'rgba(16,185,129,0.2)'}, {offset:1, color:'rgba(16,185,129,0)'}]) }
    }]
  })

  // Cookie Usage Chart (Bar)
  cookieUsageChart.setOption({
    ...commonOption,
    series: [{
      name: $t('dashboard.health.cookie_usage'),
      type: 'bar',
      data: cookieUsages,
      itemStyle: { color: '#3b82f6', borderRadius: [4, 4, 0, 0] }
    }]
  })

  // Cookie Bans Chart (Bar/Line)
  cookieBanChart.setOption({
    ...commonOption,
    series: [{
      name: $t('dashboard.health.cookie_bans'),
      type: 'bar',
      data: cookieBans,
      itemStyle: { color: '#ef4444', borderRadius: [4, 4, 0, 0] }
    }]
  })
}

const initCharts = () => {
  if(successChartRef.value) successChart = echarts.init(successChartRef.value)
  if(cookieUsageRef.value) cookieUsageChart = echarts.init(cookieUsageRef.value)
  if(cookieBanRef.value) cookieBanChart = echarts.init(cookieBanRef.value)
}

const handleResize = () => {
  successChart?.resize()
  cookieUsageChart?.resize()
  cookieBanChart?.resize()
}

onMounted(() => {
  // Initialize date range to last 30 days if not custom
  if (selectedDays.value !== 'custom') {
    const end = new Date()
    const start = new Date()
    start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
    dateRange.value = [
      start.toISOString().split('T')[0],
      end.toISOString().split('T')[0]
    ]
  }

  initCharts()
  setTimeout(() => loadData(), 50) 
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  successChart?.dispose()
  cookieUsageChart?.dispose()
  cookieBanChart?.dispose()
})

watch(() => appStore.theme, () => {
  nextTick(() => {
    successChart?.dispose(); cookieUsageChart?.dispose(); cookieBanChart?.dispose()
    initCharts()
    loadData()
  })
})
</script>

<style scoped>
.spider-health-wrapper {
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

.filter-item {
  display: flex;
  align-items: center;
  gap: 10px;
}
.filter-label {
  font-size: 14px;
  color: var(--color-text-secondary);
}
.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}
.wide {
  grid-column: span 2;
}
.chart-card {
  padding: 20px;
  border-radius: 16px;
  min-height: 350px;
}
.chart-title {
  margin: 0 0 20px 0;
  font-size: 16px;
  font-weight: 600;
}
.echart-container {
  height: 300px;
  width: 100%;
}
.glass-panel {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
}
</style>
