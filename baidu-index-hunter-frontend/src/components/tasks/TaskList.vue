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
        <el-option label="已取消" value="cancelled" />
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
            <div v-if="scope.row.parameters" class="task-parameters">
              <!-- 关键词 - 所有任务类型都有 -->
              <div v-if="scope.row.parameters.keywords">
                <strong>关键词:</strong> 
                {{ formatKeywords(scope.row.parameters.keywords) }}
              </div>
              
              <!-- 城市/地区 - 搜索指数、资讯指数和地域分布有 -->
              <div v-if="scope.row.parameters.cities">
                <strong>地区:</strong> 
                {{ formatCities(scope.row.parameters.cities) }}
              </div>
              <div v-if="scope.row.parameters.regions">
                <strong>地区:</strong> 
                {{ formatRegions(scope.row.parameters.regions) }}
              </div>
              
              <!-- 日期 - 不同任务类型有不同的日期参数 -->
              <div v-if="scope.row.parameters.date_ranges">
                <strong>时间范围:</strong> 
                {{ formatDateRanges(scope.row.parameters.date_ranges) }}
              </div>
              <div v-if="scope.row.parameters.days">
                <strong>时间范围:</strong> 最近{{ scope.row.parameters.days }}天
              </div>
              <div v-if="scope.row.parameters.year_range">
                <strong>年份范围:</strong> 
                {{ scope.row.parameters.year_range[0] }} 至 {{ scope.row.parameters.year_range[1] }}
              </div>
              <div v-if="scope.row.parameters.start_date && scope.row.parameters.end_date">
                <strong>时间范围:</strong> 
                {{ scope.row.parameters.start_date }} 至 {{ scope.row.parameters.end_date }}
              </div>
              
              <!-- 需求图谱特有的日期列表 -->
              <div v-if="scope.row.parameters.datelists">
                <strong>日期列表:</strong> 
                {{ formatDatelists(scope.row.parameters.datelists) }}
              </div>
              
              <!-- 批处理大小 - 人群属性和兴趣分析有 -->
              <div v-if="scope.row.parameters.batch_size">
                <strong>批处理大小:</strong> {{ scope.row.parameters.batch_size }}
              </div>
              
              <!-- 输出格式 - 所有任务类型都有 -->
              <div v-if="scope.row.parameters.output_format">
                <strong>输出格式:</strong> 
                {{ scope.row.parameters.output_format === 'csv' ? 'CSV' : 'Excel' }}
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
        <el-table-column label="操作" width="180">
          <template #default="scope">
            <el-button 
              type="primary"
              size="small"
              @click="viewTaskDetail(scope.row)" 
              :disabled="scope.row.status === 'pending'"
              plain
            >
              详情
            </el-button>
            <el-button 
              type="success"
              size="small"
              @click="restartTask(scope.row)" 
              v-if="scope.row.status === 'failed' || scope.row.status === 'cancelled'"
              plain
            >
              重试
            </el-button>
            <el-button 
              type="danger"
              size="small"
              @click="cancelTask(scope.row)" 
              v-if="scope.row.status === 'pending' || scope.row.status === 'running'"
              plain
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
          <!-- 关键词 -->
          <el-descriptions-item v-if="selectedTask.parameters.keywords" label="关键词">
            {{ formatKeywords(selectedTask.parameters.keywords) }}
          </el-descriptions-item>
          
          <!-- 城市/地区 -->
          <el-descriptions-item v-if="selectedTask.parameters.cities" label="地区">
            {{ formatCities(selectedTask.parameters.cities) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedTask.parameters.regions" label="地区">
            {{ formatRegions(selectedTask.parameters.regions) }}
          </el-descriptions-item>
          
          <!-- 日期参数 -->
          <el-descriptions-item v-if="selectedTask.parameters.date_ranges" label="时间范围">
            {{ formatDateRanges(selectedTask.parameters.date_ranges) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedTask.parameters.days" label="时间范围">
            最近{{ selectedTask.parameters.days }}天
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedTask.parameters.year_range" label="年份范围">
            {{ selectedTask.parameters.year_range[0] }} 至 {{ selectedTask.parameters.year_range[1] }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedTask.parameters.start_date && selectedTask.parameters.end_date" label="时间范围">
            {{ selectedTask.parameters.start_date }} 至 {{ selectedTask.parameters.end_date }}
          </el-descriptions-item>
          
          <!-- 需求图谱特有的日期列表 -->
          <el-descriptions-item v-if="selectedTask.parameters.datelists" label="日期列表">
            {{ formatDatelists(selectedTask.parameters.datelists) }}
          </el-descriptions-item>
          
          <!-- 批处理大小 -->
          <el-descriptions-item v-if="selectedTask.parameters.batch_size" label="批处理大小">
            {{ selectedTask.parameters.batch_size }}
          </el-descriptions-item>
          
          <!-- 输出格式 -->
          <el-descriptions-item v-if="selectedTask.parameters.output_format" label="输出格式">
            {{ selectedTask.parameters.output_format === 'csv' ? 'CSV' : 'Excel' }}
          </el-descriptions-item>
          
          <!-- 优先级 -->
          <el-descriptions-item v-if="selectedTask.priority" label="优先级">
            {{ getPriorityLabel(selectedTask.priority) }}
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
        
        <!-- 任务结果 -->
        <div v-if="selectedTask.status === 'completed'" class="task-results">
          <h3>任务结果</h3>
          <el-button type="primary" @click="downloadTaskResult" :loading="downloading">
            <el-icon><Download /></el-icon>下载结果
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { Download } from '@element-plus/icons-vue'

// 定义任务和日志的接口
interface TaskLog {
  id: string;
  taskId: string;
  level: string;
  message: string;
  timestamp: string;
}

interface TaskParameter {
  keywords?: string[] | { value: string }[];
  cities?: Record<string, any>;
  regions?: string[];
  date_ranges?: string[][];
  days?: number;
  year_range?: string[];
  start_date?: string;
  end_date?: string;
  datelists?: string[];
  batch_size?: number;
  output_format?: string;
  resume?: boolean;
  task_id?: string;
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
  priority: number;
  [key: string]: any;
}

const API_BASE_URL = 'http://127.0.0.1:5001/api'

// 任务列表数据
const tasks = ref<Task[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const downloading = ref(false)

// 搜索和筛选
const searchKeyword = ref('')
const taskTypeFilter = ref('')
const statusFilter = ref('')

// 任务详情
const taskDetailDialogVisible = ref(false)
const selectedTask = ref<Task | null>(null)
const taskLogs = ref<TaskLog[]>([])

// 模拟任务日志数据
const mockLogs: Record<string, TaskLog[]> = {
  'TASK-20230615-001': [
    { id: '1', taskId: 'TASK-20230615-001', level: 'info', message: '任务开始执行', timestamp: '2023-06-15 09:15:30' },
    { id: '2', taskId: 'TASK-20230615-001', level: 'info', message: '正在获取搜索指数数据', timestamp: '2023-06-15 09:16:00' },
    { id: '3', taskId: 'TASK-20230615-001', level: 'info', message: '成功获取"小米手机"的搜索指数', timestamp: '2023-06-15 09:18:30' },
    { id: '4', taskId: 'TASK-20230615-001', level: 'info', message: '成功获取"华为手机"的搜索指数', timestamp: '2023-06-15 09:22:15' },
    { id: '5', taskId: 'TASK-20230615-001', level: 'info', message: '成功获取"iPhone"的搜索指数', timestamp: '2023-06-15 09:25:45' },
    { id: '6', taskId: 'TASK-20230615-001', level: 'info', message: '数据处理完成，正在生成CSV文件', timestamp: '2023-06-15 10:28:20' },
    { id: '7', taskId: 'TASK-20230615-001', level: 'info', message: '任务完成', timestamp: '2023-06-15 10:30:45' }
  ],
  'TASK-20230615-002': [
    { id: '1', taskId: 'TASK-20230615-002', level: 'info', message: '任务开始执行', timestamp: '2023-06-15 10:20:20' },
    { id: '2', taskId: 'TASK-20230615-002', level: 'info', message: '正在获取资讯指数数据', timestamp: '2023-06-15 10:21:00' },
    { id: '3', taskId: 'TASK-20230615-002', level: 'info', message: '成功获取"新能源汽车"的资讯指数', timestamp: '2023-06-15 10:35:30' },
    { id: '4', taskId: 'TASK-20230615-002', level: 'info', message: '成功获取"电动车"的资讯指数', timestamp: '2023-06-15 10:45:15' },
    { id: '5', taskId: 'TASK-20230615-002', level: 'warning', message: '获取"混合动力"的资讯指数时遇到限流，正在重试', timestamp: '2023-06-15 10:55:45' }
  ],
  'TASK-20230614-001': [
    { id: '1', taskId: 'TASK-20230614-001', level: 'info', message: '任务开始执行', timestamp: '2023-06-14 15:12:40' },
    { id: '2', taskId: 'TASK-20230614-001', level: 'info', message: '正在获取人群属性数据', timestamp: '2023-06-14 15:13:00' },
    { id: '3', taskId: 'TASK-20230614-001', level: 'info', message: '成功获取"健身"的人群属性', timestamp: '2023-06-14 15:30:30' },
    { id: '4', taskId: 'TASK-20230614-001', level: 'warning', message: '获取"瑜伽"的人群属性时遇到限流，正在重试', timestamp: '2023-06-14 15:45:15' },
    { id: '5', taskId: 'TASK-20230614-001', level: 'error', message: 'Cookie被封禁，任务失败', timestamp: '2023-06-14 16:45:21' }
  ],
  'TASK-20230614-002': [
    { id: '1', taskId: 'TASK-20230614-002', level: 'info', message: '任务开始执行', timestamp: '2023-06-14 16:30:20' },
    { id: '2', taskId: 'TASK-20230614-002', level: 'info', message: '正在获取兴趣分析数据', timestamp: '2023-06-14 16:31:00' },
    { id: '3', taskId: 'TASK-20230614-002', level: 'info', message: '成功获取"游戏"的兴趣分析', timestamp: '2023-06-14 16:50:30' },
    { id: '4', taskId: 'TASK-20230614-002', level: 'info', message: '成功获取"电子竞技"的兴趣分析', timestamp: '2023-06-14 17:10:15' },
    { id: '5', taskId: 'TASK-20230614-002', level: 'info', message: '成功获取"手游"的兴趣分析', timestamp: '2023-06-14 17:30:45' },
    { id: '6', taskId: 'TASK-20230614-002', level: 'info', message: '数据处理完成，正在生成CSV文件', timestamp: '2023-06-14 17:43:20' },
    { id: '7', taskId: 'TASK-20230614-002', level: 'info', message: '任务完成', timestamp: '2023-06-14 17:45:33' }
  ],
  'TASK-20230613-001': [
    { id: '1', taskId: 'TASK-20230613-001', level: 'info', message: '任务开始执行', timestamp: '2023-06-13 09:45:30' },
    { id: '2', taskId: 'TASK-20230613-001', level: 'info', message: '正在获取地域分布数据', timestamp: '2023-06-13 09:46:00' },
    { id: '3', taskId: 'TASK-20230613-001', level: 'info', message: '成功获取"旅游"的地域分布', timestamp: '2023-06-13 10:00:30' },
    { id: '4', taskId: 'TASK-20230613-001', level: 'warning', message: '用户手动取消任务', timestamp: '2023-06-13 10:30:15' }
  ]
}

// 加载任务列表
let loadTasks = async () => {
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
const viewTaskDetail = async (task: Task) => {
  selectedTask.value = task
  taskDetailDialogVisible.value = true
  await loadTaskLogs(task.taskId)
}

// 加载任务日志
let loadTaskLogs = async (taskId: string) => {
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
let restartTask = async (task: Task) => {
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
let cancelTask = async (task: Task) => {
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

// 下载任务结果
let downloadTaskResult = async () => {
  if (!selectedTask.value) return
  
  downloading.value = true
  try {
    const response = await axios.get(`${API_BASE_URL}/task/${selectedTask.value.taskId}/download`, {
      responseType: 'blob'
    })
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    
    // 设置文件名
    const taskType = translateTaskType(selectedTask.value.taskType)
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const extension = selectedTask.value.parameters.output_format === 'csv' ? 'csv' : 'xlsx'
    link.setAttribute('download', `${taskType}_${timestamp}.${extension}`)
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('下载成功')
  } catch (error) {
    ElMessage.error('下载失败，请检查网络连接')
    console.error('下载任务结果错误:', error)
  } finally {
    downloading.value = false
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
  if (status === 'cancelled') return 'warning'
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

const getPriorityLabel = (priority: number) => {
  if (priority >= 8) return '高'
  if (priority >= 4) return '中'
  return '低'
}

// 格式化关键词
const formatKeywords = (keywords: any) => {
  if (Array.isArray(keywords)) {
    // 处理对象数组 [{value: '关键词1'}, {value: '关键词2'}]
    if (keywords.length > 0 && typeof keywords[0] === 'object' && 'value' in keywords[0]) {
      return keywords.map(k => k.value).join(', ')
    }
    // 处理字符串数组 ['关键词1', '关键词2']
    return keywords.join(', ')
  }
  return keywords
}

// 格式化城市
const formatCities = (cities: Record<string, any>) => {
  if (!cities) return ''
  const cityNames = Object.values(cities).map(city => city.name || city.code)
  return cityNames.join(', ')
}

// 格式化地区
const formatRegions = (regions: string[]) => {
  if (!regions) return ''
  return regions.join(', ')
}

// 格式化日期范围
const formatDateRanges = (dateRanges: string[][]) => {
  if (!dateRanges || !dateRanges.length) return ''
  return dateRanges.map(range => `${range[0]} 至 ${range[1]}`).join('; ')
}

// 格式化日期列表
const formatDatelists = (datelists: string[]) => {
  if (!datelists || !datelists.length) return ''
  return datelists.map(date => {
    if (date.length === 8) {
      return `${date.substring(0, 4)}-${date.substring(4, 6)}-${date.substring(6, 8)}`
    }
    return date
  }).join(', ')
}

// 自动刷新任务列表
const setupRefreshInterval = () => {
  const intervalId = setInterval(() => {
    if (!taskDetailDialogVisible.value) { // 不在详情页面时刷新
      loadTasks()
    }
  }, 30000) // 每30秒刷新一次
  
  // 组件卸载时清除定时器
  onMounted(() => {
    return () => {
      clearInterval(intervalId)
    }
  })
  
  return intervalId
}

// 监听详情对话框关闭
watch(() => taskDetailDialogVisible.value, (newVal) => {
  if (!newVal && selectedTask.value) {
    loadTasks() // 关闭详情对话框时刷新列表
  }
})

// 初始加载
onMounted(() => {
  // 模拟数据 - 仅用于开发测试
  if (import.meta.env.DEV || true) { // 强制使用模拟数据，无论是否为开发环境
    console.log("使用模拟数据");
    // 添加模拟数据
    const mockTasks: Task[] = [
      {
        taskId: 'TASK-20230615-001',
        taskType: 'search_index',
        status: 'completed',
        progress: 100,
        parameters: {
          keywords: ['小米手机', '华为手机', 'iPhone'],
          cities: {
            '0': { name: '全国', code: '0' },
            '928': { name: '北京', code: '928' }
          },
          date_ranges: [['2023-01-01', '2023-06-01']],
          output_format: 'csv'
        },
        createdAt: '2023-06-15 09:15:23',
        updatedAt: '2023-06-15 10:30:45',
        priority: 8
      },
      {
        taskId: 'TASK-20230615-002',
        taskType: 'feed_index',
        status: 'running',
        progress: 65,
        parameters: {
          keywords: ['新能源汽车', '电动车', '混合动力'],
          cities: {
            '0': { name: '全国', code: '0' }
          },
          days: 30,
          output_format: 'excel'
        },
        createdAt: '2023-06-15 10:20:11',
        updatedAt: '2023-06-15 11:05:32',
        priority: 5
      },
      {
        taskId: 'TASK-20230615-003',
        taskType: 'word_graph',
        status: 'pending',
        progress: 0,
        parameters: {
          keywords: ['人工智能', '机器学习', '深度学习'],
          datelists: ['20230101', '20230201', '20230301'],
          output_format: 'csv'
        },
        createdAt: '2023-06-15 11:30:45',
        updatedAt: '2023-06-15 11:30:45',
        priority: 3
      },
      {
        taskId: 'TASK-20230614-001',
        taskType: 'demographic_attributes',
        status: 'failed',
        progress: 35,
        parameters: {
          keywords: ['健身', '瑜伽', '跑步'],
          batch_size: 10,
          output_format: 'excel'
        },
        createdAt: '2023-06-14 15:12:33',
        updatedAt: '2023-06-14 16:45:21',
        priority: 6
      },
      {
        taskId: 'TASK-20230614-002',
        taskType: 'interest_profile',
        status: 'completed',
        progress: 100,
        parameters: {
          keywords: ['游戏', '电子竞技', '手游'],
          batch_size: 5,
          output_format: 'csv'
        },
        createdAt: '2023-06-14 16:30:12',
        updatedAt: '2023-06-14 17:45:33',
        priority: 4
      },
      {
        taskId: 'TASK-20230613-001',
        taskType: 'region_distribution',
        status: 'cancelled',
        progress: 20,
        parameters: {
          keywords: ['旅游', '度假', '酒店'],
          regions: ['0', '928', '2005'],
          start_date: '2023-01-01',
          end_date: '2023-05-31',
          output_format: 'excel'
        },
        createdAt: '2023-06-13 09:45:22',
        updatedAt: '2023-06-13 10:30:15',
        priority: 7
      },
      {
        taskId: 'TASK-20230612-001',
        taskType: 'search_index',
        status: 'completed',
        progress: 100,
        parameters: {
          keywords: ['教育培训', '在线课程', '考研'],
          cities: {
            '928': { name: '北京', code: '928' },
            '2005': { name: '上海', code: '2005' }
          },
          year_range: ['2022', '2023'],
          output_format: 'csv'
        },
        createdAt: '2023-06-12 14:20:33',
        updatedAt: '2023-06-12 15:45:12',
        priority: 9
      },
      {
        taskId: 'TASK-20230611-001',
        taskType: 'feed_index',
        status: 'completed',
        progress: 100,
        parameters: {
          keywords: ['美食', '餐厅', '烹饪'],
          cities: {
            '0': { name: '全国', code: '0' }
          },
          days: 90,
          output_format: 'excel'
        },
        createdAt: '2023-06-11 10:15:45',
        updatedAt: '2023-06-11 12:30:22',
        priority: 5
      },
      {
        taskId: 'TASK-20230610-001',
        taskType: 'word_graph',
        status: 'failed',
        progress: 75,
        parameters: {
          keywords: ['区块链', '比特币', '以太坊'],
          datelists: ['20230401', '20230501', '20230601'],
          output_format: 'csv'
        },
        createdAt: '2023-06-10 16:40:12',
        updatedAt: '2023-06-10 18:15:33',
        priority: 2
      },
      {
        taskId: 'TASK-20230609-001',
        taskType: 'demographic_attributes',
        status: 'completed',
        progress: 100,
        parameters: {
          keywords: ['化妆品', '护肤', '美妆'],
          batch_size: 20,
          output_format: 'excel'
        },
        createdAt: '2023-06-09 11:20:45',
        updatedAt: '2023-06-09 13:30:12',
        priority: 8
      }
    ];

    // 覆盖加载任务的方法，使用模拟数据
    loadTasks = async () => {
      loading.value = true;
      
      // 根据筛选条件过滤任务
      let filteredTasks = [...mockTasks];
      
      if (searchKeyword.value) {
        const keyword = searchKeyword.value.toLowerCase();
        filteredTasks = filteredTasks.filter(task => {
          const keywords = task.parameters.keywords;
          if (Array.isArray(keywords)) {
            return keywords.some(k => {
              if (typeof k === 'object' && k.value) {
                return k.value.toLowerCase().includes(keyword);
              }
              return String(k).toLowerCase().includes(keyword);
            });
          }
          return task.taskId.toLowerCase().includes(keyword);
        });
      }
      
      if (taskTypeFilter.value) {
        filteredTasks = filteredTasks.filter(task => task.taskType === taskTypeFilter.value);
      }
      
      if (statusFilter.value) {
        filteredTasks = filteredTasks.filter(task => task.status === statusFilter.value);
      }
      
      // 计算分页
      total.value = filteredTasks.length;
      const start = (currentPage.value - 1) * pageSize.value;
      const end = start + pageSize.value;
      tasks.value = filteredTasks.slice(start, end);
      
      loading.value = false;
    };
    
    // 覆盖加载任务日志的方法
    loadTaskLogs = async (taskId: string) => {
      setTimeout(() => {
        taskLogs.value = mockLogs[taskId] || [];
      }, 300);
    };
    
    // 覆盖重试任务的方法
    restartTask = async (task: Task) => {
      ElMessage.success('任务已重新提交');
      task.status = 'pending';
      task.progress = 0;
      task.updatedAt = new Date().toISOString().replace('T', ' ').substring(0, 19);
      loadTasks();
    };
    
    // 覆盖取消任务的方法
    cancelTask = async (task: Task) => {
      ElMessage.success('任务已取消');
      task.status = 'cancelled';
      task.updatedAt = new Date().toISOString().replace('T', ' ').substring(0, 19);
      loadTasks();
    };
    
    // 覆盖下载任务结果的方法
    downloadTaskResult = async () => {
      if (!selectedTask.value) return;
      
      downloading.value = true;
      
      setTimeout(() => {
        ElMessage.success('下载成功');
        downloading.value = false;
      }, 1500);
    };
    
    // 立即加载模拟数据
    loadTasks();
  } else {
    // 正常加载数据
    loadTasks();
    setupRefreshInterval();
  }
})
</script>

<style scoped>
.task-list-container {
  padding: 20px;
}

.task-list-container h2 {
  margin-bottom: 20px;
  font-size: 24px;
  color: #409EFF;
}

.search-bar {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  background-color: #f9fafb;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.table-wrapper {
  margin-bottom: 20px;
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.task-parameters {
  font-size: 13px;
}

.task-parameters div {
  margin-bottom: 5px;
}

.task-parameters div:last-child {
  margin-bottom: 0;
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
  color: #409EFF;
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

.task-results {
  margin-top: 20px;
  padding: 15px;
  background-color: #f0f9eb;
  border-radius: 4px;
  border-left: 4px solid #67c23a;
}
</style> 