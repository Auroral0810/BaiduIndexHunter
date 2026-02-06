<template>
  <div class="keyword-analysis-wrapper">
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
            v-model="taskId" 
            :placeholder="$t('tasks-TaskList-19c298d949224c78d-19')" 
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
                {{ scope.row.avg_success_rate ? scope.row.avg_success_rate.toFixed(2) : '0.00' }}%
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
import { Search, Refresh } from '@element-plus/icons-vue'
import { useAppStore } from '@/store/app'
import { useI18n } from 'vue-i18n'
import * as echarts from 'echarts'
import { getKeywordStatistics } from '@/api/statistics'

const { t: $t } = useI18n()
const appStore = useAppStore()
const isDark = computed(() => appStore.theme === 'dark')

const selectedTaskType = ref('all')
const selectedDays = ref(30)
const dateRange = ref([])

const taskId = ref('')
const loading = ref(false)
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
const tableData = ref([])
const chartRef = ref(null)
let chartInstance = null

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      task_type: selectedTaskType.value !== 'all' ? selectedTaskType.value : undefined,
      task_id: taskId.value || undefined,
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
