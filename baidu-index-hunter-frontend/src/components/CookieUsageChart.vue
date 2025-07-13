<script setup>
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const props = defineProps({
  apiBaseUrl: {
    type: String,
    default: 'http://127.0.0.1:5001/api'
  }
})

const chartDom = ref(null)
const usageChartInstance = ref(null)
const cookieUsageData = ref([])
const cookieUsageLoading = ref(false)
const dateRange = ref([])
const topN = ref(10)
const viewMode = ref('daily') // 'daily' | 'account'

// 图表配置
const dailyChartOption = reactive({
  title: {
    text: '每日Cookie使用量统计',
    left: 'center'
  },
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow'
    }
  },
  toolbox: {
    feature: {
      saveAsImage: {}
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: [],
    axisLabel: {
      rotate: 45
    }
  },
  yAxis: {
    type: 'value',
    name: '使用次数'
  },
  series: [
    {
      name: '使用量',
      type: 'bar',
      data: [],
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#83bff6' },
          { offset: 0.5, color: '#188df0' },
          { offset: 1, color: '#188df0' }
        ])
      },
      emphasis: {
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#2378f7' },
            { offset: 0.7, color: '#2378f7' },
            { offset: 1, color: '#83bff6' }
          ])
        }
      }
    }
  ]
})

const accountChartOption = reactive({
  title: {
    text: 'Cookie账号使用量排行',
    left: 'center'
  },
  tooltip: {
    trigger: 'axis',
    axisPointer: {
      type: 'shadow'
    }
  },
  toolbox: {
    feature: {
      saveAsImage: {}
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'value',
    name: '使用次数'
  },
  yAxis: {
    type: 'category',
    data: [],
    axisLabel: {
      width: 120,
      overflow: 'truncate'
    }
  },
  series: [
    {
      name: '使用量',
      type: 'bar',
      data: [],
      itemStyle: {
        color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
          { offset: 0, color: '#83bff6' },
          { offset: 0.5, color: '#188df0' },
          { offset: 1, color: '#188df0' }
        ])
      },
      emphasis: {
        itemStyle: {
          color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
            { offset: 0, color: '#2378f7' },
            { offset: 0.7, color: '#2378f7' },
            { offset: 1, color: '#83bff6' }
          ])
        }
      }
    }
  ]
})

// 加载Cookie使用量数据
const loadCookieUsage = async (startDate = null, endDate = null) => {
  try {
    cookieUsageLoading.value = true
    
    let params = {}
    if (startDate && endDate) {
      params.start_date = startDate
      params.end_date = endDate
    }
    
    const response = await axios.get(`${props.apiBaseUrl}/admin/cookie/usage`, { params })
    if (response.data.code === 10000) {
      cookieUsageData.value = response.data.data || []
      updateUsageChart()
    } else {
      ElMessage.error(`获取Cookie使用量数据失败: ${response.data.msg}`)
    }
  } catch (error) {
    console.error('获取Cookie使用量数据失败:', error)
    ElMessage.error('获取Cookie使用量数据失败，请检查网络连接')
  } finally {
    cookieUsageLoading.value = false
  }
}

// 更新使用量图表
const updateUsageChart = () => {
  if (!chartDom.value) return
  
  if (viewMode.value === 'daily') {
    updateDailyChart()
  } else {
    updateAccountChart()
  }
}

// 更新每日使用量图表
const updateDailyChart = () => {
  // 按日期分组数据
  const groupedByDate = {}
  cookieUsageData.value.forEach(item => {
    if (!groupedByDate[item.usage_date]) {
      groupedByDate[item.usage_date] = 0
    }
    groupedByDate[item.usage_date] += item.usage_count
  })
  
  // 转换为图表数据
  const dates = Object.keys(groupedByDate).sort()
  const values = dates.map(date => groupedByDate[date])
  
  // 更新图表配置
  dailyChartOption.xAxis.data = dates
  dailyChartOption.series[0].data = values
  
  // 渲染图表
  if (!usageChartInstance.value) {
    usageChartInstance.value = echarts.init(chartDom.value)
  }
  usageChartInstance.value.setOption(dailyChartOption)
}

// 更新账号使用量图表
const updateAccountChart = () => {
  // 按账号分组数据
  const groupedByAccount = {}
  cookieUsageData.value.forEach(item => {
    if (!groupedByAccount[item.account_id]) {
      groupedByAccount[item.account_id] = 0
    }
    groupedByAccount[item.account_id] += item.usage_count
  })
  
  // 转换为图表数据并排序
  let accountData = Object.entries(groupedByAccount)
    .map(([account, count]) => ({ account, count }))
    .sort((a, b) => b.count - a.count)
  
  // 只取前N个
  accountData = accountData.slice(0, topN.value)
  
  const accounts = accountData.map(item => item.account)
  const values = accountData.map(item => item.count)
  
  // 更新图表配置
  accountChartOption.yAxis.data = accounts
  accountChartOption.series[0].data = values
  
  // 渲染图表
  if (!usageChartInstance.value) {
    usageChartInstance.value = echarts.init(chartDom.value)
  }
  usageChartInstance.value.setOption(accountChartOption)
}

// 处理日期范围变化
const handleDateRangeChange = () => {
  if (dateRange.value && dateRange.value.length === 2) {
    const startDate = formatDate(dateRange.value[0])
    const endDate = formatDate(dateRange.value[1])
    loadCookieUsage(startDate, endDate)
  }
}

// 格式化日期
const formatDate = (date) => {
  if (!date) return ''
  const d = new Date(date)
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

// 同步Redis和MySQL中的使用量数据
const syncUsageData = async () => {
  try {
    cookieUsageLoading.value = true
    
    const response = await axios.post(`${props.apiBaseUrl}/admin/cookie/usage/sync`)
    if (response.data.code === 10000) {
      ElMessage.success('Cookie使用量数据同步成功')
      loadCookieUsage()
    } else {
      ElMessage.error(`同步Cookie使用量数据失败: ${response.data.msg}`)
    }
  } catch (error) {
    console.error('同步Cookie使用量数据失败:', error)
    ElMessage.error('同步Cookie使用量数据失败，请检查网络连接')
  } finally {
    cookieUsageLoading.value = false
  }
}

// 切换视图模式
const switchViewMode = (mode) => {
  viewMode.value = mode
  updateUsageChart()
}

// 监听视图模式变化
watch(viewMode, () => {
  updateUsageChart()
})

// 监听topN变化
watch(topN, () => {
  if (viewMode.value === 'account') {
    updateUsageChart()
  }
})

// 生命周期钩子
onMounted(() => {
  loadCookieUsage()
  
  // 添加窗口大小变化监听
  window.addEventListener('resize', handleResize)
})

// 窗口大小变化时重绘图表
const handleResize = () => {
  if (usageChartInstance.value) {
    usageChartInstance.value.resize()
  }
}

// 在组件卸载时清除资源
onUnmounted(() => {
  // 销毁图表实例
  if (usageChartInstance.value) {
    usageChartInstance.value.dispose()
    usageChartInstance.value = null
  }
  
  // 移除窗口大小变化监听
  window.removeEventListener('resize', handleResize)
})

// 暴露方法给父组件
defineExpose({
  loadCookieUsage,
  syncUsageData
})
</script>

<template>
  <div class="cookie-usage-chart-container">
    <div class="chart-header">
      <div class="chart-controls">
        <el-radio-group v-model="viewMode" size="small">
          <el-radio-button label="daily">每日统计</el-radio-button>
          <el-radio-button label="account">账号排行</el-radio-button>
        </el-radio-group>
        
        <el-input-number 
          v-if="viewMode === 'account'"
          v-model="topN" 
          :min="5" 
          :max="50" 
          size="small"
          class="top-n-selector"
          placeholder="显示前N个"
        />
        
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          size="small"
          @change="handleDateRangeChange"
        />
        
        <el-button 
          type="primary" 
          size="small" 
          @click="syncUsageData" 
          :loading="cookieUsageLoading"
        >
          同步使用量数据
        </el-button>
      </div>
    </div>
    
    <div 
      ref="chartDom" 
      class="chart-container" 
      v-loading="cookieUsageLoading"
    ></div>
  </div>
</template>

<style scoped>
.cookie-usage-chart-container {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.chart-header {
  margin-bottom: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-controls {
  display: flex;
  gap: 15px;
  align-items: center;
  flex-wrap: wrap;
}

.top-n-selector {
  width: 120px;
}

.chart-container {
  height: 400px;
  width: 100%;
}

@media (max-width: 768px) {
  .chart-controls {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .chart-container {
    height: 300px;
  }
}
</style> 