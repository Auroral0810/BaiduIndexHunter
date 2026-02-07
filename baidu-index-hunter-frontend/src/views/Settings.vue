<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useConfigStore } from '../store/config'
import { getApiSecretKey, setApiSecretKey } from '../utils/request'
import DirPicker from '../components/DirPicker.vue'
import { List, Loading, Document, Files, Refresh, Check, Connection, Lock, InfoFilled } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
const { t: $t } = useI18n()
// 使用配置存储
const configStore = useConfigStore()

// 配置分组（移除了不必要的配置组）
const configGroups = [
  { id: 'task', name: $t('views.settings.69o614'), icon: List, desc: $t('views.settings.793e27') },
  { id: 'spider', name: $t('views.settings.qas51b'), icon: Loading, desc: $t('views.settings.55l5x3') },
  { id: 'output', name: $t('views.settings.txk3c7'), icon: Document, desc: $t('views.settings.41yx5j') },
  { id: 'cookie', name: $t('views.settings.6ip168'), icon: Files, desc: $t('views.settings.234y82') },
]

// 当前选中的配置组
const activeGroup = ref('task')

// 加载状态
const loading = computed(() => configStore.isLoading)

// 需要隐藏的配置项（敏感信息、不需要的配置）
const hiddenConfigs = [
  // 系统配置
  'system.admin_email',
  'system.name',
  'system.version',
  'system.maintenance_mode',
  // API 敏感配置
  'api.host',
  'api.port',
  'api.debug',
  'api.cors_origins',
  'api.secret_key',
  'api.token_expire',
  // OSS 敏感配置
  'oss.access_key_id',
  'oss.access_key_secret',
  'oss.endpoint',
  'oss.bucket_name',
  'oss.region',
  'oss.url',
  // UI 配置（通过顶部按钮控制）
  'ui.theme',
  'ui.language',
  'ui.auto_refresh',
  'ui.items_per_page',
  'ui.refresh_interval',
]

// 获取指定分组的配置项（过滤掉隐藏的配置）
const getGroupConfigs = (group: string) => {
  const configs = configStore.getConfigsByPrefix(group)
  const filtered = {}
  for (const key in configs) {
    if (!hiddenConfigs.includes(key)) {
      filtered[key] = configs[key]
    }
  }
  return filtered
}

// 保存配置
const saveConfigs = async (prefix: string) => {
  const result = await configStore.saveConfigsByPrefix(prefix)
  if (result) {
    ElMessage.success($t('views.settings.87n068'))
  }
}

// 重置配置
const resetConfigs = async () => {
  const result = await configStore.resetConfigs()
  if (result) {
    ElMessage.success($t('views.settings.jx4357'))
  }
}

// 获取配置项类型
// 需要下拉选择的配置项及其选项
const selectOptions: Record<string, { label: string; value: string }[]> = {
  'output.default_format': [
    { label: 'CSV (.csv)', value: 'csv' },
    { label: 'Excel (.xlsx)', value: 'excel' },
    { label: 'JSON (.json)', value: 'json' },
    { label: 'Stata (.dta)', value: 'dta' },
    { label: 'Parquet (.parquet)', value: 'parquet' },
    { label: 'SQLite (.sqlite)', value: 'sql' },
  ],
  'cookie.rotation_strategy': [
    { label: 'round_robin', value: 'round_robin' },
    { label: 'random', value: 'random' },
    { label: 'least_used', value: 'least_used' },
  ],
}

// 需要目录路径选择器的配置项
const pathConfigs = ['output.default_dir']

const getConfigType = (key: string, value: any) => {
  // 检查是否为目录路径类型
  if (pathConfigs.includes(key)) return 'path'
  // 检查是否有预定义的下拉选项
  if (selectOptions[key]) return 'select'
  if (typeof value === 'boolean' || value === 'True' || value === 'False' || value === 'true' || value === 'false') return 'boolean'
  if (typeof value === 'number') {
    if (key.includes('interval') || key.includes('timeout')) return 'number'
    if (key.includes('port')) return 'port'
    return 'number'
  }
  if (typeof value === 'string') {
    if (key.includes('url') || key.includes('host')) return 'url'
    if (key.includes('secret') || key.includes('password')) return 'password'
    return 'string'
  }
  return 'string'
}

// 目录选择功能已由 DirPicker 组件提供

// 获取显示标签（优先使用中文描述）
const getDisplayLabel = (key: string) => {
  const description = getConfigDescription(key)
  return description !== $t('views.settings.8x81cv') ? description : getConfigLabel(key)
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
    // 任务配置
    'task.max_concurrent_tasks': $t('views.settings.u3c1hw'),
    'task.queue_check_interval': $t('views.settings.6v1yu9'),
    'task.default_priority': $t('views.settings.655xlj'),
    'task.max_retry_count': $t('views.settings.pdxdm5'),
    'task.retry_delay': $t('views.settings.vs2rn7'),
    
    // 爬虫配置
    'spider.min_interval': $t('views.settings.atl87p'),
    'spider.max_interval': $t('views.settings.00sc35'),
    'spider.retry_times': $t('views.settings.o37987'),
    'spider.timeout': $t('views.settings.q621z9'),
    'spider.max_workers': $t('views.settings.vb1k63'),
    'spider.user_agent_rotation': $t('views.settings.2x1gk7'),
    'spider.proxy_enabled': $t('views.settings.r3739f'),
    'spider.proxy_url': $t('views.settings.78hr7f'),
    'spider.failure_multiplier': $t('views.settings.2732fq'),
    
    // 输出配置
    'output.default_dir': '默认输出文件夹',
    'output.default_format': $t('views.settings.5pe522'),
    'output.csv_encoding': $t('views.settings.813612'),
    'output.excel_sheet_name': $t('views.settings.1744lc'),
    'output.file_name_template': $t('views.settings.275yf1'),
    'output.use_oss': $t('views.settings.63ld83'),
    
    // Cookie配置
    'cookie.block_cooldown': $t('views.settings.42533h'),
    'cookie.max_usage_per_day': $t('views.settings.t8dliz'),
    'cookie.min_available_count': $t('views.settings.9ue5fu'),
    'cookie.rotation_strategy': $t('views.settings.j56utr'),
  }
  
  return descriptions[key] || $t('views.settings.8x81cv')
}

// API 密钥（本地存储，与后端 API_SECRET_KEY 一致）
const apiSecretKey = ref('')
const saveApiKey = async () => {
  setApiSecretKey(apiSecretKey.value)
  if (apiSecretKey.value) {
    await configStore.fetchConfigs()
  }
  ElMessage.success($t('views.settings.api_key_saved'))
}

// 生命周期钩子
onMounted(async () => {
  apiSecretKey.value = getApiSecretKey() || ''
  await configStore.fetchConfigs()
})
</script>

<template>
  <div class="settings-page">
    <!-- 页面头部 -->
    <header class="page-header">
      <h1 class="page-title">{{$t('views.settings.49a0cg')}}</h1>
      <p class="page-subtitle">{{$t('views.settings.6316r3')}}</p>
    </header>

    <!-- API 连接 -->
    <div class="api-auth-section">
      <div class="api-auth-card">
        <div class="api-card-content">
          <div class="api-icon-wrapper">
            <el-icon><Connection /></el-icon>
          </div>
          <div class="api-main-info">
            <div class="api-header-row">
              <h2 class="api-auth-title">{{ $t('views.settings.api_connection_title') }}</h2>
              <el-tag 
                :type="apiSecretKey ? 'success' : 'info'" 
                effect="dark"
                class="status-tag"
                size="small"
              >
                {{ apiSecretKey ? $t('views.settings.api_configured') : $t('views.settings.api_not_configured') }}
              </el-tag>
            </div>
            <p class="api-auth-desc">{{ $t('views.settings.api_connection_desc') }}</p>
            
            <div class="api-input-wrapper">
              <el-input
                v-model="apiSecretKey"
                type="password"
                show-password
                :placeholder="$t('views.settings.api_input_placeholder')"
                clearable
                size="large"
                class="api-key-input premium-input"
                @blur="saveApiKey"
              >
                <template #prefix>
                  <el-icon class="input-icon"><Lock /></el-icon>
                </template>
              </el-input>
            </div>
          </div>
        </div>
        
        <div class="api-info-box">
          <el-icon class="info-icon"><InfoFilled /></el-icon>
          <span class="info-text">{{ $t('views.settings.api_tip') }}</span>
        </div>
      </div>
    </div>
    
    <div class="settings-layout">
      <!-- 侧边导航 -->
      <aside class="settings-sidebar">
        <nav class="settings-nav">
          <div 
              v-for="group in configGroups" 
              :key="group.id" 
            class="nav-item"
            :class="{ active: activeGroup === group.id }"
            @click="activeGroup = group.id"
            >
            <div class="nav-icon">
              <el-icon><component :is="group.icon" /></el-icon>
            </div>
            <div class="nav-content">
              <span class="nav-title">{{ group.name }}</span>
              <span class="nav-desc">{{ group.desc }}</span>
            </div>
          </div>
        </nav>
        
        <div class="sidebar-actions">
            <el-button 
            class="reset-btn"
              @click="resetConfigs" 
              plain 
            :icon="Refresh" 
              :loading="loading"
          >{{$t('views.settings.8u2y54')}}</el-button>
          </div>
      </aside>
      
      <!-- 配置内容 -->
      <main class="settings-content" v-loading="loading">
        <div class="content-card">
            <div class="card-header">
            <h2 class="group-title">
              {{ configGroups.find(g => g.id === activeGroup)?.name }}
            </h2>
              <el-button 
                type="primary" 
              class="save-btn"
                @click="saveConfigs(activeGroup)" 
                :loading="loading"
              :icon="Check"
            >{{$t('views.settings.0q2j84')}}</el-button>
            </div>
          
          <div class="config-form-wrapper">
            <template v-if="Object.keys(getGroupConfigs(activeGroup)).length > 0">
              <el-form label-position="top" class="config-form">
                <el-row :gutter="24">
                  <el-col 
                  v-for="(value, key) in getGroupConfigs(activeGroup)" 
                  :key="key"
                    :span="12"
                    :xs="24"
                >
                    <el-form-item :label="getDisplayLabel(String(key))" class="custom-form-item">
                  <!-- 布尔类型 -->
                      <div v-if="getConfigType(String(key), value) === 'boolean'" class="switch-wrapper">
                  <el-switch 
                    v-model="configStore.configs[key]"
                          :active-value="typeof value === 'string' ? 'true' : true"
                          :inactive-value="typeof value === 'string' ? 'false' : false"
                  />
                        <span class="switch-label">{{ configStore.configs[key] ? $t('views.settings.7p05v8') : $t('views.settings.5n3p7s') }}</span>
                      </div>
                  
                  <!-- 下拉选择类型 -->
                  <el-select 
                        v-else-if="getConfigType(String(key), value) === 'select'"
                    v-model="configStore.configs[key]"
                        class="full-width-input"
                  >
                    <el-option 
                      v-for="opt in selectOptions[String(key)]" 
                      :key="opt.value" 
                      :label="opt.label" 
                      :value="opt.value" 
                    />
                  </el-select>
                  
                  <!-- 数字类型 -->
                  <el-input-number 
                        v-else-if="getConfigType(String(key), value) === 'number'"
                    v-model="configStore.configs[key]"
                    :min="0"
                        :step="String(key).includes('interval') ? 0.1 : 1"
                        controls-position="right"
                        class="full-width-input"
                  />
                  
                  <!-- 端口类型 -->
                  <el-input-number 
                        v-else-if="getConfigType(String(key), value) === 'port'"
                    v-model="configStore.configs[key]"
                    :min="1"
                    :max="65535"
                        controls-position="right"
                        class="full-width-input"
                  />
                  
                  <!-- 密码类型 -->
                  <el-input 
                        v-else-if="getConfigType(String(key), value) === 'password'"
                    v-model="configStore.configs[key]"
                    show-password
                        class="custom-input"
                  />
                  
                  <!-- 路径类型（目录选择器） -->
                  <DirPicker
                    v-else-if="getConfigType(String(key), value) === 'path'"
                    v-model="configStore.configs[key]"
                    placeholder="输入文件夹路径或点击浏览选择"
                    hint="可直接输入路径或点击浏览按钮选择文件夹"
                  />

                  <!-- URL类型 -->
                  <el-input 
                        v-else-if="getConfigType(String(key), value) === 'url'"
                    v-model="configStore.configs[key]"
                        :placeholder="$t('views.settings.7f3hu6')"
                        class="custom-input"
                  />
                  
                  <!-- 默认字符串类型 -->
                  <el-input 
                    v-else
                    v-model="configStore.configs[key]"
                        class="custom-input"
                  />
                  
                      <div class="form-key-tip">{{ key }}</div>
                </el-form-item>
                  </el-col>
                </el-row>
              </el-form>
            </template>
            
            <el-empty 
              v-else 
              :description="$t('views.settings.dn9z5l')" 
              :image-size="120"
            />
          </div>
        </div>
      </main>
    </div>

    <!-- 目录浏览对话框 -->
    <!-- 目录浏览器已由 DirPicker 组件内置提供 -->
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 24px;
}

/* Header */
.page-header {
  margin-bottom: 32px;
}

.page-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text-main);
  margin-bottom: 8px;
  letter-spacing: -0.5px;
}

.page-subtitle {
  font-size: 0.95rem;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
}

.api-auth-section {
  margin-bottom: 32px;
}
.api-auth-card {
  padding: 0;
  background: var(--color-bg-surface);
  border-radius: 12px;
  border: 1px solid var(--color-border);
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  overflow: hidden;
  max-width: 800px;
}

.api-card-content {
  padding: 24px;
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.api-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(79, 70, 229, 0.1) 0%, rgba(79, 70, 229, 0.2) 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
  font-size: 24px;
  flex-shrink: 0;
}

.api-main-info {
  flex: 1;
}

.api-header-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.api-auth-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text-main);
  margin: 0;
}

.api-auth-desc {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  margin: 0 0 20px 0;
  line-height: 1.5;
}

.api-input-wrapper {
  max-width: 100%;
}

.premium-input :deep(.el-input__wrapper) {
  background-color: var(--color-bg-subtle);
  box-shadow: none !important;
  border: 1px solid transparent;
  transition: all 0.3s ease;
  padding-left: 12px;
}

.premium-input :deep(.el-input__wrapper.is-focus) {
  background-color: var(--color-bg-surface);
  border-color: var(--color-primary);
  box-shadow: 0 0 0 4px rgba(79, 70, 229, 0.1) !important;
}

.input-icon {
  font-size: 16px;
  color: var(--color-text-tertiary);
}

.api-info-box {
  background: var(--color-bg-subtle);
  padding: 12px 24px;
  border-top: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-icon {
  color: var(--color-primary);
  font-size: 16px;
}

.info-text {
  font-size: 13px;
  color: var(--color-text-secondary);
}

/* API Auth Section Old Styles Removed */
.api-key-input {
  width: 100%;
}

/* Layout */
.settings-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 32px;
  align-items: start;
}

/* Sidebar */
.settings-sidebar {
  background: var(--color-bg-surface);
  border-radius: 16px;
  padding: 16px;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  position: sticky;
  top: 100px;
}

.settings-nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
}

.nav-item:hover {
  background-color: var(--color-bg-subtle);
}

.nav-item.active {
  background-color: var(--color-primary-light);
  border-color: rgba(79, 70, 229, 0.1);
}

.nav-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background-color: var(--color-bg-subtle);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
  font-size: 1.2rem;
  transition: all 0.2s;
}

.nav-item.active .nav-icon {
  background-color: var(--color-primary);
  color: white;
}

.nav-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-title {
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--color-text-main);
}

.nav-item.active .nav-title {
  color: var(--color-primary);
}

.nav-desc {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
}

.sidebar-actions {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid var(--color-border);
}

.reset-btn {
  width: 100%;
  border-radius: 8px;
}

/* Content */
.content-card {
  background: var(--color-bg-surface);
  border-radius: 16px;
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-sm);
  overflow: hidden;
}

.card-header {
  padding: 24px 32px;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background-color: var(--color-bg-subtle);
}

.group-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-main);
  margin: 0;
}

.save-btn {
  border-radius: 8px;
  padding: 10px 24px;
  font-weight: 600;
  background-color: var(--color-primary);
  border-color: var(--color-primary);
  transition: all 0.2s;
}

.save-btn:hover {
  background-color: var(--color-primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2);
}

.config-form-wrapper {
  padding: 32px;
}

/* Form Styles */
.custom-form-item {
  background-color: var(--color-bg-subtle);
  padding: 16px 20px;
  border-radius: 12px;
  border: 1px solid transparent;
  transition: all 0.2s;
  margin-bottom: 24px !important;
}

.custom-form-item:hover {
  background-color: var(--color-bg-surface);
  border-color: var(--color-border);
  box-shadow: var(--shadow-sm);
}

:deep(.el-form-item__label) {
  font-weight: 600;
  color: var(--color-text-main) !important;
  font-size: 0.95rem;
  margin-bottom: 8px !important;
}

.form-key-tip {
  font-size: 0.75rem;
  color: var(--color-text-tertiary);
  margin-top: 8px;
  font-family: monospace;
  background: rgba(0,0,0,0.03);
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
}

/* Input Styles Overrides */
:deep(.el-input__wrapper),
:deep(.el-input-number__decrease),
:deep(.el-input-number__increase) {
  border-radius: 8px;
  box-shadow: 0 0 0 1px var(--color-border) inset !important;
  background-color: var(--color-bg-surface);
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--color-primary) inset !important;
}

.full-width-input {
  width: 100% !important;
}

.switch-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.switch-label {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

/* Responsive */
@media (max-width: 900px) {
  .settings-layout {
    grid-template-columns: 1fr;
  }
  
  .settings-sidebar {
    position: static;
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 20px;
    align-items: center;
  }
  
  .settings-nav {
    flex-direction: row;
    overflow-x: auto;
    padding-bottom: 4px;
  }
  
  .nav-item {
    min-width: 160px;
  }
  
  .sidebar-actions {
    margin-top: 0;
    padding-top: 0;
    border-top: none;
  }
}

@media (max-width: 600px) {
  .page-title {
    font-size: 2rem;
  }
  
  .settings-sidebar {
    grid-template-columns: 1fr;
  }
  
  .settings-nav {
    flex-direction: column;
  }
  
  .card-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .save-btn {
    width: 100%;
  }
}

/* DirPicker 在 settings 中的宽度 */

/* 目录浏览器 */
/* 目录浏览器样式已内置在 DirPicker 组件中 */
</style> 
