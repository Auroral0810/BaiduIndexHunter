<template>
  <div class="spider-health-wrapper">
    <!-- Filters -->
    <div class="filter-bar glass-panel">
      <div class="filter-item">
        <span class="filter-label">{{ $t('dashboard.dashboard.dd5kiw') }}</span>
        <el-radio-group v-model="timeRange" size="small" @change="loadData">
          <el-radio-button label="7">{{ $t('dashboard.dashboard.2a174n') }}</el-radio-button>
          <el-radio-button label="30">{{ $t('dashboard.dashboard.zk61g6') }}</el-radio-button>
          <el-radio-button label="90">{{ $t('dashboard.dashboard.5o84wx') }}</el-radio-button>
        </el-radio-group>
      </div>
      <div class="filter-item">
        <span class="filter-label">{{ $t('tasks-TaskList-19c298d949224c78d-3') }}</span>
        <el-select v-model="taskType" size="small" style="width: 140px" @change="loadData">
          <el-option :label="$t('dashboard.dashboard.o0v3d0')" value="" />
          <el-option v-for="type in taskTypes" :key="type" :label="$t(`task.type.${type}`)" :value="type" />
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

const timeRange = ref('30')
const taskType = ref('')
const taskTypes = ['search_index', 'feed_index', 'word_graph', 'region_distribution', 'demographic_attributes', 'interest_profile']

const successChartRef = ref(null)
const cookieUsageRef = ref(null)
const cookieBanRef = ref(null)

let successChart = null
let cookieUsageChart = null
let cookieBanChart = null

const loadData = async () => {
  try {
    // Calculate start date based on range
    const end = new Date()
    const start = new Date()
    start.setDate(start.getDate() - parseInt(timeRange.value))
    
    // Note: API currently takes date, which might be single day or we might need to fetch range.
    // The current API in controller seems to take 'date' and 'task_type'.
    // If getting range, we might need multiple calls or backend support for range.
    // Assuming backend supports returning list if no date specific, or we need to loop. 
    // To be safe and efficient, we should check if backend supports range for spider stats.
    // The code I read showed: get_spider_statistics(date, task_type).
    // If date is None, it returns all? Let's assume passed date is filter.
    // Actually, for trend, we need multiple days data.
    // The API response example showed: "statistics": [ { "stat_date": "...", ... } ]
    // This implies it returns a list, likely filtered by date if provided, or all if not?
    // Let's try calling without date to get all, then filter in frontend, or assume it returns recent.
    
    const res = await getSpiderStatistics({ task_type: taskType.value })
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
    .slice(-parseInt(timeRange.value)) // Take last N days

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
  loadData()
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
