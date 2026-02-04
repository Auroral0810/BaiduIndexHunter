<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useConfigStore } from '../store/config'

// 使用配置存储
const configStore = useConfigStore()

// 配置分组
const configGroups = [
  { id: 'api', name: 'API配置', icon: 'Connection' },
  { id: 'task', name: '任务配置', icon: 'List' },
  { id: 'spider', name: '爬虫配置', icon: 'Loading' },
  { id: 'output', name: '输出配置', icon: 'Document' },
  { id: 'cookie', name: 'Cookie配置', icon: 'Files' },
  { id: 'system', name: '系统配置', icon: 'Setting' },
  { id: 'ui', name: '界面配置', icon: 'Monitor' }
]

// 当前选中的配置组
const activeGroup = ref('api')

// 加载状态
const loading = computed(() => configStore.isLoading)

// 获取指定分组的配置项
const getGroupConfigs = (group: string) => {
  return configStore.getConfigsByPrefix(group)
}

// 保存配置
const saveConfigs = async (prefix: string) => {
  const result = await configStore.saveConfigsByPrefix(prefix)
  if (result) {
    ElMessage.success('配置保存成功')
  }
}

// 重置配置
const resetConfigs = async () => {
  const result = await configStore.resetConfigs()
  if (result) {
    ElMessage.success('配置已重置为默认值')
  }
}

// 获取配置项类型
const getConfigType = (key: string, value: any) => {
  if (typeof value === 'boolean' || value === 'True' || value === 'False') return 'boolean'
  if (typeof value === 'number') {
    if (key.includes('interval') || key.includes('timeout')) return 'number'
    if (key.includes('port')) return 'port'
    return 'number'
  }
  if (typeof value === 'string') {
    if (key.includes('url') || key.includes('host')) return 'url'
    if (key.includes('password') || key.includes('secret') || key.includes('key_id')) return 'string' // Key ID usually visible
    if (key.includes('secret') || key.includes('password')) return 'password'
    return 'string'
  }
  return 'string'
}

// 获取显示标签（优先使用中文描述）
const getDisplayLabel = (key: string) => {
  const description = getConfigDescription(key)
  return description !== '配置项描述' ? description : getConfigLabel(key)
}

// 获取配置项标签（英文/键名）
const getConfigLabel = (key: string) => {
  const parts = key.split('.')
  if (parts.length < 2) return key
  
  const lastPart = parts[parts.length - 1]
  return lastPart
    .replace(/_/g, ' ')
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, (str) => str.toUpperCase())
}

// 获取配置项描述
const getConfigDescription = (key: string) => {
  const descriptions: Record<string, string> = {
    'api.host': '服务器监听的主机地址',
    'api.port': '服务器监听的端口',
    'api.debug': '是否启用调试模式',
    'api.cors_origins': '允许的跨域来源',
    'api.secret_key': 'API安全密钥',
    'api.token_expire': 'Token过期时间（秒）',
    
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
    'spider.failure_multiplier': '失败后间隔倍数',
    
    'output.default_format': '默认输出格式：csv, excel',
    'output.csv_encoding': 'CSV文件编码',
    'output.excel_sheet_name': 'Excel工作表名称',
    'output.file_name_template': '文件名模板',
    'output.use_oss': '是否上传到阿里云OSS',
    
    'oss.access_key_id': '阿里云AccessKey ID',
    'oss.access_key_secret': '阿里云AccessKey Secret',
    'oss.bucket_name': 'OSS Bucket名称',
    'oss.endpoint': 'OSS Endpoint（例如 oss-cn-beijing.aliyuncs.com）',
    'oss.region': 'OSS Region（例如 cn-beijing）',
    'oss.url': '自定义访问域名（可选）',
    
    'cookie.block_cooldown': 'Cookie封禁冷却时间（秒）',
    'cookie.max_usage_per_day': '每日最大使用次数',
    'cookie.min_available_count': '最小可用Cookie数量',
    'cookie.rotation_strategy': 'Cookie轮换策略',
    
    'system.admin_email': '管理员邮箱',
    'system.maintenance_mode': '是否启用维护模式',
    'system.name': '系统名称',
    'system.version': '系统版本',
    
    'ui.auto_refresh': '是否自动刷新',
    'ui.items_per_page': '每页显示条数',
    'ui.language': '界面语言',
    'ui.refresh_interval': '刷新间隔（秒）',
    'ui.theme': '界面主题'
  }
  
  return descriptions[key] || '配置项描述'
}

// 生命周期钩子
onMounted(async () => {
  await configStore.fetchConfigs()
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
              :loading="loading"
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
                :loading="loading"
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
                  :label="getDisplayLabel(key)"
                >
                  <!-- 布尔类型 -->
                  <el-switch 
                    v-if="getConfigType(key, value) === 'boolean'"
                    v-model="configStore.configs[key]"
                    :active-value="typeof value === 'string' ? 'True' : true"
                    :inactive-value="typeof value === 'string' ? 'False' : false"
                  />
                  
                  <!-- 数字类型 -->
                  <el-input-number 
                    v-else-if="getConfigType(key, value) === 'number'"
                    v-model="configStore.configs[key]"
                    :min="0"
                    :step="key.includes('interval') ? 0.1 : 1"
                  />
                  
                  <!-- 端口类型 -->
                  <el-input-number 
                    v-else-if="getConfigType(key, value) === 'port'"
                    v-model="configStore.configs[key]"
                    :min="1"
                    :max="65535"
                  />
                  
                  <!-- 密码类型 -->
                  <el-input 
                    v-else-if="getConfigType(key, value) === 'password'"
                    v-model="configStore.configs[key]"
                    show-password
                  />
                  
                  <!-- URL类型 -->
                  <el-input 
                    v-else-if="getConfigType(key, value) === 'url'"
                    v-model="configStore.configs[key]"
                    placeholder="例如: http://localhost:5000"
                  />
                  
                  <!-- 默认字符串类型 -->
                  <el-input 
                    v-else
                    v-model="configStore.configs[key]"
                  />
                  
                  <div class="form-item-tip">
                    {{ key }}
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