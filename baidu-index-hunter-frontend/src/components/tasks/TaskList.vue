<template>
  <div class="task-list-container">
    <h2>{{ $t("tasks-TaskList-19c298d949224c78d-1") }}</h2>
    <div class="search-bar">
      <el-input
        v-model="searchKeyword"
        :placeholder="$t('tasks-TaskList-19c298d949224c78d-2')"
        clearable
        style="width: 200px; margin-right: 10px"
      />
      <el-select
        v-model="taskTypeFilter"
        :placeholder="$t('tasks-TaskList-19c298d949224c78d-3')"
        clearable
        style="width: 150px; margin-right: 10px"
        ><el-option
          :label="$t('tasks-TaskList-19c298d949224c78d-4')"
          value="search_index" />
        <el-option
          :label="$t('tasks-TaskList-19c298d949224c78d-5')"
          value="feed_index" />
        <el-option
          :label="$t('tasks-TaskList-19c298d949224c78d-6')"
          value="word_graph" />
        <el-option
          :label="$t('tasks-TaskList-19c298d949224c78d-7')"
          value="demographic_attributes" />
        <el-option
          :label="$t('tasks-TaskList-19c298d949224c78d-8')"
          value="interest_profile" />
        <el-option
          :label="$t('tasks-TaskList-19c298d949224c78d-9')"
          value="region_distribution"
      /></el-select>
      <el-select
        v-model="statusFilter"
        :placeholder="$t('tasks-TaskList-19c298d949224c78d-10')"
        clearable
        style="width: 150px; margin-right: 10px"
        ><el-option
          :label="$t('tasks-TaskList-19c298d949224c78d-11')"
          value="pending" />
        <el-option
          :label="$t('tasks-TaskList-19c298d949224c78d-12')"
          value="running" />
        <el-option
          :label="$t('tasks-TaskList-19c298d949224c78d-13')"
          value="completed" />
        <el-option
          :label="$t('tasks-TaskList-19c298d949224c78d-14')"
          value="failed" />
        <el-option
          :label="$t('tasks-TaskList-19c298d949224c78d-15')"
          value="cancelled"
      /></el-select>
      <el-button type="primary" @click="loadTasks">{{
        $t("tasks-TaskList-19c298d949224c78d-16")
      }}</el-button>
      <el-button @click="resetFilters">{{
        $t("tasks-TaskList-19c298d949224c78d-17")
      }}</el-button>
    </div>
    <div class="table-wrapper">
      <div v-if="loading" class="loading-container">
        <el-empty
          :description="$t('tasks-TaskList-19c298d949224c78d-18')"
          :image-size="100"
          ><template #image
            ><el-icon class="loading-icon is-loading"
              ><Loading /></el-icon></template
        ></el-empty>
      </div>
      <el-table v-else :data="tasks" style="width: 100%" border stripe
        ><el-table-column
          prop="taskId"
          :label="$t('tasks-TaskList-19c298d949224c78d-19')"
          width="210"
          show-overflow-tooltip
        />
        <el-table-column
          :label="$t('tasks-TaskList-19c298d949224c78d-20')"
          width="95"
          ><template #default="scope"
            ><el-tag :type="getTaskTypeTag(scope.row.taskType)">{{
              translateTaskType(scope.row.taskType)
            }}</el-tag></template
          ></el-table-column
        >
        <el-table-column
          :label="$t('tasks-TaskList-19c298d949224c78d-21')"
          width="85"
          ><template #default="scope"
            ><el-tag :type="getStatusTag(scope.row.status)">{{
              translateStatus(scope.row.status)
            }}</el-tag></template
          ></el-table-column
        >
        <el-table-column
          :label="$t('tasks-TaskList-19c298d949224c78d-22')"
          show-overflow-tooltip
          ><template #default="scope"
            ><div v-if="scope.row.parameters" class="task-parameters">
              <div v-if="scope.row.parameters.keywords">
                <strong>{{ $t("tasks-TaskList-19c298d949224c78d-23") }}</strong>
                {{ formatKeywords(scope.row.parameters.keywords) }}
              </div>
              <div v-if="scope.row.parameters.cities">
                <strong>{{ $t("tasks-TaskList-19c298d949224c78d-24") }}</strong>
                {{ formatCities(scope.row.parameters.cities) }}
              </div>
              <div v-if="scope.row.parameters.regions">
                <strong>{{ $t("tasks-TaskList-19c298d949224c78d-25") }}</strong>
                {{ formatRegions(scope.row.parameters.regions) }}
              </div>
              <div v-if="scope.row.parameters.date_ranges">
                <strong>{{ $t("tasks-TaskList-19c298d949224c78d-26") }}</strong>
                {{ formatDateRanges(scope.row.parameters.date_ranges) }}
              </div>
              <div v-if="scope.row.parameters.days">
                <strong>{{ $t("tasks-TaskList-19c298d949224c78d-27") }}</strong>
                {{ $t("tasks-TaskList-19c298d949224c78d-28") }}
                {{ scope.row.parameters.days }}
                {{ $t("tasks-TaskList-19c298d949224c78d-29") }}
              </div>
              <div v-if="scope.row.parameters.year_range">
                <strong>{{ $t("tasks-TaskList-19c298d949224c78d-30") }}</strong>
                {{ scope.row.parameters.year_range[0] }}
                {{ $t("tasks-TaskList-19c298d949224c78d-31") }}
                {{ scope.row.parameters.year_range[1] }}
              </div>
              <div
                v-if="
                  scope.row.parameters.start_date &&
                  scope.row.parameters.end_date
                "
              >
                <strong>{{ $t("tasks-TaskList-19c298d949224c78d-32") }}</strong>
                {{ scope.row.parameters.start_date }}
                {{ $t("tasks-TaskList-19c298d949224c78d-33") }}
                {{ scope.row.parameters.end_date }}
              </div>
              <div v-if="scope.row.parameters.datelists">
                <strong>{{ $t("tasks-TaskList-19c298d949224c78d-34") }}</strong>
                {{ formatDatelists(scope.row.parameters.datelists) }}
              </div>
              <div v-if="scope.row.parameters.batch_size">
                <strong>{{ $t("tasks-TaskList-19c298d949224c78d-35") }}</strong>
                {{ scope.row.parameters.batch_size }}
              </div>
              <div v-if="scope.row.parameters.kind">
                <strong>{{ $t("tasks-TaskList-19c298d949224c78d-36") }}</strong>
                {{
                  scope.row.parameters.kind === "all"
                    ? $t("tasks-TaskList-19c298d949224c78d-37")
                    : scope.row.parameters.kind === "pc"
                      ? "PC"
                      : $t("tasks-TaskList-19c298d949224c78d-38")
                }}
              </div>
              <div v-if="scope.row.parameters.output_format">
                <strong>{{ $t("tasks-TaskList-19c298d949224c78d-39") }}</strong>
                {{ formatLabel(scope.row.parameters.output_format) }}
              </div>
              <div v-if="scope.row.parameters.output_dir">
                <strong>输出目录: </strong>
                <span style="word-break: break-all">{{ scope.row.parameters.output_dir }}</span>
              </div>
              <div v-if="scope.row.parameters.output_name">
                <strong>文件名: </strong>{{ scope.row.parameters.output_name }}
              </div>
            </div></template
          ></el-table-column
        >
        <el-table-column
          prop="createdAt"
          :label="$t('tasks-TaskList-19c298d949224c78d-40')"
          width="160"
        />
        <el-table-column
          :label="$t('tasks-TaskList-19c298d949224c78d-41')"
          width="120"
          ><template #default="scope"
            ><div style="display: flex; align-items: center; gap: 8px">
              <el-progress
                :percentage="scope.row.progress || 0"
                :status="getProgressStatus(scope.row.status)"
                :stroke-width="18"
                style="flex: 1"
                :show-text="false"
              />
              <span
                v-if="typeof scope.row.progress === 'number'"
                style="
                  min-width: 38px;
                  text-align: right;
                  font-size: 14px;
                  color: #606266;
                "
                >{{ scope.row.progress.toFixed(1) }} %
              </span>
            </div></template
          ></el-table-column
        >
        <el-table-column
          :label="$t('tasks-TaskList-19c298d949224c78d-42')"
          width="120"
          ><template #default="scope"
            ><el-dropdown trigger="click"
              ><el-button type="primary" size="small"
                >{{ $t("tasks-TaskList-19c298d949224c78d-43") }}
                <el-icon class="el-icon--right"><ArrowDown /></el-icon
              ></el-button>
              <template #dropdown
                ><el-dropdown-menu
                  ><el-dropdown-item @click="viewTaskDetail(scope.row)"
                    ><el-icon><View /></el-icon>
                    {{
                      $t("tasks-TaskList-19c298d949224c78d-44")
                    }}</el-dropdown-item
                  >
                  <el-dropdown-item
                    v-if="
                      scope.row.status === 'failed' ||
                      scope.row.status === 'cancelled'
                    "
                    @click="restartTask(scope.row)"
                    ><el-icon><RefreshRight /></el-icon>
                    {{
                      $t("tasks-TaskList-19c298d949224c78d-45")
                    }}</el-dropdown-item
                  >
                  <el-dropdown-item
                    v-if="
                      scope.row.status === 'pending' ||
                      scope.row.status === 'running'
                    "
                    @click="cancelTask(scope.row)"
                    divided
                    ><el-icon><Close /></el-icon>
                    {{
                      $t("tasks-TaskList-19c298d949224c78d-46")
                    }}</el-dropdown-item
                  >
                  <el-dropdown-item
                    v-if="
                      scope.row.status === 'completed' &&
                      scope.row.output_files &&
                      scope.row.output_files.length > 0
                    "
                    @click="downloadTaskResult(scope.row)"
                    divided
                    ><el-icon><Download /></el-icon>
                    {{
                      $t("tasks-TaskList-19c298d949224c78d-47")
                    }}</el-dropdown-item
                  ></el-dropdown-menu
                ></template
              ></el-dropdown
            ></template
          ></el-table-column
        ></el-table
      >
    </div>
    <div class="pagination" v-if="!loading && tasks.length > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 30, 50]"
        layout="total, sizes, prev, pager, next"
        :total="total"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
    <!-- 任务详情对话框 -->
    <el-dialog
      v-model="taskDetailDialogVisible"
      :title="$t('tasks-TaskList-19c298d949224c78d-48')"
      width="50%"
      top="5vh"
      destroy-on-close
      :modal="true"
      :append-to-body="true"
      :close-on-click-modal="false"
      @open="handleDialogOpen"
      class="task-detail-dialog"
      ><div v-if="selectedTask" class="task-detail">
        <!-- 顶部信息卡片 -->
        <el-card class="info-card" shadow="hover"
          ><div class="info-header">
            <div class="task-id">
              <span class="label">{{
                $t("tasks-TaskList-19c298d949224c78d-49")
              }}</span>
              <span class="value">{{
                selectedTask.taskId || selectedTask.task_id
              }}</span>
            </div>
            <div class="task-status">
              <el-tag :type="getStatusTag(selectedTask.status)" size="large">{{
                translateStatus(selectedTask.status)
              }}</el-tag>
            </div>
          </div>
          <el-row :gutter="20" class="info-row"
            ><el-col :span="8"
              ><div class="info-item">
                <div class="info-label">
                  {{ $t("tasks-TaskList-19c298d949224c78d-50") }}
                </div>
                <div class="info-value">
                  {{
                    translateTaskType(
                      selectedTask.taskType || selectedTask.task_type,
                    )
                  }}
                </div>
              </div></el-col
            >
            <el-col :span="8"
              ><div class="info-item">
                <div class="info-label">
                  {{ $t("tasks-TaskList-19c298d949224c78d-51") }}
                </div>
                <div class="info-value">
                  {{ selectedTask.createdAt || selectedTask.create_time }}
                </div>
              </div></el-col
            >
            <el-col :span="8"
              ><div class="info-item">
                <div class="info-label">
                  {{ $t("tasks-TaskList-19c298d949224c78d-52") }}
                </div>
                <div class="info-value">
                  {{ selectedTask.updatedAt || selectedTask.update_time }}
                </div>
              </div></el-col
            ></el-row
          >
          <el-row :gutter="20" class="info-row"
            ><el-col :span="8" v-if="selectedTask.task_name"
              ><div class="info-item">
                <div class="info-label">
                  {{ $t("tasks-TaskList-19c298d949224c78d-53") }}
                </div>
                <div class="info-value">{{ selectedTask.task_name }}</div>
              </div></el-col
            >
            <el-col :span="8" v-if="selectedTask.priority"
              ><div class="info-item">
                <div class="info-label">
                  {{ $t("tasks-TaskList-19c298d949224c78d-54") }}
                </div>
                <div class="info-value">
                  {{ getPriorityLabel(selectedTask.priority) }}
                </div>
              </div></el-col
            >
            <el-col :span="8" v-if="selectedTask.id !== undefined"
              ><div class="info-item">
                <div class="info-label">
                  {{ $t("tasks-TaskList-19c298d949224c78d-55") }}
                </div>
                <div class="info-value">{{ selectedTask.id }}</div>
              </div></el-col
            ></el-row
          >
          <el-row :gutter="20" class="info-row"
            ><el-col :span="8" v-if="selectedTask.start_time"
              ><div class="info-item">
                <div class="info-label">
                  {{ $t("tasks-TaskList-19c298d949224c78d-56") }}
                </div>
                <div class="info-value">{{ selectedTask.start_time }}</div>
              </div></el-col
            >
            <el-col :span="8" v-if="selectedTask.end_time"
              ><div class="info-item">
                <div class="info-label">
                  {{ $t("tasks-TaskList-19c298d949224c78d-57") }}
                </div>
                <div class="info-value">{{ selectedTask.end_time }}</div>
              </div></el-col
            >
            <el-col :span="8" v-if="selectedTask.created_by"
              ><div class="info-item">
                <div class="info-label">
                  {{ $t("tasks-TaskList-19c298d949224c78d-58") }}
                </div>
                <div class="info-value">{{ selectedTask.created_by }}</div>
              </div></el-col
            ></el-row
          >
          <el-row
            :gutter="20"
            class="info-row"
            v-if="
              selectedTask.total_items !== undefined ||
              selectedTask.completed_items !== undefined ||
              selectedTask.failed_items !== undefined
            "
            ><el-col :span="8" v-if="selectedTask.total_items !== undefined"
              ><div class="info-item">
                <div class="info-label">
                  {{ $t("tasks-TaskList-19c298d949224c78d-59") }}
                </div>
                <div class="info-value">{{ selectedTask.total_items }}</div>
              </div></el-col
            >
            <el-col :span="8" v-if="selectedTask.completed_items !== undefined"
              ><div class="info-item">
                <div class="info-label">
                  {{ $t("tasks-TaskList-19c298d949224c78d-60") }}
                </div>
                <div class="info-value">{{ selectedTask.completed_items }}</div>
              </div></el-col
            >
            <el-col :span="8" v-if="selectedTask.failed_items !== undefined"
              ><div class="info-item">
                <div class="info-label">
                  {{ $t("tasks-TaskList-19c298d949224c78d-61") }}
                </div>
                <div class="info-value">{{ selectedTask.failed_items }}</div>
              </div></el-col
            ></el-row
          >
          <div
            v-if="selectedTask.error_message"
            class="error-message-container"
          >
            <div class="info-label">
              {{ $t("tasks-TaskList-19c298d949224c78d-62") }}
            </div>
            <el-alert type="error" :closable="false" show-icon
              ><p>{{ selectedTask.error_message }}</p></el-alert
            >
          </div>
          <div class="progress-section">
            <div class="progress-header">
              <span>{{ $t("tasks-TaskList-19c298d949224c78d-63") }}</span>
              <span v-if="selectedTask.completed_items !== undefined"
                >{{ selectedTask.completed_items }} /
                {{ selectedTask.total_items || 0 }}
                <span v-if="selectedTask.failed_items > 0" class="error-text"
                  >{{ $t("tasks-TaskList-19c298d949224c78d-64") }}
                  {{ selectedTask.failed_items }} )
                </span></span
              >
            </div>
            <el-progress
              :percentage="selectedTask.progress || 0"
              :status="getProgressStatus(selectedTask.status)"
              :stroke-width="15"
              :format="(percentage) => percentage.toFixed(1) + '%'"
            /></div
        ></el-card>
        <!-- 内容网格布局 -->
        <div class="detail-grid">
          <!-- 任务参数 -->
          <el-card class="detail-card" shadow="hover"
            ><template #header
              ><div class="card-header">
                <h3>{{ $t("tasks-TaskList-19c298d949224c78d-65") }}</h3>
              </div></template
            >
            <div class="card-content parameters-content">
              <el-descriptions :column="2" border size="small"
                ><el-descriptions-item
                  v-if="
                    selectedTask.parameters && selectedTask.parameters.keywords
                  "
                  :label="$t('tasks-TaskList-19c298d949224c78d-66')"
                  :span="2"
                  >{{
                    formatKeywords(selectedTask.parameters.keywords)
                  }}</el-descriptions-item
                >
                <el-descriptions-item
                  v-if="
                    selectedTask.parameters && selectedTask.parameters.cities
                  "
                  :label="$t('tasks-TaskList-19c298d949224c78d-67')"
                  :span="selectedTask.parameters.regions ? 1 : 2"
                  >{{
                    formatCities(selectedTask.parameters.cities)
                  }}</el-descriptions-item
                >
                <el-descriptions-item
                  v-if="
                    selectedTask.parameters && selectedTask.parameters.regions
                  "
                  :label="$t('tasks-TaskList-19c298d949224c78d-68')"
                  :span="selectedTask.parameters.cities ? 1 : 2"
                  >{{
                    formatRegions(selectedTask.parameters.regions)
                  }}</el-descriptions-item
                >
                <el-descriptions-item
                  v-if="
                    selectedTask.parameters &&
                    selectedTask.parameters.date_ranges
                  "
                  :label="$t('tasks-TaskList-19c298d949224c78d-69')"
                  :span="2"
                  >{{
                    formatDateRanges(selectedTask.parameters.date_ranges)
                  }}</el-descriptions-item
                >
                <el-descriptions-item
                  v-if="selectedTask.parameters && selectedTask.parameters.days"
                  :label="$t('tasks-TaskList-19c298d949224c78d-70')"
                  :span="1"
                  >{{ $t("tasks-TaskList-19c298d949224c78d-71") }}
                  {{ selectedTask.parameters.days }}
                  {{
                    $t("tasks-TaskList-19c298d949224c78d-72")
                  }}</el-descriptions-item
                >
                <el-descriptions-item
                  v-if="
                    selectedTask.parameters &&
                    selectedTask.parameters.year_range
                  "
                  :label="$t('tasks-TaskList-19c298d949224c78d-73')"
                  :span="1"
                  >{{ selectedTask.parameters.year_range[0] }}
                  {{ $t("tasks-TaskList-19c298d949224c78d-74") }}
                  {{
                    selectedTask.parameters.year_range[1]
                  }}</el-descriptions-item
                >
                <el-descriptions-item
                  v-if="
                    selectedTask.parameters &&
                    selectedTask.parameters.start_date &&
                    selectedTask.parameters.end_date
                  "
                  :label="$t('tasks-TaskList-19c298d949224c78d-75')"
                  :span="1"
                  >{{ selectedTask.parameters.start_date }}
                  {{ $t("tasks-TaskList-19c298d949224c78d-76") }}
                  {{ selectedTask.parameters.end_date }}</el-descriptions-item
                >
                <el-descriptions-item
                  v-if="
                    selectedTask.parameters && selectedTask.parameters.datelists
                  "
                  :label="$t('tasks-TaskList-19c298d949224c78d-77')"
                  :span="2"
                  >{{
                    formatDatelists(selectedTask.parameters.datelists)
                  }}</el-descriptions-item
                >
                <el-descriptions-item
                  v-if="
                    selectedTask.parameters &&
                    selectedTask.parameters.batch_size
                  "
                  :label="$t('tasks-TaskList-19c298d949224c78d-78')"
                  :span="1"
                  >{{
                    selectedTask.parameters.batch_size
                  }}</el-descriptions-item
                >
                <el-descriptions-item
                  v-if="selectedTask.parameters && selectedTask.parameters.kind"
                  :label="$t('tasks-TaskList-19c298d949224c78d-79')"
                  :span="1"
                  >{{
                    selectedTask.parameters.kind === "all"
                      ? $t("tasks-TaskList-19c298d949224c78d-80")
                      : selectedTask.parameters.kind === "pc"
                        ? "PC"
                        : $t("tasks-TaskList-19c298d949224c78d-81")
                  }}</el-descriptions-item
                >
                <el-descriptions-item
                  v-if="
                    selectedTask.parameters &&
                    selectedTask.parameters.output_format
                  "
                  :label="$t('tasks-TaskList-19c298d949224c78d-82')"
                  :span="1"
                  >{{ formatLabel(selectedTask.parameters.output_format) }}</el-descriptions-item
                >
                <el-descriptions-item
                  v-if="selectedTask.parameters && selectedTask.parameters.output_dir"
                  label="输出目录"
                  :span="2"
                  >{{ selectedTask.parameters.output_dir }}</el-descriptions-item
                >
                <el-descriptions-item
                  v-if="selectedTask.parameters && selectedTask.parameters.output_name"
                  label="自定义文件名"
                  :span="1"
                  >{{ selectedTask.parameters.output_name }}</el-descriptions-item
                ></el-descriptions
              >
            </div></el-card
          >
          <!-- 输出文件 -->
          <el-card class="detail-card" shadow="hover"
            ><template #header
              ><div class="card-header">
                <h3>{{ $t("tasks-TaskList-19c298d949224c78d-83") }}</h3>
              </div></template
            >
            <div class="card-content files-content">
              <div
                v-if="
                  selectedTask.output_files &&
                  selectedTask.output_files.length > 0
                "
                class="files-container"
              >
                <el-table
                  :data="selectedTask.output_files"
                  style="width: 100%"
                  size="small"
                  max-height="150"
                  ><el-table-column
                    :label="$t('tasks-TaskList-19c298d949224c78d-84')"
                    prop=""
                    min-width="200"
                    show-overflow-tooltip
                    ><template #default="scope"
                      ><div class="file-path">
                        <el-icon><Document /></el-icon>
                        <span>{{ getShortPath(scope.row) }}</span>
                      </div></template
                    ></el-table-column
                  >
                  <el-table-column
                    :label="$t('tasks-TaskList-19c298d949224c78d-85')"
                    width="100"
                    fixed="right"
                    ><template #default="scope"
                      ><el-button
                        type="primary"
                        size="small"
                        @click="downloadSingleFile(scope.row)"
                        plain
                        ><el-icon><Download /></el-icon>
                        {{
                          $t("tasks-TaskList-19c298d949224c78d-86")
                        }}</el-button
                      ></template
                    ></el-table-column
                  ></el-table
                >
                <div class="download-all">
                  <el-button
                    type="primary"
                    @click="downloadTaskResult()"
                    :loading="downloading"
                    v-if="selectedTask.status === 'completed'"
                    size="small"
                    ><el-icon><Download /></el-icon>
                    {{ $t("tasks-TaskList-19c298d949224c78d-87") }}</el-button
                  >
                </div>
              </div>
              <el-empty
                v-else
                :description="$t('tasks-TaskList-19c298d949224c78d-88')"
                :image-size="50"
              /></div
          ></el-card>
          <!-- 检查点 -->
          <el-card class="detail-card" shadow="hover"
            ><template #header
              ><div class="card-header">
                <h3>{{ $t("tasks-TaskList-19c298d949224c78d-89") }}</h3>
              </div></template
            >
            <div class="card-content checkpoint-content">
              <div
                v-if="selectedTask.checkpoint_path"
                class="checkpoint-container"
              >
                <div class="checkpoint-path">
                  <span class="path-label">{{
                    $t("tasks-TaskList-19c298d949224c78d-90")
                  }}</span>
                  <el-tag size="small"
                    >{{
                      typeof selectedTask.checkpoint_path === "string"
                        ? getShortPath(selectedTask.checkpoint_path)
                        : $t("tasks-TaskList-19c298d949224c78d-91")
                    }}
                    <el-tooltip
                      v-if="typeof selectedTask.checkpoint_path === 'string'"
                      :content="selectedTask.checkpoint_path"
                      placement="top"
                      effect="light"
                      ><el-icon><InfoFilled /></el-icon></el-tooltip
                  ></el-tag>
                  <el-button
                    v-if="typeof selectedTask.checkpoint_path === 'string'"
                    type="primary"
                    size="small"
                    @click="
                      downloadCheckpointFile(selectedTask.checkpoint_path)
                    "
                    style="margin-left: 10px"
                    ><el-icon><Download /></el-icon>
                    {{ $t("tasks-TaskList-19c298d949224c78d-92") }}</el-button
                  >
                </div>
                <div
                  v-if="typeof selectedTask.checkpoint_path === 'object'"
                  class="checkpoint-data"
                >
                  <h4>{{ $t("tasks-TaskList-19c298d949224c78d-93") }}</h4>
                  <pre>{{
                    JSON.stringify(selectedTask.checkpoint_path, null, 2)
                  }}</pre>
                </div>
              </div>
              <el-empty
                v-else
                :description="$t('tasks-TaskList-19c298d949224c78d-94')"
                :image-size="50"
              /></div
          ></el-card>
          <!-- 任务日志 -->
          <el-card class="detail-card" shadow="hover"
            ><template #header
              ><div class="card-header">
                <h3>{{ $t("tasks-TaskList-19c298d949224c78d-95") }}</h3>
              </div></template
            >
            <div class="card-content logs-content">
              <div
                v-if="selectedTask.logs && selectedTask.logs.length > 0"
                class="logs-container"
              >
                <el-table
                  :data="selectedTask.logs"
                  style="width: 100%"
                  size="small"
                  max-height="150"
                  ><el-table-column
                    :label="$t('tasks-TaskList-19c298d949224c78d-96')"
                    prop="timestamp"
                    width="150" />
                  <el-table-column
                    :label="$t('tasks-TaskList-19c298d949224c78d-97')"
                    prop="log_level"
                    width="80"
                    ><template #default="scope"
                      ><el-tag
                        :type="getLogLevelTag(scope.row.log_level)"
                        size="small"
                        >{{ scope.row.log_level }}</el-tag
                      ></template
                    ></el-table-column
                  >
                  <el-table-column
                    :label="$t('tasks-TaskList-19c298d949224c78d-98')"
                    prop="message"
                    min-width="250"
                    show-overflow-tooltip
                /></el-table>
              </div>
              <div v-else-if="selectedTask.error_message" class="error-message">
                <el-alert type="error" :closable="false" show-icon
                  ><p>{{ selectedTask.error_message }}</p></el-alert
                >
              </div>
              <el-empty
                v-else
                :description="$t('tasks-TaskList-19c298d949224c78d-99')"
                :image-size="50"
              /></div
          ></el-card>
        </div>
      </div>
      <template #footer
        ><div class="dialog-footer">
          <el-button @click="taskDetailDialogVisible = false">{{
            $t("tasks-TaskList-19c298d949224c78d-100")
          }}</el-button>
          <el-button
            type="success"
            @click="restartTask(selectedTask)"
            v-if="
              selectedTask &&
              (selectedTask.status === 'failed' ||
                selectedTask.status === 'cancelled')
            "
            >{{ $t("tasks-TaskList-19c298d949224c78d-101") }}</el-button
          >
          <el-button
            type="danger"
            @click="cancelTask(selectedTask)"
            v-if="
              selectedTask &&
              (selectedTask.status === 'pending' ||
                selectedTask.status === 'running')
            "
            >{{ $t("tasks-TaskList-19c298d949224c78d-102") }}</el-button
          >
        </div></template
      ></el-dialog
    >
  </div>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { ref, onMounted, watch, onUnmounted, computed } from "vue";

const { t, locale } = useI18n();
import { ElMessage } from "element-plus";
import axios from "axios";
import { Download, InfoFilled, Document } from "@element-plus/icons-vue";
import {
  ArrowDown,
  View,
  RefreshRight,
  Close,
  Loading,
} from "@element-plus/icons-vue";
import { webSocketService } from "@/utils/websocket";

// 定义任务接口
interface TaskParameter {
  keywords?: string[] | { value: string }[];
  cities?: Record<string, any>;
  regions?: string[];
  date_ranges?: string[][];
  days?: number;
  year_range?: string[];
  start_date?: string;
  end_date?: string;
  datelists?: string[];
  batch_size?: number;
  output_format?: string;
  output_dir?: string;
  output_name?: string;
  resume?: boolean;
  task_id?: string;
  [key: string]: any;
}

interface Task {
  taskId: string;
  taskType: string;
  status: string;
  progress: number;
  parameters: TaskParameter;
  createdAt: string;
  updatedAt: string;
  priority: number;
  result?: string | null;
  checkpoint_path?: string | object;
  output_files?: string[];
  completed_items?: number;
  total_items?: number;
  failed_items?: number;
  task_name?: string;
  error_message?: string;
  logs?: { timestamp: string; log_level: string; message: string }[];
  [key: string]: any;
}

const API_BASE_URL = "http://127.0.0.1:5001/api";
const useMockData = ref(false);

// 输出格式标签映射
const FORMAT_LABELS: Record<string, string> = {
  csv: 'CSV (.csv)',
  excel: 'Excel (.xlsx)',
  json: 'JSON (.json)',
  dta: 'Stata (.dta)',
  parquet: 'Parquet (.parquet)',
  sql: 'SQLite (.sqlite)',
};
const formatLabel = (fmt: string) => FORMAT_LABELS[fmt] || fmt.toUpperCase();

// 模拟任务数据
const mockTasks: Task[] = [
  {
    taskId: "TASK-20230615-001",
    taskType: "index_trend",
    status: "completed",
    progress: 100,
    createdAt: "2023-06-15 09:15:30",
    updatedAt: "2023-06-15 10:30:45",
    parameters: {
      keywords: [
        t("tasks-TaskList-19c298d949224c78d-103"),
        t("tasks-TaskList-19c298d949224c78d-104"),
        "iPhone",
      ],
      date_ranges: [["2023-01-01", "2023-06-01"]],
      regions: [t("tasks-TaskList-19c298d949224c78d-105")],
    },
    priority: 5,
    result: "index_trend_20230615001.xlsx",
    output_files: [],
  },
  {
    taskId: "TASK-20230615-002",
    taskType: "search_index",
    status: "running",
    progress: 65,
    createdAt: "2023-06-15 10:20:15",
    updatedAt: "2023-06-15 10:50:17",
    parameters: {
      keywords: [
        t("tasks-TaskList-19c298d949224c78d-106"),
        t("tasks-TaskList-19c298d949224c78d-107"),
      ],
      date_ranges: [["2023-03-01", "2023-06-01"]],
      regions: [
        t("tasks-TaskList-19c298d949224c78d-108"),
        t("tasks-TaskList-19c298d949224c78d-109"),
        t("tasks-TaskList-19c298d949224c78d-110"),
      ],
    },
    priority: 5,
    result: null,
    output_files: [],
  },
  {
    taskId: "TASK-20230614-001",
    taskType: "province_rank",
    status: "failed",
    progress: 45,
    createdAt: "2023-06-14 15:12:40",
    updatedAt: "2023-06-14 16:45:21",
    parameters: {
      keywords: [
        t("tasks-TaskList-19c298d949224c78d-111"),
        t("tasks-TaskList-19c298d949224c78d-112"),
      ],
      date_ranges: [["2023-05-01", "2023-06-10"]],
      regions: [],
    },
    priority: 5,
    result: null,
    output_files: [],
  },
];

// 任务列表数据
const tasks = ref<Task[]>([]);
const loading = ref(false);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(10);

// 搜索和筛选
const searchKeyword = ref("");
const taskTypeFilter = ref("");
const statusFilter = ref("");

// 任务详情
const taskDetailDialogVisible = ref(false);
const selectedTask = ref<Task | null>(null);
const downloading = ref(false);
let refreshInterval: any = null;

// 加载任务列表
const loadTasks = async () => {
  loading.value = true;
  try {
    if (useMockData.value) {
      let filteredTasks = [...mockTasks];
      if (searchKeyword.value) {
        const keyword = searchKeyword.value.toLowerCase();
        filteredTasks = filteredTasks.filter((task) => {
          const keywords = task.parameters.keywords;
          if (Array.isArray(keywords)) {
            return keywords.some((k) => {
              if (typeof k === "object" && k.value) {
                return k.value.toLowerCase().includes(keyword);
              }
              return String(k).toLowerCase().includes(keyword);
            });
          }
          return task.taskId.toLowerCase().includes(keyword);
        });
      }
      if (taskTypeFilter.value) {
        filteredTasks = filteredTasks.filter(
          (task) => task.taskType === taskTypeFilter.value,
        );
      }
      if (statusFilter.value) {
        filteredTasks = filteredTasks.filter(
          (task) => task.status === statusFilter.value,
        );
      }
      total.value = filteredTasks.length;
      const start = (currentPage.value - 1) * pageSize.value;
      const end = start + pageSize.value;
      tasks.value = filteredTasks.slice(start, end);
    } else {
      const params: Record<string, any> = {};
      if (pageSize.value) params.limit = String(pageSize.value);
      if (currentPage.value)
        params.offset = String((currentPage.value - 1) * pageSize.value);
      if (searchKeyword.value) params.keyword = searchKeyword.value;
      if (taskTypeFilter.value) params.task_type = taskTypeFilter.value;
      if (statusFilter.value) params.status = statusFilter.value;
      const response = await axios.get(`${API_BASE_URL}/task/list`, { params });
      if (response.data.code === 10000) {
        const responseTasks = response.data.data.tasks || [];
        total.value = response.data.data.total || 0;
        tasks.value = responseTasks.map((task: any) => {
          task.taskId = task.task_id || task.taskId || "";
          task.taskType = task.task_type || task.taskType || "";
          task.createdAt = task.create_time || task.createdAt || "";
          task.updatedAt = task.update_time || task.updatedAt || "";
          task.status = task.status || "pending";
          task.progress = task.progress || 0;
          if (!task.parameters) {
            task.parameters = {};
          } else if (typeof task.parameters === "string") {
            try {
              task.parameters = JSON.parse(task.parameters);
            } catch (e) {
              console.error(
                `${t("tasks-TaskList-19c298d949224c78d-113")}${task.taskId}${t("tasks-TaskList-19c298d949224c78d-114")}`,
                e,
              );
              task.parameters = {};
            }
          }
          if (task.output_files === null || task.output_files === undefined) {
            task.output_files = [];
          } else if (typeof task.output_files === "string") {
            try {
              task.output_files = JSON.parse(task.output_files);
            } catch (e) {
              task.output_files = [task.output_files];
            }
          }
          if (!Array.isArray(task.output_files)) {
            task.output_files = [task.output_files];
          }
          return task;
        });
      } else {
        ElMessage.error(
          `${t("tasks-TaskList-19c298d949224c78d-115")}${response.data.msg}`,
        );
      }
    }
  } catch (error) {
    ElMessage.error(t("tasks-TaskList-19c298d949224c78d-116"));
    tasks.value = [];
  } finally {
    loading.value = false;
    if (tasks.value && tasks.value.length > 0) {
      tasks.value = [...tasks.value];
    }
  }
};

// 重置筛选条件
const resetFilters = () => {
  searchKeyword.value = "";
  taskTypeFilter.value = "";
  statusFilter.value = "";
  currentPage.value = 1;
  loadTasks();
};

// 处理分页变化
const handleSizeChange = (size: number) => {
  pageSize.value = size;
  loadTasks();
};

const handleCurrentChange = (page: number) => {
  currentPage.value = page;
  loadTasks();
};

// 查看任务详情
const viewTaskDetail = async (task: Task) => {
  selectedTask.value = task;
  await loadTaskDetail(task.taskId);
  taskDetailDialogVisible.value = true;
};

// 加载任务详情
const loadTaskDetail = async (taskId: string) => {
  if (!taskId) return;
  try {
    const response = await axios.get(`${API_BASE_URL}/task/${taskId}`);
    if (response.data.code === 10000 && selectedTask.value) {
      const taskData = response.data.data;
      // 确保 output_files 是数组
      if (typeof taskData.output_files === 'string') {
        try {
          taskData.output_files = JSON.parse(taskData.output_files);
        } catch (e) {
          taskData.output_files = [taskData.output_files];
        }
      }
      
      Object.assign(selectedTask.value, taskData);
    } else {
      console.error(
        t("tasks-TaskList-19c298d949224c78d-117"),
        response.data.msg,
      );
    }
  } catch (error) {
    console.error(t("tasks-TaskList-19c298d949224c78d-118"), error);
  }
};

// 对话框打开处理
const handleDialogOpen = () => {
  if (selectedTask.value && selectedTask.value.taskId) {
    loadTaskDetail(selectedTask.value.taskId);
  }
};

// 重试任务
const restartTask = async (task: Task | null = null) => {
  if (!task && !selectedTask.value) return;

  const targetTask = task || selectedTask.value;
  if (!targetTask) return;

  if (useMockData.value) {
    ElMessage.success(t("tasks-TaskList-19c298d949224c78d-119"));
    const taskIndex = mockTasks.findIndex(
      (t) => t.taskId === targetTask.taskId,
    );
    if (taskIndex !== -1) {
      mockTasks[taskIndex].status = "pending";
      mockTasks[taskIndex].progress = 0;
      mockTasks[taskIndex].updatedAt = new Date()
        .toISOString()
        .replace("T", " ")
        .substring(0, 19);
    }
    loadTasks();
  } else {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/task/${targetTask.taskId}/resume`,
      );
      if (response.data.code === 10000) {
        ElMessage.success(
          t("tasks-TaskList-19c298d949224c78d-120"),
        );
        loadTasks();
      } else {
        ElMessage.error(
          `${t("tasks-TaskList-19c298d949224c78d-121")}${response.data.msg || response.data.message}`,
        );
      }
    } catch (error) {
      ElMessage.error(t("tasks-TaskList-19c298d949224c78d-122"));
      console.error(
        t("tasks-TaskList-19c298d949224c78d-123"),
        error,
      );
    }
  }
};

// 取消任务
const cancelTask = async (task: Task | null = null) => {
  if (!task && !selectedTask.value) return;

  const targetTask = task || selectedTask.value;
  if (!targetTask) return;

  if (useMockData.value) {
    ElMessage.success(t("tasks-TaskList-19c298d949224c78d-124"));
    const taskIndex = mockTasks.findIndex(
      (t) => t.taskId === targetTask.taskId,
    );
    if (taskIndex !== -1) {
      mockTasks[taskIndex].status = "cancelled";
      mockTasks[taskIndex].updatedAt = new Date()
        .toISOString()
        .replace("T", " ")
        .substring(0, 19);
    }
    loadTasks();
  } else {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/task/${targetTask.taskId}/cancel`,
      );
      if (response.data.code === 10000) {
        ElMessage.success(
          t("tasks-TaskList-19c298d949224c78d-125"),
        );
        loadTasks();
      } else {
        ElMessage.error(
          `${t("tasks-TaskList-19c298d949224c78d-126")}${response.data.msg || response.data.message}`,
        );
      }
    } catch (error) {
      ElMessage.error(t("tasks-TaskList-19c298d949224c78d-127"));
      console.error(
        t("tasks-TaskList-19c298d949224c78d-128"),
        error,
      );
    }
  }
};

// 下载任务结果
const downloadTaskResult = async (task: Task | null = null) => {
  if (!task && !selectedTask.value) return;

  const targetTask = task || selectedTask.value;
  if (!targetTask) return;

  downloading.value = true;

  try {
    if (!targetTask.output_files || !targetTask.output_files.length) {
      ElMessage.warning(t("tasks-TaskList-19c298d949224c78d-129"));
      downloading.value = false;
      return;
    }

    for (const filePath of targetTask.output_files) {
      await downloadSingleFile(filePath);
    }

    ElMessage.success(t("tasks-TaskList-19c298d949224c78d-130"));
    loadTasks();
  } catch (error) {
    ElMessage.error(t("tasks-TaskList-19c298d949224c78d-131"));
    console.error(t("tasks-TaskList-19c298d949224c78d-132"), error);
  } finally {
    downloading.value = false;
  }
};

// 下载单个文件
const downloadSingleFile = async (filePath: string) => {
  if (!filePath) return false;

  try {
    const fileName = filePath.split("/").pop();
    // 使用后端下载接口
    const downloadUrl = `${API_BASE_URL}/task/download?filePath=${encodeURIComponent(filePath)}`;
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.setAttribute("download", fileName || "output.csv");
    link.setAttribute("target", "_blank");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    return true;
  } catch (error) {
    ElMessage.error(t("tasks-TaskList-19c298d949224c78d-133"));
    console.error(t("tasks-TaskList-19c298d949224c78d-134"), error);
    return false;
  }
};

// 下载检查点文件
const downloadCheckpointFile = (checkpointPath: string) => {
  if (!checkpointPath) return;

  // 使用后端下载接口
  try {
    const fileName = checkpointPath.split("/").pop();
    const downloadUrl = `${API_BASE_URL}/task/download?filePath=${encodeURIComponent(checkpointPath)}`;
    const link = document.createElement("a");
    link.href = downloadUrl;
    link.setAttribute("download", fileName || "checkpoint.json");
    link.setAttribute("target", "_blank");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (error) {
    ElMessage.error(t("tasks-TaskList-1135"));
    console.error(t("tasks-TaskList-1136"), error);
  }
};

// 辅助函数
const translateTaskType = (type: string) => {
  const typeMap: Record<string, string> = {
    search_index: t("tasks-TaskList-19c298d949224c78d-137"),
    feed_index: t("tasks-TaskList-19c298d949224c78d-138"),
    word_graph: t("tasks-TaskList-19c298d949224c78d-139"),
    demographic_attributes: t(
      "tasks-TaskList-19c298d949224c78d-140",
    ),
    interest_profile: t("tasks-TaskList-19c298d949224c78d-141"),
    region_distribution: t("tasks-TaskList-19c298d949224c78d-142"),
  };
  return typeMap[type] || type;
};

const translateStatus = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: t("tasks-TaskList-19c298d949224c78d-143"),
    running: t("tasks-TaskList-19c298d949224c78d-144"),
    completed: t("tasks-TaskList-19c298d949224c78d-145"),
    failed: t("tasks-TaskList-19c298d949224c78d-146"),
    cancelled: t("tasks-TaskList-19c298d949224c78d-147"),
  };
  return statusMap[status] || status;
};

const getTaskTypeTag = (type: string) => {
  const typeMap: Record<string, string> = {
    search_index: "primary",
    feed_index: "success",
    word_graph: "warning",
    demographic_attributes: "danger",
    interest_profile: "info",
    region_distribution: "",
  };
  return typeMap[type] || "";
};

const getStatusTag = (status: string) => {
  const statusMap: Record<string, string> = {
    pending: "info",
    running: "warning",
    completed: "success",
    failed: "danger",
    cancelled: "info",
  };
  return statusMap[status] || "";
};

const getProgressStatus = (status: string) => {
  if (status === "completed") return "success";
  if (status === "failed") return "exception";
  if (status === "cancelled") return "warning";
  return "";
};

const getPriorityLabel = (priority: number) => {
  if (priority >= 8)
    return t("tasks-TaskList-19c298d949224c78d-148");
  if (priority >= 4)
    return t("tasks-TaskList-19c298d949224c78d-149");
  return t("tasks-TaskList-19c298d949224c78d-150");
};

const getShortPath = (path) => {
  if (!path) return "";
  if (path.length > 40) {
    const parts = path.split("/");
    const fileName = parts[parts.length - 1];
    const parentDir = parts[parts.length - 2] || "";
    return `.../${parentDir ? parentDir + "/" : ""}${fileName}`;
  }
  return path;
};

const formatKeywords = (keywords: any) => {
  if (Array.isArray(keywords)) {
    if (
      keywords.length > 0 &&
      typeof keywords[0] === "object" &&
      "value" in keywords[0]
    ) {
      return keywords.map((k) => k.value).join(", ");
    }
    return keywords.join(", ");
  }
  return keywords;
};

const formatCities = (cities: any) => {
  if (!cities) return "";
  try {
    if (typeof cities === "object" && !Array.isArray(cities)) {
      const cityNames = Object.values(cities).map(
        (city: any) => city.name || city.code || "",
      );
      return cityNames.join(", ");
    }
    if (Array.isArray(cities)) {
      return cities
        .map((city: any) => {
          if (typeof city === "object") return city.name || city.code || "";
          return String(city);
        })
        .join(", ");
    }
    return String(cities);
  } catch (error) {
    console.error(t("tasks-TaskList-19c298d949224c78d-151"), error);
    return String(cities);
  }
};

const formatRegions = (regions: string[]) => {
  if (!regions) return "";
  return regions.join(", ");
};

const formatDateRanges = (dateRanges: string[][]) => {
  if (!dateRanges || !dateRanges.length) return "";
  return dateRanges
    .map(
      (range) =>
        `${range[0]}${t("tasks-TaskList-19c298d949224c78d-152")}${range[1]}`,
    )
    .join("; ");
};

const formatDatelists = (datelists: string[]) => {
  if (!datelists || !datelists.length) return "";
  return datelists
    .map((date) => {
      if (date.length === 8) {
        return `${date.substring(0, 4)}-${date.substring(4, 6)}-${date.substring(6, 8)}`;
      }
      return date;
    })
    .join(", ");
};

// 自动刷新任务列表
const setupRefreshInterval = () => {
  if (refreshInterval) clearInterval(refreshInterval);
  refreshInterval = setInterval(() => {
    if (!taskDetailDialogVisible.value) {
      loadTasks();
    }
  }, 30000);
  return refreshInterval;
};

// 监听详情对话框关闭
watch(
  () => taskDetailDialogVisible.value,
  (newVal) => {
    if (!newVal && selectedTask.value) {
      loadTasks();
    }
  },
);

const startAutoRefresh = () => {
  if (!useMockData.value) {
    setupRefreshInterval();
  }
};

// 处理 WebSocket 实时更新
const handleWebSocketUpdate = (data) => {
  const {
    taskId,
    progress,
    status,
    completed_items,
    total_items,
    error_message,
  } = data;

  // 更新列表中的任务
  const taskIndex = tasks.value.findIndex((t) => t.taskId === taskId);
  if (taskIndex !== -1) {
    const task = tasks.value[taskIndex];
    if (progress !== undefined) task.progress = parseFloat(progress.toFixed(1));
    if (status !== undefined) task.status = status;
    if (completed_items !== undefined) task.completed_items = completed_items;
    if (total_items !== undefined) task.total_items = total_items;
    if (error_message !== undefined) task.error_message = error_message;
    task.updatedAt = new Date().toLocaleString();
  }

  // 如果是在详情弹窗中的任务，也同步更新
  if (selectedTask.value && selectedTask.value.taskId === taskId) {
    if (progress !== undefined)
      selectedTask.value.progress = parseFloat(progress.toFixed(1));
    if (status !== undefined) selectedTask.value.status = status;
    if (completed_items !== undefined)
      selectedTask.value.completed_items = completed_items;
    if (total_items !== undefined) selectedTask.value.total_items = total_items;
    if (error_message !== undefined)
      selectedTask.value.error_message = error_message;
    selectedTask.value.updatedAt = new Date().toLocaleString();
  }
};

onMounted(() => {
  loadTasks();
  startAutoRefresh();

  // 连接 WebSocket 并监听更新
  webSocketService.connect();
  webSocketService.on("task_update", handleWebSocketUpdate);
});

onUnmounted(() => {
  // 断开 WebSocket 并在组件卸载时移除监听
  webSocketService.off("task_update", handleWebSocketUpdate);

  // 清理定时器
  if (refreshInterval) {
    clearInterval(refreshInterval);
  }
});

defineExpose({
  loadTasks,
  startAutoRefresh,
});

const getLogLevelTag = (level: string) => {
  const levelMap: Record<string, string> = {
    INFO: "info",
    WARNING: "warning",
    ERROR: "danger",
    DEBUG: "success",
  };
  return levelMap[level] || "info";
};
</script>

<style scoped>
.task-list-container {
  padding: 20px;
}

.task-list-container h2 {
  margin-bottom: 20px;
  font-size: 24px;
  color: #4f46e5;
}

.search-bar {
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  background-color: var(--color-bg-subtle);
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.table-wrapper {
  margin-bottom: 20px;
  background-color: var(--color-bg-surface);
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.task-parameters {
  font-size: 13px;
}

.task-parameters div {
  margin-bottom: 5px;
}

.task-parameters div:last-child {
  margin-bottom: 0;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.loading-icon {
  font-size: 40px;
  color: #4f46e5;
  animation: rotate 1.5s linear infinite;
}

/* 任务详情对话框样式 */
:deep(.task-detail-dialog .el-dialog) {
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  margin: 0 auto !important;
  border-radius: 8px;
}

:deep(.task-detail-dialog .el-dialog__body) {
  padding: 15px;
  overflow-y: auto;
}

:deep(.task-detail-dialog .el-dialog__header) {
  padding: 12px 20px;
  margin: 0;
  border-bottom: 1px solid var(--el-border-color-lighter);
  background-color: var(--color-bg-subtle);
}

:deep(.task-detail-dialog .el-dialog__footer) {
  padding: 8px 20px;
  border-top: 1px solid var(--el-border-color-lighter);
  background-color: var(--color-bg-subtle);
}

.task-detail {
  padding: 0;
}

.info-card {
  margin-bottom: 15px;
  border-radius: 8px;
  background-color: var(--color-bg-surface);
  border: 1px solid var(--color-border);
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.task-id {
  font-size: 16px;
}

.task-id .label {
  font-weight: bold;
  margin-right: 8px;
}

.task-id .value {
  font-family: monospace;
  color: #606266;
}

.info-row {
  margin-bottom: 15px;
}

.info-item {
  margin-bottom: 10px;
}

.info-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 5px;
}

.info-value {
  font-size: 14px;
  color: #303133;
  font-weight: 500;
}

.progress-section {
  margin-top: 10px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}

.error-text {
  color: #f56c6c;
}

/* 网格布局 */
.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-gap: 15px;
}

.detail-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: var(--color-bg-surface);
  border: 1px solid var(--color-border);
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.card-content {
  overflow-y: auto;
  height: 150px;
}

.parameters-content {
  padding: 0;
}

.files-content {
  padding: 0;
}

.files-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.file-path {
  display: flex;
  align-items: center;
  gap: 8px;
}

.download-all {
  margin-top: 10px;
  display: flex;
  justify-content: flex-end;
}

.checkpoint-container {
  height: 100%;
}

.checkpoint-path {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.path-label {
  margin-right: 10px;
  font-weight: 500;
}

.checkpoint-data {
  margin-top: 10px;
  background-color: var(--color-bg-surface);
  border-radius: 4px;
  padding: 10px;
  border: 1px solid var(--color-border);
}

.checkpoint-data h4 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 14px;
  color: #4f46e5;
}

.checkpoint-data pre {
  margin: 0;
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 12px;
  max-height: 100px;
  overflow-y: auto;
  background-color: var(--color-bg-subtle);
  padding: 10px;
  border-radius: 4px;
}

.error-message {
  margin-bottom: 15px;
}

.error-message p {
  margin: 0;
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 12px;
}

.error-message-container {
  margin: 10px 0;
  padding: 5px 0;
}

.error-message-container .info-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 5px;
}

.error-message-container p {
  margin: 0;
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 12px;
}

.logs-content {
  padding: 10px;
}

.logs-container {
  height: 100%;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 响应式调整 */
@media screen and (max-width: 1200px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
}

/* Deep Theme Overrides for Descriptions */
:deep(.el-descriptions) {
  --el-descriptions-table-border: 1px solid var(--color-border);
  --el-descriptions-item-bordered-label-background: var(--color-bg-subtle);
}

:deep(.el-descriptions__body) {
  background-color: transparent !important;
  color: var(--color-text-primary);
}

:deep(.el-descriptions__label.el-descriptions__cell.is-bordered-label) {
  background-color: var(--color-bg-subtle) !important;
  color: var(--color-text-secondary);
  border-color: var(--color-border) !important;
  font-weight: 600;
}

:deep(.el-descriptions__content.el-descriptions__cell.is-bordered-content) {
  background-color: transparent !important;
  color: var(--color-text-primary);
  border-color: var(--color-border) !important;
}

:deep(.el-descriptions__table) {
  border-color: var(--color-border) !important;
}

:deep(.el-descriptions__table tr) {
  background-color: transparent !important;
}

:deep(.el-descriptions__table td), 
:deep(.el-descriptions__table th) {
  border-color: var(--color-border) !important;
}

/* Deep Theme Overrides for Tables in TaskList */
:deep(.el-table) {
  --el-table-bg-color: transparent !important;
  --el-table-tr-bg-color: transparent !important;
  --el-table-header-bg-color: var(--color-bg-subtle) !important;
  --el-table-row-hover-bg-color: var(--color-bg-subtle) !important;
  --el-table-border-color: var(--color-border) !important;
  background-color: transparent !important;
  color: var(--color-text-primary);
}

:deep(.el-table th.el-table__cell) {
  background-color: var(--color-bg-subtle) !important;
  color: var(--color-text-primary);
  font-weight: 600;
  border-bottom-color: var(--color-border) !important;
  border-right-color: var(--color-border) !important;
}

:deep(.el-table tr) {
  background-color: transparent !important;
}

:deep(.el-table td.el-table__cell) {
  background-color: transparent !important;
  border-bottom-color: var(--color-border) !important;
  border-right-color: var(--color-border) !important;
}

:deep(.el-table--border::after),
:deep(.el-table--group::after),
:deep(.el-table::before) {
  background-color: var(--color-border) !important;
}

:deep(.el-table__inner-wrapper::before) {
  background-color: var(--color-border) !important;
}
</style>
