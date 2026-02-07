<script setup lang="ts">
// @ts-nocheck
import { ref, reactive, onMounted, computed, onUnmounted } from "vue";
import { useI18n } from "vue-i18n";
import { ElMessage, ElMessageBox, ElNotification } from "element-plus";
import {
  Refresh,
  Plus,
  Delete,
  Connection,
  Search,
  CopyDocument,
  RefreshRight,
  ArrowDown,
  Check,
} from "@element-plus/icons-vue";
import axios from "axios";
import CookieUsageChart from "@/components/CookieUsageChart.vue";
import { useClipboard } from "@vueuse/core";
import { useTaskStore } from "@/stores/task";
import "element-plus/es/components/message/style/css";
import "element-plus/es/components/message-box/style/css";
import { Warning, View, Edit, Clock } from "@element-plus/icons-vue";

const { copy, isSupported } = useClipboard();

import { apiBaseUrl } from "@/config/api";

// API连接状态
const apiConnected = ref(false);

// 加载状态
const statusLoading = ref(false);
const accountsLoading = ref(false);
const bannedLoading = ref(false);
const listLoading = ref(false);
const submitting = ref(false);
const syncing = ref(false);
const testingAccount = ref(false);
const testingAll = ref(false);
const updatingStatus = ref(false);
const cleaningUp = ref(false);
const accountDetailLoading = ref(false);
const loading = ref(false);
const updatingAbSr = ref(false);

const { t: $t } = useI18n();

// Cookie池统计
const cookieStats = reactive({
  total: 0,
  available: 0,
  tempBanned: 0,
  permBanned: 0,
});

// 账号列表
const availableAccounts = ref<string[]>([]);
const tempBannedAccounts = ref<any[]>([]);
const permBannedAccounts = ref<string[]>([]);
const bannedTabActive = ref("temp");

// 封禁Cookie的多选状态
const tempBannedSelection = ref<string[]>([]);
const permBannedSelection = ref<string[]>([]);
const checkAllTemp = ref(false);
const checkAllPerm = ref(false);

const isTempIndeterminate = computed(() => {
  return (
    tempBannedSelection.value.length > 0 &&
    tempBannedSelection.value.length < tempBannedAccounts.value.length
  );
});
const isPermIndeterminate = computed(() => {
  return (
    permBannedSelection.value.length > 0 &&
    permBannedSelection.value.length < permBannedAccounts.value.length
  );
});

// Cookie列表
const cookieList = ref<any[]>([]);
const cookies = ref([]);
const currentCookie = ref(null);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(10);

// 搜索和筛选
const searchAccount = ref("");
const searchKeyword = ref("");
const statusFilter = ref("");

// 对话框可见性
const cookieDialogVisible = ref(false);
const tempBanDialogVisible = ref(false);
const updateIdDialogVisible = ref(false);
const accountDetailDialogVisible = ref(false);
const testResultDialogVisible = ref(false);
const batchTestResultDialogVisible = ref(false);
const dialogVisible = ref(false);

// 表单数据
const cookieFormRef = ref(null);
const cookieForm = reactive({
  id: null as number | null,
  account_id: "",
  cookie_name: "",
  cookie_value: "",
  cookie_string: "",
  cookie_json: "{}",
  use_string_input: false,
  expire_days: null,
  expire_option: "none",
  is_available: true,
  is_permanently_banned: false,
  temp_ban_until: null as string | null,
});

const tempBanForm = reactive({
  account_id: "",
  duration_minutes: 30,
});

const updateIdFormRef = ref(null);
const updateIdForm = reactive({
  old_account_id: "",
  new_account_id: "",
});

// 账号详情
const accountDetail = ref(null as any);
const accountDetailCookies = computed(() => {
  if (!accountDetail.value || !accountDetail.value.cookies) return [];
  return Object.entries(accountDetail.value.cookies).map(([name, value]) => ({
    name,
    value,
  }));
});
const accountDetailCookieString = computed(() => {
  if (!accountDetail.value || !accountDetail.value.cookies) return "";
  return Object.entries(accountDetail.value.cookies)
    .map(([name, value]) => `${name}=${value}`)
    .join("; ");
});

// 测试结果
const testResult = ref(null as any);
const batchTestResult = ref(null as any);

// 表单验证规则
const cookieRules = {
  account_id: [
    { required: true, message: "请输入百度账号ID", trigger: "blur" },
    { min: 2, max: 50, message: "长度在 2 到 50 个字符", trigger: "blur" },
  ],
};

const updateIdRules = {
  new_account_id: [
    { required: true, message: "请输入新的账号ID", trigger: "blur" },
    { min: 2, max: 50, message: "长度在 2 到 50 个字符", trigger: "blur" },
  ],
};

// Cookie池状态
const cookiePoolStatus = ref({
  total: 0,
  available: 0,
  blocked: 0,
  cooldown_status: {},
});

// 添加计时器引用
const banTimeUpdateTimer = ref(null);

// 添加Cookie编辑所需的变量
const cookieInputMode = ref("string");
const cookieTableData = ref<{ name: string; value: string }[]>([]);
const importType = ref("txt");
const fileList = ref<any[]>([]);
const selectedFile = ref<File | null>(null);
const importPreviewData = ref<{ name: string; value: string }[]>([]);

// 根据导入类型返回对应的文件接受格式
const importFileAccept = computed(() => {
  switch (importType.value) {
    case "txt":
      return ".txt";
    case "json":
      return ".json";
    case "csv":
      return ".csv";
    case "excel":
      return ".xlsx,.xls";
    default:
      return "";
  }
});

// 加载Cookie池状态
const refreshCookieStatus = async () => {
  statusLoading.value = true;
  try {
    await checkApiConnection();

    const response = await axios.get(
      `${apiBaseUrl}/admin/cookie/pool-status`,
    );
    if (response.data.code === 10000) {
      const data = response.data.data;
      cookieStats.total = data.total || 0;
      cookieStats.available = data.available || 0;
      cookieStats.tempBanned = data.temp_banned || 0;
      cookieStats.permBanned = data.perm_banned || 0;

      // 添加日志以便调试
      console.log($t("views.cookiemanager.ok8s0f"), data);
    } else {
      ElMessage.error($t("views.cookiemanager.fm55wb", [response.data.msg]));
    }
  } catch (error) {
    console.error($t("views.cookiemanager.2bd8so"), error);
    ElMessage.error($t("views.cookiemanager.vkiw1q"));
  } finally {
    statusLoading.value = false;
  }
};

// 检查API连接状态
const checkApiConnection = async () => {
  try {
    const response = await axios.get(`${apiBaseUrl}/health`, {
      timeout: 3000,
    });
    apiConnected.value = response.status === 200;
    return apiConnected.value;
  } catch (error) {
    apiConnected.value = false;
    return false;
  }
};

// 加载可用Cookie列表
const loadAvailableAccounts = async () => {
  accountsLoading.value = true;
  try {
    const response = await axios.get(
      `${apiBaseUrl}/admin/cookie/available-accounts`,
    );
    if (response.data.code === 10000) {
      availableAccounts.value = response.data.data.account_ids || [];
      console.log($t("views.cookiemanager.8d2gqe"), availableAccounts.value);
    } else {
      ElMessage.error($t("views.cookiemanager.c3ne55", [response.data.msg]));
    }
  } catch (error) {
    console.error($t("views.cookiemanager.14o491"), error);
    ElMessage.error($t("views.cookiemanager.py5gs8"));
  } finally {
    accountsLoading.value = false;
  }
};

// 加载被封禁的Cookie
const loadBannedAccounts = async () => {
  bannedLoading.value = true;
  try {
    const response = await axios.get(
      `${apiBaseUrl}/admin/cookie/banned-accounts`,
    );
    if (response.data.code === 10000) {
      // 正确解析临时封禁Cookie
      const tempBanned = response.data.data.temp_banned || [];
      tempBannedAccounts.value = tempBanned.map((account) => ({
        account_id: account.account_id,
        temp_ban_until: account.temp_ban_until,
        remaining_seconds: account.remaining_seconds,
      }));

      // 正确解析永久封禁Cookie
      permBannedAccounts.value = response.data.data.perm_banned || [];

      console.log($t("views.cookiemanager.984551"), tempBannedAccounts.value);
      console.log($t("views.cookiemanager.e324p4"), permBannedAccounts.value);
    } else {
      ElMessage.error($t("views.cookiemanager.21x5u6", [response.data.msg]));
    }
  } catch (error) {
    console.error($t("views.cookiemanager.i5lwf1"), error);
    ElMessage.error($t("views.cookiemanager.gutb5a"));
  } finally {
    bannedLoading.value = false;
  }
};

// 加载Cookie列表
const loadCookies = async () => {
  listLoading.value = true;
  try {
    const params = {
      page: currentPage.value,
      limit: pageSize.value,
      account_id: searchAccount.value || undefined,
      available_only: statusFilter.value === "available" ? true : undefined,
      status: statusFilter.value || undefined,
    };

    const response = await axios.get(`${apiBaseUrl}/admin/cookie/list`, {
      params,
    });
    if (response.data.code === 10000) {
      cookieList.value = (response.data.data.data || []).map((item) => {
        // 如果有cookies字段，将其转换为字符串以便显示
        if (item.cookies && typeof item.cookies === "object") {
          const cookieCount = Object.keys(item.cookies).length;
          const cookieString = Object.entries(item.cookies)
            .map(([name, value]) => `${name}=${value}`)
            .join("; ");

          return {
            ...item,
            cookie_count: cookieCount,
            cookie_value: cookieString,
          };
        }
        return item;
      });

      console.log($t("views.cookiemanager.1951zu"), cookieList.value);

      // 如果后端返回了总数，使用后端的总数
      if (response.data.data && response.data.data.total !== undefined) {
        total.value = response.data.data.total;
      } else {
        total.value = cookieList.value.length;
      }
    } else {
      ElMessage.error($t("views.cookiemanager.22y82w", [response.data.msg]));
    }
  } catch (error) {
    console.error($t("views.cookiemanager.6cm2xs"), error);
    ElMessage.error($t("views.cookiemanager.sm2pes"));
  } finally {
    listLoading.value = false;
  }
};

// 处理筛选
const handleFilter = () => {
  currentPage.value = 1;
  loadCookies();
};

// 重置筛选
const resetFilter = () => {
  searchAccount.value = "";
  statusFilter.value = "";
  currentPage.value = 1;
  loadCookies();
};

// 处理分页
const handleSizeChange = (size: number) => {
  pageSize.value = size;
  loadCookies();
};

const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  loadCookies();
};

// 打开添加Cookie对话框
const openAddCookieDialog = () => {
  // 重置表单
  Object.assign(cookieForm, {
    id: null,
    account_id: "",
    cookie_name: "",
    cookie_value: "",
    cookie_string: "",
    cookie_json: "{}",
    use_string_input: false,
    expire_days: null,
    expire_option: "none",
    is_available: true,
    is_permanently_banned: false,
    temp_ban_until: null,
  });

  // 重置表格数据
  cookieTableData.value = [];
  // 重置导入数据
  importPreviewData.value = [];
  fileList.value = [];
  selectedFile.value = null;
  // 设置默认编辑模式
  cookieInputMode.value = "string";

  cookieDialogVisible.value = true;
};

// 编辑Cookie
const editCookie = async (cookie: any) => {
  try {
    loading.value = true;

    // 获取完整的Cookie信息
    const response = await axios.get(
      `${apiBaseUrl}/admin/cookie/account-cookie/${cookie.account_id}`,
    );

    if (response.data.code === 10000) {
      const data = response.data.data;

      // 将cookies对象转换为字符串
      let cookieString = "";
      if (data.cookies) {
        cookieString = Object.entries(data.cookies)
          .map(([name, value]) => `${name}=${value}`)
          .join("; ");
      }

      // 将cookies对象转换为JSON字符串
      let cookieJson = "{}";
      if (data.cookies) {
        cookieJson = JSON.stringify(data.cookies, null, 2);
      }

      // 根据是否有过期时间设置expire_option
      const hasExpireTime = cookie.expire_time !== null;

      Object.assign(cookieForm, {
        id: cookie.id,
        account_id: data.account_id, // 确保设置了id，用于标识这是编辑操作
        cookie_name: "",
        cookie_value: "",
        cookie_string: cookieString,
        cookie_json: cookieJson,
        use_string_input: true, // 使用字符串模式编辑
        expire_days: hasExpireTime ? 365 : null,
        expire_option: hasExpireTime ? "days" : "none",
        is_available: !!cookie.is_available,
        is_permanently_banned: !!cookie.is_permanently_banned,
        temp_ban_until: cookie.temp_ban_until,
      });

      // 初始化表格数据
      cookieTableData.value = Object.entries(data.cookies || {}).map(
        ([name, value]) => ({
          name,
          value: value as string,
        }),
      );

      // 设置编辑模式
      cookieInputMode.value = "json";

      cookieDialogVisible.value = true;

      console.log($t("views.cookiemanager.q46d47"), cookieForm);
    } else {
      ElMessage.error($t("views.cookiemanager.68uf7c", [response.data.msg]));
    }
  } catch (error) {
    console.error($t("views.cookiemanager.u46r6j"), error);
    ElMessage.error($t("views.cookiemanager.o82who"));
  } finally {
    loading.value = false;
  }
};

// 提交Cookie表单
const submitCookieForm = async () => {
  if (!cookieFormRef.value) return;

  try {
    await (cookieFormRef.value as any).validate();

    submitting.value = true;

    let response;
    const cookieData: any = {
      account_id: cookieForm.account_id,
    };

    // 根据当前编辑模式处理Cookie数据
    switch (cookieInputMode.value) {
      case "string":
        // 字符串模式 - 将字符串解析为对象
        try {
          // 检查是否有字符串输入
          if (
            !cookieForm.cookie_string ||
            cookieForm.cookie_string.trim() === ""
          ) {
            // 警告但不阻止提交，使用空对象
            ElMessage.warning($t("views.cookiemanager.a4lvkm"));
            cookieData.cookie_data = {};
          } else {
            const cookieObj = {};
            const cookieParts = cookieForm.cookie_string.split(";");

            cookieParts.forEach((cookie) => {
              const trimmedCookie = cookie.trim();
              if (!trimmedCookie) return;

              // 查找第一个等号的位置
              const equalSignIndex = trimmedCookie.indexOf("=");
              if (equalSignIndex > 0) {
                const name = trimmedCookie.substring(0, equalSignIndex).trim();
                const value = trimmedCookie
                  .substring(equalSignIndex + 1)
                  .trim();
                cookieObj[name] = value;
              }
            });

            cookieData.cookie_data = cookieObj;
          }
          console.log($t("views.cookiemanager.86m8s2"), cookieData.cookie_data);
        } catch (e) {
          console.error($t("views.cookiemanager.c54ryv"), e);
          ElMessage.error($t("views.cookiemanager.lc547n"));
          submitting.value = false;
          return;
        }
        break;
      case "json":
        // JSON模式
        try {
          const jsonData = JSON.parse(cookieForm.cookie_json);

          // 检查是否是嵌套结构 (避免格式为 {account_id: xxx, cookie_data: {}} 的情况)
          if (jsonData.cookie_data) {
            cookieData.cookie_data = jsonData.cookie_data;
          } else {
            cookieData.cookie_data = jsonData;
          }
        } catch (e) {
          console.error($t("views.cookiemanager.17ykj8"), e);
          ElMessage.error($t("views.cookiemanager.y32143"));
          submitting.value = false;
          return;
        }
        break;
      case "table":
        // 表格模式
        if (cookieTableData.value.length === 0) {
          ElMessage.error($t("views.cookiemanager.mu4bkt"));
          submitting.value = false;
          return;
        }

        // 验证表格数据
        for (const row of cookieTableData.value) {
          if (!row.name.trim()) {
            ElMessage.error($t("views.cookiemanager.o60i16"));
            submitting.value = false;
            return;
          }
        }

        // 转换表格数据为对象
        const tableData = {};
        cookieTableData.value.forEach((row) => {
          // 避免特殊字段导致嵌套
          if (
            row.name !== "account_id" &&
            row.name !== "cookie_data" &&
            row.name !== "expire_days"
          ) {
            tableData[row.name] = row.value;
          }
        });
        cookieData.cookie_data = tableData;
        break;
      case "import":
        // 导入模式
        if (importPreviewData.value.length === 0) {
          ElMessage.error($t("views.cookiemanager.d57we7"));
          submitting.value = false;
          return;
        }

        // 转换导入数据为对象
        const importData = {};
        importPreviewData.value.forEach((row) => {
          // 避免特殊字段导致嵌套
          if (
            row.name !== "account_id" &&
            row.name !== "cookie_data" &&
            row.name !== "expire_days"
          ) {
            importData[row.name] = row.value;
          }
        });
        cookieData.cookie_data = importData;
        break;
    }

    // 根据expire_option决定是否设置过期时间
    if (cookieForm.expire_option === "days" && cookieForm.expire_days) {
      cookieData.expire_days = cookieForm.expire_days;
    }
    // 如果expire_option为none，则不设置expire_days，后端默认为null

    console.log($t("views.cookiemanager.4534pf"), cookieData);

    // 添加详细的日志，方便调试
    console.log(
      $t("views.cookiemanager.4534pf"),
      JSON.stringify(cookieData, null, 2),
    );

    if (cookieForm.id) {
      // 更新Cookie
      cookieData.is_available = cookieForm.is_available ? 1 : 0;
      cookieData.is_permanently_banned = cookieForm.is_permanently_banned
        ? 1
        : 0;
      cookieData.temp_ban_until = cookieForm.temp_ban_until;

      response = await axios.put(
        `${apiBaseUrl}/admin/cookie/update/${cookieForm.id}`,
        cookieData,
      );
    } else {
      // 添加Cookie
      response = await axios.post(
        `${apiBaseUrl}/admin/cookie/add`,
        cookieData,
      );
    }

    if (response.data.code === 10000) {
      ElMessage.success(
        cookieForm.id
          ? $t("views.cookiemanager.amde31")
          : $t("views.cookiemanager.5y2dsc"),
      );
      cookieDialogVisible.value = false;
      refreshCookieStatus();
      loadCookies();
      loadAvailableAccounts();
      loadBannedAccounts();
    } else {
      ElMessage.error(
        `${cookieForm.id ? $t("views.cookiemanager.g2987l") : $t("views.cookiemanager.t4da2e")}Cookie失败: ${response.data.msg}`,
      );
    }
  } catch (error: any) {
    if (error.message) {
      ElMessage.error(error.message);
    } else {
      console.error($t("views.cookiemanager.i2lq17"), error);
      ElMessage.error(
        `${cookieForm.id ? $t("views.cookiemanager.g2987l") : $t("views.cookiemanager.t4da2e")}Cookie失败，请检查网络连接`,
      );
    }
  } finally {
    submitting.value = false;
  }
};

// Cookie编辑 - JSON格式化
const formatJson = () => {
  try {
    const parsed = JSON.parse(cookieForm.cookie_json);
    cookieForm.cookie_json = JSON.stringify(parsed, null, 2);
  } catch (e) {
    ElMessage.error($t("views.cookiemanager.0739dv"));
  }
};

// Cookie编辑 - 字符串转JSON
const convertStringToJson = () => {
  if (!cookieForm.cookie_string) {
    ElMessage.warning($t("views.cookiemanager.669359"));
    return;
  }

  try {
    // 解析Cookie字符串为对象
    const cookieObj = {};
    const cookieParts = cookieForm.cookie_string.split(";");

    cookieParts.forEach((cookie) => {
      const trimmedCookie = cookie.trim();
      if (!trimmedCookie) return;

      // 查找第一个等号的位置
      const equalSignIndex = trimmedCookie.indexOf("=");
      if (equalSignIndex > 0) {
        const name = trimmedCookie.substring(0, equalSignIndex).trim();
        const value = trimmedCookie.substring(equalSignIndex + 1).trim();
        cookieObj[name] = value;
      }
    });

    // 转换为格式化的JSON
    cookieForm.cookie_json = JSON.stringify(cookieObj, null, 2);

    // 切换到JSON模式
    cookieInputMode.value = "json";

    ElMessage.success($t("views.cookiemanager.474st2"));
  } catch (e) {
    console.error($t("views.cookiemanager.67p41h"), e);
    ElMessage.error($t("views.cookiemanager.8649r1"));
  }
};

// Cookie编辑 - 表格添加字段
const addCookieField = () => {
  cookieTableData.value.push({ name: "", value: "" });
};

// Cookie编辑 - 表格删除字段
const removeCookieField = (index: number) => {
  cookieTableData.value.splice(index, 1);
};

// Cookie编辑 - 清空所有字段
const clearAllFields = () => {
  ElMessageBox.confirm(
    $t("views.cookiemanager.gyo861"),
    $t("views.cookiemanager.lwo521"),
    {
      confirmButtonText: $t("views.cookiemanager.86icn7"),
      cancelButtonText: $t("views.cookiemanager.fl98bx"),
      type: "warning",
    },
  )
    .then(() => {
      cookieTableData.value = [];
      ElMessage.success($t("views.cookiemanager.62h3wn"));
    })
    .catch(() => {});
};

// Cookie编辑 - 表格数据转JSON
const generateJsonFromTable = () => {
  if (cookieTableData.value.length === 0) {
    ElMessage.warning($t("views.cookiemanager.mu4bkt"));
    return;
  }

  const jsonObj = {};
  cookieTableData.value.forEach((row) => {
    if (row.name) {
      jsonObj[row.name] = row.value;
    }
  });

  cookieForm.cookie_json = JSON.stringify(jsonObj, null, 2);
  cookieInputMode.value = "json";
  ElMessage.success($t("views.cookiemanager.te3wwq"));
};

// Cookie编辑 - JSON转表格数据
const generateTableFromJson = () => {
  try {
    const jsonObj = JSON.parse(cookieForm.cookie_json);

    cookieTableData.value = Object.entries(jsonObj).map(([name, value]) => ({
      name,
      value: value as string,
    }));

    cookieInputMode.value = "table";
    ElMessage.success($t("views.cookiemanager.474st2"));
  } catch (e) {
    ElMessage.error($t("views.cookiemanager.0739dv"));
  }
};

// Cookie编辑 - 处理文件变更
const handleFileChange = (file: any) => {
  selectedFile.value = file.raw;
};

// Cookie编辑 - 处理Cookie文件
const processCookieFile = async () => {
  if (!selectedFile.value) {
    ElMessage.warning($t("views.cookiemanager.9s4ovr"));
    return;
  }

  importPreviewData.value = [];

  try {
    const file = selectedFile.value;

    // 根据导入类型处理文件内容
    switch (importType.value) {
      case "txt":
      case "json":
      case "csv":
        const fileContent = await readFileContent(file);
        if (importType.value === "txt") {
          processTxtContent(fileContent);
        } else if (importType.value === "json") {
          processJsonContent(fileContent);
        } else if (importType.value === "csv") {
          processCsvContent(fileContent);
        }
        break;
      case "excel":
        await processExcelFile(file);
        break;
    }
  } catch (error) {
    console.error($t("views.cookiemanager.24z4mk"), error);
    ElMessage.error($t("views.cookiemanager.2353e1"));
  }
};

// 读取文件内容
const readFileContent = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (event) => {
      if (event.target?.result) {
        resolve(event.target.result as string);
      } else {
        reject(new Error($t("views.cookiemanager.y828v3")));
      }
    };

    reader.onerror = () => {
      reject(new Error($t("views.cookiemanager.7iz0dx")));
    };

    reader.readAsText(file);
  });
};

// 处理TXT文件内容（假设格式为 name=value 或 name:value，每行一个）
const processTxtContent = (content: string) => {
  const lines = content.split("\n").filter((line) => line.trim());
  const result = [];

  for (const line of lines) {
    let name = "",
      value = "";

    if (line.includes("=")) {
      [name, value] = line.trim().split("=", 2);
    } else if (line.includes(":")) {
      [name, value] = line.trim().split(":", 2);
    }

    if (name && value) {
      result.push({ name: name.trim(), value: value.trim() });
    }
  }

  if (result.length > 0) {
    importPreviewData.value = result;
    ElMessage.success($t("views.cookiemanager.7tlafi", [result.length]));
  } else {
    ElMessage.error($t("views.cookiemanager.w23bv8"));
  }
};

// 处理JSON文件内容
const processJsonContent = (content: string) => {
  try {
    const jsonObj = JSON.parse(content);

    const result = Object.entries(jsonObj).map(([name, value]) => ({
      name,
      value: typeof value === "string" ? value : JSON.stringify(value),
    }));

    if (result.length > 0) {
      importPreviewData.value = result;
      ElMessage.success($t("views.cookiemanager.7tlafi", [result.length]));
    } else {
      ElMessage.error($t("views.cookiemanager.55yo7s"));
    }
  } catch (e) {
    ElMessage.error($t("views.cookiemanager.o453w6"));
  }
};

// 处理CSV文件内容（假设格式为两列：name,value）
const processCsvContent = (content: string) => {
  const lines = content.split("\n").filter((line) => line.trim());
  const result = [];

  // 检查是否有标题行
  const hasHeader =
    lines[0].toLowerCase().includes("name") &&
    (lines[0].toLowerCase().includes("value") ||
      lines[0].toLowerCase().includes("val"));

  // 从第一行或第二行开始处理（如果有标题行则从第二行开始）
  const startIndex = hasHeader ? 1 : 0;

  for (let i = startIndex; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;

    // 解析CSV行，处理引号和逗号的情况
    const values = parseCSVLine(line);

    if (values.length >= 2) {
      result.push({
        name: values[0].trim(),
        value: values[1].trim(),
      });
    }
  }

  if (result.length > 0) {
    importPreviewData.value = result;
    ElMessage.success($t("views.cookiemanager.7tlafi", [result.length]));
  } else {
    ElMessage.error($t("views.cookiemanager.714h0d"));
  }
};

// 解析CSV行，处理引号和逗号
const parseCSVLine = (line: string): string[] => {
  const result = [];
  let current = "";
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];

    if (char === '"' && (i === 0 || line[i - 1] !== "\\")) {
      inQuotes = !inQuotes;
    } else if (char === "," && !inQuotes) {
      result.push(current);
      current = "";
    } else {
      current += char;
    }
  }

  result.push(current);
  return result;
};

// 确认导入预览数据
const confirmImport = () => {
  if (importPreviewData.value.length === 0) {
    ElMessage.warning($t("views.cookiemanager.125i38"));
    return;
  }

  // 生成JSON格式
  const jsonObj = {};
  importPreviewData.value.forEach((row) => {
    if (row.name) {
      jsonObj[row.name] = row.value;
    }
  });

  // 更新表单
  cookieForm.cookie_json = JSON.stringify(jsonObj, null, 2);

  // 更新表格数据
  cookieTableData.value = [...importPreviewData.value];

  // 切换到JSON模式
  cookieInputMode.value = "json";

  // 清理导入数据
  importPreviewData.value = [];
  fileList.value = [];
  selectedFile.value = null;

  ElMessage.success($t("views.cookiemanager.m1eb6y"));
};

// 取消导入
const cancelImport = () => {
  importPreviewData.value = [];
  fileList.value = [];
  selectedFile.value = null;
  ElMessage.info($t("views.cookiemanager.o9m48o"));
};

// 删除Cookie
const deleteCookie = async (account_id: number) => {
  try {
    await ElMessageBox.confirm(
      $t("views.cookiemanager.b475w4"),
      $t("views.cookiemanager.2o2809"),
      {
        confirmButtonText: $t("views.cookiemanager.115uyi"),
        cancelButtonText: $t("views.cookiemanager.fl98bx"),
        type: "warning",
      },
    );

    listLoading.value = true;

    const response = await axios.delete(
      `${apiBaseUrl}/admin/cookie/delete/${account_id}`,
    );
    if (response.data.code === 10000) {
      ElMessage.success($t("views.cookiemanager.d4y7wo"));
      loadCookies();
      refreshCookieStatus();
    } else {
      ElMessage.error($t("views.cookiemanager.2y37t2", [response.data.msg]));
    }
  } catch (error: any) {
    if (error !== "cancel") {
      console.error($t("views.cookiemanager.88gk5b"), error);
      ElMessage.error($t("views.cookiemanager.qp7ts2"));
    }
  } finally {
    listLoading.value = false;
  }
};

// 生命周期钩子
onMounted(() => {
  checkApiConnection();
  refreshCookieStatus();
  loadAvailableAccounts();
  loadBannedAccounts();
  loadCookies();

  // 设置每5秒更新一次解封时间的计时器
  banTimeUpdateTimer.value = setInterval(() => {
    updateBanTimeRemaining();
    // 每分钟刷新一次被封禁的Cookie列表
    if (new Date().getSeconds() === 0) {
      loadBannedAccounts();
    }
  }, 5000);
});

// 在组件卸载时清除计时器
onUnmounted(() => {
  if (banTimeUpdateTimer.value) {
    clearInterval(banTimeUpdateTimer.value);
  }
});

// 解封Cookie
const unbanCookie = async (id: number) => {
  try {
    listLoading.value = true;

    const response = await axios.post(
      `${apiBaseUrl}/admin/cookie/unban/${id}`,
    );
    if (response.data.code === 10000) {
      ElMessage.success($t("views.cookiemanager.71bw8q"));
      loadCookies();
      refreshCookieStatus();
    } else {
      ElMessage.error($t("views.cookiemanager.4kt337", [response.data.msg]));
    }
  } catch (error) {
    console.error($t("views.cookiemanager.25o26b"), error);
    ElMessage.error($t("views.cookiemanager.4xpz05"));
  } finally {
    listLoading.value = false;
  }
};

// 同步到Redis
const syncToRedis = async () => {
  try {
    syncing.value = true;

    const response = await axios.post(
      `${apiBaseUrl}/admin/cookie/sync-to-redis`,
    );
    if (response.data.code === 10000) {
      ElMessage.success($t("views.cookiemanager.dn1070"));
      refreshCookieStatus();
    } else {
      ElMessage.error($t("views.cookiemanager.c77ri3", [response.data.msg]));
    }
  } catch (error) {
    console.error($t("views.cookiemanager.zvb424"), error);
    ElMessage.error($t("views.cookiemanager.gp1dd8"));
  } finally {
    syncing.value = false;
  }
};

// 更新ab_sr cookie
const updateAbSr = async () => {
  try {
    updatingAbSr.value = true;

    const response = await axios.post(
      `${apiBaseUrl}/admin/cookie/update-ab-sr`,
    );
    if (response.data.code === 10000) {
      ElMessage.success(response.data.msg);
      refreshCookieStatus();
      loadCookies();
    } else {
      ElMessage.error($t("views.cookiemanager.lv56y5", [response.data.msg]));
    }
  } catch (error) {
    console.error($t("views.cookiemanager.5kcqge"), error);
    ElMessage.error($t("views.cookiemanager.gp1dd8"));
  } finally {
    updatingAbSr.value = false;
  }
};

// 测试单个Cookie可用性
const testAccountAvailability = async (accountId: string) => {
  try {
    testingAccount.value = true;
    testResult.value = null;
    testResultDialogVisible.value = true;

    const response = await axios.post(
      `${apiBaseUrl}/admin/cookie/test-account-availability/${accountId}`,
    );
    if (response.data.code === 10000) {
      testResult.value = response.data.data;
    } else {
      ElMessage.error($t("views.cookiemanager.bj07v2", [response.data.msg]));
      testResultDialogVisible.value = false;
    }
  } catch (error) {
    console.error($t("views.cookiemanager.937l19"), error);
    ElMessage.error($t("views.cookiemanager.29gqz2"));
    testResultDialogVisible.value = false;
  } finally {
    testingAccount.value = false;
  }
};

// 测试所有Cookie可用性
const testAllCookiesAvailability = async () => {
  try {
    testingAll.value = true;
    batchTestResult.value = null;
    batchTestResultDialogVisible.value = true;

    const response = await axios.post(
      `${apiBaseUrl}/admin/cookie/test-availability`,
    );
    if (response.data.code === 10000) {
      batchTestResult.value = response.data.data;
    } else {
      ElMessage.error($t("views.cookiemanager.bj07v2", [response.data.msg]));
      batchTestResultDialogVisible.value = false;
    }
  } catch (error) {
    console.error($t("views.cookiemanager.348816"), error);
    ElMessage.error($t("views.cookiemanager.279nuo"));
    batchTestResultDialogVisible.value = false;
  } finally {
    testingAll.value = false;
  }
};
// 更新Cookie状态
const updateCookieStatus = async () => {
  try {
    updatingStatus.value = true;

    const response = await axios.post(
      `${apiBaseUrl}/admin/cookie/update-status`,
    );
    if (response.data.code === 10000) {
      const result = response.data.data?.updated_count;
      const updatedCount = result?.updated_count ?? 0;
      ElMessage.success($t("views.cookiemanager.511q7l", [updatedCount]));
      refreshCookieStatus();
      loadCookies();
    } else {
      ElMessage.error($t("views.cookiemanager.4e1y78", [response.data.msg]));
    }
  } catch (error) {
    console.error($t("views.cookiemanager.844qcu"), error);
    ElMessage.error($t("views.cookiemanager.gp1dd8"));
  } finally {
    updatingStatus.value = false;
  }
};

// 清理过期Cookie
const cleanupExpiredCookies = async () => {
  try {
    await ElMessageBox.confirm(
      $t("views.cookiemanager.w111ux"),
      $t("views.cookiemanager.c7m27d"),
      {
        confirmButtonText: $t("views.cookiemanager.lfpp9p"),
        cancelButtonText: $t("views.cookiemanager.fl98bx"),
        type: "warning",
      },
    );

    cleaningUp.value = true;

    const response = await axios.post(
      `${apiBaseUrl}/admin/cookie/cleanup-expired`,
    );
    if (response.data.code === 10000) {
      ElMessage.success(
        $t("views.cookiemanager.jdrpgn", [response.data.data.deleted_count]),
      );
      refreshCookieStatus();
      loadCookies();
    } else {
      ElMessage.error($t("views.cookiemanager.lyosd4", [response.data.msg]));
    }
  } catch (error: any) {
    if (error !== "cancel") {
      console.error($t("views.cookiemanager.665727"), error);
      ElMessage.error($t("views.cookiemanager.4xpz05"));
    }
  } finally {
    cleaningUp.value = false;
  }
};

// 处理账号操作
const handleAccountCommand = (command: string, accountId: string) => {
  switch (command) {
    case "view":
      viewAccountDetail(accountId);
      break;
    case "temp_ban":
      openTempBanDialog(accountId);
      break;
    case "perm_ban":
      banAccountPermanently(accountId);
      break;
    case "update":
      openUpdateIdDialog(accountId);
      break;
    case "delete":
      deleteAccount(accountId);
      break;
  }
};

// 查看账号详情
const viewAccountDetail = async (accountId: string) => {
  accountDetailLoading.value = true;
  accountDetail.value = null;
  accountDetailDialogVisible.value = true;

  try {
    const response = await axios.get(
      `${apiBaseUrl}/admin/cookie/account-cookie/${accountId}`,
    );
    if (response.data.code === 10000) {
      // 确保cookies数据正确解析
      const data = response.data.data;
      if (data) {
        accountDetail.value = {
          ...data,
          cookies: data.cookies || {},
        };
      }
    } else {
      ElMessage.error($t("views.cookiemanager.f26paw", [response.data.msg]));
      accountDetailDialogVisible.value = false;
    }
  } catch (error) {
    console.error($t("views.cookiemanager.it47f2"), error);
    ElMessage.error($t("views.cookiemanager.5af555"));
    accountDetailDialogVisible.value = false;
  } finally {
    accountDetailLoading.value = false;
  }
};

// 复制Cookie字符串
const copyCookieString = async () => {
  if (!isSupported) {
    ElMessage.error($t("views.cookiemanager.my3iml"));
    return;
  }

  try {
    await copy(accountDetailCookieString.value);
    ElMessage.success($t("views.cookiemanager.lt24jw"));
  } catch (error) {
    console.error($t("views.cookiemanager.hj488l"), error);
    ElMessage.error($t("views.cookiemanager.5x00ks"));
  }
};

// 打开临时封禁对话框
const openTempBanDialog = (accountId: string) => {
  tempBanForm.account_id = accountId;
  tempBanForm.duration_minutes = 30;
  tempBanDialogVisible.value = true;
};

// 提交临时封禁
const submitTempBan = async () => {
  try {
    submitting.value = true;

    const durationSeconds = tempBanForm.duration_minutes * 60;
    const response = await axios.post(
      `${apiBaseUrl}/admin/cookie/ban/temporary/${tempBanForm.account_id}`,
      {
        duration_seconds: durationSeconds,
      },
    );

    if (response.data.code === 10000) {
      ElMessage.success(
        $t("views.cookiemanager.vd686k", [
          tempBanForm.account_id,
          tempBanForm.duration_minutes,
        ]),
      );
      tempBanDialogVisible.value = false;
      refreshCookieStatus();
      loadCookies();
      loadAvailableAccounts();
      loadBannedAccounts();
    } else {
      ElMessage.error($t("views.cookiemanager.7y6l48", [response.data.msg]));
    }
  } catch (error) {
    console.error($t("views.cookiemanager.1pi78u"), error);
    ElMessage.error($t("views.cookiemanager.4xpz05"));
  } finally {
    submitting.value = false;
  }
};

// 永久封禁账号
const banAccountPermanently = async (accountId: string) => {
  try {
    await ElMessageBox.confirm(
      $t("views.cookiemanager.7gtd0w", [accountId]),
      $t("views.cookiemanager.si393u"),
      {
        confirmButtonText: $t("views.cookiemanager.e6y884"),
        cancelButtonText: $t("views.cookiemanager.fl98bx"),
        type: "warning",
      },
    );

    accountsLoading.value = true;

    const response = await axios.post(
      `${apiBaseUrl}/admin/cookie/ban/permanent/${accountId}`,
    );
    if (response.data.code === 10000) {
      ElMessage.success($t("views.cookiemanager.60b8ym", [accountId]));
      refreshCookieStatus();
      loadCookies();
      loadAvailableAccounts();
      loadBannedAccounts();
    } else {
      ElMessage.error($t("views.cookiemanager.svdv0r", [response.data.msg]));
    }
  } catch (error: any) {
    if (error !== "cancel") {
      console.error($t("views.cookiemanager.g025y4"), error);
      ElMessage.error($t("views.cookiemanager.4xpz05"));
    }
  } finally {
    accountsLoading.value = false;
  }
};

// 解封账号
const unbanAccount = async (accountId: string) => {
  try {
    bannedLoading.value = true;

    const response = await axios.post(
      `${apiBaseUrl}/admin/cookie/unban/${accountId}`,
    );
    if (response.data.code === 10000) {
      ElMessage.success($t("views.cookiemanager.644stx", [accountId]));
      refreshCookieStatus();
      loadCookies();
      loadAvailableAccounts();
      loadBannedAccounts();
    } else {
      ElMessage.error($t("views.cookiemanager.4kt337", [response.data.msg]));
    }
  } catch (error) {
    console.error($t("views.cookiemanager.5q1rr6"), error);
    ElMessage.error($t("views.cookiemanager.4xpz05"));
  } finally {
    bannedLoading.value = false;
  }
};

// 强制解封账号
const forceUnbanAccount = async (accountId: string) => {
  try {
    await ElMessageBox.confirm(
      $t("views.cookiemanager.3173c4", [accountId]),
      $t("views.cookiemanager.188w8t"),
      {
        confirmButtonText: $t("views.cookiemanager.8etq8j"),
        cancelButtonText: $t("views.cookiemanager.fl98bx"),
        type: "warning",
      },
    );

    bannedLoading.value = true;

    const response = await axios.post(
      `${apiBaseUrl}/admin/cookie/force-unban/${accountId}`,
    );
    if (response.data.code === 10000) {
      ElMessage.success($t("views.cookiemanager.e6tc1n", [accountId]));
      refreshCookieStatus();
      loadCookies();
      loadAvailableAccounts();
      loadBannedAccounts();
    } else {
      ElMessage.error($t("views.cookiemanager.0frwfn", [response.data.msg]));
    }
  } catch (error: any) {
    if (error !== "cancel") {
      console.error($t("views.cookiemanager.ig1iw4"), error);
      ElMessage.error($t("views.cookiemanager.4xpz05"));
    }
  } finally {
    bannedLoading.value = false;
  }
};

// 打开更新账号ID对话框
const openUpdateIdDialog = (accountId: string) => {
  updateIdForm.old_account_id = accountId;
  updateIdForm.new_account_id = "";
  updateIdDialogVisible.value = true;
};

// 提交更新账号ID
const submitUpdateId = async () => {
  if (!updateIdFormRef.value) return;

  try {
    await (updateIdFormRef.value as any).validate();

    submitting.value = true;

    const response = await axios.put(
      `${apiBaseUrl}/admin/cookie/update-account/${updateIdForm.old_account_id}`,
      {
        new_account_id: updateIdForm.new_account_id,
      },
    );

    if (response.data.code === 10000) {
      ElMessage.success(
        $t("views.cookiemanager.68b827", [
          updateIdForm.old_account_id,
          updateIdForm.new_account_id,
        ]),
      );
      updateIdDialogVisible.value = false;
      refreshCookieStatus();
      loadCookies();
      loadAvailableAccounts();
      loadBannedAccounts();
    } else {
      ElMessage.error($t("views.cookiemanager.u7lmsj", [response.data.msg]));
    }
  } catch (error: any) {
    if (error.message) {
      ElMessage.error(error.message);
    } else {
      console.error($t("views.cookiemanager.mfk41z"), error);
      ElMessage.error($t("views.cookiemanager.gp1dd8"));
    }
  } finally {
    submitting.value = false;
  }
};

// 删除账号
const deleteAccount = async (accountId: string) => {
  try {
    await ElMessageBox.confirm(
      $t("views.cookiemanager.lkhbc0", [accountId]),
      $t("views.cookiemanager.2o2809"),
      {
        confirmButtonText: $t("views.cookiemanager.115uyi"),
        cancelButtonText: $t("views.cookiemanager.fl98bx"),
        type: "warning",
      },
    );

    accountsLoading.value = true;

    const response = await axios.delete(
      `${apiBaseUrl}/admin/cookie/delete/${accountId}`,
    );
    if (response.data.code === 10000) {
      ElMessage.success($t("views.cookiemanager.f8957g", [accountId]));
      refreshCookieStatus();
      loadCookies();
      loadAvailableAccounts();
      loadBannedAccounts();
    } else {
      ElMessage.error($t("views.cookiemanager.5rdm42", [response.data.msg]));
    }
  } catch (error: any) {
    if (error !== "cancel") {
      console.error($t("views.cookiemanager.mj2k0j"), error);
      ElMessage.error($t("views.cookiemanager.ah6421"));
    }
  } finally {
    accountsLoading.value = false;
  }
};

// 辅助函数
// 格式化Cookie状态文本
const getCookieStatusText = (cookie: any) => {
  if (cookie.is_permanently_banned)
    return $t("views.cookiemanager.e6y884");
  if (cookie.temp_ban_until) return $t("views.cookiemanager.5t0x50");
  if (cookie.is_available) return $t("views.cookiemanager.8qgc3r");
  if (cookie.expire_time && new Date(cookie.expire_time) < new Date())
    return $t("views.cookiemanager.81u723");
  return $t("views.cookiemanager.jxt47y");
};

// 获取Cookie状态样式
const getCookieStatusType = (cookie: any) => {
  if (cookie.is_permanently_banned) return "danger";
  if (cookie.temp_ban_until) return "warning";
  if (cookie.is_available) return "success";
  if (cookie.expire_time && new Date(cookie.expire_time) < new Date())
    return "info";
  return "danger";
};

// 截断文本
const truncateText = (text: string, length: number) => {
  if (!text) return "";
  return text.length > length ? text.substring(0, length) + "..." : text;
};

// 格式化日期时间
const formatDateTime = (dateTime: string) => {
  if (!dateTime) return "";
  return new Date(dateTime).toLocaleString();
};

// 格式化封禁剩余时间
const formatBanTimeRemaining = (seconds) => {
  if (!seconds || seconds <= 0) return $t("views.cookiemanager.0xi183");

  const days = Math.floor(seconds / (24 * 3600));
  const hours = Math.floor((seconds % (24 * 3600)) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const remainingSeconds = Math.floor(seconds % 60);

  let result = "";
  if (days > 0) result += `${days}天`;
  if (hours > 0) result += $t("views.cookiemanager.n4d7oo", [hours]);
  if (minutes > 0) result += $t("views.cookiemanager.3yb40y", [minutes]);
  if (remainingSeconds > 0 && !days && !hours)
    result += `${remainingSeconds}秒`;

  return result || $t("views.cookiemanager.7mdr60");
};

// 更新临时封禁账号的剩余时间
const updateBanTimeRemaining = () => {
  if (tempBannedAccounts.value.length > 0) {
    tempBannedAccounts.value.forEach((account) => {
      if (account.remaining_seconds > 0) {
        account.remaining_seconds -= 5; // 每5秒减少5秒
      }
    });
  }
};

// 处理Cookie操作命令
const handleCookieCommand = (command: string, cookie: any) => {
  switch (command) {
    case "edit":
      editCookie(cookie);
      break;
    case "delete":
      deleteCookie(cookie.account_id);
      break;
    case "unban":
      // 判断是临时封禁还是永久封禁
      if (cookie.is_permanently_banned) {
        forceUnbanAccount(cookie.account_id);
      } else {
        unbanCookie(cookie.account_id);
      }
      break;
    case "temp_ban":
      openTempBanDialog(cookie.account_id);
      break;
    case "perm_ban":
      banAccountPermanently(cookie.account_id);
      break;
  }
};

// 处理Excel文件
const processExcelFile = async (file: File) => {
  try {
    // 加载xlsx库
    // 注意: 需要安装xlsx库 npm install xlsx --save
    const XLSX = await import("xlsx");

    // 读取Excel文件
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = e.target?.result;
        if (!data) {
          ElMessage.error($t("views.cookiemanager.s6yicn"));
          return;
        }

        // 解析Excel数据
        const workbook = XLSX.read(data, { type: "array" });
        const firstSheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[firstSheetName];

        // 转换为JSON
        const jsonData = XLSX.utils.sheet_to_json(worksheet);

        if (jsonData.length === 0) {
          ElMessage.error($t("views.cookiemanager.nk3619"));
          return;
        }

        // 检查是否有name和value列
        const firstRow = jsonData[0];
        const hasNameCol =
          "name" in firstRow || "Name" in firstRow || "NAME" in firstRow;
        const hasValueCol =
          "value" in firstRow || "Value" in firstRow || "VALUE" in firstRow;

        if (!hasNameCol || !hasValueCol) {
          ElMessage.error($t("views.cookiemanager.vci1y8"));
          return;
        }

        // 提取name和value列数据
        const result = jsonData
          .map((row) => {
            const nameKey = Object.keys(row).find(
              (key) => key.toLowerCase() === "name",
            );
            const valueKey = Object.keys(row).find(
              (key) => key.toLowerCase() === "value",
            );

            if (nameKey && valueKey) {
              return {
                name: String(row[nameKey]),
                value: String(row[valueKey]),
              };
            }
            return null;
          })
          .filter((item) => item !== null);

        if (result.length > 0) {
          importPreviewData.value = result;
          ElMessage.success($t("views.cookiemanager.7tlafi", [result.length]));
        } else {
          ElMessage.error($t("views.cookiemanager.rmfc5u"));
        }
      } catch (error) {
        console.error($t("views.cookiemanager.190v3u"), error);
        ElMessage.error($t("views.cookiemanager.v136my"));
      }
    };

    reader.onerror = () => {
      ElMessage.error($t("views.cookiemanager.s6yicn"));
    };

    reader.readAsArrayBuffer(file);
  } catch (error) {
    console.error($t("views.cookiemanager.s767vg"), error);
    ElMessage.error($t("views.cookiemanager.q76dr5"));
  }
};

// 添加多选相关的变量
const multipleSelection = ref([]);
const batchActionLoading = ref(false);
const batchTempBanDialogVisible = ref(false);
const batchTempBanForm = reactive({
  duration_minutes: 30,
});

// 处理表格多选变化
const handleSelectionChange = (selection) => {
  multipleSelection.value = selection;
};

// 处理临时封禁全选
const handleCheckAllTempChange = (val: boolean) => {
  tempBannedSelection.value = val
    ? tempBannedAccounts.value.map((item) => item.account_id)
    : [];
  checkAllTemp.value = val;
};

// 处理永久封禁全选
const handleCheckAllPermChange = (val: boolean) => {
  permBannedSelection.value = val ? [...permBannedAccounts.value] : [];
  checkAllPerm.value = val;
};

// 批量解封选中的临时封禁Cookie
const unbanSelectedTemp = async () => {
  if (tempBannedSelection.value.length === 0) return;

  try {
    bannedLoading.value = true;
    let successCount = 0;
    for (const accountId of tempBannedSelection.value) {
      const response = await axios.post(
        `${apiBaseUrl}/admin/cookie/unban/${accountId}`,
      );
      if (response.data.code === 10000) successCount++;
    }
    ElMessage.success($t("views.cookiemanager.m823eg", [successCount]));
    loadBannedAccounts();
    refreshCookieStatus();
    loadCookies();
    tempBannedSelection.value = [];
    checkAllTemp.value = false;
  } catch (error) {
    ElMessage.error($t("views.cookiemanager.82h75y"));
  } finally {
    bannedLoading.value = false;
  }
};

// 解封所有临时封禁Cookie
const unbanAllTemp = async () => {
  if (tempBannedAccounts.value.length === 0) return;

  try {
    await ElMessageBox.confirm(
      $t("views.cookiemanager.752va2"),
      $t("views.cookiemanager.lwo521"),
      { type: "warning" },
    );
    bannedLoading.value = true;

    let successCount = 0;
    for (const item of tempBannedAccounts.value) {
      const response = await axios.post(
        `${apiBaseUrl}/admin/cookie/unban/${item.account_id}`,
      );
      if (response.data.code === 10000) successCount++;
    }

    ElMessage.success($t("views.cookiemanager.m823eg", [successCount]));
    loadBannedAccounts();
    refreshCookieStatus();
    loadCookies();
    tempBannedSelection.value = [];
    checkAllTemp.value = false;
  } catch (error) {
    if (error !== "cancel") ElMessage.error($t("views.cookiemanager.7vg03g"));
  } finally {
    bannedLoading.value = false;
  }
};

// 批量强制解封选中的永久封禁Cookie
const unbanSelectedPerm = async () => {
  if (permBannedSelection.value.length === 0) return;

  try {
    bannedLoading.value = true;
    let successCount = 0;
    for (const accountId of permBannedSelection.value) {
      const response = await axios.post(
        `${apiBaseUrl}/admin/cookie/force-unban/${accountId}`,
      );
      if (response.data.code === 10000) successCount++;
    }
    ElMessage.success($t("views.cookiemanager.m823eg", [successCount]));
    loadBannedAccounts();
    refreshCookieStatus();
    loadCookies();
    permBannedSelection.value = [];
    checkAllPerm.value = false;
  } catch (error) {
    ElMessage.error($t("views.cookiemanager.82h75y"));
  } finally {
    bannedLoading.value = false;
  }
};

// 解封所有永久封禁Cookie
const unbanAllPerm = async () => {
  if (permBannedAccounts.value.length === 0) return;

  try {
    await ElMessageBox.confirm(
      $t("views.cookiemanager.18oe22"),
      $t("views.cookiemanager.lwo521"),
      { type: "warning" },
    );
    bannedLoading.value = true;

    let successCount = 0;
    for (const accountId of permBannedAccounts.value) {
      const response = await axios.post(
        `${apiBaseUrl}/admin/cookie/force-unban/${accountId}`,
      );
      if (response.data.code === 10000) successCount++;
    }

    ElMessage.success($t("views.cookiemanager.m823eg", [successCount]));
    loadBannedAccounts();
    refreshCookieStatus();
    loadCookies();
    permBannedSelection.value = [];
    checkAllPerm.value = false;
  } catch (error) {
    if (error !== "cancel") ElMessage.error($t("views.cookiemanager.7vg03g"));
  } finally {
    bannedLoading.value = false;
  }
};

// 批量封禁所有Cookie
const batchBanAll = async () => {
  try {
    await ElMessageBox.confirm(
      $t("views.cookiemanager.4w2y58"),
      $t("views.cookiemanager.499fk9"),
      {
        confirmButtonText: $t("views.cookiemanager.86icn7"),
        cancelButtonText: $t("views.cookiemanager.fl98bx"),
        type: "warning",
      },
    );

    batchActionLoading.value = true;

    // 获取所有可用账号ID
    const response = await axios.get(
      `${apiBaseUrl}/admin/cookie/available-accounts`,
    );
    if (response.data.code === 10000) {
      const accountIds = response.data.data.account_ids || [];

      if (accountIds.length === 0) {
        ElMessage.warning($t("views.cookiemanager.vuc8y6"));
        batchActionLoading.value = false;
        return;
      }

      // 批量封禁
      let successCount = 0;
      for (const accountId of accountIds) {
        try {
          const banResponse = await axios.post(
            `${apiBaseUrl}/admin/cookie/ban/temporary/${accountId}`,
            {
              duration_seconds: 1800, // 默认30分钟
            },
          );

          if (banResponse.data.code === 10000) {
            successCount++;
          }
        } catch (error) {
          console.error($t("views.cookiemanager.55w1lt", [accountId]), error);
        }
      }

      ElMessage.success(
        $t("views.cookiemanager.743m2w", [successCount, accountIds.length]),
      );

      // 重新加载数据
      refreshCookieStatus();
      loadCookies();
      loadAvailableAccounts();
      loadBannedAccounts();
    } else {
      ElMessage.error($t("views.cookiemanager.v1688c", [response.data.msg]));
    }
  } catch (error) {
    if (error !== "cancel") {
      console.error($t("views.cookiemanager.d4ls3l"), error);
      ElMessage.error($t("views.cookiemanager.4xpz05"));
    }
  } finally {
    batchActionLoading.value = false;
  }
};

// 批量解封所有Cookie
const batchUnbanAll = async () => {
  try {
    await ElMessageBox.confirm(
      $t("views.cookiemanager.752va2"),
      $t("views.cookiemanager.4pvsv6"),
      {
        confirmButtonText: $t("views.cookiemanager.86icn7"),
        cancelButtonText: $t("views.cookiemanager.fl98bx"),
        type: "warning",
      },
    );

    batchActionLoading.value = true;

    // 获取所有临时封禁的账号
    const response = await axios.get(
      `${apiBaseUrl}/admin/cookie/banned-accounts`,
    );
    if (response.data.code === 10000) {
      const tempBannedAccounts = response.data.data.temp_banned || [];

      if (tempBannedAccounts.length === 0) {
        ElMessage.warning($t("views.cookiemanager.uut1sx"));
        batchActionLoading.value = false;
        return;
      }

      // 批量解封
      let successCount = 0;
      for (const account of tempBannedAccounts) {
        try {
          const unbanResponse = await axios.post(
            `${apiBaseUrl}/admin/cookie/unban/${account.account_id}`,
          );

          if (unbanResponse.data.code === 10000) {
            successCount++;
          }
        } catch (error) {
          console.error(
            $t("views.cookiemanager.sdo4vu", [account.account_id]),
            error,
          );
        }
      }

      ElMessage.success(
        $t("views.cookiemanager.1o9d8s", [
          successCount,
          tempBannedAccounts.length,
        ]),
      );

      // 重新加载数据
      refreshCookieStatus();
      loadCookies();
      loadAvailableAccounts();
      loadBannedAccounts();
    } else {
      ElMessage.error($t("views.cookiemanager.21x5u6", [response.data.msg]));
    }
  } catch (error) {
    if (error !== "cancel") {
      console.error($t("views.cookiemanager.d4ls3l"), error);
      ElMessage.error($t("views.cookiemanager.4xpz05"));
    }
  } finally {
    batchActionLoading.value = false;
  }
};

// 批量临时封禁选中的Cookie
const batchTempBan = () => {
  if (multipleSelection.value.length === 0) {
    ElMessage.warning($t("views.cookiemanager.i184gl"));
    return;
  }

  batchTempBanDialogVisible.value = true;
};

// 提交批量临时封禁
const submitBatchTempBan = async () => {
  try {
    batchActionLoading.value = true;

    const durationSeconds = batchTempBanForm.duration_minutes * 60;
    let successCount = 0;

    for (const item of multipleSelection.value) {
      try {
        const response = await axios.post(
          `${apiBaseUrl}/admin/cookie/ban/temporary/${item.account_id}`,
          {
            duration_seconds: durationSeconds,
          },
        );

        if (response.data.code === 10000) {
          successCount++;
        }
      } catch (error) {
        console.error(
          $t("views.cookiemanager.pw1x8c", [item.account_id]),
          error,
        );
      }
    }

    ElMessage.success(
      $t("views.cookiemanager.43wsob", [
        successCount,
        multipleSelection.value.length,
        batchTempBanForm.duration_minutes,
      ]),
    );
    batchTempBanDialogVisible.value = false;

    // 重新加载数据
    refreshCookieStatus();
    loadCookies();
    loadAvailableAccounts();
    loadBannedAccounts();

    // 清空选择
    multipleSelection.value = [];
  } catch (error) {
    console.error($t("views.cookiemanager.m75rm2"), error);
    ElMessage.error($t("views.cookiemanager.611tx8"));
  } finally {
    batchActionLoading.value = false;
  }
};

// 批量永久封禁选中的Cookie
const batchPermBan = async () => {
  if (multipleSelection.value.length === 0) {
    ElMessage.warning($t("views.cookiemanager.i184gl"));
    return;
  }

  try {
    await ElMessageBox.confirm(
      $t("views.cookiemanager.42j2v1", [multipleSelection.value.length]),
      $t("views.cookiemanager.w7vu17"),
      {
        confirmButtonText: $t("views.cookiemanager.86icn7"),
        cancelButtonText: $t("views.cookiemanager.fl98bx"),
        type: "warning",
      },
    );

    batchActionLoading.value = true;

    let successCount = 0;
    for (const item of multipleSelection.value) {
      try {
        const response = await axios.post(
          `${apiBaseUrl}/admin/cookie/ban/permanent/${item.account_id}`,
        );

        if (response.data.code === 10000) {
          successCount++;
        }
      } catch (error) {
        console.error(
          $t("views.cookiemanager.1so2vh", [item.account_id]),
          error,
        );
      }
    }

    ElMessage.success(
      $t("views.cookiemanager.807tln", [
        successCount,
        multipleSelection.value.length,
      ]),
    );

    // 重新加载数据
    refreshCookieStatus();
    loadCookies();
    loadAvailableAccounts();
    loadBannedAccounts();

    // 清空选择
    multipleSelection.value = [];
  } catch (error) {
    if (error !== "cancel") {
      console.error($t("views.cookiemanager.qx5d25"), error);
      ElMessage.error($t("views.cookiemanager.qt6o66"));
    }
  } finally {
    batchActionLoading.value = false;
  }
};

// 批量解封选中的Cookie
const batchUnban = async () => {
  if (multipleSelection.value.length === 0) {
    ElMessage.warning($t("views.cookiemanager.7x653r"));
    return;
  }

  try {
    await ElMessageBox.confirm(
      $t("views.cookiemanager.hv8683", [multipleSelection.value.length]),
      $t("views.cookiemanager.4pvsv6"),
      {
        confirmButtonText: $t("views.cookiemanager.86icn7"),
        cancelButtonText: $t("views.cookiemanager.fl98bx"),
        type: "warning",
      },
    );

    batchActionLoading.value = true;

    let successCount = 0;
    for (const item of multipleSelection.value) {
      try {
        // 对于临时封禁的使用普通解封
        if (item.temp_ban_until) {
          const response = await axios.post(
            `${apiBaseUrl}/admin/cookie/unban/${item.account_id}`,
          );

          if (response.data.code === 10000) {
            successCount++;
          }
        }
        // 对于永久封禁的使用强制解封
        else if (item.is_permanently_banned) {
          const response = await axios.post(
            `${apiBaseUrl}/admin/cookie/force-unban/${item.account_id}`,
          );

          if (response.data.code === 10000) {
            successCount++;
          }
        }
        // 对于正常状态的Cookie不需要操作
        else {
          successCount++;
        }
      } catch (error) {
        console.error(
          $t("views.cookiemanager.sdo4vu", [item.account_id]),
          error,
        );
      }
    }

    ElMessage.success(
      $t("views.cookiemanager.1o9d8s", [
        successCount,
        multipleSelection.value.length,
      ]),
    );

    // 重新加载数据
    refreshCookieStatus();
    loadCookies();
    loadAvailableAccounts();
    loadBannedAccounts();

    // 清空选择
    multipleSelection.value = [];
  } catch (error) {
    if (error !== "cancel") {
      console.error($t("views.cookiemanager.d4ls3l"), error);
      ElMessage.error($t("views.cookiemanager.4xpz05"));
    }
  } finally {
    batchActionLoading.value = false;
  }
};
</script>

<template>
  <div class="cookie-manager-container">
    <div class="page-header">
      <h1>{{ $t("views.cookiemanager.h318s4") }}</h1>
      <div class="api-status">
        <el-tag :type="apiConnected ? 'success' : 'danger'" effect="dark">
          {{
            apiConnected
              ? $t("views.cookiemanager.la9d7i")
              : $t("views.cookiemanager.frt8cm")
          }}
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
              <span>{{ $t("views.cookiemanager.584l78") }}</span>
              <div>
                <el-button
                  type="primary"
                  size="small"
                  @click="refreshCookieStatus"
                  :loading="statusLoading"
                >
                  <el-icon><Refresh /></el-icon
                  >{{ $t("views.cookiemanager.p3kgye") }}</el-button
                >
                <el-button
                  type="success"
                  size="small"
                  @click="openAddCookieDialog"
                >
                  <el-icon><Plus /></el-icon
                  >{{ $t("views.cookiemanager.t4da2e") }}</el-button
                >
              </div>
            </div>
          </template>

          <div v-loading="statusLoading" class="status-overview">
            <div class="status-item">
              <div class="status-value">{{ cookieStats.total }}</div>
              <div class="status-label">
                {{ $t("views.cookiemanager.elw1fx") }}
              </div>
            </div>
            <div class="status-item success">
              <div class="status-value">{{ cookieStats.available }}</div>
              <div class="status-label">
                {{ $t("views.cookiemanager.8qgc3r") }}
              </div>
            </div>
            <div class="status-item warning">
              <div class="status-value">{{ cookieStats.tempBanned }}</div>
              <div class="status-label">
                {{ $t("views.cookiemanager.5t0x50") }}
              </div>
            </div>
            <div class="status-item danger">
              <div class="status-value">{{ cookieStats.permBanned }}</div>
              <div class="status-label">
                {{ $t("views.cookiemanager.e6y884") }}
              </div>
            </div>
          </div>

          <el-divider />

          <div class="action-buttons">
            <el-button
              type="primary"
              @click="testAllCookiesAvailability"
              :loading="testingAll"
            >
              <el-icon><Check /></el-icon
              >{{ $t("views.cookiemanager.o0ffn2") }}</el-button
            >
            <el-button
              type="warning"
              @click="updateCookieStatus"
              :loading="updatingStatus"
            >
              <el-icon><RefreshRight /></el-icon
              >{{ $t("views.cookiemanager.4lih7b") }}</el-button
            >
            <el-button
              type="danger"
              @click="cleanupExpiredCookies"
              :loading="cleaningUp"
            >
              <el-icon><Delete /></el-icon
              >{{ $t("views.cookiemanager.x768ru") }}</el-button
            >
          </div>

          <!-- 账号列表 -->
          <div class="account-list-section">
            <div class="section-header">
              <h3>{{ $t("views.cookiemanager.e19l34") }}</h3>
              <el-button size="small" text @click="loadAvailableAccounts">{{
                $t("views.cookiemanager.p3kgye")
              }}</el-button>
            </div>
            <div v-loading="accountsLoading" class="account-list">
              <template v-if="availableAccounts.length > 0">
                <div
                  v-for="account in availableAccounts"
                  :key="account"
                  class="account-item"
                >
                  <div class="account-info">
                    <el-tag size="small" effect="plain">{{ account }}</el-tag>
                  </div>
                  <div class="account-actions">
                    <el-button
                      size="small"
                      type="primary"
                      @click="testAccountAvailability(account)"
                      plain
                      >{{ $t("views.cookiemanager.vne764") }}</el-button
                    >
                    <el-dropdown
                      trigger="click"
                      @command="handleAccountCommand($event, account)"
                    >
                      <el-button size="small" plain
                        >{{ $t("views.cookiemanager.s2tp53")
                        }}<el-icon class="el-icon--right"
                          ><ArrowDown
                        /></el-icon>
                      </el-button>
                      <template #dropdown>
                        <el-dropdown-menu>
                          <el-dropdown-item command="view">{{
                            $t("views.cookiemanager.x4jo6h")
                          }}</el-dropdown-item>
                          <el-dropdown-item command="temp_ban" divided>{{
                            $t("views.cookiemanager.5t0x50")
                          }}</el-dropdown-item>
                          <el-dropdown-item command="perm_ban">{{
                            $t("views.cookiemanager.e6y884")
                          }}</el-dropdown-item>
                          <el-dropdown-item command="update" divided>{{
                            $t("views.cookiemanager.tvm48e")
                          }}</el-dropdown-item>
                          <el-dropdown-item command="delete" divided>{{
                            $t("views.cookiemanager.115uyi")
                          }}</el-dropdown-item>
                        </el-dropdown-menu>
                      </template>
                    </el-dropdown>
                  </div>
                </div>
              </template>
              <el-empty
                v-else
                :description="$t('views.cookiemanager.xt8ck8')"
              />
            </div>
          </div>
        </el-card>

        <!-- 封禁的账号卡片 -->
        <el-card class="banned-accounts-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>{{ $t("views.cookiemanager.k0r455") }}</span>
              <el-button
                size="small"
                type="primary"
                @click="loadBannedAccounts"
                plain
              >
                <el-icon><Refresh /></el-icon
                >{{ $t("views.cookiemanager.p3kgye") }}</el-button
              >
            </div>
          </template>

          <div v-loading="bannedLoading" class="banned-accounts">
            <el-tabs v-model="bannedTabActive">
              <el-tab-pane
                :label="$t('views.cookiemanager.5t0x50')"
                name="temp"
              >
                <div
                  class="banned-toolbar"
                  v-if="tempBannedAccounts.length > 0"
                >
                  <el-checkbox
                    v-model="checkAllTemp"
                    :indeterminate="isTempIndeterminate"
                    @change="handleCheckAllTempChange"
                    >{{ $t("views.cookiemanager.8st7lh") }}</el-checkbox
                  >
                  <el-button
                    type="primary"
                    link
                    size="small"
                    :disabled="tempBannedSelection.length === 0"
                    @click="unbanSelectedTemp"
                    >{{ $t("views.cookiemanager.ae5zra") }}</el-button
                  >
                  <el-button
                    type="danger"
                    link
                    size="small"
                    @click="unbanAllTemp"
                    >{{ $t("views.cookiemanager.05o6ep") }}</el-button
                  >
                </div>
                <template v-if="tempBannedAccounts.length > 0">
                  <el-checkbox-group v-model="tempBannedSelection">
                    <div
                      v-for="account in tempBannedAccounts"
                      :key="account.account_id"
                      class="banned-account-item"
                    >
                      <el-checkbox
                        :value="account.account_id"
                        class="banned-checkbox"
                      />
                      <div class="banned-account-info">
                        <div class="account-header">
                          <span class="account-id">{{
                            account.account_id
                          }}</span>
                          <el-tag
                            size="small"
                            type="warning"
                            effect="light"
                            class="status-tag"
                          >
                            {{ $t("views.cookiemanager.c6burr")
                            }}{{
                              formatBanTimeRemaining(account.remaining_seconds)
                            }}
                          </el-tag>
                        </div>
                        <div
                          class="ban-time-meta"
                          v-if="account.temp_ban_until"
                        >
                          <el-icon><Clock /></el-icon>
                          {{ account.temp_ban_until }}
                        </div>
                      </div>
                      <div class="banned-account-actions">
                        <el-button
                          size="small"
                          type="primary"
                          @click.stop="unbanAccount(account.account_id)"
                          plain
                          >{{ $t("views.cookiemanager.mf8dc8") }}</el-button
                        >
                      </div>
                    </div>
                  </el-checkbox-group>
                </template>
                <el-empty
                  v-else
                  :description="$t('views.cookiemanager.oi7woo')"
                />
              </el-tab-pane>
              <el-tab-pane
                :label="$t('views.cookiemanager.e6y884')"
                name="perm"
              >
                <div
                  class="banned-toolbar"
                  v-if="permBannedAccounts.length > 0"
                >
                  <el-checkbox
                    v-model="checkAllPerm"
                    :indeterminate="isPermIndeterminate"
                    @change="handleCheckAllPermChange"
                    >{{ $t("views.cookiemanager.8st7lh") }}</el-checkbox
                  >
                  <el-button
                    type="primary"
                    link
                    size="small"
                    :disabled="permBannedSelection.length === 0"
                    @click="unbanSelectedPerm"
                    >{{ $t("views.cookiemanager.dp7l10") }}</el-button
                  >
                  <el-button
                    type="danger"
                    link
                    size="small"
                    @click="unbanAllPerm"
                    >{{ $t("views.cookiemanager.k609zq") }}</el-button
                  >
                </div>
                <template v-if="permBannedAccounts.length > 0">
                  <el-checkbox-group v-model="permBannedSelection">
                    <div
                      v-for="account in permBannedAccounts"
                      :key="account"
                      class="banned-account-item"
                    >
                      <el-checkbox :value="account" class="banned-checkbox" />
                      <div class="banned-account-info">
                        <div class="account-header">
                          <span class="account-id">{{ account }}</span>
                          <el-tag
                            size="small"
                            type="danger"
                            effect="light"
                            class="status-tag"
                          >
                            {{ $t("views.cookiemanager.e6y884") }}
                          </el-tag>
                        </div>
                      </div>
                      <div class="banned-account-actions">
                        <el-button
                          size="small"
                          type="danger"
                          @click.stop="forceUnbanAccount(account)"
                          plain
                          >{{ $t("views.cookiemanager.8etq8j") }}</el-button
                        >
                      </div>
                    </div>
                  </el-checkbox-group>
                </template>
                <el-empty
                  v-else
                  :description="$t('views.cookiemanager.fvo87d')"
                />
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
              <span>{{ $t("views.cookiemanager.7368q6") }}</span>
              <div class="header-actions">
                <el-button
                  type="primary"
                  size="small"
                  @click="syncToRedis"
                  :loading="syncing"
                >
                  <el-icon><Connection /></el-icon
                  >{{ $t("views.cookiemanager.278g1g") }}</el-button
                >
                <el-button
                  type="success"
                  size="small"
                  @click="updateAbSr"
                  :loading="updatingAbSr"
                >
                  <el-icon><RefreshRight /></el-icon
                  >{{ $t("views.cookiemanager.y9p7s8") }}</el-button
                >
                <el-button
                  size="small"
                  @click="loadCookies"
                  :loading="listLoading"
                >
                  <el-icon><Refresh /></el-icon
                  >{{ $t("views.cookiemanager.p3kgye") }}</el-button
                >
              </div>
            </div>
          </template>

          <div class="filter-section">
            <el-input
              v-model="searchAccount"
              :placeholder="$t('views.cookiemanager.554j21')"
              clearable
              prefix-icon="Search"
              class="filter-item"
            />
            <el-select
              v-model="statusFilter"
              :placeholder="$t('views.cookiemanager.bmk76u')"
              clearable
              class="filter-item"
            >
              <el-option
                :label="$t('views.cookiemanager.8qgc3r')"
                value="available"
              />
              <el-option
                :label="$t('views.cookiemanager.5t0x50')"
                value="temp_banned"
              />
              <el-option
                :label="$t('views.cookiemanager.e6y884')"
                value="perm_banned"
              />
              <el-option
                :label="$t('views.cookiemanager.81u723')"
                value="expired"
              />
            </el-select>
            <el-button type="primary" @click="handleFilter">{{
              $t("views.cookiemanager.7ti321")
            }}</el-button>
            <el-button plain @click="resetFilter">{{
              $t("views.cookiemanager.7cu76x")
            }}</el-button>
            <el-button type="success" @click="openAddCookieDialog">
              <el-icon><Plus /></el-icon
              >{{ $t("views.cookiemanager.t4da2e") }}</el-button
            >
          </div>

          <div class="batch-actions" v-if="cookieList.length > 0">
            <el-button-group>
              <el-button
                type="danger"
                @click="batchBanAll"
                :loading="batchActionLoading"
                >{{ $t("views.cookiemanager.4i2gzk") }}</el-button
              >
              <el-button
                type="success"
                @click="batchUnbanAll"
                :loading="batchActionLoading"
                >{{ $t("views.cookiemanager.gvg393") }}</el-button
              >
            </el-button-group>
            <el-button-group v-if="multipleSelection.length > 0" class="ml-10">
              <el-button
                type="warning"
                @click="batchTempBan"
                :loading="batchActionLoading"
                >{{ $t("views.cookiemanager.s8yksu") }}</el-button
              >
              <el-button
                type="danger"
                @click="batchPermBan"
                :loading="batchActionLoading"
                >{{ $t("views.cookiemanager.yt1jqk") }}</el-button
              >
              <el-button
                type="success"
                @click="batchUnban"
                :loading="batchActionLoading"
                >{{ $t("views.cookiemanager.ae5zra") }}</el-button
              >
            </el-button-group>
            <span v-if="multipleSelection.length > 0" class="selection-info"
              >{{ $t("views.cookiemanager.sh12bf")
              }}{{ multipleSelection.length
              }}{{ $t("views.cookiemanager.58g533") }}</span
            >
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
            <el-table-column
              prop="account_id"
              :label="$t('views.cookiemanager.pep1je')"
              width="120"
              show-overflow-tooltip
              sortable
            />
            <el-table-column
              :label="$t('views.cookiemanager.rps185')"
              width="90"
            >
              <template #default="scope">
                <el-tag size="small" effect="plain" type="info">
                  {{ scope.row.cookie_count || 0 }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              :label="$t('views.cookiemanager.q28nq7')"
              show-overflow-tooltip
            >
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
            <el-table-column
              :label="$t('views.cookiemanager.w5f1e1')"
              width="100"
              sortable
            >
              <template #default="scope">
                <el-tag :type="getCookieStatusType(scope.row)" effect="light">
                  {{ getCookieStatusText(scope.row) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column
              :label="$t('views.cookiemanager.8j8u6u')"
              width="150"
              sortable
            >
              <template #default="scope">
                <span v-if="scope.row.expire_time">
                  {{ formatDateTime(scope.row.expire_time) }}
                </span>
                <span v-else>{{ $t("views.cookiemanager.c805dh") }}</span>
              </template>
            </el-table-column>
            <el-table-column
              :label="$t('views.cookiemanager.s2tp53')"
              width="100"
            >
              <template #default="scope">
                <el-dropdown
                  trigger="click"
                  @command="
                    (command) => handleCookieCommand(command, scope.row)
                  "
                >
                  <el-button type="primary" size="small" plain
                    >{{ $t("views.cookiemanager.s2tp53")
                    }}<el-icon class="el-icon--right"><ArrowDown /></el-icon>
                  </el-button>
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item command="edit">{{
                        $t("views.cookiemanager.f46go7")
                      }}</el-dropdown-item>
                      <el-dropdown-item
                        command="temp_ban"
                        v-if="
                          !scope.row.temp_ban_until &&
                          scope.row.is_permanently_banned !== 1
                        "
                        >{{
                          $t("views.cookiemanager.5t0x50")
                        }}</el-dropdown-item
                      >
                      <el-dropdown-item
                        command="perm_ban"
                        v-if="scope.row.is_permanently_banned !== 1"
                        >{{
                          $t("views.cookiemanager.e6y884")
                        }}</el-dropdown-item
                      >
                      <el-dropdown-item
                        command="unban"
                        v-if="
                          scope.row.temp_ban_until ||
                          scope.row.is_permanently_banned
                        "
                        >{{
                          $t("views.cookiemanager.mf8dc8")
                        }}</el-dropdown-item
                      >
                      <el-dropdown-item command="delete" divided>{{
                        $t("views.cookiemanager.115uyi")
                      }}</el-dropdown-item>
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
          <span>{{ $t("views.cookiemanager.b1v50i") }}</span>
        </div>
      </template>

      <CookieUsageChart :api-base-url="apiBaseUrl" />
    </el-card>
    <!-- 添加/编辑Cookie对话框 -->
    <el-dialog
      v-model="cookieDialogVisible"
      :title="
        cookieForm.account_id
          ? $t('views.cookiemanager.2623i5')
          : $t('views.cookiemanager.t4da2e')
      "
      width="700px"
      destroy-on-close
    >
      <el-form
        :model="cookieForm"
        label-width="120px"
        :rules="cookieRules"
        ref="cookieFormRef"
      >
        <el-form-item
          :label="$t('views.cookiemanager.pep1je')"
          prop="account_id"
        >
          <el-input
            v-model="cookieForm.account_id"
            :placeholder="$t('views.cookiemanager.5s8vk4')"
          />
        </el-form-item>

        <el-tabs v-model="cookieInputMode" type="card">
          <!-- 字符串输入模式 -->
          <el-tab-pane :label="$t('views.cookiemanager.0jv8m7')" name="string">
            <el-form-item :label="$t('views.cookiemanager.uk514y')">
              <el-input
                v-model="cookieForm.cookie_string"
                type="textarea"
                rows="8"
                :placeholder="$t('views.cookiemanager.56wc28')"
              />
            </el-form-item>
          </el-tab-pane>

          <!-- JSON输入模式 -->
          <el-tab-pane :label="$t('views.cookiemanager.6wnhzb')" name="json">
            <el-form-item label="Cookie JSON" prop="cookie_json">
              <el-input
                v-model="cookieForm.cookie_json"
                type="textarea"
                rows="8"
                :placeholder="$t('views.cookiemanager.oqt324')"
                :spellcheck="false"
              />
              <div class="form-actions">
                <el-button size="small" type="primary" @click="formatJson">{{
                  $t("views.cookiemanager.144hw4")
                }}</el-button>
                <el-button
                  size="small"
                  type="info"
                  @click="convertStringToJson"
                  >{{ $t("views.cookiemanager.bs6wbh") }}</el-button
                >
              </div>
            </el-form-item>
          </el-tab-pane>

          <!-- 表格输入模式 -->
          <el-tab-pane :label="$t('views.cookiemanager.c9u3wg')" name="table">
            <div class="table-toolbar">
              <el-button type="primary" size="small" @click="addCookieField">
                <el-icon><Plus /></el-icon
                >{{ $t("views.cookiemanager.n1j1b9") }}</el-button
              >
              <el-button type="danger" size="small" @click="clearAllFields">
                <el-icon><Delete /></el-icon
                >{{ $t("views.cookiemanager.kdgy84") }}</el-button
              >
            </div>

            <el-table
              :data="cookieTableData"
              border
              style="width: 100%"
              max-height="300px"
            >
              <el-table-column
                :label="$t('views.cookiemanager.pep1je')"
                width="180"
              >
                <template #default="scope">
                  <el-input
                    v-model="scope.row.name"
                    :placeholder="$t('views.cookiemanager.xuc351')"
                    size="small"
                  />
                </template>
              </el-table-column>
              <el-table-column :label="$t('views.cookiemanager.q28nq7')">
                <template #default="scope">
                  <el-input
                    v-model="scope.row.value"
                    :placeholder="$t('views.cookiemanager.3b8z62')"
                    size="small"
                  />
                </template>
              </el-table-column>
              <el-table-column
                :label="$t('views.cookiemanager.s2tp53')"
                width="120"
              >
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
              <el-button
                size="small"
                type="primary"
                @click="generateJsonFromTable"
                >{{ $t("views.cookiemanager.w4j2q1") }}</el-button
              >
              <el-button
                size="small"
                type="info"
                @click="generateTableFromJson"
                >{{ $t("views.cookiemanager.6p2h3h") }}</el-button
              >
            </div>
          </el-tab-pane>

          <!-- 导入模式 -->
          <el-tab-pane :label="$t('views.cookiemanager.1883e3')" name="import">
            <el-form-item :label="$t('views.cookiemanager.td2u38')">
              <el-select
                v-model="importType"
                :placeholder="$t('views.cookiemanager.628u23')"
              >
                <el-option
                  :label="$t('views.cookiemanager.n95bbl')"
                  value="txt"
                />
                <el-option
                  :label="$t('views.cookiemanager.o88dqp')"
                  value="json"
                />
                <el-option
                  :label="$t('views.cookiemanager.301485')"
                  value="csv"
                />
                <el-option
                  :label="$t('views.cookiemanager.0o7p74')"
                  value="excel"
                />
              </el-select>
            </el-form-item>

            <el-form-item :label="$t('views.cookiemanager.41x3g4')">
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
                  <el-button type="primary">{{
                    $t("views.cookiemanager.41x3g4")
                  }}</el-button>
                </template>
                <template #tip>
                  <div class="el-upload__tip">
                    {{ $t("views.cookiemanager.g05hd1") }}
                  </div>
                </template>
              </el-upload>
              <el-button
                type="success"
                @click="processCookieFile"
                :disabled="!selectedFile"
                >{{ $t("views.cookiemanager.42wv66") }}</el-button
              >
            </el-form-item>

            <el-form-item
              :label="$t('views.cookiemanager.23tt1n')"
              v-if="importPreviewData.length > 0"
            >
              <el-table
                :data="importPreviewData"
                border
                style="width: 100%"
                max-height="200px"
              >
                <el-table-column
                  :label="$t('views.cookiemanager.pep1je')"
                  prop="name"
                  width="180"
                />
                <el-table-column
                  :label="$t('views.cookiemanager.q28nq7')"
                  prop="value"
                  show-overflow-tooltip
                />
              </el-table>
              <div class="form-actions">
                <el-button size="small" type="primary" @click="confirmImport">{{
                  $t("views.cookiemanager.f13q7e")
                }}</el-button>
                <el-button size="small" type="danger" @click="cancelImport">{{
                  $t("views.cookiemanager.5c03y1")
                }}</el-button>
              </div>
            </el-form-item>
          </el-tab-pane>
        </el-tabs>

        <el-divider />

        <el-form-item :label="$t('views.cookiemanager.6wj7ss')">
          <el-radio-group v-model="cookieForm.expire_option">
            <el-radio :label="'none'">{{
              $t("views.cookiemanager.c805dh")
            }}</el-radio>
            <el-radio :label="'days'">{{
              $t("views.cookiemanager.7hkyhk")
            }}</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item
          :label="$t('views.cookiemanager.36h81u')"
          v-if="cookieForm.expire_option === 'days'"
        >
          <el-input-number
            v-model="cookieForm.expire_days"
            :min="1"
            :max="365"
          />
          <span class="form-tip">{{ $t("views.cookiemanager.l1d4m6") }}</span>
        </el-form-item>

        <el-form-item
          v-if="cookieForm.id"
          :label="$t('views.cookiemanager.iv86lc')"
          prop="is_available"
        >
          <el-switch
            v-model="cookieForm.is_available"
            :disabled="
              cookieForm.is_permanently_banned || cookieForm.temp_ban_until
            "
          />
          <span class="form-tip">{{
            cookieForm.is_available
              ? $t("views.cookiemanager.8qgc3r")
              : $t("views.cookiemanager.jxt47y")
          }}</span>
        </el-form-item>

        <el-form-item
          v-if="cookieForm.id"
          :label="$t('views.cookiemanager.e6y884')"
          prop="is_permanently_banned"
        >
          <el-switch v-model="cookieForm.is_permanently_banned" />
          <span class="form-tip">{{
            cookieForm.is_permanently_banned
              ? $t("views.cookiemanager.e239nh")
              : $t("views.cookiemanager.2hu57i")
          }}</span>
        </el-form-item>

        <el-form-item
          v-if="cookieForm.id && !cookieForm.is_permanently_banned"
          :label="$t('views.cookiemanager.1psc3j')"
          prop="temp_ban_until"
        >
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
          <el-button @click="cookieDialogVisible = false">{{
            $t("views.cookiemanager.fl98bx")
          }}</el-button>
          <el-button
            type="primary"
            @click="submitCookieForm"
            :loading="submitting"
            >{{ $t("views.cookiemanager.og231w") }}</el-button
          >
        </div>
      </template>
    </el-dialog>

    <!-- 临时封禁对话框 -->
    <el-dialog
      v-model="tempBanDialogVisible"
      :title="$t('views.cookiemanager.mj7whc')"
      width="400px"
      destroy-on-close
    >
      <el-form :model="tempBanForm" label-width="100px">
        <el-form-item :label="$t('views.cookiemanager.pep1je')">
          <el-tag>{{ tempBanForm.account_id }}</el-tag>
        </el-form-item>
        <el-form-item :label="$t('views.cookiemanager.8sthw8')">
          <el-input-number
            v-model="tempBanForm.duration_minutes"
            :min="1"
            :max="1440"
          />
          <span class="form-tip">{{ $t("views.cookiemanager.8585f1") }}</span>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="tempBanDialogVisible = false">{{
            $t("views.cookiemanager.fl98bx")
          }}</el-button>
          <el-button
            type="primary"
            @click="submitTempBan"
            :loading="submitting"
            >{{ $t("views.cookiemanager.og231w") }}</el-button
          >
        </div>
      </template>
    </el-dialog>

    <!-- 更新账号ID对话框 -->
    <el-dialog
      v-model="updateIdDialogVisible"
      :title="$t('views.cookiemanager.tvm48e')"
      width="400px"
      destroy-on-close
    >
      <el-form
        :model="updateIdForm"
        label-width="100px"
        :rules="updateIdRules"
        ref="updateIdFormRef"
      >
        <el-form-item :label="$t('views.cookiemanager.c2tmph')">
          <el-tag>{{ updateIdForm.old_account_id }}</el-tag>
        </el-form-item>
        <el-form-item
          :label="$t('views.cookiemanager.79rvpp')"
          prop="new_account_id"
        >
          <el-input
            v-model="updateIdForm.new_account_id"
            :placeholder="$t('views.cookiemanager.n82uxe')"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="updateIdDialogVisible = false">{{
            $t("views.cookiemanager.fl98bx")
          }}</el-button>
          <el-button
            type="primary"
            @click="submitUpdateId"
            :loading="submitting"
            >{{ $t("views.cookiemanager.og231w") }}</el-button
          >
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
          <el-descriptions-item
            :label="$t('views.cookiemanager.pep1je')"
            :span="2"
            >{{ accountDetail.account_id }}</el-descriptions-item
          >
          <el-descriptions-item :label="$t('views.cookiemanager.rps185')">{{
            accountDetail.cookie_count
          }}</el-descriptions-item>
          <el-descriptions-item :label="$t('views.cookiemanager.w5f1e1')">
            <el-tag :type="accountDetail.is_available ? 'success' : 'danger'">
              {{
                accountDetail.is_available
                  ? $t("views.cookiemanager.8qgc3r")
                  : $t("views.cookiemanager.jxt47y")
              }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>

        <el-divider content-position="left">{{
          $t("views.cookiemanager.7v7w52")
        }}</el-divider>

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
              <el-icon><CopyDocument /></el-icon
              >{{ $t("views.cookiemanager.12b01g") }}</el-button
            >
          </div>

          <el-table :data="accountDetailCookies" style="width: 100%" border>
            <el-table-column
              prop="name"
              :label="$t('views.cookiemanager.4u7j97')"
              width="180"
            />
            <el-table-column
              prop="value"
              :label="$t('views.cookiemanager.q28nq7')"
              show-overflow-tooltip
            />
          </el-table>
        </div>
        <el-empty v-else :description="$t('views.cookiemanager.33om7b')" />
      </div>
    </el-dialog>

    <!-- 测试结果对话框 -->
    <el-dialog
      v-model="testResultDialogVisible"
      :title="$t('views.cookiemanager.m2kpbj')"
      width="500px"
      destroy-on-close
    >
      <div v-loading="testingAccount">
        <template v-if="testResult">
          <el-result
            :icon="testResult.is_valid ? 'success' : 'error'"
            :title="
              testResult.is_valid
                ? $t('views.cookiemanager.08l5c0')
                : $t('views.cookiemanager.6yn21w')
            "
            :sub-title="testResult.message"
          >
            <template #extra>
              <el-descriptions border :column="1">
                <el-descriptions-item
                  :label="$t('views.cookiemanager.pep1je')"
                  >{{ testResult.account_id }}</el-descriptions-item
                >
                <el-descriptions-item
                  :label="$t('views.cookiemanager.h324e4')"
                  >{{ testResult.status }}</el-descriptions-item
                >
                <el-descriptions-item
                  :label="$t('views.cookiemanager.he5717')"
                  >{{ testResult.action_taken }}</el-descriptions-item
                >
              </el-descriptions>
            </template>
          </el-result>
        </template>
        <el-empty v-else :description="$t('views.cookiemanager.ksf4g2')" />
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
            <el-descriptions-item :label="$t('views.cookiemanager.5e9o59')">{{
              batchTestResult.total_tested
            }}</el-descriptions-item>
            <el-descriptions-item :label="$t('views.cookiemanager.92wnmz')">
              <el-tag type="success">{{ batchTestResult.valid_count }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item :label="$t('views.cookiemanager.31k5ft')">
              <el-tag type="warning">{{ batchTestResult.banned_count }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item :label="$t('views.cookiemanager.7r1583')">
              <el-tag type="danger">{{
                batchTestResult.not_login_count
              }}</el-tag>
            </el-descriptions-item>
          </el-descriptions>

          <el-divider />

          <el-tabs>
            <el-tab-pane :label="$t('views.cookiemanager.ukji93')">
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
                <el-empty
                  v-if="!batchTestResult.valid_accounts.length"
                  :description="$t('views.cookiemanager.387e2o')"
                />
              </div>
            </el-tab-pane>
            <el-tab-pane :label="$t('views.cookiemanager.80371x')">
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
                <el-empty
                  v-if="!batchTestResult.banned_accounts.length"
                  :description="$t('views.cookiemanager.y7o532')"
                />
              </div>
            </el-tab-pane>
            <el-tab-pane :label="$t('views.cookiemanager.8d95yp')">
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

                <el-empty
                  v-if="!batchTestResult.not_login_accounts.length"
                  :description="$t('views.cookiemanager.cjq16u')"
                />
              </div>
            </el-tab-pane>
          </el-tabs>
        </template>
        <el-empty v-else :description="$t('views.cookiemanager.ksf4g2')" />
      </div>
    </el-dialog>

    <!-- 添加批量临时封禁对话框 -->
    <el-dialog
      v-model="batchTempBanDialogVisible"
      :title="$t('views.cookiemanager.pm211s')"
      width="400px"
      destroy-on-close
    >
      <el-form :model="batchTempBanForm" label-width="100px">
        <el-form-item :label="$t('views.cookiemanager.8sthw8')">
          <el-input-number
            v-model="batchTempBanForm.duration_minutes"
            :min="1"
            :max="1440"
          />
          <span class="form-tip">{{ $t("views.cookiemanager.8585f1") }}</span>
        </el-form-item>
        <el-form-item :label="$t('views.cookiemanager.43648j')">
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
          <el-button @click="batchTempBanDialogVisible = false">{{
            $t("views.cookiemanager.fl98bx")
          }}</el-button>
          <el-button
            type="primary"
            @click="submitBatchTempBan"
            :loading="batchActionLoading"
            >{{ $t("views.cookiemanager.og231w") }}</el-button
          >
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.cookie-manager-container {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 32px 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  padding: 24px 32px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--glass-border);
  box-shadow: var(--shadow-md);
}

.page-header h1 {
  font-size: 2rem;
  font-weight: 800;
  color: var(--color-text-main);
  letter-spacing: -1px;
  margin: 0;
}

.api-status {
  display: flex;
  align-items: center;
}

/* Stats Overview */
.status-overview {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.status-item {
  background: var(--color-bg-subtle);
  border-radius: var(--radius-lg);
  padding: 16px;
  border: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: left;
  position: relative;
  overflow: hidden;
}

.status-item:hover {
  border-color: var(--color-primary-light);
  background: var(--color-bg-surface);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.status-value {
  font-size: 1.75rem;
  font-weight: 800;
  color: var(--color-text-main);
  line-height: 1.2;
}

.status-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--color-text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.status-item.success .status-value {
  color: var(--color-success);
}
.status-item.warning .status-value {
  color: var(--color-warning);
}
.status-item.danger .status-value {
  color: var(--color-danger);
}

/* Card Styles */
.status-card,
.banned-accounts-card,
.cookie-list-card {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border-radius: var(--radius-lg);
  border: 1px solid var(--glass-border);
  box-shadow: var(--shadow-sm);
  transition: all 0.3s ease;
  margin-bottom: 24px !important;
}

.status-card:hover,
.banned-accounts-card:hover,
.cookie-list-card:hover {
  box-shadow: var(--shadow-md);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.card-header span {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-text-main);
  transition: color 0.3s ease;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 24px;
  justify-content: flex-start;
}

/* Account List */
.account-list-section {
  margin-top: 32px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h3 {
  font-size: 1rem;
  font-weight: 700;
  margin: 0;
  color: var(--color-text-main);
}

.account-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 500px;
  overflow-y: auto;
  padding-right: 4px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-base);
  padding: 8px;
  background: var(--color-bg-subtle);
}

.account-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: var(--color-bg-surface);
  border-radius: var(--radius-base);
  border: 1px solid transparent;
  transition: all 0.2s;
}

.account-item:hover {
  border-color: var(--color-primary-light);
  box-shadow: var(--shadow-sm);
}

.account-info {
  display: flex;
  align-items: center;
}

.account-actions {
  display: flex;
  gap: 8px;
}

/* Banned Accounts Section */
.banned-accounts :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.banned-accounts :deep(.el-tabs__active-bar) {
  height: 3px;
  border-radius: 3px;
  background: var(--color-primary-gradient);
}

.banned-accounts :deep(.el-tabs__item) {
  font-weight: 700;
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  transition: all 0.3s;
}

.banned-accounts :deep(.el-tabs__item.is-active) {
  color: var(--color-primary);
}

.banned-accounts :deep(.el-tabs__item:focus:not(:focus-visible)),
.banned-accounts :deep(.el-tabs__item:focus-visible) {
  outline: none;
  box-shadow: none;
}

.banned-toolbar {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  padding: 12px;
  background: var(--color-bg-subtle);
  border-radius: var(--radius-base);
  border-bottom: none;
}

.banned-accounts {
  max-height: 500px;
  overflow-y: auto;
}

.banned-account-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
  transition: all 0.2s;
}

.banned-account-item:hover {
  background: var(--color-bg-subtle);
}

.banned-account-item:last-child {
  border-bottom: none;
}

.banned-checkbox {
  margin-right: 4px;
}

.banned-account-info {
  display: flex;
  flex-direction: column;
  flex: 1;
  gap: 6px;
  min-width: 0;
}

.account-header {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.account-id {
  font-weight: 700;
  font-family: "JetBrains Mono", "Fira Code", monospace;
  font-size: 1rem;
  color: var(--color-text-main);
  word-break: break-all;
}

.status-tag {
  flex-shrink: 0;
}

.ban-time-meta {
  font-size: 0.75rem;
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  gap: 4px;
}

.banned-account-actions {
  flex-shrink: 0;
  margin-left: auto;
}

/* Filters and Tables */
.filter-section {
  display: flex;
  margin-bottom: 24px;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-item {
  width: 220px;
}

.batch-actions {
  margin-bottom: 20px;
  display: flex;
  gap: 12px;
  padding: 12px 20px;
  background: var(--color-primary-light);
  border-radius: var(--radius-lg);
  align-items: center;
}

.selection-info {
  font-weight: 600;
  color: var(--color-primary);
  margin-left: 12px;
}

.el-table {
  --el-table-border-color: var(--color-border);
  --el-table-bg-color: transparent;
  --el-table-tr-bg-color: transparent;
  --el-table-header-bg-color: var(--color-bg-subtle);
  background-color: transparent;
  border-radius: var(--radius-lg);
  overflow: hidden;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 24px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
}

/* Helper Classes from User */
.mr-5 {
  margin-right: 5px;
}
.mb-5 {
  margin-bottom: 5px;
}
.ml-10 {
  margin-left: 10px;
}

.selected-accounts {
  max-height: 100px;
  overflow-y: auto;
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-base);
  background: var(--color-bg-subtle);
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.usage-chart-card {
  margin-bottom: 24px;
  border-radius: var(--radius-lg);
}

.table-toolbar {
  margin-bottom: 16px;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.search-bar {
  margin-bottom: 24px;
}

.form-tip {
  margin-left: 10px;
  font-size: 12px;
  color: var(--color-text-secondary);
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
  padding: 12px;
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-base);
}

.test-result-tag {
  margin-bottom: 0;
}

.form-actions {
  display: flex;
  margin-top: 16px;
  gap: 12px;
  justify-content: flex-end;
}

.el-upload__tip {
  margin-top: 8px;
  color: var(--color-text-secondary);
}

.dialog-subtitle {
  margin: 0 0 16px 0;
  padding-bottom: 12px;
  font-size: 1.1rem;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-primary);
  font-weight: 600;
}
</style>
