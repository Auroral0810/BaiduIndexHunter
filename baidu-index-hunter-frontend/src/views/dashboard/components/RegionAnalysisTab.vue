<template>
  <div class="region-analysis-wrapper">
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
        <span class="filter-label">{{ $t('components-RegionCitySelector-19c298e1bc4e14bf9-11') }} / {{ $t('components-RegionCitySelector-19c298e1bc4e14bf9-2') }}</span>
        <el-input v-model="cityName" :placeholder="$t('dashboard.dashboard.o0v3d0')" size="small" style="width: 240px" @change="loadData" clearable>
          <template #append>
            <el-button @click="loadData"><el-icon><Search /></el-icon></el-button>
          </template>
        </el-input>
      </div>
      <div class="filter-item">
         <span class="filter-label">{{ $t('tasks-TaskList-19c298d949224c78d-3') }}</span>
         <el-select v-model="taskType" size="small" style="width: 200px" @change="loadData" clearable>
            <el-option v-for="type in taskTypesList" :key="type" :label="taskTypeMap[type] || type" :value="type" />
          </el-select>
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
import * as echarts from 'echarts'
import { getCityStatistics } from '@/api/statistics'
import { Search } from '@element-plus/icons-vue'
import { useAppStore } from '@/store/app'
import { useI18n } from 'vue-i18n'

const { t: $t } = useI18n()
const appStore = useAppStore()
const isDark = computed(() => appStore.theme === 'dark')

const dateRange = ref([])
const cityName = ref('')
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

const cityChartRef = ref(null)
let cityChart = null

const loadData = async () => {
  try {
    const params = { 
      city_name: cityName.value || undefined, 
      task_type: taskType.value || undefined,
      limit: 20 
    }
    
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    
    const res = await getCityStatistics(params)
    
    if (res.code === 10000) {
      updateChart(res.data.cities || [])
    }
  } catch (e) {
    console.error(e)
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
  // Initialize date range to last 30 days
  const end = new Date()
  const start = new Date()
  start.setTime(start.getTime() - 3600 * 1000 * 24 * 30)
  dateRange.value = [
    start.toISOString().split('T')[0],
    end.toISOString().split('T')[0]
  ]

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
.filter-bar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 15px;
  border-radius: 12px;
}
.filter-item {
  display: flex;
  align-items: center;
  gap: 10px;
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
