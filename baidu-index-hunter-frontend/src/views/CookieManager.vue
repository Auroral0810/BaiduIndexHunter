<script setup lang="ts">
// @ts-nocheck
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { 
  Refresh, Plus, Delete, Connection, Search, CopyDocument,
  RefreshRight, ArrowDown, Check
} from '@element-plus/icons-vue'
import axios from 'axios'
import { useClipboard } from '@vueuse/core'

const { copy, isSupported } = useClipboard()

const API_BASE_URL = 'http://127.0.0.1:5001/api'

// API连接状态
const apiConnected = ref(false)

// 加载状态
const statusLoading = ref(false)
const accountsLoading = ref(false)
const bannedLoading = ref(false)
const listLoading = ref(false)
const submitting = ref(false)
const syncing = ref(false)
const testingAccount = ref(false)
const testingAll = ref(false)
const updatingStatus = ref(false)
const cleaningUp = ref(false)
const accountDetailLoading = ref(false)
const loading = ref(false)

// Cookie池统计
const cookieStats = reactive({
  total: 0,
  available: 0,
  tempBanned: 0,
  permBanned: 0
})

// 账号列表
const availableAccounts = ref<string[]>([])
const tempBannedAccounts = ref<any[]>([])
const permBannedAccounts = ref<any[]>([])
const bannedTabActive = ref('temp')

// Cookie列表
const cookieList = ref<any[]>([])
const cookies = ref([])
const currentCookie = ref(null)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)

// 搜索和筛选
const searchAccount = ref('')
const searchKeyword = ref('')
const statusFilter = ref('')

// 对话框可见性
const cookieDialogVisible = ref(false)
const tempBanDialogVisible = ref(false)
const updateIdDialogVisible = ref(false)
const accountDetailDialogVisible = ref(false)
const testResultDialogVisible = ref(false)
const batchTestResultDialogVisible = ref(false)
const dialogVisible = ref(false)

// 表单数据
const cookieFormRef = ref(null)
const cookieForm = reactive({
  id: null as number | null,
  account_id: '',
  cookie_name: '',
  cookie_value: '',
  cookie_string: '',
  use_string_input: false,
  expire_days: 365,
  is_available: true,
  is_permanently_banned: false,
  temp_ban_until: null as string | null
})

const tempBanForm = reactive({
  account_id: '',
  duration_minutes: 30
})

const updateIdFormRef = ref(null)
const updateIdForm = reactive({
  old_account_id: '',
  new_account_id: ''
})

// 账号详情
const accountDetail = ref(null as any)
const accountDetailCookies = computed(() => {
  if (!accountDetail.value || !accountDetail.value.cookies) return []
  return Object.entries(accountDetail.value.cookies).map(([name, value]) => ({
    name,
    value
  }))
})
const accountDetailCookieString = computed(() => {
  if (!accountDetail.value || !accountDetail.value.cookies) return ''
  return Object.entries(accountDetail.value.cookies)
    .map(([name, value]) => `${name}=${value}`)
    .join('; ')
})

// 测试结果
const testResult = ref(null as any)
const batchTestResult = ref(null as any)

// 表单验证规则
const cookieRules = {
  account_id: [
    { required: true, message: '请输入账号ID', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  cookie_name: [
    { required: true, message: '请输入Cookie名称', trigger: 'blur' }
  ],
  cookie_value: [
    { required: true, message: '请输入Cookie值', trigger: 'blur' }
  ],
  cookie_string: [
    { required: true, message: '请输入Cookie字符串', trigger: 'blur' }
  ]
}

const updateIdRules = {
  new_account_id: [
    { required: true, message: '请输入新账号ID', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ]
}

// Cookie池状态
const cookiePoolStatus = ref({
  total: 0,
  available: 0,
  blocked: 0,
  cooldown_status: {}
})

// 加载Cookie池状态
const refreshCookieStatus = async () => {
  statusLoading.value = true
  try {
    await checkApiConnection()
    
    const response = await axios.get(`${API_BASE_URL}/admin/cookie/pool-status`)
    if (response.data.code === 10000) {
      const data = response.data.data
      cookieStats.total = data.total || 0
      cookieStats.available = data.available || 0
      cookieStats.tempBanned = data.temp_banned || 0
      cookieStats.permBanned = data.perm_banned || 0
      
      // 添加日志以便调试
      console.log('Cookie池状态:', data)
    } else {
      ElMessage.error(`获取Cookie池状态失败: ${response.data.msg}`)
    }
  } catch (error) {
    console.error('获取Cookie池状态失败:', error)
    ElMessage.error('获取Cookie池状态失败，请检查网络连接')
  } finally {
    statusLoading.value = false
  }
}

// 检查API连接状态
const checkApiConnection = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/health`, { timeout: 3000 })
    apiConnected.value = response.status === 200
    return apiConnected.value
  } catch (error) {
    apiConnected.value = false
    return false
  }
}

// 加载可用账号列表
const loadAvailableAccounts = async () => {
  accountsLoading.value = true
  try {
    const response = await axios.get(`${API_BASE_URL}/admin/cookie/available-accounts`)
    if (response.data.code === 10000) {
      availableAccounts.value = response.data.data.account_ids || []
      console.log('可用账号列表:', availableAccounts.value)
    } else {
      ElMessage.error(`获取可用账号列表失败: ${response.data.msg}`)
    }
  } catch (error) {
    console.error('获取可用账号列表失败:', error)
    ElMessage.error('获取可用账号列表失败，请检查网络连接')
  } finally {
    accountsLoading.value = false
  }
}

// 加载被封禁的账号
const loadBannedAccounts = async () => {
  bannedLoading.value = true
  try {
    const response = await axios.get(`${API_BASE_URL}/admin/cookie/banned-accounts`)
    if (response.data.code === 10000) {
      tempBannedAccounts.value = response.data.data.temp_banned || []
      permBannedAccounts.value = response.data.data.perm_banned || []
      console.log('临时封禁账号:', tempBannedAccounts.value)
      console.log('永久封禁账号:', permBannedAccounts.value)
    } else {
      ElMessage.error(`获取被封禁账号列表失败: ${response.data.msg}`)
    }
  } catch (error) {
    console.error('获取被封禁账号列表失败:', error)
    ElMessage.error('获取被封禁账号列表失败，请检查网络连接')
  } finally {
    bannedLoading.value = false
  }
}

// 加载Cookie列表
const loadCookies = async () => {
  listLoading.value = true
  try {
    const params = {
      page: currentPage.value,
      limit: pageSize.value,
      account_id: searchAccount.value || undefined,
      available_only: statusFilter.value === 'available' ? true : undefined
    }
    
    const response = await axios.get(`${API_BASE_URL}/admin/cookie/list`, { params })
    if (response.data.code === 10000) {
      cookieList.value = response.data.data || []
      console.log('Cookie列表:', cookieList.value)
      
      // 如果后端返回了总数，使用后端的总数
      if (response.data.total) {
        total.value = response.data.total
      } else {
        total.value = cookieList.value.length
      }
    } else {
      ElMessage.error(`获取Cookie列表失败: ${response.data.msg}`)
    }
  } catch (error) {
    console.error('获取Cookie列表失败:', error)
    ElMessage.error('获取Cookie列表失败，请检查网络连接')
  } finally {
    listLoading.value = false
  }
}

// 处理筛选
const handleFilter = () => {
  currentPage.value = 1
  loadCookies()
}

// 重置筛选
const resetFilter = () => {
  searchAccount.value = ''
  statusFilter.value = ''
  currentPage.value = 1
  loadCookies()
}

// 处理分页
const handleSizeChange = (size: number) => {
  pageSize.value = size
  loadCookies()
}

const handleCurrentChange = (page: number) => {
  currentPage.value = page
  loadCookies()
}

// 打开添加Cookie对话框
const openAddCookieDialog = () => {
  // 重置表单
  Object.assign(cookieForm, {
    id: null,
    account_id: '',
    cookie_name: '',
    cookie_value: '',
    cookie_string: '',
    use_string_input: false,
    expire_days: 365,
    is_available: true,
    is_permanently_banned: false,
    temp_ban_until: null
  })
  
  cookieDialogVisible.value = true
}

// 编辑Cookie
const editCookie = (cookie: any) => {
  Object.assign(cookieForm, {
    id: cookie.id,
    account_id: cookie.account_id,
    cookie_name: cookie.cookie_name,
    cookie_value: cookie.cookie_value,
    cookie_string: '',
    use_string_input: false,
    expire_days: cookie.expire_time ? 365 : null,
    is_available: cookie.is_available === 1,
    is_permanently_banned: cookie.is_permanently_banned === 1,
    temp_ban_until: cookie.temp_ban_until
  })
  
  cookieDialogVisible.value = true
}

// 提交Cookie表单
const submitCookieForm = async () => {
  if (!cookieFormRef.value) return
  
  try {
    await (cookieFormRef.value as any).validate()
    
    submitting.value = true
    
    let response
    const cookieData: any = {
      account_id: cookieForm.account_id
    }
    
    if (cookieForm.use_string_input) {
      // 如果使用字符串输入，直接将字符串作为cookie_data
      cookieData.cookie_data = cookieForm.cookie_string
    } else {
      // 如果使用键值对输入，将cookie_name和cookie_value封装到cookie_data对象中
      cookieData.cookie_data = {}
      cookieData.cookie_data[cookieForm.cookie_name] = cookieForm.cookie_value
    }
    
    if (cookieForm.expire_days) {
      cookieData.expire_days = cookieForm.expire_days
    }
    
    console.log('提交的Cookie数据:', cookieData)
    
    if (cookieForm.id) {
      // 更新Cookie
      cookieData.is_available = cookieForm.is_available ? 1 : 0
      cookieData.is_permanently_banned = cookieForm.is_permanently_banned ? 1 : 0
      cookieData.temp_ban_until = cookieForm.temp_ban_until
      
      response = await axios.put(`${API_BASE_URL}/admin/cookie/update/${cookieForm.id}`, cookieData)
    } else {
      // 添加Cookie
      response = await axios.post(`${API_BASE_URL}/admin/cookie/add`, cookieData)
    }
    
    if (response.data.code === 10000) {
      ElMessage.success(cookieForm.id ? 'Cookie更新成功' : 'Cookie添加成功')
      cookieDialogVisible.value = false
      refreshCookieStatus()
      loadCookies()
      loadAvailableAccounts()
      loadBannedAccounts()
    } else {
      ElMessage.error(`${cookieForm.id ? '更新' : '添加'}Cookie失败: ${response.data.msg}`)
    }
  } catch (error: any) {
    if (error.message) {
      ElMessage.error(error.message)
    } else {
      console.error('提交Cookie表单失败:', error)
      ElMessage.error(`${cookieForm.id ? '更新' : '添加'}Cookie失败，请检查网络连接`)
    }
  } finally {
    submitting.value = false
  }
}

// 删除Cookie
const deleteCookie = async (id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除此Cookie吗？此操作不可恢复。', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    listLoading.value = true
    
    const response = await axios.delete(`${API_BASE_URL}/admin/cookie/delete/${id}`)
    if (response.data.code === 10000) {
      ElMessage.success('Cookie删除成功')
      loadCookies()
      refreshCookieStatus()
    } else {
      ElMessage.error(`删除Cookie失败: ${response.data.msg}`)
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除Cookie失败:', error)
      ElMessage.error('删除Cookie失败，请检查网络连接')
    }
  } finally {
    listLoading.value = false
  }
}

// 生命周期钩子
onMounted(() => {
  refreshCookieStatus()
  loadCookies()
})

// 解封Cookie
const unbanCookie = async (id: number) => {
  try {
    listLoading.value = true
    
    const response = await axios.post(`${API_BASE_URL}/admin/cookie/unban/${id}`)
    if (response.data.code === 10000) {
      ElMessage.success('Cookie解封成功')
      loadCookies()
      refreshCookieStatus()
    } else {
      ElMessage.error(`解封Cookie失败: ${response.data.msg}`)
    }
  } catch (error) {
    console.error('解封Cookie失败:', error)
    ElMessage.error('解封Cookie失败，请检查网络连接')
  } finally {
    listLoading.value = false
  }
}

// 同步到Redis
const syncToRedis = async () => {
  try {
    syncing.value = true
    
    const response = await axios.post(`${API_BASE_URL}/admin/cookie/sync-to-redis`)
    if (response.data.code === 10000) {
      ElMessage.success('Cookie数据同步到Redis成功')
      refreshCookieStatus()
    } else {
      ElMessage.error(`同步到Redis失败: ${response.data.msg}`)
    }
  } catch (error) {
    console.error('同步到Redis失败:', error)
    ElMessage.error('同步到Redis失败，请检查网络连接')
  } finally {
    syncing.value = false
  }
}

// 测试单个账号可用性
const testAccountAvailability = async (accountId: string) => {
  try {
    testingAccount.value = true
    testResult.value = null
    testResultDialogVisible.value = true
    
    const response = await axios.post(`${API_BASE_URL}/admin/cookie/test-account-availability/${accountId}`)
    if (response.data.code === 10000) {
      testResult.value = response.data.data
    } else {
      ElMessage.error(`测试账号可用性失败: ${response.data.msg}`)
      testResultDialogVisible.value = false
    }
  } catch (error) {
    console.error('测试账号可用性失败:', error)
    ElMessage.error('测试账号可用性失败，请检查网络连接')
    testResultDialogVisible.value = false
  } finally {
    testingAccount.value = false
  }
}

// 测试所有Cookie可用性
const testAllCookiesAvailability = async () => {
  try {
    testingAll.value = true
    batchTestResult.value = null
    batchTestResultDialogVisible.value = true
    
    const response = await axios.post(`${API_BASE_URL}/admin/cookie/test-availability`)
    if (response.data.code === 10000) {
      batchTestResult.value = response.data.data
    } else {
      ElMessage.error(`测试Cookie可用性失败: ${response.data.msg}`)
      batchTestResultDialogVisible.value = false
    }
  } catch (error) {
    console.error('测试Cookie可用性失败:', error)
    ElMessage.error('测试Cookie可用性失败，请检查网络连接')
    batchTestResultDialogVisible.value = false
  } finally {
    testingAll.value = false
  }
}

// 更新Cookie状态
const updateCookieStatus = async () => {
  try {
    updatingStatus.value = true
    
    const response = await axios.post(`${API_BASE_URL}/admin/cookie/update-status`)
    if (response.data.code === 10000) {
      ElMessage.success(`成功更新${response.data.data.updated_count}条Cookie状态`)
      refreshCookieStatus()
      loadCookies()
    } else {
      ElMessage.error(`更新Cookie状态失败: ${response.data.msg}`)
    }
  } catch (error) {
    console.error('更新Cookie状态失败:', error)
    ElMessage.error('更新Cookie状态失败，请检查网络连接')
  } finally {
    updatingStatus.value = false
  }
}

// 清理过期Cookie
const cleanupExpiredCookies = async () => {
  try {
    await ElMessageBox.confirm('确定要清理所有过期的Cookie吗？此操作不可恢复。', '确认清理', {
      confirmButtonText: '清理',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    cleaningUp.value = true
    
    const response = await axios.post(`${API_BASE_URL}/admin/cookie/cleanup-expired`)
    if (response.data.code === 10000) {
      ElMessage.success(`成功清理${response.data.data.deleted_count}条过期Cookie`)
      refreshCookieStatus()
      loadCookies()
    } else {
      ElMessage.error(`清理过期Cookie失败: ${response.data.msg}`)
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('清理过期Cookie失败:', error)
      ElMessage.error('清理过期Cookie失败，请检查网络连接')
    }
  } finally {
    cleaningUp.value = false
  }
}

// 处理账号操作
const handleAccountCommand = (command: string, accountId: string) => {
  switch (command) {
    case 'view':
      viewAccountDetail(accountId)
      break
    case 'temp_ban':
      openTempBanDialog(accountId)
      break
    case 'perm_ban':
      banAccountPermanently(accountId)
      break
    case 'unban':
      unbanAccount(accountId)
      break
    case 'force_unban':
      forceUnbanAccount(accountId)
      break
    case 'update':
      openUpdateIdDialog(accountId)
      break
    case 'delete':
      deleteAccount(accountId)
      break
  }
}

// 查看账号详情
const viewAccountDetail = async (accountId: string) => {
  accountDetailLoading.value = true
  accountDetail.value = null
  accountDetailDialogVisible.value = true
  
  try {
    const response = await axios.get(`${API_BASE_URL}/admin/cookie/account-cookie/${accountId}`)
    if (response.data.code === 10000) {
      accountDetail.value = response.data.data
    } else {
      ElMessage.error(`获取账号详情失败: ${response.data.msg}`)
      accountDetailDialogVisible.value = false
    }
  } catch (error) {
    console.error('获取账号详情失败:', error)
    ElMessage.error('获取账号详情失败，请检查网络连接')
    accountDetailDialogVisible.value = false
  } finally {
    accountDetailLoading.value = false
  }
}

// 复制Cookie字符串
const copyCookieString = async () => {
  if (!isSupported) {
    ElMessage.error('您的浏览器不支持复制功能')
    return
  }
  
  try {
    await copy(accountDetailCookieString.value)
    ElMessage.success('Cookie字符串已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败')
  }
}

// 打开临时封禁对话框
const openTempBanDialog = (accountId: string) => {
  tempBanForm.account_id = accountId
  tempBanForm.duration_minutes = 30
  tempBanDialogVisible.value = true
}

// 提交临时封禁
const submitTempBan = async () => {
  try {
    submitting.value = true
    
    const durationSeconds = tempBanForm.duration_minutes * 60
    const response = await axios.post(`${API_BASE_URL}/admin/cookie/ban/temporary/${tempBanForm.account_id}`, {
      duration_seconds: durationSeconds
    })
    
    if (response.data.code === 10000) {
      ElMessage.success(`账号 ${tempBanForm.account_id} 已临时封禁 ${tempBanForm.duration_minutes} 分钟`)
      tempBanDialogVisible.value = false
      refreshCookieStatus()
      loadCookies()
      loadAvailableAccounts()
      loadBannedAccounts()
    } else {
      ElMessage.error(`临时封禁账号失败: ${response.data.msg}`)
    }
  } catch (error) {
    console.error('临时封禁账号失败:', error)
    ElMessage.error('临时封禁账号失败，请检查网络连接')
  } finally {
    submitting.value = false
  }
}

// 永久封禁账号
const banAccountPermanently = async (accountId: string) => {
  try {
    await ElMessageBox.confirm(`确定要永久封禁账号 ${accountId} 吗？此操作可以通过强制解封恢复。`, '确认永久封禁', {
      confirmButtonText: '封禁',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    accountsLoading.value = true
    
    const response = await axios.post(`${API_BASE_URL}/admin/cookie/ban/permanent/${accountId}`)
    if (response.data.code === 10000) {
      ElMessage.success(`账号 ${accountId} 已永久封禁`)
      refreshCookieStatus()
      loadCookies()
      loadAvailableAccounts()
      loadBannedAccounts()
    } else {
      ElMessage.error(`永久封禁账号失败: ${response.data.msg}`)
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('永久封禁账号失败:', error)
      ElMessage.error('永久封禁账号失败，请检查网络连接')
    }
  } finally {
    accountsLoading.value = false
  }
}

// 解封账号
const unbanAccount = async (accountId: string) => {
  try {
    bannedLoading.value = true
    
    const response = await axios.post(`${API_BASE_URL}/admin/cookie/unban/${accountId}`)
    if (response.data.code === 10000) {
      ElMessage.success(`账号 ${accountId} 已解封`)
      refreshCookieStatus()
      loadCookies()
      loadAvailableAccounts()
      loadBannedAccounts()
    } else {
      ElMessage.error(`解封账号失败: ${response.data.msg}`)
    }
  } catch (error) {
    console.error('解封账号失败:', error)
    ElMessage.error('解封账号失败，请检查网络连接')
  } finally {
    bannedLoading.value = false
  }
}

// 强制解封账号
const forceUnbanAccount = async (accountId: string) => {
  try {
    await ElMessageBox.confirm(`确定要强制解封账号 ${accountId} 吗？这将解除所有封禁。`, '确认强制解封', {
      confirmButtonText: '强制解封',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    bannedLoading.value = true
    
    const response = await axios.post(`${API_BASE_URL}/admin/cookie/force-unban/${accountId}`)
    if (response.data.code === 10000) {
      ElMessage.success(`账号 ${accountId} 已强制解封`)
      refreshCookieStatus()
      loadCookies()
      loadAvailableAccounts()
      loadBannedAccounts()
    } else {
      ElMessage.error(`强制解封账号失败: ${response.data.msg}`)
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('强制解封账号失败:', error)
      ElMessage.error('强制解封账号失败，请检查网络连接')
    }
  } finally {
    bannedLoading.value = false
  }
}

// 打开更新账号ID对话框
const openUpdateIdDialog = (accountId: string) => {
  updateIdForm.old_account_id = accountId
  updateIdForm.new_account_id = ''
  updateIdDialogVisible.value = true
}

// 提交更新账号ID
const submitUpdateId = async () => {
  if (!updateIdFormRef.value) return
  
  try {
    await (updateIdFormRef.value as any).validate()
    
    submitting.value = true
    
    const response = await axios.put(`${API_BASE_URL}/admin/cookie/update-account/${updateIdForm.old_account_id}`, {
      new_account_id: updateIdForm.new_account_id
    })
    
    if (response.data.code === 10000) {
      ElMessage.success(`账号ID已从 ${updateIdForm.old_account_id} 更新为 ${updateIdForm.new_account_id}`)
      updateIdDialogVisible.value = false
      refreshCookieStatus()
      loadCookies()
      loadAvailableAccounts()
      loadBannedAccounts()
    } else {
      ElMessage.error(`更新账号ID失败: ${response.data.msg}`)
    }
  } catch (error: any) {
    if (error.message) {
      ElMessage.error(error.message)
    } else {
      console.error('更新账号ID失败:', error)
      ElMessage.error('更新账号ID失败，请检查网络连接')
    }
  } finally {
    submitting.value = false
  }
}

// 删除账号
const deleteAccount = async (accountId: string) => {
  try {
    await ElMessageBox.confirm(`确定要删除账号 ${accountId} 的所有Cookie吗？此操作不可恢复。`, '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    accountsLoading.value = true
    
    const response = await axios.delete(`${API_BASE_URL}/admin/cookie/delete/${accountId}`)
    if (response.data.code === 10000) {
      ElMessage.success(`账号 ${accountId} 的所有Cookie已删除`)
      refreshCookieStatus()
      loadCookies()
      loadAvailableAccounts()
      loadBannedAccounts()
    } else {
      ElMessage.error(`删除账号失败: ${response.data.msg}`)
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error('删除账号失败:', error)
      ElMessage.error('删除账号失败，请检查网络连接')
    }
  } finally {
    accountsLoading.value = false
  }
}

// 辅助函数
// 格式化Cookie状态文本
const getCookieStatusText = (cookie: any) => {
  if (cookie.is_permanently_banned === 1) return '永久封禁'
  if (cookie.temp_ban_until) return '临时封禁'
  if (cookie.is_available === 1) return '可用'
  if (cookie.expire_time && new Date(cookie.expire_time) < new Date()) return '已过期'
  return '不可用'
}

// 获取Cookie状态样式
const getCookieStatusType = (cookie: any) => {
  if (cookie.is_permanently_banned === 1) return 'danger'
  if (cookie.temp_ban_until) return 'warning'
  if (cookie.is_available === 1) return 'success'
  if (cookie.expire_time && new Date(cookie.expire_time) < new Date()) return 'info'
  return 'danger'
}

// 截断文本
const truncateText = (text: string, length: number) => {
  if (!text) return ''
  return text.length > length ? text.substring(0, length) + '...' : text
}

// 格式化日期时间
const formatDateTime = (dateTime: string) => {
  if (!dateTime) return ''
  return new Date(dateTime).toLocaleString()
}

// 格式化封禁剩余时间
const formatBanTimeRemaining = (endTime: string) => {
  if (!endTime) return ''
  
  const now = new Date()
  const end = new Date(endTime)
  const diffMs = end.getTime() - now.getTime()
  
  if (diffMs <= 0) return '已解封'
  
  const diffMin = Math.floor(diffMs / 60000)
  if (diffMin < 60) return `${diffMin}分钟`
  
  const hours = Math.floor(diffMin / 60)
  const minutes = diffMin % 60
  return `${hours}小时${minutes > 0 ? ` ${minutes}分钟` : ''}`
}

// 初始化
onMounted(() => {
  checkApiConnection()
  refreshCookieStatus()
  loadAvailableAccounts()
  loadBannedAccounts()
  loadCookies()
})
</script>

<template>
  <div class="cookie-manager-container">
    <div class="page-header">
      <h1>Cookie 管理系统</h1>
      <div class="api-status">
        <el-tag :type="apiConnected ? 'success' : 'danger'" effect="dark">
          {{ apiConnected ? 'API 已连接' : 'API 未连接' }}
        </el-tag>
      </div>
    </div>
    
    <el-row :gutter="20">
      <!-- 左侧面板 -->
      <el-col :span="8">
        <!-- Cookie池状态卡片 -->
        <el-card class="status-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>Cookie池状态</span>
              <div>
                <el-button type="primary" size="small" @click="refreshCookieStatus" :loading="statusLoading">
                  <el-icon><Refresh /></el-icon> 刷新
                </el-button>
                <el-button type="success" size="small" @click="openAddCookieDialog">
                  <el-icon><Plus /></el-icon> 添加
                </el-button>
              </div>
            </div>
          </template>
          
          <div v-loading="statusLoading" class="status-overview">
            <div class="status-item">
              <div class="status-value">{{ cookieStats.total }}</div>
              <div class="status-label">总数</div>
            </div>
            <div class="status-item success">
              <div class="status-value">{{ cookieStats.available }}</div>
              <div class="status-label">可用</div>
            </div>
            <div class="status-item warning">
              <div class="status-value">{{ cookieStats.tempBanned }}</div>
              <div class="status-label">临时封禁</div>
            </div>
            <div class="status-item danger">
              <div class="status-value">{{ cookieStats.permBanned }}</div>
              <div class="status-label">永久封禁</div>
            </div>
          </div>
          
          <el-divider />
          
          <div class="action-buttons">
            <el-button type="primary" @click="testAllCookiesAvailability" :loading="testingAll">
              <el-icon><Check /></el-icon> 测试全部可用性
            </el-button>
            <el-button type="warning" @click="updateCookieStatus" :loading="updatingStatus">
              <el-icon><RefreshRight /></el-icon> 更新Cookie状态
            </el-button>
            <el-button type="danger" @click="cleanupExpiredCookies" :loading="cleaningUp">
              <el-icon><Delete /></el-icon> 清理过期Cookie
            </el-button>
          </div>
          
          <!-- 账号列表 -->
          <div class="account-list-section">
            <div class="section-header">
              <h3>可用账号列表</h3>
              <el-button size="small" text @click="loadAvailableAccounts">刷新</el-button>
            </div>
            <div v-loading="accountsLoading" class="account-list">
              <template v-if="availableAccounts.length > 0">
                <div v-for="account in availableAccounts" :key="account" class="account-item">
                  <div class="account-info">
                    <el-tag size="small" effect="plain">{{ account }}</el-tag>
                  </div>
                  <div class="account-actions">
                    <el-button size="small" type="primary" @click="testAccountAvailability(account)" plain>测试</el-button>
                    <el-dropdown trigger="click" @command="handleAccountCommand($event, account)">
                      <el-button size="small" plain>
                        操作<el-icon class="el-icon--right"><ArrowDown /></el-icon>
                      </el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item command="view">查看详情</el-dropdown-item>
                          <el-dropdown-item command="temp_ban" divided>临时封禁</el-dropdown-item>
                          <el-dropdown-item command="perm_ban">永久封禁</el-dropdown-item>
                          <el-dropdown-item command="unban">解封</el-dropdown-item>
                          <el-dropdown-item command="force_unban">强制解封</el-dropdown-item>
                          <el-dropdown-item command="update" divided>更新账号ID</el-dropdown-item>
                          <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>
                </div>
              </template>
              <el-empty v-else description="暂无可用账号" />
            </div>
          </div>
        </el-card>
        
        <!-- 封禁的账号卡片 -->
        <el-card class="banned-accounts-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>被封禁的账号</span>
              <el-button size="small" type="primary" @click="loadBannedAccounts" plain>
                <el-icon><Refresh /></el-icon> 刷新
              </el-button>
            </div>
          </template>
          
          <div v-loading="bannedLoading" class="banned-accounts">
            <el-tabs v-model="bannedTabActive">
              <el-tab-pane label="临时封禁" name="temp">
                <template v-if="tempBannedAccounts.length > 0">
                  <div v-for="account in tempBannedAccounts" :key="account.accountId" class="banned-account-item">
                    <div class="banned-account-info">
                      <div class="account-id">{{ account.accountId }}</div>
                      <div class="ban-time">
                        <el-tooltip :content="account.banEndTime" placement="top">
                          <span>解封剩余: {{ formatBanTimeRemaining(account.banEndTime) }}</span>
                        </el-tooltip>
                      </div>
                    </div>
                    <div class="banned-account-actions">
                      <el-button size="small" type="primary" @click="unbanAccount(account.accountId)" plain>解封</el-button>
                    </div>
                  </div>
                </template>
                <el-empty v-else description="暂无临时封禁账号" />
              </el-tab-pane>
              <el-tab-pane label="永久封禁" name="perm">
                <template v-if="permBannedAccounts.length > 0">
                  <div v-for="account in permBannedAccounts" :key="account.accountId" class="banned-account-item">
                    <div class="banned-account-info">
                      <div class="account-id">{{ account.accountId }}</div>
                    </div>
                    <div class="banned-account-actions">
                      <el-button size="small" type="danger" @click="forceUnbanAccount(account.accountId)" plain>强制解封</el-button>
                    </div>
                  </div>
                </template>
                <el-empty v-else description="暂无永久封禁账号" />
              </el-tab-pane>
            </el-tabs>
          </div>
        </el-card>
      </el-col>
      
      <!-- 右侧面板 -->
      <el-col :span="16">
        <!-- Cookie列表卡片 -->
        <el-card class="cookie-list-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>Cookie 列表</span>
              <div class="header-actions">
                <el-button type="primary" size="small" @click="syncToRedis" :loading="syncing">
                  <el-icon><Connection /></el-icon> 同步到Redis
                </el-button>
                <el-button size="small" @click="loadCookies" :loading="listLoading">
                  <el-icon><Refresh /></el-icon> 刷新
                </el-button>
              </div>
            </div>
          </template>
          
          <div class="filter-section">
            <el-input
              v-model="searchAccount"
              placeholder="搜索账号ID"
              clearable
              prefix-icon="Search"
              class="filter-item"
            />
            <el-select
              v-model="statusFilter"
              placeholder="状态筛选"
              clearable
              class="filter-item"
            >
              <el-option label="可用" value="available" />
              <el-option label="临时封禁" value="temp_banned" />
              <el-option label="永久封禁" value="perm_banned" />
              <el-option label="已过期" value="expired" />
            </el-select>
            <el-button type="primary" @click="handleFilter">筛选</el-button>
            <el-button plain @click="resetFilter">重置</el-button>
          </div>
          
          <el-table
            v-loading="listLoading"
            :data="cookieList"
            style="width: 100%"
            border
            row-key="id"
            :default-sort="{ prop: 'account_id', order: 'ascending' }"
          >
            <el-table-column prop="id" label="ID" width="70" sortable />
            <el-table-column prop="account_id" label="账号ID" width="120" sortable />
            <el-table-column prop="cookie_name" label="Cookie名称" width="120" sortable />
            <el-table-column label="Cookie值" show-overflow-tooltip>
              <template #default="scope">
                <el-tooltip 
                  :content="scope.row.cookie_value" 
                  placement="top" 
                  :hide-after="0"
                >
                  <el-tag size="small" effect="plain" type="info">
                    {{ truncateText(scope.row.cookie_value, 20) }}
                  </el-tag>
                </el-tooltip>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100" sortable>
              <template #default="scope">
                <el-tag :type="getCookieStatusType(scope.row)" effect="light">
                  {{ getCookieStatusText(scope.row) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="过期时间" width="150" sortable>
              <template #default="scope">
                <span v-if="scope.row.expire_time">
                  {{ formatDateTime(scope.row.expire_time) }}
                </span>
                <span v-else>永不过期</span>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200">
              <template #default="scope">
                <el-button
                  type="primary"
                  size="small"
                  @click="editCookie(scope.row)"
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
                  @click="unbanCookie(scope.row.id)"
                  plain
                >
                  解封
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              :total="total"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>
    
    <!-- 添加/编辑Cookie对话框 -->
    <el-dialog
      v-model="cookieDialogVisible"
      :title="cookieForm.id ? '编辑Cookie' : '添加Cookie'"
      width="550px"
      destroy-on-close
    >
      <el-form :model="cookieForm" label-width="120px" :rules="cookieRules" ref="cookieFormRef">
        <el-form-item label="账号ID" prop="account_id">
          <el-input v-model="cookieForm.account_id" placeholder="请输入账号ID" />
        </el-form-item>
        
        <el-form-item v-if="!cookieForm.use_string_input" label="Cookie名称" prop="cookie_name">
          <el-input v-model="cookieForm.cookie_name" placeholder="请输入Cookie名称" />
        </el-form-item>
        
        <el-form-item v-if="!cookieForm.use_string_input" label="Cookie值" prop="cookie_value">
          <el-input v-model="cookieForm.cookie_value" type="textarea" rows="3" placeholder="请输入Cookie值" />
        </el-form-item>
        
        <el-form-item v-if="cookieForm.use_string_input" label="Cookie字符串" prop="cookie_string">
          <el-input v-model="cookieForm.cookie_string" type="textarea" rows="6" placeholder="请输入完整Cookie字符串（name=value; name2=value2）" />
        </el-form-item>
        
        <el-form-item>
          <el-checkbox v-model="cookieForm.use_string_input">使用Cookie字符串输入</el-checkbox>
        </el-form-item>
        
        <el-form-item label="过期天数" prop="expire_days">
          <el-input-number v-model="cookieForm.expire_days" :min="1" :max="365" />
          <span class="form-tip">不设置则永不过期</span>
        </el-form-item>
        
        <el-form-item v-if="cookieForm.id" label="可用状态" prop="is_available">
          <el-switch
            v-model="cookieForm.is_available"
            :disabled="cookieForm.is_permanently_banned || cookieForm.temp_ban_until"
          />
          <span class="form-tip">{{ cookieForm.is_available ? '可用' : '不可用' }}</span>
        </el-form-item>
        
        <el-form-item v-if="cookieForm.id" label="永久封禁" prop="is_permanently_banned">
          <el-switch v-model="cookieForm.is_permanently_banned" />
          <span class="form-tip">{{ cookieForm.is_permanently_banned ? '是' : '否' }}</span>
        </el-form-item>
        
        <el-form-item v-if="cookieForm.id && !cookieForm.is_permanently_banned" label="临时封禁至" prop="temp_ban_until">
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
        <div class="dialog-footer">
          <el-button @click="cookieDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitCookieForm" :loading="submitting">
            确认
          </el-button>
        </div>
      </template>
    </el-dialog>
    
    <!-- 临时封禁对话框 -->
    <el-dialog
      v-model="tempBanDialogVisible"
      title="临时封禁账号"
      width="400px"
      destroy-on-close
    >
      <el-form :model="tempBanForm" label-width="100px">
        <el-form-item label="账号ID">
          <el-tag>{{ tempBanForm.account_id }}</el-tag>
        </el-form-item>
        <el-form-item label="封禁时长">
          <el-input-number v-model="tempBanForm.duration_minutes" :min="1" :max="1440" />
          <span class="form-tip">分钟</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="tempBanDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitTempBan" :loading="submitting">
            确认
          </el-button>
        </div>
      </template>
    </el-dialog>
    
    <!-- 更新账号ID对话框 -->
    <el-dialog
      v-model="updateIdDialogVisible"
      title="更新账号ID"
      width="400px"
      destroy-on-close
    >
      <el-form :model="updateIdForm" label-width="100px" :rules="updateIdRules" ref="updateIdFormRef">
        <el-form-item label="原账号ID">
          <el-tag>{{ updateIdForm.old_account_id }}</el-tag>
        </el-form-item>
        <el-form-item label="新账号ID" prop="new_account_id">
          <el-input v-model="updateIdForm.new_account_id" placeholder="请输入新账号ID" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="updateIdDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitUpdateId" :loading="submitting">
            确认
          </el-button>
        </div>
      </template>
    </el-dialog>
    
    <!-- 查看账号Cookie详情对话框 -->
    <el-dialog
      v-model="accountDetailDialogVisible"
      title="账号Cookie详情"
      width="700px"
      destroy-on-close
    >
      <div v-loading="accountDetailLoading">
        <el-descriptions border :column="2" v-if="accountDetail">
          <el-descriptions-item label="账号ID" :span="2">{{ accountDetail.account_id }}</el-descriptions-item>
          <el-descriptions-item label="Cookie数量">{{ accountDetail.cookie_count }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="accountDetail.is_available ? 'success' : 'danger'">
              {{ accountDetail.is_available ? '可用' : '不可用' }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
        
        <el-divider content-position="left">Cookie详情</el-divider>
        
        <div class="cookie-detail-list" v-if="accountDetail">
          <el-input
            type="textarea"
            :rows="10"
            placeholder="Cookie值"
            v-model="accountDetailCookieString"
            readonly
          />
          <div class="action-row">
            <el-button type="primary" @click="copyCookieString">
              <el-icon><CopyDocument /></el-icon> 复制Cookie字符串
            </el-button>
          </div>
          
          <el-table :data="accountDetailCookies" style="width: 100%" border>
            <el-table-column prop="name" label="名称" width="180" />
            <el-table-column prop="value" label="值" show-overflow-tooltip />
          </el-table>
        </div>
        <el-empty v-else description="暂无详情" />
      </div>
    </el-dialog>
    
    <!-- 测试结果对话框 -->
    <el-dialog
      v-model="testResultDialogVisible"
      title="Cookie测试结果"
      width="500px"
      destroy-on-close
    >
      <div v-loading="testingAccount">
        <template v-if="testResult">
          <el-result
            :icon="testResult.is_valid ? 'success' : 'error'"
            :title="testResult.is_valid ? 'Cookie有效' : 'Cookie无效'"
            :sub-title="testResult.message"
          >
            <template #extra>
              <el-descriptions border :column="1">
                <el-descriptions-item label="账号ID">{{ testResult.account_id }}</el-descriptions-item>
                <el-descriptions-item label="状态码">{{ testResult.status }}</el-descriptions-item>
                <el-descriptions-item label="执行操作">{{ testResult.action_taken }}</el-descriptions-item>
              </el-descriptions>
            </template>
          </el-result>
        </template>
        <el-empty v-else description="暂无测试结果" />
      </div>
    </el-dialog>
    
    <!-- 批量测试结果对话框 -->
    <el-dialog
      v-model="batchTestResultDialogVisible"
      title="批量测试结果"
      width="700px"
      destroy-on-close
    >
      <div v-loading="testingAll">
        <template v-if="batchTestResult">
          <el-descriptions border :column="2">
            <el-descriptions-item label="测试总数">{{ batchTestResult.total_tested }}</el-descriptions-item>
            <el-descriptions-item label="有效数量">
              <el-tag type="success">{{ batchTestResult.valid_count }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="封禁数量">
              <el-tag type="warning">{{ batchTestResult.banned_count }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="未登录数量">
              <el-tag type="danger">{{ batchTestResult.not_login_count }}</el-tag>
            </el-descriptions-item>
          </el-descriptions>
          
          <el-divider />
          
          <el-tabs>
            <el-tab-pane label="有效账号">
              <div class="test-result-accounts">
                <el-tag
                  v-for="account in batchTestResult.valid_accounts"
                  :key="account"
                  type="success"
                  effect="plain"
                  class="test-result-tag"
                >
                  {{ account }}
                </el-tag>
                <el-empty v-if="!batchTestResult.valid_accounts.length" description="暂无有效账号" />
              </div>
            </el-tab-pane>
            <el-tab-pane label="被封禁账号">
              <div class="test-result-accounts">
                <el-tag
                  v-for="account in batchTestResult.banned_accounts"
                  :key="account"
                  type="warning"
                  effect="plain"
                  class="test-result-tag"
                >
                  {{ account }}
                </el-tag>
                <el-empty v-if="!batchTestResult.banned_accounts.length" description="暂无被封禁账号" />
              </div>
            </el-tab-pane>
            <el-tab-pane label="未登录账号">
              <div class="test-result-accounts">
                <el-tag
                  v-for="account in batchTestResult.not_login_accounts"
                  :key="account"
                  type="danger"
                  effect="plain"
                  class="test-result-tag"
                >
                  {{ account }}
                </el-tag>
                <el-empty v-if="!batchTestResult.not_login_accounts.length" description="暂无未登录账号" />
              </div>
            </el-tab-pane>
          </el-tabs>
        </template>
        <el-empty v-else description="暂无测试结果" />
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.cookie-manager-container {
  padding: 20px;
  max-width: 1600px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 28px;
  color: #303133;
  margin: 0;
  background: linear-gradient(45deg, #409EFF, #67C23A);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.api-status {
  display: flex;
  align-items: center;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  font-size: 16px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.status-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.banned-accounts-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.cookie-list-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.status-overview {
  display: flex;
  justify-content: space-between;
  padding: 15px 0;
}

.status-item {
  text-align: center;
  padding: 10px;
  border-radius: 8px;
  background-color: #f5f7fa;
  flex: 1;
  margin: 0 5px;
}

.status-value {
  font-size: 24px;
  font-weight: bold;
  margin-bottom: 5px;
}

.status-label {
  font-size: 12px;
  color: #606266;
}

.status-item.success .status-value {
  color: #67C23A;
}

.status-item.warning .status-value {
  color: #E6A23C;
}

.status-item.danger .status-value {
  color: #F56C6C;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 15px;
}

.account-list-section {
  margin-top: 15px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.section-header h3 {
  margin: 0;
  font-size: 16px;
  color: #606266;
}

.account-list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
}

.account-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid #EBEEF5;
  transition: background-color 0.3s;
}

.account-item:hover {
  background-color: #F5F7FA;
}

.account-item:last-child {
  border-bottom: none;
}

.account-info {
  display: flex;
  align-items: center;
}

.account-actions {
  display: flex;
  gap: 5px;
}

.banned-accounts {
  max-height: 400px;
  overflow-y: auto;
}

.banned-account-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid #EBEEF5;
}

.banned-account-item:last-child {
  border-bottom: none;
}

.banned-account-info {
  display: flex;
  flex-direction: column;
}

.account-id {
  font-weight: bold;
  margin-bottom: 5px;
}

.ban-time {
  font-size: 12px;
  color: #909399;
}

.filter-section {
  display: flex;
  margin-bottom: 15px;
  gap: 10px;
  flex-wrap: wrap;
}

.filter-item {
  width: 200px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 15px;
}

.form-tip {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 15px;
}

.cookie-detail-list {
  margin-top: 15px;
}

.action-row {
  margin: 10px 0;
  display: flex;
  justify-content: flex-end;
}

.test-result-accounts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
  padding: 10px;
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
}

.test-result-tag {
  margin-bottom: 5px;
}
</style>