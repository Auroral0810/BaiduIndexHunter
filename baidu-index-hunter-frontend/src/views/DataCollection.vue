<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElNotification } from 'element-plus'
import axios from 'axios'
import SearchIndexTask from '@/components/tasks/SearchIndexTask.vue'
import FeedIndexTask from '@/components/tasks/FeedIndexTask.vue'
import WordGraphTask from '@/components/tasks/WordGraphTask.vue'
import DemographicAttributesTask from '@/components/tasks/DemographicAttributesTask.vue'
import InterestProfileTask from '@/components/tasks/InterestProfileTask.vue'
import RegionDistributionTask from '@/components/tasks/RegionDistributionTask.vue'
import TaskList from '@/components/tasks/TaskList.vue'
import { webSocketService } from '@/utils/websocket'
import { 
  Close, 
  Search, 
  Reading, 
  Connection, 
  User, 
  Star, 
  MapLocation, 
  List,
  Check,
  Loading
} from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
const { t: $t } = useI18n()
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

// 任务配置
const tasks = [
  { id: 'search_index', label: $t('views.datacollection.2ncis3'), icon: Search, desc: $t('views.datacollection.8d6dy1') },
  { id: 'feed_index', label: $t('views.datacollection.653q6s'), icon: Reading, desc: $t('views.datacollection.770h43') },
  { id: 'word_graph', label: $t('views.datacollection.k08266'), icon: Connection, desc: $t('views.datacollection.it27vl') },
  { id: 'demographic_attributes', label: $t('views.datacollection.i19rq5'), icon: User, desc: $t('views.datacollection.5zbj95') },
  { id: 'interest_profile', label: $t('views.datacollection.7l4pg4'), icon: Star, desc: $t('views.datacollection.i43k73') },
  { id: 'region_distribution', label: $t('views.datacollection.sciq8u'), icon: MapLocation, desc: $t('views.datacollection.41p6g7') },
  { id: 'task_list', label: $t('views.datacollection.718hqw'), icon: List, desc: $t('views.datacollection.6kxv6b') },
]

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
        console.log($t('views.datacollection.s62rmw'))
        taskListRef.value.loadTasks()
        taskListRef.value.startAutoRefresh()
      } else {
        console.warn($t('views.datacollection.yx367u'))
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
        title: $t('views.datacollection.twuj24'),
        message: $t('views.datacollection.220fyz'),
        type: 'success',
        duration: 2000
      })
    } else if (!apiStatus.value) {
      ElNotification({
        title: $t('views.datacollection.77140v'),
        message: $t('views.datacollection.327h7u'),
        type: 'error',
        duration: 0
      })
      apiStatusDialog.value = true
    }
  } catch (error) {
    apiStatus.value = false
    ElNotification({
      title: $t('views.datacollection.77140v'),
      message: $t('views.datacollection.5iycwm'),
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
    <!-- 页面头部 -->
    <div class="page-header">
      <h1>{{$t('views.datacollection.1r5t7h')}}</h1>
      <div class="header-actions">
        <el-tag :type="apiStatus ? 'success' : 'danger'" effect="dark" class="status-tag" @click="apiStatusDialog = true">
          {{ apiStatus ? $t('views.datacollection.qww0ij') : $t('views.datacollection.v35896') }}
        </el-tag>
      </div>
    </div>

    <!-- 主布局 -->
    <div class="collection-layout">
      <!-- 侧边导航 -->
      <aside class="collection-sidebar">
        <div class="sidebar-header">
          <span>{{$t('views.datacollection.h2894t')}}</span>
        </div>
        <div class="task-nav">
          <div 
            v-for="task in tasks" 
            :key="task.id"
            class="task-nav-item"
            :class="{ active: activeTab === task.id }"
            @click="activeTab = task.id; handleTabChange(task.id)"
          >
            <div class="nav-icon-box">
              <el-icon><component :is="task.icon" /></el-icon>
            </div>
            <div class="nav-text">
              <span class="nav-label">{{ task.label }}</span>
              <span class="nav-desc">{{ task.desc }}</span>
            </div>
            <div class="active-indicator"></div>
          </div>
        </div>
      </aside>

      <!-- 内容区域 -->
      <main class="collection-content">
        <div class="content-card">
          <div class="content-header">
            <h2>{{ tasks.find(t => t.id === activeTab)?.label }}</h2>
            <div class="header-actions">
              <!-- 这里可以放置该任务特定的操作按钮 -->
            </div>
          </div>
          
          <div class="task-component-wrapper">
            <keep-alive>
              <component :is="activeTab === 'search_index' ? SearchIndexTask :
                             activeTab === 'feed_index' ? FeedIndexTask :
                             activeTab === 'word_graph' ? WordGraphTask :
                             activeTab === 'demographic_attributes' ? DemographicAttributesTask :
                             activeTab === 'interest_profile' ? InterestProfileTask :
                             activeTab === 'region_distribution' ? RegionDistributionTask :
                             TaskList" 
                         :ref="activeTab === 'task_list' ? 'taskListRef' : undefined" />
            </keep-alive>
          </div>
        </div>
      </main>
    </div>

    <!-- API状态对话框 -->
    <el-dialog 
      v-model="apiStatusDialog"
      :title="$t('views.datacollection.235m2c')" 
      width="400px"
      destroy-on-close
      center
      class="custom-dialog"
    >
      <div class="api-status-content">
        <div class="status-visual" :class="{ 'is-active': apiStatus }">
          <el-icon size="48"><component :is="apiStatus ? Check : Close" /></el-icon>
        </div>
        <h3>{{ apiStatus ? $t('views.datacollection.ldw8s0') : $t('views.datacollection.w4f54h') }}</h3>
        <p>{{ apiStatus ? $t('views.datacollection.rsbfb0') : $t('views.datacollection.5iycwm') }}</p>
        
            <div v-if="apiStatus" class="api-endpoint">
          <span>Endpoint: </span>
          <code>{{ API_BASE_URL }}</code>
            </div>
      </div>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="checkApiHealth" :loading="!apiStatus && apiStatusDialog">{{$t('views.datacollection.14ux91')}}</el-button>
          <el-button @click="apiStatusDialog = false">{{$t('views.datacollection.u24u75')}}</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 全局任务进度悬浮面板 -->
    <transition name="slide-fade">
      <div v-if="showProgressPanel && currentRunningTask" class="global-progress-panel">
        <div class="panel-header">
          <div class="panel-title-area">
            <el-icon class="running-icon is-loading" v-if="currentRunningTask.status === 'running'"><Loading /></el-icon>
            <span class="panel-title">{{$t('views.datacollection.wt72k3')}}{{ currentRunningTask.taskId }}</span>
          </div>
          <el-button link class="close-btn" @click="showProgressPanel = false">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
        
        <div class="panel-content">
          <div class="progress-stats">
            <div class="stat-row">
              <span class="stat-label">{{$t('views.datacollection.6k50e9')}}</span>
              <span class="stat-value">{{ currentRunningTask.completed_items || 0 }} / {{ currentRunningTask.total_items || '?' }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">{{$t('views.cookiemanager.w5f1e1')}}</span>
              <el-tag size="small" :type="getProgressStatus(currentRunningTask.status) || 'primary'">
                {{ currentRunningTask.status === 'running' ? $t('views.datacollection.601og3') : currentRunningTask.status }}
              </el-tag>
            </div>
          </div>
          
          <div class="progress-bar-wrapper">
          <el-progress 
            :percentage="Number((currentRunningTask.progress || 0).toFixed(2))" 
            :status="getProgressStatus(currentRunningTask.status)"
              :stroke-width="8"
            striped
            striped-flow
              :duration="10"
          />
          </div>
          
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
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 24px;
}

/* Header */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 20px 32px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 16px;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  z-index: 10;
  position: relative;
}

:root.dark .page-header {
  background: rgba(30, 41, 59, 0.8);
}

.page-header h1 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-main);
  margin: 0;
}

.status-tag {
  cursor: pointer;
  padding: 0 12px;
  height: 32px;
  line-height: 32px;
  font-weight: 500;
  transition: all 0.2s;
}

.status-tag:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

/* Layout */
.collection-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 32px;
  align-items: start;
}

/* Sidebar */
.collection-sidebar {
  background: var(--color-bg-surface);
  border-radius: 16px;
  border: 1px solid var(--color-border);
  overflow: hidden;
  position: sticky;
  top: 100px;
}

.sidebar-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--color-border);
  font-weight: 700;
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.task-nav {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.task-nav-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.task-nav-item:hover {
  background-color: var(--color-bg-subtle);
}

.task-nav-item.active {
  background-color: var(--color-primary-light);
}

.nav-icon-box {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background-color: var(--color-bg-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  color: var(--color-text-secondary);
  transition: all 0.2s;
}

.task-nav-item.active .nav-icon-box {
  background-color: var(--color-primary);
  color: white;
}

.nav-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.nav-label {
  font-weight: 600;
  color: var(--color-text-main);
  font-size: 0.95rem;
}

.task-nav-item.active .nav-label {
  color: var(--color-primary);
}

.nav-desc {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.active-indicator {
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 0;
  background-color: var(--color-primary);
  border-radius: 0 4px 4px 0;
  transition: height 0.2s ease;
}

.task-nav-item.active .active-indicator {
  height: 60%;
}

/* Content */
.content-card {
  background: var(--color-bg-surface);
  border-radius: 16px;
  border: 1px solid var(--color-border);
  min-height: 600px;
  box-shadow: var(--shadow-sm);
}

.content-header {
  padding: 24px 32px;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: var(--color-bg-subtle);
  border-radius: 16px 16px 0 0;
}

.content-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-main);
}

.task-component-wrapper {
  padding: 32px;
}

/* Dialog */
.status-visual {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  background-color: #fee2e2;
  color: #ef4444;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
}

.status-visual.is-active {
  background-color: #d1fae5;
  color: #10b981;
}

.api-status-content {
  text-align: center;
}

.api-status-content h3 {
  font-size: 1.5rem;
  margin-bottom: 12px;
  color: var(--color-text-main);
}

.api-status-content p {
  color: var(--color-text-secondary);
  margin-bottom: 24px;
}

.api-endpoint {
  background-color: var(--color-bg-subtle);
  padding: 12px;
  border-radius: 8px;
  display: inline-block;
}

.api-endpoint code {
  color: var(--color-primary);
  font-weight: 600;
}

/* Progress Panel */
.global-progress-panel {
  position: fixed;
  bottom: 32px;
  right: 32px;
  width: 380px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 16px;
  box-shadow: var(--shadow-lg);
  border: 1px solid var(--color-border);
  z-index: 2000;
  overflow: hidden;
  animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes slideUp {
  from { transform: translateY(100px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: rgba(255, 255, 255, 0.5);
}

.panel-title-area {
  display: flex;
  align-items: center;
  gap: 8px;
}

.panel-title {
  font-weight: 600;
  color: var(--color-text-main);
  font-size: 0.95rem;
}

.panel-content {
  padding: 20px;
}

.progress-stats {
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
}

.stat-value {
  font-weight: 600;
  font-family: monospace;
  color: var(--color-text-main);
}

.error-msg {
  margin-top: 12px;
  font-size: 0.85rem;
  color: #ef4444;
  background: #fef2f2;
  padding: 8px;
  border-radius: 6px;
  border: 1px solid #fee2e2;
}

/* Responsive */
@media (max-width: 900px) {
  .collection-layout {
    grid-template-columns: 1fr;
  }
  
  .collection-sidebar {
    position: static;
    margin-bottom: 32px;
  }
  
  .task-nav {
    flex-direction: row;
    overflow-x: auto;
    padding-bottom: 16px;
  }
  
  .task-nav-item {
    min-width: 200px;
  }
  
  .active-indicator {
    left: 50%;
    top: auto;
    bottom: 0;
    transform: translateX(-50%);
    width: 0;
    height: 4px;
    border-radius: 4px 4px 0 0;
    transition: width 0.2s ease;
  }
  
  .task-nav-item.active .active-indicator {
    height: 4px;
    width: 60%;
  }
}

@media (max-width: 600px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 20px;
  }
  
  .page-title {
    font-size: 2rem;
  }
  
  .api-status-card {
    width: 100%;
  }
  
  .global-progress-panel {
    width: calc(100% - 48px);
    right: 24px;
    bottom: 24px;
  }
}
</style>

<style scoped>
/* Global Deep Theme Overrides for all child tasks */
:deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background-color: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
  box-shadow: -1px 0 0 0 var(--color-primary) !important;
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
}

:deep(.el-checkbox__input.is-checked + .el-checkbox__label) {
  color: var(--color-primary) !important;
}

:deep(.el-button--primary) {
  --el-button-bg-color: var(--color-primary);
  --el-button-border-color: var(--color-primary);
  --el-button-hover-bg-color: var(--color-primary-light);
  --el-button-hover-border-color: var(--color-primary-light);
  --el-button-active-bg-color: var(--color-primary-dark);
  --el-button-active-border-color: var(--color-primary-dark);
}

:deep(.el-button--primary.is-plain) {
  --el-button-text-color: var(--color-primary);
  --el-button-bg-color: var(--color-bg-subtle);
  --el-button-border-color: var(--color-primary);
  --el-button-hover-text-color: white;
  --el-button-hover-bg-color: var(--color-primary);
  --el-button-hover-border-color: var(--color-primary);
}

:deep(.el-switch.is-checked .el-switch__core) {
  background-color: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
}

:deep(.el-slider__bar) {
  background-color: var(--color-primary) !important;
}

:deep(.el-slider__button) {
  border-color: var(--color-primary) !important;
}
</style>
