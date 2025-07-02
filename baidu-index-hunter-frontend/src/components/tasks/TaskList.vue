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
        <el-table-column label="操作" width="240">
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
            <el-button 
              type="primary"
              size="small"
              @click="downloadTaskResult(scope.row)" 
              v-if="scope.row.status === 'completed' && scope.row.output_files && scope.row.output_files.length > 0"
              plain
            >
              下载
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
            {{ selectedTask.createdAt || selectedTask.create_time }}
          </el-descriptions-item>
          <el-descriptions-item label="更新时间">
            {{ selectedTask.updatedAt || selectedTask.update_time }}
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
          <el-descriptions-item v-if="selectedTask.parameters && selectedTask.parameters.keywords" label="关键词">
            {{ formatKeywords(selectedTask.parameters.keywords) }}
          </el-descriptions-item>
          
          <!-- 城市/地区 -->
          <el-descriptions-item v-if="selectedTask.parameters && selectedTask.parameters.cities" label="地区">
            {{ formatCities(selectedTask.parameters.cities) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedTask.parameters && selectedTask.parameters.regions" label="地区">
            {{ formatRegions(selectedTask.parameters.regions) }}
          </el-descriptions-item>
          
          <!-- 日期参数 -->
          <el-descriptions-item v-if="selectedTask.parameters && selectedTask.parameters.date_ranges" label="时间范围">
            {{ formatDateRanges(selectedTask.parameters.date_ranges) }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedTask.parameters && selectedTask.parameters.days" label="时间范围">
            最近{{ selectedTask.parameters.days }}天
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedTask.parameters && selectedTask.parameters.year_range" label="年份范围">
            {{ selectedTask.parameters.year_range[0] }} 至 {{ selectedTask.parameters.year_range[1] }}
          </el-descriptions-item>
          <el-descriptions-item v-if="selectedTask.parameters && selectedTask.parameters.start_date && selectedTask.parameters.end_date" label="时间范围">
            {{ selectedTask.parameters.start_date }} 至 {{ selectedTask.parameters.end_date }}
          </el-descriptions-item>
          
          <!-- 需求图谱特有的日期列表 -->
          <el-descriptions-item v-if="selectedTask.parameters && selectedTask.parameters.datelists" label="日期列表">
            {{ formatDatelists(selectedTask.parameters.datelists) }}
          </el-descriptions-item>
          
          <!-- 批处理大小 -->
          <el-descriptions-item v-if="selectedTask.parameters && selectedTask.parameters.batch_size" label="批处理大小">
            {{ selectedTask.parameters.batch_size }}
          </el-descriptions-item>
          
          <!-- 输出格式 -->
          <el-descriptions-item v-if="selectedTask.parameters && selectedTask.parameters.output_format" label="输出格式">
            {{ selectedTask.parameters.output_format === 'csv' ? 'CSV' : 'Excel' }}
          </el-descriptions-item>
          
          <!-- 优先级 -->
          <el-descriptions-item v-if="selectedTask.priority" label="优先级">
            {{ getPriorityLabel(selectedTask.priority) }}
          </el-descriptions-item>
        </el-descriptions>
        
        <!-- 检查点路径 -->
        <div v-if="selectedTask.checkpoint_path" class="checkpoint-section">
          <h3>检查点文件</h3>
          <div class="checkpoint-path">
            <span class="path-label">路径: </span>
            <el-tag size="small">
              {{ 
                typeof selectedTask.checkpoint_path === 'string' 
                  ? selectedTask.checkpoint_path 
                  : '检查点数据已加载' 
              }}
            </el-tag>
            <el-button 
              v-if="typeof selectedTask.checkpoint_path === 'string'" 
              type="primary" 
              size="small" 
              @click="downloadCheckpointFile(selectedTask.checkpoint_path)"
              style="margin-left: 10px;"
            >
              <el-icon><Download /></el-icon>下载检查点
            </el-button>
          </div>
          <div v-if="typeof selectedTask.checkpoint_path === 'object'" class="checkpoint-data">
            <h4>检查点数据：</h4>
            <pre>{{ JSON.stringify(selectedTask.checkpoint_path, null, 2) }}</pre>
          </div>
        </div>
        
        <!-- 输出文件列表 -->
        <div v-if="selectedTask.output_files && selectedTask.output_files.length > 0" class="output-files-section">
          <h3>输出文件</h3>
          <el-table :data="selectedTask.output_files" style="width: 100%" size="small">
            <el-table-column label="文件路径" prop="">
              <template #default="scope">
                <div class="file-path">
                  {{ scope.row }}
                </div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="100">
              <template #default="scope">
                <el-button 
                  type="primary" 
                  size="small" 
                  @click="downloadSingleFile(scope.row)"
                  plain
                >
                  下载
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
        
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
        
        <!-- 任务结果按钮 -->
        <div v-if="selectedTask.status === 'completed' && selectedTask.output_files && selectedTask.output_files.length > 0" class="task-results">
          <h3>任务结果</h3>
          <el-button type="primary" @click="downloadTaskResult()" :loading="downloading">
            <el-icon><Download /></el-icon>下载全部结果
          </el-button>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch, onUnmounted } from 'vue'
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
  result?: string | null;
  [key: string]: any;
}

const API_BASE_URL = 'http://127.0.0.1:5001/api'

// 使用模拟数据的标志
const useMockData = ref(false) // 设置为false表示使用真实API

// 模拟任务数据
const mockTasks: Task[] = [
  {
    taskId: 'TASK-20230615-001',
    taskType: 'index_trend',
    status: 'completed',
    progress: 100,
    createdAt: '2023-06-15 09:15:30',
    updatedAt: '2023-06-15 10:30:45',
    parameters: {
      keywords: ['小米手机', '华为手机', 'iPhone'],
      dateRanges: [['2023-01-01', '2023-06-01']],
      regions: ['全国']
    },
    priority: 5,
    result: 'index_trend_20230615001.xlsx'
  },
  {
    taskId: 'TASK-20230615-002',
    taskType: 'search_index',
    status: 'running',
    progress: 65,
    createdAt: '2023-06-15 10:20:15',
    updatedAt: '2023-06-15 10:50:17',
    parameters: {
      keywords: ['笔记本电脑', '平板电脑'],
      dateRanges: [['2023-03-01', '2023-06-01']],
      regions: ['北京', '上海', '广州']
    },
    priority: 5,
    result: null
  },
  {
    taskId: 'TASK-20230614-001',
    taskType: 'province_rank',
    status: 'failed',
    progress: 45,
    createdAt: '2023-06-14 15:12:40',
    updatedAt: '2023-06-14 16:45:21',
    parameters: {
      keywords: ['运动鞋', '休闲鞋'],
      dateRanges: [['2023-05-01', '2023-06-10']],
      regions: []
    },
    priority: 5,
    result: null
  }
];

// 模拟日志数据
const mockLogs: Record<string, TaskLog[]> = {
  'TASK-20230615-001': [
    { id: '1', taskId: 'TASK-20230615-001', level: 'info', message: '任务开始执行', timestamp: '2023-06-15 09:15:30' },
    { id: '2', taskId: 'TASK-20230615-001', level: 'info', message: '正在处理关键词: 小米手机', timestamp: '2023-06-15 09:20:45' },
    { id: '3', taskId: 'TASK-20230615-001', level: 'info', message: '正在处理关键词: 华为手机', timestamp: '2023-06-15 09:35:12' },
    { id: '4', taskId: 'TASK-20230615-001', level: 'info', message: '正在处理关键词: iPhone', timestamp: '2023-06-15 09:50:33' },
    { id: '5', taskId: 'TASK-20230615-001', level: 'info', message: '任务完成', timestamp: '2023-06-15 10:30:45' }
  ],
  'TASK-20230615-002': [
    { id: '1', taskId: 'TASK-20230615-002', level: 'info', message: '任务开始执行', timestamp: '2023-06-15 10:20:15' },
    { id: '2', taskId: 'TASK-20230615-002', level: 'warning', message: '请求速率受限，等待中...', timestamp: '2023-06-15 10:45:22' },
    { id: '3', taskId: 'TASK-20230615-002', level: 'info', message: '继续执行任务', timestamp: '2023-06-15 10:50:17' }
  ],
  'TASK-20230614-001': [
    { id: '1', taskId: 'TASK-20230614-001', level: 'info', message: '任务开始执行', timestamp: '2023-06-14 15:12:40' },
    { id: '2', taskId: 'TASK-20230614-001', level: 'error', message: '处理关键词时发生错误: 服务器返回 500', timestamp: '2023-06-14 16:20:55' },
    { id: '3', taskId: 'TASK-20230614-001', level: 'error', message: '任务执行失败', timestamp: '2023-06-14 16:45:21' }
  ]
};

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

// 加载任务列表
const loadTasks = async () => {
  loading.value = true
  try {
    if (useMockData.value) {
      // 使用模拟数据
      console.log("使用模拟数据");
      
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
    } else {
      // 使用真实API
      // 构建有效的查询参数
      const params: Record<string, any> = {}
      
      // 只添加有值的查询参数
      if (pageSize.value) params.limit = pageSize.value
      if (currentPage.value) params.offset = (currentPage.value - 1) * pageSize.value
      if (searchKeyword.value) params.keyword = searchKeyword.value
      if (taskTypeFilter.value) params.task_type = taskTypeFilter.value
      if (statusFilter.value) params.status = statusFilter.value
      
      const response = await axios.get(`${API_BASE_URL}/task/list`, { params })
      
      if (response.data.code === 10000) {
        const responseTasks = response.data.data.tasks || []
        total.value = response.data.data.total || 0
        
        // 处理任务数据
        tasks.value = responseTasks.map((task: any) => {
          // 确保task_id映射到taskId
          task.taskId = task.task_id
          task.taskType = task.task_type
          task.createdAt = task.create_time
          task.updatedAt = task.update_time
          
          // 确保parameters字段是对象
          if (task.parameters && typeof task.parameters === 'string') {
            try {
              task.parameters = JSON.parse(task.parameters)
            } catch (e) {
              console.error('解析parameters失败:', e)
              task.parameters = {}
            }
          }
          
          // 确保output_files字段是数组
          if (task.output_files === null) {
            task.output_files = []
          } else if (typeof task.output_files === 'string') {
            try {
              task.output_files = JSON.parse(task.output_files)
            } catch (e) {
              console.error('解析output_files失败:', e)
              // 如果是字符串但不是JSON，可能是单个文件路径
              task.output_files = [task.output_files]
            }
          }
          
          // 检查checkpoint_path，确保是合适的格式
          if (task.checkpoint_path) {
            if (typeof task.checkpoint_path === 'string') {
              // 如果是字符串，保留原样
              console.log('检查点路径:', task.checkpoint_path)
            } else if (typeof task.checkpoint_path === 'object') {
              // 对象格式的检查点数据
              console.log('检查点数据对象:', task.checkpoint_path)
            }
          }
          
          return task
        })
      } else {
        ElMessage.error(`获取任务列表失败: ${response.data.msg}`)
      }
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
  
  // 如果需要，加载完整的任务详情
  try {
    const response = await axios.get(`${API_BASE_URL}/task/${task.taskId}`)
    if (response.data.code === 10000) {
      const taskDetail = response.data.data
      
      // 映射字段名
      taskDetail.taskId = taskDetail.task_id
      taskDetail.taskType = taskDetail.task_type
      taskDetail.createdAt = taskDetail.create_time
      taskDetail.updatedAt = taskDetail.update_time
      
      // 确保parameters字段是对象
      if (taskDetail.parameters && typeof taskDetail.parameters === 'string') {
        try {
          taskDetail.parameters = JSON.parse(taskDetail.parameters)
        } catch (e) {
          console.error('解析parameters失败:', e)
          taskDetail.parameters = {}
        }
      }
      
      // 确保output_files字段是数组
      if (taskDetail.output_files === null) {
        taskDetail.output_files = []
      } else if (typeof taskDetail.output_files === 'string') {
        try {
          taskDetail.output_files = JSON.parse(taskDetail.output_files)
        } catch (e) {
          console.error('解析output_files失败:', e)
          // 如果是字符串但不是JSON，可能是单个文件路径
          taskDetail.output_files = [taskDetail.output_files]
        }
      }
      
      selectedTask.value = taskDetail
    }
  } catch (error) {
    console.error('加载任务详情错误:', error)
  }
}

// 加载任务日志
const loadTaskLogs = async (taskId: string) => {
  if (useMockData.value) {
    // 使用模拟数据
    setTimeout(() => {
      taskLogs.value = mockLogs[taskId] || [];
    }, 300);
  } else {
    // 使用真实API
    try {
      const response = await axios.get(`${API_BASE_URL}/task/${taskId}/logs`)
      if (response.data.code === 10000) {
        taskLogs.value = response.data.data || []
      } else {
        taskLogs.value = []
        console.error('获取任务日志失败:', response.data.msg)
      }
    } catch (error) {
      taskLogs.value = []
      console.error('加载任务日志错误:', error)
    }
  }
}

// 重试任务
const restartTask = async (task: Task) => {
  if (useMockData.value) {
    // 使用模拟数据
    ElMessage.success('任务已重新提交');
    const taskIndex = mockTasks.findIndex(t => t.taskId === task.taskId);
    if (taskIndex !== -1) {
      mockTasks[taskIndex].status = 'pending';
      mockTasks[taskIndex].progress = 0;
      mockTasks[taskIndex].updatedAt = new Date().toISOString().replace('T', ' ').substring(0, 19);
    }
    loadTasks();
  } else {
    // 使用真实API
    try {
      const response = await axios.post(`${API_BASE_URL}/task/${task.taskId}/resume`)
      
      if (response.data.code === 10000) {
        ElMessage.success('任务已重新提交')
        loadTasks()
      } else {
        ElMessage.error(`重试任务失败: ${response.data.msg || response.data.message}`)
      }
    } catch (error) {
      ElMessage.error('重试任务失败，请检查网络连接')
      console.error('重试任务错误:', error)
    }
  }
}

// 取消任务
const cancelTask = async (task: Task) => {
  if (useMockData.value) {
    // 使用模拟数据
    ElMessage.success('任务已取消');
    const taskIndex = mockTasks.findIndex(t => t.taskId === task.taskId);
    if (taskIndex !== -1) {
      mockTasks[taskIndex].status = 'cancelled';
      mockTasks[taskIndex].updatedAt = new Date().toISOString().replace('T', ' ').substring(0, 19);
    }
    loadTasks();
  } else {
    // 使用真实API
    try {
      const response = await axios.post(`${API_BASE_URL}/task/${task.taskId}/cancel`)
      
      if (response.data.code === 10000) {
        ElMessage.success('任务已取消')
        loadTasks()
      } else {
        ElMessage.error(`取消任务失败: ${response.data.msg || response.data.message}`)
      }
    } catch (error) {
      ElMessage.error('取消任务失败，请检查网络连接')
      console.error('取消任务错误:', error)
    }
  }
}

// 下载任务结果
const downloadTaskResult = async (task: Task | null = null) => {
  const targetTask = task || selectedTask.value
  if (!targetTask) return
  
  if (useMockData.value) {
    // 使用模拟数据
    downloading.value = true;
    
    setTimeout(() => {
      ElMessage.success('下载成功');
      downloading.value = false;
    }, 1500);
  } else {
    // 使用真实API
    downloading.value = true
    try {
      // 检查是否有输出文件
      if (!targetTask.output_files || !targetTask.output_files.length) {
        ElMessage.warning('该任务没有可下载的结果文件')
        downloading.value = false
        return
      }
      
      // 为每个输出文件创建下载链接
      for (const filePath of targetTask.output_files) {
        // 从路径中提取文件名
        const fileName = filePath.split('/').pop()
        
        // 构建下载URL
        const downloadUrl = `${API_BASE_URL}/task/download?filePath=${encodeURIComponent(filePath)}`
        
        // 创建临时链接并点击
        const link = document.createElement('a')
        link.href = downloadUrl
        link.setAttribute('download', fileName || 'output.csv')
        link.setAttribute('target', '_blank')
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      }
      
      ElMessage.success('下载成功')
    } catch (error) {
      ElMessage.error('下载失败，请检查网络连接')
      console.error('下载任务结果错误:', error)
    } finally {
      downloading.value = false
    }
  }
}

// 下载单个文件
const downloadSingleFile = (filePath: string) => {
  if (!filePath) return
  
  if (useMockData.value) {
    // 使用模拟数据
    ElMessage.success('下载成功');
  } else {
    // 使用真实API
    try {
      // 从路径中提取文件名
      const fileName = filePath.split('/').pop()
      
      // 构建下载URL
      const downloadUrl = `${API_BASE_URL}/task/download?filePath=${encodeURIComponent(filePath)}`
      
      // 创建临时链接并点击
      const link = document.createElement('a')
      link.href = downloadUrl
      link.setAttribute('download', fileName || 'output.csv')
      link.setAttribute('target', '_blank')
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      
      ElMessage.success('下载成功')
    } catch (error) {
      ElMessage.error('下载失败，请检查网络连接')
      console.error('下载文件错误:', error)
    }
  }
}

// 下载检查点文件
const downloadCheckpointFile = (checkpointPath: string) => {
  if (!checkpointPath) return
  
  downloadSingleFile(checkpointPath)
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
  
  return intervalId
}

// 监听详情对话框关闭
watch(() => taskDetailDialogVisible.value, (newVal) => {
  if (!newVal && selectedTask.value) {
    loadTasks() // 关闭详情对话框时刷新列表
  }
})

// 添加一个启动自动刷新的方法
const startAutoRefresh = () => {
  if (!useMockData.value) {
    const intervalId = setupRefreshInterval()
    
    // 组件卸载时清除定时器
    onUnmounted(() => {
      clearInterval(intervalId)
    })
  }
}

// 初始加载
onMounted(() => {
  console.log("TaskList组件已挂载");
  // 不在挂载时加载数据，而是等待父组件激活时加载
})

// 导出方法供父组件调用
defineExpose({
  loadTasks,
  startAutoRefresh
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

.checkpoint-section {
  margin-top: 20px;
  padding: 15px;
  background-color: #f0f9eb;
  border-radius: 4px;
  border-left: 4px solid #67c23a;
}

.checkpoint-path {
  display: flex;
  align-items: center;
}

.path-label {
  margin-right: 10px;
}

.checkpoint-data {
  margin-top: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  padding: 10px;
  max-height: 200px;
  overflow-y: auto;
}

.checkpoint-data h4 {
  margin-top: 0;
  margin-bottom: 8px;
  font-size: 14px;
  color: #67c23a;
}

.checkpoint-data pre {
  margin: 0;
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 12px;
}

.output-files-section {
  margin-top: 20px;
  padding: 15px;
  background-color: #f0f9eb;
  border-radius: 4px;
  border-left: 4px solid #67c23a;
}

.file-path {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style> 