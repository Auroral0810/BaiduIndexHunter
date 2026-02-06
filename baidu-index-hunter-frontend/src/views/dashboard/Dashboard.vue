<template>
  <div class="dashboard-wrapper">
    <!-- Animated Background Layer -->
    <div class="canvas-bg">
      <div class="glow-orb orb-1"></div>
      <div class="glow-orb orb-2"></div>
      <div class="grid-overlay"></div>
    </div>

    <!-- Main Navigation / Header -->
    <header class="dashboard-main-header glass-panel">
      <div class="brand">
        <div class="logo-icon">
          <el-icon><TrendCharts /></el-icon>
        </div>
        <div class="title-group">
          <h1 class="main-title">{{ $t('dashboard.dashboard.2dwsg6') }}</h1>
          <div class="live-status">
            <span class="pulse-dot" :class="{ 'is-active': wsConnected }"></span>
            <span class="status-text">{{ wsConnected ? $t('dashboard.dashboard.status_ok') : $t('dashboard.dashboard.status_disconnected') }}</span>
          </div>
        </div>
      </div>
      
      <!-- Tabs Navigation -->
      <div class="tabs-nav">
        <el-tabs v-model="activeTab" class="dashboard-tabs">
          <el-tab-pane :label="$t('dashboard.tabs.overview')" name="overview" />
          <el-tab-pane :label="$t('dashboard.tabs.spider_health')" name="spider_health" />
          <el-tab-pane :label="$t('dashboard.tabs.keyword_analysis')" name="keywords" />
          <el-tab-pane :label="$t('dashboard.tabs.region_analysis')" name="region" />
        </el-tabs>
      </div>
    </header>

    <div class="dashboard-content">
      <keep-alive>
        <component :is="currentTabComponent" />
      </keep-alive>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { TrendCharts } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { webSocketService } from '@/utils/websocket'

// Components
import OverviewTab from './components/OverviewTab.vue'
import SpiderHealthTab from './components/SpiderHealthTab.vue'
import KeywordAnalysisTab from './components/KeywordAnalysisTab.vue'
import RegionAnalysisTab from './components/RegionAnalysisTab.vue'

const { t: $t } = useI18n()
const activeTab = ref('overview')
const wsConnected = ref(false)

const currentTabComponent = computed(() => {
  switch (activeTab.value) {
    case 'overview': return OverviewTab
    case 'spider_health': return SpiderHealthTab
    case 'keywords': return KeywordAnalysisTab
    case 'region': return RegionAnalysisTab
    default: return OverviewTab
  }
})

onMounted(() => {
  webSocketService.connect()
  webSocketService.on('connect', () => wsConnected.value = true)
  webSocketService.on('disconnect', () => wsConnected.value = false)
})

onUnmounted(() => {
  // WebSocket disconnection handling might be in global service or app store
})

</script>

<style scoped>
.dashboard-wrapper {
  position: relative;
  min-height: calc(100vh - 100px);
  background: var(--color-bg-body);
  color: var(--color-text-main);
  padding: 24px;
  overflow-x: hidden;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
  transition: all 0.3s ease;
}

/* Background effects */
.canvas-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}

.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  opacity: 0.15;
}

.orb-1 { width: 600px; height: 600px; top: -10%; right: -5%; background: #6366f1; }
.orb-2 { width: 500px; height: 500px; bottom: 5%; left: -5%; background: #8b5cf6; }

.grid-overlay {
  position: absolute;
  inset: 0;
  background-image: 
    linear-gradient(rgba(30, 41, 59, 0.2) 1px, transparent 1px),
    linear-gradient(90deg, rgba(30, 41, 59, 0.2) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: radial-gradient(circle at center, black, transparent 90%);
}

.glass-panel {
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  box-shadow: var(--shadow-lg);
}

.dashboard-main-header {
  height: 80px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 32px;
  border-radius: 20px;
  margin-bottom: 24px;
  position: relative;
  z-index: 10;
}

.brand {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
  box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
}

.main-title {
  font-size: 1.5rem;
  font-weight: 800;
  letter-spacing: -0.5px;
  margin: 0;
}

.live-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.65rem;
  font-weight: 700;
  color: #10b981;
  letter-spacing: 1px;
}

.pulse-dot {
  width: 6px;
  height: 6px;
  background: #94a3b8;
  border-radius: 50%;
  opacity: 0.5;
  transition: all 0.3s;
}

.pulse-dot.is-active {
  background: #10b981;
  opacity: 1;
  box-shadow: 0 0 8px #10b981;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(1.5); }
  100% { opacity: 1; transform: scale(1); }
}

.tabs-nav {
  /* Style for tabs within header */
}

/* Custom Element Plus Tabs Style Override */
:deep(.el-tabs__header) {
  margin: 0;
}
:deep(.el-tabs__nav-wrap::after) {
  display: none;
}
:deep(.el-tabs__item) {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-secondary);
}
:deep(.el-tabs__item.is-active) {
  color: #6366f1;
}

.dashboard-content {
  position: relative;
  z-index: 1;
}
</style>
