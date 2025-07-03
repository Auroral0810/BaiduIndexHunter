<!-- 爬虫统计页面 -->
<template>
  <div class="statistics-container">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>爬虫统计数据</span>
          <div class="filter-container">
            <el-date-picker
              v-model="queryParams.date"
              type="date"
              placeholder="选择日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              @change="loadData"
            />
            <el-select v-model="queryParams.taskType" placeholder="任务类型" clearable @change="loadData">
              <el-option
                v-for="item in taskTypeOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            <el-button type="primary" @click="loadData">查询</el-button>
            <el-button @click="resetQuery">重置</el-button>
          </div>
        </div>
      </template>
      
      <el-table :data="statisticsData" stripe style="width: 100%">
        <el-table-column prop="stat_date" label="日期" width="120" />
        <el-table-column prop="task_type" label="任务类型" width="120">
          <template #default="scope">
            {{ formatTaskType(scope.row.task_type) }}
          </template>
        </el-table-column>
        <el-table-column prop="total_tasks" label="任务总数" width="100" />
        <el-table-column prop="completed_tasks" label="完成任务" width="100" />
        <el-table-column prop="failed_tasks" label="失败任务" width="100" />
        <el-table-column prop="total_items" label="数据总量" width="100" />
        <el-table-column prop="total_crawled_items" label="累计爬取条数" width="120" />
        <el-table-column prop="success_rate" label="成功率" width="100">
          <template #default="scope">
            {{ scope.row.success_rate ? scope.row.success_rate.toFixed(2) + '%' : '0%' }}
          </template>
        </el-table-column>
        <el-table-column prop="avg_duration" label="平均耗时(秒)" width="120">
          <template #default="scope">
            {{ scope.row.avg_duration ? scope.row.avg_duration.toFixed(2) : '0' }}
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination-container">
        <el-pagination
          :current-page="currentPage"
          :page-sizes="[10, 20, 50, 100]"
          :page-size="pageSize"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { getSpiderStatistics } from '@/api/statistics'
import { ElMessage } from 'element-plus'

// 查询参数
const queryParams = ref({
  date: '',
  taskType: ''
})

// 任务类型选项
const taskTypeOptions = [
  { value: 'index', label: '搜索指数' },
  { value: 'news', label: '资讯指数' },
  { value: 'feedindex', label: '需求图谱' },
  { value: 'region', label: '地域分布' },
  { value: 'crowd', label: '人群分布' }
]

// 数据
const allStatisticsData = ref([])
const statisticsData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return allStatisticsData.value.slice(start, end)
})

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const total = computed(() => allStatisticsData.value.length)

// 加载数据
const loadData = async () => {
  try {
    const res = await getSpiderStatistics(queryParams.value)
    if (res.code === 10000) {
      allStatisticsData.value = res.data.statistics
      currentPage.value = 1
    } else {
      ElMessage.error(res.msg || '获取统计数据失败')
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
    ElMessage.error('加载统计数据失败')
  }
}

// 重置查询
const resetQuery = () => {
  queryParams.value = {
    date: '',
    taskType: ''
  }
  loadData()
}

// 分页操作
const handleSizeChange = (val) => {
  pageSize.value = val
}

const handleCurrentChange = (val) => {
  currentPage.value = val
}

// 格式化任务类型
const formatTaskType = (type) => {
  const option = taskTypeOptions.find(item => item.value === type)
  return option ? option.label : type
}

// 页面加载时获取数据
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.statistics-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-container {
  display: flex;
  gap: 10px;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style> 