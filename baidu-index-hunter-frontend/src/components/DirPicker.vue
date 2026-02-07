<template>
  <div class="dir-picker">
    <!-- 输入框 + 浏览按钮 -->
    <div class="dir-picker-input">
      <el-input
        :model-value="modelValue"
        :placeholder="placeholder"
        clearable
        @update:model-value="$emit('update:modelValue', $event)"
      />
      <el-button type="primary" plain @click="openBrowser">浏览</el-button>
    </div>
    <div v-if="hint" class="dir-picker-hint">{{ hint }}</div>

    <!-- 目录浏览对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="选择文件夹"
      width="600px"
      :close-on-click-modal="false"
      append-to-body
    >
      <div v-loading="loading" class="dir-browser">
        <!-- 路径输入（可编辑，回车跳转） -->
        <div class="dir-nav-path">
          <el-input
            v-model="inputPath"
            size="small"
            placeholder="输入路径后按回车跳转"
            @keyup.enter="navigateTo(inputPath)"
          >
            <template #prepend>路径</template>
            <template #append>
              <el-button @click="navigateTo(inputPath)">跳转</el-button>
            </template>
          </el-input>
        </div>

        <!-- 工具栏 -->
        <div class="dir-toolbar">
          <el-button size="small" :disabled="!parentPath" @click="goParent">⬆ 上级目录</el-button>
          <el-button size="small" @click="refresh">刷新</el-button>
          <el-button size="small" type="primary" plain @click="showNewDir = !showNewDir">+ 新建文件夹</el-button>
        </div>

        <!-- 新建文件夹 -->
        <div v-if="showNewDir" class="dir-new-folder">
          <el-input
            v-model="newFolderName"
            size="small"
            placeholder="输入新文件夹名称"
            @keyup.enter="createFolder"
            style="flex: 1"
          />
          <el-button size="small" type="primary" @click="createFolder" :disabled="!newFolderName.trim()">创建</el-button>
          <el-button size="small" @click="showNewDir = false; newFolderName = ''">取消</el-button>
        </div>

        <!-- 目录列表 -->
        <div class="dir-list">
          <div
            v-for="d in dirs"
            :key="d"
            class="dir-item"
            @dblclick="navigateTo(currentPath + '/' + d)"
            @click="selectedSubDir = d"
            :class="{ 'is-selected': selectedSubDir === d }"
          >
            <span class="dir-item-icon">📁</span>
            <span class="dir-item-name">{{ d }}</span>
            <span class="dir-item-hint">双击进入</span>
          </div>
          <div v-if="dirs.length === 0" class="dir-empty">
            此目录下无子文件夹（可点击"新建文件夹"创建）
          </div>
        </div>

        <!-- 已选路径 -->
        <div class="dir-selected-hint">
          当前选中: <strong>{{ currentPath }}</strong>
        </div>
      </div>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmSelect">选择此目录</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  modelValue: string
  placeholder?: string
  hint?: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
}>()

const dialogVisible = ref(false)
const loading = ref(false)
const currentPath = ref('')
const inputPath = ref('')
const parentPath = ref<string | null>(null)
const dirs = ref<string[]>([])
const selectedSubDir = ref('')
const showNewDir = ref(false)
const newFolderName = ref('')

import { apiBase } from '@/config/api'

/** 打开浏览器对话框 */
const openBrowser = async () => {
  selectedSubDir.value = ''
  showNewDir.value = false
  newFolderName.value = ''
  await loadDir(props.modelValue || '')
  dialogVisible.value = true
}

/** 加载目录 */
const loadDir = async (path: string) => {
  loading.value = true
  try {
    const res = await fetch(`${apiBase}/api/config/browse_dir?path=${encodeURIComponent(path)}`)
    const data = await res.json()
    if (data.code === 10000 && data.data) {
      currentPath.value = data.data.current
      inputPath.value = data.data.current
      parentPath.value = data.data.parent
      dirs.value = data.data.dirs
      selectedSubDir.value = ''
    } else {
      ElMessage.warning(data.msg || '无法访问该目录')
    }
  } catch {
    ElMessage.error('浏览目录失败，请检查后端服务')
  } finally {
    loading.value = false
  }
}

const navigateTo = (path: string) => {
  if (path.trim()) loadDir(path.trim())
}

const goParent = () => {
  if (parentPath.value) loadDir(parentPath.value)
}

const refresh = () => loadDir(currentPath.value)

/** 新建文件夹 */
const createFolder = async () => {
  const name = newFolderName.value.trim()
  if (!name) return
  const newPath = currentPath.value + '/' + name
  try {
    const res = await fetch(`${apiBase}/api/config/validate_path`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path: newPath, create: true })
    })
    const data = await res.json()
    if (data.code === 10000) {
      newFolderName.value = ''
      showNewDir.value = false
      await loadDir(currentPath.value)
      ElMessage.success(`文件夹 "${name}" 已创建`)
    } else {
      ElMessage.error(data.msg || '创建失败')
    }
  } catch {
    ElMessage.error('创建文件夹失败')
  }
}

/** 确认选择 */
const confirmSelect = () => {
  emit('update:modelValue', currentPath.value)
  dialogVisible.value = false
}
</script>

<style scoped>
.dir-picker-input {
  display: flex;
  gap: 8px;
  align-items: center;
}
.dir-picker-input .el-input {
  flex: 1;
}
.dir-picker-hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

/* --- 对话框内部样式 --- */
.dir-browser {
  min-height: 300px;
}
.dir-nav-path {
  margin-bottom: 10px;
}
.dir-toolbar {
  margin-bottom: 10px;
  display: flex;
  gap: 8px;
  align-items: center;
}
.dir-new-folder {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 10px;
  padding: 8px 12px;
  background: #fafafa;
  border-radius: 6px;
}
.dir-list {
  border: 1px solid #ebeef5;
  border-radius: 6px;
  max-height: 320px;
  overflow-y: auto;
  margin-bottom: 10px;
}
.dir-item {
  padding: 9px 14px;
  cursor: pointer;
  border-bottom: 1px solid #f5f7fa;
  user-select: none;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background 0.15s;
}
.dir-item:hover {
  background: #ecf5ff;
}
.dir-item.is-selected {
  background: #e1effe;
}
.dir-item:last-child {
  border-bottom: none;
}
.dir-item-icon {
  flex-shrink: 0;
}
.dir-item-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.dir-item-hint {
  font-size: 12px;
  color: #c0c4cc;
  opacity: 0;
  transition: opacity 0.15s;
}
.dir-item:hover .dir-item-hint {
  opacity: 1;
}
.dir-empty {
  padding: 32px 24px;
  text-align: center;
  color: #909399;
  font-size: 13px;
}
.dir-selected-hint {
  padding: 8px 12px;
  background: #ecf5ff;
  border-radius: 6px;
  font-size: 13px;
  color: #606266;
  word-break: break-all;
}
</style>
