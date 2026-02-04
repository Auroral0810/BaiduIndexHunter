<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { useConfigStore } from '../store/config'
import { useI18n } from 'vue-i18n'
import { setLocale } from '../i18n'

const { t, locale } = useI18n()

// 使用配置存储
const configStore = useConfigStore()

// 配置分组（精简后）
const configGroups = computed(() => [
  { id: 'task', name: t('settings.groups.task'), icon: 'List' },
  { id: 'spider', name: t('settings.groups.spider'), icon: 'Loading' },
  { id: 'cookie', name: t('settings.groups.cookie'), icon: 'Files' },
  { id: 'output', name: t('settings.groups.output'), icon: 'Document' },
  { id: 'ui', name: t('settings.groups.ui'), icon: 'Monitor' }
])

// 当前选中的配置组
const activeGroup = ref('task')

// 加载状态
const loading = computed(() => configStore.isLoading)

// 语言选项
const languageOptions = [
  { value: 'zh_CN', label: '简体中文' },
  { value: 'zh_TW', label: '繁體中文' },
  { value: 'en', label: 'English' },
  { value: 'ja', label: '日本語' }
]

// 主题选项
const themeOptions = computed(() => [
  { value: 'light', label: t('settings.ui.themeLight') },
  { value: 'dark', label: t('settings.ui.themeDark') }
])

// 本地界面设置
const localSettings = reactive({
  theme: localStorage.getItem('ui.theme') || 'light',
  language: localStorage.getItem('ui.language') || 'zh_CN'
})

// 监听主题变化
watch(() => localSettings.theme, (newTheme) => {
  localStorage.setItem('ui.theme', newTheme)
  applyTheme(newTheme)
})

// 监听语言变化
watch(() => localSettings.language, (newLang) => {
  setLocale(newLang)
  ElMessage.success(t('settings.messages.saveSuccess'))
})

// 应用主题
const applyTheme = (theme: string) => {
  if (theme === 'dark') {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

// 获取指定分组的配置项（过滤掉不需要的配置）
const getGroupConfigs = (group: string) => {
  const configs = configStore.getConfigsByPrefix(group)
  
  // 过滤掉不需要的配置项
  const excludeKeys = [
    'system.admin_email',
    'system.maintenance_mode',
    'system.version',
    'system.name',
    'ui.theme',
    'ui.language',
    'ui.items_per_page',
    'ui.auto_refresh',
    'ui.refresh_interval'
  ]
  
  const filtered: Record<string, any> = {}
  for (const [key, value] of Object.entries(configs)) {
    if (!excludeKeys.includes(key)) {
      filtered[key] = value
    }
  }
  return filtered
}

// 保存配置
const saveConfigs = async (prefix: string) => {
  const result = await configStore.saveConfigsByPrefix(prefix)
  if (result) {
    ElMessage.success(t('settings.messages.saveSuccess'))
  }
}

// 重置配置
const resetConfigs = async () => {
  const result = await configStore.resetConfigs()
  if (result) {
    ElMessage.success(t('settings.messages.resetSuccess'))
  }
}

// 获取配置项类型
const getConfigType = (key: string, value: any) => {
  if (typeof value === 'boolean' || value === 'True' || value === 'False' || value === 'true' || value === 'false') return 'boolean'
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

// 获取配置项描述
const getConfigDescription = (key: string) => {
  const configKey = `settings.configs.${key}`
  const translated = t(configKey)
  // 如果翻译键不存在，返回原始键名
  return translated === configKey ? key.split('.').pop() : translated
}

// 生命周期钩子
onMounted(async () => {
  await configStore.fetchConfigs()
  applyTheme(localSettings.theme)
})
</script>

<template>
  <div class="settings-container">
    <h1 class="page-title">{{ t('settings.title') }}</h1>
    
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
              {{ t('settings.actions.reset') }}
            </el-button>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="19">
        <el-card class="settings-card" shadow="hover" v-loading="loading">
          <template #header>
            <div class="card-header">
              <h2>{{ configGroups.find(g => g.id === activeGroup)?.name }}</h2>
              <el-button 
                v-if="activeGroup !== 'ui'"
                type="primary" 
                @click="saveConfigs(activeGroup)" 
                :loading="loading"
              >
                {{ t('settings.actions.save') }}
              </el-button>
            </div>
          </template>
          
          <div class="config-group">
            <!-- 界面设置：使用本地存储 -->
            <template v-if="activeGroup === 'ui'">
              <el-form label-position="top">
                <el-form-item :label="t('settings.ui.theme')">
                  <el-radio-group v-model="localSettings.theme">
                    <el-radio-button 
                      v-for="option in themeOptions" 
                      :key="option.value" 
                      :value="option.value"
                    >
                      {{ option.label }}
                    </el-radio-button>
                  </el-radio-group>
                  <div class="form-item-tip">{{ t('settings.ui.themeTip') }}</div>
                </el-form-item>
                
                <el-form-item :label="t('settings.ui.language')">
                  <el-select v-model="localSettings.language" style="width: 200px;">
                    <el-option
                      v-for="option in languageOptions"
                      :key="option.value"
                      :label="option.label"
                      :value="option.value"
                    />
                  </el-select>
                  <div class="form-item-tip">{{ t('settings.ui.languageTip') }}</div>
                </el-form-item>
              </el-form>
              
              <el-divider />
              
              <el-alert
                :title="t('common.info')"
                type="info"
                :closable="false"
                show-icon
              >
                <template #default>
                  {{ t('settings.ui.localStorageNote') }}
                </template>
              </el-alert>
            </template>
            
            <!-- 其他配置：从服务器读取 -->
            <template v-else-if="Object.keys(getGroupConfigs(activeGroup)).length > 0">
              <el-form label-position="top">
                <el-form-item 
                  v-for="(value, key) in getGroupConfigs(activeGroup)" 
                  :key="key"
                  :label="getConfigDescription(key)"
                >
                  <!-- 布尔类型 -->
                  <el-switch 
                    v-if="getConfigType(key, value) === 'boolean'"
                    v-model="configStore.configs[key]"
                    :active-value="typeof value === 'string' ? 'true' : true"
                    :inactive-value="typeof value === 'string' ? 'false' : false"
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
                    placeholder="http://localhost:5000"
                  />
                  
                  <!-- 默认字符串类型 -->
                  <el-input 
                    v-else
                    v-model="configStore.configs[key]"
                  />
                  
                  <div class="form-item-tip">{{ key }}</div>
                </el-form-item>
              </el-form>
            </template>
            
            <el-empty 
              v-else 
              :description="t('common.noData')" 
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
  color: var(--text-primary);
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
  border-top: 1px solid var(--border-color);
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
  color: var(--text-primary);
}

.config-group {
  padding: 10px 0;
}

.form-item-tip {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin-top: 5px;
}
</style>
