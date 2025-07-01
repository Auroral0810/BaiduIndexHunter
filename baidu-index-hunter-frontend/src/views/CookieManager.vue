<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:5001/api'

// Cookie池状态
const cookiePoolStatus = ref({
  total: 0,
  available: 0,
  blocked: 0,
  cooldown_status: {}
})

// Cookie列表
const cookies = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const currentCookie = ref(null)

// 分页
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 搜索和筛选
const searchKeyword = ref('')
const statusFilter = ref('')

// 新增/编辑Cookie表单
const cookieForm = reactive({
  id: null,
  account_id: '',
  cookie_name: '',
  cookie_value: '',
  is_available: true,
  is_permanently_banned: false,
  temp_ban_until: null
})

// 加载Cookie池状态
const loadCookiePoolStatus = async () => {
  loading.value = true
  try {
    const response = await axios.get(`${API_BASE_URL}/cookie/status`)
    
    if (response.data.code === 0) {
      cookiePoolStatus.value = response.data.data
    } else {
      ElMessage.error(`获取Cookie池状态失败: ${response.data.message}`)
    }
  } catch (error) {
    ElMessage.error('获取Cookie池状态失败，请检查网络连接')
    console.error('加载Cookie池状态错误:', error)
  } finally {
    loading.value = false
  }
}

// 加载Cookie列表
const loadCookies = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      limit: pageSize.value,
      keyword: searchKeyword.value || undefined,
      status: statusFilter.value || undefined
    }
    
    const response = await axios.get(`${API_BASE_URL}/cookie/list`, { params })
    
    if (response.data.code === 0) {
      cookies.value = response.data.data.cookies || []
      total.value = response.data.data.total || 0
    } else {
      ElMessage.error(`获取Cookie列表失败: ${response.data.message}`)
    }
  } catch (error) {
    ElMessage.error('获取Cookie列表失败，请检查网络连接')
    console.error('加载Cookie列表错误:', error)
  } finally {
    loading.value = false
  }
}

// 解锁所有Cookie
const unlockAllCookies = async () => {
  try {
    await ElMessageBox.confirm('确定要解锁所有Cookie吗？这可能影响爬取效率。', '确认', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    loading.value = true
    
    const response = await axios.post(`${API_BASE_URL}/cookie/unlock_all`)
    
    if (response.data.code === 0) {
      ElMessage.success('所有Cookie已解锁')
      await loadCookiePoolStatus()
      await loadCookies()
    } else {
      ElMessage.error(`解锁Cookie失败: ${response.data.message}`)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('解锁Cookie失败')
      console.error('解锁Cookie错误:', error)
    }
  } finally {
    loading.value = false
  }
}

// 解锁单个Cookie
const unlockCookie = async (cookieId) => {
  try {
    loading.value = true
    
    const response = await axios.post(`${API_BASE_URL}/cookie/${cookieId}/unlock`)
    
    if (response.data.code === 0) {
      ElMessage.success('Cookie已解锁')
      await loadCookiePoolStatus()
      await loadCookies()
    } else {
      ElMessage.error(`解锁Cookie失败: ${response.data.message}`)
    }
  } catch (error) {
    ElMessage.error('解锁Cookie失败')
    console.error('解锁Cookie错误:', error)
  } finally {
    loading.value = false
  }
}

// 删除Cookie
const deleteCookie = async (cookieId) => {
  try {
    await ElMessageBox.confirm('确定要删除此Cookie吗？此操作不可恢复。', '确认', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'danger'
    })
    
    loading.value = true
    
    const response = await axios.delete(`${API_BASE_URL}/cookie/${cookieId}`)
    
    if (response.data.code === 0) {
      ElMessage.success('Cookie已删除')
      await loadCookiePoolStatus()
      await loadCookies()
    } else {
      ElMessage.error(`删除Cookie失败: ${response.data.message}`)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除Cookie失败')
      console.error('删除Cookie错误:', error)
    }
  } finally {
    loading.value = false
  }
}

// 打开新增Cookie对话框
const openAddDialog = () => {
  // 重置表单
  Object.assign(cookieForm, {
    id: null,
    account_id: '',
    cookie_name: '',
    cookie_value: '',
    is_available: true,
    is_permanently_banned: false,
    temp_ban_until: null
  })
  
  dialogVisible.value = true
}

// 打开编辑Cookie对话框
const openEditDialog = (cookie) => {
  // 填充表单
  Object.assign(cookieForm, {
    id: cookie.id,
    account_id: cookie.account_id,
    cookie_name: cookie.cookie_name,
    cookie_value: cookie.cookie_value,
    is_available: cookie.is_available === 1,
    is_permanently_banned: cookie.is_permanently_banned === 1,
    temp_ban_until: cookie.temp_ban_until
  })
  
  dialogVisible.value = true
}

// 保存Cookie
const saveCookie = async () => {
  try {
    loading.value = true
    
    const cookieData = {
      account_id: cookieForm.account_id,
      cookie_name: cookieForm.cookie_name,
      cookie_value: cookieForm.cookie_value,
      is_available: cookieForm.is_available ? 1 : 0,
      is_permanently_banned: cookieForm.is_permanently_banned ? 1 : 0,
      temp_ban_until: cookieForm.temp_ban_until
    }
    
    let response
    
    if (cookieForm.id) {
      // 更新Cookie
      response = await axios.put(`${API_BASE_URL}/cookie/${cookieForm.id}`, cookieData)
    } else {
      // 新增Cookie
      response = await axios.post(`${API_BASE_URL}/cookie`, cookieData)
    }
    
    if (response.data.code === 0) {
      ElMessage.success(cookieForm.id ? 'Cookie已更新' : 'Cookie已添加')
      dialogVisible.value = false
      await loadCookiePoolStatus()
      await loadCookies()
    } else {
      ElMessage.error(`保存Cookie失败: ${response.data.message}`)
    }
  } catch (error) {
    ElMessage.error('保存Cookie失败')
    console.error('保存Cookie错误:', error)
  } finally {
    loading.value = false
  }
}

// 处理分页变化
const handleSizeChange = (size) => {
  pageSize.value = size
  loadCookies()
}

const handleCurrentChange = (page) => {
  currentPage.value = page
  loadCookies()
}

// 重置筛选条件
const resetFilters = () => {
  searchKeyword.value = ''
  statusFilter.value = ''
  currentPage.value = 1
  loadCookies()
}

// 格式化状态
const formatStatus = (cookie) => {
  if (cookie.is_permanently_banned === 1) return '永久封禁'
  if (cookie.temp_ban_until) return '临时封禁'
  if (cookie.is_available === 1) return '可用'
  return '不可用'
}

// 获取状态标签类型
const getStatusTagType = (cookie) => {
  if (cookie.is_permanently_banned === 1) return 'danger'
  if (cookie.temp_ban_until) return 'warning'
  if (cookie.is_available === 1) return 'success'
  return 'info'
}

// 生命周期钩子
onMounted(() => {
  loadCookiePoolStatus()
  loadCookies()
})
</script>

<template>
  <div class="cookie-manager-container">
    <h1 class="page-title">Cookie 管理</h1>
    
    <el-row :gutter="20">
      <el-col :span="8">
        <!-- Cookie池状态 -->
        <el-card class="cookie-status-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <h2>Cookie池状态</h2>
              <el-button @click="loadCookiePoolStatus" :loading="loading" plain>
                刷新
              </el-button>
            </div>
          </template>
          
          <div v-loading="loading">
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
              <el-button type="primary" @click="openAddDialog">
                <el-icon><Plus /></el-icon>添加Cookie
              </el-button>
              <el-button type="warning" @click="unlockAllCookies" :loading="loading">
                <el-icon><Unlock /></el-icon>解锁所有Cookie
              </el-button>
            </div>
            
            <div v-if="Object.keys(cookiePoolStatus.cooldown_status || {}).length > 0" class="blocked-cookies-list">
              <h3>被锁定的Cookie</h3>
              <el-table :data="Object.entries(cookiePoolStatus.cooldown_status || {}).map(([id, status]) => ({ id, ...status }))">
                <el-table-column prop="id" label="Cookie ID"></el-table-column>
                <el-table-column prop="remaining_minutes" label="剩余冷却时间">
                  <template #default="scope">
                    {{ scope.row.remaining_minutes }} 分钟
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="100">
                  <template #default="scope">
                    <el-button 
                      type="primary"
                      size="small"
                      @click="unlockCookie(scope.row.id)" 
                      plain
                    >
                      解锁
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="16">
        <!-- Cookie列表 -->
        <el-card class="cookie-list-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <h2>Cookie列表</h2>
            </div>
          </template>
          
          <div class="search-bar">
            <el-input
              v-model="searchKeyword"
              placeholder="搜索账号ID"
              clearable
              style="width: 200px; margin-right: 10px"
            />
            <el-select
              v-model="statusFilter"
              placeholder="状态"
              clearable
              style="width: 150px; margin-right: 10px"
            >
              <el-option label="可用" value="available" />
              <el-option label="不可用" value="unavailable" />
              <el-option label="临时封禁" value="temp_banned" />
              <el-option label="永久封禁" value="perm_banned" />
            </el-select>
            <el-button type="primary" @click="loadCookies">搜索</el-button>
            <el-button @click="resetFilters">重置</el-button>
          </div>
          
          <el-table
            v-loading="loading"
            :data="cookies"
            style="width: 100%"
            border
            stripe
          >
            <el-table-column prop="id" label="ID" width="80" />
            <el-table-column prop="account_id" label="账号ID" width="150" />
            <el-table-column prop="cookie_name" label="Cookie名称" width="150" />
            <el-table-column label="Cookie值" show-overflow-tooltip>
              <template #default="scope">
                <el-tooltip 
                  :content="scope.row.cookie_value" 
                  placement="top" 
                  :hide-after="0"
                >
                  <span>{{ scope.row.cookie_value.substring(0, 30) }}...</span>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="scope">
                <el-tag :type="getStatusTagType(scope.row)">
                  {{ formatStatus(scope.row) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="last_updated" label="更新时间" width="180" />
            <el-table-column label="操作" width="200">
              <template #default="scope">
                <el-button 
                  type="primary"
                  size="small"
                  @click="openEditDialog(scope.row)" 
                  plain
                >
                  编辑
                </el-button>
                <el-button 
                  type="danger"
                  size="small"
                  @click="deleteCookie(scope.row.id)" 
                  plain
                >
                  删除
                </el-button>
                <el-button 
                  v-if="scope.row.temp_ban_until"
                  type="warning"
                  size="small"
                  @click="unlockCookie(scope.row.id)" 
                  plain
                >
                  解锁
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <div class="pagination">
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
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 新增/编辑Cookie对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="cookieForm.id ? '编辑Cookie' : '新增Cookie'"
      width="600px"
      destroy-on-close
    >
      <el-form :model="cookieForm" label-position="top">
        <el-form-item label="账号ID">
          <el-input v-model="cookieForm.account_id" placeholder="请输入账号ID"></el-input>
        </el-form-item>
        
        <el-form-item label="Cookie名称">
          <el-input v-model="cookieForm.cookie_name" placeholder="请输入Cookie名称"></el-input>
        </el-form-item>
        
        <el-form-item label="Cookie值">
          <el-input 
            v-model="cookieForm.cookie_value" 
            type="textarea" 
            :rows="4"
            placeholder="请输入Cookie值"
          ></el-input>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-switch
            v-model="cookieForm.is_available"
            active-text="可用"
            inactive-text="不可用"
            :disabled="cookieForm.is_permanently_banned || cookieForm.temp_ban_until"
          />
        </el-form-item>
        
        <el-form-item label="永久封禁">
          <el-switch
            v-model="cookieForm.is_permanently_banned"
            active-text="是"
            inactive-text="否"
          />
        </el-form-item>
        
        <el-form-item label="临时封禁到期时间" v-if="!cookieForm.is_permanently_banned">
          <el-date-picker
            v-model="cookieForm.temp_ban_until"
            type="datetime"
            placeholder="选择日期时间"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveCookie" :loading="loading">
            保存
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.cookie-manager-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 30px;
}

.page-title {
  font-size: 2rem;
  margin-bottom: 24px;
  color: #303133;
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

.cookie-status-card, .cookie-list-card {
  margin-bottom: 20px;
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
  justify-content: space-around;
  margin: 20px 0;
}

.blocked-cookies-list {
  margin-top: 20px;
}

.blocked-cookies-list h3 {
  font-size: 1rem;
  margin-bottom: 10px;
}

.search-bar {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>