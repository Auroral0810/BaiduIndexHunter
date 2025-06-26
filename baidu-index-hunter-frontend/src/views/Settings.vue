<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'

// 表单数据
const apiForm = reactive({
  baseUrl: 'http://localhost:5000',
  apiKey: '',
  timeout: 30000
})

const cookieForm = reactive({
  minAvailableCookies: 3,
  cookieBlockCooldown: 30,
  cookieExpirationBuffer: 3600
})

const spiderForm = reactive({
  minInterval: 3,
  maxInterval: 10,
  retryTimes: 3,
  timeout: 30,
  maxWorkers: 10
})

// 状态
const apiFormLoading = ref(false)
const cookieFormLoading = ref(false)
const spiderFormLoading = ref(false)

// Cookie池状态
const cookiePoolStatus = ref({
  total: 0,
  available: 0,
  blocked: 0
})

const cookiePoolLoading = ref(false)

// 方法
const loadSettings = async () => {
  apiFormLoading.value = true
  cookieFormLoading.value = true
  spiderFormLoading.value = true
  
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 这里应该是从API获取实际设置
    // 这里仅作为示例
    apiForm.baseUrl = 'http://localhost:5000'
    apiForm.apiKey = 'sk_test_*****'
    apiForm.timeout = 30000
    
    cookieForm.minAvailableCookies = 3
    cookieForm.cookieBlockCooldown = 30
    cookieForm.cookieExpirationBuffer = 3600
    
    spiderForm.minInterval = 3
    spiderForm.maxInterval = 10
    spiderForm.retryTimes = 3
    spiderForm.timeout = 30
    spiderForm.maxWorkers = 10
    
    ElMessage.success('设置加载成功')
  } catch (error) {
    ElMessage.error('加载设置失败')
    console.error('加载设置错误:', error)
  } finally {
    apiFormLoading.value = false
    cookieFormLoading.value = false
    spiderFormLoading.value = false
  }
}

const loadCookiePoolStatus = async () => {
  cookiePoolLoading.value = true
  
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 这里应该是从API获取实际的Cookie池状态
    // 这里仅作为示例
    cookiePoolStatus.value = {
      total: 15,
      available: 12,
      blocked: 3,
      cooldown_status: {
        'cookie_1': { remaining_minutes: 5 },
        'cookie_2': { remaining_minutes: 12 },
        'cookie_3': { remaining_minutes: 8 },
      }
    }
  } catch (error) {
    ElMessage.error('加载Cookie池状态失败')
    console.error('加载Cookie池状态错误:', error)
  } finally {
    cookiePoolLoading.value = false
  }
}

const saveApiSettings = async () => {
  apiFormLoading.value = true
  
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 这里应该是实际保存设置的API调用
    console.log('保存API设置:', apiForm)
    
    ElMessage.success('API设置保存成功')
  } catch (error) {
    ElMessage.error('保存API设置失败')
    console.error('保存API设置错误:', error)
  } finally {
    apiFormLoading.value = false
  }
}

const saveCookieSettings = async () => {
  cookieFormLoading.value = true
  
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 这里应该是实际保存设置的API调用
    console.log('保存Cookie设置:', cookieForm)
    
    ElMessage.success('Cookie设置保存成功')
  } catch (error) {
    ElMessage.error('保存Cookie设置失败')
    console.error('保存Cookie设置错误:', error)
  } finally {
    cookieFormLoading.value = false
  }
}

const saveSpiderSettings = async () => {
  spiderFormLoading.value = true
  
  try {
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 500))
    
    // 这里应该是实际保存设置的API调用
    console.log('保存爬虫设置:', spiderForm)
    
    ElMessage.success('爬虫设置保存成功')
  } catch (error) {
    ElMessage.error('保存爬虫设置失败')
    console.error('保存爬虫设置错误:', error)
  } finally {
    spiderFormLoading.value = false
  }
}

const refreshCookiePool = async () => {
  try {
    await ElMessage.confirm('确定要刷新Cookie池状态吗？', '确认', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await loadCookiePoolStatus()
    ElMessage.success('Cookie池状态已刷新')
  } catch {
    // 用户取消
  }
}

const unlockAllCookies = async () => {
  try {
    await ElMessage.confirm('确定要解锁所有Cookie吗？这可能影响爬取效率。', '确认', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    cookiePoolLoading.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 这里应该是实际解锁Cookie的API调用
    
    cookiePoolStatus.value.blocked = 0
    cookiePoolStatus.value.available = cookiePoolStatus.value.total
    cookiePoolStatus.value.cooldown_status = {}
    
    ElMessage.success('所有Cookie已解锁')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('解锁Cookie失败')
      console.error('解锁Cookie错误:', error)
    }
  } finally {
    cookiePoolLoading.value = false
  }
}

// 生命周期钩子
onMounted(() => {
  loadSettings()
  loadCookiePoolStatus()
})
</script>

<template>
  <div class="settings-container">
    <h1 class="page-title">配置信息</h1>
    
    <el-row :gutter="20">
      <el-col :span="16">
        <!-- API设置 -->
        <el-card class="settings-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <h2>API 设置</h2>
              <el-button type="primary" @click="saveApiSettings" :loading="apiFormLoading">
                保存设置
              </el-button>
            </div>
          </template>
          
          <el-form :model="apiForm" label-position="top" :disabled="apiFormLoading">
            <el-form-item label="API 基础URL">
              <el-input v-model="apiForm.baseUrl" placeholder="例如: http://localhost:5000"></el-input>
            </el-form-item>
            
            <el-form-item label="API 密钥">
              <el-input v-model="apiForm.apiKey" placeholder="API密钥" show-password></el-input>
            </el-form-item>
            
            <el-form-item label="请求超时时间 (毫秒)">
              <el-input-number v-model="apiForm.timeout" :min="1000" :max="60000" :step="1000"></el-input-number>
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- Cookie设置 -->
        <el-card class="settings-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <h2>Cookie 管理设置</h2>
              <el-button type="primary" @click="saveCookieSettings" :loading="cookieFormLoading">
                保存设置
              </el-button>
            </div>
          </template>
          
          <el-form :model="cookieForm" label-position="top" :disabled="cookieFormLoading">
            <el-form-item label="最小可用Cookie数量">
              <el-input-number v-model="cookieForm.minAvailableCookies" :min="1" :max="50"></el-input-number>
              <div class="form-item-tip">
                当可用Cookie数量低于此值时，系统将尝试重新登录获取Cookie
              </div>
            </el-form-item>
            
            <el-form-item label="Cookie冷却时间 (分钟)">
              <el-input-number v-model="cookieForm.cookieBlockCooldown" :min="5" :max="120"></el-input-number>
              <div class="form-item-tip">
                Cookie被锁定后，需要等待的冷却时间
              </div>
            </el-form-item>
            
            <el-form-item label="Cookie过期缓冲时间 (秒)">
              <el-input-number v-model="cookieForm.cookieExpirationBuffer" :min="600" :max="86400" :step="600"></el-input-number>
              <div class="form-item-tip">
                Cookie过期前的缓冲时间，系统将在Cookie过期前此段时间刷新Cookie
              </div>
            </el-form-item>
          </el-form>
        </el-card>
        
        <!-- 爬虫设置 -->
        <el-card class="settings-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <h2>爬虫设置</h2>
              <el-button type="primary" @click="saveSpiderSettings" :loading="spiderFormLoading">
                保存设置
              </el-button>
            </div>
          </template>
          
          <el-form :model="spiderForm" label-position="top" :disabled="spiderFormLoading">
            <el-form-item label="请求间隔时间">
              <div class="interval-inputs">
                <el-input-number v-model="spiderForm.minInterval" :min="1" :max="30" placeholder="最小间隔"></el-input-number>
                <span class="interval-separator">~</span>
                <el-input-number v-model="spiderForm.maxInterval" :min="1" :max="30" placeholder="最大间隔"></el-input-number>
                <span class="interval-unit">秒</span>
              </div>
              <div class="form-item-tip">
                每次请求之间的随机等待时间范围
              </div>
            </el-form-item>
            
            <el-form-item label="重试次数">
              <el-input-number v-model="spiderForm.retryTimes" :min="0" :max="10"></el-input-number>
              <div class="form-item-tip">
                请求失败时的最大重试次数
              </div>
            </el-form-item>
            
            <el-form-item label="请求超时时间 (秒)">
              <el-input-number v-model="spiderForm.timeout" :min="5" :max="120"></el-input-number>
            </el-form-item>
            
            <el-form-item label="最大爬虫工作线程数">
              <el-input-number v-model="spiderForm.maxWorkers" :min="1" :max="50"></el-input-number>
              <div class="form-item-tip">
                并行处理任务的最大线程数，建议根据硬件配置设置
              </div>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>
      
      <el-col :span="8">
        <!-- Cookie池状态 -->
        <el-card class="settings-card cookie-status-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <h2>Cookie池状态</h2>
              <el-button @click="refreshCookiePool" :loading="cookiePoolLoading" plain>
                刷新
              </el-button>
            </div>
          </template>
          
          <div v-loading="cookiePoolLoading">
            <div class="cookie-status-section">
              <el-row :gutter="10">
                <el-col :span="8">
                  <div class="status-item">
                    <div class="status-value">{{ cookiePoolStatus.total }}</div>
                    <div class="status-label">总数</div>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="status-item success">
                    <div class="status-value">{{ cookiePoolStatus.available }}</div>
                    <div class="status-label">可用</div>
                  </div>
                </el-col>
                <el-col :span="8">
                  <div class="status-item danger">
                    <div class="status-value">{{ cookiePoolStatus.blocked }}</div>
                    <div class="status-label">锁定</div>
                  </div>
                </el-col>
              </el-row>
            </div>
            
            <el-divider></el-divider>
            
            <div class="cookie-actions">
              <el-button type="warning" @click="unlockAllCookies" :loading="cookiePoolLoading">
                解锁所有Cookie
              </el-button>
            </div>
            
            <div v-if="cookiePoolStatus.blocked > 0" class="blocked-cookies-list">
              <h3>被锁定的Cookie</h3>
              <el-table :data="Object.entries(cookiePoolStatus.cooldown_status || {}).map(([id, status]) => ({ id, ...status }))">
                <el-table-column prop="id" label="Cookie ID"></el-table-column>
                <el-table-column prop="remaining_minutes" label="剩余冷却时间">
                  <template #default="scope">
                    {{ scope.row.remaining_minutes }} 分钟
                  </template>
                </el-table-column>
              </el-table>
            </div>
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
}

.page-title {
  font-size: 2rem;
  margin-bottom: 24px;
  color: #303133;
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

.form-item-tip {
  font-size: 0.85rem;
  color: #909399;
  margin-top: 5px;
}

.interval-inputs {
  display: flex;
  align-items: center;
}

.interval-separator {
  margin: 0 10px;
  color: #909399;
}

.interval-unit {
  margin-left: 10px;
  color: #909399;
}

.cookie-status-section {
  padding: 10px 0;
}

.status-item {
  text-align: center;
  padding: 15px 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.status-value {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 5px;
}

.status-label {
  font-size: 0.9rem;
  color: #606266;
}

.status-item.success .status-value {
  color: #67c23a;
}

.status-item.danger .status-value {
  color: #f56c6c;
}

.cookie-actions {
  display: flex;
  justify-content: center;
  margin: 20px 0;
}

.blocked-cookies-list {
  margin-top: 20px;
}

.blocked-cookies-list h3 {
  font-size: 1rem;
  margin-bottom: 10px;
}

@media (max-width: 768px) {
  .interval-inputs {
    flex-wrap: wrap;
  }
}
</style> 