<template>
  <div class="task-container">
    <div class="task-header">
      <h2>{{ $t("tasks-WordGraphTask-19c298e227e044aa6-1") }}</h2>
      <div class="task-desc">
        {{ $t("tasks-WordGraphTask-19c298e227e044aa6-2") }}
      </div>
    </div>
    <el-card class="task-card"
      ><template #header
        ><div class="card-header">
          <span>{{ $t("tasks-WordGraphTask-19c298e227e044aa6-3") }}</span>
        </div></template
      >
      <el-form :model="formData" label-width="120px" class="task-form"
        ><!-- 关键词设置 -->
        <el-divider content-position="left">{{
          $t("tasks-WordGraphTask-19c298e227e044aa6-4")
        }}</el-divider>
        <el-form-item :label="$t('tasks-WordGraphTask-19c298e227e044aa6-5')"
          ><el-input
            v-model="batchKeywords"
            type="textarea"
            :rows="4"
            :placeholder="$t('tasks-WordGraphTask-19c298e227e044aa6-6')"
          />
          <div class="keywords-actions">
            <el-button
              type="primary"
              @click="addBatchKeywords"
              :disabled="!batchKeywords.trim()"
              ><el-icon><Plus /></el-icon>
              {{ $t("tasks-WordGraphTask-19c298e227e044aa6-7") }}</el-button
            >
            <span class="keywords-tip">{{
              $t("tasks-WordGraphTask-19c298e227e044aa6-8")
            }}</span>
          </div></el-form-item
        >
        <el-form-item :label="$t('tasks-WordGraphTask-19c298e227e044aa6-9')"
          ><el-upload
            class="upload-area"
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleKeywordsFileChange"
            accept=".xlsx,.csv,.txt"
            ><el-button type="primary"
              ><el-icon><Upload /></el-icon>
              {{ $t("tasks-WordGraphTask-19c298e227e044aa6-10") }}</el-button
            >
            <div class="upload-tip">
              {{ $t("tasks-WordGraphTask-19c298e227e044aa6-11") }}
            </div></el-upload
          >
          <div class="file-import-options">
            <el-checkbox v-model="skipFirstLine">{{
              $t("tasks-WordGraphTask-19c298e227e044aa6-12")
            }}</el-checkbox>
          </div></el-form-item
        >
        <el-form-item
          :label="$t('tasks-WordGraphTask-19c298e227e044aa6-13')"
          v-if="formData.keywords.length > 0"
          ><div class="keywords-tags-container">
            <div class="keywords-tags">
              <el-tag
                v-for="(keyword, index) in formData.keywords"
                :key="index"
                closable
                @close="removeKeyword(index)"
                class="keyword-tag"
                :type="
                  keywordCheckResults[keyword.value] === false
                    ? 'danger'
                    : keywordCheckResults[keyword.value] === true
                      ? 'success'
                      : ''
                "
                >{{ keyword.value }}
                <el-tooltip
                  v-if="keywordCheckResults[keyword.value] === false"
                  :content="$t('tasks-WordGraphTask-19c298e227e044aa6-14')"
                  placement="top"
                  ><el-icon class="keyword-warning"
                    ><Warning /></el-icon></el-tooltip
              ></el-tag>
            </div>
            <div class="keywords-actions">
              <el-button type="danger" plain size="small" @click="clearKeywords"
                ><el-icon><Delete /></el-icon>
                {{ $t("tasks-WordGraphTask-19c298e227e044aa6-15") }}</el-button
              >
              <el-button
                type="primary"
                size="small"
                @click="checkKeywords"
                :loading="checkingKeywords"
                ><el-icon><Check /></el-icon>
                {{ $t("tasks-WordGraphTask-19c298e227e044aa6-16") }}</el-button
              >
              <el-button
                type="warning"
                plain
                size="small"
                @click="removeInvalidKeywords"
                :disabled="!hasInvalidKeywords"
                ><el-icon><Close /></el-icon>
                {{ $t("tasks-WordGraphTask-19c298e227e044aa6-17") }}</el-button
              >
              <div class="keywords-count">
                {{ $t("tasks-WordGraphTask-19c298e227e044aa6-18") }}
                {{ formData.keywords.length }}
                {{ $t("tasks-WordGraphTask-19c298e227e044aa6-19") }}
              </div>
            </div>
          </div></el-form-item
        >
        <!-- 日期设置 -->
        <el-divider content-position="left">{{
          $t("tasks-WordGraphTask-19c298e227e044aa6-20")
        }}</el-divider>
        <el-form-item :label="$t('tasks-WordGraphTask-19c298e227e044aa6-24')">
          <div class="date-selection-container" v-loading="loadingTimeRange">
            <div class="date-selection-header">
              <span class="selection-count" v-if="selectedWeeks.length > 0">
                已选择 <el-tag type="success" size="small">{{ selectedWeeks.length }}</el-tag> 周
              </span>
              <div class="selection-actions">
                <el-button link type="primary" @click="selectAllWeeks" :disabled="!weeklyDates.length">全选</el-button>
                <el-button link type="warning" @click="clearWeeks" :disabled="!selectedWeeks.length">清空</el-button>
              </div>
            </div>
            
            <el-select
              v-model="selectedWeeks"
              multiple
              filterable
              collapse-tags
              collapse-tags-tooltip
              :placeholder="timeRangeError ? '获取时间范围失败' : '请选择周开始日期'"
              style="width: 100%"
              :disabled="!weeklyDates.length"
            >
              <el-option
                v-for="item in weeklyDates"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            
            <div class="date-range-info" v-if="timeRangeStore.startDate && timeRangeStore.endDate">
              <el-icon><Calendar /></el-icon>
              <span>可选范围：{{ timeRangeStore.startDate }} 至 {{ timeRangeStore.endDate }}</span>
            </div>
            
            <div class="date-error-info" v-else-if="timeRangeError">
              <el-alert :title="timeRangeError" type="error" :closable="false" show-icon>
                <template #default>
                  <el-button link type="primary" @click="fetchTimeRange">点击重试</el-button>
                </template>
              </el-alert>
            </div>
          </div>
        </el-form-item>
        <!-- 输出设置 -->
        <el-divider content-position="left">{{
          $t("tasks-WordGraphTask-19c298e227e044aa6-30")
        }}</el-divider>
        <el-form-item :label="$t('tasks-WordGraphTask-19c298e227e044aa6-31')"
          ><el-radio-group v-model="formData.output_format"
            ><el-radio label="csv">{{
              $t("tasks-WordGraphTask-19c298e227e044aa6-32")
            }}</el-radio>
            <el-radio label="excel">{{
              $t("tasks-WordGraphTask-19c298e227e044aa6-33")
            }}</el-radio></el-radio-group
          ></el-form-item
        >
        <!-- 任务设置 -->
        <el-divider content-position="left">{{
          $t("tasks-WordGraphTask-19c298e227e044aa6-34")
        }}</el-divider>
        <el-form-item :label="$t('tasks-WordGraphTask-19c298e227e044aa6-35')"
          ><el-switch
            v-model="formData.resume"
            :active-text="$t('tasks-WordGraphTask-19c298e227e044aa6-36')"
            :inactive-text="$t('tasks-WordGraphTask-19c298e227e044aa6-37')"
        /></el-form-item>
        <el-form-item
          :label="$t('tasks-WordGraphTask-19c298e227e044aa6-38')"
          v-if="formData.resume"
          ><el-input
            v-model="formData.task_id"
            :placeholder="$t('tasks-WordGraphTask-19c298e227e044aa6-39')"
        /></el-form-item>
        <el-form-item :label="$t('tasks-WordGraphTask-19c298e227e044aa6-40')"
          ><el-slider
            v-model="formData.priority"
            :marks="priorityMarks"
            :min="1"
            :max="10"
            :step="1"
            show-stops
        /></el-form-item>
        <el-form-item
          ><el-button
            type="primary"
            @click="showTaskOverview"
            :disabled="!canSubmit"
            size="large"
            ><el-icon><Check /></el-icon>
            {{ $t("tasks-WordGraphTask-19c298e227e044aa6-41") }}</el-button
          >
          <el-button @click="resetForm" size="large"
            ><el-icon><Refresh /></el-icon>
            {{ $t("tasks-WordGraphTask-19c298e227e044aa6-42") }}</el-button
          ></el-form-item
        ></el-form
      ></el-card
    >
    <el-dialog
      v-model="successDialogVisible"
      :title="$t('tasks-WordGraphTask-19c298e227e044aa6-43')"
      width="500px"
      ><div class="success-content">
        <el-result
          icon="success"
          :title="$t('tasks-WordGraphTask-19c298e227e044aa6-44')"
          :sub-title="`${$t('tasks-WordGraphTask-19c298e227e044aa6-45')}${taskId}`"
          ><template #extra
            ><el-button type="primary" @click="goToTaskList">{{
              $t("tasks-WordGraphTask-19c298e227e044aa6-46")
            }}</el-button>
            <el-button @click="successDialogVisible = false">{{
              $t("tasks-WordGraphTask-19c298e227e044aa6-47")
            }}</el-button></template
          ></el-result
        >
      </div></el-dialog
    >
    <!-- 关键词检查结果对话框 -->
    <el-dialog
      v-model="checkResultDialogVisible"
      :title="$t('tasks-WordGraphTask-19c298e227e044aa6-48')"
      width="500px"
      modal
      append-to-body
      :close-on-click-modal="false"
      :show-close="true"
      ><div class="check-result-content">
        <el-alert
          v-if="checkResults.existsCount > 0"
          type="success"
          :title="`${checkResults.existsCount}${$t('tasks-WordGraphTask-19c298e227e044aa6-49')}`"
          :closable="false"
          show-icon
        />
        <el-alert
          v-if="checkResults.notExistsCount > 0"
          type="warning"
          :title="`${checkResults.notExistsCount}${$t('tasks-WordGraphTask-19c298e227e044aa6-50')}`"
          :closable="false"
          show-icon
          style="margin-top: 10px"
        />
        <div v-if="checkResults.notExistsCount > 0" class="invalid-keywords">
          <p>{{ $t("tasks-WordGraphTask-19c298e227e044aa6-51") }}</p>
          <div class="keywords-list">
            <el-tag
              v-for="(keyword, index) in checkResults.notExistsKeywords"
              :key="index"
              type="danger"
              class="keyword-tag"
              style="margin: 5px"
              >{{ keyword }}</el-tag
            >
          </div>
        </div>
      </div>
      <template #footer
        ><span class="dialog-footer"
          ><el-button @click="checkResultDialogVisible = false">{{
            $t("tasks-WordGraphTask-19c298e227e044aa6-52")
          }}</el-button>
          <el-button
            type="warning"
            @click="removeInvalidKeywordsFromDialog"
            :disabled="checkResults.notExistsCount === 0"
            >{{ $t("tasks-WordGraphTask-19c298e227e044aa6-53") }}</el-button
          ></span
        ></template
      ></el-dialog
    >
    <!-- 导入结果对话框 -->
    <el-dialog
      v-model="importResultDialogVisible"
      :title="$t('tasks-WordGraphTask-19c298e227e044aa6-54')"
      width="500px"
      modal
      append-to-body
      :close-on-click-modal="false"
      :show-close="true"
      ><div class="import-result-content">
        <el-alert
          v-if="importResults.validItems.length > 0"
          type="success"
          :title="`${$t('tasks-WordGraphTask-19c298e227e044aa6-55')}${importResults.validItems.length}${$t('tasks-WordGraphTask-19c298e227e044aa6-56')}`"
          :closable="false"
          show-icon
        />
        <el-alert
          v-if="importResults.invalidItems.length > 0"
          type="warning"
          :title="`${importResults.invalidItems.length}${$t('tasks-WordGraphTask-19c298e227e044aa6-57')}`"
          :closable="false"
          show-icon
          style="margin-top: 10px"
        />
        <div
          v-if="importResults.invalidItems.length > 0"
          class="invalid-keywords"
        >
          <p>{{ $t("tasks-WordGraphTask-19c298e227e044aa6-58") }}</p>
          <div class="keywords-list">
            <el-tag
              v-for="(item, index) in importResults.invalidItems.slice(0, 20)"
              :key="index"
              type="danger"
              class="keyword-tag"
              style="margin: 5px"
              >{{ item }}</el-tag
            >
            <el-tag v-if="importResults.invalidItems.length > 20" type="info"
              >{{ $t("tasks-WordGraphTask-19c298e227e044aa6-59") }}
              {{ importResults.invalidItems.length - 20 }}
              {{ $t("tasks-WordGraphTask-19c298e227e044aa6-60") }}</el-tag
            >
          </div>
        </div>
      </div>
      <template #footer
        ><span class="dialog-footer"
          ><el-button @click="importResultDialogVisible = false">{{
            $t("tasks-WordGraphTask-19c298e227e044aa6-61")
          }}</el-button></span
        ></template
      ></el-dialog
    >
    <!-- 添加任务概览对话框 -->
    <el-dialog
      v-model="taskOverviewDialogVisible"
      :title="$t('tasks-WordGraphTask-19c298e227e044aa6-62')"
      width="600px"
      :close-on-click-modal="false"
      ><div class="task-overview">
        <el-descriptions
          :title="$t('tasks-WordGraphTask-19c298e227e044aa6-63')"
          :column="1"
          border
          ><el-descriptions-item
            :label="$t('tasks-WordGraphTask-19c298e227e044aa6-64')"
            ><el-tag>{{
              $t("tasks-WordGraphTask-19c298e227e044aa6-65")
            }}</el-tag></el-descriptions-item
          >
          <el-descriptions-item
            :label="$t('tasks-WordGraphTask-19c298e227e044aa6-66')"
            ><div class="overview-keywords">
              <span class="overview-count"
                >{{ $t("tasks-WordGraphTask-19c298e227e044aa6-67") }}
                {{ formData.keywords.length }}
                {{ $t("tasks-WordGraphTask-19c298e227e044aa6-68") }}</span
              >
              <div class="overview-tags">
                <el-tag
                  v-for="(keyword, index) in formData.keywords.slice(0, 10)"
                  :key="index"
                  size="small"
                  class="overview-tag"
                  >{{ keyword.value }}</el-tag
                >
                <el-tag
                  v-if="formData.keywords.length > 10"
                  type="info"
                  size="small"
                  >{{ $t("tasks-WordGraphTask-19c298e227e044aa6-69") }}
                  {{ formData.keywords.length - 10 }}
                  {{ $t("tasks-WordGraphTask-19c298e227e044aa6-70") }}</el-tag
                >
              </div>
            </div></el-descriptions-item
          >
          <el-descriptions-item
            :label="$t('tasks-WordGraphTask-19c298e227e044aa6-71')"
            >已选择 {{ selectedWeeks.length }} 周
            <span v-if="selectedWeeks.length > 0" style="color: #909399; margin-left: 8px;">
              ({{ formatDisplayDate(selectedWeeks[0]) }} 至 {{ formatDisplayDate(selectedWeeks[selectedWeeks.length - 1]) }})
            </span></el-descriptions-item
          >
          <el-descriptions-item
            :label="$t('tasks-WordGraphTask-19c298e227e044aa6-74')"
            >{{
              formData.output_format === "csv"
                ? $t("tasks-WordGraphTask-19c298e227e044aa6-75")
                : $t("tasks-WordGraphTask-19c298e227e044aa6-76")
            }}</el-descriptions-item
          >
          <el-descriptions-item
            :label="$t('tasks-WordGraphTask-19c298e227e044aa6-77')"
            ><div>
              {{ $t("tasks-WordGraphTask-19c298e227e044aa6-81") }}
              {{ formData.priority }}
            </div>
            <div v-if="formData.resume">
              {{ $t("tasks-WordGraphTask-19c298e227e044aa6-82") }}
              {{ formData.task_id }}
            </div></el-descriptions-item
          ></el-descriptions
        >
      </div>
      <template #footer
        ><span class="dialog-footer"
          ><el-button @click="taskOverviewDialogVisible = false">{{
            $t("tasks-WordGraphTask-19c298e227e044aa6-83")
          }}</el-button>
          <el-button
            type="primary"
            @click="confirmSubmitTask"
            :loading="submitting"
            >{{ $t("tasks-WordGraphTask-19c298e227e044aa6-84") }}</el-button
          ></span
        ></template
      ></el-dialog
    >
  </div>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { ref, reactive, computed, onMounted } from "vue";
import { useWordGraphStore } from "@/store/wordGraph";

const { t } = useI18n();
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import {
  Plus,
  Delete,
  Upload,
  Check,
  Refresh,
  Warning,
  Close,
  Calendar,
} from "@element-plus/icons-vue";
import axios from "axios";
import * as XLSX from "xlsx";

const API_BASE_URL = "http://127.0.0.1:5001/api";
const router = useRouter();

// Pinia store 用于缓存时间范围
const timeRangeStore = useWordGraphStore();

// 表单数据
const formData = reactive({
  keywords: [] as { value: string }[],
  datelists: [] as string[],
  output_format: "csv",
  resume: false,
  task_id: "",
  priority: 5,
});

// 关键词输入
const batchKeywords = ref("");
const skipFirstLine = ref(true);

// 周日期选择
const selectedWeeks = ref<string[]>([]);
const loadingTimeRange = ref(false);
const timeRangeError = ref("");

// 可选的周日期列表
const weeklyDates = computed(() => timeRangeStore.getWeeklyDates);


// 状态
const submitting = ref(false);
const taskId = ref("");
const successDialogVisible = ref(false);

// ... (keep intermediate code) ...

// 日期范围限制
const TODAY = new Date();
TODAY.setHours(0, 0, 0, 0);
const ONE_YEAR_AGO = new Date(TODAY);
ONE_YEAR_AGO.setFullYear(TODAY.getFullYear() - 1);
ONE_YEAR_AGO.setDate(ONE_YEAR_AGO.getDate() - 7);

const todayStr = computed(() => {
  return `${TODAY.getFullYear()}-${String(TODAY.getMonth() + 1).padStart(2, "0")}-${String(TODAY.getDate()).padStart(2, "0")}`;
});

const oneYearAgoStr = computed(() => {
  return `${ONE_YEAR_AGO.getFullYear()}-${String(ONE_YEAR_AGO.getMonth() + 1).padStart(2, "0")}-${String(ONE_YEAR_AGO.getDate()).padStart(2, "0")}`;
});

// 禁用日期函数
const disabledDate = (date: Date) => {
  return (
    date.getTime() < ONE_YEAR_AGO.getTime() || date.getTime() > TODAY.getTime()
  );
};

// 导入结果
const importResultDialogVisible = ref(false);
const importResultTitle = ref("");
const importResults = reactive({
  validItems: [] as string[],
  invalidItems: [] as string[],
});

// 获取时间范围
const fetchTimeRange = async () => {
  loadingTimeRange.value = true;
  timeRangeError.value = "";
  try {
    await timeRangeStore.fetchTimeRange();
  } catch (error: any) {
    timeRangeError.value = error.message || "获取时间范围失败";
  } finally {
    loadingTimeRange.value = false;
  }
};

// 全选所有周
const selectAllWeeks = () => {
  selectedWeeks.value = weeklyDates.value.map(d => d.value);
};

// 清空选中的周
const clearWeeks = () => {
  selectedWeeks.value = [];
};

// 组件挂载时获取时间范围
onMounted(() => {
  fetchTimeRange();
});



// 任务概览对话框
const taskOverviewDialogVisible = ref(false);

// 关键词检查结果
const keywordCheckResults = reactive<Record<string, boolean | null>>({});
const checkingKeywords = ref(false);
const checkResultDialogVisible = ref(false);
const checkResults = reactive({
  existsCount: 0,
  notExistsCount: 0,
  notExistsKeywords: [] as string[],
});

// 优先级标记
const priorityMarks = {
  1: t("tasks-WordGraphTask-19c298e227e044aa6-85"),
  5: t("tasks-WordGraphTask-19c298e227e044aa6-86"),
  10: t("tasks-WordGraphTask-19c298e227e044aa6-87"),
};

// 计算是否可以提交
const canSubmit = computed(() => {
  // 必须有关键词
  if (formData.keywords.length === 0) return false;

  // 必须有选中的周日期
  if (selectedWeeks.value.length === 0) return false;

  // 恢复任务时需要任务ID
  if (formData.resume && !formData.task_id.trim()) return false;

  return true;
});

// 格式化日期显示
const formatDisplayDate = (dateStr: string) => {
  if (!dateStr || dateStr.length !== 8) return dateStr;
  return `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}`;
};

// 移除旧的日期处理函数
// const handleDateChange...
// const addSelectedDate...
// const removeDate...
// const clearDates...

// 检查关键词
const checkKeywords = async () => {
  if (formData.keywords.length === 0) {
    ElMessage.warning(
      t("tasks-WordGraphTask-19c298e227e044aa6-88"),
    );
    return;
  }

  checkingKeywords.value = true;

  try {
    const keywords = formData.keywords.map((k) => k.value);
    const response = await axios.post(`${API_BASE_URL}/word-check/check`, {
      words: keywords,
    });

    if (response.data.code === 10000) {
      const results = response.data.data.results;

      // 更新检查结果
      for (const word in results) {
        keywordCheckResults[word] = results[word].exists;
      }

      // 统计结果
      checkResults.existsCount = Object.values(results).filter(
        (r) => r.exists,
      ).length;
      checkResults.notExistsCount = Object.values(results).filter(
        (r) => !r.exists,
      ).length;

      // 获取不存在的关键词列表
      checkResults.notExistsKeywords = [];
      for (const word in results) {
        if (!results[word].exists) {
          checkResults.notExistsKeywords.push(word);
        }
      }

      // 显示检查结果对话框
      checkResultDialogVisible.value = true;
    } else {
      ElMessage.error(
        `${t("tasks-WordGraphTask-19c298e227e044aa6-89")}${response.data.msg}`,
      );
    }
  } catch (error) {
    console.error(
      t("tasks-WordGraphTask-19c298e227e044aa6-90"),
      error,
    );
    ElMessage.error(t("tasks-WordGraphTask-19c298e227e044aa6-91"));
  } finally {
    checkingKeywords.value = false;
  }
};

// 添加关键词时重置检查结果
const addBatchKeywords = () => {
  if (!batchKeywords.value.trim()) return;

  const lines = batchKeywords.value.split("\n").filter((line) => line.trim());
  let addedCount = 0;
  let duplicateCount = 0;

  lines.forEach((line) => {
    const keyword = line.trim();
    if (keyword && !formData.keywords.some((k) => k.value === keyword)) {
      formData.keywords.push({ value: keyword });
      keywordCheckResults[keyword] = null; // 重置检查结果
      addedCount++;
    } else if (keyword) {
      duplicateCount++;
    }
  });

  if (addedCount > 0) {
    ElMessage.success(
      `${t("tasks-WordGraphTask-19c298e227e044aa6-92")}${addedCount}${t("tasks-WordGraphTask-19c298e227e044aa6-93")}`,
    );
  }

  if (duplicateCount > 0) {
    ElMessage.warning(
      `${duplicateCount}${t("tasks-WordGraphTask-19c298e227e044aa6-94")}`,
    );
  }

  batchKeywords.value = "";
};

// 移除关键词时同时移除检查结果
const removeKeyword = (index: number) => {
  const keyword = formData.keywords[index].value;
  delete keywordCheckResults[keyword];
  formData.keywords.splice(index, 1);
};

// 清空关键词时同时清空检查结果
const clearKeywords = () => {
  ElMessageBox.confirm(
    t("tasks-WordGraphTask-19c298e227e044aa6-95"),
    t("tasks-WordGraphTask-19c298e227e044aa6-96"),
    {
      confirmButtonText: t(
        "tasks-WordGraphTask-19c298e227e044aa6-97",
      ),
      cancelButtonText: t(
        "tasks-WordGraphTask-19c298e227e044aa6-98",
      ),
      type: "warning",
    },
  )
    .then(() => {
      formData.keywords = [];
      Object.keys(keywordCheckResults).forEach((key) => {
        delete keywordCheckResults[key];
      });
    })
    .catch(() => {});
};

// 处理关键词文件上传
const handleKeywordsFileChange = async (file: any) => {
  if (!file) return;

  try {
    const keywords = await readFileContent(file.raw, skipFirstLine.value);

    if (keywords.length === 0) {
      ElMessage.warning(
        t("tasks-WordGraphTask-19c298e227e044aa6-99"),
      );
      return;
    }

    // 过滤已存在的关键词
    const validKeywords = [];
    const invalidKeywords = [];

    keywords.forEach((keyword) => {
      const trimmedKeyword = keyword.trim();
      if (
        trimmedKeyword &&
        !formData.keywords.some((k) => k.value === trimmedKeyword)
      ) {
        validKeywords.push(trimmedKeyword);
      } else if (trimmedKeyword) {
        invalidKeywords.push(trimmedKeyword);
      }
    });

    // 添加有效关键词
    validKeywords.forEach((keyword) => {
      formData.keywords.push({ value: keyword });
      keywordCheckResults[keyword] = null; // 重置检查结果
    });

    // 显示导入结果
    importResults.validItems = validKeywords;
    importResults.invalidItems = invalidKeywords;
    importResultDialogVisible.value = true;
  } catch (error) {
    console.error(
      t("tasks-WordGraphTask-19c298e227e044aa6-100"),
      error,
    );
    ElMessage.error(t("tasks-WordGraphTask-19c298e227e044aa6-101"));
  }
};

// 读取文件内容
const readFileContent = (
  file: File,
  skipFirstLine: boolean,
): Promise<string[]> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();

    reader.onload = (e) => {
      try {
        const result = e.target?.result;
        if (!result) {
          resolve([]);
          return;
        }

        let lines: string[] = [];

        // 根据文件类型处理
        if (file.name.endsWith(".xlsx")) {
          const data = new Uint8Array(result as ArrayBuffer);
          const workbook = XLSX.read(data, { type: "array" });
          const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
          const jsonData = XLSX.utils.sheet_to_json(firstSheet, {
            header: 1,
          }) as any[][];

          lines = jsonData.map((row) => row[0]?.toString() || "");
        } else if (file.name.endsWith(".csv") || file.name.endsWith(".txt")) {
          lines = (result as string).split(/\r\n|\n/);
        }

        // 跳过第一行
        if (skipFirstLine && lines.length > 0) {
          lines = lines.slice(1);
        }

        // 过滤空行
        lines = lines.filter((line) => line.trim() !== "");

        resolve(lines);
      } catch (error) {
        reject(error);
      }
    };

    reader.onerror = () => {
      reject(
        new Error(t("tasks-WordGraphTask-19c298e227e044aa6-102")),
      );
    };

    if (file.name.endsWith(".xlsx")) {
      reader.readAsArrayBuffer(file);
    } else {
      reader.readAsText(file);
    }
  });
};

// 提交任务
const submitTask = async () => {
  submitting.value = true;

  try {
    // 准备参数
    const params: any = {
      taskType: "word_graph",
      parameters: {
        keywords: formData.keywords.map((k) => k.value),
        datelists: selectedWeeks.value,  // 发送选中的周日期数组
        output_format: formData.output_format,
        resume: formData.resume,
      },
      priority: formData.priority,
    };

    // 添加任务ID（如果是恢复任务）
    if (formData.resume && formData.task_id) {
      params.parameters.task_id = formData.task_id;
    }

    const response = await axios.post(`${API_BASE_URL}/task/create`, params);

    if (response.data.code === 10000) {
      taskId.value = response.data.data.taskId;
      successDialogVisible.value = true;
    } else {
      ElMessage.error(
        `${t("tasks-WordGraphTask-19c298e227e044aa6-103")}${response.data.msg}`,
      );
    }
  } catch (error) {
    ElMessage.error(t("tasks-WordGraphTask-19c298e227e044aa6-104"));
    console.error(
      t("tasks-WordGraphTask-19c298e227e044aa6-105"),
      error,
    );
  } finally {
    submitting.value = false;
  }
};

// 重置表单
const resetForm = () => {
  formData.keywords = [];
  selectedWeeks.value = [];
  batchKeywords.value = "";
  formData.output_format = "csv";
  formData.resume = false;
  formData.task_id = "";
  formData.priority = 5;
};

// 前往任务列表页面
const goToTaskList = () => {
  router.push({ path: "/data-collection", query: { tab: "task_list" } });
  successDialogVisible.value = false;
};

// 显示任务概览
const showTaskOverview = () => {
  taskOverviewDialogVisible.value = true;
};

// 确认提交任务
const confirmSubmitTask = async () => {
  taskOverviewDialogVisible.value = false;
  submitTask();
};

// 计算是否有不存在的关键词
const hasInvalidKeywords = computed(() => {
  return Object.values(keywordCheckResults).some((result) => result === false);
});

// 从对话框中清除不存在的关键词
const removeInvalidKeywordsFromDialog = () => {
  const invalidKeywords: string[] = [];

  // 找出不存在的关键词
  formData.keywords = formData.keywords.filter((keyword) => {
    const exists = keywordCheckResults[keyword.value] !== false;
    if (!exists) {
      invalidKeywords.push(keyword.value);
      delete keywordCheckResults[keyword.value];
    }
    return exists;
  });

  if (invalidKeywords.length > 0) {
    ElMessage.success(
      `${t("tasks-WordGraphTask-19c298e227e044aa6-106")}${invalidKeywords.length}${t("tasks-WordGraphTask-19c298e227e044aa6-107")}`,
    );
    checkResultDialogVisible.value = false;
  }
};

// 清除不存在的关键词（通过按钮直接触发）
const removeInvalidKeywords = () => {
  if (!hasInvalidKeywords.value) return;

  ElMessageBox.confirm(
    t("tasks-WordGraphTask-19c298e227e044aa6-108"),
    t("tasks-WordGraphTask-19c298e227e044aa6-109"),
    {
      confirmButtonText: t(
        "tasks-WordGraphTask-19c298e227e044aa6-110",
      ),
      cancelButtonText: t(
        "tasks-WordGraphTask-19c298e227e044aa6-111",
      ),
      type: "warning",
    },
  )
    .then(() => {
      const invalidKeywords: string[] = [];

      // 找出不存在的关键词
      formData.keywords = formData.keywords.filter((keyword) => {
        const exists = keywordCheckResults[keyword.value] !== false;
        if (!exists) {
          invalidKeywords.push(keyword.value);
          delete keywordCheckResults[keyword.value];
        }
        return exists;
      });

      if (invalidKeywords.length > 0) {
        ElMessage.success(
          `${t("tasks-WordGraphTask-19c298e227e044aa6-112")}${invalidKeywords.length}${t("tasks-WordGraphTask-19c298e227e044aa6-113")}`,
        );
      }
    })
    .catch(() => {});
};
</script>

<style scoped>
.task-container {
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
}

.task-header {
  margin-bottom: 20px;
  text-align: center;
}

.task-header h2 {
  font-size: 28px;
  color: #4f46e5;
  margin-bottom: 10px;
}

.task-desc {
  color: #606266;
  font-size: 14px;
}

.task-card {
  margin-bottom: 20px;
  border-radius: 8px;
  background-color: var(--color-bg-surface);
  border: 1px solid var(--color-border);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
}

.task-form {
  padding: 10px 20px;
}

.keywords-actions,
.date-actions {
  display: flex;
  align-items: center;
  margin-top: 10px;
  gap: 10px;
}

.keywords-tip {
  color: #909399;
  font-size: 12px;
}

.date-selection-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
}

.date-selection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 24px;
}

.selection-count {
  font-size: 13px;
  color: #606266;
}

.selection-actions {
  display: flex;
  gap: 12px;
}

.date-range-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #909399;
  background-color: var(--color-bg-subtle);
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px dashed var(--color-border);
}

.date-range-info .el-icon {
  font-size: 16px;
  color: #4f46e5;
}

.keywords-tags-container,
.date-tags-container {
  width: 100%;
}

.keywords-tags,
.date-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
  max-height: 120px;
  overflow-y: auto;
  padding: 5px;
  border: 1px solid var(--color-border);
  background-color: var(--color-bg-subtle);
  border-radius: 4px;
}

.keyword-tag,
.date-tag {
  margin-bottom: 4px;
}

.keywords-count,
.date-count {
  font-size: 14px;
  color: #909399;
}

.upload-area {
  display: flex;
  align-items: center;
}

.upload-tip {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}

.date-selection {
  display: flex;
  align-items: center;
  gap: 10px;
}

.success-content {
  text-align: center;
}

.file-import-options {
  margin-top: 8px;
  display: flex;
  align-items: center;
}

.import-result-content {
  padding: 10px;
}

.invalid-items {
  margin-top: 15px;
  padding: 10px;
  background-color: var(--color-bg-subtle);
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
}

.invalid-items p {
  font-weight: bold;
  margin-bottom: 5px;
}

.invalid-items ul {
  margin: 0;
  padding-left: 20px;
}

.invalid-items li {
  margin-bottom: 3px;
}

.keyword-warning {
  margin-left: 4px;
  color: #f56c6c;
}

.check-result-content {
  padding: 10px;
}

.invalid-keywords {
  margin-top: 15px;
  padding: 10px;
  background-color: var(--color-bg-subtle);
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
}

.invalid-keywords p {
  font-weight: bold;
  margin-bottom: 5px;
}

.keywords-list {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.keyword-tag {
  margin: 5px;
}

.task-overview {
  padding: 20px;
}

.overview-keywords,
.overview-dates {
  display: flex;
  align-items: center;
  gap: 10px;
}

.overview-count {
  font-weight: bold;
  color: #4f46e5;
}

.overview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  max-height: 100px;
  overflow-y: auto;
}

.overview-tag {
  background-color: #e6f7ff;
  color: #1890ff;
  border: 1px solid #91d5ff;
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 12px;
}
</style>
