<template>
  <div class="task-container">
    <div class="task-header">
      <h2>{{ $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-1") }}</h2>
      <div class="task-desc">
        {{ $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-2") }}
      </div>
    </div>
    <el-card class="task-card"
      ><template #header
        ><div class="card-header">
          <span>{{
            $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-3")
          }}</span>
        </div></template
      >
      <el-form :model="formData" label-width="120px" class="task-form"
        ><!-- 关键词设置 -->
        <el-divider content-position="left">{{
          $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-4")
        }}</el-divider>
        <el-form-item
          :label="$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-5')"
          ><el-input
            v-model="batchKeywords"
            type="textarea"
            :rows="4"
            :placeholder="
              $t('tasks-DemographicAttributesTask-19c298e1c74d5b997-6')
            "
          />
          <div class="keywords-actions">
            <el-button
              type="primary"
              @click="addBatchKeywords"
              :disabled="!batchKeywords.trim()"
              ><el-icon><Plus /></el-icon>
              {{
                $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-7")
              }}</el-button
            >
            <span class="keywords-tip">{{
              $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-8")
            }}</span>
          </div></el-form-item
        >
        <el-form-item
          :label="$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-9')"
          ><el-upload
            class="upload-area"
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleKeywordsFileChange"
            accept=".xlsx,.csv,.txt"
            ><el-button type="primary"
              ><el-icon><Upload /></el-icon>
              {{
                $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-10")
              }}</el-button
            >
            <div class="upload-tip">
              {{ $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-11") }}
            </div></el-upload
          >
          <div class="file-import-options">
            <el-checkbox v-model="skipFirstLine">{{
              $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-12")
            }}</el-checkbox>
          </div></el-form-item
        >
        <el-form-item
          :label="$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-13')"
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
                  :content="
                    $t('tasks-DemographicAttributesTask-19c298e1c74d5b997-14')
                  "
                  placement="top"
                  ><el-icon class="keyword-warning"
                    ><Warning /></el-icon></el-tooltip
              ></el-tag>
            </div>
            <div class="keywords-actions">
              <el-button type="danger" plain size="small" @click="clearKeywords"
                ><el-icon><Delete /></el-icon>
                {{
                  $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-15")
                }}</el-button
              >
              <el-button
                type="primary"
                size="small"
                @click="checkKeywords"
                :loading="checkingKeywords"
                ><el-icon><Check /></el-icon>
                {{
                  $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-16")
                }}</el-button
              >
              <el-button
                type="warning"
                plain
                size="small"
                @click="removeInvalidKeywords"
                :disabled="!hasInvalidKeywords"
                ><el-icon><Close /></el-icon>
                {{
                  $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-17")
                }}</el-button
              >
              <div class="keywords-count">
                {{
                  $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-18")
                }}
                {{ formData.keywords.length }}
                {{ $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-19") }}
              </div>
            </div>
          </div></el-form-item
        >
        <!-- 输出设置 -->
        <el-divider content-position="left">{{
          $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-20")
        }}</el-divider>

        <el-form-item
          :label="$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-24')">
          <el-select v-model="formData.output_format" style="width: 200px">
            <el-option label="CSV (.csv)" value="csv" />
            <el-option label="Excel (.xlsx)" value="excel" />
            <el-option label="JSON (.json)" value="json" />
            <el-option label="Stata (.dta)" value="dta" />
            <el-option label="Parquet (.parquet)" value="parquet" />
            <el-option label="SQLite (.sqlite)" value="sql" />
          </el-select>
        </el-form-item>
        <el-form-item label="输出目录">
          <DirPicker
            v-model="formData.output_dir"
            placeholder="留空则使用系统默认输出目录"
            hint="自定义此任务的输出目录，留空使用全局配置中的默认目录"
          />
        </el-form-item>
        <el-form-item label="自定义文件名">
          <el-input v-model="formData.output_name" placeholder="留空则使用默认文件名" clearable />
          <div style="font-size: 12px; color: #909399; margin-top: 4px;">设置输出文件名前缀（如 "my_data"），留空则使用默认格式</div>
        </el-form-item>
        <el-form-item
          :label="$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-27')"
          ><el-input-number
            v-model="formData.batch_size"
            :min="1"
            :max="50"
            controls-position="right"
          />
          <div class="input-tip">
            {{ $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-28") }}
          </div></el-form-item
        >
        <!-- 任务设置 -->
        <el-divider content-position="left">{{
          $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-29")
        }}</el-divider>
        <el-form-item
          :label="$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-30')"
          ><el-switch
            v-model="formData.resume"
            :active-text="
              $t('tasks-DemographicAttributesTask-19c298e1c74d5b997-31')
            "
            :inactive-text="
              $t('tasks-DemographicAttributesTask-19c298e1c74d5b997-32')
            "
        /></el-form-item>
        <el-form-item
          :label="$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-33')"
          v-if="formData.resume"
          ><el-input
            v-model="formData.task_id"
            :placeholder="
              $t('tasks-DemographicAttributesTask-19c298e1c74d5b997-34')
            "
        /></el-form-item>
        <el-form-item
          :label="$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-35')"
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
            {{
              $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-36")
            }}</el-button
          >
          <el-button @click="resetForm" size="large"
            ><el-icon><Refresh /></el-icon>
            {{
              $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-37")
            }}</el-button
          ></el-form-item
        ></el-form
      ></el-card
    >
    <el-dialog
      v-model="successDialogVisible"
      :title="$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-38')"
      width="500px"
      ><div class="success-content">
        <el-result
          icon="success"
          :title="$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-39')"
          :sub-title="`${$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-40')}${taskId}`"
          ><template #extra
            ><el-button type="primary" @click="goToTaskList">{{
              $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-41")
            }}</el-button>
            <el-button @click="successDialogVisible = false">{{
              $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-42")
            }}</el-button></template
          ></el-result
        >
      </div></el-dialog
    >
    <!-- 关键词检查结果对话框 -->
    <el-dialog
      v-model="checkResultDialogVisible"
      :title="$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-43')"
      width="500px"
      modal
      append-to-body
      :close-on-click-modal="false"
      :show-close="true"
      ><div class="check-result-content">
        <el-alert
          v-if="checkResults.existsCount > 0"
          type="success"
          :title="`${checkResults.existsCount}${$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-44')}`"
          :closable="false"
          show-icon
        />
        <el-alert
          v-if="checkResults.notExistsCount > 0"
          type="warning"
          :title="`${checkResults.notExistsCount}${$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-45')}`"
          :closable="false"
          show-icon
          style="margin-top: 10px"
        />
        <div v-if="checkResults.notExistsCount > 0" class="invalid-keywords">
          <p>
            {{ $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-46") }}
          </p>
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
            $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-47")
          }}</el-button>
          <el-button
            type="warning"
            @click="removeInvalidKeywordsFromDialog"
            :disabled="checkResults.notExistsCount === 0"
            >{{
              $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-48")
            }}</el-button
          ></span
        ></template
      ></el-dialog
    >
    <!-- 导入结果对话框 -->
    <el-dialog
      v-model="importResultDialogVisible"
      :title="importResultTitle"
      width="500px"
      modal
      append-to-body
      :close-on-click-modal="false"
      :show-close="true"
      ><div class="import-result-content">
        <el-alert
          v-if="importResults.validItems.length > 0"
          type="success"
          :title="`${$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-49')}${importResults.validItems.length}${$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-50')}`"
          :closable="false"
          show-icon
        />
        <el-alert
          v-if="importResults.invalidItems.length > 0"
          type="warning"
          :title="`${importResults.invalidItems.length}${$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-51')}`"
          :closable="false"
          show-icon
          style="margin-top: 10px"
        />
        <div
          v-if="importResults.invalidItems.length > 0"
          class="invalid-keywords"
        >
          <p>
            {{ $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-52") }}
          </p>
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
              >{{ $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-53") }}
              {{ importResults.invalidItems.length - 20 }}
              {{
                $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-54")
              }}</el-tag
            >
          </div>
        </div>
      </div>
      <template #footer
        ><span class="dialog-footer"
          ><el-button @click="importResultDialogVisible = false">{{
            $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-55")
          }}</el-button></span
        ></template
      ></el-dialog
    >
    <!-- 添加任务概览对话框 -->
    <el-dialog
      v-model="taskOverviewDialogVisible"
      :title="$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-56')"
      width="600px"
      :close-on-click-modal="false"
      ><div class="task-overview">
        <el-descriptions
          :title="$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-57')"
          :column="1"
          border
          ><el-descriptions-item
            :label="$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-58')"
            ><el-tag>{{
              $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-59")
            }}</el-tag></el-descriptions-item
          >
          <el-descriptions-item
            :label="$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-60')"
            ><div class="overview-keywords">
              <span class="overview-count"
                >{{
                  $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-61")
                }}
                {{ formData.keywords.length }}
                {{
                  $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-62")
                }}</span
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
                  >{{
                    $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-63")
                  }}
                  {{ formData.keywords.length - 10 }}
                  {{
                    $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-64")
                  }}</el-tag
                >
              </div>
            </div></el-descriptions-item
          >
          <el-descriptions-item
            :label="$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-65')"
            ><div>
              {{ $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-66") }}
              {{
                formData.output_format === "csv"
                  ? $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-67")
                  : $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-68")
              }}
            </div>
            <div>
              {{ $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-69") }}
              {{ formData.batch_size }}
            </div></el-descriptions-item
          >
          <el-descriptions-item
            :label="$t('tasks-DemographicAttributesTask-19c298e1c74d5b997-70')"
            ><div>
              {{ $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-74") }}
              {{ formData.priority }}
            </div>
            <div v-if="formData.resume">
              {{ $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-75") }}
              {{ formData.task_id }}
            </div></el-descriptions-item
          ></el-descriptions
        >
      </div>
      <template #footer
        ><span class="dialog-footer"
          ><el-button @click="taskOverviewDialogVisible = false">{{
            $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-76")
          }}</el-button>
          <el-button
            type="primary"
            @click="confirmSubmitTask"
            :loading="submitting"
            >{{
              $t("tasks-DemographicAttributesTask-19c298e1c74d5b997-77")
            }}</el-button
          ></span
        ></template
      ></el-dialog
    >
  </div>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { ref, reactive, computed } from "vue";

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
} from "@element-plus/icons-vue";
import axios from "axios";
import DirPicker from "../DirPicker.vue";
import * as XLSX from "xlsx";

const API_BASE_URL = "http://127.0.0.1:5001/api";
const router = useRouter();

// 表单数据
const formData = reactive({
  keywords: [] as { value: string }[],
  output_format: "csv",
  output_dir: "",
  output_name: "",
  batch_size: 5,
  resume: false,
  task_id: "",
  priority: 5,
});

// 关键词输入
const batchKeywords = ref("");
const skipFirstLine = ref(true);

// 状态
const submitting = ref(false);
const taskId = ref("");
const successDialogVisible = ref(false);

// 导入结果
const importResultDialogVisible = ref(false);
const importResultTitle = ref("");
const importResults = reactive({
  validItems: [] as string[],
  invalidItems: [] as string[],
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
  1: t("tasks-DemographicAttributesTask-19c298e1c74d5b997-78"),
  5: t("tasks-DemographicAttributesTask-19c298e1c74d5b997-79"),
  10: t("tasks-DemographicAttributesTask-19c298e1c74d5b997-80"),
};

// 计算是否可以提交
const canSubmit = computed(() => {
  // 必须有关键词
  if (formData.keywords.length === 0) return false;

  // 恢复任务时需要任务ID
  if (formData.resume && !formData.task_id.trim()) return false;

  return true;
});

// 计算是否有不存在的关键词
const hasInvalidKeywords = computed(() => {
  return Object.values(keywordCheckResults).some((result) => result === false);
});

// 检查关键词
const checkKeywords = async () => {
  if (formData.keywords.length === 0) {
    ElMessage.warning(
      t("tasks-DemographicAttributesTask-19c298e1c74d5b997-81"),
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
        `${t("tasks-DemographicAttributesTask-19c298e1c74d5b997-82")}${response.data.msg}`,
      );
    }
  } catch (error) {
    console.error(
      t("tasks-DemographicAttributesTask-19c298e1c74d5b997-83"),
      error,
    );
    ElMessage.error(
      t("tasks-DemographicAttributesTask-19c298e1c74d5b997-84"),
    );
  } finally {
    checkingKeywords.value = false;
  }
};

// 批量添加关键词
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
      `${t("tasks-DemographicAttributesTask-19c298e1c74d5b997-85")}${addedCount}${t("tasks-DemographicAttributesTask-19c298e1c74d5b997-86")}`,
    );
  }

  if (duplicateCount > 0) {
    ElMessage.warning(
      `${duplicateCount}${t("tasks-DemographicAttributesTask-19c298e1c74d5b997-87")}`,
    );
  }

  batchKeywords.value = "";
};

// 移除关键词
const removeKeyword = (index: number) => {
  const keyword = formData.keywords[index].value;
  delete keywordCheckResults[keyword];
  formData.keywords.splice(index, 1);
};

// 清空关键词
const clearKeywords = () => {
  ElMessageBox.confirm(
    t("tasks-DemographicAttributesTask-19c298e1c74d5b997-88"),
    t("tasks-DemographicAttributesTask-19c298e1c74d5b997-89"),
    {
      confirmButtonText: t(
        "tasks-DemographicAttributesTask-19c298e1c74d5b997-90",
      ),
      cancelButtonText: t(
        "tasks-DemographicAttributesTask-19c298e1c74d5b997-91",
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

// 清除不存在的关键词
const removeInvalidKeywords = () => {
  if (!hasInvalidKeywords.value) return;

  ElMessageBox.confirm(
    t("tasks-DemographicAttributesTask-19c298e1c74d5b997-92"),
    t("tasks-DemographicAttributesTask-19c298e1c74d5b997-93"),
    {
      confirmButtonText: t(
        "tasks-DemographicAttributesTask-19c298e1c74d5b997-94",
      ),
      cancelButtonText: t(
        "tasks-DemographicAttributesTask-19c298e1c74d5b997-95",
      ),
      type: "warning",
    },
  )
    .then(() => {
      const invalidKeywords = [];

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
          `${t("tasks-DemographicAttributesTask-19c298e1c74d5b997-96")}${invalidKeywords.length}${t("tasks-DemographicAttributesTask-19c298e1c74d5b997-97")}`,
        );
      }
    })
    .catch(() => {});
};

// 从对话框中清除不存在的关键词
const removeInvalidKeywordsFromDialog = () => {
  const invalidKeywords = [];

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
      `${t("tasks-DemographicAttributesTask-19c298e1c74d5b997-98")}${invalidKeywords.length}${t("tasks-DemographicAttributesTask-19c298e1c74d5b997-99")}`,
    );
    checkResultDialogVisible.value = false;
  }
};

// 处理关键词文件上传
const handleKeywordsFileChange = async (file: any) => {
  if (!file) return;

  try {
    const keywords = await readFileContent(file.raw, skipFirstLine.value);

    if (keywords.length === 0) {
      ElMessage.warning(
        t("tasks-DemographicAttributesTask-19c298e1c74d5b997-100"),
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
    importResultTitle.value = t(
      "tasks-DemographicAttributesTask-19c298e1c74d5b997-101",
    );
    importResultDialogVisible.value = true;
  } catch (error) {
    console.error(
      t("tasks-DemographicAttributesTask-19c298e1c74d5b997-102"),
      error,
    );
    ElMessage.error(
      t("tasks-DemographicAttributesTask-19c298e1c74d5b997-103"),
    );
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
        new Error(
          t(
            "tasks-DemographicAttributesTask-19c298e1c74d5b997-104",
          ),
        ),
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
      taskType: "demographic_attributes",
      parameters: {
        keywords: formData.keywords.map((k) => k.value),
        output_format: formData.output_format,
        ...(formData.output_dir ? { output_dir: formData.output_dir } : {}),
        ...(formData.output_name ? { output_name: formData.output_name } : {}),
        batch_size: formData.batch_size,
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
        `${t("tasks-DemographicAttributesTask-19c298e1c74d5b997-105")}${response.data.msg}`,
      );
    }
  } catch (error) {
    ElMessage.error(
      t("tasks-DemographicAttributesTask-19c298e1c74d5b997-106"),
    );
    console.error(
      t("tasks-DemographicAttributesTask-19c298e1c74d5b997-107"),
      error,
    );
  } finally {
    submitting.value = false;
  }
};

// 重置表单
const resetForm = () => {
  formData.keywords = [];
  formData.output_format = "csv";
  formData.batch_size = 10;
  formData.resume = false;
  formData.task_id = "";
  formData.priority = 5;
  batchKeywords.value = "";
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

.keywords-actions {
  display: flex;
  align-items: center;
  margin-top: 10px;
  gap: 10px;
}

.keywords-tip,
.input-tip {
  color: #909399;
  font-size: 12px;
}

.input-tip {
  margin-top: 5px;
  margin-left: 5px;
}

.keywords-tags-container {
  width: 100%;
}

.keywords-tags {
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

.keyword-tag {
  margin-bottom: 4px;
  display: flex;
  align-items: center;
}

.keyword-warning {
  margin-left: 4px;
  color: #f56c6c;
}

.keywords-count {
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

.overview-keywords {
  margin-top: 10px;
}

.overview-count {
  font-weight: bold;
  margin-right: 10px;
}

.overview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.overview-tag {
  background-color: #f0f9eb;
  color: #67c23a;
  border-color: #67c23a;
}
</style>
