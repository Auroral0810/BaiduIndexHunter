<template>
  <div class="keyword-analysis-wrapper">
    <!-- Filter -->
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
        <span class="filter-label">Task ID</span>
        <el-input v-model="taskId" :placeholder="$t('tasks-TaskList-19c298d949224c78d-19')" size="small" style="width: 240px" @change="loadData" clearable>
           <template #append>
            <el-button @click="loadData">
              <el-icon><Search /></el-icon>
            </el-button>
          </template>
        </el-input>
      </div>
      <div class="filter-item" style="margin-left: auto">
        <el-button type="primary" size="small" @click="loadData" :loading="loading">{{ $t('dashboard.dashboard.327577') }}</el-button>
      </div>
    </div>

    <div class="content-grid">
      <!-- Top Keywords Chart -->
      <div class="chart-card glass-panel">
        <h4 class="chart-title">{{ $t('dashboard.keywords.top_charts') }}</h4>
        <div ref="chartRef" class="echart-container"></div>
      </div>

      <!-- Keywords Table -->
      <div class="table-card glass-panel">
        <el-table :data="tableData" style="width: 100%" height="350">
          <el-table-column prop="keyword" :label="$t('tasks-TaskList-19c298d949224c78d-66')" width="180" />
          <el-table-column prop="item_count" :label="$t('dashboard.dashboard.crawled_items')" sortable />
          <el-table-column prop="avg_success_rate" :label="$t('dashboard.dashboard.success_rate')" sortable>
            <template #default="scope">
              <el-tag :type="scope.row.avg_success_rate > 90 ? 'success' : 'warning'">
                {{ scope.row.avg_success_rate.toFixed(2) }}%
              </el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'
import * as echarts from 'echarts'
import { getKeywordStatistics } from '@/api/statistics'
import { Search } from '@element-plus/icons-vue'
import { useAppStore } from '@/store/app'
import { useI18n } from 'vue-i18n'

const { t: $t } = useI18n()
const appStore = useAppStore()
const isDark = computed(() => appStore.theme === 'dark')

const dateRange = ref([])
const taskId = ref('')
const loading = ref(false)
const tableData = ref([])
const chartRef = ref(null)
let chartInstance = null

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      task_id: taskId.value || undefined,
      limit: 20
    }
    
    if (dateRange.value && dateRange.value.length === 2) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    
    const res = await getKeywordStatistics(params)
    if (res.code === 10000) {
      if (res.data && res.data.keywords) {
        tableData.value = res.data.keywords
        updateChart(res.data.keywords)
      } else {
        tableData.value = []
        updateChart([])
      }
    }
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

const updateChart = (data) => {
  if (!chartInstance) return
  
  if (data.length === 0) {
    chartInstance.clear()
    chartInstance.setOption({
      title: { text: $t('dashboard.charts.no_data'), left: 'center', top: 'center', textStyle: { color: isDark.value ? '#94a3b8' : '#64748b' } }
    })
    return
  }

  const keywords = data.map(i => i.keyword)
  const values = data.map(i => i.item_count)

  const option = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { 
      type: 'value', 
      splitLine: { lineStyle: { color: isDark.value ? '#1e293b' : '#eee' } },
      axisLabel: { color: isDark.value ? '#94a3b8' : '#64748b' }
    },
    yAxis: { 
      type: 'category', 
      data: keywords, 
      inverse: true,
      axisLabel: { color: isDark.value ? '#94a3b8' : '#64748b', width: 100, overflow: 'truncate' }
    },
    series: [{
      name: $t('dashboard.dashboard.crawled_items'),
      type: 'bar',
      data: values,
      itemStyle: {
        color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
          { offset: 0, color: '#8b5cf6' },
          { offset: 1, color: '#6366f1' }
        ]),
        borderRadius: [0, 4, 4, 0]
      }
    }]
  }
  chartInstance.setOption(option)
}

const initChart = () => {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value)
  }
}

const handleResize = () => chartInstance?.resize()

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
  // Wait for ref to be populated
  setTimeout(() => loadData(), 50)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
})

watch(() => appStore.theme, () => {
    chartInstance?.dispose()
    nextTick(() => {
        initChart()
        loadData()
    })
})
</script>

<style scoped>
.keyword-analysis-wrapper {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.filter-bar {
  display: flex;
  align-items: center;
  padding: 15px;
  border-radius: 12px;
}
.filter-item {
  display: flex;
  align-items: center;
  gap: 10px;
}
.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
.chart-card, .table-card {
  padding: 20px;
  border-radius: 16px;
  min-height: 400px;
}
.echart-container {
  height: 350px;
  width: 100%;
}
.glass-panel {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
}
</style>
