<template>
  <div class="logs-viewport">
    <!-- Atmospheric Background Layers -->
    <div class="glow-layer"></div>
    <div class="grid-overlay"></div>

    <div class="main-container">
      <!-- High-Density Unified Header -->
      <header class="integrated-header">
        <div class="branding">
          <div class="system-tag">SYSTEM</div>
          <div class="nav-sep">/</div>
          <h1 class="title-primary">{{ $t('views.logs.title') }}</h1>
        </div>

        <div class="header-center">
          <div class="stream-badge" :class="{ 'is-live': connected }">
            <div class="badge-inner">
              <span class="pulse-ring"></span>
              <span class="status-dot"></span>
              <span class="status-text">{{ connected ? 'LIVE STREAM' : 'OFFLINE' }}</span>
            </div>
          </div>
        </div>

        <div class="header-right">
          <div class="engine-info">
            <span class="label">ENGINE:</span>
            <span class="value">HUNTER CORE v2.0</span>
          </div>
        </div>
      </header>

      <!-- The Log Console -->
      <main class="console-box shadow-2xl">
        <!-- Pixel-Perfect Aligned Toolbar -->
        <div class="console-controls glass-blur">
          <div class="primary-controls">
            <div class="control-unit search-unit">
              <el-input
                v-model="searchQuery"
                :placeholder="$t('views.logs.search_placeholder')"
                prefix-icon="Search"
                clearable
                class="saas-input"
              />
            </div>
            <div class="control-unit level-unit">
              <el-select 
                v-model="filterLevel" 
                class="saas-select"
                popper-class="saas-popper"
              >
                <template #prefix>
                  <el-icon><Filter /></el-icon>
                </template>
                <el-option :label="$t('views.logs.all_levels')" value="ALL" />
                <el-option label="INFO" value="INFO" />
                <el-option label="WARNING" value="WARNING" />
                <el-option label="ERROR" value="ERROR" />
                <el-option label="DEBUG" value="DEBUG" />
              </el-select>
            </div>
            
            <div class="control-unit toggle-unit">
              <el-tooltip :content="isPaused ? $t('views.logs.resume') : $t('views.logs.pause')" placement="top">
                <button 
                  class="saas-tool-btn" 
                  :class="{ 'is-warning': isPaused }"
                  @click="isPaused = !isPaused"
                >
                  <el-icon><VideoPause v-if="!isPaused" /><VideoPlay v-else /></el-icon>
                </button>
              </el-tooltip>
              <el-tooltip :content="$t('views.logs.auto_scroll')" placement="top">
                <button 
                  class="saas-tool-btn" 
                  :class="{ 'is-active': autoScroll }"
                  @click="autoScroll = !autoScroll"
                >
                  <el-icon><Bottom /></el-icon>
                </button>
              </el-tooltip>
            </div>
          </div>

          <div class="secondary-actions">
            <el-button 
              type="danger" 
              plain 
              class="saas-action-btn clear-btn"
              @click="clearLogs"
            >
              <el-icon><Delete /></el-icon>
              <span>{{ $t('views.logs.clear_btn') }}</span>
            </el-button>
            <el-button 
              type="primary" 
              class="saas-action-btn download-btn"
              @click="downloadLogs"
            >
              <el-icon><Download /></el-icon>
              <span>{{ $t('views.logs.download_log') }}</span>
            </el-button>
          </div>
        </div>

        <!-- High-Performance Log Area -->
        <div class="console-body" ref="terminalBody" @scroll="handleScroll">
          <div v-if="filteredLogs.length === 0" class="console-empty">
            <div class="empty-vector">
              <el-icon><Monitor /></el-icon>
              <div class="radar-ping"></div>
            </div>
            <p class="empty-text">Tracing active. Listening for system broadcasts...</p>
          </div>
          
          <div 
            v-for="(log, index) in filteredLogs" 
            :key="log.type === 'progress' ? `progress-${log.task_id}` : index" 
            class="log-row"
            :class="[log.level.toLowerCase(), { 'is-progress': log.type === 'progress' }]"
            :data-index="index"
          >
            <!-- Decorative track -->
            <div class="row-indicator"></div>
            <div class="row-content">
              <span class="meta-time">{{ log.time }}</span>
              <span class="meta-lvl">{{ log.type === 'progress' ? 'PROG' : log.level }}</span>
              <div class="meta-path" v-if="log.type !== 'progress'">
                <span class="path-name">{{ log.name }}</span>
                <span class="path-loc">{{ log.function }}:{{ log.line }}</span>
              </div>
              <span class="row-msg" v-html="highlightMessage(log.message, searchQuery)"></span>
            </div>
          </div>
        </div>

        <!-- Compact Footer Info Bar -->
        <footer class="console-info-bar">
          <div class="info-group">
            <div class="info-item">
              <span class="i-label">LIVE FLOW:</span>
              <span class="i-val highlight">{{ logSpeed }} tps</span>
            </div>
            <div class="info-item">
              <span class="i-label">BUFFER:</span>
              <span class="i-val">{{ logs.length }}</span>
            </div>
            <div class="info-item">
              <span class="i-label">VISIBLE:</span>
              <span class="i-val">{{ filteredLogs.length }}</span>
            </div>
          </div>
          <div class="info-timestamp">
            {{ new Date().toLocaleTimeString() }}
          </div>
        </footer>
      </main>
    </div>

    <!-- Smart Floating Copy Button -->
    <Transition name="pop-scale">
      <div 
        v-if="selectionMenu.visible" 
        class="smart-copy-btn"
        :style="{ left: selectionMenu.x + 'px', top: selectionMenu.y + 'px' }"
        @click.stop="copySelectedLogs"
      >
        <div class="glass-bg"></div>
        <div class="btn-content">
          <el-icon v-if="!copySuccess" class="action-icon"><CopyDocument /></el-icon>
          <el-icon v-else class="action-icon success"><Check /></el-icon>
          <span class="btn-text">
            {{ copySuccess ? $t('views.logs.copied') : $t('views.logs.copy_items', { count: selectedLogCount }) }}
          </span>
        </div>
      </div>
    </Transition>
  </div>
</template>


<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { io } from 'socket.io-client'
import { useI18n } from 'vue-i18n'
import { 
  Search, Delete, Download, VideoPause, VideoPlay, 
  Bottom, Monitor, Filter, CopyDocument, Check
} from '@element-plus/icons-vue'
import { saveAs } from 'file-saver'
import { ElMessage } from 'element-plus'
import { apiBase } from '@/config/api'

const { t: $t } = useI18n()

// WebSocket state
const connected = ref(false)
const socket = ref(null)
const logs = ref([])
const maxLogs = 1000 // Buffer limit

// UI State
const searchQuery = ref('')
const filterLevel = ref('ALL')
const isPaused = ref(false)
const autoScroll = ref(true)
const terminalBody = ref(null)
const logSpeed = ref(0)
let messageCount = 0
let speedTimer = null

// Selection & Copy State
const selectedLogCount = ref(0)
const selectionMenu = ref({ visible: false, x: 0, y: 0, logIndices: [] })
const copySuccess = ref(false)

// Filtering logic
const filteredLogs = computed(() => {
  return logs.value.filter(log => {
    const q = searchQuery.value.toLowerCase()
    return (!q || log.message.toLowerCase().includes(q) || log.name.toLowerCase().includes(q)) &&
           (filterLevel.value === 'ALL' || log.level === filterLevel.value)
  })
})

const handleScroll = () => {
  if (!terminalBody.value) return
  const { scrollTop, scrollHeight, clientHeight } = terminalBody.value
  autoScroll.value = scrollHeight - scrollTop - clientHeight < 50
  
  // Hide menu on scroll to prevent misalignment
  if (selectionMenu.value.visible) {
    clearSelectionMenu()
  }
}

const scrollToBottom = async () => {
  if (autoScroll.value && terminalBody.value) {
    await nextTick()
    terminalBody.value.scrollTop = terminalBody.value.scrollHeight
  }
}

const clearLogs = () => logs.value = []

// Selection Handling
const handleMouseUp = (event) => {
  const selection = window.getSelection()
  if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
    // Delay clearing to allow clicking the button itself
    // We handle button click separately, so if we clicked elsewhere, clear
    const target = event.target
    if (!target.closest('.smart-copy-btn')) {
      clearSelectionMenu()
    }
    return
  }

  // Check if selection is within log container
  if (!terminalBody.value.contains(selection.anchorNode)) return

  // Find start and end indices
  const range = selection.getRangeAt(0)
  const container = terminalBody.value
  
  // Find all log rows in the selection range
  const logRows = Array.from(container.querySelectorAll('.log-row'))
  const selectedIndices = []
  
  logRows.forEach((row, index) => {
    if (selection.containsNode(row, true)) {
      selectedIndices.push(index)
    }
  })

  // If we selected text inside a single row, add that row
  if (selectedIndices.length === 0) {
    let node = selection.anchorNode
    while (node && node !== container) {
      if (node.classList && node.classList.contains('log-row')) {
        const index = parseInt(node.getAttribute('data-index'))
        if (!isNaN(index)) selectedIndices.push(index)
        break
      }
      node = node.parentNode
    }
  }

  if (selectedIndices.length > 0) {
    const uniqueIndices = [...new Set(selectedIndices)].sort((a, b) => a - b)
    selectedLogCount.value = uniqueIndices.length
    selectionMenu.value = {
      visible: true,
      x: event.clientX,
      y: event.clientY - 20, // Position above cursor
      logIndices: uniqueIndices
    }
  } else {
    clearSelectionMenu()
  }
}

const clearSelectionMenu = () => {
  selectionMenu.value.visible = false
  selectedLogCount.value = 0
  copySuccess.value = false
}

const copySelectedLogs = async () => {
  if (selectedLogCount.value === 0) return

  const indices = selectionMenu.value.logIndices
  const content = indices.map(idx => {
    const l = filteredLogs.value[idx]
    if (!l) return ''
    return `${l.time} | ${l.level.padEnd(8)} | ${l.name}: ${l.message}`
  }).filter(Boolean).join('\n')

  try {
    await navigator.clipboard.writeText(content)
    copySuccess.value = true
    ElMessage.success({
      message: `${selectedLogCount.value} Logs Copied!`,
      type: 'success',
      duration: 2000,
      customClass: 'saas-notification'
    })
    
    // Auto hide after success
    setTimeout(() => {
      clearSelectionMenu()
    }, 1500)
  } catch (err) {
    ElMessage.error('Details copy failed')
  }
}

// Escape regex special characters
const escapeRegExp = (string) => {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// Highlight search query tokens
const highlightMessage = (text, query) => {
  if (!query || !text) return text
  const escapedQuery = escapeRegExp(query)
  const regex = new RegExp(`(${escapedQuery})`, 'gi')
  return text.replace(regex, '<span class="hl-token">$1</span>')
}

const downloadLogs = () => {
  const content = filteredLogs.value.map(l => 
    `${l.time} | ${l.level.padEnd(8)} | ${l.name}:${l.function}:${l.line} - ${l.message}`
  ).join('\n')
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  saveAs(blob, `hunter_logs_${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '_')}.log`)
}

const initSocket = () => {
  socket.value = io(apiBase)
  socket.value.on('connect', () => connected.value = true)
  socket.value.on('disconnect', () => connected.value = false)
  socket.value.on('system_log', (data) => {
    if (isPaused.value) return
    messageCount++
    
    // 进度类型日志: 覆盖上一条同类进度，实现"原地刷新"效果
    if (data.type === 'progress') {
      const lastIdx = findLastProgressIndex(data.task_id)
      if (lastIdx >= 0) {
        logs.value[lastIdx] = data
      } else {
        logs.value.push(data)
      }
    } else {
      logs.value.push(data)
    }
    
    if (logs.value.length > maxLogs) logs.value.shift()
    if (autoScroll.value) scrollToBottom()
  })
}

/** 从末尾向前查找同一 task_id 的最后一条 progress 日志的索引 */
const findLastProgressIndex = (taskId) => {
  for (let i = logs.value.length - 1; i >= 0; i--) {
    const entry = logs.value[i]
    if (entry.type === 'progress' && (!taskId || entry.task_id === taskId)) {
      return i
    }
  }
  return -1
}

onMounted(() => {
  initSocket()
  speedTimer = setInterval(() => { logSpeed.value = messageCount; messageCount = 0 }, 1000)
  document.addEventListener('mouseup', handleMouseUp)
})

onUnmounted(() => {
  if (socket.value) socket.value.disconnect()
  if (speedTimer) clearInterval(speedTimer)
  document.removeEventListener('mouseup', handleMouseUp)
})

watch(filteredLogs, () => { if (autoScroll.value) scrollToBottom() })
</script>


<style scoped>
/* Atmospheric Layers */
.logs-viewport {
  position: relative;
  min-height: calc(100vh - 120px);
  padding: 12px 24px;
  overflow: hidden;
  background-color: var(--color-bg-base);
}

.glow-layer {
  position: absolute;
  top: -10%;
  left: 50%;
  width: 100vw;
  height: 60vh;
  transform: translateX(-50%);
  background: radial-gradient(circle at 50% 0%, var(--color-primary-light), transparent 70%);
  opacity: 0.15;
  pointer-events: none;
}

.grid-overlay {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(var(--color-border) 1px, transparent 1px);
  background-size: 32px 32px;
  opacity: 0.12;
  mask-image: linear-gradient(to bottom, black, transparent);
  pointer-events: none;
}

.main-container {
  position: relative;
  z-index: 10;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 144px);
  gap: 12px;
}

/* Integrated Grand Header */
.integrated-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 48px;
  padding: 0 8px;
}

.branding {
  display: flex;
  align-items: center;
  gap: 10px;
}

.system-tag {
  background: var(--color-bg-subtle);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 800;
  color: var(--color-text-tertiary);
  letter-spacing: 0.1em;
}

.nav-sep { color: var(--color-border); font-size: 0.9rem; }

.title-primary {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--color-text-main);
  letter-spacing: -0.01em;
}

.stream-badge {
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border);
  padding: 4px 14px;
  border-radius: 20px;
  box-shadow: var(--shadow-sm);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.badge-inner {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-dot { width: 8px; height: 8px; border-radius: 50%; background: #94a3b8; }
.status-text { font-size: 0.75rem; font-weight: 700; color: var(--color-text-secondary); letter-spacing: 0.05em; }

.is-live { border-color: rgba(16, 185, 129, 0.3); background: rgba(16, 185, 129, 0.05); }
.is-live .status-dot { background: #10b981; box-shadow: 0 0 10px #10b981; }
.is-live .status-text { color: #059669; }

.pulse-ring {
  position: absolute; width: 8px; height: 8px; border-radius: 50%; opacity: 0; background: #10b981;
}
.is-live .pulse-ring { animation: ripple 2s infinite; }

@keyframes ripple { from { transform: scale(1); opacity: 0.5; } to { transform: scale(3); opacity: 0; } }

.engine-info { font-size: 0.7rem; color: var(--color-text-tertiary); display: flex; gap: 8px; }
.engine-info .value { color: var(--color-primary); font-weight: 700; }

/* The Console Prism */
.console-box {
  flex: 1;
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.console-controls {
  height: 60px;
  padding: 0 16px;
  background: var(--color-bg-subtle);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.primary-controls { display: flex; align-items: center; gap: 12px; }

/* Unified Unit Sizing */
.control-unit { height: 38px; display: flex; align-items: center; }

.search-unit { width: 280px; }
.level-unit { width: 140px; }

.saas-tool-btn {
  height: 38px;
  width: 38px;
  border-radius: 8px;
  border: 1px solid var(--color-border);
  background: var(--color-bg-surface);
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
  display: flex; align-items: center; justify-content: center;
  margin-left: 8px;
}

.saas-tool-btn:hover { background: var(--color-bg-subtle); border-color: var(--color-primary); color: var(--color-primary); }
.saas-tool-btn.is-active { background: var(--color-primary); border-color: var(--color-primary); color: white; }
.saas-tool-btn.is-warning { background: #fff7ed; border-color: #fb923c; color: #ea580c; }

.secondary-actions { display: flex; gap: 12px; }

.saas-action-btn { height: 38px; font-weight: 700; font-size: 0.85rem; border-radius: 10px; }

/* Terminal Content */
.console-body {
  flex: 1;
  background: #0d1117; /* High contrast but eye-friendly */
  overflow-y: auto;
  padding: 16px;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 13px;
  line-height: 1.7;
}

.console-body::-webkit-scrollbar { width: 8px; }
.console-body::-webkit-scrollbar-thumb { background: #30363d; border-radius: 10px; }

.log-row {
  display: flex;
  position: relative;
  padding: 4px 12px;
  border-radius: 6px;
  margin-bottom: 2px;
  transition: background 0.15s;
}

.log-row:hover { background: rgba(255, 255, 255, 0.04); }

.row-indicator {
  position: absolute; left: 0; top: 6px; bottom: 6px; width: 3px; border-radius: 0 4px 4px 0;
}

.row-content { display: flex; gap: 16px; color: #c9d1d9; }

.meta-time { color: #8b949e; flex-shrink: 0; font-variant-numeric: tabular-nums; }

.meta-lvl {
  width: 50px; text-align: center; font-weight: 800; font-size: 10px; border-radius: 4px; padding: 1px 4px; flex-shrink: 0;
}

.meta-path { display: flex; gap: 8px; font-size: 12px; color: #58a6ff; opacity: 0.8; flex-shrink: 0; }
.path-loc { color: #8b949e; opacity: 0.6; }

.row-msg { flex: 1; word-break: break-all; }

/* Themes for Rows */
.info .row-indicator { background: #4ade80; }
.info .meta-lvl { color: #4ade80; background: rgba(74, 222, 128, 0.15); }

/* Highlight Token Styling */
:deep(.hl-token) {
  background: rgba(234, 179, 8, 0.4); /* Amber highlight */
  color: #fffbdf;
  border-radius: 2px;
  padding: 0 2px;
  font-weight: 700;
  box-shadow: 0 0 4px rgba(234, 179, 8, 0.5);
}

.warning .row-indicator { background: #fbbf24; }
.warning .meta-lvl { color: #fbbf24; background: rgba(251, 191, 36, 0.15); }
.warning .row-msg { color: #fde68a; }

.error .row-indicator { background: #f87171; }
.error .meta-lvl { color: #f87171; background: rgba(248, 113, 113, 0.15); }
.error .row-msg { color: #fecaca; font-weight: 600; }

.debug .meta-lvl { color: #94a3b8; background: rgba(148, 163, 184, 0.1); }

/* Progress bar row — sticky highlight */
.is-progress {
  background: rgba(56, 189, 248, 0.06);
  border: 1px solid rgba(56, 189, 248, 0.15);
  border-radius: 8px;
  padding: 6px 12px;
  margin: 4px 0;
  transition: all 0.3s ease;
}
.is-progress .row-indicator { background: #38bdf8; }
.is-progress .meta-lvl {
  color: #38bdf8;
  background: rgba(56, 189, 248, 0.15);
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.05em;
}
.is-progress .row-msg {
  color: #e0f2fe;
  font-weight: 600;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
}

/* Empty View */
.console-empty { height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #484f58; }
.empty-vector { font-size: 64px; margin-bottom: 24px; position: relative; }
.radar-ping { position: absolute; inset: 0; border: 2px solid var(--color-primary); border-radius: 50%; animation: radialPulse 3s infinite; }
@keyframes radialPulse { from { transform: scale(1); opacity: 0.6; } to { transform: scale(2.5); opacity: 0; } }

/* Footer */
.console-info-bar {
  height: 40px;
  background: var(--color-bg-subtle);
  border-top: 1px solid var(--color-border);
  padding: 0 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--color-text-tertiary);
}

.info-group { display: flex; gap: 24px; }
.info-item { display: flex; gap: 6px; }
.i-val.highlight { color: var(--color-primary); }

/* Fixes for Contrast & Visibility */
:deep(.saas-input .el-input__wrapper) {
  background: var(--color-bg-surface) !important;
  border: 1px solid var(--color-border);
  box-shadow: none !important;
  border-radius: 10px;
}
:deep(.saas-input .el-input__inner) {
  color: var(--color-text-main) !important;
  font-weight: 500;
}

:deep(.saas-select .el-input__wrapper) {
  background: var(--color-bg-surface) !important;
  border-radius: 10px;
}

/* SMART COPY BUTTON STYLES */
.smart-copy-btn {
  position: fixed;
  z-index: 9999;
  transform: translate(-50%, -100%);
  margin-top: -10px;
  cursor: pointer;
  filter: drop-shadow(0 4px 12px rgba(0,0,0,0.2));
}

.smart-copy-btn .glass-bg {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(8px);
  border-radius: 30px;
  border: 1px solid rgba(255,255,255,0.1);
  box-shadow: 
    0 0 0 1px rgba(0,0,0,0.2),
    0 10px 15px -3px rgba(0,0,0,0.3);
}

.smart-copy-btn .btn-content {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  color: white;
  white-space: nowrap;
}

.smart-copy-btn .action-icon {
  font-size: 1.1rem;
}

.smart-copy-btn .action-icon.success {
  color: #4ade80;
}

.smart-copy-btn .btn-text {
  font-size: 0.85rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.smart-copy-btn:hover .glass-bg {
  background: rgba(30, 41, 59, 0.95);
  border-color: var(--color-primary);
  box-shadow: 
    0 0 0 1px var(--color-primary),
    0 10px 25px -5px rgba(0,0,0,0.4);
}

/* Transitions */
.pop-scale-enter-active,
.pop-scale-leave-active {
  transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.pop-scale-enter-from,
.pop-scale-leave-to {
  opacity: 0;
  transform: translate(-50%, -80%) scale(0.8);
}
</style>
