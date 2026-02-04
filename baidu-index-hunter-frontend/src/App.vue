<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAppStore, SUPPORTED_LANGUAGES } from './store/app'
import { Sunny, Moon } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const appStore = useAppStore()
const activeIndex = ref('1')

// 监听当前路由以更新菜单高亮项
const routeMap = {
  '/': '1',
  '/data-collection': '2',
  '/cookie-manager': '3',
  '/dashboard': '4',
  '/settings': '5',
  '/about': '6',
  '/privacy': '7',
}

// 根据当前路径更新激活的菜单项
const updateActiveMenu = () => {
  const path = route.path
  activeIndex.value = routeMap[path] || '1'
}

// 监听路由变化
watch(() => route.path, () => {
  updateActiveMenu()
})

// 初始更新菜单项
updateActiveMenu()

const handleSelect = (key) => {
  switch(key) {
    case '1':
      router.push('/')
      break
    case '2':
      router.push('/data-collection')
      break
    case '3':
      router.push('/cookie-manager')
      break
    case '4':
      router.push('/dashboard')
      break
    case '5':
      router.push('/settings')
      break
    case '6':
      router.push('/about')
      break
    case '7':
      router.push('/privacy')
      break
  }
}

// 主题切换
const isDark = computed(() => appStore.theme === 'dark')
const toggleTheme = () => {
  appStore.setTheme(isDark.value ? 'light' : 'dark')
}

// 语言切换
const currentLanguage = computed(() => appStore.getCurrentLanguage())
const handleLanguageChange = (langCode) => {
  appStore.setLanguage(langCode)
}

// 初始化主题
onMounted(() => {
  appStore.initTheme()
})
</script>

<template>
  <div class="app-wrapper" :class="{ 'dark-mode': isDark }">
    <header class="app-header">
      <div class="header-content">
        <div class="logo" @click="router.push('/')">
          <img src="./assets/logo.svg" alt="BaiduIndexHunter" class="logo-img">
          <span class="logo-text">BaiduIndexHunter</span>
          <el-tag size="small" type="info" class="version-tag">v{{ appStore.version }}</el-tag>
        </div>
        
        <nav class="app-nav">
          <el-menu
            :default-active="activeIndex"
            mode="horizontal"
            @select="handleSelect"
            class="nav-menu"
            :ellipsis="false">
            <el-menu-item index="1" class="nav-item">
              <el-icon><i-ep-house /></el-icon>
              <span>首页</span>
            </el-menu-item>
            <el-menu-item index="2" class="nav-item">
              <el-icon><i-ep-data-line /></el-icon>
              <span>数据采集</span>
            </el-menu-item>
            <el-menu-item index="3" class="nav-item">
              <el-icon><i-ep-data-line /></el-icon>
              <span>Cookie管理</span>
            </el-menu-item>
            <el-menu-item index="4" class="nav-item">
              <el-icon><i-ep-data-analysis /></el-icon>
              <span>数据大屏</span>
            </el-menu-item>
            <el-menu-item index="5" class="nav-item">
              <el-icon><i-ep-setting /></el-icon>
              <span>配置信息</span>
            </el-menu-item>
            <el-menu-item index="6" class="nav-item">
              <el-icon><i-ep-info-filled /></el-icon>
              <span>关于</span>
            </el-menu-item>
          </el-menu>
        </nav>

        <!-- 右侧工具栏 -->
        <div class="header-tools">
          <!-- 主题切换按钮 -->
          <el-tooltip :content="isDark ? '切换到浅色模式' : '切换到深色模式'" placement="bottom">
            <button class="theme-toggle-btn" @click="toggleTheme" :class="{ 'is-dark': isDark }">
              <div class="theme-toggle-track">
                <div class="theme-toggle-thumb">
                  <el-icon v-if="isDark" class="theme-icon"><Moon /></el-icon>
                  <el-icon v-else class="theme-icon"><Sunny /></el-icon>
                </div>
              </div>
            </button>
          </el-tooltip>

          <!-- 语言切换下拉框 -->
          <el-dropdown trigger="click" @command="handleLanguageChange" class="language-dropdown">
            <button class="language-btn">
              <span class="language-flag">{{ currentLanguage.flag }}</span>
              <span class="language-name">{{ currentLanguage.name }}</span>
              <el-icon class="el-icon--right"><i-ep-arrow-down /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item 
                  v-for="lang in SUPPORTED_LANGUAGES" 
                  :key="lang.code" 
                  :command="lang.code"
                  :class="{ 'is-active': appStore.language === lang.code }"
                >
                  <span class="dropdown-flag">{{ lang.flag }}</span>
                  <span class="dropdown-name">{{ lang.name }}</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </header>
    
    <main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    
    <footer class="app-footer">
      <div class="footer-content">
        <div class="copyright">
          © {{ new Date().getFullYear() }} BaiduIndexHunter v{{ appStore.version }} - 仅供学习研究使用，请勿用于商业用途
        </div>
        <div class="footer-links">
          <a href="#" @click.prevent="router.push('/about')">关于</a>
          <a href="#" @click.prevent="router.push('/privacy')">使用条款</a>
        </div>
      </div>
    </footer>
  </div>
</template>

<style>
:root {
  /* 品牌色 - 更加稳重的深邃科技蓝 */
  --primary-color: #2563eb;
  --primary-hover: #1d4ed8;
  --primary-light: #eff6ff;
  
  /* 渐变改为同色系微渐变 */
  --primary-gradient: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  
  /* 深色强调色 */
  --accent-color: #0f172a;
  
  /* 文字颜色 */
  --text-primary: #0f172a;
  --text-regular: #334155;
  --text-secondary: #64748b;
  --text-placeholder: #cbd5e1;
  
  /* 背景颜色 */
  --background-color: #f8fafc;
  --surface-color: #ffffff;
  --border-color: #e2e8f0;
  --border-lighter: #f1f5f9;
  
  /* 阴影系统 */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.05), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.05), 0 10px 10px -5px rgba(0, 0, 0, 0.02);
  
  /* 圆角 */
  --radius-sm: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  --radius-full: 9999px;
  
  --content-width: 1200px;
}

/* 深色主题变量 */
.dark-mode {
  --primary-color: #3b82f6;
  --primary-hover: #60a5fa;
  --primary-light: #1e3a5f;
  
  --text-primary: #f1f5f9;
  --text-regular: #cbd5e1;
  --text-secondary: #94a3b8;
  --text-placeholder: #64748b;
  
  --background-color: #0f172a;
  --surface-color: #1e293b;
  --border-color: #334155;
  --border-lighter: #1e293b;
  
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
}

body {
  margin: 0;
  padding: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  color: var(--text-regular);
  background-color: var(--background-color);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  transition: background-color 0.3s ease, color 0.3s ease;
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

.dark-mode ::-webkit-scrollbar-thumb {
  background: #475569;
}

::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>

<style scoped>
.app-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--background-color);
  transition: background-color 0.3s ease;
}

.app-header {
  background-color: var(--surface-color);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  position: sticky;
  top: 0;
  z-index: 1000;
  border-bottom: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.header-content {
  max-width: var(--content-width);
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 72px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  padding: 8px;
  border-radius: var(--radius-md);
  transition: all 0.3s ease;
}

.logo:hover {
  background-color: var(--primary-light);
}

.logo-img {
  height: 40px;
  width: 40px;
  filter: drop-shadow(0 4px 6px rgba(59, 130, 246, 0.2));
}

.logo-text {
  font-size: 22px;
  font-weight: 700;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
}

.version-tag {
  font-size: 11px;
  padding: 2px 6px;
  height: auto;
}

.app-nav {
  height: 100%;
  display: flex;
  align-items: center;
  flex: 1;
  justify-content: center;
}

.nav-menu {
  background: transparent !important;
  border-bottom: none !important;
  height: 72px;
}

.nav-item {
  font-size: 15px;
  font-weight: 500;
  height: 72px !important;
  line-height: 72px !important;
  padding: 0 20px !important;
  color: var(--text-regular) !important;
  transition: all 0.3s ease;
  position: relative;
}

.nav-item .el-icon {
  margin-right: 6px;
  font-size: 18px;
  vertical-align: middle;
}

.nav-item:hover {
  color: var(--primary-color) !important;
  background-color: transparent !important;
}

.nav-item::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  width: 0;
  height: 3px;
  background: var(--primary-gradient);
  transition: all 0.3s ease;
  transform: translateX(-50%);
  border-top-left-radius: 3px;
  border-top-right-radius: 3px;
}

.nav-item:hover::after,
.nav-item.is-active::after {
  width: 100%;
}

.nav-item.is-active {
  color: var(--primary-color) !important;
  background-color: transparent !important;
  font-weight: 600;
}

/* 右侧工具栏 */
.header-tools {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 主题切换按钮 */
.theme-toggle-btn {
  position: relative;
  width: 56px;
  height: 28px;
  padding: 0;
  border: none;
  background: transparent;
  cursor: pointer;
  outline: none;
}

.theme-toggle-track {
  position: relative;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  border-radius: 14px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
}

.theme-toggle-btn.is-dark .theme-toggle-track {
  background: linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%);
}

.theme-toggle-thumb {
  position: absolute;
  top: 2px;
  left: 2px;
  width: 24px;
  height: 24px;
  background: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.theme-toggle-btn.is-dark .theme-toggle-thumb {
  left: 30px;
  background: #334155;
}

.theme-icon {
  font-size: 14px;
  color: #f59e0b;
  transition: all 0.3s ease;
}

.theme-toggle-btn.is-dark .theme-icon {
  color: #fbbf24;
}

/* 语言切换按钮 */
.language-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 4px;
  min-width: 120px;
  background: var(--surface-color);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.3s ease;
  color: var(--text-regular);
  font-size: 14px;
}

.language-btn:hover {
  border-color: var(--primary-color);
  background: var(--primary-light);
}

.language-flag {
  font-size: 18px;
}

.language-name {
  font-weight: 500;
}

.dropdown-flag {
  margin-right: 2px;
  font-size: 16px;
}

.dropdown-name {
  font-size: 14px;
}

:deep(.el-dropdown-menu__item.is-active) {
  background-color: var(--primary-light);
  color: var(--primary-color);
}

.app-main {
  flex: 1;
  padding: 32px 24px;
  max-width: var(--content-width);
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}

.app-footer {
  background-color: var(--surface-color);
  padding: 40px 24px;
  border-top: 1px solid var(--border-color);
  margin-top: auto;
  transition: all 0.3s ease;
}

.footer-content {
  max-width: var(--content-width);
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 20px;
}

.copyright {
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
}

.footer-links {
  display: flex;
  gap: 32px;
}

.footer-links a {
  color: var(--text-regular);
  font-size: 14px;
  text-decoration: none;
  transition: all 0.2s ease;
  position: relative;
}

.footer-links a:hover {
  color: var(--primary-color);
}

/* 页面过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1), transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

@media screen and (max-width: 1200px) {
  .language-name {
    display: none;
  }
  
  .language-btn {
    padding: 8px;
  }
}

@media screen and (max-width: 768px) {
  .header-content {
    height: auto;
    padding: 12px;
    flex-wrap: wrap;
  }
  
  .logo {
    margin-bottom: 0;
  }
  
  .nav-menu {
    height: auto;
    border: none;
    width: 100%;
    margin-top: 10px;
    display: flex;
    overflow-x: auto;
    padding-bottom: 5px;
  }
  
  .nav-item {
    padding: 0 16px !important;
    height: 48px !important;
    line-height: 48px !important;
    flex-shrink: 0;
  }
  
  .nav-item::after {
    display: none;
  }
  
  .header-tools {
    position: absolute;
    right: 12px;
    top: 12px;
  }
  
  .app-main {
    padding: 20px 16px;
  }
  
  .footer-content {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
}
</style>
