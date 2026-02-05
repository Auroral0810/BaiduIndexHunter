<template>
  <div class="task-container">
    <div class="task-header">
      <h2>{{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-1") }}</h2>
      <div class="task-desc">
        {{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-2") }}
      </div>
    </div>
    <el-card class="task-card"
      ><template #header
        ><div class="card-header">
          <span>{{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-3") }}</span>
        </div></template
      >
      <el-form :model="formData" label-width="120px" class="task-form"
        ><!-- 关键词设置 -->
        <el-divider content-position="left">{{
          $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-4")
        }}</el-divider>
        <el-form-item :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-5')"
          ><el-input
            v-model="batchKeywords"
            type="textarea"
            :rows="4"
            :placeholder="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-6')"
          />
          <div class="keywords-actions">
            <el-button
              type="primary"
              @click="addBatchKeywords"
              :disabled="!batchKeywords.trim()"
              ><el-icon><Plus /></el-icon>
              {{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-7") }}</el-button
            >
            <span class="keywords-tip">{{
              $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-8")
            }}</span>
          </div></el-form-item
        >
        <el-form-item :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-9')"
          ><el-upload
            class="upload-area"
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleKeywordsFileChange"
            accept=".xlsx,.csv,.txt"
            ><el-button type="primary"
              ><el-icon><Upload /></el-icon>
              {{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-10") }}</el-button
            >
            <div class="upload-tip">
              {{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-11") }}
            </div></el-upload
          >
          <div class="file-import-options">
            <el-checkbox v-model="skipFirstLine">{{
              $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-12")
            }}</el-checkbox>
          </div></el-form-item
        >
        <el-form-item
          :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-13')"
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
                  :content="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-14')"
                  placement="top"
                  ><el-icon class="keyword-warning"
                    ><Warning /></el-icon></el-tooltip
              ></el-tag>
            </div>
            <div class="keywords-actions">
              <el-button type="danger" plain size="small" @click="clearKeywords"
                ><el-icon><Delete /></el-icon>
                {{
                  $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-15")
                }}</el-button
              >
              <el-button
                type="primary"
                size="small"
                @click="checkKeywords"
                :loading="checkingKeywords"
                ><el-icon><Check /></el-icon>
                {{
                  $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-16")
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
                  $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-17")
                }}</el-button
              >
              <div class="keywords-count">
                {{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-18") }}
                {{ formData.keywords.length }}
                {{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-19") }}
              </div>
            </div>
          </div></el-form-item
        >
        <!-- 城市设置 -->
        <el-divider content-position="left">{{
          $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-20")
        }}</el-divider>
        <el-form-item :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-21')"
          ><RegionCitySelector
            v-model="selectedCities"
            :api-base-url="API_BASE_URL"
            @change="handleCitiesChange"
        /></el-form-item>
        <el-form-item :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-22')"
          ><el-upload
            class="upload-area"
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleCitiesFileChange"
            accept=".xlsx,.csv,.txt"
            ><el-button type="primary"
              ><el-icon><Upload /></el-icon>
              {{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-23") }}</el-button
            >
            <div class="upload-tip">
              {{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-24") }}
            </div></el-upload
          >
          <div class="file-import-options">
            <el-checkbox v-model="skipFirstLineForCities">{{
              $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-25")
            }}</el-checkbox>
          </div></el-form-item
        >
        <!-- 时间设置 -->
        <el-divider content-position="left">{{
          $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-26")
        }}</el-divider>
        <el-form-item :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-27')"
          ><el-radio-group v-model="formData.kind"
            ><el-radio-button label="all">{{
              $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-28")
            }}</el-radio-button>
            <el-radio-button label="pc">PC</el-radio-button>
            <el-radio-button label="wise">{{
              $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-29")
            }}</el-radio-button></el-radio-group
          ></el-form-item
        >
        <el-form-item :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-30')"
          ><el-radio-group v-model="timeType"
            ><el-radio-button label="all">{{
              $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-31")
            }}</el-radio-button>
            <el-radio-button label="custom">{{
              $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-32")
            }}</el-radio-button>
            <el-radio-button label="preset">{{
              $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-33")
            }}</el-radio-button>
            <el-radio-button label="year">{{
              $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-34")
            }}</el-radio-button></el-radio-group
          ></el-form-item
        >
        <el-form-item
          :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-35')"
          v-if="timeType === 'custom'"
          ><el-date-picker
            v-model="dateRange"
            type="daterange"
            :range-separator="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-36')"
            :start-placeholder="
              $t('tasks-SearchIndexTask-19c298e21d4fb2dcd-37')
            "
            :end-placeholder="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-38')"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
            :disabled-date="disabledDate"
        /></el-form-item>
        <el-form-item
          :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-39')"
          v-if="timeType === 'preset'"
          ><el-select
            v-model="formData.days"
            :placeholder="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-40')"
            style="width: 100%"
            ><el-option
              :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-41')"
              :value="7" />
            <el-option
              :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-42')"
              :value="30" />
            <el-option
              :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-43')"
              :value="90" />
            <el-option
              :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-44')"
              :value="180" /></el-select
        ></el-form-item>
        <el-form-item
          :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-45')"
          v-if="timeType === 'year'"
          ><div class="year-range">
            <el-date-picker
              v-model="formData.yearRange[0]"
              type="year"
              :placeholder="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-46')"
              format="YYYY"
              value-format="YYYY"
              :disabled-date="disabledYearStart"
            />
            <span class="range-separator">{{
              $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-47")
            }}</span>
            <el-date-picker
              v-model="formData.yearRange[1]"
              type="year"
              :placeholder="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-48')"
              format="YYYY"
              value-format="YYYY"
              :disabled-date="disabledYearEnd"
            /></div
        ></el-form-item>
        <el-form-item
          v-if="timeType === 'all'"
          :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-49')"
          ><div class="time-info">
            <el-alert
              :title="`${$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-50')}${formData.kind === 'pc' ? $t('tasks-SearchIndexTask-19c298e21d4fb2dcd-52') : $t('tasks-SearchIndexTask-19c298e21d4fb2dcd-53')}${$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-51')}`"
              type="info"
              :closable="false"
              show-icon
            /></div
        ></el-form-item>
        <!-- 任务设置 -->
        <el-divider content-position="left">{{
          $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-54")
        }}</el-divider>
        <el-form-item :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-55')"
          ><el-switch
            v-model="formData.resume"
            :active-text="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-56')"
            :inactive-text="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-57')"
        /></el-form-item>
        <el-form-item
          :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-58')"
          v-if="formData.resume"
          ><el-input
            v-model="formData.taskId"
            :placeholder="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-59')"
        /></el-form-item>
        <el-form-item :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-60')"
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
            {{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-61") }}</el-button
          >
          <el-button @click="resetForm" size="large"
            ><el-icon><Refresh /></el-icon>
            {{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-62") }}</el-button
          ></el-form-item
        ></el-form
      ></el-card
    >
    <el-dialog
      v-model="successDialogVisible"
      :title="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-63')"
      width="500px"
      ><div class="success-content">
        <el-result
          icon="success"
          :title="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-64')"
          :sub-title="`${$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-65')}${taskId}`"
          ><template #extra
            ><el-button type="primary" @click="goToTaskList">{{
              $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-66")
            }}</el-button>
            <el-button @click="successDialogVisible = false">{{
              $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-67")
            }}</el-button></template
          ></el-result
        >
      </div></el-dialog
    >
    <!-- 关键词检查结果对话框 -->
    <el-dialog
      v-model="checkResultDialogVisible"
      :title="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-68')"
      width="500px"
      modal
      append-to-body
      :close-on-click-modal="false"
      :show-close="true"
      ><div class="check-result-content">
        <el-alert
          v-if="checkResults.existsCount > 0"
          type="success"
          :title="`${checkResults.existsCount}${$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-69')}`"
          :closable="false"
          show-icon
        />
        <el-alert
          v-if="checkResults.notExistsCount > 0"
          type="warning"
          :title="`${checkResults.notExistsCount}${$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-70')}`"
          :closable="false"
          show-icon
          style="margin-top: 10px"
        />
        <div v-if="checkResults.notExistsCount > 0" class="invalid-keywords">
          <p>{{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-71") }}</p>
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
            $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-72")
          }}</el-button>
          <el-button
            type="warning"
            @click="removeInvalidKeywordsFromDialog"
            :disabled="checkResults.notExistsCount === 0"
            >{{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-73") }}</el-button
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
          :title="`${$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-74')} ${importResults.validItems.length}${importResultTitle === $t('tasks-SearchIndexTask-19c298e21d4fb2dcd-75') ? $t('tasks-SearchIndexTask-19c298e21d4fb2dcd-76') : $t('tasks-SearchIndexTask-19c298e21d4fb2dcd-77')}`"
          :closable="false"
          show-icon
        />
        <el-alert
          v-if="importResults.invalidItems.length > 0"
          type="warning"
          :title="`${importResults.invalidItems.length} ${importResultTitle === $t('tasks-SearchIndexTask-19c298e21d4fb2dcd-79') ? $t('tasks-SearchIndexTask-19c298e21d4fb2dcd-80') : $t('tasks-SearchIndexTask-19c298e21d4fb2dcd-81')}${$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-78')}`"
          :closable="false"
          show-icon
          style="margin-top: 10px"
        />
        <div
          v-if="importResults.invalidItems.length > 0"
          class="invalid-keywords"
        >
          <p>
            {{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-82") }}
            {{
              importResultTitle ===
              $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-83")
                ? $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-84")
                : $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-85")
            }}
            ：
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
              >{{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-86") }}
              {{ importResults.invalidItems.length - 20 }}
              {{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-87") }}</el-tag
            >
          </div>
        </div>
      </div>
      <template #footer
        ><span class="dialog-footer"
          ><el-button @click="importResultDialogVisible = false">{{
            $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-88")
          }}</el-button></span
        ></template
      ></el-dialog
    >
    <!-- 添加任务概览对话框 -->
    <el-dialog
      v-model="taskOverviewDialogVisible"
      :title="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-89')"
      width="600px"
      :close-on-click-modal="false"
      ><div class="task-overview">
        <el-descriptions
          :title="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-90')"
          :column="1"
          border
          ><el-descriptions-item
            :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-91')"
            ><el-tag>{{
              $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-92")
            }}</el-tag></el-descriptions-item
          >
          <el-descriptions-item
            :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-93')"
            ><div class="overview-keywords">
              <span class="overview-count"
                >{{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-94") }}
                {{ formData.keywords.length }}
                {{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-95") }}</span
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
                  >{{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-96") }}
                  {{ formData.keywords.length - 10 }}
                  {{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-97") }}</el-tag
                >
              </div>
            </div></el-descriptions-item
          >
          <el-descriptions-item
            :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-98')"
            ><div class="overview-cities">
              <span class="overview-count"
                >{{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-99") }}
                {{ selectedCities.length }}
                {{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-100") }}</span
              >
              <div class="overview-tags">
                <el-tag
                  v-for="(code, index) in selectedCities.slice(0, 10)"
                  :key="index"
                  size="small"
                  class="overview-tag"
                  >{{ getCityOrProvinceName(code) }}</el-tag
                >
                <el-tag
                  v-if="selectedCities.length > 10"
                  type="info"
                  size="small"
                  >{{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-102") }}
                  {{ selectedCities.length - 10 }}
                  {{
                    $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-103")
                  }}</el-tag
                >
              </div>
            </div></el-descriptions-item
          >
          <el-descriptions-item
            :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-104')"
            ><div class="overview-time">
              <template v-if="timeType === 'all'"
                >{{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-105") }}
                {{
                  formData.kind === "pc"
                    ? $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-106")
                    : $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-107")
                }}
                {{
                  $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-108")
                }}</template
              >
              <template v-else-if="timeType === 'preset'"
                >{{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-109") }}
                {{ formData.days }}
                {{
                  $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-110")
                }}</template
              >
              <template v-else-if="timeType === 'custom' && dateRange"
                >{{ dateRange[0] }}
                {{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-111") }}
                {{ dateRange[1] }}</template
              >
              <template
                v-else-if="
                  timeType === 'year' &&
                  formData.yearRange[0] &&
                  formData.yearRange[1]
                "
                >{{ formData.yearRange[0] }}
                {{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-112") }}
                {{ formData.yearRange[1] }}
                {{
                  $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-113")
                }}</template
              >
            </div></el-descriptions-item
          >
          <el-descriptions-item
            :label="$t('tasks-SearchIndexTask-19c298e21d4fb2dcd-114')"
            ><div>
              {{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-115") }}
              {{
                formData.kind === "all"
                  ? $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-116")
                  : formData.kind === "pc"
                    ? "PC"
                    : $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-117")
              }}
            </div>
            <div>
              {{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-118") }}
              {{ formData.priority }}
            </div>
            <div v-if="formData.resume">
              {{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-119") }}
              {{ formData.taskId }}
            </div></el-descriptions-item
          ></el-descriptions
        >
      </div>
      <template #footer
        ><span class="dialog-footer"
          ><el-button @click="taskOverviewDialogVisible = false">{{
            $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-120")
          }}</el-button>
          <el-button
            type="primary"
            @click="confirmSubmitTask"
            :loading="submitting"
            >{{ $t("tasks-SearchIndexTask-19c298e21d4fb2dcd-121") }}</el-button
          ></span
        ></template
      ></el-dialog
    >
  </div>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { ref, reactive, computed, onMounted, watch } from "vue";

const { t, locale } = useI18n();
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
import RegionCitySelector from "../RegionCitySelector.vue";
import { useRegionStore } from "../../store/region";
import * as XLSX from "xlsx";

const API_BASE_URL = "http://127.0.0.1:5001/api";
const router = useRouter();
const regionStore = useRegionStore();

// 表单数据
const formData = reactive({
  keywords: [] as { value: string }[],
  days: 30,
  yearRange: ["", ""] as [string, string],
  resume: false,
  taskId: "",
  priority: 5,
  kind: "all",
});

// 城市数据
const selectedCities = ref<string[]>(["0"]); // 默认选中全国
const cityMap = ref<Record<string, string>>({}); // 城市代码到名称的映射

// 关键词输入
const batchKeywords = ref("");
const skipFirstLine = ref(true);
const skipFirstLineForCities = ref(true);

// 时间类型
const timeType = ref("all"); // 默认为全部数据
const dateRange = ref<[string, string] | null>(null);

// 日期范围限制
const MIN_DATE = new Date(2011, 0, 1);
const TODAY = new Date();
TODAY.setHours(0, 0, 0, 0);
const YESTERDAY = new Date(TODAY);
YESTERDAY.setDate(YESTERDAY.getDate() - 1);

// 禁用日期函数
const disabledDate = (date: Date) => {
  const minDate =
    formData.kind === "pc" ? new Date(2006, 0, 1) : new Date(2011, 0, 1);
  return (
    date.getTime() < minDate.getTime() || date.getTime() > YESTERDAY.getTime()
  );
};

// 禁用年份开始函数
const disabledYearStart = (date: Date) => {
  const year = date.getFullYear();
  const minYear = formData.kind === "pc" ? 2006 : 2011;
  return year < minYear || year > new Date().getFullYear();
};

// 禁用年份结束函数
const disabledYearEnd = (date: Date) => {
  const year = date.getFullYear();
  const startYear = formData.yearRange[0]
    ? parseInt(formData.yearRange[0])
    : formData.kind === "pc"
      ? 2006
      : 2011;
  return year < startYear || year > new Date().getFullYear();
};

// 状态
const submitting = ref(false);
const taskId = ref("");
const successDialogVisible = ref(false);

// 优先级标记 (使用 computed 实现语言切换响应)
const priorityMarks = computed(() => ({
  1: t("tasks-SearchIndexTask-19c298e21d4fb2dcd-122"),
  5: t("tasks-SearchIndexTask-19c298e21d4fb2dcd-123"),
  10: t("tasks-SearchIndexTask-19c298e21d4fb2dcd-124"),
}));

// 导入结果
const importResultDialogVisible = ref(false);
const importResultTitle = ref("");
const importResults = reactive({
  validItems: [] as string[],
  invalidItems: [] as string[],
});

// 关键词检查结果
const keywordCheckResults = reactive<Record<string, boolean | null>>({});
const checkingKeywords = ref(false);
const checkResultDialogVisible = ref(false);
const checkResults = reactive({
  existsCount: 0,
  notExistsCount: 0,
  notExistsKeywords: [] as string[],
});

// 任务概览对话框
const taskOverviewDialogVisible = ref(false);

// 计算是否可以提交
const canSubmit = computed(() => {
  // 必须有关键词
  if (formData.keywords.length === 0) return false;

  // 必须选择至少一个城市
  if (selectedCities.value.length === 0) return false;

  // 检查时间设置
  if (
    timeType.value === "custom" &&
    (!dateRange.value || !dateRange.value[0] || !dateRange.value[1])
  )
    return false;
  if (
    timeType.value === "year" &&
    (!formData.yearRange[0] || !formData.yearRange[1])
  )
    return false;

  // 恢复任务时需要任务ID
  if (formData.resume && !formData.taskId.trim()) return false;

  return true;
});

// 计算是否有不存在的关键词
const hasInvalidKeywords = computed(() => {
  return Object.values(keywordCheckResults).some((result) => result === false);
});

// 处理城市选择变化
const handleCitiesChange = (cities: string[]) => {
  selectedCities.value = cities.length > 0 ? cities : ["0"]; // 如果没有选择城市，默认选择全国
};

// 获取城市名称映射
const fetchCityMap = async () => {
  try {
    // 使用store获取城市数据
    if (!regionStore.isInitialized) {
      await regionStore.fetchRegionData();
    }

    cityMap.value = regionStore.getAllCities;
  } catch (error) {
    console.error(
      t("tasks-SearchIndexTask-19c298e21d4fb2dcd-125"),
      error,
    );
  }
};

// 检查关键词
const checkKeywords = async () => {
  if (formData.keywords.length === 0) {
    ElMessage.warning(
      t("tasks-SearchIndexTask-19c298e21d4fb2dcd-126"),
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
        `${t("tasks-SearchIndexTask-19c298e21d4fb2dcd-127")}${response.data.msg}`,
      );
    }
  } catch (error) {
    console.error(
      t("tasks-SearchIndexTask-19c298e21d4fb2dcd-128"),
      error,
    );
    ElMessage.error(
      t("tasks-SearchIndexTask-19c298e21d4fb2dcd-129"),
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
      `${t("tasks-SearchIndexTask-19c298e21d4fb2dcd-130")}${addedCount}${t("tasks-SearchIndexTask-19c298e21d4fb2dcd-131")}`,
    );
  }

  if (duplicateCount > 0) {
    ElMessage.warning(
      `${duplicateCount}${t("tasks-SearchIndexTask-19c298e21d4fb2dcd-132")}`,
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
    t("tasks-SearchIndexTask-19c298e21d4fb2dcd-133"),
    t("tasks-SearchIndexTask-19c298e21d4fb2dcd-134"),
    {
      confirmButtonText: t(
        "tasks-SearchIndexTask-19c298e21d4fb2dcd-135",
      ),
      cancelButtonText: t(
        "tasks-SearchIndexTask-19c298e21d4fb2dcd-136",
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
    t("tasks-SearchIndexTask-19c298e21d4fb2dcd-137"),
    t("tasks-SearchIndexTask-19c298e21d4fb2dcd-138"),
    {
      confirmButtonText: t(
        "tasks-SearchIndexTask-19c298e21d4fb2dcd-139",
      ),
      cancelButtonText: t(
        "tasks-SearchIndexTask-19c298e21d4fb2dcd-140",
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
          `${t("tasks-SearchIndexTask-19c298e21d4fb2dcd-141")}${invalidKeywords.length}${t("tasks-SearchIndexTask-19c298e21d4fb2dcd-142")}`,
        );
      }
    })
    .catch(() => {});
};

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
      `${t("tasks-SearchIndexTask-19c298e21d4fb2dcd-143")}${invalidKeywords.length}${t("tasks-SearchIndexTask-19c298e21d4fb2dcd-144")}`,
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
        t("tasks-SearchIndexTask-19c298e21d4fb2dcd-145"),
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
      "tasks-SearchIndexTask-19c298e21d4fb2dcd-146",
    );
    importResultDialogVisible.value = true;
  } catch (error) {
    console.error(
      t("tasks-SearchIndexTask-19c298e21d4fb2dcd-147"),
      error,
    );
    ElMessage.error(
      t("tasks-SearchIndexTask-19c298e21d4fb2dcd-148"),
    );
  }
};

// 处理城市文件上传
const handleCitiesFileChange = async (file: any) => {
  if (!file) return;

  try {
    // 确保区域数据已加载
    if (!regionStore.isInitialized) {
      await regionStore.fetchRegionData();
    }

    const cityCodes = await readFileContent(
      file.raw,
      skipFirstLineForCities.value,
    );

    if (cityCodes.length === 0) {
      ElMessage.warning(
        t("tasks-SearchIndexTask-19c298e21d4fb2dcd-149"),
      );
      return;
    }

    // 验证城市代码
    const { validCodes, invalidCodes } =
      regionStore.validateCityCodes(cityCodes);

    // 更新选中的城市
    if (validCodes.length > 0) {
      selectedCities.value = validCodes;
    }

    // 显示导入结果
    importResults.validItems = validCodes;
    importResults.invalidItems = invalidCodes;
    importResultTitle.value = t(
      "tasks-SearchIndexTask-19c298e21d4fb2dcd-150",
    );
    importResultDialogVisible.value = true;
  } catch (error) {
    console.error(
      t("tasks-SearchIndexTask-19c298e21d4fb2dcd-151"),
      error,
    );
    ElMessage.error(
      t("tasks-SearchIndexTask-19c298e21d4fb2dcd-152"),
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
        new Error(t("tasks-SearchIndexTask-19c298e21d4fb2dcd-153")),
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
    // 构建城市参数
    const citiesParam: Record<string, any> = {};

    // 处理选中的城市和省份
    selectedCities.value.forEach((code) => {
      // 检查是否是省份代码
      if (regionStore.getProvincesList[code]) {
        citiesParam[code] = {
          name: regionStore.getProvinceName(code),
          code: code,
        };
      }
      // 检查是否是城市代码或全国代码
      else if (regionStore.getAllCities[code]) {
        citiesParam[code] = {
          name: regionStore.getCityName(code),
          code: code,
        };
      }
    });

    // 准备参数
    const params: any = {
      taskType: "search_index",
      parameters: {
        keywords: formData.keywords.map((k) => k.value),
        cities: citiesParam,
        resume: formData.resume,
        kind: formData.kind,
      },
      priority: formData.priority,
    };

    // 添加时间相关参数
    if (timeType.value === "preset") {
      params.parameters.days = formData.days;
    } else if (timeType.value === "custom" && dateRange.value) {
      params.parameters.date_ranges = [
        [dateRange.value[0], dateRange.value[1]],
      ];
    } else if (
      timeType.value === "year" &&
      formData.yearRange[0] &&
      formData.yearRange[1]
    ) {
      params.parameters.year_range = [
        formData.yearRange[0],
        formData.yearRange[1],
      ];
    } else if (timeType.value === "all") {
      // 全部数据类型：生成按年份分割的日期范围数组
      const currentYear = new Date().getFullYear();
      const currentDate = new Date();
      let startYear;

      if (formData.kind === "pc") {
        startYear = 2006; // PC端从2006年开始
      } else {
        startYear = 2011; // 移动端和PC+移动从2011年开始
      }

      // 生成年度日期范围数组
      const dateRanges = [];
      for (let year = startYear; year <= currentYear; year++) {
        let startDate, endDate;

        if (year === startYear && formData.kind === "pc") {
          // PC端第一年从6月1日开始
          startDate = `${year}-06-01`;
        } else {
          // 其他情况从1月1日开始
          startDate = `${year}-01-01`;
        }

        if (year === currentYear) {
          // 当前年份到今天
          const month = String(currentDate.getMonth() + 1).padStart(2, "0");
          const day = String(currentDate.getDate()).padStart(2, "0");
          endDate = `${year}-${month}-${day}`;
        } else {
          // 其他年份到12月31日
          endDate = `${year}-12-31`;
        }

        dateRanges.push([startDate, endDate]);
      }

      params.parameters.date_ranges = dateRanges;
    }

    // 添加任务ID（如果是恢复任务）
    if (formData.resume && formData.taskId) {
      params.parameters.task_id = formData.taskId;
    }

    const response = await axios.post(`${API_BASE_URL}/task/create`, params);

    if (response.data.code === 10000) {
      taskId.value = response.data.data.taskId;
      successDialogVisible.value = true;
    } else {
      ElMessage.error(
        `${t("tasks-SearchIndexTask-19c298e21d4fb2dcd-154")}${response.data.message}`,
      );
    }
  } catch (error) {
    ElMessage.error(
      t("tasks-SearchIndexTask-19c298e21d4fb2dcd-155"),
    );
    console.error(
      t("tasks-SearchIndexTask-19c298e21d4fb2dcd-156"),
      error,
    );
  } finally {
    submitting.value = false;
  }
};

// 重置表单
const resetForm = () => {
  formData.keywords = [];
  batchKeywords.value = "";
  selectedCities.value = ["0"];
  timeType.value = "all";
  formData.days = 30;
  dateRange.value = null;
  formData.yearRange = ["", ""];
  formData.resume = false;
  formData.taskId = "";
  formData.priority = 5;
  formData.kind = "all";
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
  await submitTask();
};

// 获取城市或省份名称
const getCityOrProvinceName = (code: string) => {
  // 处理全国代码
  if (code === "0") {
    return t("tasks-SearchIndexTask-19c298e21d4fb2dcd-101"); // 全国
  }
  if (regionStore.getProvincesList[code]) {
    return regionStore.getProvinceName(code);
  } else if (regionStore.getAllCities[code]) {
    return regionStore.getCityName(code);
  }
  return code; // 默认显示城市代码
};

// 判断是否选择了全国
const nationwideSelected = computed(() => {
  return selectedCities.value.length === 1 && selectedCities.value[0] === "0";
});

// 页面加载时获取城市映射
onMounted(() => {
  fetchCityMap();
});
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

.keywords-tip {
  color: #909399;
  font-size: 12px;
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

.year-range {
  display: flex;
  align-items: center;
}

.range-separator {
  margin: 0 10px;
  color: #909399;
}

.success-content {
  text-align: center;
}

.time-info {
  margin-top: 10px;
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
  background-color: #f8f8f8;
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
.overview-cities,
.overview-time {
  margin-top: 10px;
}

.overview-count {
  font-weight: bold;
  margin-right: 10px;
}

.overview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.overview-tag {
  margin-bottom: 4px;
}

/* Deep Theme Overrides for Element Plus */
:deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
  background-color: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
  box-shadow: -1px 0 0 0 var(--color-primary) !important;
}

:deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background-color: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
}

:deep(.el-checkbox__input.is-checked + .el-checkbox__label) {
  color: var(--color-primary) !important;
}

:deep(.el-button--primary) {
  --el-button-bg-color: var(--color-primary);
  --el-button-border-color: var(--color-primary);
  --el-button-hover-bg-color: var(--color-primary-light);
  --el-button-hover-border-color: var(--color-primary-light);
  --el-button-active-bg-color: var(--color-primary-dark);
  --el-button-active-border-color: var(--color-primary-dark);
}

:deep(.el-button--primary.is-plain) {
  --el-button-text-color: var(--color-primary);
  --el-button-bg-color: var(--color-bg-subtle);
  --el-button-border-color: var(--color-primary);
  --el-button-hover-text-color: white;
  --el-button-hover-bg-color: var(--color-primary);
  --el-button-hover-border-color: var(--color-primary);
}

:deep(.el-switch.is-checked .el-switch__core) {
  background-color: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
}

:deep(.el-slider__bar) {
  background-color: var(--color-primary) !important;
}

:deep(.el-slider__button) {
  border-color: var(--color-primary) !important;
}
</style>
