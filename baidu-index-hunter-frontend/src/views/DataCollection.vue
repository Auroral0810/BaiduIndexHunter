<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElNotification } from 'element-plus'
import { useI18n } from 'vue-i18n'
import axios from 'axios'
import SearchIndexTask from '@/components/tasks/SearchIndexTask.vue'
import FeedIndexTask from '@/components/tasks/FeedIndexTask.vue'
import WordGraphTask from '@/components/tasks/WordGraphTask.vue'
import DemographicAttributesTask from '@/components/tasks/DemographicAttributesTask.vue'
import InterestProfileTask from '@/components/tasks/InterestProfileTask.vue'
import RegionDistributionTask from '@/components/tasks/RegionDistributionTask.vue'
import TaskList from '@/components/tasks/TaskList.vue'
import { webSocketService } from '@/utils/websocket'
import { Close } from '@element-plus/icons-vue'

const { t } = useI18n()
const API_BASE_URL = 'http://127.0.0.1:5001/api'

const route = useRoute()
const router = useRouter()

const activeTab = ref('search_index')
const apiStatus = ref(false)
const apiStatusDialog = ref(false)
const taskListRef = ref(null)

// 当前运行的任务
const currentRunningTask = ref(null)
const showProgressPanel = ref(false)

// 处理 WebSocket 更新
const handleWebSocketUpdate = (data) => {
  if (data.status === 'running' || data.status === 'pending') {
    currentRunningTask.value = {
      ...data,
      updateTime: new Date()
    }
    showProgressPanel.value = true
  } else if (data.status === 'completed' || data.status === 'failed' || data.status === 'cancelled') {
    // 任务结束，更新状态并延迟关闭面板
    if (currentRunningTask.value && currentRunningTask.value.taskId === data.taskId) {
      currentRunningTask.value = {
        ...currentRunningTask.value,
        ...data,
        progress: data.status === 'completed' ? 100 : data.progress
      }
      
      // 3秒后自动关闭面板
      setTimeout(() => {
        if (currentRunningTask.value && currentRunningTask.value.taskId === data.taskId) {
           showProgressPanel.value = false
           // 延迟清空，避免面板突然消失内容
           setTimeout(() => {
             currentRunningTask.value = null
           }, 300)
        }
      }, 5000)
    }
  }
}

// 格式化进度状态
const getProgressStatus = (status) => {
  if (status === 'completed') return 'success'
  if (status === 'failed') return 'exception'
  if (status === 'cancelled') return 'warning'
  return ''
}

// 监听路由查询参数变化
watch(() => route.query, (query) => {
  if (query.tab && typeof query.tab === 'string') {
    activeTab.value = query.tab
  }
}, { immediate: true })

// 监听标签切换，当切换到任务列表时加载数据
watch(() => activeTab.value, (newTab) => {
  if (newTab === 'task_list') {
    // 增加延迟时间，确保组件完全挂载
    setTimeout(() => {
      if (taskListRef.value) {
        console.log('开始加载任务列表数据')
        taskListRef.value.loadTasks()
        taskListRef.value.startAutoRefresh()
      } else {
        console.warn('任务列表组件引用尚未可用')
      }
    }, 300) // 增加到300ms
  }
}, { immediate: true })

// 处理标签切换
const handleTabChange = (tab) => {
  router.push({ 
    path: '/data-collection', 
    query: { tab } 
  })
}

// 检查API健康状态
const checkApiHealth = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/health`)
    const prevStatus = apiStatus.value
    apiStatus.value = response.status === 200 && response.data.code === 10000
    
    if (apiStatus.value && !prevStatus) {
      ElNotification({
        title: '连接成功',
        message: 'API服务连接成功',
        type: 'success',
        duration: 2000
      })
    } else if (!apiStatus.value) {
      ElNotification({
        title: '连接失败',
        message: 'API服务异常，请检查后端服务是否启动',
        type: 'error',
        duration: 0
      })
      apiStatusDialog.value = true
    }
  } catch (error) {
    apiStatus.value = false
    ElNotification({
      title: '连接失败',
      message: '无法连接到API服务，请确保后端服务已启动',
      type: 'error',
      duration: 0
    })
    apiStatusDialog.value = true
  }
}

onMounted(() => {
  checkApiHealth()
  
  // 连接 WebSocket 并监听
  webSocketService.connect()
  webSocketService.on('task_update', handleWebSocketUpdate)
})
</script>

<template>
  <div class="data-collection-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>{{ t('dataCollection.title') }}</h1>
      <div class="api-status-indicator" @click="apiStatusDialog = true">
        <div class="status-dot" :class="{ active: apiStatus }"></div>
        <span>{{ apiStatus ? t('dataCollection.status.running') : t('dataCollection.status.disconnected') }}</span>
      </div>
    </div>

    <!-- 主卡片 -->
    <el-card class="main-card">
      <el-tabs 
        v-model="activeTab" 
        class="task-tabs" 
        tab-position="left"
        @tab-change="handleTabChange"
      >
        <el-tab-pane :label="t('dataCollection.tabs.searchIndex')" name="search_index">
          <search-index-task></search-index-task>
        </el-tab-pane>
        
        <el-tab-pane :label="t('dataCollection.tabs.feedIndex')" name="feed_index">
          <feed-index-task></feed-index-task>
        </el-tab-pane>
        
        <el-tab-pane :label="t('dataCollection.tabs.wordGraph')" name="word_graph">
          <word-graph-task></word-graph-task>
        </el-tab-pane>
        
        <el-tab-pane :label="t('dataCollection.tabs.demographicAttributes')" name="demographic_attributes">
          <demographic-attributes-task></demographic-attributes-task>
        </el-tab-pane>
        
        <el-tab-pane :label="t('dataCollection.tabs.interestProfile')" name="interest_profile">
          <interest-profile-task></interest-profile-task>
        </el-tab-pane>
        
        <el-tab-pane :label="t('dataCollection.tabs.regionDistribution')" name="region_distribution">
          <region-distribution-task></region-distribution-task>
        </el-tab-pane>
        
        <el-tab-pane :label="t('dataCollection.tabs.taskList')" name="task_list">
          <task-list ref="taskListRef"></task-list>
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <!-- API状态对话框 -->
    <el-dialog 
      :visible="apiStatusDialog"
      @update:visible="apiStatusDialog = $event"
      :title="t('dataCollection.dialog.title')" 
      width="400px"
      destroy-on-close
      center
    >
      <div class="api-status-content">
        <el-result 
          :icon="apiStatus ? 'success' : 'error'"
          :title="apiStatus ? t('dataCollection.dialog.normal') : t('dataCollection.dialog.abnormal')"
          :sub-title="apiStatus ? t('dataCollection.dialog.normalDesc') : t('dataCollection.dialog.abnormalDesc')"
        >
          <template #extra>
            <el-button type="primary" @click="checkApiHealth">{{ t('common.refresh') }}</el-button>
            <el-button @click="apiStatusDialog = false">{{ t('common.cancel') }}</el-button>
            <div v-if="apiStatus" class="api-endpoint">
              <span>{{ t('dataCollection.dialog.apiAddress') }}: </span>
              <el-tag size="small">{{ API_BASE_URL }}</el-tag>
            </div>
          </template>
        </el-result>
      </div>
    </el-dialog>

    <!-- 全局任务进度悬浮面板 -->
    <transition name="slide-fade">
      <div v-if="showProgressPanel && currentRunningTask" class="global-progress-panel">
        <div class="panel-header">
          <span class="panel-title">
            <span class="status-indicator" :class="currentRunningTask.status"></span>
            {{ t('dataCollection.progress.currentTask') }}: {{ currentRunningTask.taskId }}
          </span>
          <el-icon class="close-btn" @click="showProgressPanel = false"><Close /></el-icon>
        </div>
        <div class="panel-content">
          <div class="progress-info">
            <span class="progress-text">
              {{ t('dataCollection.progress.progress') }}: {{ currentRunningTask.completed_items || 0 }} / {{ currentRunningTask.total_items || '?' }} 
              ({{ currentRunningTask.progress ? currentRunningTask.progress.toFixed(2) : 0 }}%)
            </span>
            <span class="status-text">{{ currentRunningTask.status === 'running' ? t('dataCollection.progress.running') : currentRunningTask.status }}</span>
          </div>
          <el-progress 
            :percentage="currentRunningTask.progress || 0" 
            :status="getProgressStatus(currentRunningTask.status)"
            :stroke-width="10"
            striped
            striped-flow
          />
          <div v-if="currentRunningTask.error_message" class="error-msg">
            {{ currentRunningTask.error_message }}
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<style scoped>
.data-collection-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 30px;
  background: var(--bg-page);
  border-radius: 16px;
  box-shadow: var(--shadow-md);
}

.page-header {
  margin-bottom: 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--text-primary);
}

.page-header h1 {
  font-size: 32px;
  font-weight: bold;
  background: var(--primary-gradient);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.api-status-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 15px;
  border-radius: 25px;
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: var(--shadow-sm);
  color: var(--text-regular);
}

.api-status-indicator:hover {
  background-color: var(--primary-light);
  transform: translateY(-2px);
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: var(--error-color);
  transition: all 0.3s;
}

.status-dot.active {
  background-color: var(--success-color);
  box-shadow: 0 0 0 3px rgba(103, 194, 58, 0.2);
}

.main-card {
  border-radius: 15px;
  box-shadow: var(--shadow-md);
  overflow: hidden;
  background-color: var(--bg-card);
  border: 1px solid var(--border-color);
}

.task-tabs {
  min-height: 600px;
}

.task-tabs :deep(.el-tabs__header) {
  padding: 15px 0;
  background-color: var(--bg-card);
  border-bottom: 2px solid var(--border-color);
}

.task-tabs :deep(.el-tabs__nav) {
  background-color: var(--bg-card);
  border-radius: 8px;
  padding: 10px 0;
}

.task-tabs :deep(.el-tabs__item) {
  height: 50px;
  line-height: 50px;
  padding: 0 20px;
  transition: all 0.3s;
  border-left: 3px solid transparent;
  color: var(--text-regular);
}

.task-tabs :deep(.el-tabs__item.is-active) {
  color: var(--primary-color);
  background-color: var(--primary-light);
  border-left: 3px solid var(--primary-color);
}

.task-tabs :deep(.el-tabs__content) {
  padding: 20px;
  background-color: var(--bg-page);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
}

.api-status-content {
  text-align: center;
}

.api-endpoint {
  margin-top: 10px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: var(--text-regular);
}

/* 全局进度悬浮面板 */
.global-progress-panel {
  position: fixed;
  bottom: 30px;
  right: 30px;
  width: 350px;
  background: var(--bg-card);
  border-radius: 12px;
  box-shadow: var(--shadow-lg);
  z-index: 2000;
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.panel-header {
  padding: 12px 15px;
  background-color: var(--bg-elevated);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.panel-title {
  font-size: 14px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-primary);
}

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: var(--text-secondary);
}

.status-indicator.running { background-color: var(--primary-color); box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2); }
.status-indicator.completed { background-color: var(--success-color); }
.status-indicator.failed { background-color: var(--error-color); }

.close-btn {
  cursor: pointer;
  color: var(--text-secondary);
  transition: color 0.2s;
}

.close-btn:hover {
  color: var(--text-primary);
}

.panel-content {
  padding: 15px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 13px;
  color: var(--text-regular);
}

.error-msg {
  margin-top: 8px;
  font-size: 12px;
  color: var(--error-color);
  line-height: 1.4;
}

.slide-fade-enter-active {
  transition: all 0.3s ease-out;
}

.slide-fade-leave-active {
  transition: all 0.3s cubic-bezier(1, 0.5, 0.8, 1);
}

.slide-fade-enter-from,
.slide-fade-leave-to {
  transform: translateY(20px);
  opacity: 0;
}
</style>
