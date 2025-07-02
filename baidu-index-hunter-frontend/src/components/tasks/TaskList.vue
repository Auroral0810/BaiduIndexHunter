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
      <div v-if="loading" class="loading-container">
        <el-empty description="正在加载数据..." :image-size="100">
          <template #image>
            <el-icon class="loading-icon"><i-ep-loading /></el-icon>
          </template>
        </el-empty>
      </div>
      <el-table
        v-else
        :data="tasks"
        style="width: 100%"
        border
        stripe
      >
        <el-table-column prop="taskId" label="任务ID" width="210" />
        <el-table-column label="任务类型" width="95">
          <template #default="scope">
            <el-tag :type="getTaskTypeTag(scope.row.taskType)">
              {{ translateTaskType(scope.row.taskType) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="scope">
            <el-tag :type="getStatusTag(scope.row.status)">
              {{ translateStatus(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="参数">
          <template #default="scope">
            <div v-if="scope.row.parameters" class="task-parameters">
              <div v-if="scope.row.parameters.keywords">
                <strong>关键词:</strong> 
                {{ formatKeywords(scope.row.parameters.keywords) }}
              </div>
              <div v-if="scope.row.parameters.cities">
                <strong>地区:</strong> 
                {{ formatCities(scope.row.parameters.cities) }}
              </div>
              <div v-if="scope.row.parameters.regions">
                <strong>地区:</strong> 
                {{ formatRegions(scope.row.parameters.regions) }}
              </div>
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
              <div v-if="scope.row.parameters.datelists">
                <strong>日期列表:</strong> 
                {{ formatDatelists(scope.row.parameters.datelists) }}
              </div>
              <div v-if="scope.row.parameters.batch_size">
                <strong>批处理大小:</strong> {{ scope.row.parameters.batch_size }}
              </div>
              <div v-if="scope.row.parameters.output_format">
                <strong>输出格式:</strong> 
                {{ scope.row.parameters.output_format === 'csv' ? 'CSV' : 'Excel' }}
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="创建时间" width="160" />
        <el-table-column label="进度" width="140">
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
    
    <div class="pagination" v-if="!loading && tasks.length > 0">
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
      width="50%"
      top="5vh"
      destroy-on-close
      :modal="true"
      :append-to-body="true"
      :close-on-click-modal="false"
      @open="handleDialogOpen"
      class="task-detail-dialog"
    >
      <div v-if="selectedTask" class="task-detail">
        <!-- 顶部信息卡片 -->
        <el-card class="info-card" shadow="hover">
          <div class="info-header">
            <div class="task-id">
              <span class="label">任务ID:</span>
              <span class="value">{{ selectedTask.taskId || selectedTask.task_id }}</span>
            </div>
            <div class="task-status">
              <el-tag :type="getStatusTag(selectedTask.status)" size="large">
                {{ translateStatus(selectedTask.status) }}
              </el-tag>
            </div>
          </div>
          
          <el-row :gutter="20" class="info-row">
            <el-col :span="8">
              <div class="info-item">
                <div class="info-label">任务类型</div>
                <div class="info-value">{{ translateTaskType(selectedTask.taskType || selectedTask.task_type) }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <div class="info-label">创建时间</div>
                <div class="info-value">{{ selectedTask.createdAt || selectedTask.create_time }}</div>
              </div>
            </el-col>
            <el-col :span="8">
              <div class="info-item">
                <div class="info-label">更新时间</div>
                <div class="info-value">{{ selectedTask.updatedAt || selectedTask.update_time }}</div>
              </div>
            </el-col>
            <el-col :span="8" v-if="selectedTask.task_name">
              <div class="info-item">
                <div class="info-label">任务名称</div>
                <div class="info-value">{{ selectedTask.task_name }}</div>
              </div>
            </el-col>
            <el-col :span="16" v-if="selectedTask.priority">
              <div class="info-item">
                <div class="info-label">优先级</div>
                <div class="info-value">{{ getPriorityLabel(selectedTask.priority) }}</div>
              </div>
            </el-col>
          </el-row>
          
          <div class="progress-section">
            <div class="progress-header">
              <span>任务进度</span>
              <span v-if="selectedTask.completed_items !== undefined">
                {{ selectedTask.completed_items }} / {{ selectedTask.total_items || 0 }}
                <span v-if="selectedTask.failed_items > 0" class="error-text">
                  (失败: {{ selectedTask.failed_items }})
                </span>
              </span>
            </div>
            <el-progress 
              :percentage="selectedTask.progress || 0" 
              :status="getProgressStatus(selectedTask.status)"
              :stroke-width="15"
            />
          </div>
        </el-card>
        
        <!-- 内容网格布局 -->
        <div class="detail-grid">
          <!-- 任务参数 -->
          <el-card class="detail-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <h3>任务参数</h3>
              </div>
            </template>
            <div class="card-content parameters-content">
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item v-if="selectedTask.parameters && selectedTask.parameters.keywords" label="关键词" :span="2">
                  {{ formatKeywords(selectedTask.parameters.keywords) }}
                </el-descriptions-item>
                <el-descriptions-item v-if="selectedTask.parameters && selectedTask.parameters.cities" label="地区" :span="selectedTask.parameters.regions ? 1 : 2">
                  {{ formatCities(selectedTask.parameters.cities) }}
                </el-descriptions-item>
                <el-descriptions-item v-if="selectedTask.parameters && selectedTask.parameters.regions" label="地区" :span="selectedTask.parameters.cities ? 1 : 2">
                  {{ formatRegions(selectedTask.parameters.regions) }}
                </el-descriptions-item>
                <el-descriptions-item v-if="selectedTask.parameters && selectedTask.parameters.date_ranges" label="时间范围" :span="2">
                  {{ formatDateRanges(selectedTask.parameters.date_ranges) }}
                </el-descriptions-item>
                <el-descriptions-item v-if="selectedTask.parameters && selectedTask.parameters.days" label="时间范围" :span="1">
                  最近{{ selectedTask.parameters.days }}天
                </el-descriptions-item>
                <el-descriptions-item v-if="selectedTask.parameters && selectedTask.parameters.year_range" label="年份范围" :span="1">
                  {{ selectedTask.parameters.year_range[0] }} 至 {{ selectedTask.parameters.year_range[1] }}
                </el-descriptions-item>
                <el-descriptions-item v-if="selectedTask.parameters && selectedTask.parameters.start_date && selectedTask.parameters.end_date" label="时间范围" :span="1">
                  {{ selectedTask.parameters.start_date }} 至 {{ selectedTask.parameters.end_date }}
                </el-descriptions-item>
                <el-descriptions-item v-if="selectedTask.parameters && selectedTask.parameters.datelists" label="日期列表" :span="2">
                  {{ formatDatelists(selectedTask.parameters.datelists) }}
                </el-descriptions-item>
                <el-descriptions-item v-if="selectedTask.parameters && selectedTask.parameters.batch_size" label="批处理大小" :span="1">
                  {{ selectedTask.parameters.batch_size }}
                </el-descriptions-item>
                <el-descriptions-item v-if="selectedTask.parameters && selectedTask.parameters.output_format" label="输出格式" :span="1">
                  {{ selectedTask.parameters.output_format === 'csv' ? 'CSV' : 'Excel' }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </el-card>
          
          <!-- 输出文件 -->
          <el-card class="detail-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <h3>输出文件</h3>
              </div>
            </template>
            <div class="card-content files-content">
              <div v-if="selectedTask.output_files && selectedTask.output_files.length > 0" class="files-container">
                <el-table :data="selectedTask.output_files" style="width: 100%" size="small" max-height="150">
                  <el-table-column label="文件路径" prop="" min-width="200">
                    <template #default="scope">
                      <div class="file-path">
                        <el-icon><Document /></el-icon>
                        <span>{{ getShortPath(scope.row) }}</span>
                        <el-tooltip :content="scope.row" placement="top" effect="light">
                          <el-icon><InfoFilled /></el-icon>
                        </el-tooltip>
                      </div>
                    </template>
                  </el-table-column>
                  <el-table-column label="操作" width="100" fixed="right">
                    <template #default="scope">
                      <el-button 
                        type="primary" 
                        size="small" 
                        @click="downloadSingleFile(scope.row)"
                        plain
                      >
                        <el-icon><Download /></el-icon>下载
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
                
                <div class="download-all">
                  <el-button type="primary" @click="downloadTaskResult()" :loading="downloading" v-if="selectedTask.status === 'completed'" size="small">
                    <el-icon><Download /></el-icon>下载全部
                  </el-button>
                </div>
              </div>
              <el-empty v-else description="暂无输出文件" :image-size="50" />
            </div>
          </el-card>
          
          <!-- 检查点 -->
          <el-card class="detail-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <h3>检查点</h3>
              </div>
            </template>
            <div class="card-content checkpoint-content">
              <div v-if="selectedTask.checkpoint_path" class="checkpoint-container">
                <div class="checkpoint-path">
                  <span class="path-label">检查点路径: </span>
                  <el-tag size="small">
                    {{ 
                      typeof selectedTask.checkpoint_path === 'string' 
                        ? getShortPath(selectedTask.checkpoint_path) 
                        : '检查点数据已加载' 
                    }}
                    <el-tooltip 
                      v-if="typeof selectedTask.checkpoint_path === 'string'"
                      :content="selectedTask.checkpoint_path" 
                      placement="top" 
                      effect="light"
                    >
                      <el-icon><InfoFilled /></el-icon>
                    </el-tooltip>
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
              <el-empty v-else description="暂无检查点数据" :image-size="50" />
            </div>
          </el-card>
          
          <!-- 错误信息 -->
          <el-card class="detail-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <h3>任务日志</h3>
              </div>
            </template>
            <div class="card-content logs-content">
              <div v-if="selectedTask.error_message" class="error-message">
                <el-alert
                  type="error"
                  :closable="false"
                  show-icon
                >
                  <p>{{ selectedTask.error_message }}</p>
                </el-alert>
              </div>
              <el-empty v-else description="日志功能即将推出，敬请期待" :image-size="50" />
            </div>
          </el-card>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="taskDetailDialogVisible = false">关闭</el-button>
          <el-button 
            type="success" 
            @click="restartTask(selectedTask)" 
            v-if="selectedTask && (selectedTask.status === 'failed' || selectedTask.status === 'cancelled')"
          >
            重试任务
          </el-button>
          <el-button 
            type="danger" 
            @click="cancelTask(selectedTask)" 
            v-if="selectedTask && (selectedTask.status === 'pending' || selectedTask.status === 'running')"
          >
            取消任务
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { Download, InfoFilled, Document } from '@element-plus/icons-vue'

// 定义任务接口
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
  checkpoint_path?: string | object;
  output_files?: string[];
  completed_items?: number;
  total_items?: number;
  failed_items?: number;
  task_name?: string;
  error_message?: string;
  [key: string]: any;
}

const API_BASE_URL = 'http://127.0.0.1:5001/api'
const useMockData = ref(false)

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
      date_ranges: [['2023-01-01', '2023-06-01']],
      regions: ['全国']
    },
    priority: 5,
    result: 'index_trend_20230615001.xlsx',
    output_files: []
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
      date_ranges: [['2023-03-01', '2023-06-01']],
      regions: ['北京', '上海', '广州']
    },
    priority: 5,
    result: null,
    output_files: []
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
      date_ranges: [['2023-05-01', '2023-06-10']],
      regions: []
    },
    priority: 5,
    result: null,
    output_files: []
  }
];

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
const downloading = ref(false)

// 加载任务列表
const loadTasks = async () => {
  loading.value = true
  try {
    if (useMockData.value) {
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
      total.value = filteredTasks.length;
      const start = (currentPage.value - 1) * pageSize.value;
      const end = start + pageSize.value;
      tasks.value = filteredTasks.slice(start, end);
    } else {
      const params: Record<string, any> = {}
      if (pageSize.value) params.limit = String(pageSize.value)
      if (currentPage.value) params.offset = String((currentPage.value - 1) * pageSize.value)
      if (searchKeyword.value) params.keyword = searchKeyword.value
      if (taskTypeFilter.value) params.task_type = taskTypeFilter.value
      if (statusFilter.value) params.status = statusFilter.value
      const response = await axios.get(`${API_BASE_URL}/task/list`, { params })
      if (response.data.code === 10000) {
        const responseTasks = response.data.data.tasks || []
        total.value = response.data.data.total || 0
        tasks.value = responseTasks.map((task: any) => {
          task.taskId = task.task_id || task.taskId || ''
          task.taskType = task.task_type || task.taskType || ''
          task.createdAt = task.create_time || task.createdAt || ''
          task.updatedAt = task.update_time || task.updatedAt || ''
          task.status = task.status || 'pending'
          task.progress = task.progress || 0
          if (!task.parameters) {
            task.parameters = {};
          } else if (typeof task.parameters === 'string') {
            try {
              task.parameters = JSON.parse(task.parameters);
            } catch (e) {
              console.error(`任务 ${task.taskId} 解析parameters失败:`, e);
              task.parameters = {};
            }
          }
          if (task.output_files === null || task.output_files === undefined) {
            task.output_files = [];
          } else if (typeof task.output_files === 'string') {
            try {
              task.output_files = JSON.parse(task.output_files);
            } catch (e) {
              task.output_files = [task.output_files];
            }
          }
          if (!Array.isArray(task.output_files)) {
            task.output_files = [task.output_files];
          }
          return task
        })
      } else {
        ElMessage.error(`获取任务列表失败: ${response.data.msg}`)
      }
    }
  } catch (error) {
    ElMessage.error('获取任务列表失败，请检查网络连接')
    tasks.value = []
  } finally {
    loading.value = false
    if (tasks.value && tasks.value.length > 0) {
      tasks.value = [...tasks.value]
    }
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
  await loadTaskDetail(task.taskId)
  taskDetailDialogVisible.value = true
}

// 加载任务详情
const loadTaskDetail = async (taskId: string) => {
  if (!taskId) return
  try {
    const response = await axios.get(`${API_BASE_URL}/task/${taskId}`)
    if (response.data.code === 10000 && selectedTask.value) {
      Object.assign(selectedTask.value, response.data.data)
    } else {
      console.error('获取任务详情失败:', response.data.msg)
    }
  } catch (error) {
    console.error('加载任务详情错误:', error)
  }
}

// 对话框打开处理
const handleDialogOpen = () => {
  if (selectedTask.value && selectedTask.value.taskId) {
    loadTaskDetail(selectedTask.value.taskId)
  }
}

// 重试任务
const restartTask = async (task: Task | null = null) => {
  if (!task && !selectedTask.value) return
  
  const targetTask = task || selectedTask.value
  if (!targetTask) return
  
  if (useMockData.value) {
    ElMessage.success('任务已重新提交');
    const taskIndex = mockTasks.findIndex(t => t.taskId === targetTask.taskId);
    if (taskIndex !== -1) {
      mockTasks[taskIndex].status = 'pending';
      mockTasks[taskIndex].progress = 0;
      mockTasks[taskIndex].updatedAt = new Date().toISOString().replace('T', ' ').substring(0, 19);
    }
    loadTasks();
  } else {
    try {
      const response = await axios.post(`${API_BASE_URL}/task/${targetTask.taskId}/resume`)
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
const cancelTask = async (task: Task | null = null) => {
  if (!task && !selectedTask.value) return
  
  const targetTask = task || selectedTask.value
  if (!targetTask) return
  
  if (useMockData.value) {
    ElMessage.success('任务已取消');
    const taskIndex = mockTasks.findIndex(t => t.taskId === targetTask.taskId);
    if (taskIndex !== -1) {
      mockTasks[taskIndex].status = 'cancelled';
      mockTasks[taskIndex].updatedAt = new Date().toISOString().replace('T', ' ').substring(0, 19);
    }
    loadTasks();
  } else {
    try {
      const response = await axios.post(`${API_BASE_URL}/task/${targetTask.taskId}/cancel`)
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
  if (!task && !selectedTask.value) return
  
  const targetTask = task || selectedTask.value
  if (!targetTask) return
  
  downloading.value = true
  
  try {
    if (!targetTask.output_files || !targetTask.output_files.length) {
      ElMessage.warning('该任务没有可下载的结果文件')
      downloading.value = false
      return
    }
    
    for (const filePath of targetTask.output_files) {
      await downloadSingleFile(filePath)
    }
    
    ElMessage.success('下载成功')
    loadTasks()
  } catch (error) {
    ElMessage.error('下载失败，请检查网络连接')
    console.error('下载任务结果错误:', error)
  } finally {
    downloading.value = false
  }
}

// 下载单个文件
const downloadSingleFile = async (filePath: string) => {
  if (!filePath) return false
  
  try {
    const fileName = filePath.split('/').pop()
    const downloadUrl = `${API_BASE_URL}/task/download?filePath=${encodeURIComponent(filePath)}`
    
    const link = document.createElement('a')
    link.href = downloadUrl
    link.setAttribute('download', fileName || 'output.csv')
    link.setAttribute('target', '_blank')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    return true
  } catch (error) {
    ElMessage.error('下载失败，请检查网络连接')
    console.error('下载文件错误:', error)
    return false
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

const getPriorityLabel = (priority: number) => {
  if (priority >= 8) return '高'
  if (priority >= 4) return '中'
  return '低'
}

const getShortPath = (path) => {
  if (!path) return ''
  if (path.length > 40) {
    const parts = path.split('/')
    const fileName = parts[parts.length - 1]
    const parentDir = parts[parts.length - 2] || ''
    return `.../${parentDir ? parentDir + '/' : ''}${fileName}`
  }
  return path
}

const formatKeywords = (keywords: any) => {
  if (Array.isArray(keywords)) {
    if (keywords.length > 0 && typeof keywords[0] === 'object' && 'value' in keywords[0]) {
      return keywords.map(k => k.value).join(', ')
    }
    return keywords.join(', ')
  }
  return keywords
}

const formatCities = (cities: any) => {
  if (!cities) return ''
  try {
    if (typeof cities === 'object' && !Array.isArray(cities)) {
      const cityNames = Object.values(cities).map((city: any) => city.name || city.code || '')
      return cityNames.join(', ')
    }
    if (Array.isArray(cities)) {
      return cities.map((city: any) => {
        if (typeof city === 'object') return city.name || city.code || ''
        return String(city)
      }).join(', ')
    }
    return String(cities)
  } catch (error) {
    console.error('格式化城市错误:', error)
    return String(cities)
  }
}

const formatRegions = (regions: string[]) => {
  if (!regions) return ''
  return regions.join(', ')
}

const formatDateRanges = (dateRanges: string[][]) => {
  if (!dateRanges || !dateRanges.length) return ''
  return dateRanges.map(range => `${range[0]} 至 ${range[1]}`).join('; ')
}

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
    if (!taskDetailDialogVisible.value) {
      loadTasks()
    }
  }, 30000)
  return intervalId
}

// 监听详情对话框关闭
watch(() => taskDetailDialogVisible.value, (newVal) => {
  if (!newVal && selectedTask.value) {
    loadTasks()
  }
})

const startAutoRefresh = () => {
  if (!useMockData.value) {
    const intervalId = setupRefreshInterval()
    onUnmounted(() => {
      clearInterval(intervalId)
    })
  }
}

onMounted(() => {
  loadTasks()
  startAutoRefresh()
})

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

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.loading-icon {
  font-size: 40px;
  color: #409EFF;
  animation: rotate 1.5s linear infinite;
}

/* 任务详情对话框样式 */
:deep(.task-detail-dialog .el-dialog) {
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  margin: 0 auto !important;
  border-radius: 8px;
}

:deep(.task-detail-dialog .el-dialog__body) {
  padding: 15px;
  overflow-y: auto;
}

:deep(.task-detail-dialog .el-dialog__header) {
  padding: 12px 20px;
  margin: 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background-color: #f8f9fa;
}

:deep(.task-detail-dialog .el-dialog__footer) {
  padding: 8px 20px;
  border-top: 1px solid var(--el-border-color-lighter);
  background-color: #f8f9fa;
}

.task-detail {
  padding: 0;
}

.info-card {
  margin-bottom: 15px;
  border-radius: 4px;
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.task-id {
  font-size: 16px;
}

.task-id .label {
  font-weight: bold;
  margin-right: 8px;
}

.task-id .value {
  font-family: monospace;
  color: #606266;
}

.info-row {
  margin-bottom: 15px;
}

.info-item {
  margin-bottom: 10px;
}

.info-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 5px;
}

.info-value {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.progress-section {
  margin-top: 10px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}

.error-text {
  color: #F56C6C;
}

/* 网格布局 */
.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-gap: 15px;
}

.detail-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.card-content {
  overflow-y: auto;
  height: 150px;
}

.parameters-content {
  padding: 0;
}

.files-content {
  padding: 0;
}

.files-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.file-path {
  display: flex;
  align-items: center;
  gap: 8px;
}

.download-all {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
}

.checkpoint-container {
  height: 100%;
}

.checkpoint-path {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.path-label {
  margin-right: 10px;
  font-weight: 500;
}

.checkpoint-data {
  margin-top: 10px;
  background-color: #fff;
  border-radius: 4px;
  padding: 10px;
  border: 1px solid #ebeef5;
}

.checkpoint-data h4 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 14px;
  color: #409EFF;
}

.checkpoint-data pre {
  margin: 0;
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 12px;
  max-height: 100px;
  overflow-y: auto;
  background-color: #f8f9fa;
  padding: 10px;
  border-radius: 4px;
}

.error-message {
  margin-bottom: 15px;
}

.error-message p {
  margin: 0;
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 12px;
}

.logs-content {
  padding: 10px;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 响应式调整 */
@media screen and (max-width: 1200px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>