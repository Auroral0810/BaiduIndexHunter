<script setup>
import { useI18n } from "vue-i18n";
import { ref, reactive, onMounted, onUnmounted, watch, computed } from "vue";
import * as echarts from "echarts";
import axios from "axios";
import { ElMessage, ElTable, ElTableColumn } from "element-plus";

const { t, locale } = useI18n();

const props = defineProps({
  apiBaseUrl: {
    type: String,
    default: "http://127.0.0.1:5001/api",
  },
});

const chartDom = ref(null);
const usageChartInstance = ref(null);
const cookieUsageData = ref([]);
const cookieUsageLoading = ref(false);
const dateRange = ref([]);
const topN = ref(10);
const viewMode = ref("daily"); // 'daily' | 'account' | 'line' | 'pie' | 'scatter' | 'heatmap'
const chartType = ref("bar"); // 'bar' | 'line' | 'pie' | 'scatter' | 'heatmap'
const showDataTable = ref(false);
const detailDate = ref(null);
const dailyDetailVisible = ref(false);

// 计算属性 - 获取所有日期
const availableDates = computed(() => {
  const dates = [
    ...new Set(cookieUsageData.value.map((item) => item.usage_date)),
  ].sort();
  return dates;
});

// 图表配置
const dailyChartOption = reactive({
  title: {
    text: t("components-CookieUsageChart-19c298e1b08b4a7ef-26"),
    left: "center",
  },
  tooltip: {
    trigger: "axis",
    axisPointer: {
      type: "shadow",
    },
  },
  toolbox: {
    feature: {
      saveAsImage: { name: "cookie_usage_daily" },
      dataZoom: {
        yAxisIndex: "none",
      },
      restore: {},
      dataView: { readOnly: false },
      magicType: { type: ["bar", "line"] },
    },
  },
  dataZoom: [
    {
      type: "slider",
      show: true,
      xAxisIndex: [0],
      start: 0,
      end: 100,
    },
    {
      type: "inside",
      xAxisIndex: [0],
      start: 0,
      end: 100,
    },
  ],

  grid: {
    left: "3%",
    right: "4%",
    bottom: "15%",
    containLabel: true,
  },
  xAxis: {
    type: "category",
    data: [],
    axisLabel: {
      rotate: 45,
    },
  },
  yAxis: {
    type: "value",
    name: t("components-CookieUsageChart-19c298e1b08b4a7ef-27"),
  },
  series: [
    {
      name: t("components-CookieUsageChart-19c298e1b08b4a7ef-28"),
      type: "bar",
      data: [],
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: "#83bff6" },
          { offset: 0.5, color: "#188df0" },
          { offset: 1, color: "#188df0" },
        ]),
      },
      emphasis: {
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "#2378f7" },
            { offset: 0.7, color: "#2378f7" },
            { offset: 1, color: "#83bff6" },
          ]),
        },
      },
    },
  ],
});

const accountChartOption = reactive({
  title: {
    text: t("components-CookieUsageChart-19c298e1b08b4a7ef-29"),
    left: "center",
  },
  tooltip: {
    trigger: "axis",
    axisPointer: {
      type: "shadow",
    },
  },
  toolbox: {
    feature: {
      saveAsImage: { name: "cookie_usage_account" },
      dataZoom: {
        yAxisIndex: "none",
      },
      restore: {},
      dataView: { readOnly: false },
    },
  },
  dataZoom: [
    {
      type: "slider",
      show: true,
      yAxisIndex: [0],
      start: 0,
      end: 100,
    },
    {
      type: "inside",
      yAxisIndex: [0],
      start: 0,
      end: 100,
    },
  ],

  grid: {
    left: "3%",
    right: "4%",
    bottom: "3%",
    containLabel: true,
  },
  xAxis: {
    type: "value",
    name: t("components-CookieUsageChart-19c298e1b08b4a7ef-30"),
  },
  yAxis: {
    type: "category",
    data: [],
    axisLabel: {
      width: 120,
      overflow: "truncate",
    },
  },
  series: [
    {
      name: t("components-CookieUsageChart-19c298e1b08b4a7ef-31"),
      type: "bar",
      data: [],
      itemStyle: {
        color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
          { offset: 0, color: "#83bff6" },
          { offset: 0.5, color: "#188df0" },
          { offset: 1, color: "#188df0" },
        ]),
      },
      emphasis: {
        itemStyle: {
          color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
            { offset: 0, color: "#2378f7" },
            { offset: 0.7, color: "#2378f7" },
            { offset: 1, color: "#83bff6" },
          ]),
        },
      },
    },
  ],
});

const lineChartOption = reactive({
  title: {
    text: t("components-CookieUsageChart-19c298e1b08b4a7ef-32"),
    left: "center",
  },
  tooltip: {
    trigger: "axis",
    axisPointer: {
      type: "cross",
    },
  },
  legend: {
    type: "scroll",
    bottom: 0,
  },
  toolbox: {
    feature: {
      saveAsImage: { name: "cookie_usage_trend" },
      dataZoom: {
        yAxisIndex: "none",
      },
      restore: {},
      dataView: { readOnly: false },
    },
  },
  dataZoom: [
    {
      type: "slider",
      show: true,
      xAxisIndex: [0],
      start: 0,
      end: 100,
    },
    {
      type: "inside",
      xAxisIndex: [0],
      start: 0,
      end: 100,
    },
  ],

  grid: {
    left: "3%",
    right: "4%",
    bottom: "15%",
    containLabel: true,
  },
  xAxis: {
    type: "category",
    data: [],
    boundaryGap: false,
  },
  yAxis: {
    type: "value",
    name: t("components-CookieUsageChart-19c298e1b08b4a7ef-33"),
    splitLine: {
      lineStyle: {
        type: "dashed",
      },
    },
  },
  series: [],
});

const pieChartOption = reactive({
  title: {
    text: t("components-CookieUsageChart-19c298e1b08b4a7ef-34"),
    left: "center",
  },
  tooltip: {
    trigger: "item",
    formatter: "{a} <br/>{b}: {c} ({d}%)",
  },
  legend: {
    type: "scroll",
    orient: "vertical",
    right: 10,
    top: 20,
    bottom: 20,
  },
  toolbox: {
    feature: {
      saveAsImage: { name: "cookie_usage_distribution" },
      restore: {},
      dataView: { readOnly: false },
    },
  },
  series: [
    {
      name: t("components-CookieUsageChart-19c298e1b08b4a7ef-35"),
      type: "pie",
      radius: ["40%", "70%"],
      avoidLabelOverlap: false,
      itemStyle: {
        borderRadius: 10,
        borderColor: "#fff",
        borderWidth: 2,
      },
      label: {
        show: false,
        position: "center",
      },
      emphasis: {
        label: {
          show: true,
          fontSize: "16",
          fontWeight: "bold",
        },
      },
      labelLine: {
        show: false,
      },
      data: [],
    },
  ],
});

const heatmapChartOption = reactive({
  title: {
    text: t("components-CookieUsageChart-19c298e1b08b4a7ef-36"),
    left: "center",
  },
  tooltip: {
    position: "top",
    formatter: function (params) {
      return `${params.data[1]} (${params.data[0]}): ${params.data[2]}${t("components-CookieUsageChart-19c298e1b08b4a7ef-37")}`;
    },
  },
  toolbox: {
    feature: {
      saveAsImage: { name: "cookie_usage_heatmap" },
      restore: {},
      dataView: { readOnly: false },
    },
  },
  grid: {
    height: "70%",
    top: "10%",
  },
  xAxis: {
    type: "category",
    data: [],
    splitArea: {
      show: true,
    },
  },
  yAxis: {
    type: "category",
    data: [],
    splitArea: {
      show: true,
    },
  },
  visualMap: {
    min: 0,
    max: 10,
    calculable: true,
    orient: "horizontal",
    left: "center",
    bottom: "0%",
  },
  series: [
    {
      name: t("components-CookieUsageChart-19c298e1b08b4a7ef-38"),
      type: "heatmap",
      data: [],
      label: {
        show: true,
      },
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: "rgba(0, 0, 0, 0.5)",
        },
      },
    },
  ],
});

// 加载Cookie使用量数据
const loadCookieUsage = async (startDate = null, endDate = null) => {
  try {
    cookieUsageLoading.value = true;

    let params = {};
    if (startDate && endDate) {
      params.start_date = startDate;
      params.end_date = endDate;
    }

    const response = await axios.get(`${props.apiBaseUrl}/admin/cookie/usage`, {
      params,
    });
    if (response.data.code === 10000) {
      cookieUsageData.value = response.data.data || [];
      updateUsageChart();
    } else {
      ElMessage.error(
        `${t("components-CookieUsageChart-19c298e1b08b4a7ef-39")}${response.data.msg}`,
      );
    }
  } catch (error) {
    console.error(
      t("components-CookieUsageChart-19c298e1b08b4a7ef-40"),
      error,
    );
    ElMessage.error(
      t("components-CookieUsageChart-19c298e1b08b4a7ef-41"),
    );
  } finally {
    cookieUsageLoading.value = false;
  }
};

// 更新使用量图表
const updateUsageChart = () => {
  if (!chartDom.value) return;

  switch (viewMode.value) {
    case "daily":
      updateDailyChart();
      break;
    case "account":
      updateAccountChart();
      break;
    case "line":
      updateLineChart();
      break;
    case "pie":
      updatePieChart();
      break;
    case "heatmap":
      updateHeatmapChart();
      break;
    default:
      updateDailyChart();
  }
};

// 更新每日使用量图表
const updateDailyChart = () => {
  // 按日期分组数据
  const groupedByDate = {};
  cookieUsageData.value.forEach((item) => {
    if (!groupedByDate[item.usage_date]) {
      groupedByDate[item.usage_date] = 0;
    }
    groupedByDate[item.usage_date] += item.usage_count;
  });

  // 转换为图表数据
  const dates = Object.keys(groupedByDate).sort();
  const values = dates.map((date) => groupedByDate[date]);

  // 更新图表配置
  dailyChartOption.xAxis.data = dates;
  dailyChartOption.series[0].data = values;
  dailyChartOption.series[0].type = chartType.value;

  // 渲染图表
  if (!usageChartInstance.value) {
    usageChartInstance.value = echarts.init(chartDom.value);
    // 添加点击事件，显示单日详情
    usageChartInstance.value.on("click", (params) => {
      if (params.componentType === "series") {
        showDailyDetail(params.name);
      }
    });
  }
  usageChartInstance.value.setOption(dailyChartOption, true);
};

// 更新账号使用量图表
const updateAccountChart = () => {
  // 按账号分组数据
  const groupedByAccount = {};
  cookieUsageData.value.forEach((item) => {
    if (!groupedByAccount[item.account_id]) {
      groupedByAccount[item.account_id] = 0;
    }
    groupedByAccount[item.account_id] += item.usage_count;
  });

  // 转换为图表数据并排序
  let accountData = Object.entries(groupedByAccount)
    .map(([account, count]) => ({ account, count }))
    .sort((a, b) => b.count - a.count);

  // 只取前N个
  accountData = accountData.slice(0, topN.value);

  const accounts = accountData.map((item) => item.account);
  const values = accountData.map((item) => item.count);

  // 更新图表配置
  accountChartOption.yAxis.data = accounts;
  accountChartOption.series[0].data = values;

  // 渲染图表
  if (!usageChartInstance.value) {
    usageChartInstance.value = echarts.init(chartDom.value);
  }
  usageChartInstance.value.setOption(accountChartOption, true);
};

// 更新趋势线图
const updateLineChart = () => {
  // 获取所有不同的账号和日期
  const accounts = [
    ...new Set(cookieUsageData.value.map((item) => item.account_id)),
  ];
  const dates = [
    ...new Set(cookieUsageData.value.map((item) => item.usage_date)),
  ].sort();

  // 对数据按照账号和日期进行分组
  const accountData = {};
  accounts.forEach((account) => {
    accountData[account] = {};
    dates.forEach((date) => {
      accountData[account][date] = 0;
    });
  });

  // 填充数据
  cookieUsageData.value.forEach((item) => {
    accountData[item.account_id][item.usage_date] = item.usage_count;
  });

  // 选择前N个使用量最高的账号
  const totalUsageByAccount = {};
  accounts.forEach((account) => {
    totalUsageByAccount[account] = Object.values(accountData[account]).reduce(
      (sum, count) => sum + count,
      0,
    );
  });

  const topAccounts = Object.entries(totalUsageByAccount)
    .sort((a, b) => b[1] - a[1])
    .slice(0, topN.value)
    .map((item) => item[0]);

  // 创建线图系列数据
  const series = topAccounts.map((account) => {
    return {
      name: account,
      type: "line",
      data: dates.map((date) => accountData[account][date]),
      smooth: true,
      showSymbol: false,
      emphasis: {
        focus: "series",
      },
    };
  });

  // 更新图表配置
  lineChartOption.xAxis.data = dates;
  lineChartOption.series = series;

  // 渲染图表
  if (!usageChartInstance.value) {
    usageChartInstance.value = echarts.init(chartDom.value);
  }
  usageChartInstance.value.setOption(lineChartOption, true);
};

// 更新饼图
const updatePieChart = () => {
  // 按账号分组数据
  const groupedByAccount = {};
  cookieUsageData.value.forEach((item) => {
    if (!groupedByAccount[item.account_id]) {
      groupedByAccount[item.account_id] = 0;
    }
    groupedByAccount[item.account_id] += item.usage_count;
  });

  // 转换为图表数据并排序
  let accountData = Object.entries(groupedByAccount)
    .map(([account, count]) => ({ account, count }))
    .sort((a, b) => b.count - a.count);

  // 只取前N个，其他归为"其他"类别
  const topData = accountData.slice(0, topN.value);
  const otherData = accountData.slice(topN.value);

  let pieData = topData.map((item) => ({
    name: item.account,
    value: item.count,
  }));

  // 如果有其他数据，汇总为"其他"类别
  if (otherData.length > 0) {
    const otherSum = otherData.reduce((sum, item) => sum + item.count, 0);
    pieData.push({
      name: t("components-CookieUsageChart-19c298e1b08b4a7ef-42"),
      value: otherSum,
    });
  }

  // 更新图表配置
  pieChartOption.series[0].data = pieData;

  // 渲染图表
  if (!usageChartInstance.value) {
    usageChartInstance.value = echarts.init(chartDom.value);
  }
  usageChartInstance.value.setOption(pieChartOption, true);
};

// 更新热力图
const updateHeatmapChart = () => {
  // 获取所有不同的账号和日期
  const accounts = [
    ...new Set(cookieUsageData.value.map((item) => item.account_id)),
  ]
    .sort((a, b) => a.localeCompare(b))
    .slice(0, 20); // 限制最多20个账号，以免图表太拥挤

  const dates = [
    ...new Set(cookieUsageData.value.map((item) => item.usage_date)),
  ].sort();

  // 准备热力图数据
  const heatmapData = [];
  const maxValue = { value: 0 };

  cookieUsageData.value.forEach((item) => {
    if (accounts.includes(item.account_id)) {
      heatmapData.push([item.usage_date, item.account_id, item.usage_count]);
      if (item.usage_count > maxValue.value) {
        maxValue.value = item.usage_count;
      }
    }
  });

  // 更新图表配置
  heatmapChartOption.xAxis.data = dates;
  heatmapChartOption.yAxis.data = accounts;
  heatmapChartOption.series[0].data = heatmapData;
  heatmapChartOption.visualMap.max = maxValue.value;

  // 渲染图表
  if (!usageChartInstance.value) {
    usageChartInstance.value = echarts.init(chartDom.value);
  }
  usageChartInstance.value.setOption(heatmapChartOption, true);
};

// 处理日期范围变化
const handleDateRangeChange = () => {
  if (dateRange.value && dateRange.value.length === 2) {
    const startDate = formatDate(dateRange.value[0]);
    const endDate = formatDate(dateRange.value[1]);
    loadCookieUsage(startDate, endDate);
  }
};

// 格式化日期
const formatDate = (date) => {
  if (!date) return "";
  const d = new Date(date);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
};

// 同步Redis和MySQL中的使用量数据
const syncUsageData = async () => {
  try {
    cookieUsageLoading.value = true;

    const response = await axios.post(
      `${props.apiBaseUrl}/admin/cookie/usage/sync`,
    );
    if (response.data.code === 10000) {
      ElMessage.success(
        t("components-CookieUsageChart-19c298e1b08b4a7ef-43"),
      );
      loadCookieUsage();
    } else {
      ElMessage.error(
        `${t("components-CookieUsageChart-19c298e1b08b4a7ef-44")}${response.data.msg}`,
      );
    }
  } catch (error) {
    console.error(
      t("components-CookieUsageChart-19c298e1b08b4a7ef-45"),
      error,
    );
    ElMessage.error(
      t("components-CookieUsageChart-19c298e1b08b4a7ef-46"),
    );
  } finally {
    cookieUsageLoading.value = false;
  }
};

// 切换视图模式
const switchViewMode = (mode) => {
  viewMode.value = mode;
  updateUsageChart();
};

// 切换图表类型
const switchChartType = (type) => {
  chartType.value = type;
  updateUsageChart();
};

// 切换数据表格可见性
const toggleDataTable = () => {
  showDataTable.value = !showDataTable.value;
};

// 导出当前数据为CSV
const exportToCsv = () => {
  try {
    let csvContent = t(
      "components-CookieUsageChart-19c298e1b08b4a7ef-47",
    );

    cookieUsageData.value.forEach((item) => {
      csvContent += `${item.account_id},${item.usage_date},${item.usage_count}\n`;
    });

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute(
      "download",
      `cookie_usage_data_${formatDate(new Date())}.csv`,
    );
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    ElMessage.success(
      t("components-CookieUsageChart-19c298e1b08b4a7ef-48"),
    );
  } catch (error) {
    console.error(
      t("components-CookieUsageChart-19c298e1b08b4a7ef-49"),
      error,
    );
    ElMessage.error(
      t("components-CookieUsageChart-19c298e1b08b4a7ef-50"),
    );
  }
};

// 显示单日详情
const showDailyDetail = (date) => {
  detailDate.value = date;
  dailyDetailVisible.value = true;
};

// 计算单日详情数据
const dailyDetailData = computed(() => {
  if (!detailDate.value) return [];

  return cookieUsageData.value
    .filter((item) => item.usage_date === detailDate.value)
    .sort((a, b) => b.usage_count - a.usage_count);
});

// 监听视图模式变化
watch(viewMode, () => {
  updateUsageChart();
});

// 监听图表类型变化
watch(chartType, () => {
  if (["daily"].includes(viewMode.value)) {
    updateUsageChart();
  }
});

// 监听topN变化
watch(topN, () => {
  if (["account", "line", "pie"].includes(viewMode.value)) {
    updateUsageChart();
  }
});

// 生命周期钩子
onMounted(() => {
  loadCookieUsage();

  // 添加窗口大小变化监听
  window.addEventListener("resize", handleResize);
});

// 窗口大小变化时重绘图表
const handleResize = () => {
  if (usageChartInstance.value) {
    usageChartInstance.value.resize();
  }
};

// 更新图表的国际化文本
const updateChartI18nTexts = () => {
  // 更新 dailyChartOption
  dailyChartOption.title.text = t("components-CookieUsageChart-19c298e1b08b4a7ef-26");
  dailyChartOption.yAxis.name = t("components-CookieUsageChart-19c298e1b08b4a7ef-27");
  dailyChartOption.series[0].name = t("components-CookieUsageChart-19c298e1b08b4a7ef-28");
  
  // 更新 accountChartOption
  accountChartOption.title.text = t("components-CookieUsageChart-19c298e1b08b4a7ef-29");
  accountChartOption.xAxis.name = t("components-CookieUsageChart-19c298e1b08b4a7ef-30");
  accountChartOption.series[0].name = t("components-CookieUsageChart-19c298e1b08b4a7ef-31");
  
  // 更新 lineChartOption
  lineChartOption.title.text = t("components-CookieUsageChart-19c298e1b08b4a7ef-32");
  lineChartOption.yAxis.name = t("components-CookieUsageChart-19c298e1b08b4a7ef-33");
  
  // 更新 pieChartOption
  pieChartOption.title.text = t("components-CookieUsageChart-19c298e1b08b4a7ef-34");
  pieChartOption.series[0].name = t("components-CookieUsageChart-19c298e1b08b4a7ef-35");
  
  // 更新 heatmapChartOption
  heatmapChartOption.title.text = t("components-CookieUsageChart-19c298e1b08b4a7ef-36");
  
  // 刷新图表显示
  if (usageChartInstance.value) {
    updateUsageChart();
  }
};

// 监听语言变化，更新图表文本
watch(locale, () => {
  updateChartI18nTexts();
});

// 在组件卸载时清除资源
onUnmounted(() => {
  // 销毁图表实例
  if (usageChartInstance.value) {
    usageChartInstance.value.dispose();
    usageChartInstance.value = null;
  }

  // 移除窗口大小变化监听
  window.removeEventListener("resize", handleResize);
});

// 暴露方法给父组件
defineExpose({
  loadCookieUsage,
  syncUsageData,
});
</script>

<template>
  <div class="cookie-usage-chart-container">
    <div class="chart-header">
      <div class="chart-controls">
        <el-radio-group v-model="viewMode" size="small"
          ><el-radio-button label="daily">{{
            $t("components-CookieUsageChart-19c298e1b08b4a7ef-1")
          }}</el-radio-button>
          <el-radio-button label="account">{{
            $t("components-CookieUsageChart-19c298e1b08b4a7ef-2")
          }}</el-radio-button>
          <el-radio-button label="line">{{
            $t("components-CookieUsageChart-19c298e1b08b4a7ef-3")
          }}</el-radio-button>
          <el-radio-button label="pie">{{
            $t("components-CookieUsageChart-19c298e1b08b4a7ef-4")
          }}</el-radio-button>
          <el-radio-button label="heatmap">{{
            $t("components-CookieUsageChart-19c298e1b08b4a7ef-5")
          }}</el-radio-button></el-radio-group
        >
        <el-radio-group
          v-if="viewMode === 'daily'"
          v-model="chartType"
          size="small"
          ><el-radio-button label="bar">{{
            $t("components-CookieUsageChart-19c298e1b08b4a7ef-6")
          }}</el-radio-button>
          <el-radio-button label="line">{{
            $t("components-CookieUsageChart-19c298e1b08b4a7ef-7")
          }}</el-radio-button></el-radio-group
        >
        <el-input-number
          v-if="['account', 'line', 'pie'].includes(viewMode)"
          v-model="topN"
          :min="5"
          :max="50"
          size="small"
          class="top-n-selector"
          :placeholder="$t('components-CookieUsageChart-19c298e1b08b4a7ef-8')"
        />
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          :range-separator="
            $t('components-CookieUsageChart-19c298e1b08b4a7ef-9')
          "
          :start-placeholder="
            $t('components-CookieUsageChart-19c298e1b08b4a7ef-10')
          "
          :end-placeholder="
            $t('components-CookieUsageChart-19c298e1b08b4a7ef-11')
          "
          size="small"
          @change="handleDateRangeChange"
        />
        <div class="action-buttons">
          <el-button
            type="primary"
            size="small"
            @click="syncUsageData"
            :loading="cookieUsageLoading"
            >{{
              $t("components-CookieUsageChart-19c298e1b08b4a7ef-12")
            }}</el-button
          >
          <el-button type="success" size="small" @click="toggleDataTable">{{
            showDataTable
              ? $t("components-CookieUsageChart-19c298e1b08b4a7ef-13")
              : $t("components-CookieUsageChart-19c298e1b08b4a7ef-14")
          }}</el-button>
          <el-button type="info" size="small" @click="exportToCsv">{{
            $t("components-CookieUsageChart-19c298e1b08b4a7ef-15")
          }}</el-button>
        </div>
      </div>
    </div>
    <div
      ref="chartDom"
      class="chart-container"
      v-loading="cookieUsageLoading"
    ></div>
    <!-- 数据表格 -->
    <div v-if="showDataTable" class="data-table-container">
      <h3>{{ $t("components-CookieUsageChart-19c298e1b08b4a7ef-16") }}</h3>
      <el-table
        :data="cookieUsageData"
        border
        stripe
        style="width: 100%"
        height="300"
        ><el-table-column
          prop="account_id"
          :label="$t('components-CookieUsageChart-19c298e1b08b4a7ef-17')"
          sortable />
        <el-table-column
          prop="usage_date"
          :label="$t('components-CookieUsageChart-19c298e1b08b4a7ef-18')"
          sortable />
        <el-table-column
          prop="usage_count"
          :label="$t('components-CookieUsageChart-19c298e1b08b4a7ef-19')"
          sortable
      /></el-table>
    </div>
    <!-- 单日详情对话框 -->
    <el-dialog
      v-model="dailyDetailVisible"
      :title="`${detailDate}${$t('components-CookieUsageChart-19c298e1b08b4a7ef-20')}`"
      width="600px"
      destroy-on-close
      ><el-table
        :data="dailyDetailData"
        border
        stripe
        style="width: 100%"
        max-height="500"
        ><el-table-column
          prop="account_id"
          :label="$t('components-CookieUsageChart-19c298e1b08b4a7ef-21')"
          width="180"
          sortable />
        <el-table-column
          prop="usage_count"
          :label="$t('components-CookieUsageChart-19c298e1b08b4a7ef-22')"
          width="100"
          sortable />
        <el-table-column
          :label="$t('components-CookieUsageChart-19c298e1b08b4a7ef-23')"
          ><template #default="scope"
            ><el-progress
              :percentage="
                Math.round(
                  (scope.row.usage_count /
                    dailyDetailData.reduce(
                      (sum, item) => sum + item.usage_count,
                      0,
                    )) *
                    100,
                )
              "
              :stroke-width="15" /></template></el-table-column
      ></el-table>
      <template #footer
        ><div class="dialog-footer">
          <el-button @click="dailyDetailVisible = false">{{
            $t("components-CookieUsageChart-19c298e1b08b4a7ef-24")
          }}</el-button>
          <el-button type="primary" @click="exportToCsv">{{
            $t("components-CookieUsageChart-19c298e1b08b4a7ef-25")
          }}</el-button>
        </div></template
      ></el-dialog
    >
  </div>
</template>

<style scoped>
.cookie-usage-chart-container {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.chart-header {
  margin-bottom: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.chart-controls {
  display: flex;
  gap: 15px;
  align-items: center;
  flex-wrap: wrap;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.top-n-selector {
  width: 120px;
}

.chart-container {
  height: 500px;
  width: 100%;
  transition: all 0.3s ease;
}

.data-table-container {
  margin-top: 20px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 15px;
}

.data-table-container h3 {
  margin-top: 0;
  margin-bottom: 15px;
  font-size: 16px;
  color: #4f46e5;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .chart-controls {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .chart-container {
    height: 400px;
  }
}
</style>
