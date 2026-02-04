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

// 临时兜底函数，防止找不到 $t 报错
const $t = (key: string) => {
  const map = {
    'views.cookiemanager.cslk87': 'Cookie管理',
    'views.cookiemanager.s8b3r4': 'API已连接',
    'views.cookiemanager.ryfkc7': 'API未连接',
    'views.cookiemanager.584l78': 'Cookie池状态',
    'views.cookiemanager.p3kgye': '刷新',
    'views.cookiemanager.u72yh2': '添加Cookie',
    'views.cookiemanager.elw1fx': '总数',
    'views.cookiemanager.8qgc3r': '可用',
    'views.cookiemanager.5t0x50': '临时封禁',
    'views.cookiemanager.e6y884': '永久封禁',
    'views.cookiemanager.1u4sy2': '测试全部',
    'views.cookiemanager.dl2a0c': '更新状态',
    'views.cookiemanager.rq4zij': '清理过期',
    'views.cookiemanager.nlb473': '可用账号列表',
    'views.cookiemanager.vne764': '测试',
    'views.cookiemanager.s2tp53': '操作',
    'views.cookiemanager.x4jo6h': '查看详情',
    'views.cookiemanager.ee2q48': '更新ID',
    'views.cookiemanager.115uyi': '删除',
    'views.cookiemanager.61po6w': '封禁账号管理',
    'views.cookiemanager.8st7lh': '全选',
    'views.cookiemanager.d5714o': '批量解封',
    'views.cookiemanager.j33j3w': '解封全部',
    'views.cookiemanager.92zl33': '剩余时间: ',
    'views.cookiemanager.mf8dc8': '解封',
    'views.cookiemanager.ns9cp5': '批量强制解封',
    'views.cookiemanager.sk5fy0': '强制解封全部',
    'views.cookiemanager.8etq8j': '强制解封',
    'views.cookiemanager.47kxcu': 'Cookie详细列表',
    'views.cookiemanager.278g1g': '同步到Redis',
    'views.cookiemanager.y9p7s8': '更新ab_sr',
    'views.cookiemanager.33q43q': '搜索账号ID',
    'views.cookiemanager.37b4p5': '筛选状态',
    'views.cookiemanager.81u723': '已过期',
    'views.cookiemanager.1209y9': '搜索',
    'views.cookiemanager.7cu76x': '重置',
    'views.cookiemanager.t4da2e': '添加Cookie',
    'views.cookiemanager.psm0p5': '全部临时封禁',
    'views.cookiemanager.d3v4ch': '全部解封',
    'views.cookiemanager.8v7qie': '批量临时封禁',
    'views.cookiemanager.87x3w7': '批量永久封禁',
    'views.cookiemanager.sh12bf': '已选择 ',
    'views.cookiemanager.epnr2i': ' 个账号',
    'views.cookiemanager.fr15xl': '账号ID',
    'views.cookiemanager.oz57n9': '数量',
    'views.cookiemanager.q28nq7': 'Cookie值',
    'views.cookiemanager.w5f1e1': '状态',
    'views.cookiemanager.8j8u6u': '过期时间',
    'views.cookiemanager.c805dh': '永不过期',
    'views.cookiemanager.f46go7': '编辑',
    'views.cookiemanager.881jd7': 'Cookie使用量趋势',
    'views.cookiemanager.2623i5': '编辑Cookie',
    'views.cookiemanager.3xcu12': '账号ID',
    'views.cookiemanager.th42gs': '请输入账号ID',
    'views.cookiemanager.b34o26': '字符串模式',
    'views.cookiemanager.uk514y': 'Cookie字符串',
    'views.cookiemanager.gd2jp8': '格式: name1=value1; name2=value2',
    'views.cookiemanager.fva0k0': 'JSON模式',
    'views.cookiemanager.87v8fc': '请输入标准的JSON格式',
    'views.cookiemanager.4883c4': '格式化',
    'views.cookiemanager.hixo3o': '字符串转JSON',
    'views.cookiemanager.kr35u8': '表格模式',
    'views.cookiemanager.n1j1b9': '添加字段',
    'views.cookiemanager.qr83x8': '清空字段',
    'views.cookiemanager.g4qpr8': '键名',
    'views.cookiemanager.1p02i5': '键值',
    'views.cookiemanager.72nhk1': '生成JSON',
    'views.cookiemanager.94620b': 'JSON转表格',
    'views.cookiemanager.6u74s1': '批量导入',
    'views.cookiemanager.v75iyb': '导入格式',
    'views.cookiemanager.7n8765': '选择文件类型',
    'views.cookiemanager.y0on43': '文本文件 (.txt)',
    'views.cookiemanager.oj2848': 'JSON文件 (.json)',
    'views.cookiemanager.0kmv3e': 'CSV文件 (.csv)',
    'views.cookiemanager.33ufz3': 'Excel文件 (.xlsx)',
    'views.cookiemanager.7y1v98': '选择文件',
    'views.cookiemanager.41x3g4': '点击上传',
    'views.cookiemanager.vf7cx7': '支持 txt, json, csv, excel 格式',
    'views.cookiemanager.2y13xa': '处理并预览',
    'views.cookiemanager.23tt1n': '导入预览',
    'views.cookiemanager.f13q7e': '确认导入',
    'views.cookiemanager.5c03y1': '取消导入',
    'views.cookiemanager.6wj7ss': '过期设置',
    'views.cookiemanager.7hkyhk': '设置过期天数',
    'views.cookiemanager.36h81u': '过期天数',
    'views.cookiemanager.ud3t6n': '天后自动标记为过期',
    'views.cookiemanager.w0o3pl': '是否可用',
    'views.cookiemanager.jxt47y': '不可用',
    'views.cookiemanager.6cqov8': '永久封禁中',
    'views.cookiemanager.237n2f': '正常',
    'views.cookiemanager.1psc3j': '临时封禁至',
    'views.cookiemanager.bwoi8t': '选择日期时间',
    'views.cookiemanager.x5j4qy': '确 定',
    'views.cookiemanager.bc0ucq': '临时封禁账号',
    'views.cookiemanager.yw8177': '封禁时长(分钟)',
    'views.cookiemanager.shqml1': '封禁时间到期后将自动恢复可用',
    'views.cookiemanager.c288pq': '原账号ID',
    'views.cookiemanager.1w7hm4': '新账号ID',
    'views.cookiemanager.yuju0p': '请输入新的唯一账号ID',
    'views.cookiemanager.7v7w52': 'Cookie详情',
    'views.cookiemanager.57v4p0': '复制字符串',
    'views.cookiemanager.918rdv': 'Cookie键名',
    'views.cookiemanager.865d07': 'Cookie值',
    'views.cookiemanager.nyl3rr': '未找到账号详情',
    'views.cookiemanager.47d298': '账号可用性测试结果',
    'views.cookiemanager.a3782e': '测试通过',
    'views.cookiemanager.29gqz2': '测试失败',
    'views.cookiemanager.h324e4': '状态码',
    'views.cookiemanager.1wxu3a': '系统操作',
    'views.cookiemanager.6y0q17': '暂无测试数据',
    'views.cookiemanager.d1w998': '批量测试结果',
    'views.cookiemanager.5e9o59': '测试总数',
    'views.cookiemanager.8k2v29': '可用数量',
    'views.cookiemanager.31k5ft': '封禁数量',
    'views.cookiemanager.7r1583': '未登录数量',
    'views.cookiemanager.95c723': '可用账号',
    'views.cookiemanager.6zi5yp': '无可用账号',
    'views.cookiemanager.1j3e7c': '被封禁账号',
    'views.cookiemanager.4uia1i': '无被封禁账号',
    'views.cookiemanager.nf4qda': '未登录账号',
    'views.cookiemanager.qjcdc8': '无未登录账号',
    'views.cookiemanager.5t4569': '批量临时封禁账号',
    'views.cookiemanager.bmf617': '已选账号',
    'views.cookiemanager.cj97s5': '已过期/待解封',
    'views.cookiemanager.n4d7oo': '{0}小时',
    'views.cookiemanager.3yb40y': '{0}分钟',
    'views.cookiemanager.2vus85': '即将在几秒内解封',
    'views.cookiemanager.nzr215': '长度在 2 到 50 个字符',
    'views.cookiemanager.s8l0f7': '请输入新的账号ID',
    'views.cookiemanager.m8bw6q': '加载Cookie统计成功:',
    'views.cookiemanager.fm55wb': '获取Cookie池状态失败: {0}',
    'views.cookiemanager.yhv62u': '获取Cookie池状态出错:',
    'views.cookiemanager.6k0j54': '获取Cookie状态失败，请检查API连接',
    'views.cookiemanager.nyw444': '加载可用账号成功:',
    'views.cookiemanager.9595fe': '获取可用账号列表失败: {0}',
    'views.cookiemanager.06297z': '加载可用账号出错:',
    'views.cookiemanager.3877rl': '获取账号列表失败',
    'views.cookiemanager.nt6rw4': '临时封禁账号:',
    'views.cookiemanager.r2um4g': '永久封禁账号:',
    'views.cookiemanager.d370l8': '获取封禁账号失败: {0}',
    'views.cookiemanager.4oi867': '加载封禁账号出错:',
    'views.cookiemanager.4md8km': '获取封禁账号失败',
    'views.cookiemanager.y73432': '加载Cookie列表成功:',
    'views.cookiemanager.22y82w': '获取Cookie列表失败: {0}',
    'views.cookiemanager.q7ga82': '加载Cookie列表出错:',
    'views.cookiemanager.62jq54': '获取列表失败',
    'views.cookiemanager.qgrx5n': '编辑表单已填充:',
    'views.cookiemanager.73548z': '获取Cookie信息失败: {0}',
    'views.cookiemanager.gbulp9': '获取详情出错:',
    'views.cookiemanager.p28u6i': '获取账号详情失败',
    'views.cookiemanager.py4r15': 'Cookie内容为空',
    'views.cookiemanager.vpm68i': '解析后的字符串Cookie:',
    'views.cookiemanager.r579kh': '解析Cookie字符串失败:',
    'views.cookiemanager.elejp7': 'Cookie解析失败，请检查格式 (name=value; name2=value2)',
    'views.cookiemanager.7o77s1': '解析JSON失败:',
    'views.cookiemanager.y32143': 'JSON格式错误，请检查输入',
    'views.cookiemanager.1u2wzd': '表格数据为空',
    'views.cookiemanager.wi6cn1': '表格中存在空的字段名',
    'views.cookiemanager.8w43al': '预览数据为空',
    'views.cookiemanager.311o2a': '准备提交的Cookie数据:',
    'views.cookiemanager.4534pf': '提交的最终JSON数据:',
    'views.cookiemanager.5fkkmo': '更新Cookie成功',
    'views.cookiemanager.g7u2yi': '添加Cookie成功',
    'views.cookiemanager.g2987l': '更新',
    'views.cookiemanager.u72yh2': '添加',
    'views.cookiemanager.qa3xuk': '保存失败:',
    'views.cookiemanager.f3jy50': 'JSON 格式无效',
    'views.cookiemanager.669359': '请先输入Cookie字符串',
    'views.cookiemanager.474st2': '转换成功',
    'views.cookiemanager.5ghrc3': '解析失败:',
    'views.cookiemanager.nroaf7': 'Cookie 字符串解析失败，请检查格式',
    'views.cookiemanager.yb9x3t': '确认清空所有已输入的字段吗？',
    'views.cookiemanager.lwo521': '提示',
    'views.cookiemanager.86icn7': '确定',
    'views.cookiemanager.fl98bx': '取消',
    'views.cookiemanager.27eiu6': '已清空',
    'views.cookiemanager.mu4bkt': '表格数据为空',
    'views.cookiemanager.l6m6j9': '生成成功',
    'views.cookiemanager.6o2ln6': '转换成功',
    'views.cookiemanager.21g119': 'JSON 格式无效',
    'views.cookiemanager.9s4ovr': '请先选择文件',
    'views.cookiemanager.737pwz': '文件处理失败:',
    'views.cookiemanager.was925': '解析文件失败，请检查格式',
    'views.cookiemanager.b04g8f': '无法读取文件内容',
    'views.cookiemanager.9s7630': '读取文件出错',
    'views.cookiemanager.l4k485': '成功解析 {0} 个字段',
    'views.cookiemanager.113i8h': '未在文件中找到有效的 name=value 格式',
    'views.cookiemanager.gu9n94': 'JSON 中未找到有效数据',
    'views.cookiemanager.t64i5t': '无效的 JSON 格式',
    'views.cookiemanager.j011g6': '未在 CSV 中找到有效数据',
    'views.cookiemanager.9y3nzo': '没有预览数据可导入',
    'views.cookiemanager.m1eb6y': '导入成功',
    'views.cookiemanager.o9m48o': '已取消导入',
    'views.cookiemanager.96lf7s': '确定要删除该 Cookie 吗？删除后不可恢复',
    'views.cookiemanager.2o2809': '确认删除',
    'views.cookiemanager.g5651u': '删除成功',
    'views.cookiemanager.cf1i41': '删除失败: {0}',
    'views.cookiemanager.1w21ob': '删除出错:',
    'views.cookiemanager.7q6yyr': '操作失败，请检查连接',
    'views.cookiemanager.571777': '解封成功',
    'views.cookiemanager.d54930': '解封失败: {0}',
    'views.cookiemanager.1c1876': '解封出错:',
    'views.cookiemanager.qks4og': '操作失败',
    'views.cookiemanager.95zbt0': '已成功同步到 Redis',
    'views.cookiemanager.o23jc7': '同步失败: {0}',
    'views.cookiemanager.572hd7': '同步出错:',
    'views.cookiemanager.i8i700': '操作失败',
    'views.cookiemanager.lv56y5': '更新ab_sr失败: {0}',
    'views.cookiemanager.159cck': '更新ab_sr出错:',
    'views.cookiemanager.17221j': '更新失败',
    'views.cookiemanager.tcz61g': '测试请求失败: {0}',
    'views.cookiemanager.1n28v7': '测试出错:',
    'views.cookiemanager.9at4s7': '测试失败',
    'views.cookiemanager.l0z0ky': '测试请求失败: {0}',
    'views.cookiemanager.oucusd': '批量测试出错:',
    'views.cookiemanager.l8ekty': '批量测试失败',
    'views.cookiemanager.6srmjj': '成功更新 {0} 个 Cookie 状态',
    'views.cookiemanager.127qbk': '更新状态失败: {0}',
    'views.cookiemanager.f65q9r': '更新状态出错:',
    'views.cookiemanager.6y7tf4': '更新失败',
    'views.cookiemanager.4m3644': '确定要清理所有已过期的 Cookie 吗？',
    'views.cookiemanager.36a5u1': '清理确认',
    'views.cookiemanager.s11lru': '开始清理',
    'views.cookiemanager.1it2py': '成功删除 {0} 个过期 Cookie',
    'views.cookiemanager.48ig46': '清理失败: {0}',
    'views.cookiemanager.9v2e49': '清理出错:',
    'views.cookiemanager.q93dxj': '操作失败',
    'views.cookiemanager.c91ed6': '获取失败: {0}',
    'views.cookiemanager.i2phqs': '详情查询出错:',
    'views.cookiemanager.p2s635': '详情获取失败',
    'views.cookiemanager.0x3yl3': '当前浏览器不支持剪贴板',
    'views.cookiemanager.2c157h': '已复制到剪贴板',
    'views.cookiemanager.kxhhb7': '复制出错:',
    'views.cookiemanager.5x00ks': '复制失败',
    'views.cookiemanager.6tt3m1': '账号 {0} 已成功临时封禁 {1} 分钟',
    'views.cookiemanager.rmoi5b': '封禁失败: {0}',
    'views.cookiemanager.h82589': '临时封禁出错:',
    'views.cookiemanager.8v5z9x': '操作失败',
    'views.cookiemanager.iw1a8d': '确定要永久封禁账号 {0} 吗？',
    'views.cookiemanager.wy9gqv': '永久封禁确认',
    'views.cookiemanager.h14i63': '永久封禁',
    'views.cookiemanager.60b8ym': '账号 {0} 已永久封禁',
    'views.cookiemanager.5215c3': '操作失败: {0}',
    'views.cookiemanager.820gh6': '封禁操作出错:',
    'views.cookiemanager.36zs5h': '操作失败',
    'views.cookiemanager.644stx': '账号 {0} 已解封',
    'views.cookiemanager.1w01sr': '解封失败: {0}',
    'views.cookiemanager.23633d': '解封操作出错:',
    'views.cookiemanager.36363t': '操作失败',
    'views.cookiemanager.x4j49z': '确定要强制解封账号 {0} 吗？',
    'views.cookiemanager.2t22kr': '强制解封确认',
    'views.cookiemanager.e6tc1n': '账号 {0} 已强制解封',
    'views.cookiemanager.vn0vpy': '强制解封失败: {0}',
    'views.cookiemanager.5b4rzz': '强制解封出错:',
    'views.cookiemanager.3h7t12': '操作失败',
    'views.cookiemanager.68b827': '账号ID已从 {0} 更新为 {1}',
    'views.cookiemanager.cl6b3x': '更新失败: {0}',
    'views.cookiemanager.v4cf99': '更新ID出错:',
    'views.cookiemanager.6pr34t': '更新失败',
    'views.cookiemanager.8365s4': '确定要彻底删除账号 {0} 的所有数据吗？',
    'views.cookiemanager.qeiey3': '账号 {0} 已删除',
    'views.cookiemanager.5rdm42': '删除账号失败: {0}',
    'views.cookiemanager.1bf1co': '账号删除出错:',
    'views.cookiemanager.oq3rf6': '删除失败',
    'views.cookiemanager.o1w9pl': '无法读取 Excel 文件内容',
    'views.cookiemanager.r72u3m': 'Excel 文件为空',
    'views.cookiemanager.56q81p': 'Excel 文件中必须包含 name 和 value 列',
    'views.cookiemanager.h929uc': '未解析到有效数据',
    'views.cookiemanager.8g5xrc': '解析 Excel 失败:',
    'views.cookiemanager.00kt80': 'Excel 解析错误',
    'views.cookiemanager.f0xi3y': 'Excel 加载失败:',
    'views.cookiemanager.3mfklj': '无法加载 Excel 处理库',
    'views.cookiemanager.11w111': '成功解封 {0} 个账号',
    'views.cookiemanager.r58bc3': '批量解封出错',
    'views.cookiemanager.o3k17t': '确定要解封所有临时封禁的账号吗？',
    'views.cookiemanager.i5fk3t': '解封出错',
    'views.cookiemanager.516123': '确定要强制解封所有永久封禁的账号吗？',
    'views.cookiemanager.nyi371': '确定要临时封禁所有当前可用的账号吗？',
    'views.cookiemanager.866552': '全部封禁确认',
    'views.cookiemanager.w0x11t': '当前没有可用账号',
    'views.cookiemanager.49bw7m': '封禁账号 {0} 出错:',
    'views.cookiemanager.zvlkac': '成功封禁 {0} 个账号，失败 {1} 个',
    'views.cookiemanager.t13gse': '获取账号列表失败: {0}',
    'views.cookiemanager.i3g56q': '操作出错:',
    'views.cookiemanager.30d34h': '操作失败',
    'views.cookiemanager.lid246': '确定要解封所有临时封禁的账号吗？',
    'views.cookiemanager.241361': '全部解封确认',
    'views.cookiemanager.nbwin3': '当前没有封禁的账号',
    'views.cookiemanager.9v446o': '解封账号 {0} 出错:',
    'views.cookiemanager.qtx2n9': '成功解封 {0} 个账号，共处理 {1} 个',
    'views.cookiemanager.23m5mp': '获取封禁账号失败: {0}',
    'views.cookiemanager.j7887t': '操作出错:',
    'views.cookiemanager.768gq2': '操作失败',
    'views.cookiemanager.a7uc8x': '请先选择账号',
    'views.cookiemanager.lx6v3t': '批量封禁账号 {0} 出错:',
    'views.cookiemanager.vox4d8': '成功封禁 {0} 个账号，共处理 {1} 个，时长 {2} 分钟',
    'views.cookiemanager.9jgsur': '批量封禁出错:',
    'views.cookiemanager.utl8fd': '批量封禁失败',
    'views.cookiemanager.j8c1xd': '确定要将选中的 {0} 个账号永久封禁吗？',
    'views.cookiemanager.qvw6rw': '批量永久封禁确认',
    'views.cookiemanager.xn5154': '永久封禁账号 {0} 出错:',
    'views.cookiemanager.qyx343': '成功永久封禁 {0} 个账号，共处理 {1} 个',
    'views.cookiemanager.514w67': '批量永久封禁出错:',
    'views.cookiemanager.pl3n3k': '批量永久封禁失败',
    'views.cookiemanager.s5426c': '请先选择要解封的账号',
    'views.cookiemanager.8e2n55': '确定要解封选中的 {0} 个账号吗？',
  }
  
  let res = map[key] || key
  // 处理占位符 {0}, {1}...
  if (arguments.length > 1) {
    const params = Array.isArray(arguments[1]) ? arguments[1] : [arguments[1]]
    params.forEach((p, i) => {
      res = res.replace(`{${i}}`, p)
    })
  }
  return res
}

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
    { required: true, message: '请输入百度账号ID', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ]
}

const updateIdRules = {
  new_account_id: [
    { required: true, message: '请输入新的账号ID', trigger: 'blur' },
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
      console.log($t('views.cookiemanager.m8bw6q'), data)
    } else {
      ElMessage.error($t('views.cookiemanager.fm55wb', [response.data.msg]))
    }
  } catch (error) {
    console.error($t('views.cookiemanager.yhv62u'), error)
    ElMessage.error($t('views.cookiemanager.6k0j54'))
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
      console.log($t('views.cookiemanager.nyw444'), availableAccounts.value)
    } else {
      ElMessage.error($t('views.cookiemanager.9595fe', [response.data.msg]))
    }
  } catch (error) {
    console.error($t('views.cookiemanager.06297z'), error)
    ElMessage.error($t('views.cookiemanager.3877rl'))
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
      
      console.log($t('views.cookiemanager.nt6rw4'), tempBannedAccounts.value)
      console.log($t('views.cookiemanager.r2um4g'), permBannedAccounts.value)
    } else {
      ElMessage.error($t('views.cookiemanager.d370l8', [response.data.msg]))
    }
  } catch (error) {
    console.error($t('views.cookiemanager.4oi867'), error)
    ElMessage.error($t('views.cookiemanager.4md8km'))
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
      
      console.log($t('views.cookiemanager.y73432'), cookieList.value)
      
      // 如果后端返回了总数，使用后端的总数
      if (response.data.total) {
        total.value = response.data.total
      } else {
        total.value = cookieList.value.length
      }
    } else {
      ElMessage.error($t('views.cookiemanager.22y82w', [response.data.msg]))
    }
  } catch (error) {
    console.error($t('views.cookiemanager.q7ga82'), error)
    ElMessage.error($t('views.cookiemanager.62jq54'))
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
      
      console.log($t('views.cookiemanager.qgrx5n'), cookieForm);
    } else {
      ElMessage.error($t('views.cookiemanager.73548z', [response.data.msg]));
    }
  } catch (error) {
    console.error($t('views.cookiemanager.gbulp9'), error);
    ElMessage.error($t('views.cookiemanager.p28u6i'));
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
            ElMessage.warning($t('views.cookiemanager.py4r15'))
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
          console.log($t('views.cookiemanager.vpm68i'), cookieData.cookie_data)
        } catch (e) {
          console.error($t('views.cookiemanager.r579kh'), e)
          ElMessage.error($t('views.cookiemanager.elejp7'))
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
          console.error($t('views.cookiemanager.7o77s1'), e)
          ElMessage.error($t('views.cookiemanager.y32143'))
          submitting.value = false
          return
        }
        break
      case 'table':
        // 表格模式
        if (cookieTableData.value.length === 0) {
          ElMessage.error($t('views.cookiemanager.1u2wzd'))
          submitting.value = false
          return
        }
        
        // 验证表格数据
        for (const row of cookieTableData.value) {
          if (!row.name.trim()) {
            ElMessage.error($t('views.cookiemanager.wi6cn1'))
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
          ElMessage.error($t('views.cookiemanager.8w43al'))
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
    
    console.log($t('views.cookiemanager.311o2a'), cookieData)
    
    // 添加详细的日志，方便调试
    console.log($t('views.cookiemanager.4534pf'), JSON.stringify(cookieData, null, 2))
    
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
      ElMessage.success(cookieForm.id ? $t('views.cookiemanager.5fkkmo') : $t('views.cookiemanager.g7u2yi'))
      cookieDialogVisible.value = false
      refreshCookieStatus()
      loadCookies()
      loadAvailableAccounts()
      loadBannedAccounts()
    } else {
      ElMessage.error(`${cookieForm.id ? $t('views.cookiemanager.g2987l') : $t('views.cookiemanager.u72yh2')}Cookie失败: ${response.data.msg}`)
    }
  } catch (error: any) {
    if (error.message) {
      ElMessage.error(error.message)
    } else {
      console.error($t('views.cookiemanager.qa3xuk'), error)
      ElMessage.error(`${cookieForm.id ? $t('views.cookiemanager.g2987l') : $t('views.cookiemanager.u72yh2')}Cookie失败，请检查网络连接`)
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
    ElMessage.error($t('views.cookiemanager.f3jy50'))
  }
}

// Cookie编辑 - 字符串转JSON
const convertStringToJson = () => {
  if (!cookieForm.cookie_string) {
    ElMessage.warning($t('views.cookiemanager.669359'))
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
    
    ElMessage.success($t('views.cookiemanager.474st2'))
  } catch (e) {
    console.error($t('views.cookiemanager.5ghrc3'), e)
    ElMessage.error($t('views.cookiemanager.nroaf7'))
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
  ElMessageBox.confirm($t('views.cookiemanager.yb9x3t'), $t('views.cookiemanager.lwo521'), {
    confirmButtonText: $t('views.cookiemanager.86icn7'),
    cancelButtonText: $t('views.cookiemanager.fl98bx'),
    type: 'warning'
  }).then(() => {
    cookieTableData.value = []
    ElMessage.success($t('views.cookiemanager.27eiu6'))
  }).catch(() => {})
}

// Cookie编辑 - 表格数据转JSON
const generateJsonFromTable = () => {
  if (cookieTableData.value.length === 0) {
    ElMessage.warning($t('views.cookiemanager.mu4bkt'))
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
  ElMessage.success($t('views.cookiemanager.l6m6j9'))
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
    ElMessage.success($t('views.cookiemanager.6o2ln6'))
  } catch (e) {
    ElMessage.error($t('views.cookiemanager.21g119'))
  }
}

// Cookie编辑 - 处理文件变更
const handleFileChange = (file: any) => {
  selectedFile.value = file.raw
}

// Cookie编辑 - 处理Cookie文件
const processCookieFile = async () => {
  if (!selectedFile.value) {
    ElMessage.warning($t('views.cookiemanager.9s4ovr'))
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
    console.error($t('views.cookiemanager.737pwz'), error)
    ElMessage.error($t('views.cookiemanager.was925'))
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
        reject(new Error($t('views.cookiemanager.b04g8f')))
      }
    }
    
    reader.onerror = () => {
      reject(new Error($t('views.cookiemanager.9s7630')))
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
    ElMessage.success($t('views.cookiemanager.l4k485', [result.length]))
  } else {
    ElMessage.error($t('views.cookiemanager.113i8h'))
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
      ElMessage.success($t('views.cookiemanager.l4k485', [result.length]))
    } else {
      ElMessage.error($t('views.cookiemanager.gu9n94'))
    }
  } catch (e) {
    ElMessage.error($t('views.cookiemanager.t64i5t'))
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
    ElMessage.success($t('views.cookiemanager.l4k485', [result.length]))
  } else {
    ElMessage.error($t('views.cookiemanager.j011g6'))
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
    ElMessage.warning($t('views.cookiemanager.9y3nzo'))
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
  
  ElMessage.success($t('views.cookiemanager.m1eb6y'))
}

// 取消导入
const cancelImport = () => {
  importPreviewData.value = []
  fileList.value = []
  selectedFile.value = null
  ElMessage.info($t('views.cookiemanager.o9m48o'))
}

// 删除Cookie
const deleteCookie = async (account_id: number) => {
  try {
    await ElMessageBox.confirm($t('views.cookiemanager.96lf7s'), $t('views.cookiemanager.2o2809'), {
      confirmButtonText: $t('views.cookiemanager.115uyi'),
      cancelButtonText: $t('views.cookiemanager.fl98bx'),
      type: 'warning'
    })
    
    listLoading.value = true
    
    const response = await axios.delete(`${API_BASE_URL}/admin/cookie/delete/${account_id}`)
    if (response.data.code === 10000) {
      ElMessage.success($t('views.cookiemanager.g5651u'))
      loadCookies()
      refreshCookieStatus()
    } else {
      ElMessage.error($t('views.cookiemanager.cf1i41', [response.data.msg]))
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error($t('views.cookiemanager.1w21ob'), error)
      ElMessage.error($t('views.cookiemanager.7q6yyr'))
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
      ElMessage.success($t('views.cookiemanager.571777'))
      loadCookies()
      refreshCookieStatus()
    } else {
      ElMessage.error($t('views.cookiemanager.d54930', [response.data.msg]))
    }
  } catch (error) {
    console.error($t('views.cookiemanager.1c1876'), error)
    ElMessage.error($t('views.cookiemanager.qks4og'))
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
      ElMessage.success($t('views.cookiemanager.95zbt0'))
      refreshCookieStatus()
    } else {
      ElMessage.error($t('views.cookiemanager.o23jc7', [response.data.msg]))
    }
  } catch (error) {
    console.error($t('views.cookiemanager.572hd7'), error)
    ElMessage.error($t('views.cookiemanager.i8i700'))
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
      ElMessage.error($t('views.cookiemanager.lv56y5', [response.data.msg]))
    }
  } catch (error) {
    console.error($t('views.cookiemanager.159cck'), error)
    ElMessage.error($t('views.cookiemanager.17221j'))
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
      ElMessage.error($t('views.cookiemanager.tcz61g', [response.data.msg]))
      testResultDialogVisible.value = false
    }
  } catch (error) {
    console.error($t('views.cookiemanager.1n28v7'), error)
    ElMessage.error($t('views.cookiemanager.9at4s7'))
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
      ElMessage.error($t('views.cookiemanager.l0z0ky', [response.data.msg]))
      batchTestResultDialogVisible.value = false
    }
  } catch (error) {
    console.error($t('views.cookiemanager.oucusd'), error)
    ElMessage.error($t('views.cookiemanager.l8ekty'))
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
      ElMessage.success($t('views.cookiemanager.6srmjj', [response.data.data.updated_count]))
      refreshCookieStatus()
      loadCookies()
    } else {
      ElMessage.error($t('views.cookiemanager.127qbk', [response.data.msg]))
    }
  } catch (error) {
    console.error($t('views.cookiemanager.f65q9r'), error)
    ElMessage.error($t('views.cookiemanager.6y7tf4'))
  } finally {
    updatingStatus.value = false
  }
}

// 清理过期Cookie
const cleanupExpiredCookies = async () => {
  try {
    await ElMessageBox.confirm($t('views.cookiemanager.4m3644'), $t('views.cookiemanager.36a5u1'), {
      confirmButtonText: $t('views.cookiemanager.s11lru'),
      cancelButtonText: $t('views.cookiemanager.fl98bx'),
      type: 'warning'
    })
    
    cleaningUp.value = true
    
    const response = await axios.post(`${API_BASE_URL}/admin/cookie/cleanup-expired`)
    if (response.data.code === 10000) {
      ElMessage.success($t('views.cookiemanager.1it2py', [response.data.data.deleted_count]))
      refreshCookieStatus()
      loadCookies()
    } else {
      ElMessage.error($t('views.cookiemanager.48ig46', [response.data.msg]))
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error($t('views.cookiemanager.9v2e49'), error)
      ElMessage.error($t('views.cookiemanager.q93dxj'))
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
      ElMessage.error($t('views.cookiemanager.c91ed6', [response.data.msg]))
      accountDetailDialogVisible.value = false
    }
  } catch (error) {
    console.error($t('views.cookiemanager.i2phqs'), error)
    ElMessage.error($t('views.cookiemanager.p2s635'))
    accountDetailDialogVisible.value = false
  } finally {
    accountDetailLoading.value = false
  }
}

// 复制Cookie字符串
const copyCookieString = async () => {
  if (!isSupported) {
    ElMessage.error($t('views.cookiemanager.0x3yl3'))
    return
  }
  
  try {
    await copy(accountDetailCookieString.value)
    ElMessage.success($t('views.cookiemanager.2c157h'))
  } catch (error) {
    console.error($t('views.cookiemanager.kxhhb7'), error)
    ElMessage.error($t('views.cookiemanager.5x00ks'))
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
      ElMessage.success($t('views.cookiemanager.6tt3m1', [tempBanForm.account_id,tempBanForm.duration_minutes]))
      tempBanDialogVisible.value = false
      refreshCookieStatus()
      loadCookies()
      loadAvailableAccounts()
      loadBannedAccounts()
    } else {
      ElMessage.error($t('views.cookiemanager.rmoi5b', [response.data.msg]))
    }
  } catch (error) {
    console.error($t('views.cookiemanager.h82589'), error)
    ElMessage.error($t('views.cookiemanager.8v5z9x'))
  } finally {
    submitting.value = false
  }
}

// 永久封禁账号
const banAccountPermanently = async (accountId: string) => {
  try {
    await ElMessageBox.confirm($t('views.cookiemanager.iw1a8d', [accountId]), $t('views.cookiemanager.wy9gqv'), {
      confirmButtonText: $t('views.cookiemanager.h14i63'),
      cancelButtonText: $t('views.cookiemanager.fl98bx'),
      type: 'warning'
    })
    
    accountsLoading.value = true
    
    const response = await axios.post(`${API_BASE_URL}/admin/cookie/ban/permanent/${accountId}`)
    if (response.data.code === 10000) {
      ElMessage.success($t('views.cookiemanager.60b8ym', [accountId]))
      refreshCookieStatus()
      loadCookies()
      loadAvailableAccounts()
      loadBannedAccounts()
    } else {
      ElMessage.error($t('views.cookiemanager.5215c3', [response.data.msg]))
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error($t('views.cookiemanager.820gh6'), error)
      ElMessage.error($t('views.cookiemanager.36zs5h'))
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
      ElMessage.success($t('views.cookiemanager.644stx', [accountId]))
      refreshCookieStatus()
      loadCookies()
      loadAvailableAccounts()
      loadBannedAccounts()
    } else {
      ElMessage.error($t('views.cookiemanager.1w01sr', [response.data.msg]))
    }
  } catch (error) {
    console.error($t('views.cookiemanager.23633d'), error)
    ElMessage.error($t('views.cookiemanager.36363t'))
  } finally {
    bannedLoading.value = false
  }
}

// 强制解封账号
const forceUnbanAccount = async (accountId: string) => {
  try {
    await ElMessageBox.confirm($t('views.cookiemanager.x4j49z', [accountId]), $t('views.cookiemanager.2t22kr'), {
      confirmButtonText: $t('views.cookiemanager.8etq8j'),
      cancelButtonText: $t('views.cookiemanager.fl98bx'),
      type: 'warning'
    })
    
    bannedLoading.value = true
    
    const response = await axios.post(`${API_BASE_URL}/admin/cookie/force-unban/${accountId}`)
    if (response.data.code === 10000) {
      ElMessage.success($t('views.cookiemanager.e6tc1n', [accountId]))
      refreshCookieStatus()
      loadCookies()
      loadAvailableAccounts()
      loadBannedAccounts()
    } else {
      ElMessage.error($t('views.cookiemanager.vn0vpy', [response.data.msg]))
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error($t('views.cookiemanager.5b4rzz'), error)
      ElMessage.error($t('views.cookiemanager.3h7t12'))
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
      ElMessage.success($t('views.cookiemanager.68b827', [updateIdForm.old_account_id,updateIdForm.new_account_id]))
      updateIdDialogVisible.value = false
      refreshCookieStatus()
      loadCookies()
      loadAvailableAccounts()
      loadBannedAccounts()
    } else {
      ElMessage.error($t('views.cookiemanager.cl6b3x', [response.data.msg]))
    }
  } catch (error: any) {
    if (error.message) {
      ElMessage.error(error.message)
    } else {
      console.error($t('views.cookiemanager.v4cf99'), error)
      ElMessage.error($t('views.cookiemanager.6pr34t'))
    }
  } finally {
    submitting.value = false
  }
}

// 删除账号
const deleteAccount = async (accountId: string) => {
  try {
    await ElMessageBox.confirm($t('views.cookiemanager.8365s4', [accountId]), $t('views.cookiemanager.2o2809'), {
      confirmButtonText: $t('views.cookiemanager.115uyi'),
      cancelButtonText: $t('views.cookiemanager.fl98bx'),
      type: 'warning'
    })
    
    accountsLoading.value = true
    
    const response = await axios.delete(`${API_BASE_URL}/admin/cookie/delete/${accountId}`)
    if (response.data.code === 10000) {
      ElMessage.success($t('views.cookiemanager.qeiey3', [accountId]))
      refreshCookieStatus()
      loadCookies()
      loadAvailableAccounts()
      loadBannedAccounts()
    } else {
      ElMessage.error($t('views.cookiemanager.5rdm42', [response.data.msg]))
    }
  } catch (error: any) {
    if (error !== 'cancel') {
      console.error($t('views.cookiemanager.1bf1co'), error)
      ElMessage.error($t('views.cookiemanager.oq3rf6'))
    }
  } finally {
    accountsLoading.value = false
  }
}

// 辅助函数
// 格式化Cookie状态文本
const getCookieStatusText = (cookie: any) => {
  if (cookie.is_permanently_banned === 1) return $t('views.cookiemanager.e6y884')
  if (cookie.temp_ban_until) return $t('views.cookiemanager.5t0x50')
  if (cookie.is_available === 1) return $t('views.cookiemanager.8qgc3r')
  if (cookie.expire_time && new Date(cookie.expire_time) < new Date()) return $t('views.cookiemanager.81u723')
  return $t('views.cookiemanager.jxt47y')
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
  if (!seconds || seconds <= 0) return $t('views.cookiemanager.cj97s5')
  
  const days = Math.floor(seconds / (24 * 3600))
  const hours = Math.floor((seconds % (24 * 3600)) / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  
  let result = ''
  if (days > 0) result += `${days}天`
  if (hours > 0) result += $t('views.cookiemanager.n4d7oo', [hours])
  if (minutes > 0) result += $t('views.cookiemanager.3yb40y', [minutes])
  if (remainingSeconds > 0 && !days && !hours) result += `${remainingSeconds}秒`
  
  return result || $t('views.cookiemanager.2vus85')
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
      // 判断是临时封禁还是永久封禁
      if (cookie.is_permanently_banned === 1) {
        forceUnbanAccount(cookie.account_id)
      } else {
        unbanCookie(cookie.account_id)
      }
      break
    case 'temp_ban':
      openTempBanDialog(cookie.account_id)
      break
    case 'perm_ban':
      banAccountPermanently(cookie.account_id)
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
          ElMessage.error($t('views.cookiemanager.o1w9pl'))
          return
        }
        
        // 解析Excel数据
        const workbook = XLSX.read(data, { type: 'array' })
        const firstSheetName = workbook.SheetNames[0]
        const worksheet = workbook.Sheets[firstSheetName]
        
        // 转换为JSON
        const jsonData = XLSX.utils.sheet_to_json(worksheet)
        
        if (jsonData.length === 0) {
          ElMessage.error($t('views.cookiemanager.r72u3m'))
          return
        }
        
        // 检查是否有name和value列
        const firstRow = jsonData[0]
        const hasNameCol = 'name' in firstRow || 'Name' in firstRow || 'NAME' in firstRow
        const hasValueCol = 'value' in firstRow || 'Value' in firstRow || 'VALUE' in firstRow
        
        if (!hasNameCol || !hasValueCol) {
          ElMessage.error($t('views.cookiemanager.56q81p'))
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
          ElMessage.success($t('views.cookiemanager.l4k485', [result.length]))
        } else {
          ElMessage.error($t('views.cookiemanager.h929uc'))
        }
      } catch (error) {
        console.error($t('views.cookiemanager.8g5xrc'), error)
        ElMessage.error($t('views.cookiemanager.00kt80'))
      }
    }
    
    reader.onerror = () => {
      ElMessage.error($t('views.cookiemanager.o1w9pl'))
    }
    
    reader.readAsArrayBuffer(file)
  } catch (error) {
    console.error($t('views.cookiemanager.f0xi3y'), error)
    ElMessage.error($t('views.cookiemanager.3mfklj'))
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
    ElMessage.success($t('views.cookiemanager.11w111', [successCount]))
    loadBannedAccounts()
    refreshCookieStatus()
    loadCookies()
    tempBannedSelection.value = []
    checkAllTemp.value = false
  } catch (error) {
    ElMessage.error($t('views.cookiemanager.r58bc3'))
  } finally {
    bannedLoading.value = false
  }
}

// 解封所有临时封禁Cookie
const unbanAllTemp = async () => {
  if (tempBannedAccounts.value.length === 0) return
  
  try {
    await ElMessageBox.confirm($t('views.cookiemanager.o3k17t'), $t('views.cookiemanager.lwo521'), { type: 'warning' })
    bannedLoading.value = true
    
    let successCount = 0
    for (const item of tempBannedAccounts.value) {
      const response = await axios.post(`${API_BASE_URL}/admin/cookie/unban/${item.account_id}`)
      if (response.data.code === 10000) successCount++
    }
    
    ElMessage.success($t('views.cookiemanager.11w111', [successCount]))
    loadBannedAccounts()
    refreshCookieStatus()
    loadCookies()
    tempBannedSelection.value = []
    checkAllTemp.value = false
  } catch (error) {
    if (error !== 'cancel') ElMessage.error($t('views.cookiemanager.i5fk3t'))
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
    ElMessage.success($t('views.cookiemanager.11w111', [successCount]))
    loadBannedAccounts()
    refreshCookieStatus()
    loadCookies()
    permBannedSelection.value = []
    checkAllPerm.value = false
  } catch (error) {
    ElMessage.error($t('views.cookiemanager.r58bc3'))
  } finally {
    bannedLoading.value = false
  }
}

// 解封所有永久封禁Cookie
const unbanAllPerm = async () => {
  if (permBannedAccounts.value.length === 0) return
  
  try {
    await ElMessageBox.confirm($t('views.cookiemanager.516123'), $t('views.cookiemanager.lwo521'), { type: 'warning' })
    bannedLoading.value = true
    
    let successCount = 0
    for (const accountId of permBannedAccounts.value) {
      const response = await axios.post(`${API_BASE_URL}/admin/cookie/force-unban/${accountId}`)
      if (response.data.code === 10000) successCount++
    }
    
    ElMessage.success($t('views.cookiemanager.11w111', [successCount]))
    loadBannedAccounts()
    refreshCookieStatus()
    loadCookies()
    permBannedSelection.value = []
    checkAllPerm.value = false
  } catch (error) {
    if (error !== 'cancel') ElMessage.error($t('views.cookiemanager.i5fk3t'))
  } finally {
    bannedLoading.value = false
  }
}

// 批量封禁所有Cookie
const batchBanAll = async () => {
  try {
    await ElMessageBox.confirm($t('views.cookiemanager.nyi371'), $t('views.cookiemanager.866552'), {
      confirmButtonText: $t('views.cookiemanager.86icn7'),
      cancelButtonText: $t('views.cookiemanager.fl98bx'),
      type: 'warning'
    })
    
    batchActionLoading.value = true
    
    // 获取所有可用账号ID
    const response = await axios.get(`${API_BASE_URL}/admin/cookie/available-accounts`)
    if (response.data.code === 10000) {
      const accountIds = response.data.data.account_ids || []
      
      if (accountIds.length === 0) {
        ElMessage.warning($t('views.cookiemanager.w0x11t'))
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
          console.error($t('views.cookiemanager.49bw7m', [accountId]), error)
        }
      }
      
      ElMessage.success($t('views.cookiemanager.zvlkac', [successCount,accountIds.length]))
      
      // 重新加载数据
      refreshCookieStatus()
      loadCookies()
      loadAvailableAccounts()
      loadBannedAccounts()
    } else {
      ElMessage.error($t('views.cookiemanager.t13gse', [response.data.msg]))
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error($t('views.cookiemanager.i3g56q'), error)
      ElMessage.error($t('views.cookiemanager.30d34h'))
    }
  } finally {
    batchActionLoading.value = false
  }
}

// 批量解封所有Cookie
const batchUnbanAll = async () => {
  try {
    await ElMessageBox.confirm($t('views.cookiemanager.lid246'), $t('views.cookiemanager.241361'), {
      confirmButtonText: $t('views.cookiemanager.86icn7'),
      cancelButtonText: $t('views.cookiemanager.fl98bx'),
      type: 'warning'
    })
    
    batchActionLoading.value = true
    
    // 获取所有临时封禁的账号
    const response = await axios.get(`${API_BASE_URL}/admin/cookie/banned-accounts`)
    if (response.data.code === 10000) {
      const tempBannedAccounts = response.data.data.temp_banned || []
      
      if (tempBannedAccounts.length === 0) {
        ElMessage.warning($t('views.cookiemanager.nbwin3'))
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
          console.error($t('views.cookiemanager.9v446o', [account.account_id]), error)
        }
      }
      
      ElMessage.success($t('views.cookiemanager.qtx2n9', [successCount,tempBannedAccounts.length]))
      
      // 重新加载数据
      refreshCookieStatus()
      loadCookies()
      loadAvailableAccounts()
      loadBannedAccounts()
    } else {
      ElMessage.error($t('views.cookiemanager.23m5mp', [response.data.msg]))
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error($t('views.cookiemanager.j7887t'), error)
      ElMessage.error($t('views.cookiemanager.768gq2'))
    }
  } finally {
    batchActionLoading.value = false
  }
}

// 批量临时封禁选中的Cookie
const batchTempBan = () => {
  if (multipleSelection.value.length === 0) {
    ElMessage.warning($t('views.cookiemanager.a7uc8x'))
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
        console.error($t('views.cookiemanager.lx6v3t', [item.account_id]), error)
      }
    }
    
    ElMessage.success($t('views.cookiemanager.vox4d8', [successCount,multipleSelection.value.length,batchTempBanForm.duration_minutes]))
    batchTempBanDialogVisible.value = false
    
    // 重新加载数据
    refreshCookieStatus()
    loadCookies()
    loadAvailableAccounts()
    loadBannedAccounts()
    
    // 清空选择
    multipleSelection.value = []
  } catch (error) {
    console.error($t('views.cookiemanager.9jgsur'), error)
    ElMessage.error($t('views.cookiemanager.utl8fd'))
  } finally {
    batchActionLoading.value = false
  }
}

// 批量永久封禁选中的Cookie
const batchPermBan = async () => {
  if (multipleSelection.value.length === 0) {
    ElMessage.warning($t('views.cookiemanager.a7uc8x'))
    return
  }
  
  try {
    await ElMessageBox.confirm($t('views.cookiemanager.j8c1xd', [multipleSelection.value.length]), $t('views.cookiemanager.qvw6rw'), {
      confirmButtonText: $t('views.cookiemanager.86icn7'),
      cancelButtonText: $t('views.cookiemanager.fl98bx'),
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
        console.error($t('views.cookiemanager.xn5154', [item.account_id]), error)
      }
    }
    
    ElMessage.success($t('views.cookiemanager.qyx343', [successCount,multipleSelection.value.length]))
    
    // 重新加载数据
    refreshCookieStatus()
    loadCookies()
    loadAvailableAccounts()
    loadBannedAccounts()
    
    // 清空选择
    multipleSelection.value = []
  } catch (error) {
    if (error !== 'cancel') {
      console.error($t('views.cookiemanager.514w67'), error)
      ElMessage.error($t('views.cookiemanager.pl3n3k'))
    }
  } finally {
    batchActionLoading.value = false
  }
}

// 批量解封选中的Cookie
const batchUnban = async () => {
  if (multipleSelection.value.length === 0) {
    ElMessage.warning($t('views.cookiemanager.s5426c'))
    return
  }
  
  try {
    await ElMessageBox.confirm($t('views.cookiemanager.8e2n55', [multipleSelection.value.length]), $t('views.cookiemanager.241361'), {
      confirmButtonText: $t('views.cookiemanager.86icn7'),
      cancelButtonText: $t('views.cookiemanager.fl98bx'),
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
        console.error($t('views.cookiemanager.9v446o', [item.account_id]), error)
      }
    }
    
    ElMessage.success($t('views.cookiemanager.qtx2n9', [successCount,multipleSelection.value.length]))
    
    // 重新加载数据
    refreshCookieStatus()
    loadCookies()
    loadAvailableAccounts()
    loadBannedAccounts()
    
    // 清空选择
    multipleSelection.value = []
  } catch (error) {
    if (error !== 'cancel') {
      console.error($t('views.cookiemanager.j7887t'), error)
      ElMessage.error($t('views.cookiemanager.768gq2'))
    }
  } finally {
    batchActionLoading.value = false
  }
}
</script>

<template>
  <div class="cookie-manager-container">
    <div class="page-header">
      <h1>{{$t('views.cookiemanager.cslk87')}}</h1>
      <div class="api-status">
        <el-tag :type="apiConnected ? 'success' : 'danger'" effect="dark">
          {{ apiConnected ? $t('views.cookiemanager.s8b3r4') : $t('views.cookiemanager.ryfkc7') }}
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
              <span>{{$t('views.cookiemanager.584l78')}}</span>
              <div>
                <el-button type="primary" size="small" @click="refreshCookieStatus" :loading="statusLoading">
                  <el-icon><Refresh /></el-icon>{{$t('views.cookiemanager.p3kgye')}}</el-button>
                <el-button type="success" size="small" @click="openAddCookieDialog">
                  <el-icon><Plus /></el-icon>{{$t('views.cookiemanager.u72yh2')}}</el-button>
              </div>
            </div>
          </template>
          
          <div v-loading="statusLoading" class="status-overview">
            <div class="status-item">
              <div class="status-value">{{ cookieStats.total }}</div>
              <div class="status-label">{{$t('views.cookiemanager.elw1fx')}}</div>
            </div>
            <div class="status-item success">
              <div class="status-value">{{ cookieStats.available }}</div>
              <div class="status-label">{{$t('views.cookiemanager.8qgc3r')}}</div>
            </div>
            <div class="status-item warning">
              <div class="status-value">{{ cookieStats.tempBanned }}</div>
              <div class="status-label">{{$t('views.cookiemanager.5t0x50')}}</div>
            </div>
            <div class="status-item danger">
              <div class="status-value">{{ cookieStats.permBanned }}</div>
              <div class="status-label">{{$t('views.cookiemanager.e6y884')}}</div>
            </div>
          </div>
          
          <el-divider />
          
          <div class="action-buttons">
            <el-button type="primary" @click="testAllCookiesAvailability" :loading="testingAll">
              <el-icon><Check /></el-icon>{{$t('views.cookiemanager.1u4sy2')}}</el-button>
            <el-button type="warning" @click="updateCookieStatus" :loading="updatingStatus">
              <el-icon><RefreshRight /></el-icon>{{$t('views.cookiemanager.dl2a0c')}}</el-button>
            <el-button type="danger" @click="cleanupExpiredCookies" :loading="cleaningUp">
              <el-icon><Delete /></el-icon>{{$t('views.cookiemanager.rq4zij')}}</el-button>
          </div>
          
          <!-- 账号列表 -->
          <div class="account-list-section">
            <div class="section-header">
              <h3>{{$t('views.cookiemanager.nlb473')}}</h3>
              <el-button size="small" text @click="loadAvailableAccounts">{{$t('views.cookiemanager.p3kgye')}}</el-button>
            </div>
            <div v-loading="accountsLoading" class="account-list">
              <template v-if="availableAccounts.length > 0">
                <div v-for="account in availableAccounts" :key="account" class="account-item">
                  <div class="account-info">
                    <el-tag size="small" effect="plain">{{ account }}</el-tag>
                  </div>
                  <div class="account-actions">
                    <el-button size="small" type="primary" @click="testAccountAvailability(account)" plain>{{$t('views.cookiemanager.vne764')}}</el-button>
                    <el-dropdown trigger="click" @command="handleAccountCommand($event, account)">
                      <el-button size="small" plain>{{$t('views.cookiemanager.s2tp53')}}<el-icon class="el-icon--right"><ArrowDown /></el-icon>
                      </el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item command="view">{{$t('views.cookiemanager.x4jo6h')}}</el-dropdown-item>
                          <el-dropdown-item command="temp_ban" divided>{{$t('views.cookiemanager.5t0x50')}}</el-dropdown-item>
                          <el-dropdown-item command="perm_ban">{{$t('views.cookiemanager.e6y884')}}</el-dropdown-item>
                          <el-dropdown-item command="update" divided>{{$t('views.cookiemanager.ee2q48')}}</el-dropdown-item>
                          <el-dropdown-item command="delete" divided>{{$t('views.cookiemanager.115uyi')}}</el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>
                </div>
              </template>
              <el-empty v-else :description="$t('views.cookiemanager.xt8ck8')" />
            </div>
          </div>
        </el-card>
        
        <!-- 封禁的账号卡片 -->
        <el-card class="banned-accounts-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>{{$t('views.cookiemanager.61po6w')}}</span>
              <el-button size="small" type="primary" @click="loadBannedAccounts" plain>
                <el-icon><Refresh /></el-icon>{{$t('views.cookiemanager.p3kgye')}}</el-button>
            </div>
          </template>
          
          <div v-loading="bannedLoading" class="banned-accounts">
            <el-tabs v-model="bannedTabActive">
              <el-tab-pane :label="$t('views.cookiemanager.5t0x50')" name="temp">
                <div class="banned-toolbar" v-if="tempBannedAccounts.length > 0">
                  <el-checkbox v-model="checkAllTemp" :indeterminate="isTempIndeterminate" @change="handleCheckAllTempChange">{{$t('views.cookiemanager.8st7lh')}}</el-checkbox>
                  <el-button type="primary" link size="small" :disabled="tempBannedSelection.length === 0" @click="unbanSelectedTemp">{{$t('views.cookiemanager.d5714o')}}</el-button>
                  <el-button type="danger" link size="small" @click="unbanAllTemp">{{$t('views.cookiemanager.j33j3w')}}</el-button>
                </div>
                <template v-if="tempBannedAccounts.length > 0">
                  <el-checkbox-group v-model="tempBannedSelection">
                    <div v-for="account in tempBannedAccounts" :key="account.account_id" class="banned-account-item">
                      <el-checkbox :value="account.account_id" class="banned-checkbox" />
                      <div class="banned-account-info">
                        <div class="account-id">{{ account.account_id }}</div>
                        <div class="ban-time">{{$t('views.cookiemanager.92zl33')}}{{ formatBanTimeRemaining(account.remaining_seconds) }}
                        </div>
                        <div class="ban-time-tooltip">
                          {{ account.temp_ban_until }}
                        </div>
                      </div>
                      <div class="banned-account-actions">
                        <el-button size="small" type="primary" @click.stop="unbanAccount(account.account_id)" plain>{{$t('views.cookiemanager.mf8dc8')}}</el-button>
                      </div>
                    </div>
                  </el-checkbox-group>
                </template>
                <el-empty v-else :description="$t('views.cookiemanager.oi7woo')" />
              </el-tab-pane>
              <el-tab-pane :label="$t('views.cookiemanager.e6y884')" name="perm">
                <div class="banned-toolbar" v-if="permBannedAccounts.length > 0">
                  <el-checkbox v-model="checkAllPerm" :indeterminate="isPermIndeterminate" @change="handleCheckAllPermChange">{{$t('views.cookiemanager.8st7lh')}}</el-checkbox>
                  <el-button type="primary" link size="small" :disabled="permBannedSelection.length === 0" @click="unbanSelectedPerm">{{$t('views.cookiemanager.ns9cp5')}}</el-button>
                  <el-button type="danger" link size="small" @click="unbanAllPerm">{{$t('views.cookiemanager.sk5fy0')}}</el-button>
                </div>
                <template v-if="permBannedAccounts.length > 0">
                  <el-checkbox-group v-model="permBannedSelection">
                    <div v-for="account in permBannedAccounts" :key="account" class="banned-account-item">
                      <el-checkbox :value="account" class="banned-checkbox" />
                      <div class="banned-account-info">
                        <div class="account-id">{{ account }}</div>
                        <div class="ban-status">{{$t('views.cookiemanager.e6y884')}}</div>
                      </div>
                      <div class="banned-account-actions">
                        <el-button size="small" type="danger" @click.stop="forceUnbanAccount(account)" plain>{{$t('views.cookiemanager.8etq8j')}}</el-button>
                      </div>
                    </div>
                  </el-checkbox-group>
                </template>
                <el-empty v-else :description="$t('views.cookiemanager.fvo87d')" />
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
              <span>{{$t('views.cookiemanager.47kxcu')}}</span>
              <div class="header-actions">
                <el-button type="primary" size="small" @click="syncToRedis" :loading="syncing">
                  <el-icon><Connection /></el-icon>{{$t('views.cookiemanager.278g1g')}}</el-button>
                <el-button type="success" size="small" @click="updateAbSr" :loading="updatingAbSr">
                  <el-icon><RefreshRight /></el-icon>{{$t('views.cookiemanager.y9p7s8')}}</el-button>
                <el-button size="small" @click="loadCookies" :loading="listLoading">
                  <el-icon><Refresh /></el-icon>{{$t('views.cookiemanager.p3kgye')}}</el-button>
              </div>
            </div>
          </template>
          
          <div class="filter-section">
            <el-input
              v-model="searchAccount"
              :placeholder="$t('views.cookiemanager.33q43q')"
              clearable
              prefix-icon="Search"
              class="filter-item"
            />
            <el-select
              v-model="statusFilter"
              :placeholder="$t('views.cookiemanager.37b4p5')"
              clearable
              class="filter-item"
            >
              <el-option :label="$t('views.cookiemanager.8qgc3r')" value="available" />
              <el-option :label="$t('views.cookiemanager.5t0x50')" value="temp_banned" />
              <el-option :label="$t('views.cookiemanager.e6y884')" value="perm_banned" />
              <el-option :label="$t('views.cookiemanager.81u723')" value="expired" />
            </el-select>
            <el-button type="primary" @click="handleFilter">{{$t('views.cookiemanager.1209y9')}}</el-button>
            <el-button plain @click="resetFilter">{{$t('views.cookiemanager.7cu76x')}}</el-button>
            <el-button type="success" @click="openAddCookieDialog">
              <el-icon><Plus /></el-icon>{{$t('views.cookiemanager.t4da2e')}}</el-button>
          </div>
          
          <div class="batch-actions" v-if="cookieList.length > 0">
            <el-button-group>
              <el-button type="danger" @click="batchBanAll" :loading="batchActionLoading">{{$t('views.cookiemanager.psm0p5')}}</el-button>
              <el-button type="success" @click="batchUnbanAll" :loading="batchActionLoading">{{$t('views.cookiemanager.d3v4ch')}}</el-button>
            </el-button-group>
            <el-button-group v-if="multipleSelection.length > 0" class="ml-10">
              <el-button type="warning" @click="batchTempBan" :loading="batchActionLoading">{{$t('views.cookiemanager.8v7qie')}}</el-button>
              <el-button type="danger" @click="batchPermBan" :loading="batchActionLoading">{{$t('views.cookiemanager.87x3w7')}}</el-button>
              <el-button type="success" @click="batchUnban" :loading="batchActionLoading">{{$t('views.cookiemanager.d5714o')}}</el-button>
            </el-button-group>
            <span v-if="multipleSelection.length > 0" class="selection-info">{{$t('views.cookiemanager.sh12bf')}}{{ multipleSelection.length }}{{$t('views.cookiemanager.epnr2i')}}</span>
          </div>
          
          <el-table
            v-loading="listLoading"
            :data="cookieList"
            style="width: 100%"
            border
            row-key="account_id"
            :default-sort="{ prop: 'account_id', order: 'ascending' }"
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="55" />
            <el-table-column prop="account_id" :label="$t('views.cookiemanager.fr15xl')" width="120" show-overflow-tooltip sortable />
            <el-table-column :label="$t('views.cookiemanager.oz57n9')" width="90">
              <template #default="scope">
                <el-tag size="small" effect="plain" type="info">
                  {{ scope.row.cookie_count || 0 }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="$t('views.cookiemanager.q28nq7')" show-overflow-tooltip>
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
            <el-table-column :label="$t('views.cookiemanager.w5f1e1')" width="100" sortable>
              <template #default="scope">
                <el-tag :type="getCookieStatusType(scope.row)" effect="light">
                  {{ getCookieStatusText(scope.row) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column :label="$t('views.cookiemanager.8j8u6u')" width="150" sortable>
              <template #default="scope">
                <span v-if="scope.row.expire_time">
                  {{ formatDateTime(scope.row.expire_time) }}
                </span>
                <span v-else>{{$t('views.cookiemanager.c805dh')}}</span>
              </template>
            </el-table-column>
            <el-table-column :label="$t('views.cookiemanager.s2tp53')" width="100">
              <template #default="scope">
                <el-dropdown trigger="click" @command="(command) => handleCookieCommand(command, scope.row)">
                  <el-button type="primary" size="small" plain>{{$t('views.cookiemanager.s2tp53')}}<el-icon class="el-icon--right"><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="edit">{{$t('views.cookiemanager.f46go7')}}</el-dropdown-item>
                      <el-dropdown-item command="temp_ban" v-if="!scope.row.temp_ban_until && scope.row.is_permanently_banned !== 1">{{$t('views.cookiemanager.5t0x50')}}</el-dropdown-item>
                      <el-dropdown-item command="perm_ban" v-if="scope.row.is_permanently_banned !== 1">{{$t('views.cookiemanager.e6y884')}}</el-dropdown-item>
                      <el-dropdown-item command="unban" v-if="scope.row.temp_ban_until || scope.row.is_permanently_banned === 1">{{$t('views.cookiemanager.mf8dc8')}}</el-dropdown-item>
                      <el-dropdown-item command="delete" divided>{{$t('views.cookiemanager.115uyi')}}</el-dropdown-item>
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
          <span>{{$t('views.cookiemanager.881jd7')}}</span>
        </div>
      </template>
      
      <CookieUsageChart :api-base-url="API_BASE_URL" />
    </el-card>
    <!-- 添加/编辑Cookie对话框 -->
    <el-dialog
      v-model="cookieDialogVisible"
      :title="cookieForm.account_id ? $t('views.cookiemanager.2623i5') : $t('views.cookiemanager.t4da2e')"
      width="700px"
      destroy-on-close
    >
      <el-form :model="cookieForm" label-width="120px" :rules="cookieRules" ref="cookieFormRef">
        <el-form-item :label="$t('views.cookiemanager.3xcu12')" prop="account_id">
          <el-input v-model="cookieForm.account_id" :placeholder="$t('views.cookiemanager.th42gs')" />
        </el-form-item>
        
        <el-tabs v-model="cookieInputMode" type="card">
          <!-- 字符串输入模式 -->
          <el-tab-pane :label="$t('views.cookiemanager.b34o26')" name="string">
            <el-form-item :label="$t('views.cookiemanager.uk514y')">
              <el-input v-model="cookieForm.cookie_string" type="textarea" rows="8" :placeholder="$t('views.cookiemanager.gd2jp8')" />
            </el-form-item>
          </el-tab-pane>
          
          <!-- JSON输入模式 -->
          <el-tab-pane :label="$t('views.cookiemanager.fva0k0')" name="json">
            <el-form-item label="Cookie JSON" prop="cookie_json">
              <el-input v-model="cookieForm.cookie_json" type="textarea" rows="8" :placeholder="$t('views.cookiemanager.87v8fc')" :spellcheck="false" />
              <div class="form-actions">
                <el-button size="small" type="primary" @click="formatJson">{{$t('views.cookiemanager.4883c4')}}</el-button>
                <el-button size="small" type="info" @click="convertStringToJson">{{$t('views.cookiemanager.hixo3o')}}</el-button>
              </div>
            </el-form-item>
          </el-tab-pane>
          
          <!-- 表格输入模式 -->
          <el-tab-pane :label="$t('views.cookiemanager.kr35u8')" name="table">
            <div class="table-toolbar">
              <el-button type="primary" size="small" @click="addCookieField">
                <el-icon><Plus /></el-icon>{{$t('views.cookiemanager.n1j1b9')}}</el-button>
              <el-button type="danger" size="small" @click="clearAllFields">
                <el-icon><Delete /></el-icon>{{$t('views.cookiemanager.qr83x8')}}</el-button>
            </div>
            
            <el-table :data="cookieTableData" border style="width: 100%" max-height="300px">
              <el-table-column :label="$t('views.cookiemanager.fr15xl')" width="180">
                <template #default="scope">
                  <el-input v-model="scope.row.name" :placeholder="$t('views.cookiemanager.g4qpr8')" size="small" />
                </template>
              </el-table-column>
              <el-table-column :label="$t('views.cookiemanager.q28nq7')">
                <template #default="scope">
                  <el-input v-model="scope.row.value" :placeholder="$t('views.cookiemanager.1p02i5')" size="small" />
                </template>
              </el-table-column>
              <el-table-column :label="$t('views.cookiemanager.s2tp53')" width="120">
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
              <el-button size="small" type="primary" @click="generateJsonFromTable">{{$t('views.cookiemanager.72nhk1')}}</el-button>
              <el-button size="small" type="info" @click="generateTableFromJson">{{$t('views.cookiemanager.94620b')}}</el-button>
            </div>
          </el-tab-pane>
          
          <!-- 导入模式 -->
          <el-tab-pane :label="$t('views.cookiemanager.6u74s1')" name="import">
            <el-form-item :label="$t('views.cookiemanager.v75iyb')">
              <el-select v-model="importType" :placeholder="$t('views.cookiemanager.7n8765')">
                <el-option :label="$t('views.cookiemanager.y0on43')" value="txt" />
                <el-option :label="$t('views.cookiemanager.oj2848')" value="json" />
                <el-option :label="$t('views.cookiemanager.0kmv3e')" value="csv" />
                <el-option :label="$t('views.cookiemanager.33ufz3')" value="excel" />
              </el-select>
            </el-form-item>
            
            <el-form-item :label="$t('views.cookiemanager.7y1v98')">
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
                  <el-button type="primary">{{$t('views.cookiemanager.41x3g4')}}</el-button>
                </template>
                <template #tip>
                  <div class="el-upload__tip">{{$t('views.cookiemanager.vf7cx7')}}</div>
                </template>
              </el-upload>
              <el-button type="success" @click="processCookieFile" :disabled="!selectedFile">{{$t('views.cookiemanager.2y13xa')}}</el-button>
            </el-form-item>
            
            <el-form-item :label="$t('views.cookiemanager.23tt1n')" v-if="importPreviewData.length > 0">
              <el-table :data="importPreviewData" border style="width: 100%" max-height="200px">
                <el-table-column :label="$t('views.cookiemanager.fr15xl')" prop="name" width="180" />
                <el-table-column :label="$t('views.cookiemanager.q28nq7')" prop="value" show-overflow-tooltip />
              </el-table>
              <div class="form-actions">
                <el-button size="small" type="primary" @click="confirmImport">{{$t('views.cookiemanager.f13q7e')}}</el-button>
                <el-button size="small" type="danger" @click="cancelImport">{{$t('views.cookiemanager.5c03y1')}}</el-button>
              </div>
            </el-form-item>
          </el-tab-pane>
        </el-tabs>
        
        <el-divider />
        
        <el-form-item :label="$t('views.cookiemanager.6wj7ss')">
          <el-radio-group v-model="cookieForm.expire_option">
            <el-radio :label="'none'">{{$t('views.cookiemanager.c805dh')}}</el-radio>
            <el-radio :label="'days'">{{$t('views.cookiemanager.7hkyhk')}}</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item :label="$t('views.cookiemanager.36h81u')" v-if="cookieForm.expire_option === 'days'">
          <el-input-number v-model="cookieForm.expire_days" :min="1" :max="365" />
          <span class="form-tip">{{$t('views.cookiemanager.ud3t6n')}}</span>
        </el-form-item>
        
        <el-form-item v-if="cookieForm.id" :label="$t('views.cookiemanager.w0o3pl')" prop="is_available">
          <el-switch
            v-model="cookieForm.is_available"
            :disabled="cookieForm.is_permanently_banned || cookieForm.temp_ban_until"
          />
          <span class="form-tip">{{ cookieForm.is_available ? $t('views.cookiemanager.8qgc3r') : $t('views.cookiemanager.jxt47y') }}</span>
        </el-form-item>
        
        <el-form-item v-if="cookieForm.id" :label="$t('views.cookiemanager.e6y884')" prop="is_permanently_banned">
          <el-switch v-model="cookieForm.is_permanently_banned" />
          <span class="form-tip">{{ cookieForm.is_permanently_banned ? $t('views.cookiemanager.6cqov8') : $t('views.cookiemanager.237n2f') }}</span>
        </el-form-item>
        
        <el-form-item v-if="cookieForm.id && !cookieForm.is_permanently_banned" :label="$t('views.cookiemanager.1psc3j')" prop="temp_ban_until">
          <el-date-picker
            v-model="cookieForm.temp_ban_until"
            type="datetime"
            :placeholder="$t('views.cookiemanager.bwoi8t')"
            format="YYYY-MM-DD HH:mm:ss"
            value-format="YYYY-MM-DD HH:mm:ss"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="cookieDialogVisible = false">{{$t('views.cookiemanager.fl98bx')}}</el-button>
          <el-button type="primary" @click="submitCookieForm" :loading="submitting">{{$t('views.cookiemanager.x5j4qy')}}</el-button>
        </div>
      </template>
    </el-dialog>
    
    <!-- 临时封禁对话框 -->
    <el-dialog
      v-model="tempBanDialogVisible"
      :title="$t('views.cookiemanager.bc0ucq')"
      width="400px"
      destroy-on-close
    >
      <el-form :model="tempBanForm" label-width="100px">
        <el-form-item :label="$t('views.cookiemanager.3xcu12')">
          <el-tag>{{ tempBanForm.account_id }}</el-tag>
        </el-form-item>
        <el-form-item :label="$t('views.cookiemanager.yw8177')">
          <el-input-number v-model="tempBanForm.duration_minutes" :min="1" :max="1440" />
          <span class="form-tip">{{$t('views.cookiemanager.shqml1')}}</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="tempBanDialogVisible = false">{{$t('views.cookiemanager.fl98bx')}}</el-button>
          <el-button type="primary" @click="submitTempBan" :loading="submitting">{{$t('views.cookiemanager.x5j4qy')}}</el-button>
        </div>
      </template>
    </el-dialog>
    
    <!-- 更新账号ID对话框 -->
    <el-dialog
      v-model="updateIdDialogVisible"
      :title="$t('views.cookiemanager.ee2q48')"
      width="400px"
      destroy-on-close
    >
      <el-form :model="updateIdForm" label-width="100px" :rules="updateIdRules" ref="updateIdFormRef">
        <el-form-item :label="$t('views.cookiemanager.c288pq')">
          <el-tag>{{ updateIdForm.old_account_id }}</el-tag>
        </el-form-item>
        <el-form-item :label="$t('views.cookiemanager.1w7hm4')" prop="new_account_id">
          <el-input v-model="updateIdForm.new_account_id" :placeholder="$t('views.cookiemanager.yuju0p')" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="updateIdDialogVisible = false">{{$t('views.cookiemanager.fl98bx')}}</el-button>
          <el-button type="primary" @click="submitUpdateId" :loading="submitting">{{$t('views.cookiemanager.x5j4qy')}}</el-button>
        </div>
      </template>
    </el-dialog>
    
    <!-- 查看Cookie详情对话框 -->
    <el-dialog
      v-model="accountDetailDialogVisible"
      :title="$t('views.cookiemanager.7v7w52')"
      width="700px"
      destroy-on-close
    >
      <div v-loading="accountDetailLoading">
        <el-descriptions border :column="2" v-if="accountDetail">
          <el-descriptions-item :label="$t('views.cookiemanager.fr15xl')" :span="2">{{ accountDetail.account_id }}</el-descriptions-item>
          <el-descriptions-item :label="$t('views.cookiemanager.oz57n9')">{{ accountDetail.cookie_count }}</el-descriptions-item>
          <el-descriptions-item :label="$t('views.cookiemanager.w5f1e1')">
            <el-tag :type="accountDetail.is_available ? 'success' : 'danger'">
              {{ accountDetail.is_available ? $t('views.cookiemanager.8qgc3r') : $t('views.cookiemanager.jxt47y') }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
        
        <el-divider content-position="left">{{$t('views.cookiemanager.7v7w52')}}</el-divider>
        
        <div class="cookie-detail-list" v-if="accountDetail">
          <el-input
            type="textarea"
            :rows="10"
            :placeholder="$t('views.cookiemanager.q28nq7')"
            v-model="accountDetailCookieString"
            readonly
          />
          <div class="action-row">
            <el-button type="primary" @click="copyCookieString">
              <el-icon><CopyDocument /></el-icon>{{$t('views.cookiemanager.57v4p0')}}</el-button>
          </div>
          
          <el-table :data="accountDetailCookies" style="width: 100%" border>
            <el-table-column prop="name" :label="$t('views.cookiemanager.918rdv')" width="180" />
            <el-table-column prop="value" :label="$t('views.cookiemanager.865d07')" show-overflow-tooltip />
          </el-table>
        </div>
        <el-empty v-else :description="$t('views.cookiemanager.nyl3rr')" />
      </div>
    </el-dialog>
    
    <!-- 测试结果对话框 -->
    <el-dialog
      v-model="testResultDialogVisible"
      :title="$t('views.cookiemanager.47d298')"
      width="500px"
      destroy-on-close
    >
      <div v-loading="testingAccount">
        <template v-if="testResult">
          <el-result
            :icon="testResult.is_valid ? 'success' : 'error'"
            :title="testResult.is_valid ? $t('views.cookiemanager.a3782e') : $t('views.cookiemanager.29gqz2')"
            :sub-title="testResult.message"
          >
            <template #extra>
              <el-descriptions border :column="1">
                <el-descriptions-item :label="$t('views.cookiemanager.3xcu12')">{{ testResult.account_id }}</el-descriptions-item>
                <el-descriptions-item :label="$t('views.cookiemanager.h324e4')">{{ testResult.status }}</el-descriptions-item>
                <el-descriptions-item :label="$t('views.cookiemanager.1wxu3a')">{{ testResult.action_taken }}</el-descriptions-item>
              </el-descriptions>
            </template>
          </el-result>
        </template>
        <el-empty v-else :description="$t('views.cookiemanager.6y0q17')" />
      </div>
    </el-dialog>
    
    <!-- 批量测试结果对话框 -->
    <el-dialog
      v-model="batchTestResultDialogVisible"
      :title="$t('views.cookiemanager.d1w998')"
      width="700px"
      destroy-on-close
    >
      <div v-loading="testingAll">
        <template v-if="batchTestResult">
          <el-descriptions border :column="2">
            <el-descriptions-item :label="$t('views.cookiemanager.5e9o59')">{{ batchTestResult.total_tested }}</el-descriptions-item>
            <el-descriptions-item :label="$t('views.cookiemanager.8k2v29')">
              <el-tag type="success">{{ batchTestResult.valid_count }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item :label="$t('views.cookiemanager.31k5ft')">
              <el-tag type="warning">{{ batchTestResult.banned_count }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item :label="$t('views.cookiemanager.7r1583')">
              <el-tag type="danger">{{ batchTestResult.not_login_count }}</el-tag>
            </el-descriptions-item>
          </el-descriptions>
          
          <el-divider />
          
          <el-tabs>
            <el-tab-pane :label="$t('views.cookiemanager.95c723')">
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
                <el-empty v-if="!batchTestResult.valid_accounts.length" :description="$t('views.cookiemanager.6zi5yp')" />
              </div>
            </el-tab-pane>
            <el-tab-pane :label="$t('views.cookiemanager.1j3e7c')">
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
                <el-empty v-if="!batchTestResult.banned_accounts.length" :description="$t('views.cookiemanager.4uia1i')" />
              </div>
            </el-tab-pane>
            <el-tab-pane :label="$t('views.cookiemanager.nf4qda')">
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
                
                <el-empty v-if="!batchTestResult.not_login_accounts.length" :description="$t('views.cookiemanager.qjcdc8')" />
              </div>
            </el-tab-pane>
          </el-tabs>
        </template>
        <el-empty v-else :description="$t('views.cookiemanager.6y0q17')" />
      </div>
    </el-dialog>
    
    <!-- 添加批量临时封禁对话框 -->
    <el-dialog
      v-model="batchTempBanDialogVisible"
      :title="$t('views.cookiemanager.5t4569')"
      width="400px"
      destroy-on-close
    >
      <el-form :model="batchTempBanForm" label-width="100px">
        <el-form-item :label="$t('views.cookiemanager.yw8177')">
          <el-input-number v-model="batchTempBanForm.duration_minutes" :min="1" :max="1440" />
          <span class="form-tip">{{$t('views.cookiemanager.shqml1')}}</span>
        </el-form-item>
        <el-form-item :label="$t('views.cookiemanager.bmf617')">
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
          <el-button @click="batchTempBanDialogVisible = false">{{$t('views.cookiemanager.fl98bx')}}</el-button>
          <el-button type="primary" @click="submitBatchTempBan" :loading="batchActionLoading">{{$t('views.cookiemanager.x5j4qy')}}</el-button>
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
  color: var(--color-text-main);
  margin: 0;
  background: linear-gradient(45deg, var(--color-primary), #8b5cf6);
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
  background-color: var(--color-bg-subtle);
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
  color: var(--color-text-secondary);
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
  color: var(--color-text-secondary);
}

.account-list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid var(--color-border);
  border-radius: 4px;
}

.account-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid var(--color-border);
  transition: background-color 0.3s;
}

.account-item:hover {
  background-color: var(--color-bg-subtle);
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
  background-color: var(--color-bg-subtle);
  border-bottom: 1px solid var(--color-border);
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
  border-bottom: 1px solid var(--color-border);
  gap: 15px;
}

.banned-account-item:last-child {
  border-bottom: none;
}

.banned-account-item:hover {
  background-color: var(--color-bg-subtle);
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
  color: var(--color-text-main);
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
  color: var(--color-text-secondary);
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
  color: var(--color-text-secondary);
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
  color: var(--color-text-secondary);
  line-height: 1.4;
}

.dialog-subtitle {
  margin: 0 0 15px 0;
  padding-bottom: 10px;
  font-size: 16px;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-primary);
}

.batch-actions {
  margin: 10px 0;
  display: flex;
  align-items: center;
}

.selection-info {
  margin-left: 15px;
  color: var(--color-text-secondary);
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
  border: 1px solid var(--color-border);
  border-radius: 4px;
}
</style>