<template>
  <div class="logs-container">
    <div class="page-header">
      <div class="header-info">
        <h2 class="title">{{ $t('views.logs.title') }}</h2>
        <p class="subtitle">{{ $t('views.logs.subtitle') }}</p>
      </div>
      <div class="header-actions">
        <el-tag 
          :type="connected ? 'success' : 'danger'" 
          class="status-tag" 
          effect="dark"
        >
          <div class="status-dot" :class="{ 'pulse': connected }"></div>
          {{ connected ? $t('views.logs.status_connected') : $t('views.logs.status_disconnected') }}
        </el-tag>
      </div>
    </div>

    <!-- Terminal Section -->
    <div class="terminal-card glass-panel">
      <div class="terminal-header">
        <div class="terminal-title">
          <el-icon class="terminal-icon"><Monitor /></el-icon>
          <span>{{ $t('views.logs.terminal_title') }}</span>
        </div>
        <div class="terminal-controls">
          <div class="control-group">
            <el-input
              v-model="searchQuery"
              :placeholder="$t('views.logs.search_placeholder')"
              prefix-icon="Search"
              clearable
              class="terminal-search"
              size="small"
            />
            <el-select 
              v-model="filterLevel" 
              size="small" 
              class="level-select"
              :placeholder="$t('views.logs.filter_level')"
            >
              <el-option :label="$t('views.logs.all_levels')" value="ALL" />
              <el-option label="INFO" value="INFO" />
              <el-option label="WARNING" value="WARNING" />
              <el-option label="ERROR" value="ERROR" />
              <el-option label="DEBUG" value="DEBUG" />
            </el-select>
          </div>
          
          <div class="control-group">
            <el-button-group>
              <el-tooltip :content="isPaused ? $t('views.logs.resume') : $t('views.logs.pause')" placement="top">
                <el-button 
                  :type="isPaused ? 'warning' : 'default'" 
                  size="small" 
                  @click="isPaused = !isPaused"
                >
                  <el-icon><VideoPause v-if="!isPaused" /><VideoPlay v-else /></el-icon>
                </el-button>
              </el-tooltip>
              <el-tooltip :content="$t('views.logs.auto_scroll')" placement="top">
                <el-button 
                  :type="autoScroll ? 'primary' : 'default'" 
                  size="small" 
                  @click="autoScroll = !autoScroll"
                >
                  <el-icon><Bottom /></el-icon>
                </el-button>
              </el-tooltip>
            </el-button-group>
            
            <el-button type="danger" size="small" plain @click="clearLogs">
              <el-icon><Delete /></el-icon>
            </el-button>
            <el-button size="small" @click="downloadLogs">
              <el-icon><Download /></el-icon>
            </el-button>
          </div>
        </div>
      </div>

      <div class="terminal-body" ref="terminalBody" @scroll="handleScroll">
        <div v-if="filteredLogs.length === 0" class="empty-terminal">
          <el-icon class="empty-icon"><Monitor /></el-icon>
          <p>{{ $t('dashboard.charts.no_data') }}</p>
        </div>
        <div 
          v-for="(log, index) in filteredLogs" 
          :key="index" 
          class="log-line"
          :class="log.level.toLowerCase()"
        >
          <span class="log-time">{{ log.time }}</span>
          <span class="log-level-badge">[{{ log.level }}]</span>
          <span class="log-source">{{ log.name }}:{{ log.function }}:{{ log.line }}</span>
          <span class="log-sep">-</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
      </div>
      
      <div class="terminal-footer">
        <div class="stat-item">
          <span class="label">LINES:</span>
          <span class="value">{{ logs.length }}</span>
        </div>
        <div class="stat-item">
          <span class="label">FILTERED:</span>
          <span class="value">{{ filteredLogs.length }}</span>
        </div>
        <div class="stat-item">
          <span class="label">SPEED:</span>
          <span class="value">{{ logSpeed }} msg/s</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { io } from 'socket.io-client'
import { useI18n } from 'vue-i18n'
import { 
  Search, Delete, Download, VideoPause, VideoPlay, 
  Bottom, Monitor 
} from '@element-plus/icons-vue'
import { saveAs } from 'file-saver'

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

// Filtering logic
const filteredLogs = computed(() => {
  return logs.value.filter(log => {
    const matchesSearch = !searchQuery.value || 
      log.message.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      log.name.toLowerCase().includes(searchQuery.value.toLowerCase())
    
    const matchesLevel = filterLevel.value === 'ALL' || log.level === filterLevel.value
    
    return matchesSearch && matchesLevel
  })
})

const handleScroll = () => {
  if (!terminalBody.value) return
  const { scrollTop, scrollHeight, clientHeight } = terminalBody.value
  // If user scrolls up, disable autoScroll
  if (scrollHeight - scrollTop - clientHeight > 50) {
    autoScroll.value = false
  } else {
    autoScroll.value = true
  }
}

const scrollToBottom = async () => {
  if (autoScroll.value && terminalBody.value) {
    await nextTick()
    terminalBody.value.scrollTop = terminalBody.value.scrollHeight
  }
}

const clearLogs = () => {
  logs.value = []
}

const downloadLogs = () => {
  const content = filteredLogs.value.map(l => 
    `${l.time} | ${l.level.padEnd(8)} | ${l.name}:${l.function}:${l.line} - ${l.message}`
  ).join('\n')
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
  saveAs(blob, `system_logs_${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '_')}.log`)
}

const initSocket = () => {
  const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5001'
  socket.value = io(API_BASE)

  socket.value.on('connect', () => {
    connected.value = true
    console.log('Logs WebSocket connected')
  })

  socket.value.on('disconnect', () => {
    connected.value = false
  })

  socket.value.on('system_log', (data) => {
    if (isPaused.value) return
    
    messageCount++
    logs.value.push(data)
    
    // Maintain buffer size
    if (logs.value.length > maxLogs) {
      logs.value.shift()
    }
    
    if (autoScroll.value) {
      scrollToBottom()
    }
  })
}

onMounted(() => {
  initSocket()
  speedTimer = setInterval(() => {
    logSpeed.value = messageCount
    messageCount = 0
  }, 1000)
})

onUnmounted(() => {
  if (socket.value) {
    socket.value.disconnect()
  }
  if (speedTimer) clearInterval(speedTimer)
})

watch(filteredLogs, () => {
  if (autoScroll.value) {
    scrollToBottom()
  }
})
</script>

<style scoped>
.logs-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
  height: calc(100vh - 160px);
}

/* 顶部 Header 区域 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 4px;
}

.title {
  margin: 0;
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--color-text-main);
  letter-spacing: -0.01em;
}

.subtitle {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  font-size: 0.95rem;
}

/* 状态标签 */
.status-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 12px;
  height: 32px;
  font-weight: 500;
  border-radius: 6px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #94a3b8;
}

.status-dot.pulse {
  background-color: var(--color-success);
  box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
  animation: pulse-green 2s infinite cubic-bezier(0.4, 0, 0.6, 1);
}

@keyframes pulse-green {
  0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
  70% { box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
  100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

/* 终端卡片主体 - 适配 Light/Dark */
.terminal-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-md);
  transition: all 0.3s ease;
}

.terminal-header {
  height: 56px;
  background: var(--color-bg-subtle);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  border-bottom: 1px solid var(--color-border);
}

.terminal-title {
  font-weight: 600;
  color: var(--color-text-main);
  display: flex;
  align-items: center;
  gap: 8px;
}

.terminal-icon {
  color: var(--color-text-tertiary);
}

/* 终端控制栏 */
.terminal-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.level-select {
  width: 120px;
}

/* 终端内容区域 - 保持代码风格但适配主题 */
.terminal-body {
  flex: 1;
  padding: 16px;
  font-family: 'JetBrains Mono', 'Fira Code', 'Menlo', 'Monaco', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
  overflow-y: auto;
  overflow-x: auto;
  background: #1e1e1e; /* 保持深色背景以获得最佳代码高亮效果，或者根据主题切换 */
  color: #e5e5e5;
  scroll-behavior: auto;
}

/* 如果需要在浅色模式下也使用深色终端（通常更好看），则保持 #1e1e1e。
   如果用户觉得“不适配”，可能是指外框。现在外框已经是 var(--color-bg-surface)。
   主要内容区域通常终端都是黑底白字。 */

/* Custom Scrollbar */
.terminal-body::-webkit-scrollbar {
  width: 10px;
}
.terminal-body::-webkit-scrollbar-thumb {
  background: #424242;
  border-radius: 5px;
}
.terminal-body::-webkit-scrollbar-track {
  background: transparent;
}

/* Log Lines Styling */
.log-line {
  white-space: pre-wrap;
  word-break: break-all;
  padding: 2px 8px;
  border-radius: 4px;
  display: flex;
  gap: 10px;
  color: #d4d4d4;
  border-left: 2px solid transparent; /* 增加左侧标记 */
}

.log-line:hover {
  background: rgba(255, 255, 255, 0.05);
}

.log-time { color: #858585; min-width: 140px; }
.log-level-badge { font-weight: 700; min-width: 60px; text-align: center; border-radius: 4px; font-size: 12px; padding: 0 4px; height: 18px; line-height: 18px; align-self: center; }
.log-source { color: #569cd6; } /* VS Code Blue */
.log-sep { color: #555; }
.log-message { flex: 1; }

/* Level Specific Colors */
.info .log-level-badge { background: rgba(74, 222, 128, 0.2); color: #4ade80; } 
.warning .log-level-badge { background: rgba(251, 191, 36, 0.2); color: #fbbf24; }
.warning .log-line { border-left-color: #fbbf24; background: rgba(251, 191, 36, 0.05); }
.error .log-level-badge { background: rgba(248, 113, 113, 0.2); color: #f87171; }
.error .log-message { color: #fca5a5; } 
.error .log-line { border-left-color: #ef4444; background: rgba(239, 68, 68, 0.1); }
.debug .log-level-badge { background: rgba(148, 163, 184, 0.2); color: #94a3b8; }

.empty-terminal {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #666;
  gap: 16px;
}

.empty-icon {
  font-size: 48px;
  opacity: 0.5;
}

.terminal-footer {
  height: 36px;
  background: var(--color-bg-subtle); /* Footer match header */
  border-top: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: flex-end; /* Align right */
  padding: 0 20px;
  gap: 20px;
  font-size: 12px;
  color: var(--color-text-secondary);
}

.stat-item {
  display: flex;
  gap: 8px;
}

.stat-item .label { font-weight: 600; }
.stat-item .value { font-family: var(--font-family-mono); }

.glass-panel {
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}
</style>
