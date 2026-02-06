<template>
  <div class="spider-health-wrapper">
    <!-- Filters -->
    <div class="filter-bar glass-panel">
      <div class="filter-item">
        <span class="filter-label">{{ $t('dashboard.dashboard.dd5kiw') }}</span>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          size="small"
          range-separator="-"
          :start-placeholder="$t('dashboard.dashboard.start_date')"
          :end-placeholder="$t('dashboard.dashboard.end_date')"
          value-format="YYYY-MM-DD"
          @change="loadData"
          style="width: 240px"
        />
      </div>
      <div class="filter-item">
        <span class="filter-label">{{ $t('tasks-TaskList-19c298d949224c78d-3') }}</span>
        <el-select v-model="taskType" size="small" style="width: 200px" @change="loadData" clearable>
          <el-option v-for="type in taskTypesList" :key="type" :label="taskTypeMap[type] || type" :value="type" />
        </el-select>
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
import * as echarts from 'echarts'
import { getSpiderStatistics } from '@/api/statistics'
import { useI18n } from 'vue-i18n'
import { useAppStore } from '@/store/app'

const { t: $t } = useI18n()
const appStore = useAppStore()
const isDark = computed(() => appStore.theme === 'dark')

const dateRange = ref([])
const taskType = ref('')
const taskTypesList = ['search_index', 'feed_index', 'word_graph', 'region_distribution', 'demographic_attributes', 'interest_profile']

const taskTypeMap = computed(() => ({
  'search_index': $t('views.datacollection.2ncis3'),
  'feed_index': $t('views.datacollection.653q6s'),
  'word_graph': $t('views.datacollection.k08266'),
  'region_distribution': $t('views.datacollection.sciq8u'),
  'demographic_attributes': $t('views.datacollection.i19rq5'),
  'interest_profile': $t('dashboard.dashboard.py2bk3')
}))

// Initialize date range to last 30 days
onMounted(() => {
  const end = new Date()
  const start = new Date()
  start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
  dateRange.value = [
    start.toISOString().split('T')[0],
    end.toISOString().split('T')[0]
  ]
})

const successChartRef = ref(null)
const cookieUsageRef = ref(null)
const cookieBanRef = ref(null)

let successChart = null
let cookieUsageChart = null
let cookieBanChart = null

const loadData = async () => {
  try {
    const params = {
      task_type: taskType.value || undefined
    }
    
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    
    const res = await getSpiderStatistics(params)
    if (res.code === 10000) {
      updateCharts(res.data.statistics)
    }
  } catch (e) {
    console.error(e)
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
  initCharts()
  // Wait for onMounted in setup to set initial dateRange then load
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
.filter-bar {
  display: flex;
  gap: 20px;
  padding: 15px;
  border-radius: 12px;
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
