<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import * as XLSX from 'xlsx'
import { Delete, Search } from '@element-plus/icons-vue'

// 表单数据
const form = reactive({
  keywords: [],
  manualKeywords: '',
  timeRange: [],
  startYear: 2011,
  endYear: new Date().getFullYear(),
  cities: [],
  dataType: 'all',
  dataFrequency: 'week',
  dataSourceType: 'all',
  indexType: ['overall_avg'],
  isCustomTimeRange: false,
  selectedKeywords: []
})

// 关键词文件上传相关
const fileList = ref([])
const uploadRef = ref(null)
const keywordTableData = ref([])
const selectAll = ref(false)
const includeFirstRow = ref(false)

// 城市数据结构
const provinceList = ref([
  { value: 'all', label: '全国' },
  { value: 'beijing', label: '北京' },
  { value: 'tianjin', label: '天津' },
  { value: 'hebei', label: '河北' },
  { value: 'shanxi', label: '山西' },
  { value: 'neimenggu', label: '内蒙古' },
  { value: 'liaoning', label: '辽宁' },
  { value: 'jilin', label: '吉林' },
  { value: 'heilongjiang', label: '黑龙江' },
  { value: 'shanghai', label: '上海' },
  { value: 'jiangsu', label: '江苏' },
  { value: 'zhejiang', label: '浙江' },
  { value: 'anhui', label: '安徽' },
  { value: 'fujian', label: '福建' },
  { value: 'jiangxi', label: '江西' },
  { value: 'shandong', label: '山东' },
  { value: 'henan', label: '河南' },
  { value: 'hubei', label: '湖北' },
  { value: 'hunan', label: '湖南' },
  { value: 'guangdong', label: '广东' },
  { value: 'guangxi', label: '广西' },
  { value: 'hainan', label: '海南' },
  { value: 'chongqing', label: '重庆' },
  { value: 'sichuan', label: '四川' },
  { value: 'guizhou', label: '贵州' },
  { value: 'yunnan', label: '云南' },
  { value: 'xizang', label: '西藏' },
  { value: 'shaanxi', label: '陕西' },
  { value: 'gansu', label: '甘肃' },
  { value: 'qinghai', label: '青海' },
  { value: 'ningxia', label: '宁夏' },
  { value: 'xinjiang', label: '新疆' }
])

// 城市数据映射
const cityMap = {
  '1': '济南', '2': '贵阳', '4': '六盘水', '5': '南昌', '6': '九江', '7': '鹰潭', '8': '抚州',
  '9': '上饶', '10': '赣州', '11': '重庆', '13': '包头', '14': '鄂尔多斯', '15': '巴彦淖尔',
  '16': '乌海', '20': '呼和浩特', '21': '赤峰', '22': '通辽', '25': '呼伦贝尔', '28': '武汉',
  '29': '大连', '30': '黄石', '31': '荆州', '32': '襄阳', '33': '黄冈', '34': '荆门',
  '35': '宜昌', '36': '十堰', '37': '随州', '39': '鄂州', '40': '咸宁', '41': '孝感',
  '43': '长沙', '44': '岳阳', '45': '衡阳', '46': '株洲', '47': '湘潭', '48': '益阳',
  '49': '郴州', '50': '福州', '51': '莆田', '52': '三明', '53': '龙岩', '54': '厦门',
  '55': '泉州', '56': '漳州', '57': '上海', '59': '遵义', '66': '娄底', '67': '怀化',
  '68': '常德', '77': '青岛', '78': '烟台', '79': '临沂', '80': '潍坊', '81': '淄博',
  '82': '东营', '84': '菏泽', '85': '枣庄', '86': '德州', '87': '宁德', '88': '威海',
  '89': '柳州', '90': '南宁', '91': '桂林', '92': '贺州', '93': '贵港', '94': '深圳',
  '95': '广州', '96': '宜宾', '97': '成都', '98': '绵阳', '99': '广元', '100': '遂宁',
  '101': '巴中', '102': '内江', '103': '泸州', '104': '南充', '106': '德阳', '107': '乐山',
  '108': '广安', '109': '资阳', '111': '自贡', '112': '攀枝花', '113': '达州', '114': '雅安',
  '115': '吉安', '117': '昆明', '118': '玉林', '119': '河池', '123': '玉溪', '125': '南京',
  '126': '苏州', '127': '无锡', '128': '北海', '129': '钦州', '130': '防城港', '131': '百色',
  '132': '梧州', '133': '东莞', '134': '丽水', '135': '金华', '136': '萍乡', '137': '景德镇',
  '138': '杭州', '139': '西宁', '140': '银川', '141': '石家庄', '143': '衡水', '144': '张家口',
  '145': '承德', '146': '秦皇岛', '147': '廊坊', '148': '沧州', '149': '温州', '150': '沈阳',
  '151': '盘锦', '152': '哈尔滨', '153': '大庆', '154': '长春', '155': '四平', '156': '连云港',
  '157': '淮安', '158': '扬州', '159': '泰州', '161': '徐州', '162': '常州', '163': '南通',
  '164': '天津', '165': '西安', '166': '兰州', '168': '郑州', '169': '镇江', '172': '宿迁',
  '173': '铜陵', '174': '黄山', '175': '池州', '178': '淮南', '179': '宿州', '181': '六安',
  '182': '滁州', '183': '淮北', '184': '阜阳', '185': '马鞍山', '186': '安庆', '187': '蚌埠',
  '188': '芜湖', '189': '合肥', '191': '辽源', '194': '松原', '195': '云浮', '196': '佛山',
  '197': '湛江', '198': '江门', '199': '惠州', '200': '珠海', '201': '韶关', '202': '阳江',
  '203': '茂名', '204': '潮州', '205': '揭阳', '207': '中山', '208': '清远', '209': '肇庆',
  '210': '河源', '211': '梅州', '212': '汕头', '213': '汕尾', '215': '鞍山', '216': '朝阳',
  '217': '锦州', '218': '铁岭', '219': '丹东', '220': '本溪', '221': '营口', '222': '抚顺',
  '223': '阜新', '224': '辽阳', '225': '葫芦岛', '226': '张家界', '228': '长治', '229': '忻州',
  '230': '晋中', '235': '朔州', '236': '阳泉', '237': '吕梁', '239': '海口', '243': '三亚',
  '246': '新余', '253': '南平', '256': '宜春', '259': '保定', '261': '唐山', '262': '南阳',
  '263': '新乡', '264': '开封', '265': '焦作', '266': '平顶山', '268': '许昌', '269': '永州',
  '270': '吉林', '271': '铜川', '272': '安康', '273': '宝鸡', '274': '商洛', '275': '渭南',
  '276': '汉中', '277': '咸阳', '278': '榆林', '282': '定西', '283': '武威', '284': '酒泉',
  '285': '张掖', '286': '嘉峪关', '287': '台州', '288': '衢州', '289': '宁波', '291': '眉山',
  '292': '邯郸', '293': '邢台', '295': '伊春', '300': '黑河', '301': '鹤岗', '302': '七台河',
  '303': '绍兴', '304': '嘉兴', '305': '湖州', '306': '舟山', '307': '平凉', '308': '天水',
  '309': '白银', '317': '克拉玛依', '319': '齐齐哈尔', '320': '佳木斯', '322': '牡丹江',
  '323': '鸡西', '324': '绥化', '335': '昭通', '339': '曲靖', '342': '丽江', '343': '金昌',
  '344': '陇南', '350': '临沧', '352': '济宁', '353': '泰安', '359': '双鸭山', '366': '日照',
  '370': '安阳', '371': '驻马店', '373': '信阳', '374': '鹤壁', '375': '周口', '376': '商丘',
  '378': '洛阳', '379': '漯河', '380': '濮阳', '381': '三门峡', '391': '亳州', '395': '吴忠',
  '396': '固原', '401': '延安', '405': '邵阳', '407': '通化', '408': '白山', '422': '铜仁',
  '424': '安顺', '426': '毕节', '438': '保山', '466': '拉萨', '467': '乌鲁木齐', '472': '石嘴山',
  '480': '中卫', '506': '来宾', '514': '北京', '665': '崇左', '666': '普洱', '0': '全国'
}

// 城市与省份的映射关系
const cityProvinceMap = {
  '0': 'all', // 全国
  '514': 'beijing', // 北京
  '164': 'tianjin', // 天津
  '141': 'hebei', '143': 'hebei', '144': 'hebei', '145': 'hebei', '146': 'hebei', '147': 'hebei', '148': 'hebei', '259': 'hebei', '261': 'hebei', '292': 'hebei', '293': 'hebei',
  // ... 其他城市与省份的映射关系
}

// 按省份分组的城市列表
const citiesByProvince = ref({})
const selectedProvince = ref('all')

// 加载城市数据并按省份分组
const loadCitiesGroupByProvince = () => {
  // 创建省份和城市的映射
  const provinceMap = {}
  
  // 遍历城市，按省份分组
  Object.keys(cityMap).forEach(cityId => {
    const provinceName = cityProvinceMap[cityId] || 'other'
    if (!provinceMap[provinceName]) {
      provinceMap[provinceName] = []
    }
    
    provinceMap[provinceName].push({
      value: cityId,
      label: cityMap[cityId]
    })
  })
  
  citiesByProvince.value = provinceMap
}

// 城市数据
const allCities = computed(() => {
  if (selectedProvince.value === 'all') {
    return [{ value: '0', label: '全国' }]
  } else {
    return citiesByProvince.value[selectedProvince.value] || []
  }
})

const cityLoading = ref(false)
const citySearchKeyword = ref('')

// 计算属性
const filteredCities = computed(() => {
  if (selectedProvince.value === 'all') return []
  
  const cities = citiesByProvince.value[selectedProvince.value] || []
  
  if (!citySearchKeyword.value.trim()) {
    return cities
  }
  
  return cities.filter(city => 
    city.label.toLowerCase().includes(citySearchKeyword.value.toLowerCase())
  )
})

const isAllCitiesSelected = computed(() => {
  if (selectedProvince.value === 'all' || !citiesByProvince.value[selectedProvince.value]) {
    return false
  }
  
  const currentProvinceCities = citiesByProvince.value[selectedProvince.value].map(city => city.value)
  return currentProvinceCities.every(cityId => form.cities.includes(cityId))
})

const canUseDaily = computed(() => {
  if (form.isCustomTimeRange) {
    if (!form.timeRange || form.timeRange.length !== 2) return false
    const startDate = new Date(form.timeRange[0])
    const endDate = new Date(form.timeRange[1])
    const diff = Math.abs(endDate - startDate) / (1000 * 60 * 60 * 24 * 365)
    return diff <= 1
  } else {
    return form.endYear - form.startYear <= 1
  }
})

// 获取当前年份
const currentYear = new Date().getFullYear()
const yearRange = computed(() => {
  return Array.from({ length: currentYear - 2010 }, (_, i) => 2011 + i)
})

const endYearRange = computed(() => {
  return Array.from({ length: currentYear - form.startYear + 1 }, (_, i) => form.startYear + i)
})

// 指数类型全选
const indexTypes = [
  { label: 'overall_avg', name: '整体日均值' },
  { label: 'mobile_avg', name: '移动日均值' },
  { label: 'overall_yoy', name: '整体同比' },
  { label: 'overall_qoq', name: '整体环比' },
  { label: 'mobile_yoy', name: '移动同比' },
  { label: 'mobile_qoq', name: '移动环比' }
]

const isAllIndexTypesSelected = computed(() => {
  return form.indexType.length === indexTypes.length
})

const toggleAllIndexTypes = () => {
  if (isAllIndexTypesSelected.value) {
    form.indexType = []
  } else {
    form.indexType = indexTypes.map(type => type.label)
  }
}

// 关键词表格相关
const updateKeywordTable = () => {
  keywordTableData.value = form.keywords.map((keyword, index) => ({
    id: index + 1,
    keyword,
    selected: form.selectedKeywords.includes(keyword)
  }))
}

// 方法
const handleKeywordFileUpload = (file) => {
  const reader = new FileReader()
  
  reader.onload = (e) => {
    if (!e.target) return
    
    try {
      const data = e.target.result
      const filename = file.name.toLowerCase()
      let keywords = []
      
      // 根据文件类型处理
      if (filename.endsWith('.xlsx') || filename.endsWith('.xls')) {
        // Excel文件
        const workbook = XLSX.read(data, { type: 'array' })
        const firstSheet = workbook.Sheets[workbook.SheetNames[0]]
        const rows = XLSX.utils.sheet_to_json(firstSheet, { header: 1 })
        
        // 如果不包含首行，则跳过第一行
        if (!includeFirstRow.value && rows.length > 0) {
          rows.shift()
        }
        
        // 提取每行第一列作为关键词
        keywords = rows.map(row => row[0]?.toString().trim()).filter(Boolean)
      } else if (filename.endsWith('.csv') || filename.endsWith('.txt')) {
        // CSV/TXT文件
        const text = new TextDecoder().decode(data instanceof ArrayBuffer ? new Uint8Array(data) : data)
        const lines = text.split(/\r?\n/).filter(Boolean)
        
        // 如果不包含首行，则跳过第一行
        if (!includeFirstRow.value && lines.length > 0) {
          lines.shift()
        }
        
        keywords = lines.map(line => {
          // 对于CSV，只取第一列
          if (filename.endsWith('.csv')) {
            return line.split(',')[0]?.trim()
          }
          return line.trim()
        }).filter(Boolean)
      } else if (filename.endsWith('.json')) {
        // JSON文件
        const text = new TextDecoder().decode(data instanceof ArrayBuffer ? new Uint8Array(data) : data)
        const jsonData = JSON.parse(text)
        
        // 处理JSON数据，支持多种格式
        if (Array.isArray(jsonData)) {
          // 如果是数组，直接使用或提取关键词字段
          if (typeof jsonData[0] === 'string') {
            // ["关键词1", "关键词2", ...]
            keywords = jsonData
          } else if (typeof jsonData[0] === 'object') {
            // [{"关键词": "值"}, {"关键词": "值"}, ...]
            // 尝试常见的字段名称
            const possibleFields = ['keyword', 'name', 'text', 'value', 'title', 'term', '关键词']
            const keyField = possibleFields.find(field => jsonData[0][field] !== undefined) || Object.keys(jsonData[0])[0]
            keywords = jsonData.map(item => item[keyField]?.toString().trim()).filter(Boolean)
          }
        } else if (typeof jsonData === 'object') {
          // 如果是对象，尝试提取值
          keywords = Object.values(jsonData).map(val => val?.toString().trim()).filter(Boolean)
        }
        
        // 如果不包含首行，则跳过第一个关键词
        if (!includeFirstRow.value && keywords.length > 0) {
          keywords.shift()
        }
      }
      
      // 添加不重复的关键词
      let addedCount = 0
      for (const keyword of keywords) {
        if (keyword && !form.keywords.includes(keyword)) {
          form.keywords.push(keyword)
          addedCount++
        }
      }
      
      // 更新表格数据
      updateKeywordTable()
      
      ElMessage.success(`成功从文件添加 ${addedCount} 个关键词`)
    } catch (error) {
      console.error('文件解析失败:', error)
      ElMessage.error('文件解析失败，请检查文件格式')
    }
    
    // 清空文件列表，允许重新上传
    fileList.value = []
  }
  
  reader.readAsArrayBuffer(file.raw)
  return false // 阻止自动上传
}

const handleManualKeywords = () => {
  if (!form.manualKeywords.trim()) return
  
  const newKeywords = form.manualKeywords
    .split(/[\n,，;；\s]+/)
    .filter(Boolean)
    .map(k => k.trim())
  
  form.keywords = [...new Set([...form.keywords, ...newKeywords])]
  form.manualKeywords = ''
  
  // 更新关键词表格
  updateKeywordTable()
  
  ElMessage.success(`成功添加 ${newKeywords.length} 个关键词`)
}

const removeKeyword = (keyword) => {
  const index = form.keywords.indexOf(keyword)
  if (index !== -1) {
    form.keywords.splice(index, 1)
    
    // 从已选中的关键词中也删除
    const selectedIndex = form.selectedKeywords.indexOf(keyword)
    if (selectedIndex !== -1) {
      form.selectedKeywords.splice(selectedIndex, 1)
    }
    
    // 更新关键词表格
    updateKeywordTable()
  }
}

const handleSelectAllKeywords = () => {
  selectAll.value = !selectAll.value
  
  if (selectAll.value) {
    form.selectedKeywords = [...form.keywords]
  } else {
    form.selectedKeywords = []
  }
  
  // 更新表格数据的选中状态
  keywordTableData.value.forEach(item => {
    item.selected = selectAll.value
  })
}

const handleKeywordSelect = (keyword, selected) => {
  if (selected) {
    if (!form.selectedKeywords.includes(keyword)) {
      form.selectedKeywords.push(keyword)
    }
  } else {
    const index = form.selectedKeywords.indexOf(keyword)
    if (index !== -1) {
      form.selectedKeywords.splice(index, 1)
    }
  }
}

const handleDeleteSelectedKeywords = () => {
  if (form.selectedKeywords.length === 0) {
    ElMessage.warning('请先选择要删除的关键词')
    return
  }
  
  ElMessageBox.confirm(`确定要删除选中的 ${form.selectedKeywords.length} 个关键词吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    form.keywords = form.keywords.filter(keyword => !form.selectedKeywords.includes(keyword))
    form.selectedKeywords = []
    updateKeywordTable()
    ElMessage.success('删除成功')
  }).catch(() => {
    // 用户取消操作
  })
}

const selectAllCities = () => {
  if (selectedProvince.value === 'all') return
  
  const currentProvinceCities = citiesByProvince.value[selectedProvince.value].map(city => city.value)
  
  if (isAllCitiesSelected.value) {
    // 取消全选，从已选城市中移除当前省份所有城市
    form.cities = form.cities.filter(cityId => !currentProvinceCities.includes(cityId))
  } else {
    // 全选，添加当前省份所有未选城市
    for (const cityId of currentProvinceCities) {
      if (!form.cities.includes(cityId)) {
        form.cities.push(cityId)
      }
    }
    // 如果有全国，则移除
    if (form.cities.includes('0')) {
      form.cities = form.cities.filter(id => id !== '0')
    }
  }
}

const handleClearCities = () => {
  form.cities = []
}

const handleProvinceChange = () => {
  citySearchKeyword.value = ''
}

const setYearRange = () => {
  if (!form.startYear || !form.endYear) return
  
  const startDate = new Date(form.startYear, 0, 1)
  const endDate = new Date(form.endYear, 11, 31)
  form.timeRange = [startDate, endDate]
}

const validateForm = () => {
  if (form.keywords.length === 0) {
    ElMessage.warning('请至少添加一个关键词')
    return false
  }
  
  if (!form.timeRange || !form.timeRange[0] || !form.timeRange[1]) {
    ElMessage.warning('请选择时间范围')
    return false
  }
  
  if (form.cities.length === 0) {
    ElMessage.warning('请至少选择一个城市')
    return false
  }
  
  if (form.indexType.length === 0) {
    ElMessage.warning('请至少选择一种指数类型')
    return false
  }
  
  return true
}

const submitForm = async () => {
  if (!validateForm()) return
  
  // 确认对话框
  try {
    await ElMessageBox.confirm(
      `您将开始采集 ${form.keywords.length} 个关键词、${form.cities.length} 个城市的数据，是否继续？`,
      '确认采集',
      {
        confirmButtonText: '开始采集',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    
    // 用户确认，开始采集
    startCollection()
  } catch {
    // 用户取消，不执行任何操作
  }
}

const startCollection = async () => {
  ElMessage.success('开始采集数据，请在任务管理中查看进度')
  
  // 这里应该调用后端API来启动采集任务
  // 在实际应用中，这里会发送采集请求到后端
  console.log('采集表单数据:', form)
  
  /*
  try {
    const response = await axios.post('/api/collection/start', {
      keywords: form.keywords,
      startDate: form.timeRange[0],
      endDate: form.timeRange[1],
      cities: form.cities,
      dataType: form.dataType,
      dataFrequency: form.dataFrequency,
      dataSourceType: form.dataSourceType,
      indexType: form.indexType
    })
    
    console.log('API响应:', response.data)
  } catch (error) {
    ElMessage.error('启动采集任务失败')
    console.error('API错误:', error)
  }
  */
}

// 生命周期钩子
onMounted(() => {
  loadCitiesGroupByProvince()
  setYearRange() // 设置默认年份范围
})

// 处理城市数据转换为级联选择需要的格式
const provinceOptions = computed(() => {
  // 全国选项单独处理
  const options = [
    {
      value: 'all',
      label: '全国',
      children: [{ value: '0', label: '全国' }]
    }
  ]
  
  // 添加各省份及其城市
  provinceList.value.forEach(province => {
    if (province.value !== 'all') {
      const cities = citiesByProvince.value[province.value] || []
      options.push({
        value: province.value,
        label: province.label,
        children: cities.length > 0 ? cities : []
      })
    }
  })
  
  return options
})

// 处理级联选择的输出，确保只有城市被选中
const handleCascaderChange = (values) => {
  // 过滤掉所有省级选项
  const provinceValues = provinceList.value.map(p => p.value)
  form.cities = values.filter(val => !provinceValues.includes(val))
  
  // 强制更新视图
  setTimeout(() => {
    updateSelectedCities()
  }, 0)
}

// 更新已选城市的视图
const updateSelectedCities = () => {
  // 用于强制更新视图
  form.cities = [...form.cities]
}

// 根据城市ID获取城市名称
const getCityName = (cityId) => {
  return cityMap[cityId] || cityId
}

// 从已选城市中移除指定城市
const removeCity = (cityId) => {
  const index = form.cities.indexOf(cityId)
  if (index !== -1) {
    form.cities.splice(index, 1)
  }
}

// 开始年份变更时的逻辑
const handleStartYearChange = () => {
  // 如果结束年份小于开始年份，自动更新结束年份为开始年份
  if (form.endYear < form.startYear) {
    form.endYear = form.startYear
  }
  setYearRange()
}

// 增加城市选择的方法
const isCitySelected = (cityId) => {
  return form.cities.includes(cityId)
}

const toggleCitySelection = (cityId) => {
  const index = form.cities.indexOf(cityId)
  if (index === -1) {
    // 添加城市
    form.cities.push(cityId)
  } else {
    // 移除城市
    form.cities.splice(index, 1)
  }
}

const selectCity = (cityId) => {
  // 如果是全国，则清空其他选择，只选择全国
  if (cityId === '0') {
    form.cities = ['0']
  } 
  // 如果当前包含全国，但要选择其他城市，则移除全国
  else if (form.cities.includes('0')) {
    form.cities = form.cities.filter(id => id !== '0')
    form.cities.push(cityId)
  }
  // 否则正常添加
  else if (!form.cities.includes(cityId)) {
    form.cities.push(cityId)
  }
}

// 重置表单
const resetForm = () => {
  form.keywords = []
  form.manualKeywords = ''
  form.timeRange = []
  form.startYear = 2011
  form.endYear = new Date().getFullYear()
  form.cities = []
  form.dataType = 'all'
  form.dataFrequency = 'week'
  form.dataSourceType = 'all'
  form.indexType = ['overall_avg']
  form.isCustomTimeRange = false
  form.selectedKeywords = []
  
  // 重置关键词表格
  updateKeywordTable()
  setYearRange()
}

const handleSelectAllCities = () => {
  // 获取所有非全国城市ID
  const allCityIds = Object.keys(cityMap).filter(id => id !== '0')
  
  // 如果当前已经全选了，则清空
  if (form.cities.length === allCityIds.length) {
    form.cities = []
  } else {
    // 否则全选所有城市
    form.cities = [...allCityIds]
  }
}
</script>

<template>
  <div class="data-collection-container">
    <h1 class="page-title">数据采集</h1>
    
    <el-card class="collection-form-card">
      <el-form :model="form" label-position="top">
        <!-- 关键词选择 -->
        <el-form-item label="关键词">
          <div class="keyword-section">
            <div class="keyword-input">
              <el-input
                v-model="form.manualKeywords"
                type="textarea"
                :rows="4"
                placeholder="输入关键词，用逗号、空格或换行分隔"
              ></el-input>
              <el-button type="primary" @click="handleManualKeywords">添加关键词</el-button>
            </div>
            
            <div class="keyword-upload">
              <div class="upload-options">
                <el-checkbox v-model="includeFirstRow">包含首行</el-checkbox>
              </div>
              <el-upload
                ref="uploadRef"
                class="upload-demo"
                :auto-upload="false"
                :limit="1"
                :file-list="fileList"
                :on-change="handleKeywordFileUpload"
                accept=".xlsx,.xls,.csv,.txt,.json"
              >
                <template #trigger>
                  <el-button type="primary">选择文件</el-button>
                </template>
                <template #tip>
                  <div class="el-upload__tip">
                    支持Excel、CSV、TXT、JSON格式，每行一个关键词
                  </div>
                </template>
              </el-upload>
            </div>
          </div>
          
          <!-- 关键词表格 - 横向卡片布局 -->
          <div v-if="form.keywords.length > 0" class="keyword-cards-section">
            <div class="keyword-cards-header">
              <div class="cards-title">已添加的关键词 ({{ form.keywords.length }})</div>
              <div class="cards-actions">
                <el-button
                  type="primary"
                  size="small"
                  @click="handleSelectAllKeywords"
                >
                  {{ selectAll ? '取消全选' : '全选' }}
                </el-button>
                <el-button
                  type="danger"
                  size="small"
                  @click="handleDeleteSelectedKeywords"
                  :disabled="form.selectedKeywords.length === 0"
                >
                  批量删除 ({{ form.selectedKeywords.length }})
                </el-button>
              </div>
            </div>
            
            <div class="keyword-cards-container">
              <div v-for="(keyword, index) in form.keywords" :key="index" class="keyword-card">
                <div class="keyword-card-content">
                  <el-checkbox
                    v-model="form.selectedKeywords" 
                    :label="keyword"
                  ></el-checkbox>
                  <div class="keyword-text" :title="keyword">{{ keyword }}</div>
                  <el-button
                    type="danger"
                    size="small"
                    circle
                    @click="removeKeyword(keyword)"
                  >
                    <el-icon><Delete /></el-icon>
                  </el-button>
                </div>
              </div>
            </div>
          </div>
          
          <div v-else class="no-keywords">
            暂无关键词，请添加或上传
          </div>
        </el-form-item>
        
        <!-- 时间范围选择 -->
        <el-form-item label="时间范围">
          <div class="time-range-selection">
            <el-radio-group v-model="form.isCustomTimeRange" class="time-range-type">
              <el-radio :label="false">按年份选择</el-radio>
              <el-radio :label="true">自定义日期范围</el-radio>
            </el-radio-group>
            
            <div v-if="!form.isCustomTimeRange" class="year-selection">
              <el-form-item label="开始年份">
                <el-select v-model="form.startYear" placeholder="开始年份" @change="handleStartYearChange" class="year-select">
                  <el-option
                    v-for="year in yearRange"
                    :key="year"
                    :label="year"
                    :value="year"
                  ></el-option>
                </el-select>
              </el-form-item>
              
              <el-form-item label="结束年份">
                <el-select v-model="form.endYear" placeholder="结束年份" @change="setYearRange" class="year-select">
                  <el-option
                    v-for="year in endYearRange"
                    :key="year"
                    :label="year"
                    :value="year"
                  ></el-option>
                </el-select>
              </el-form-item>
            </div>
            
            <div v-else class="custom-date-range">
              <el-date-picker
                v-model="form.timeRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              ></el-date-picker>
            </div>
          </div>
        </el-form-item>
        
        <!-- 城市选择 - 增加全选所有城市选项 -->
        <el-form-item label="城市选择">
          <div class="city-selection-container">
            <!-- 城市选择标签页 -->
            <div class="city-tabs">
              <div class="global-city-actions">
                <el-button type="primary" @click="selectCity('0')">选择全国</el-button>
                <el-button type="primary" @click="handleSelectAllCities">
                  {{ form.cities.length === Object.keys(cityMap).length - 1 ? '取消全选城市' : '全选所有城市' }}
                </el-button>
                <el-button @click="handleClearCities" :disabled="!form.cities.length">
                  清空
                </el-button>
              </div>
              
              <el-tabs v-model="selectedProvince" @tab-click="handleProvinceChange">
                <el-tab-pane label="全国总览" name="all">
                  <div class="city-selection-actions">
                    <el-button size="small" type="primary" @click="selectCity('0')">全国</el-button>
                  </div>
                </el-tab-pane>
                
                <el-tab-pane v-for="province in provinceList.filter(p => p.value !== 'all')" 
                            :key="province.value" 
                            :label="province.label" 
                            :name="province.value">
                  <div class="city-selection-actions">
                    <el-input
                      v-model="citySearchKeyword"
                      placeholder="搜索城市"
                      prefix-icon="Search"
                      clearable
                      class="city-search"
                    ></el-input>
                    <el-button size="small" type="primary" @click="selectAllCities">
                      {{ isAllCitiesSelected ? '取消全选' : '全选' }}
                    </el-button>
                    <el-button size="small" @click="handleClearCities" :disabled="!form.cities.length">
                      清空
                    </el-button>
                  </div>
                  
                  <div class="city-button-group">
                    <el-button
                      v-for="city in filteredCities"
                      :key="city.value"
                      size="small"
                      :type="isCitySelected(city.value) ? 'primary' : ''"
                      @click="toggleCitySelection(city.value)"
                      class="city-button"
                    >
                      {{ city.label }}
                    </el-button>
                  </div>
                </el-tab-pane>
              </el-tabs>
            </div>
            
            <!-- 已选择的城市 -->
            <div class="selected-cities" v-if="form.cities.length > 0">
              <div class="selected-cities-title">已选择 {{ form.cities.length }} 个城市：</div>
              <div class="selected-cities-tags">
                <el-tag 
                  v-for="cityId in form.cities" 
                  :key="cityId"
                  closable
                  @close="removeCity(cityId)"
                  class="city-tag"
                >
                  {{ getCityName(cityId) }}
                </el-tag>
              </div>
            </div>
            
            <div v-else class="no-cities">
              暂未选择城市，请从上方选择
            </div>
          </div>
        </el-form-item>
        
        <!-- 数据类型选择 -->
        <el-form-item label="数据频率">
          <el-radio-group v-model="form.dataFrequency">
            <el-radio label="day" :disabled="!canUseDaily">日度数据</el-radio>
            <el-radio label="week">周度数据</el-radio>
          </el-radio-group>
          <div v-if="!canUseDaily && form.dataFrequency === 'day'" class="frequency-warning">
            <el-alert
              title="日度数据仅支持一年以内的时间范围"
              type="warning"
              :closable="false"
              show-icon
            ></el-alert>
          </div>
        </el-form-item>
        
        <el-form-item label="终端类型">
          <el-radio-group v-model="form.dataSourceType">
            <el-radio label="all">PC+移动端</el-radio>
            <el-radio label="pc">PC端</el-radio>
            <el-radio label="mobile">移动端</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="指数类型">
          <div class="index-type-header">
            <el-button type="primary" link @click="toggleAllIndexTypes">
              {{ isAllIndexTypesSelected ? '取消全选' : '全选' }}
            </el-button>
          </div>
          <el-checkbox-group v-model="form.indexType" class="index-type-group">
            <el-checkbox v-for="type in indexTypes" :key="type.label" :label="type.label">
              {{ type.name }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        
        <el-form-item label="数据类型">
          <el-radio-group v-model="form.dataType">
            <el-radio label="all">全部类型</el-radio>
            <el-radio label="trend">趋势研究</el-radio>
            <el-radio label="map">需求图谱</el-radio>
            <el-radio label="portrait">人群画像</el-radio>
            <el-radio label="news">资讯指数</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <!-- 提交按钮 -->
        <el-form-item>
          <div class="form-actions">
            <el-button type="primary" @click="submitForm" size="large">开始采集</el-button>
            <el-button @click="resetForm" size="large">重置</el-button>
          </div>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.data-collection-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 25px;
  background-color: #f7fafd;
  min-height: 100vh;
}

.page-title {
  font-size: 2.2rem;
  margin-bottom: 30px;
  color: #2c3e50;
  font-weight: 600;
  position: relative;
  padding-bottom: 15px;
  text-align: center;
  letter-spacing: 1px;
}

.page-title::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 80px;
  height: 4px;
  background: linear-gradient(90deg, #409eff, #67c23a);
  border-radius: 2px;
}

.collection-form-card {
  margin-bottom: 40px;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: box-shadow 0.3s ease;
}

.collection-form-card:hover {
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.15);
}

.keyword-section {
  display: flex;
  gap: 25px;
  margin-bottom: 25px;
}

.keyword-input {
  flex: 2;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.keyword-upload {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  background-color: #f9fafc;
  padding: 15px;
  border-radius: 8px;
  border: 1px dashed #dcdfe6;
}

.keyword-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
}

.keyword-tag {
  margin-right: 5px;
}

.no-keywords {
  color: #909399;
  font-style: italic;
  margin-top: 15px;
  text-align: center;
  padding: 30px;
  border: 1px dashed #dcdfe6;
  border-radius: 8px;
  background-color: #fcfcfc;
}

.keyword-cards-section {
  margin-top: 25px;
}

.keyword-cards-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding: 0 10px;
}

.cards-title {
  font-weight: 600;
  font-size: 16px;
  color: #2c3e50;
}

.cards-actions {
  display: flex;
  gap: 12px;
}

.keyword-cards-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 15px;
  max-height: 320px;
  overflow-y: auto;
  padding: 15px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  background-color: #f9fafc;
  scrollbar-width: thin;
}

.keyword-cards-container::-webkit-scrollbar {
  width: 8px;
}

.keyword-cards-container::-webkit-scrollbar-thumb {
  background-color: #c0c4cc;
  border-radius: 4px;
}

.keyword-cards-container::-webkit-scrollbar-track {
  background-color: #f9fafc;
}

.keyword-card {
  background-color: #fff;
  border-radius: 8px;
  padding: 12px 15px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  transition: all 0.3s ease;
  border: 1px solid #ebeef5;
}

.keyword-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.keyword-card-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.keyword-text {
  flex-grow: 1;
  margin: 0 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #303133;
  font-size: 14px;
}

.global-city-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  padding: 15px;
  background-color: #ecf5ff;
  border-radius: 8px;
  border: 1px solid #d9ecff;
}

.time-range-selection {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.time-range-type {
  margin-bottom: 15px;
}

.year-selection {
  display: flex;
  gap: 30px;
}

.year-select {
  width: 200px;
}

.province-select,
.city-search {
  width: 100%;
}

.city-selection-container {
  width: 100%;
}

.city-selection-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 15px;
  align-items: center;
}

.city-search {
  width: 250px;
}

.city-button-group {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 15px;
}

.city-button {
  margin-right: 0;
}

.city-tabs {
  margin-bottom: 20px;
  border-radius: 8px;
  padding: 15px;
  background-color: #f9fafc;
  border: 1px solid #e4e7ed;
}

.upload-options {
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
}

.el-form-item__label {
  font-weight: 600;
  font-size: 16px;
  color: #303133;
  margin-bottom: 8px;
}

.el-card__body {
  padding: 30px;
}

.no-cities, .loading-cities {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 120px;
  color: #909399;
  background-color: #fcfcfc;
  border: 1px dashed #dcdfe6;
  border-radius: 8px;
}

.loading-cities {
  display: flex;
  align-items: center;
  gap: 10px;
}

.index-type-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.index-type-group {
  display: flex;
  flex-wrap: wrap;
  gap: 25px;
  padding: 15px;
  background-color: #f9fafc;
  border-radius: 8px;
}

.frequency-warning {
  margin-top: 15px;
}

.form-actions {
  display: flex;
  justify-content: center;
  gap: 25px;
  margin-top: 30px;
}

.form-actions .el-button {
  min-width: 150px;
  padding: 12px 20px;
  font-size: 16px;
}

@media (max-width: 768px) {
  .keyword-section {
    flex-direction: column;
  }
  
  .year-selection {
    flex-direction: column;
  }
  
  .city-selection-actions {
    flex-direction: column;
    align-items: stretch;
  }
  
  .city-selection-buttons {
    margin-top: 10px;
  }
  
  .form-actions {
    flex-direction: column;
  }
}

.selected-cities {
  margin-top: 20px;
}

.selected-cities-title {
  font-weight: 600;
  margin-bottom: 12px;
  color: #303133;
}

.selected-cities-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 15px;
  background-color: #f9fafc;
  border-radius: 8px;
  border: 1px solid #ebeef5;
}

.city-tag {
  margin-right: 0;
  transition: all 0.2s ease;
}

.city-tag:hover {
  transform: translateY(-2px);
}

:deep(.el-tabs__item) {
  font-size: 15px;
  padding: 0 20px;
}

:deep(.el-tabs__active-bar) {
  height: 3px;
}
</style> 