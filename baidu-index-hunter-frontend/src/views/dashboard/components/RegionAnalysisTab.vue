<template>
  <div class="region-analysis-wrapper">
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
        <div class="control-item search-item">
          <el-input 
            v-model="cityName" 
            :placeholder="$t('dashboard.region.city_name')" 
            class="premium-input" 
            @change="loadData" 
            clearable
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <el-button class="refresh-action" @click="loadData" :loading="loading" circle>
          <el-icon><Refresh /></el-icon>
        </el-button>
      </div>
    </div>

    <!-- Charts and Tables -->
    <div class="content-grid">
      <!-- Top Cities Map/Chart (Using Chart for simplicity and reliability without geojson) -->
      <div class="chart-card glass-panel wide">
        <h4 class="chart-title">{{ $t('dashboard.region.top_cities') }}</h4>
        <div ref="cityChartRef" class="echart-container"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import { Search, Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { getCityStatistics } from '@/api/statistics'
import { useAppStore } from '@/store/app'
import { useI18n } from 'vue-i18n'

const { t: $t } = useI18n()
const appStore = useAppStore()
const isDark = computed(() => appStore.theme === 'dark')

const selectedTaskType = ref('all')
const selectedDays = ref(30)
const dateRange = ref([])
const loading = ref(false)

const cityName = ref('')
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

const cityChartRef = ref(null)
let cityChart = null

const loadData = async () => {
  loading.value = true
  try {
    const params = { 
      city_name: cityName.value || undefined, 
      task_type: selectedTaskType.value !== 'all' ? selectedTaskType.value : undefined,
      limit: 20 
    }
    
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    } else if (selectedDays.value !== 'custom' && selectedDays.value !== -1) {
      const end = new Date()
      const start = new Date()
      start.setTime(start.getTime() - 3600 * 1000 * 24 * selectedDays.value)
      params.start_date = start.toISOString().split('T')[0]
      params.end_date = end.toISOString().split('T')[0]
    }
    
    const res = await getCityStatistics(params)
    
    if (res.code === 10000) {
      updateChart(res.data.cities || [])
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const updateChart = (data) => {
  if (!cityChart) return
  if (data.length === 0) {
    cityChart.clear()
    cityChart.setOption({
       title: { text: $t('dashboard.charts.no_data'), left: 'center', top: 'center', textStyle: { color: isDark.value ? '#94a3b8' : '#64748b' } }
    })
    return
  }

  const cities = data.map(i => i.city_name)
  const values = data.map(i => i.item_count)

  const option = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { 
      type: 'category', 
      data: cities, 
      axisLabel: { interval: 0, rotate: 30, color: isDark.value ? '#94a3b8' : '#64748b' }
    },
    yAxis: { 
      type: 'value', 
      splitLine: { lineStyle: { color: isDark.value ? '#1e293b' : '#eee' } },
      axisLabel: { color: isDark.value ? '#94a3b8' : '#64748b' }
    },
    series: [{
      name: $t('dashboard.dashboard.crawled_items'),
      type: 'bar',
      data: values,
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#06b6d4' },
          { offset: 1, color: '#3b82f6' }
        ]),
        borderRadius: [4, 4, 0, 0]
      }
    }]
  }
  
  cityChart.setOption(option)
}

const initChart = () => {
  if (cityChartRef.value) {
    cityChart = echarts.init(cityChartRef.value)
  }
}

const handleResize = () => cityChart?.resize()

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

  initChart()
  setTimeout(() => loadData(), 50)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  cityChart?.dispose()
})

watch(() => appStore.theme, () => {
    cityChart?.dispose()
    nextTick(() => {
        initChart()
        loadData()
    })
})
</script>

<style scoped>
.region-analysis-wrapper {
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
.premium-select :deep(.el-input__wrapper),
.premium-input :deep(.el-input__wrapper) {
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  box-shadow: none !important;
  border-radius: 12px;
  padding: 0 16px;
  height: 40px;
  transition: all 0.3s ease;
}

.days-select {
  width: 160px;
}

.premium-select {
  width: 220px;
}

.premium-input {
  width: 280px;
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
.chart-card {
  padding: 20px;
  border-radius: 16px;
  min-height: 400px;
}
.echart-container {
  height: 400px;
  width: 100%;
}
.glass-panel {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
}
</style>
