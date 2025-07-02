<template>
  <el-dialog
    :visible="visible"
    @update:visible="emit('update:visible', $event)"
    title="任务详情"
    width="700px"
    destroy-on-close
    :modal="true"
    :append-to-body="true"
    :close-on-click-modal="false"
  >
    <div v-if="task" class="task-detail">
      <el-descriptions bordered :column="2">
        <el-descriptions-item label="任务ID" :span="2">
          {{ task.taskId }}
        </el-descriptions-item>
        <el-descriptions-item label="任务类型">
          {{ translateTaskType(task.taskType) }}
        </el-descriptions-item>
        <el-descriptions-item label="任务状态">
          <el-tag :type="getStatusTag(task.status)">
            {{ translateStatus(task.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">
          {{ task.createdAt || task.create_time }}
        </el-descriptions-item>
        <el-descriptions-item label="更新时间">
          {{ task.updatedAt || task.update_time }}
        </el-descriptions-item>
        <el-descriptions-item label="进度" :span="2">
          <el-progress 
            :percentage="task.progress || 0" 
            :status="getProgressStatus(task.status)"
          />
        </el-descriptions-item>
      </el-descriptions>
      
      <h3>任务参数</h3>
      <el-descriptions bordered :column="1">
        <!-- 关键词 -->
        <el-descriptions-item v-if="task.parameters && task.parameters.keywords" label="关键词">
          {{ formatKeywords(task.parameters.keywords) }}
        </el-descriptions-item>
        
        <!-- 城市/地区 -->
        <el-descriptions-item v-if="task.parameters && task.parameters.cities" label="地区">
          {{ formatCities(task.parameters.cities) }}
        </el-descriptions-item>
        <el-descriptions-item v-if="task.parameters && task.parameters.regions" label="地区">
          {{ formatRegions(task.parameters.regions) }}
        </el-descriptions-item>
        
        <!-- 日期参数 -->
        <el-descriptions-item v-if="task.parameters && task.parameters.date_ranges" label="时间范围">
          {{ formatDateRanges(task.parameters.date_ranges) }}
        </el-descriptions-item>
        <el-descriptions-item v-if="task.parameters && task.parameters.days" label="时间范围">
          最近{{ task.parameters.days }}天
        </el-descriptions-item>
        <el-descriptions-item v-if="task.parameters && task.parameters.year_range" label="年份范围">
          {{ task.parameters.year_range[0] }} 至 {{ task.parameters.year_range[1] }}
        </el-descriptions-item>
        <el-descriptions-item v-if="task.parameters && task.parameters.start_date && task.parameters.end_date" label="时间范围">
          {{ task.parameters.start_date }} 至 {{ task.parameters.end_date }}
        </el-descriptions-item>
        
        <!-- 需求图谱特有的日期列表 -->
        <el-descriptions-item v-if="task.parameters && task.parameters.datelists" label="日期列表">
          {{ formatDatelists(task.parameters.datelists) }}
        </el-descriptions-item>
        
        <!-- 批处理大小 -->
        <el-descriptions-item v-if="task.parameters && task.parameters.batch_size" label="批处理大小">
          {{ task.parameters.batch_size }}
        </el-descriptions-item>
        
        <!-- 输出格式 -->
        <el-descriptions-item v-if="task.parameters && task.parameters.output_format" label="输出格式">
          {{ task.parameters.output_format === 'csv' ? 'CSV' : 'Excel' }}
        </el-descriptions-item>
        
        <!-- 优先级 -->
        <el-descriptions-item v-if="task.priority" label="优先级">
          {{ getPriorityLabel(task.priority) }}
        </el-descriptions-item>
      </el-descriptions>
      
      <!-- 检查点路径 -->
      <div v-if="task.checkpoint_path" class="checkpoint-section">
        <h3>检查点文件</h3>
        <div class="checkpoint-path">
          <span class="path-label">路径: </span>
          <el-tag size="small">
            {{ 
              typeof task.checkpoint_path === 'string' 
                ? getShortPath(task.checkpoint_path) 
                : '检查点数据已加载' 
            }}
            <el-tooltip 
              v-if="typeof task.checkpoint_path === 'string'"
              :content="task.checkpoint_path" 
              placement="top" 
              effect="light"
            >
              <el-icon><InfoFilled /></el-icon>
            </el-tooltip>
          </el-tag>
          <el-button 
            v-if="typeof task.checkpoint_path === 'string'" 
            type="primary" 
            size="small" 
            @click="downloadCheckpointFile(task.checkpoint_path)"
            style="margin-left: 10px;"
          >
            <el-icon><Download /></el-icon>下载检查点
          </el-button>
        </div>
        <div v-if="typeof task.checkpoint_path === 'object'" class="checkpoint-data">
          <h4>检查点数据：</h4>
          <pre>{{ JSON.stringify(task.checkpoint_path, null, 2) }}</pre>
        </div>
      </div>
      
      <!-- 输出文件列表 -->
      <div v-if="task.output_files && task.output_files.length > 0" class="output-files-section">
        <h3>输出文件</h3>
        <el-table :data="task.output_files" style="width: 100%" size="small">
          <el-table-column label="文件路径" prop="">
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
          <el-table-column label="操作" width="100">
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
      </div>
      
      <h3>任务日志</h3>
      <div class="task-logs">
        <el-timeline v-if="logs.length > 0">
          <el-timeline-item
            v-for="log in logs"
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
      <div v-if="task.status === 'completed' && task.output_files && task.output_files.length > 0" class="task-results">
        <h3>任务结果</h3>
        <el-button type="primary" @click="downloadTaskResult()" :loading="downloading">
          <el-icon><Download /></el-icon>下载全部结果
        </el-button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, defineProps, defineEmits, watch, withDefaults } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { Download, InfoFilled, Document } from '@element-plus/icons-vue'

// 定义组件的属性
interface TaskProps {
  visible: boolean;
  task: any;
  API_BASE_URL: string;
}

const props = withDefaults(defineProps<TaskProps>(), {
  visible: false,
  task: () => null,
  API_BASE_URL: 'http://127.0.0.1:5001/api'
})

// 定义事件
const emit = defineEmits<{
  'update:visible': [value: boolean];
  'download-complete': [];
}>()

// 任务日志
const logs = ref<any[]>([])
const downloading = ref(false)

// 监听任务变化，加载日志
watch(() => props.task, async (newTask) => {
  if (newTask && newTask.taskId) {
    await loadTaskLogs(newTask.taskId)
  }
}, { immediate: true })

// 加载任务日志
const loadTaskLogs = async (taskId: string) => {
  if (!taskId) return
  
  try {
    const response = await axios.get(`${props.API_BASE_URL}/task/${taskId}/logs`)
    if (response.data.code === 10000) {
      logs.value = response.data.data || []
    } else {
      logs.value = []
      console.error('获取任务日志失败:', response.data.msg)
    }
  } catch (error) {
    logs.value = []
    console.error('加载任务日志错误:', error)
  }
}

// 下载任务结果
const downloadTaskResult = async () => {
  if (!props.task) return
  
  downloading.value = true
  try {
    // 检查是否有输出文件
    if (!props.task.output_files || !props.task.output_files.length) {
      ElMessage.warning('该任务没有可下载的结果文件')
      downloading.value = false
      return
    }
    
    // 为每个输出文件创建下载链接
    for (const filePath of props.task.output_files) {
      await downloadSingleFile(filePath)
    }
    
    ElMessage.success('下载成功')
    emit('download-complete')
  } catch (error) {
    ElMessage.error('下载失败，请检查网络连接')
    console.error('下载任务结果错误:', error)
  } finally {
    downloading.value = false
  }
}

// 下载单个文件
const downloadSingleFile = async (filePath) => {
  if (!filePath) return
  
  try {
    // 从路径中提取文件名
    const fileName = filePath.split('/').pop()
    
    // 构建下载URL
    const downloadUrl = `${props.API_BASE_URL}/task/download?filePath=${encodeURIComponent(filePath)}`
    
    // 创建临时链接并点击
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
const downloadCheckpointFile = (checkpointPath) => {
  if (!checkpointPath) return
  
  downloadSingleFile(checkpointPath)
}

// 辅助函数：获取短路径
const getShortPath = (path) => {
  if (!path) return ''
  
  // 如果路径太长，只显示文件名和部分路径
  if (path.length > 40) {
    const parts = path.split('/')
    const fileName = parts[parts.length - 1]
    const parentDir = parts[parts.length - 2] || ''
    return `.../${parentDir ? parentDir + '/' : ''}${fileName}`
  }
  return path
}

// 辅助函数
const translateTaskType = (type) => {
  const typeMap = {
    'search_index': '搜索指数',
    'feed_index': '资讯指数',
    'word_graph': '需求图谱',
    'demographic_attributes': '人群属性',
    'interest_profile': '兴趣分析',
    'region_distribution': '地域分布'
  }
  return typeMap[type] || type
}

const translateStatus = (status) => {
  const statusMap = {
    'pending': '等待中',
    'running': '执行中',
    'completed': '已完成',
    'failed': '失败',
    'cancelled': '已取消'
  }
  return statusMap[status] || status
}

const getStatusTag = (status) => {
  const statusMap = {
    'pending': 'info',
    'running': 'warning',
    'completed': 'success',
    'failed': 'danger',
    'cancelled': 'info'
  }
  return statusMap[status] || ''
}

const getProgressStatus = (status) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  if (status === 'cancelled') return 'warning'
  return ''
}

const getLogTypeIcon = (level) => {
  const levelMap = {
    'info': 'primary',
    'warning': 'warning',
    'error': 'danger',
    'debug': 'info'
  }
  return levelMap[level] || 'info'
}

const getPriorityLabel = (priority) => {
  if (priority >= 8) return '高'
  if (priority >= 4) return '中'
  return '低'
}

// 格式化关键词
const formatKeywords = (keywords) => {
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
const formatCities = (cities: any) => {
  if (!cities) return ''
  
  try {
    // 处理对象形式的城市数据 {0: {code: "0", name: "全国"}, 901: {code: "901", name: "山东"}}
    if (typeof cities === 'object' && !Array.isArray(cities)) {
      const cityNames = Object.values(cities).map((city: any) => city.name || city.code || '')
      return cityNames.join(', ')
    }
    
    // 处理数组形式的城市数据
    if (Array.isArray(cities)) {
      return cities.map((city: any) => {
        if (typeof city === 'object') return city.name || city.code || ''
        return String(city)
      }).join(', ')
    }
    
    // 字符串或其他类型
    return String(cities)
  } catch (error) {
    console.error('格式化城市错误:', error)
    return String(cities)
  }
}

// 格式化地区
const formatRegions = (regions) => {
  if (!regions) return ''
  return regions.join(', ')
}

// 格式化日期范围
const formatDateRanges = (dateRanges) => {
  if (!dateRanges || !dateRanges.length) return ''
  return dateRanges.map(range => `${range[0]} 至 ${range[1]}`).join('; ')
}

// 格式化日期列表
const formatDatelists = (datelists) => {
  if (!datelists || !datelists.length) return ''
  return datelists.map(date => {
    if (date.length === 8) {
      return `${date.substring(0, 4)}-${date.substring(4, 6)}-${date.substring(6, 8)}`
    }
    return date
  }).join(', ')
}
</script>

<style scoped>
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
  flex-wrap: wrap;
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
  display: flex;
  align-items: center;
  gap: 5px;
}
</style> 