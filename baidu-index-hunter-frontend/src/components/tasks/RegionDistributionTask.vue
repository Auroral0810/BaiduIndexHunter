<template>
  <div class="task-container">
    <div class="task-header">
      <h2>{{ $t("tasks-RegionDistributionTask-19c298e201890d5db-1") }}</h2>
      <div class="task-desc">
        {{ $t("tasks-RegionDistributionTask-19c298e201890d5db-2") }}
      </div>
    </div>
    <el-card class="task-card"
      ><template #header
        ><div class="card-header">
          <span>{{
            $t("tasks-RegionDistributionTask-19c298e201890d5db-3")
          }}</span>
        </div></template
      >
      <el-form :model="formData" label-width="120px" class="task-form"
        ><!-- 关键词设置 -->
        <el-divider content-position="left">{{
          $t("tasks-RegionDistributionTask-19c298e201890d5db-4")
        }}</el-divider>
        <el-form-item
          :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-5')"
          ><el-input
            v-model="batchKeywords"
            type="textarea"
            :rows="4"
            :placeholder="
              $t('tasks-RegionDistributionTask-19c298e201890d5db-6')
            "
          />
          <div class="keywords-actions">
            <el-button
              type="primary"
              @click="addBatchKeywords"
              :disabled="!batchKeywords.trim()"
              ><el-icon><Plus /></el-icon>
              {{
                $t("tasks-RegionDistributionTask-19c298e201890d5db-7")
              }}</el-button
            >
            <span class="keywords-tip">{{
              $t("tasks-RegionDistributionTask-19c298e201890d5db-8")
            }}</span>
          </div></el-form-item
        >
        <el-form-item
          :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-9')"
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
                $t("tasks-RegionDistributionTask-19c298e201890d5db-10")
              }}</el-button
            >
            <div class="upload-tip">
              {{ $t("tasks-RegionDistributionTask-19c298e201890d5db-11") }}
            </div></el-upload
          >
          <div class="file-import-options">
            <el-checkbox v-model="skipFirstLine">{{
              $t("tasks-RegionDistributionTask-19c298e201890d5db-12")
            }}</el-checkbox>
          </div></el-form-item
        >
        <el-form-item
          :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-13')"
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
                    $t('tasks-RegionDistributionTask-19c298e201890d5db-14')
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
                  $t("tasks-RegionDistributionTask-19c298e201890d5db-15")
                }}</el-button
              >
              <el-button
                type="primary"
                size="small"
                @click="checkKeywords"
                :loading="checkingKeywords"
                ><el-icon><Check /></el-icon>
                {{
                  $t("tasks-RegionDistributionTask-19c298e201890d5db-16")
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
                  $t("tasks-RegionDistributionTask-19c298e201890d5db-17")
                }}</el-button
              >
              <div class="keywords-count">
                {{ $t("tasks-RegionDistributionTask-19c298e201890d5db-18") }}
                {{ formData.keywords.length }}
                {{ $t("tasks-RegionDistributionTask-19c298e201890d5db-19") }}
              </div>
            </div>
          </div></el-form-item
        >
        <!-- 地区设置 -->
        <el-divider content-position="left">{{
          $t("tasks-RegionDistributionTask-19c298e201890d5db-20")
        }}</el-divider>
        <el-form-item
          :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-21')"
          ><RegionProvinceSelector
            v-model="selectedRegions"
            :api-base-url="apiBaseUrl"
            @change="handleRegionsChange"
        /></el-form-item>
        <el-form-item
          :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-22')"
          ><el-upload
            class="upload-area"
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleRegionsFileChange"
            accept=".xlsx,.csv,.txt"
            ><el-button type="primary"
              ><el-icon><Upload /></el-icon>
              {{
                $t("tasks-RegionDistributionTask-19c298e201890d5db-23")
              }}</el-button
            >
            <div class="upload-tip">
              {{ $t("tasks-RegionDistributionTask-19c298e201890d5db-24") }}
            </div></el-upload
          >
          <div class="file-import-options">
            <el-checkbox v-model="skipFirstLineForRegions">{{
              $t("tasks-RegionDistributionTask-19c298e201890d5db-25")
            }}</el-checkbox>
          </div></el-form-item
        >
        <!-- 时间设置 -->
        <el-divider content-position="left">{{
          $t("tasks-RegionDistributionTask-19c298e201890d5db-26")
        }}</el-divider>
        <el-form-item
          :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-30')"
          ><el-radio-group v-model="timeType"
            ><el-radio-button value="all">{{
              $t("tasks-RegionDistributionTask-19c298e201890d5db-31")
            }}</el-radio-button>
            <el-radio-button value="custom">{{
              $t("tasks-RegionDistributionTask-19c298e201890d5db-32")
            }}</el-radio-button>
            <el-radio-button value="preset">{{
              $t("tasks-RegionDistributionTask-19c298e201890d5db-33")
            }}</el-radio-button>
            <el-radio-button value="year">{{
              $t("tasks-RegionDistributionTask-19c298e201890d5db-34")
            }}</el-radio-button></el-radio-group
          ></el-form-item
        >
        <el-form-item
          :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-35')"
          v-if="timeType === 'custom'"
          ><el-date-picker
            v-model="dateRange"
            type="daterange"
            :range-separator="
              $t('tasks-RegionDistributionTask-19c298e201890d5db-36')
            "
            :start-placeholder="
              $t('tasks-RegionDistributionTask-19c298e201890d5db-37')
            "
            :end-placeholder="
              $t('tasks-RegionDistributionTask-19c298e201890d5db-38')
            "
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledDate"
            style="width: 100%"
            @change="handleDateRangeChange"
        /></el-form-item>
        <el-form-item
          :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-39')"
          v-if="timeType === 'preset'"
          ><el-select
            v-model="formData.days"
            :placeholder="
              $t('tasks-RegionDistributionTask-19c298e201890d5db-40')
            "
            style="width: 100%"
            ><el-option
              :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-41')"
              :value="7" />
            <el-option
              :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-42')"
              :value="30" />
            <el-option
              :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-43')"
              :value="90" />
            <el-option
              :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-44')"
              :value="180" />
            <el-option
              :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-45')"
              :value="365" /></el-select
        ></el-form-item>
        <el-form-item
          :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-46')"
          v-if="timeType === 'year'"
          ><div class="year-range">
            <el-date-picker
              v-model="formData.yearRange[0]"
              type="year"
              :placeholder="
                $t('tasks-RegionDistributionTask-19c298e201890d5db-47')
              "
              format="YYYY"
              value-format="YYYY"
              :disabled-date="disabledYearStart"
            />
            <span class="range-separator">{{
              $t("tasks-RegionDistributionTask-19c298e201890d5db-48")
            }}</span>
            <el-date-picker
              v-model="formData.yearRange[1]"
              type="year"
              :placeholder="
                $t('tasks-RegionDistributionTask-19c298e201890d5db-49')
              "
              format="YYYY"
              value-format="YYYY"
              :disabled-date="disabledYearEnd"
            /></div
        ></el-form-item>
        <el-form-item
          v-if="timeType === 'all'"
          :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-50')"
          ><div class="time-info">
            <el-alert
              :title="$t('tasks-RegionDistributionTask-19c298e201890d5db-alltime-hint') || '将爱取 2011 年至今的全部数据'"
              type="info"
              :closable="false"
              show-icon
            /></div
        ></el-form-item>
        <!-- 输出设置 -->
        <el-divider content-position="left">{{
          $t("tasks.common.output_settings")
        }}</el-divider>
        <el-form-item
          :label="$t('tasks.common.output_format')">
          <el-select v-model="formData.output_format" style="width: 200px">
            <el-option label="CSV (.csv)" value="csv" />
            <el-option label="Excel (.xlsx)" value="excel" />
            <el-option label="JSON (.json)" value="json" />
            <el-option label="Stata (.dta)" value="dta" />
            <el-option label="Parquet (.parquet)" value="parquet" />
            <el-option label="SQLite (.sqlite)" value="sql" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('tasks.common.output_dir')">
          <DirPicker
            v-model="formData.output_dir"
            :placeholder="$t('tasks.common.output_dir_placeholder')"
            :hint="$t('tasks.common.output_dir_hint')"
          />
        </el-form-item>
        <el-form-item :label="$t('tasks.common.custom_filename')">
          <el-input v-model="formData.output_name" :placeholder="$t('tasks.common.custom_filename_placeholder')" clearable />
          <div style="font-size: 12px; color: #909399; margin-top: 4px;">{{ $t('tasks.common.custom_filename_hint') }}</div>
        </el-form-item>
        <!-- 任务设置 -->
        <el-divider content-position="left">{{
          $t("tasks-RegionDistributionTask-19c298e201890d5db-59")
        }}</el-divider>
        <el-form-item
          :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-60')"
          ><el-switch
            v-model="formData.resume"
            :active-text="
              $t('tasks-RegionDistributionTask-19c298e201890d5db-61')
            "
            :inactive-text="
              $t('tasks-RegionDistributionTask-19c298e201890d5db-62')
            "
        /></el-form-item>
        <el-form-item
          :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-63')"
          v-if="formData.resume"
          ><el-input
            v-model="formData.task_id"
            :placeholder="
              $t('tasks-RegionDistributionTask-19c298e201890d5db-64')
            "
        /></el-form-item>
        <el-form-item
          :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-65')"
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
              $t("tasks-RegionDistributionTask-19c298e201890d5db-66")
            }}</el-button
          >
          <el-button @click="resetForm" size="large"
            ><el-icon><Refresh /></el-icon>
            {{
              $t("tasks-RegionDistributionTask-19c298e201890d5db-67")
            }}</el-button
          ></el-form-item
        ></el-form
      ></el-card
    >
    <el-dialog
      v-model="successDialogVisible"
      :title="$t('tasks-RegionDistributionTask-19c298e201890d5db-68')"
      width="500px"
      ><div class="success-content">
        <el-result
          icon="success"
          :title="$t('tasks-RegionDistributionTask-19c298e201890d5db-69')"
          :sub-title="`${$t('tasks-RegionDistributionTask-19c298e201890d5db-70')}${taskId}`"
          ><template #extra
            ><el-button type="primary" @click="goToTaskList">{{
              $t("tasks-RegionDistributionTask-19c298e201890d5db-71")
            }}</el-button>
            <el-button @click="successDialogVisible = false">{{
              $t("tasks-RegionDistributionTask-19c298e201890d5db-72")
            }}</el-button></template
          ></el-result
        >
      </div></el-dialog
    >
    <!-- 关键词检查结果对话框 -->
    <el-dialog
      v-model="checkResultDialogVisible"
      :title="$t('tasks-RegionDistributionTask-19c298e201890d5db-73')"
      width="500px"
      modal
      append-to-body
      :close-on-click-modal="false"
      :show-close="true"
      ><div class="check-result-content">
        <el-alert
          v-if="checkResults.existsCount > 0"
          type="success"
          :title="`${checkResults.existsCount}${$t('tasks-RegionDistributionTask-19c298e201890d5db-74')}`"
          :closable="false"
          show-icon
        />
        <el-alert
          v-if="checkResults.notExistsCount > 0"
          type="warning"
          :title="`${checkResults.notExistsCount}${$t('tasks-RegionDistributionTask-19c298e201890d5db-75')}`"
          :closable="false"
          show-icon
          style="margin-top: 10px"
        />
        <div v-if="checkResults.notExistsCount > 0" class="invalid-keywords">
          <p>{{ $t("tasks-RegionDistributionTask-19c298e201890d5db-76") }}</p>
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
            $t("tasks-RegionDistributionTask-19c298e201890d5db-77")
          }}</el-button>
          <el-button
            type="warning"
            @click="removeInvalidKeywordsFromDialog"
            :disabled="checkResults.notExistsCount === 0"
            >{{
              $t("tasks-RegionDistributionTask-19c298e201890d5db-78")
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
          :title="`${$t('tasks-RegionDistributionTask-19c298e201890d5db-79')} ${importResults.validItems.length}${importResultTitle === $t('tasks-RegionDistributionTask-19c298e201890d5db-80') ? $t('tasks-RegionDistributionTask-19c298e201890d5db-81') : $t('tasks-RegionDistributionTask-19c298e201890d5db-82')}`"
          :closable="false"
          show-icon
        />
        <el-alert
          v-if="importResults.invalidItems.length > 0"
          type="warning"
          :title="`${importResults.invalidItems.length} ${importResultTitle === $t('tasks-RegionDistributionTask-19c298e201890d5db-84') ? $t('tasks-RegionDistributionTask-19c298e201890d5db-85') : $t('tasks-RegionDistributionTask-19c298e201890d5db-86')}${$t('tasks-RegionDistributionTask-19c298e201890d5db-83')}`"
          :closable="false"
          show-icon
          style="margin-top: 10px"
        />
        <div
          v-if="importResults.invalidItems.length > 0"
          class="invalid-keywords"
        >
          <p>
            {{ $t("tasks-RegionDistributionTask-19c298e201890d5db-87") }}
            {{
              importResultTitle ===
              $t("tasks-RegionDistributionTask-19c298e201890d5db-88")
                ? $t("tasks-RegionDistributionTask-19c298e201890d5db-89")
                : $t("tasks-RegionDistributionTask-19c298e201890d5db-90")
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
              >{{ $t("tasks-RegionDistributionTask-19c298e201890d5db-91") }}
              {{ importResults.invalidItems.length - 20 }}
              {{
                $t("tasks-RegionDistributionTask-19c298e201890d5db-92")
              }}</el-tag
            >
          </div>
        </div>
      </div>
      <template #footer
        ><span class="dialog-footer"
          ><el-button @click="importResultDialogVisible = false">{{
            $t("tasks-RegionDistributionTask-19c298e201890d5db-93")
          }}</el-button></span
        ></template
      ></el-dialog
    >
    <!-- 添加任务概览对话框 -->
    <el-dialog
      v-model="taskOverviewDialogVisible"
      :title="$t('tasks-RegionDistributionTask-19c298e201890d5db-94')"
      width="600px"
      :close-on-click-modal="false"
      ><div class="task-overview">
        <el-descriptions
          :title="$t('tasks-RegionDistributionTask-19c298e201890d5db-95')"
          :column="1"
          border
          ><el-descriptions-item
            :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-96')"
            ><el-tag>{{
              $t("tasks-RegionDistributionTask-19c298e201890d5db-97")
            }}</el-tag></el-descriptions-item
          >
          <el-descriptions-item
            :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-98')"
            ><div class="overview-keywords">
              <span class="overview-count"
                >{{ $t("tasks-RegionDistributionTask-19c298e201890d5db-99") }}
                {{ formData.keywords.length }}
                {{
                  $t("tasks-RegionDistributionTask-19c298e201890d5db-100")
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
                    $t("tasks-RegionDistributionTask-19c298e201890d5db-101")
                  }}
                  {{ formData.keywords.length - 10 }}
                  {{
                    $t("tasks-RegionDistributionTask-19c298e201890d5db-102")
                  }}</el-tag
                >
              </div>
            </div></el-descriptions-item
          >
          <el-descriptions-item
            :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-103')"
            ><div class="overview-regions">
              <span class="overview-count"
                >{{ $t("tasks-RegionDistributionTask-19c298e201890d5db-104") }}
                {{ selectedRegions.length }}
                {{
                  $t("tasks-RegionDistributionTask-19c298e201890d5db-105")
                }}</span
              >
              <div class="overview-tags">
                <el-tag
                  v-for="(code, index) in selectedRegions.slice(0, 10)"
                  :key="index"
                  size="small"
                  class="overview-tag"
                  >{{ getRegionName(code) }}</el-tag
                >
                <el-tag
                  v-if="selectedRegions.length > 10"
                  type="info"
                  size="small"
                  >{{
                    $t("tasks-RegionDistributionTask-19c298e201890d5db-107")
                  }}
                  {{ selectedRegions.length - 10 }}
                  {{
                    $t("tasks-RegionDistributionTask-19c298e201890d5db-108")
                  }}</el-tag
                >
              </div>
            </div></el-descriptions-item
          >
          <el-descriptions-item
            :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-109')"
            ><div class="overview-time">
              <template v-if="timeType === 'all'"
                >{{ $t("tasks-RegionDistributionTask-19c298e201890d5db-110") }}
                2011
                {{
                  $t("tasks-RegionDistributionTask-19c298e201890d5db-113")
                }}</template
              >
              <template v-else-if="timeType === 'preset'"
                >{{ $t("tasks-RegionDistributionTask-19c298e201890d5db-114") }}
                {{ formData.days }}
                {{
                  $t("tasks-RegionDistributionTask-19c298e201890d5db-115")
                }}</template
              >
              <template
                v-else-if="
                  timeType === 'custom' && dateRange && dateRange.length === 2
                "
                >{{ dateRange[0] }}
                {{ $t("tasks-RegionDistributionTask-19c298e201890d5db-116") }}
                {{ dateRange[1] }}</template
              >
              <template
                v-else-if="
                  timeType === 'year' &&
                  formData.yearRange[0] &&
                  formData.yearRange[1]
                "
                >{{ formData.yearRange[0] }}
                {{ $t("tasks-RegionDistributionTask-19c298e201890d5db-117") }}
                {{ formData.yearRange[1] }}
                {{
                  $t("tasks-RegionDistributionTask-19c298e201890d5db-118")
                }}</template
              >
            </div></el-descriptions-item
          >
          <el-descriptions-item
            :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-119')"
            >{{
              formData.output_format === "csv"
                ? $t("tasks-RegionDistributionTask-19c298e201890d5db-120")
                : $t("tasks-RegionDistributionTask-19c298e201890d5db-121")
            }}</el-descriptions-item
          >
          <el-descriptions-item
            :label="$t('tasks-RegionDistributionTask-19c298e201890d5db-122')"
            ><div>
              {{ $t("tasks-RegionDistributionTask-19c298e201890d5db-126") }}
              {{ formData.priority }}
            </div>
            <div v-if="formData.resume">
              {{ $t("tasks-RegionDistributionTask-19c298e201890d5db-127") }}
              {{ formData.task_id }}
            </div></el-descriptions-item
          ></el-descriptions
        >
      </div>
      <template #footer
        ><span class="dialog-footer"
          ><el-button @click="taskOverviewDialogVisible = false">{{
            $t("tasks-RegionDistributionTask-19c298e201890d5db-128")
          }}</el-button>
          <el-button
            type="primary"
            @click="confirmSubmitTask"
            :loading="submitting"
            >{{
              $t("tasks-RegionDistributionTask-19c298e201890d5db-129")
            }}</el-button
          ></span
        ></template
      ></el-dialog
    >
  </div>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { ref, reactive, computed, onMounted, nextTick } from "vue";

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
import * as XLSX from "xlsx";
import RegionProvinceSelector from "@/components/RegionProvinceSelector.vue";
import DirPicker from "../DirPicker.vue";
import { useRegionStore } from "@/store/region";

import { apiBaseUrl } from "@/config/api";
const router = useRouter();
const regionStore = useRegionStore();

// 表单数据
const formData = reactive({
  keywords: [] as { value: string }[],
  regionLevel: "province",
  days: 90,
  start_date: "",
  end_date: "",
  output_format: "csv",
  output_dir: "",
  output_name: "",
  resume: false,
  task_id: "",
  priority: 5,
  yearRange: [2011, new Date().getFullYear()],
});


// 地区选择
const selectedRegions = ref<string[]>(["0"]); // 默认选择全国
const skipFirstLineForRegions = ref(true);

// 关键词输入
const batchKeywords = ref("");
const skipFirstLine = ref(true);

// 时间设置
const timeType = ref("all");
const dateRange = ref<string[]>([]);

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

// 优先级标记
const priorityMarks = computed(() => ({
  1: t("tasks-RegionDistributionTask-19c298e201890d5db-130"),
  5: t("tasks-RegionDistributionTask-19c298e201890d5db-131"),
  10: t("tasks-RegionDistributionTask-19c298e201890d5db-132"),
}));

// 关键词检查结果
const keywordCheckResults = reactive<Record<string, boolean | null>>({});
const checkingKeywords = ref(false);
const checkResultDialogVisible = ref(false);
const checkResults = reactive({
  existsCount: 0,
  notExistsCount: 0,
  notExistsKeywords: [] as string[],
});

// 日期范围限制
const MIN_DATE = new Date(2011, 0, 1);
const TODAY = new Date();
TODAY.setHours(0, 0, 0, 0);
const YESTERDAY = new Date(TODAY);
YESTERDAY.setDate(YESTERDAY.getDate() - 1);

// 禁用日期函数
const disabledDate = (date: Date) => {
  // 地域分布数据从 2011 年开始
  const minDate = new Date(2011, 0, 1);
  return (
    date.getTime() < minDate.getTime() || date.getTime() > YESTERDAY.getTime()
  );
};


// 禁用年份开始函数
const disabledYearStart = (date: Date) => {
  const year = date.getFullYear();
  const minYear = 2011; // 地域分布数据从 2011 年开始
  return year < minYear || year > new Date().getFullYear();
};


// 禁用年份结束函数
const disabledYearEnd = (date: Date) => {
  const year = date.getFullYear();
  const startYear = formData.yearRange[0]
    ? parseInt(formData.yearRange[0])
    : 2011;
  return year < startYear || year > new Date().getFullYear();
};


// 从store获取省份和城市数据
const provincesList = computed(() => regionStore.getProvincesList);

// 计算是否可以提交
const canSubmit = computed(() => {
  // 必须有关键词
  if (formData.keywords.length === 0) return false;

  // 必须选择至少一个地区
  if (selectedRegions.value.length === 0) return false;

  // 自定义日期范围时，必须同时有开始和结束日期
  if (
    timeType.value === "custom" &&
    (!formData.start_date || !formData.end_date)
  )
    return false;

  // 恢复任务时需要任务ID
  if (formData.resume && !formData.task_id.trim()) return false;

  return true;
});

// 处理时间范围类型变化
const handleDateRangeChange = (dates: string[]) => {
  if (dates && dates.length === 2) {
    formData.start_date = dates[0];
    formData.end_date = dates[1];
  } else {
    formData.start_date = "";
    formData.end_date = "";
  }
};

// 检查关键词
const checkKeywords = async () => {
  if (formData.keywords.length === 0) {
    ElMessage.warning(
      t("tasks-RegionDistributionTask-19c298e201890d5db-133"),
    );
    return;
  }

  checkingKeywords.value = true;

  try {
    const keywords = formData.keywords.map((k) => k.value);
    const response = await axios.post(`${apiBaseUrl}/word-check/check`, {
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
        `${t("tasks-RegionDistributionTask-19c298e201890d5db-134")}${response.data.msg}`,
      );
    }
  } catch (error) {
    console.error(
      t("tasks-RegionDistributionTask-19c298e201890d5db-135"),
      error,
    );
    ElMessage.error(
      t("tasks-RegionDistributionTask-19c298e201890d5db-136"),
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
      `${t("tasks-RegionDistributionTask-19c298e201890d5db-137")}${addedCount}${t("tasks-RegionDistributionTask-19c298e201890d5db-138")}`,
    );
  }

  if (duplicateCount > 0) {
    ElMessage.warning(
      `${duplicateCount}${t("tasks-RegionDistributionTask-19c298e201890d5db-139")}`,
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
    t("tasks-RegionDistributionTask-19c298e201890d5db-140"),
    t("tasks-RegionDistributionTask-19c298e201890d5db-141"),
    {
      confirmButtonText: t(
        "tasks-RegionDistributionTask-19c298e201890d5db-142",
      ),
      cancelButtonText: t(
        "tasks-RegionDistributionTask-19c298e201890d5db-143",
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
        t("tasks-RegionDistributionTask-19c298e201890d5db-144"),
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
      "tasks-RegionDistributionTask-19c298e201890d5db-145",
    );
    importResultDialogVisible.value = true;
  } catch (error) {
    console.error(
      t("tasks-RegionDistributionTask-19c298e201890d5db-146"),
      error,
    );
    ElMessage.error(
      t("tasks-RegionDistributionTask-19c298e201890d5db-147"),
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
          t("tasks-RegionDistributionTask-19c298e201890d5db-148"),
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

// 处理地区选择变化
const handleRegionsChange = (regions: string[]) => {
  selectedRegions.value = regions.length > 0 ? regions : ["0"]; // 如果没有选择地区，默认选择全国
};

// 处理地区文件上传
const handleRegionsFileChange = async (file: any) => {
  if (!file) return;

  try {
    // 确保区域数据已加载
    if (!regionStore.isInitialized) {
      await regionStore.fetchRegionData();
    }

    const regionCodes = await readFileContent(
      file.raw,
      skipFirstLineForRegions.value,
    );

    if (regionCodes.length === 0) {
      ElMessage.warning(
        t("tasks-RegionDistributionTask-19c298e201890d5db-149"),
      );
      return;
    }

    // 验证地区代码
    const { validCodes, invalidCodes } =
      regionStore.validateCityCodes(regionCodes);

    // 更新选中的地区
    if (validCodes.length > 0) {
      selectedRegions.value = validCodes;
    }

    // 显示导入结果
    importResults.validItems = validCodes;
    importResults.invalidItems = invalidCodes;
    importResultTitle.value = t(
      "tasks-RegionDistributionTask-19c298e201890d5db-150",
    );
    importResultDialogVisible.value = true;
  } catch (error) {
    console.error(
      t("tasks-RegionDistributionTask-19c298e201890d5db-151"),
      error,
    );
    ElMessage.error(
      t("tasks-RegionDistributionTask-19c298e201890d5db-152"),
    );
  }
};

// 计算是否有不存在的关键词
const hasInvalidKeywords = computed(() => {
  return Object.values(keywordCheckResults).some((result) => result === false);
});

// 清除不存在的关键词
const removeInvalidKeywords = () => {
  if (!hasInvalidKeywords.value) return;

  ElMessageBox.confirm(
    t("tasks-RegionDistributionTask-19c298e201890d5db-153"),
    t("tasks-RegionDistributionTask-19c298e201890d5db-154"),
    {
      confirmButtonText: t(
        "tasks-RegionDistributionTask-19c298e201890d5db-155",
      ),
      cancelButtonText: t(
        "tasks-RegionDistributionTask-19c298e201890d5db-156",
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
          `${t("tasks-RegionDistributionTask-19c298e201890d5db-157")}${invalidKeywords.length}${t("tasks-RegionDistributionTask-19c298e201890d5db-158")}`,
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
      `${t("tasks-RegionDistributionTask-19c298e201890d5db-159")}${invalidKeywords.length}${t("tasks-RegionDistributionTask-19c298e201890d5db-160")}`,
    );
    checkResultDialogVisible.value = false;
  }
};

// 提交任务
const submitTask = async () => {
  submitting.value = true;

  try {
    // 准备参数
    const params: any = {
      taskType: "region_distribution",
      parameters: {
        keywords: formData.keywords.map((k) => k.value),
        regionLevel: formData.regionLevel,
        output_format: formData.output_format,
        ...(formData.output_dir ? { output_dir: formData.output_dir } : {}),
        ...(formData.output_name ? { output_name: formData.output_name } : {}),
        resume: formData.resume,
        regions: selectedRegions.value,
      },
      priority: formData.priority,
    };


    // 添加时间参数
    if (timeType.value === "preset") {
      params.parameters.days = formData.days;
    } else if (timeType.value === "year") {
      params.parameters.yearRange = formData.yearRange;
    } else if (
      timeType.value === "custom" &&
      dateRange.value &&
      dateRange.value.length === 2
    ) {
      params.parameters.start_date = dateRange.value[0];
      params.parameters.end_date = dateRange.value[1];
    } else if (timeType.value === "all") {
      // 全部数据类型：生成按年份分割的日期范围数组
      const currentYear = new Date().getFullYear();
      const currentDate = new Date();
      // 地域分布数据从 2011 年开始
      const startYear = 2011;

      // 生成年度日期范围数组
      const dateRanges = [];
      for (let year = startYear; year <= currentYear; year++) {
        let startDate, endDate;

        // 从 1 月 1 日开始
        startDate = `${year}-01-01`;


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
    if (formData.resume && formData.task_id) {
      params.parameters.task_id = formData.task_id;
    }

    const response = await axios.post(`${apiBaseUrl}/task/create`, params);

    if (response.data.code === 10000) {
      taskId.value = response.data.data.taskId;
      successDialogVisible.value = true;
    } else {
      ElMessage.error(
        `${t("tasks-RegionDistributionTask-19c298e201890d5db-161")}${response.data.msg}`,
      );
    }
  } catch (error) {
    ElMessage.error(
      t("tasks-RegionDistributionTask-19c298e201890d5db-162"),
    );
    console.error(
      t("tasks-RegionDistributionTask-19c298e201890d5db-163"),
      error,
    );
  } finally {
    submitting.value = false;
  }
};

// 重置表单
const resetForm = () => {
  formData.keywords = [];
  formData.regionLevel = "province";
  formData.days = 30;
  formData.start_date = "";
  formData.end_date = "";
  formData.output_format = "csv";
  formData.resume = false;
  formData.task_id = "";
  formData.priority = 5;
  batchKeywords.value = "";
  timeType.value = "all";
  dateRange.value = [];
  formData.yearRange = [2011, new Date().getFullYear()];
  selectedRegions.value = ["0"]; // 重置为全国
};

// 前往任务列表页面
const goToTaskList = () => {
  router.push({ path: "/data-collection", query: { tab: "task_list" } });
  successDialogVisible.value = false;
};

// 显示任务概览对话框
const showTaskOverview = async () => {
  // 使用 nextTick 确保所有响应式更新完成后再显示对话框
  await nextTick();
  taskOverviewDialogVisible.value = true;
};

// 确认提交任务
const confirmSubmitTask = async () => {
  taskOverviewDialogVisible.value = false;
  submitTask();
};

// 获取地区名称
const getRegionName = (code: string) => {
  // 处理全国代码
  if (code === "0") {
    return t("tasks-RegionDistributionTask-19c298e201890d5db-106"); // 全国
  }
  const region = regionStore.getRegionByCode(code);
  return region ? region.name : code;
};

// 判断是否选择了全国
const nationwideSelected = computed(() => {
  return selectedRegions.value.length === 1 && selectedRegions.value[0] === "0";
});

// 页面加载时获取地区列表
onMounted(async () => {
  // 从store获取地区数据
  if (!regionStore.isInitialized) {
    await regionStore.fetchRegionData();
  }
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

.year-range {
  display: flex;
  align-items: center;
}

.range-separator {
  margin: 0 10px;
  color: #909399;
}

.time-info {
  margin-top: 10px;
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
.overview-regions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.overview-count {
  font-weight: bold;
  color: #303133;
}

.overview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.overview-tag {
  background-color: #e6f7ff;
  color: #1890ff;
  border-color: #91d5ff;
}

.overview-time {
  color: #303133;
  font-weight: bold;
}
</style>
