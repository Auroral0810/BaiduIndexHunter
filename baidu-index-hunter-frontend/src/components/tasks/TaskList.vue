<template>
  <div class="task-list-container">
    <h2>任务列表</h2>
    
    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索关键词"
        clearable
        style="width: 200px; margin-right: 10px"
      />
      <el-select
        v-model="taskTypeFilter"
        placeholder="任务类型"
        clearable
        style="width: 150px; margin-right: 10px"
      >
        <el-option label="搜索指数" value="search_index" />
        <el-option label="资讯指数" value="feed_index" />
        <el-option label="需求图谱" value="word_graph" />
        <el-option label="人群属性" value="demographic_attributes" />
        <el-option label="兴趣分析" value="interest_profile" />
        <el-option label="地域分布" value="region_distribution" />
      </el-select>
      <el-select
        v-model="statusFilter"
        placeholder="任务状态"
        clearable
        style="width: 150px; margin-right: 10px"
      >
        <el-option label="等待中" value="pending" />
        <el-option label="执行中" value="running" />
        <el-option label="已完成" value="completed" />
        <el-option label="失败" value="failed" />
      </el-select>
      <el-button type="primary" @click="loadTasks">搜索</el-button>
      <el-button @click="resetFilters">重置</el-button>
    </div>
    
    <div class="table-wrapper">
      <el-table
        v-loading="loading"
        :data="tasks"
        style="width: 100%"
        border
        stripe
      >
        <el-table-column prop="taskId" label="任务ID" width="200" />
        <el-table-column label="任务类型" width="120">
          <template #default="scope">
            <el-tag :type="getTaskTypeTag(scope.row.taskType)">
              {{ translateTaskType(scope.row.taskType) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusTag(scope.row.status)">
              {{ translateStatus(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="参数">
          <template #default="scope">
            <div v-if="scope.row.parameters">
              <div v-if="scope.row.parameters.keywords">
                <strong>关键词:</strong> 
                {{ Array.isArray(scope.row.parameters.keywords) 
                  ? scope.row.parameters.keywords.join(', ') 
                  : scope.row.parameters.keywords 
                }}
              </div>
              <div v-if="scope.row.parameters.cityCode">
                <strong>城市:</strong> {{ scope.row.parameters.cityCode }}
              </div>
              <div v-if="scope.row.parameters.startDate || scope.row.parameters.endDate">
                <strong>时间范围:</strong> 
                {{ scope.row.parameters.startDate || '-' }} 
                至 
                {{ scope.row.parameters.endDate || '-' }}
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="180" />
        <el-table-column label="进度" width="150">
          <template #default="scope">
            <el-progress 
              :percentage="scope.row.progress || 0" 
              :status="getProgressStatus(scope.row.status)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="scope">
            <el-button 
              type="text" 
              @click="viewTaskDetail(scope.row)" 
              :disabled="scope.row.status === 'pending'"
            >
              详情
            </el-button>
            <el-button 
              type="text" 
              @click="restartTask(scope.row)" 
              v-if="scope.row.status === 'failed'"
            >
              重试
            </el-button>
            <el-button 
              type="text" 
              @click="cancelTask(scope.row)" 
              v-if="scope.row.status === 'pending' || scope.row.status === 'running'"
            >
              取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 30, 50]"
        layout="total, sizes, prev, pager, next"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
    
    <!-- 任务详情对话框 -->
    <el-dialog
      v-model="taskDetailDialogVisible"
      title="任务详情"
      width="700px"
      destroy-on-close
    >
      <div v-if="selectedTask" class="task-detail">
        <el-descriptions bordered :column="2">
          <el-descriptions-item label="任务ID" :span="2">
            {{ selectedTask.taskId }}
          </el-descriptions-item>
          <el-descriptions-item label="任务类型">
            {{ translateTaskType(selectedTask.taskType) }}
          </el-descriptions-item>
          <el-descriptions-item label="任务状态">
            <el-tag :type="getStatusTag(selectedTask.status)">
              {{ translateStatus(selectedTask.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">
            {{ selectedTask.createdAt }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ selectedTask.updatedAt }}
          </el-descriptions-item>
          <el-descriptions-item label="进度" :span="2">
            <el-progress 
              :percentage="selectedTask.progress || 0" 
              :status="getProgressStatus(selectedTask.status)"
            />
          </el-descriptions-item>
        </el-descriptions>
        
        <h3>任务参数</h3>
        <el-descriptions bordered :column="1">
          <el-descriptions-item v-for="(value, key) in selectedTask.parameters" :key="key" :label="translateParamKey(key)">
            {{ formatParamValue(key, value) }}
          </el-descriptions-item>
        </el-descriptions>
        
        <h3>任务日志</h3>
        <div class="task-logs">
          <el-timeline v-if="taskLogs.length > 0">
            <el-timeline-item
              v-for="log in taskLogs"
              :key="log.id"
              :timestamp="log.timestamp"
              :type="getLogTypeIcon(log.level)"
            >
              {{ log.message }}
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无日志" />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

// 定义任务和日志的接口
interface TaskLog {
  id: string;
  taskId: string;
  level: string;
  message: string;
  timestamp: string;
}

interface TaskParameter {
  keywords?: string[];
  cityCode?: string;
  startDate?: string;
  endDate?: string;
  dataType?: string;
  regionLevel?: string;
  attributeType?: string;
  interestType?: string;
  [key: string]: any;
}

interface Task {
  taskId: string;
  taskType: string;
  status: string;
  progress: number;
  parameters: TaskParameter;
  createdAt: string;
  updatedAt: string;
  [key: string]: any;
}

const API_BASE_URL = 'http://localhost:4000/api'

// 任务列表数据
const tasks = ref<Task[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

// 搜索和筛选
const searchKeyword = ref('')
const taskTypeFilter = ref('')
const statusFilter = ref('')

// 任务详情
const taskDetailDialogVisible = ref(false)
const selectedTask = ref<Task | null>(null)
const taskLogs = ref<TaskLog[]>([])

// 加载任务列表
const loadTasks = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      limit: pageSize.value,
      keyword: searchKeyword.value || undefined,
      taskType: taskTypeFilter.value || undefined,
      status: statusFilter.value || undefined
    }
    
    const response = await axios.get(`${API_BASE_URL}/task/list`, { params })
    
    if (response.data.code === 0) {
      tasks.value = response.data.data.tasks || []
      total.value = response.data.data.total || 0
    } else {
      ElMessage.error(`获取任务列表失败: ${response.data.message}`)
    }
  } catch (error) {
    ElMessage.error('获取任务列表失败，请检查网络连接')
    console.error('加载任务列表错误:', error)
  } finally {
    loading.value = false
  }
}

// 重置筛选条件
const resetFilters = () => {
  searchKeyword.value = ''
  taskTypeFilter.value = ''
  statusFilter.value = ''
  currentPage.value = 1
  loadTasks()
}

// 处理分页变化
const handleSizeChange = (size: number) => {
  pageSize.value = size
  loadTasks()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadTasks()
}

// 查看任务详情
const viewTaskDetail = async (task: any) => {
  selectedTask.value = task
  taskDetailDialogVisible.value = true
  await loadTaskLogs(task.taskId)
}

// 加载任务日志
const loadTaskLogs = async (taskId: string) => {
  try {
    const response = await axios.get(`${API_BASE_URL}/task/${taskId}/logs`)
    if (response.data.code === 0) {
      taskLogs.value = response.data.data || []
    } else {
      taskLogs.value = []
      console.error('获取任务日志失败:', response.data.message)
    }
  } catch (error) {
    taskLogs.value = []
    console.error('加载任务日志错误:', error)
  }
}

// 重试任务
const restartTask = async (task: any) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/task/${task.taskId}/restart`)
    
    if (response.data.code === 0) {
      ElMessage.success('任务已重新提交')
      loadTasks()
    } else {
      ElMessage.error(`重试任务失败: ${response.data.message}`)
    }
  } catch (error) {
    ElMessage.error('重试任务失败，请检查网络连接')
    console.error('重试任务错误:', error)
  }
}

// 取消任务
const cancelTask = async (task: any) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/task/${task.taskId}/cancel`)
    
    if (response.data.code === 0) {
      ElMessage.success('任务已取消')
      loadTasks()
    } else {
      ElMessage.error(`取消任务失败: ${response.data.message}`)
    }
  } catch (error) {
    ElMessage.error('取消任务失败，请检查网络连接')
    console.error('取消任务错误:', error)
  }
}

// 辅助函数
const translateTaskType = (type: string) => {
  const typeMap: Record<string, string> = {
    'search_index': '搜索指数',
    'feed_index': '资讯指数',
    'word_graph': '需求图谱',
    'demographic_attributes': '人群属性',
    'interest_profile': '兴趣分析',
    'region_distribution': '地域分布'
  }
  return typeMap[type] || type
}

const translateStatus = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': '等待中',
    'running': '执行中',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

const getTaskTypeTag = (type: string) => {
  const typeMap: Record<string, string> = {
    'search_index': 'primary',
    'feed_index': 'success',
    'word_graph': 'warning',
    'demographic_attributes': 'danger',
    'interest_profile': 'info',
    'region_distribution': ''
  }
  return typeMap[type] || ''
}

const getStatusTag = (status: string) => {
  const statusMap: Record<string, string> = {
    'pending': 'info',
    'running': 'warning',
    'completed': 'success',
    'failed': 'danger',
    'cancelled': 'info'
  }
  return statusMap[status] || ''
}

const getProgressStatus = (status: string) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  return ''
}

const getLogTypeIcon = (level: string) => {
  const levelMap: Record<string, string> = {
    'info': 'primary',
    'warning': 'warning',
    'error': 'danger',
    'debug': 'info'
  }
  return levelMap[level] || 'info'
}

const translateParamKey = (key: string) => {
  const keyMap: Record<string, string> = {
    'keywords': '关键词',
    'cityCode': '城市',
    'startDate': '开始日期',
    'endDate': '结束日期',
    'dataType': '数据类型',
    'regionLevel': '区域等级',
    'attributeType': '属性类型',
    'interestType': '兴趣类型'
  }
  return keyMap[key] || key
}

const formatParamValue = (key: string, value: any) => {
  if (key === 'keywords' && Array.isArray(value)) {
    return value.join(', ')
  }
  if (key === 'dataType') {
    const dataTypeMap: Record<string, string> = {
      'all': '整体趋势',
      'pc': 'PC趋势',
      'wise': '移动趋势'
    }
    return dataTypeMap[value as string] || value
  }
  if (key === 'regionLevel') {
    return (value as string) === 'province' ? '省级' : '城市级'
  }
  if (key === 'attributeType') {
    const attributeMap: Record<string, string> = {
      'age': '年龄分布',
      'gender': '性别分布',
      'education': '学历水平'
    }
    return attributeMap[value as string] || value
  }
  if (key === 'interestType') {
    const interestMap: Record<string, string> = {
      'general': '综合兴趣',
      'ecommerce': '电商消费',
      'app': 'APP偏好'
    }
    return interestMap[value as string] || value
  }
  return value
}

// 自动刷新任务列表
const setupRefreshInterval = () => {
  const intervalId = setInterval(() => {
    if (!taskDetailDialogVisible.value) { // 不在详情页面时刷新
      loadTasks()
    }
  }, 30000) // 每30秒刷新一次
  
  onMounted(() => {
    loadTasks()
  })
  
  watch(() => taskDetailDialogVisible.value, (newVal) => {
    if (!newVal && selectedTask.value) {
      loadTasks() // 关闭详情对话框时刷新列表
    }
  })
  
  return intervalId
}

const intervalId = setupRefreshInterval()

// 组件卸载时清除定时器
onMounted(() => {
  return () => {
    clearInterval(intervalId)
  }
})

// 初始加载
onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.task-list-container {
  padding: 20px;
}

.search-bar {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.table-wrapper {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.task-detail {
  margin-top: 20px;
}

.task-detail h3 {
  margin: 20px 0 10px;
  font-size: 16px;
}

.task-logs {
  margin-top: 10px;
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 10px;
  background-color: #f9f9f9;
}
</style> 