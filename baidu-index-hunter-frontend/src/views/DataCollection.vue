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

const API_BASE_URL = 'http://127.0.0.1:5001/api'

const route = useRoute()
const router = useRouter()

const activeTab = ref('search_index')
const apiStatus = ref(false)
const apiStatusDialog = ref(false)
const taskListRef = ref(null)

watch(() => route.query, (query) => {
  if (query.tab && typeof query.tab === 'string') {
    activeTab.value = query.tab
  }
}, { immediate: true })

// 监听标签切换，当切换到任务列表时加载数据
watch(() => activeTab.value, (newTab) => {
  if (newTab === 'task_list' && taskListRef.value) {
    // 延迟一点加载，确保组件已完全挂载
    setTimeout(() => {
      taskListRef.value.loadTasks()
      taskListRef.value.startAutoRefresh()
    }, 100)
  }
}, { immediate: true })

const handleTabChange = (tab: string) => {
  router.push({ 
    path: '/data-collection', 
    query: { tab } 
  })
  
  // 如果切换到任务列表，加载任务数据
  if (tab === 'task_list' && taskListRef.value) {
    taskListRef.value.loadTasks()
    taskListRef.value.startAutoRefresh()
  }
}

onMounted(() => {
  checkApiHealth()
})

const checkApiHealth = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/health`)
    const prevStatus = apiStatus.value
    apiStatus.value = response.status === 200
    
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
</script>

<template>
  <div class="data-collection-container">
    <div class="page-header">
      <h1>百度指数数据采集</h1>
      <div class="api-status-indicator" @click="apiStatusDialog = true">
        <div class="status-dot" :class="{ active: apiStatus }"></div>
        <span>{{ apiStatus ? '服务运行中' : '服务未连接' }}</span>
      </div>
    </div>

    <el-card class="main-card">
      <el-tabs 
        v-model="activeTab" 
        class="task-tabs" 
        tab-position="left"
        @tab-change="handleTabChange"
      >
        <el-tab-pane label="搜索指数" name="search_index">
          <search-index-task />
        </el-tab-pane>
        <el-tab-pane label="资讯指数" name="feed_index">
          <feed-index-task />
        </el-tab-pane>
        <el-tab-pane label="需求图谱" name="word_graph">
          <word-graph-task />
        </el-tab-pane>
        <el-tab-pane label="人群属性" name="demographic_attributes">
          <demographic-attributes-task />
        </el-tab-pane>
        <el-tab-pane label="兴趣分析" name="interest_profile">
          <interest-profile-task />
        </el-tab-pane>
        <el-tab-pane label="地域分布" name="region_distribution">
          <region-distribution-task />
        </el-tab-pane>
        <el-tab-pane label="任务列表" name="task_list">
          <task-list ref="taskListRef" />
        </el-tab-pane>
      </el-tabs>
    </el-card>

    <el-dialog 
      v-model="apiStatusDialog" 
      title="API服务状态" 
      width="400px"
      destroy-on-close
      center
    >
      <div class="api-status-content">
        <el-result 
          :icon="apiStatus ? 'success' : 'error'"
          :title="apiStatus ? 'API服务正常' : 'API服务异常'"
          :sub-title="apiStatus ? '服务连接正常，可以正常采集数据' : '无法连接到API服务，请确保后端服务已启动'"
        >
          <template #extra>
            <el-button type="primary" @click="checkApiHealth">刷新状态</el-button>
            <el-button @click="apiStatusDialog = false">关闭</el-button>
            <div class="api-endpoint" v-if="apiStatus">
              <span>API地址: </span>
              <el-tag size="small">{{ API_BASE_URL }}</el-tag>
            </div>
          </template>
        </el-result>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.data-collection-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 30px;
  background: #f4f7fc;
  border-radius: 16px;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
}

.page-header {
  margin-bottom: 30px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #333;
}

.page-header h1 {
  font-size: 32px;
  font-weight: bold;
  color: #409EFF;
  background: linear-gradient(45deg, #409EFF, #67C23A);
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
  background-color: #f9fafb;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.api-status-indicator:hover {
  background-color: #e3f4ff;
  transform: translateY(-2px);
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: #F56C6C;
  transition: all 0.3s;
}

.status-dot.active {
  background-color: #67C23A;
  box-shadow: 0 0 0 3px rgba(103, 194, 58, 0.2);
}

.main-card {
  border-radius: 15px;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  background-color: #fff;
}

.task-tabs {
  min-height: 600px;
}

.task-tabs :deep(.el-tabs__header) {
  padding: 15px 0;
  background-color: #ffffff;
  border-bottom: 2px solid #eff2f7;
}

.task-tabs :deep(.el-tabs__nav) {
  background-color: #ffffff;
  border-radius: 8px;
  padding: 10px 0;
}

.task-tabs :deep(.el-tabs__item) {
  height: 50px;
  line-height: 50px;
  padding: 0 20px;
  transition: all 0.3s;
  border-left: 3px solid transparent;
}

.task-tabs :deep(.el-tabs__item.is-active) {
  color: #409EFF;
  background-color: #ecf5ff;
  border-left: 3px solid #409EFF;
}

.task-tabs :deep(.el-tabs__content) {
  padding: 20px;
  background-color: #fafafa;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
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
}
</style>
