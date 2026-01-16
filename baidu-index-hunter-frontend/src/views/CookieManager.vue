<script setup lang="ts">
// @ts-nocheck
import { ref, reactive, onMounted, computed, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox, ElNotification } from 'element-plus'
import { 
  Refresh, Plus, Delete, Connection, Search, CopyDocument,
  RefreshRight, ArrowDown, Check
} from '@element-plus/icons-vue'
import axios from 'axios'
import CookieUsageChart from '@/components/CookieUsageChart.vue'
import { useClipboard } from '@vueuse/core'
import { useTaskStore } from '@/stores/task'
import 'element-plus/es/components/message/style/css'
import 'element-plus/es/components/message-box/style/css'
import { Warning, View, Edit } from '@element-plus/icons-vue'

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
const updatingAbSr = ref(false)

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
const permBannedAccounts = ref<string[]>([])
const bannedTabActive = ref('temp')

// 封禁Cookie的多选状态
const tempBannedSelection = ref<string[]>([])
const permBannedSelection = ref<string[]>([])
const checkAllTemp = ref(false)
const checkAllPerm = ref(false)

const isTempIndeterminate = computed(() => {
  return tempBannedSelection.value.length > 0 && tempBannedSelection.value.length < tempBannedAccounts.value.length
})
const isPermIndeterminate = computed(() => {
  return permBannedSelection.value.length > 0 && permBannedSelection.value.length < permBannedAccounts.value.length
})

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
  cookie_json: '{}',
  use_string_input: false,
  expire_days: null,
  expire_option: 'none',
  is_available: true,
  is_permanently_banned: false,
  temp_ban_until: null as string | null,
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
    { required: true, message: '请输入Cookie名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ]
}

const updateIdRules = {
  new_account_id: [
    { required: true, message: '请输入新Cookie名称', trigger: 'blur' },
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

// 添加计时器引用
const banTimeUpdateTimer = ref(null)

// 添加Cookie编辑所需的变量
const cookieInputMode = ref('string')
const cookieTableData = ref<{ name: string, value: string }[]>([])
const importType = ref('txt')
const fileList = ref<any[]>([])
const selectedFile = ref<File | null>(null)
const importPreviewData = ref<{ name: string, value: string }[]>([])

// 根据导入类型返回对应的文件接受格式
const importFileAccept = computed(() => {
  switch (importType.value) {
    case 'txt':
      return '.txt'
    case 'json':
      return '.json'
    case 'csv':
      return '.csv'
    case 'excel':
      return '.xlsx,.xls'
    default:
      return ''
  }
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

// 加载可用Cookie列表
const loadAvailableAccounts = async () => {
  accountsLoading.value = true
  try {
    const response = await axios.get(`${API_BASE_URL}/admin/cookie/available-accounts`)
    if (response.data.code === 10000) {
      availableAccounts.value = response.data.data.account_ids || []
      console.log('可用Cookie列表:', availableAccounts.value)
    } else {
      ElMessage.error(`获取可用Cookie列表失败: ${response.data.msg}`)
    }
  } catch (error) {
    console.error('获取可用Cookie列表失败:', error)
    ElMessage.error('获取可用Cookie列表失败，请检查网络连接')
  } finally {
    accountsLoading.value = false
  }
}

// 加载被封禁的Cookie
const loadBannedAccounts = async () => {
  bannedLoading.value = true
  try {
    const response = await axios.get(`${API_BASE_URL}/admin/cookie/banned-accounts`)
    if (response.data.code === 10000) {
      // 正确解析临时封禁Cookie
      const tempBanned = response.data.data.temp_banned || []
      tempBannedAccounts.value = tempBanned.map(account => ({
        account_id: account.account_id,
        temp_ban_until: account.temp_ban_until,
        remaining_seconds: account.remaining_seconds
      }))
      
      // 正确解析永久封禁Cookie
      permBannedAccounts.value = response.data.data.perm_banned || []
      
      console.log('临时封禁Cookie:', tempBannedAccounts.value)
      console.log('永久封禁Cookie:', permBannedAccounts.value)
    } else {
      ElMessage.error(`获取被封禁Cookie列表失败: ${response.data.msg}`)
    }
  } catch (error) {
    console.error('获取被封禁Cookie列表失败:', error)
    ElMessage.error('获取被封禁Cookie列表失败，请检查网络连接')
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
      available_only: statusFilter.value === 'available' ? true : undefined,
      status: statusFilter.value || undefined
    }
    
    const response = await axios.get(`${API_BASE_URL}/admin/cookie/list`, { params })
    if (response.data.code === 10000) {
      // 处理返回的数据，确保cookie_value正确显示
      cookieList.value = (response.data.data || []).map(item => {
        // 如果有cookies字段，将其转换为字符串以便显示
        if (item.cookies && typeof item.cookies === 'object') {
          const cookieCount = Object.keys(item.cookies).length;
          const cookieString = Object.entries(item.cookies)
            .map(([name, value]) => `${name}=${value}`)
            .join('; ');
          
          return {
            ...item,
            cookie_count: cookieCount,
            cookie_value: cookieString
          };
        }
        return item;
      });
      
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
    cookie_json: '{}',
    use_string_input: false,
    expire_days: null,
    expire_option: 'none',
    is_available: true,
    is_permanently_banned: false,
    temp_ban_until: null
  })
  
  // 重置表格数据
  cookieTableData.value = []
  // 重置导入数据
  importPreviewData.value = []
  fileList.value = []
  selectedFile.value = null
  // 设置默认编辑模式
  cookieInputMode.value = 'string'
  
  cookieDialogVisible.value = true
}

// 编辑Cookie
const editCookie = async (cookie: any) => {
  try {
    loading.value = true;
    
    // 获取完整的Cookie信息
    const response = await axios.get(`${API_BASE_URL}/admin/cookie/account-cookie/${cookie.account_id}`);
    
    if (response.data.code === 10000) {
      const data = response.data.data;
      
      // 将cookies对象转换为字符串
      let cookieString = '';
      if (data.cookies) {
        cookieString = Object.entries(data.cookies)
          .map(([name, value]) => `${name}=${value}`)
          .join('; ');
      }
      
      // 将cookies对象转换为JSON字符串
      let cookieJson = '{}';
      if (data.cookies) {
        cookieJson = JSON.stringify(data.cookies, null, 2);
      }
      
      // 根据是否有过期时间设置expire_option
      const hasExpireTime = cookie.expire_time !== null;
      
      Object.assign(cookieForm, {
        id: cookie.id,
        account_id: data.account_id, // 确保设置了id，用于标识这是编辑操作
        cookie_name: '',
        cookie_value: '',
        cookie_string: cookieString,
        cookie_json: cookieJson,
        use_string_input: true, // 使用字符串模式编辑
        expire_days: hasExpireTime ? 365 : null,
        expire_option: hasExpireTime ? 'days' : 'none',
        is_available: cookie.is_available === 1,
        is_permanently_banned: cookie.is_permanently_banned === 1,
        temp_ban_until: cookie.temp_ban_until
      });
      
      // 初始化表格数据
      cookieTableData.value = Object.entries(data.cookies || {}).map(([name, value]) => ({
        name,
        value: value as string
      }));
      
      // 设置编辑模式
      cookieInputMode.value = 'json';
      
      cookieDialogVisible.value = true;
      
      console.log('编辑Cookie:', cookieForm);
    } else {
      ElMessage.error(`获取Cookie详情失败: ${response.data.msg}`);
    }
  } catch (error) {
    console.error('获取Cookie详情失败:', error);
    ElMessage.error('获取Cookie详情失败，请检查网络连接');
  } finally {
    loading.value = false;
  }
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
    
    // 根据当前编辑模式处理Cookie数据
    switch (cookieInputMode.value) {
      case 'string':
        // 字符串模式 - 将字符串解析为对象
        try {
          // 检查是否有字符串输入
          if (!cookieForm.cookie_string || cookieForm.cookie_string.trim() === '') {
            // 警告但不阻止提交，使用空对象
            ElMessage.warning('Cookie字符串为空，将提交空Cookie数据')
            cookieData.cookie_data = {}
          } else {
            const cookieObj = {}
            const cookieParts = cookieForm.cookie_string.split(';')
            
            cookieParts.forEach(cookie => {
              const trimmedCookie = cookie.trim()
              if (!trimmedCookie) return
              
              // 查找第一个等号的位置
              const equalSignIndex = trimmedCookie.indexOf('=')
              if (equalSignIndex > 0) {
                const name = trimmedCookie.substring(0, equalSignIndex).trim()
                const value = trimmedCookie.substring(equalSignIndex + 1).trim()
                cookieObj[name] = value
              }
            })
            
            cookieData.cookie_data = cookieObj
          }
          console.log("解析后的Cookie数据:", cookieData.cookie_data)
        } catch (e) {
          console.error("Cookie字符串解析错误:", e)
          ElMessage.error('Cookie字符串格式错误，请检查输入')
          submitting.value = false
          return
        }
        break
      case 'json':
        // JSON模式
        try {
          const jsonData = JSON.parse(cookieForm.cookie_json)
          
          // 检查是否是嵌套结构 (避免格式为 {account_id: xxx, cookie_data: {}} 的情况)
          if (jsonData.cookie_data) {
            cookieData.cookie_data = jsonData.cookie_data
          } else {
            cookieData.cookie_data = jsonData
          }
        } catch (e) {
          console.error("JSON解析错误:", e)
          ElMessage.error('JSON格式错误，请检查输入')
          submitting.value = false
          return
        }
        break
      case 'table':
        // 表格模式
        if (cookieTableData.value.length === 0) {
          ElMessage.error('表格数据为空，请添加至少一个Cookie字段')
          submitting.value = false
          return
        }
        
        // 验证表格数据
        for (const row of cookieTableData.value) {
          if (!row.name.trim()) {
            ElMessage.error('Cookie字段名不能为空')
            submitting.value = false
            return
          }
        }
        
        // 转换表格数据为对象
        const tableData = {}
        cookieTableData.value.forEach(row => {
          // 避免特殊字段导致嵌套
          if (row.name !== 'account_id' && row.name !== 'cookie_data' && row.name !== 'expire_days') {
            tableData[row.name] = row.value
          }
        })
        cookieData.cookie_data = tableData
        break
      case 'import':
        // 导入模式
        if (importPreviewData.value.length === 0) {
          ElMessage.error('导入数据为空，请先处理文件')
          submitting.value = false
          return
        }
        
        // 转换导入数据为对象
        const importData = {}
        importPreviewData.value.forEach(row => {
          // 避免特殊字段导致嵌套
          if (row.name !== 'account_id' && row.name !== 'cookie_data' && row.name !== 'expire_days') {
            importData[row.name] = row.value
          }
        })
        cookieData.cookie_data = importData
        break
    }
    
    // 根据expire_option决定是否设置过期时间
    if (cookieForm.expire_option === 'days' && cookieForm.expire_days) {
      cookieData.expire_days = cookieForm.expire_days
    }
    // 如果expire_option为none，则不设置expire_days，后端默认为null
    
    console.log('提交的Cookie数据:', cookieData)
    
    // 添加详细的日志，方便调试
    console.log('准备提交的Cookie数据:', JSON.stringify(cookieData, null, 2))
    
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

// Cookie编辑 - JSON格式化
const formatJson = () => {
  try {
    const parsed = JSON.parse(cookieForm.cookie_json)
    cookieForm.cookie_json = JSON.stringify(parsed, null, 2)
  } catch (e) {
    ElMessage.error('JSON格式错误，无法格式化')
  }
}

// Cookie编辑 - 字符串转JSON
const convertStringToJson = () => {
  if (!cookieForm.cookie_string) {
    ElMessage.warning('请先输入Cookie字符串')
    return
  }
  
  try {
    // 解析Cookie字符串为对象
    const cookieObj = {}
    const cookieParts = cookieForm.cookie_string.split(';')
    
    cookieParts.forEach(cookie => {
      const trimmedCookie = cookie.trim()
      if (!trimmedCookie) return
      
      // 查找第一个等号的位置
      const equalSignIndex = trimmedCookie.indexOf('=')
      if (equalSignIndex > 0) {
        const name = trimmedCookie.substring(0, equalSignIndex).trim()
        const value = trimmedCookie.substring(equalSignIndex + 1).trim()
        cookieObj[name] = value
      }
    })
    
    // 转换为格式化的JSON
    cookieForm.cookie_json = JSON.stringify(cookieObj, null, 2)
    
    // 切换到JSON模式
    cookieInputMode.value = 'json'
    
    ElMessage.success('转换成功')
  } catch (e) {
    console.error('转换失败:', e)
    ElMessage.error('转换失败，请检查Cookie字符串格式')
  }
}

// Cookie编辑 - 表格添加字段
const addCookieField = () => {
  cookieTableData.value.push({ name: '', value: '' })
}

// Cookie编辑 - 表格删除字段
const removeCookieField = (index: number) => {
  cookieTableData.value.splice(index, 1)
}

// Cookie编辑 - 清空所有字段
const clearAllFields = () => {
  ElMessageBox.confirm('确定要清空所有字段吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    cookieTableData.value = []
    ElMessage.success('已清空所有字段')
  }).catch(() => {})
}

// Cookie编辑 - 表格数据转JSON
const generateJsonFromTable = () => {
  if (cookieTableData.value.length === 0) {
    ElMessage.warning('表格数据为空')
    return
  }
  
  const jsonObj = {}
  cookieTableData.value.forEach(row => {
    if (row.name) {
      jsonObj[row.name] = row.value
    }
  })
  
  cookieForm.cookie_json = JSON.stringify(jsonObj, null, 2)
  cookieInputMode.value = 'json'
  ElMessage.success('已同步到JSON')
}

// Cookie编辑 - JSON转表格数据
const generateTableFromJson = () => {
  try {
    const jsonObj = JSON.parse(cookieForm.cookie_json)
    
    cookieTableData.value = Object.entries(jsonObj).map(([name, value]) => ({
      name,
      value: value as string
    }))
    
    cookieInputMode.value = 'table'
    ElMessage.success('已同步到表格')
  } catch (e) {
    ElMessage.error('JSON格式错误，无法转换为表格')
  }
}

// Cookie编辑 - 处理文件变更
const handleFileChange = (file: any) => {
  selectedFile.value = file.raw
}

// Cookie编辑 - 处理Cookie文件
const processCookieFile = async () => {
  if (!selectedFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  
  importPreviewData.value = []
  
  try {
    const file = selectedFile.value
    
    // 根据导入类型处理文件内容
    switch (importType.value) {
      case 'txt':
      case 'json':
      case 'csv':
        const fileContent = await readFileContent(file)
        if (importType.value === 'txt') {
          processTxtContent(fileContent)
        } else if (importType.value === 'json') {
          processJsonContent(fileContent)
        } else if (importType.value === 'csv') {
          processCsvContent(fileContent)
        }
        break
      case 'excel':
        await processExcelFile(file)
        break
    }
  } catch (error) {
    console.error('处理文件失败:', error)
    ElMessage.error('处理文件失败，请检查文件格式')
  }
}

// 读取文件内容
const readFileContent = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    
    reader.onload = (event) => {
      if (event.target?.result) {
        resolve(event.target.result as string)
      } else {
        reject(new Error('读取文件内容失败'))
      }
    }
    
    reader.onerror = () => {
      reject(new Error('读取文件失败'))
    }
    
    reader.readAsText(file)
  })
}

// 处理TXT文件内容（假设格式为 name=value 或 name:value，每行一个）
const processTxtContent = (content: string) => {
  const lines = content.split('\n').filter(line => line.trim())
  const result = []
  
  for (const line of lines) {
    let name = '', value = ''
    
    if (line.includes('=')) {
      [name, value] = line.trim().split('=', 2)
    } else if (line.includes(':')) {
      [name, value] = line.trim().split(':', 2)
    }
    
    if (name && value) {
      result.push({ name: name.trim(), value: value.trim() })
    }
  }
  
  if (result.length > 0) {
    importPreviewData.value = result
    ElMessage.success(`成功解析${result.length}个Cookie字段`)
  } else {
    ElMessage.error('未找到有效的Cookie字段，请检查文件格式')
  }
}

// 处理JSON文件内容
const processJsonContent = (content: string) => {
  try {
    const jsonObj = JSON.parse(content)
    
    const result = Object.entries(jsonObj).map(([name, value]) => ({
      name,
      value: typeof value === 'string' ? value : JSON.stringify(value)
    }))
    
    if (result.length > 0) {
      importPreviewData.value = result
      ElMessage.success(`成功解析${result.length}个Cookie字段`)
    } else {
      ElMessage.error('JSON数据为空')
    }
  } catch (e) {
    ElMessage.error('JSON格式错误，无法解析')
  }
}

// 处理CSV文件内容（假设格式为两列：name,value）
const processCsvContent = (content: string) => {
  const lines = content.split('\n').filter(line => line.trim())
  const result = []
  
  // 检查是否有标题行
  const hasHeader = lines[0].toLowerCase().includes('name') && 
                   (lines[0].toLowerCase().includes('value') || lines[0].toLowerCase().includes('val'))
  
  // 从第一行或第二行开始处理（如果有标题行则从第二行开始）
  const startIndex = hasHeader ? 1 : 0
  
  for (let i = startIndex; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue
    
    // 解析CSV行，处理引号和逗号的情况
    const values = parseCSVLine(line)
    
    if (values.length >= 2) {
      result.push({
        name: values[0].trim(),
        value: values[1].trim()
      })
    }
  }
  
  if (result.length > 0) {
    importPreviewData.value = result
    ElMessage.success(`成功解析${result.length}个Cookie字段`)
  } else {
    ElMessage.error('未找到有效的Cookie字段，请检查CSV格式')
  }
}

// 解析CSV行，处理引号和逗号
const parseCSVLine = (line: string): string[] => {
  const result = []
  let current = ''
  let inQuotes = false
  
  for (let i = 0; i < line.length; i++) {
    const char = line[i]
    
    if (char === '"' && (i === 0 || line[i - 1] !== '\\')) {
      inQuotes = !inQuotes
    } else if (char === ',' && !inQuotes) {
      result.push(current)
      current = ''
    } else {
      current += char
    }
  }
  
  result.push(current)
  return result
}

// 确认导入预览数据
const confirmImport = () => {
  if (importPreviewData.value.length === 0) {
    ElMessage.warning('没有可导入的数据')
    return
  }
  
  // 生成JSON格式
  const jsonObj = {}
  importPreviewData.value.forEach(row => {
    if (row.name) {
      jsonObj[row.name] = row.value
    }
  })
  
  // 更新表单
  cookieForm.cookie_json = JSON.stringify(jsonObj, null, 2)
  
  // 更新表格数据
  cookieTableData.value = [...importPreviewData.value]
  
  // 切换到JSON模式
  cookieInputMode.value = 'json'
  
  // 清理导入数据
  importPreviewData.value = []
  fileList.value = []
  selectedFile.value = null
  
  ElMessage.success('导入成功')
}

// 取消导入
const cancelImport = () => {
  importPreviewData.value = []
  fileList.value = []
  selectedFile.value = null
  ElMessage.info('已取消导入')
}

// 删除Cookie
const deleteCookie = async (account_id: number) => {
  try {
    await ElMessageBox.confirm('确定要删除此Cookie吗？此操作不可恢复。', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    listLoading.value = true
    
    const response = await axios.delete(`${API_BASE_URL}/admin/cookie/delete/${account_id}`)
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
  checkApiConnection()
  refreshCookieStatus()
  loadAvailableAccounts()
  loadBannedAccounts()
  loadCookies()
  
  // 设置每5秒更新一次解封时间的计时器
  banTimeUpdateTimer.value = setInterval(() => {
    updateBanTimeRemaining();
    // 每分钟刷新一次被封禁的Cookie列表
    if (new Date().getSeconds() === 0) {
      loadBannedAccounts();
    }
  }, 5000);
})

// 在组件卸载时清除计时器
onUnmounted(() => {
  if (banTimeUpdateTimer.value) {
    clearInterval(banTimeUpdateTimer.value)
  }
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

// 更新ab_sr cookie
const updateAbSr = async () => {
  try {
    updatingAbSr.value = true
    
    const response = await axios.post(`${API_BASE_URL}/admin/cookie/update-ab-sr`)
    if (response.data.code === 10000) {
      ElMessage.success(response.data.msg)
      refreshCookieStatus()
      loadCookies()
    } else {
      ElMessage.error(`更新ab_sr失败: ${response.data.msg}`)
    }
  } catch (error) {
    console.error('更新ab_sr失败:', error)
    ElMessage.error('更新ab_sr失败，请检查网络连接')
  } finally {
    updatingAbSr.value = false
  }
}

// 测试单个Cookie可用性
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
      // 确保cookies数据正确解析
      const data = response.data.data;
      if (data) {
        accountDetail.value = {
          ...data,
          cookies: data.cookies || {}
        };
      }
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
const formatBanTimeRemaining = (seconds) => {
  if (!seconds || seconds <= 0) return '已解封'
  
  const days = Math.floor(seconds / (24 * 3600))
  const hours = Math.floor((seconds % (24 * 3600)) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  
  let result = ''
  if (days > 0) result += `${days}天`
  if (hours > 0) result += `${hours}小时`
  if (minutes > 0) result += `${minutes}分钟`
  if (remainingSeconds > 0 && !days && !hours) result += `${remainingSeconds}秒`
  
  return result || '0秒'
}

// 更新临时封禁账号的剩余时间
const updateBanTimeRemaining = () => {
  if (tempBannedAccounts.value.length > 0) {
    tempBannedAccounts.value.forEach(account => {
      if (account.remaining_seconds > 0) {
        account.remaining_seconds -= 5 // 每5秒减少5秒
      }
    })
  }
}

// 处理Cookie操作命令
const handleCookieCommand = (command: string, cookie: any) => {
  switch (command) {
    case 'edit':
      editCookie(cookie)
      break
    case 'delete':
      deleteCookie(cookie.account_id)
      break
    case 'unban':
      unbanCookie(cookie.account_id)
      break
  }
}

// 处理Excel文件
const processExcelFile = async (file: File) => {
  try {
    // 加载xlsx库
    // 注意: 需要安装xlsx库 npm install xlsx --save
    const XLSX = await import('xlsx')
    
    // 读取Excel文件
    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const data = e.target?.result
        if (!data) {
          ElMessage.error('读取Excel文件失败')
          return
        }
        
        // 解析Excel数据
        const workbook = XLSX.read(data, { type: 'array' })
        const firstSheetName = workbook.SheetNames[0]
        const worksheet = workbook.Sheets[firstSheetName]
        
        // 转换为JSON
        const jsonData = XLSX.utils.sheet_to_json(worksheet)
        
        if (jsonData.length === 0) {
          ElMessage.error('Excel文件内容为空')
          return
        }
        
        // 检查是否有name和value列
        const firstRow = jsonData[0]
        const hasNameCol = 'name' in firstRow || 'Name' in firstRow || 'NAME' in firstRow
        const hasValueCol = 'value' in firstRow || 'Value' in firstRow || 'VALUE' in firstRow
        
        if (!hasNameCol || !hasValueCol) {
          ElMessage.error('Excel文件必须包含name和value列')
          return
        }
        
        // 提取name和value列数据
        const result = jsonData.map(row => {
          const nameKey = Object.keys(row).find(key => key.toLowerCase() === 'name')
          const valueKey = Object.keys(row).find(key => key.toLowerCase() === 'value')
          
          if (nameKey && valueKey) {
            return {
              name: String(row[nameKey]),
              value: String(row[valueKey])
            }
          }
          return null
        }).filter(item => item !== null)
        
        if (result.length > 0) {
          importPreviewData.value = result
          ElMessage.success(`成功解析${result.length}个Cookie字段`)
        } else {
          ElMessage.error('未找到有效的Cookie字段，请检查Excel格式')
        }
      } catch (error) {
        console.error('解析Excel失败:', error)
        ElMessage.error('解析Excel文件失败，请检查格式')
      }
    }
    
    reader.onerror = () => {
      ElMessage.error('读取Excel文件失败')
    }
    
    reader.readAsArrayBuffer(file)
  } catch (error) {
    console.error('处理Excel文件失败:', error)
    ElMessage.error('处理Excel文件失败，请确保安装了xlsx库')
  }
}

// 添加多选相关的变量
const multipleSelection = ref([])
const batchActionLoading = ref(false)
const batchTempBanDialogVisible = ref(false)
const batchTempBanForm = reactive({
  duration_minutes: 30
})

// 处理表格多选变化
const handleSelectionChange = (selection) => {
  multipleSelection.value = selection
}

// 处理临时封禁全选
const handleCheckAllTempChange = (val: boolean) => {
  tempBannedSelection.value = val ? tempBannedAccounts.value.map(item => item.account_id) : []
  checkAllTemp.value = val
}

// 处理永久封禁全选
const handleCheckAllPermChange = (val: boolean) => {
  permBannedSelection.value = val ? [...permBannedAccounts.value] : []
  checkAllPerm.value = val
}

// 批量解封选中的临时封禁Cookie
const unbanSelectedTemp = async () => {
  if (tempBannedSelection.value.length === 0) return
  
  try {
    bannedLoading.value = true
    let successCount = 0
    for (const accountId of tempBannedSelection.value) {
      const response = await axios.post(`${API_BASE_URL}/admin/cookie/unban/${accountId}`)
      if (response.data.code === 10000) successCount++
    }
    ElMessage.success(`成功解封 ${successCount} 个Cookie`)
    loadBannedAccounts()
    refreshCookieStatus()
    loadCookies()
    tempBannedSelection.value = []
    checkAllTemp.value = false
  } catch (error) {
    ElMessage.error('批量解封失败')
  } finally {
    bannedLoading.value = false
  }
}

// 解封所有临时封禁Cookie
const unbanAllTemp = async () => {
  if (tempBannedAccounts.value.length === 0) return
  
  try {
    await ElMessageBox.confirm('确定要解封所有临时封禁的Cookie吗？', '提示', { type: 'warning' })
    bannedLoading.value = true
    
    let successCount = 0
    for (const item of tempBannedAccounts.value) {
      const response = await axios.post(`${API_BASE_URL}/admin/cookie/unban/${item.account_id}`)
      if (response.data.code === 10000) successCount++
    }
    
    ElMessage.success(`成功解封 ${successCount} 个Cookie`)
    loadBannedAccounts()
    refreshCookieStatus()
    loadCookies()
    tempBannedSelection.value = []
    checkAllTemp.value = false
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('解封所有失败')
  } finally {
    bannedLoading.value = false
  }
}

// 批量强制解封选中的永久封禁Cookie
const unbanSelectedPerm = async () => {
  if (permBannedSelection.value.length === 0) return
  
  try {
    bannedLoading.value = true
    let successCount = 0
    for (const accountId of permBannedSelection.value) {
      const response = await axios.post(`${API_BASE_URL}/admin/cookie/force-unban/${accountId}`)
      if (response.data.code === 10000) successCount++
    }
    ElMessage.success(`成功解封 ${successCount} 个Cookie`)
    loadBannedAccounts()
    refreshCookieStatus()
    loadCookies()
    permBannedSelection.value = []
    checkAllPerm.value = false
  } catch (error) {
    ElMessage.error('批量解封失败')
  } finally {
    bannedLoading.value = false
  }
}

// 解封所有永久封禁Cookie
const unbanAllPerm = async () => {
  if (permBannedAccounts.value.length === 0) return
  
  try {
    await ElMessageBox.confirm('确定要强制解封所有永久封禁的Cookie吗？', '提示', { type: 'warning' })
    bannedLoading.value = true
    
    let successCount = 0
    for (const accountId of permBannedAccounts.value) {
      const response = await axios.post(`${API_BASE_URL}/admin/cookie/force-unban/${accountId}`)
      if (response.data.code === 10000) successCount++
    }
    
    ElMessage.success(`成功解封 ${successCount} 个Cookie`)
    loadBannedAccounts()
    refreshCookieStatus()
    loadCookies()
    permBannedSelection.value = []
    checkAllPerm.value = false
  } catch (error) {
    if (error !== 'cancel') ElMessage.error('解封所有失败')
  } finally {
    bannedLoading.value = false
  }
}

// 批量封禁所有Cookie
const batchBanAll = async () => {
  try {
    await ElMessageBox.confirm('确定要临时封禁所有Cookie吗？此操作可以通过批量解封恢复。', '确认批量封禁', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    batchActionLoading.value = true
    
    // 获取所有可用账号ID
    const response = await axios.get(`${API_BASE_URL}/admin/cookie/available-accounts`)
    if (response.data.code === 10000) {
      const accountIds = response.data.data.account_ids || []
      
      if (accountIds.length === 0) {
        ElMessage.warning('没有可用的Cookie可以封禁')
        batchActionLoading.value = false
        return
      }
      
      // 批量封禁
      let successCount = 0
      for (const accountId of accountIds) {
        try {
          const banResponse = await axios.post(`${API_BASE_URL}/admin/cookie/ban/temporary/${accountId}`, {
            duration_seconds: 1800 // 默认30分钟
          })
          
          if (banResponse.data.code === 10000) {
            successCount++
          }
        } catch (error) {
          console.error(`封禁账号 ${accountId} 失败:`, error)
        }
      }
      
      ElMessage.success(`成功封禁 ${successCount}/${accountIds.length} 个Cookie`)
      
      // 重新加载数据
      refreshCookieStatus()
      loadCookies()
      loadAvailableAccounts()
      loadBannedAccounts()
    } else {
      ElMessage.error(`获取可用账号失败: ${response.data.msg}`)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量封禁失败:', error)
      ElMessage.error('批量封禁失败，请检查网络连接')
    }
  } finally {
    batchActionLoading.value = false
  }
}

// 批量解封所有Cookie
const batchUnbanAll = async () => {
  try {
    await ElMessageBox.confirm('确定要解封所有被临时封禁的Cookie吗？', '确认批量解封', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    batchActionLoading.value = true
    
    // 获取所有临时封禁的账号
    const response = await axios.get(`${API_BASE_URL}/admin/cookie/banned-accounts`)
    if (response.data.code === 10000) {
      const tempBannedAccounts = response.data.data.temp_banned || []
      
      if (tempBannedAccounts.length === 0) {
        ElMessage.warning('没有临时封禁的Cookie可以解封')
        batchActionLoading.value = false
        return
      }
      
      // 批量解封
      let successCount = 0
      for (const account of tempBannedAccounts) {
        try {
          const unbanResponse = await axios.post(`${API_BASE_URL}/admin/cookie/unban/${account.account_id}`)
          
          if (unbanResponse.data.code === 10000) {
            successCount++
          }
        } catch (error) {
          console.error(`解封账号 ${account.account_id} 失败:`, error)
        }
      }
      
      ElMessage.success(`成功解封 ${successCount}/${tempBannedAccounts.length} 个Cookie`)
      
      // 重新加载数据
      refreshCookieStatus()
      loadCookies()
      loadAvailableAccounts()
      loadBannedAccounts()
    } else {
      ElMessage.error(`获取被封禁账号失败: ${response.data.msg}`)
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量解封失败:', error)
      ElMessage.error('批量解封失败，请检查网络连接')
    }
  } finally {
    batchActionLoading.value = false
  }
}

// 批量临时封禁选中的Cookie
const batchTempBan = () => {
  if (multipleSelection.value.length === 0) {
    ElMessage.warning('请先选择要封禁的Cookie')
    return
  }
  
  batchTempBanDialogVisible.value = true
}

// 提交批量临时封禁
const submitBatchTempBan = async () => {
  try {
    batchActionLoading.value = true
    
    const durationSeconds = batchTempBanForm.duration_minutes * 60
    let successCount = 0
    
    for (const item of multipleSelection.value) {
      try {
        const response = await axios.post(`${API_BASE_URL}/admin/cookie/ban/temporary/${item.account_id}`, {
          duration_seconds: durationSeconds
        })
        
        if (response.data.code === 10000) {
          successCount++
        }
      } catch (error) {
        console.error(`临时封禁账号 ${item.account_id} 失败:`, error)
      }
    }
    
    ElMessage.success(`成功临时封禁 ${successCount}/${multipleSelection.value.length} 个Cookie，持续时间 ${batchTempBanForm.duration_minutes} 分钟`)
    batchTempBanDialogVisible.value = false
    
    // 重新加载数据
    refreshCookieStatus()
    loadCookies()
    loadAvailableAccounts()
    loadBannedAccounts()
    
    // 清空选择
    multipleSelection.value = []
  } catch (error) {
    console.error('批量临时封禁失败:', error)
    ElMessage.error('批量临时封禁失败，请检查网络连接')
  } finally {
    batchActionLoading.value = false
  }
}

// 批量永久封禁选中的Cookie
const batchPermBan = async () => {
  if (multipleSelection.value.length === 0) {
    ElMessage.warning('请先选择要封禁的Cookie')
    return
  }
  
  try {
    await ElMessageBox.confirm(`确定要永久封禁选中的 ${multipleSelection.value.length} 个Cookie吗？此操作可以通过强制解封恢复。`, '确认批量永久封禁', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    batchActionLoading.value = true
    
    let successCount = 0
    for (const item of multipleSelection.value) {
      try {
        const response = await axios.post(`${API_BASE_URL}/admin/cookie/ban/permanent/${item.account_id}`)
        
        if (response.data.code === 10000) {
          successCount++
        }
      } catch (error) {
        console.error(`永久封禁账号 ${item.account_id} 失败:`, error)
      }
    }
    
    ElMessage.success(`成功永久封禁 ${successCount}/${multipleSelection.value.length} 个Cookie`)
    
    // 重新加载数据
    refreshCookieStatus()
    loadCookies()
    loadAvailableAccounts()
    loadBannedAccounts()
    
    // 清空选择
    multipleSelection.value = []
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量永久封禁失败:', error)
      ElMessage.error('批量永久封禁失败，请检查网络连接')
    }
  } finally {
    batchActionLoading.value = false
  }
}

// 批量解封选中的Cookie
const batchUnban = async () => {
  if (multipleSelection.value.length === 0) {
    ElMessage.warning('请先选择要解封的Cookie')
    return
  }
  
  try {
    await ElMessageBox.confirm(`确定要解封选中的 ${multipleSelection.value.length} 个Cookie吗？`, '确认批量解封', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    batchActionLoading.value = true
    
    let successCount = 0
    for (const item of multipleSelection.value) {
      try {
        // 对于临时封禁的使用普通解封
        if (item.temp_ban_until) {
          const response = await axios.post(`${API_BASE_URL}/admin/cookie/unban/${item.account_id}`)
          
          if (response.data.code === 10000) {
            successCount++
          }
        } 
        // 对于永久封禁的使用强制解封
        else if (item.is_permanently_banned === 1) {
          const response = await axios.post(`${API_BASE_URL}/admin/cookie/force-unban/${item.account_id}`)
          
          if (response.data.code === 10000) {
            successCount++
          }
        }
        // 对于正常状态的Cookie不需要操作
        else {
          successCount++
        }
      } catch (error) {
        console.error(`解封账号 ${item.account_id} 失败:`, error)
      }
    }
    
    ElMessage.success(`成功解封 ${successCount}/${multipleSelection.value.length} 个Cookie`)
    
    // 重新加载数据
    refreshCookieStatus()
    loadCookies()
    loadAvailableAccounts()
    loadBannedAccounts()
    
    // 清空选择
    multipleSelection.value = []
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量解封失败:', error)
      ElMessage.error('批量解封失败，请检查网络连接')
    }
  } finally {
    batchActionLoading.value = false
  }
}
</script>

<template>
  <div class="cookie-manager-container">
    <div class="page-header">
      <h1>Cookie 管理</h1>
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
              <h3>可用Cookie列表</h3>
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
                          <el-dropdown-item command="update" divided>更新Cookie名称</el-dropdown-item>
                          <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>
                </div>
              </template>
              <el-empty v-else description="暂无可用Cookie" />
            </div>
          </div>
        </el-card>
        
        <!-- 封禁的账号卡片 -->
        <el-card class="banned-accounts-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>被封禁的Cookie</span>
              <el-button size="small" type="primary" @click="loadBannedAccounts" plain>
                <el-icon><Refresh /></el-icon> 刷新
              </el-button>
            </div>
          </template>
          
          <div v-loading="bannedLoading" class="banned-accounts">
            <el-tabs v-model="bannedTabActive">
              <el-tab-pane label="临时封禁" name="temp">
                <div class="banned-toolbar" v-if="tempBannedAccounts.length > 0">
                  <el-checkbox v-model="checkAllTemp" :indeterminate="isTempIndeterminate" @change="handleCheckAllTempChange">全选</el-checkbox>
                  <el-button type="primary" link size="small" :disabled="tempBannedSelection.length === 0" @click="unbanSelectedTemp">解封选中</el-button>
                  <el-button type="danger" link size="small" @click="unbanAllTemp">解封所有</el-button>
                </div>
                <template v-if="tempBannedAccounts.length > 0">
                  <el-checkbox-group v-model="tempBannedSelection">
                    <div v-for="account in tempBannedAccounts" :key="account.account_id" class="banned-account-item">
                      <el-checkbox :value="account.account_id" class="banned-checkbox" />
                      <div class="banned-account-info">
                        <div class="account-id">{{ account.account_id }}</div>
                        <div class="ban-time">
                          剩余: {{ formatBanTimeRemaining(account.remaining_seconds) }}
                        </div>
                        <div class="ban-time-tooltip">
                          {{ account.temp_ban_until }}
                        </div>
                      </div>
                      <div class="banned-account-actions">
                        <el-button size="small" type="primary" @click.stop="unbanAccount(account.account_id)" plain>解封</el-button>
                      </div>
                    </div>
                  </el-checkbox-group>
                </template>
                <el-empty v-else description="暂无临时封禁账号" />
              </el-tab-pane>
              <el-tab-pane label="永久封禁" name="perm">
                <div class="banned-toolbar" v-if="permBannedAccounts.length > 0">
                  <el-checkbox v-model="checkAllPerm" :indeterminate="isPermIndeterminate" @change="handleCheckAllPermChange">全选</el-checkbox>
                  <el-button type="primary" link size="small" :disabled="permBannedSelection.length === 0" @click="unbanSelectedPerm">强制解封选中</el-button>
                  <el-button type="danger" link size="small" @click="unbanAllPerm">强制解封所有</el-button>
                </div>
                <template v-if="permBannedAccounts.length > 0">
                  <el-checkbox-group v-model="permBannedSelection">
                    <div v-for="account in permBannedAccounts" :key="account" class="banned-account-item">
                      <el-checkbox :value="account" class="banned-checkbox" />
                      <div class="banned-account-info">
                        <div class="account-id">{{ account }}</div>
                        <div class="ban-status">永久封禁</div>
                      </div>
                      <div class="banned-account-actions">
                        <el-button size="small" type="danger" @click.stop="forceUnbanAccount(account)" plain>强制解封</el-button>
                      </div>
                    </div>
                  </el-checkbox-group>
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
                <el-button type="success" size="small" @click="updateAbSr" :loading="updatingAbSr">
                  <el-icon><RefreshRight /></el-icon> 更新ab_sr
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
              placeholder="搜索Cookie名称"
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
            <el-button type="success" @click="openAddCookieDialog">
              <el-icon><Plus /></el-icon> 添加Cookie
            </el-button>
          </div>
          
          <div class="batch-actions" v-if="cookieList.length > 0">
            <el-button-group>
              <el-button type="danger" @click="batchBanAll" :loading="batchActionLoading">批量封禁所有Cookie</el-button>
              <el-button type="success" @click="batchUnbanAll" :loading="batchActionLoading">批量解封所有Cookie</el-button>
            </el-button-group>
            <el-button-group v-if="multipleSelection.length > 0" class="ml-10">
              <el-button type="warning" @click="batchTempBan" :loading="batchActionLoading">临时封禁选中</el-button>
              <el-button type="danger" @click="batchPermBan" :loading="batchActionLoading">永久封禁选中</el-button>
              <el-button type="success" @click="batchUnban" :loading="batchActionLoading">解封选中</el-button>
            </el-button-group>
            <span v-if="multipleSelection.length > 0" class="selection-info">
              已选择 {{ multipleSelection.length }} 项
            </span>
          </div>
          
          <el-table
            v-loading="listLoading"
            :data="cookieList"
            style="width: 100%"
            border
            row-key="id"
            :default-sort="{ prop: 'account_id', order: 'ascending' }"
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column prop="account_id" label="Cookie名" width="120" show-overflow-tooltip sortable />
            <el-table-column label="字段数量" width="90">
              <template #default="scope">
                <el-tag size="small" effect="plain" type="info">
                  {{ scope.row.cookie_count || 0 }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="Cookie值" show-overflow-tooltip>
              <template #default="scope">
                <el-tooltip 
                  :content="scope.row.cookie_value" 
                  placement="top" 
                  :hide-after="0"
                >
                  <el-tag size="small" effect="plain" type="info">
                    {{ truncateText(scope.row.cookie_value, 40) }}
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
            <el-table-column label="操作" width="100">
              <template #default="scope">
                <el-dropdown trigger="click" @command="(command) => handleCookieCommand(command, scope.row)">
                  <el-button type="primary" size="small" plain>
                    操作<el-icon class="el-icon--right"><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="edit">编辑</el-dropdown-item>
                      <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                      <el-dropdown-item v-if="scope.row.temp_ban_until" command="unban">解封</el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </template>
            </el-table-column>
          </el-table>
          
          <div class="pagination-container">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :page-sizes="[20, 35, 50]"
              layout="total, sizes, prev, pager, next, jumper"
              :total="total"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>
    <!-- Cookie使用量图表卡片 -->
    <el-card class="usage-chart-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>Cookie使用量统计</span>
        </div>
      </template>
      
      <CookieUsageChart :api-base-url="API_BASE_URL" />
    </el-card>
    <!-- 添加/编辑Cookie对话框 -->
    <el-dialog
      v-model="cookieDialogVisible"
      :title="cookieForm.account_id ? '编辑Cookie' : '添加Cookie'"
      width="700px"
      destroy-on-close
    >
      <el-form :model="cookieForm" label-width="120px" :rules="cookieRules" ref="cookieFormRef">
        <el-form-item label="Cookie名称" prop="account_id">
          <el-input v-model="cookieForm.account_id" placeholder="请输入Cookie名称" />
        </el-form-item>
        
        <el-tabs v-model="cookieInputMode" type="card">
          <!-- 字符串输入模式 -->
          <el-tab-pane label="字符串输入" name="string">
            <el-form-item label="Cookie字符串">
              <el-input v-model="cookieForm.cookie_string" type="textarea" rows="8" placeholder="请输入完整Cookie字符串（name=value; name2=value2）" />
            </el-form-item>
          </el-tab-pane>
          
          <!-- JSON输入模式 -->
          <el-tab-pane label="JSON输入" name="json">
            <el-form-item label="Cookie JSON" prop="cookie_json">
              <el-input v-model="cookieForm.cookie_json" type="textarea" rows="8" placeholder="请输入JSON格式的Cookie数据" :spellcheck="false" />
              <div class="form-actions">
                <el-button size="small" type="primary" @click="formatJson">格式化JSON</el-button>
                <el-button size="small" type="info" @click="convertStringToJson">从字符串转换</el-button>
              </div>
            </el-form-item>
          </el-tab-pane>
          
          <!-- 表格输入模式 -->
          <el-tab-pane label="表格输入" name="table">
            <div class="table-toolbar">
              <el-button type="primary" size="small" @click="addCookieField">
                <el-icon><Plus /></el-icon> 添加字段
              </el-button>
              <el-button type="danger" size="small" @click="clearAllFields">
                <el-icon><Delete /></el-icon> 清空所有
              </el-button>
            </div>
            
            <el-table :data="cookieTableData" border style="width: 100%" max-height="300px">
              <el-table-column label="Cookie名" width="180">
                <template #default="scope">
                  <el-input v-model="scope.row.name" placeholder="字段名称" size="small" />
                </template>
              </el-table-column>
              <el-table-column label="Cookie值">
                <template #default="scope">
                  <el-input v-model="scope.row.value" placeholder="字段值" size="small" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120">
                <template #default="scope">
                  <el-button
                    type="danger"
                    icon="Delete"
                    circle
                    size="small"
                    @click="removeCookieField(scope.$index)"
                  />
                </template>
              </el-table-column>
            </el-table>
            <div class="form-actions">
              <el-button size="small" type="primary" @click="generateJsonFromTable">同步到JSON</el-button>
              <el-button size="small" type="info" @click="generateTableFromJson">从JSON同步</el-button>
            </div>
          </el-tab-pane>
          
          <!-- 导入模式 -->
          <el-tab-pane label="文件导入" name="import">
            <el-form-item label="导入方式">
              <el-select v-model="importType" placeholder="请选择导入方式">
                <el-option label="TXT文件" value="txt" />
                <el-option label="JSON文件" value="json" />
                <el-option label="CSV文件" value="csv" />
                <el-option label="Excel文件" value="excel" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="文件上传">
              <el-upload
                class="upload-demo"
                action="#"
                :auto-upload="false"
                :on-change="handleFileChange"
                :file-list="fileList"
                :limit="1"
                :accept="importFileAccept"
              >
                <template #trigger>
                  <el-button type="primary">选择文件</el-button>
                </template>
                <template #tip>
                  <div class="el-upload__tip">
                    请上传包含Cookie数据的文件，CSV/Excel格式需要包含name和value两列
                  </div>
                </template>
              </el-upload>
              <el-button type="success" @click="processCookieFile" :disabled="!selectedFile">处理文件</el-button>
            </el-form-item>
            
            <el-form-item label="导入预览" v-if="importPreviewData.length > 0">
              <el-table :data="importPreviewData" border style="width: 100%" max-height="200px">
                <el-table-column label="Cookie名" prop="name" width="180" />
                <el-table-column label="Cookie值" prop="value" show-overflow-tooltip />
              </el-table>
              <div class="form-actions">
                <el-button size="small" type="primary" @click="confirmImport">确认导入</el-button>
                <el-button size="small" type="danger" @click="cancelImport">取消导入</el-button>
              </div>
            </el-form-item>
          </el-tab-pane>
        </el-tabs>
        
        <el-divider />
        
        <el-form-item label="过期设置">
          <el-radio-group v-model="cookieForm.expire_option">
            <el-radio :label="'none'">永不过期</el-radio>
            <el-radio :label="'days'">设置过期天数</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="过期天数" v-if="cookieForm.expire_option === 'days'">
          <el-input-number v-model="cookieForm.expire_days" :min="1" :max="365" />
          <span class="form-tip">天后过期</span>
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
      title="临时封禁Cookie"
      width="400px"
      destroy-on-close
    >
      <el-form :model="tempBanForm" label-width="100px">
        <el-form-item label="Cookie名称">
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
      title="更新Cookie名称"
      width="400px"
      destroy-on-close
    >
      <el-form :model="updateIdForm" label-width="100px" :rules="updateIdRules" ref="updateIdFormRef">
        <el-form-item label="原Cookie名称">
          <el-tag>{{ updateIdForm.old_account_id }}</el-tag>
        </el-form-item>
        <el-form-item label="新Cookie名称" prop="new_account_id">
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
    
    <!-- 查看Cookie详情对话框 -->
    <el-dialog
      v-model="accountDetailDialogVisible"
      title="Cookie详情"
      width="700px"
      destroy-on-close
    >
      <div v-loading="accountDetailLoading">
        <el-descriptions border :column="2" v-if="accountDetail">
          <el-descriptions-item label="Cookie名" :span="2">{{ accountDetail.account_id }}</el-descriptions-item>
          <el-descriptions-item label="字段数量">{{ accountDetail.cookie_count }}</el-descriptions-item>
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
                <el-descriptions-item label="Cookie名称">{{ testResult.account_id }}</el-descriptions-item>
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
            <el-tab-pane label="有效Cookie">
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
                <el-empty v-if="!batchTestResult.valid_accounts.length" description="暂无有效Cookie" />
              </div>
            </el-tab-pane>
            <el-tab-pane label="被封禁Cookie">
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
                <el-empty v-if="!batchTestResult.banned_accounts.length" description="暂无被封禁Cookie" />
              </div>
            </el-tab-pane>
            <el-tab-pane label="未登录Cookie">
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
                
                <el-empty v-if="!batchTestResult.not_login_accounts.length" description="暂无未登录Cookie" />
              </div>
            </el-tab-pane>
          </el-tabs>
        </template>
        <el-empty v-else description="暂无测试结果" />
      </div>
    </el-dialog>
    
    <!-- 添加批量临时封禁对话框 -->
    <el-dialog
      v-model="batchTempBanDialogVisible"
      title="批量临时封禁Cookie"
      width="400px"
      destroy-on-close
    >
      <el-form :model="batchTempBanForm" label-width="100px">
        <el-form-item label="封禁时长">
          <el-input-number v-model="batchTempBanForm.duration_minutes" :min="1" :max="1440" />
          <span class="form-tip">分钟</span>
        </el-form-item>
        <el-form-item label="选中账号">
          <div class="selected-accounts">
            <el-tag
              v-for="item in multipleSelection"
              :key="item.account_id"
              size="small"
              class="mr-5 mb-5"
            >
              {{ item.account_id }}
            </el-tag>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="batchTempBanDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitBatchTempBan" :loading="batchActionLoading">
            确认
          </el-button>
        </div>
      </template>
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

.banned-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 10px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #ebeef5;
  margin-bottom: 10px;
}

.banned-checkbox {
  margin-right: 10px;
}

.banned-accounts {
  max-height: 500px;
  overflow-y: auto;
}

.banned-account-item {
  display: flex;
  align-items: flex-start;
  padding: 16px 15px;
  border-bottom: 1px solid #EBEEF5;
  gap: 15px;
}

.banned-account-item:last-child {
  border-bottom: none;
}

.banned-account-item:hover {
  background-color: #F5F7FA;
}

.banned-checkbox {
  margin-top: 8px;
  flex-shrink: 0;
}

.banned-checkbox :deep(.el-checkbox__label) {
  display: none;
}

.banned-account-info {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
  gap: 6px;
}

.account-id {
  font-weight: bold;
  font-size: 16px;
  color: #303133;
  line-height: 1.5;
  word-break: break-all;
  margin-bottom: 4px;
}

.ban-time {
  font-size: 13px;
  color: #67C23A;
  font-weight: 500;
  line-height: 1.6;
}

.ban-time-tooltip {
  font-size: 12px;
  color: #909399;
  line-height: 1.5;
}

.ban-status {
  font-size: 13px;
  color: #F56C6C;
  font-weight: 500;
  line-height: 1.6;
}

.banned-account-actions {
  flex-shrink: 0;
  margin-top: 4px;
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

.form-actions {
  display: flex;
  margin-top: 10px;
  gap: 10px;
  justify-content: flex-end;
}

.table-toolbar {
  margin-bottom: 10px;
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

.el-upload__tip {
  margin-top: 8px;
  color: #909399;
  line-height: 1.4;
}

.dialog-subtitle {
  margin: 0 0 15px 0;
  padding-bottom: 10px;
  font-size: 16px;
  border-bottom: 1px solid #EBEEF5;
  color: #409EFF;
}

.batch-actions {
  margin: 10px 0;
  display: flex;
  align-items: center;
}

.selection-info {
  margin-left: 15px;
  color: #606266;
  font-size: 14px;
}


.usage-chart-card {
  margin-bottom: 20px;
  border-radius: 8px;
}
.ml-10 {
  margin-left: 10px;
}

.mr-5 {
  margin-right: 5px;
}

.mb-5 {
  margin-bottom: 5px;
}

.selected-accounts {
  max-height: 100px;
  overflow-y: auto;
  padding: 5px;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
}
</style>