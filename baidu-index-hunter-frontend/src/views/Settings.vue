<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:5001/api'

// 配置分组
const configGroups = [
  { id: 'api', name: 'API配置', icon: 'Connection' },
  { id: 'task', name: '任务配置', icon: 'List' },
  { id: 'spider', name: '爬虫配置', icon: 'Loading' },
  { id: 'output', name: '输出配置', icon: 'Document' }
]

// 当前选中的配置组
const activeGroup = ref('api')

// 配置数据
const configs = ref({})
const loading = ref(false)
const saving = ref(false)

// 加载配置
const loadConfigs = async () => {
  loading.value = true
  try {
    const response = await axios.get(`${API_BASE_URL}/config/list`)
    
    if (response.data.code === 0) {
      configs.value = response.data.data || {}
      ElMessage.success('配置加载成功')
    } else {
      ElMessage.error(`加载配置失败: ${response.data.message}`)
    }
  } catch (error) {
    ElMessage.error('加载配置失败，请检查网络连接')
    console.error('加载配置错误:', error)
  } finally {
    loading.value = false
  }
}

// 保存配置
const saveConfigs = async (prefix) => {
  saving.value = true
  
  try {
    // 获取指定前缀的配置项
    const configsToSave = {}
    for (const key in configs.value) {
      if (key.startsWith(`${prefix}.`)) {
        configsToSave[key] = configs.value[key]
      }
    }
    
    const response = await axios.post(`${API_BASE_URL}/config/batch_set`, configsToSave)
    
    if (response.data.code === 0) {
      ElMessage.success('配置保存成功')
    } else {
      ElMessage.error(`保存配置失败: ${response.data.message}`)
    }
  } catch (error) {
    ElMessage.error('保存配置失败，请检查网络连接')
    console.error('保存配置错误:', error)
  } finally {
    saving.value = false
  }
}

// 重置配置
const resetConfigs = async () => {
  try {
    const response = await axios.post(`${API_BASE_URL}/config/init_defaults`)
    
    if (response.data.code === 0) {
      ElMessage.success('配置已重置为默认值')
      await loadConfigs()
    } else {
      ElMessage.error(`重置配置失败: ${response.data.message}`)
    }
  } catch (error) {
    ElMessage.error('重置配置失败，请检查网络连接')
    console.error('重置配置错误:', error)
  }
}

// 获取配置项类型
const getConfigType = (key, value) => {
  if (typeof value === 'boolean') return 'boolean'
  if (typeof value === 'number') {
    if (key.includes('interval') || key.includes('timeout')) return 'number'
    if (key.includes('port')) return 'port'
    return 'number'
  }
  if (typeof value === 'string') {
    if (key.includes('url') || key.includes('host')) return 'url'
    if (key.includes('password') || key.includes('secret')) return 'password'
    return 'string'
  }
  return 'string'
}

// 获取配置项标签
const getConfigLabel = (key) => {
  const parts = key.split('.')
  if (parts.length < 2) return key
  
  const lastPart = parts[parts.length - 1]
  return lastPart
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, (str) => str.toUpperCase())
}

// 获取配置项描述
const getConfigDescription = (key) => {
  const descriptions = {
    'api.host': '服务器监听的主机地址',
    'api.port': '服务器监听的端口',
    'api.debug': '是否启用调试模式',
    'api.cors_origins': '允许的跨域来源',
    'task.max_concurrent_tasks': '最大并发任务数',
    'task.queue_check_interval': '任务队列检查间隔（秒）',
    'task.default_priority': '默认任务优先级（1-10）',
    'task.max_retry_count': '任务最大重试次数',
    'task.retry_delay': '任务重试延迟（秒）',
    'spider.min_interval': '请求间隔最小秒数',
    'spider.max_interval': '请求间隔最大秒数',
    'spider.retry_times': '请求失败重试次数',
    'spider.timeout': '请求超时时间（秒）',
    'spider.max_workers': '最大工作线程数',
    'spider.user_agent_rotation': '是否轮换User-Agent',
    'spider.proxy_enabled': '是否启用代理',
    'spider.proxy_url': '代理URL',
    'output.default_format': '默认输出格式：csv, excel',
    'output.csv_encoding': 'CSV文件编码',
    'output.excel_sheet_name': 'Excel工作表名称',
  }
  
  return descriptions[key] || '配置项描述'
}

// 获取指定分组的配置项
const getGroupConfigs = (group) => {
  const result = {}
  for (const key in configs.value) {
    if (key.startsWith(`${group}.`)) {
      result[key] = configs.value[key]
    }
  }
  return result
}

// 生命周期钩子
onMounted(() => {
  loadConfigs()
})
</script>

<template>
  <div class="settings-container">
    <h1 class="page-title">系统配置</h1>
    
    <el-row :gutter="20">
      <el-col :span="5">
        <el-card class="settings-menu-card" shadow="hover">
          <el-menu
            :default-active="activeGroup"
            class="settings-menu"
            @select="activeGroup = $event"
          >
            <el-menu-item 
              v-for="group in configGroups" 
              :key="group.id" 
              :index="group.id"
            >
              <el-icon><component :is="group.icon" /></el-icon>
              <span>{{ group.name }}</span>
            </el-menu-item>
          </el-menu>
          
          <div class="menu-actions">
            <el-button 
              type="warning" 
              @click="resetConfigs" 
              plain 
              icon="Refresh" 
              size="small"
            >
              重置为默认配置
            </el-button>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="19">
        <el-card class="settings-card" shadow="hover" v-loading="loading">
          <template #header>
            <div class="card-header">
              <h2>{{ configGroups.find(g => g.id === activeGroup)?.name || '系统配置' }}</h2>
              <el-button 
                type="primary" 
                @click="saveConfigs(activeGroup)" 
                :loading="saving"
              >
                保存配置
              </el-button>
            </div>
          </template>
          
          <div class="config-group">
            <template v-if="Object.keys(getGroupConfigs(activeGroup)).length > 0">
              <el-form label-position="top">
                <el-form-item 
                  v-for="(value, key) in getGroupConfigs(activeGroup)" 
                  :key="key"
                  :label="getConfigLabel(key)"
                >
                  <!-- 布尔类型 -->
                  <el-switch 
                    v-if="getConfigType(key, value) === 'boolean'"
                    v-model="configs.value[key]"
                  />
                  
                  <!-- 数字类型 -->
                  <el-input-number 
                    v-else-if="getConfigType(key, value) === 'number'"
                    v-model="configs.value[key]"
                    :min="0"
                    :step="key.includes('interval') ? 0.1 : 1"
                  />
                  
                  <!-- 端口类型 -->
                  <el-input-number 
                    v-else-if="getConfigType(key, value) === 'port'"
                    v-model="configs.value[key]"
                    :min="1"
                    :max="65535"
                  />
                  
                  <!-- 密码类型 -->
                  <el-input 
                    v-else-if="getConfigType(key, value) === 'password'"
                    v-model="configs.value[key]"
                    show-password
                  />
                  
                  <!-- URL类型 -->
                  <el-input 
                    v-else-if="getConfigType(key, value) === 'url'"
                    v-model="configs.value[key]"
                    placeholder="例如: http://localhost:5000"
                  />
                  
                  <!-- 默认字符串类型 -->
                  <el-input 
                    v-else
                    v-model="configs.value[key]"
                  />
                  
                  <div class="form-item-tip">
                    {{ getConfigDescription(key) }}
                  </div>
                </el-form-item>
              </el-form>
            </template>
            
            <el-empty 
              v-else 
              description="该分组下没有配置项" 
            />
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.settings-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.page-title {
  font-size: 2rem;
  margin-bottom: 24px;
  color: #303133;
}

.settings-menu-card {
  margin-bottom: 20px;
}

.settings-menu {
  border-right: none;
}

.menu-actions {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
  text-align: center;
}

.settings-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
}

.config-group {
  padding: 10px 0;
}

.form-item-tip {
  font-size: 0.85rem;
  color: #909399;
  margin-top: 5px;
}
</style> 