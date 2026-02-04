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
      <div class="header-container">
        <div class="logo-area" @click="router.push('/')">
          <div class="logo-icon">
            <img src="./assets/logo.svg" alt="Logo" />
          </div>
          <div class="logo-text">
            <span>BaiduIndex</span>
            <span class="logo-suffix">Hunter</span>
          </div>
          <el-tag size="small" type="primary" effect="light" class="version-tag">v{{ appStore.version }}</el-tag>
        </div>
        
        <nav class="app-nav">
          <el-menu
            :default-active="activeIndex"
            mode="horizontal"
            @select="handleSelect"
            class="nav-menu"
            :ellipsis="false">
            <el-menu-item index="1" class="nav-item">首页</el-menu-item>
            <el-menu-item index="2" class="nav-item">数据采集</el-menu-item>
            <el-menu-item index="3" class="nav-item">Cookie管理</el-menu-item>
            <el-menu-item index="4" class="nav-item">数据大屏</el-menu-item>
            <el-menu-item index="5" class="nav-item">配置</el-menu-item>
            <el-menu-item index="6" class="nav-item">关于</el-menu-item>
            <el-menu-item index="7" class="nav-item">使用条款</el-menu-item>
          </el-menu>
        </nav>

        <!-- 右侧工具栏 -->
        <div class="header-tools">
          <!-- 主题切换按钮 -->
          <button class="theme-toggle-btn" @click="toggleTheme" :title="isDark ? '切换到浅色模式' : '切换到深色模式'">
            <el-icon v-if="isDark" class="theme-icon"><Moon /></el-icon>
            <el-icon v-else class="theme-icon"><Sunny /></el-icon>
          </button>

          <!-- 语言切换 -->
          <el-dropdown trigger="click" @command="handleLanguageChange" popper-class="language-popper">
            <button class="language-btn">
              <span class="language-flag">{{ currentLanguage.flag }}</span>
              <span class="language-code">{{ currentLanguage.code === 'zh-CN' ? 'CN' : 'EN' }}</span>
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
          
          <a href="https://github.com/your-repo" target="_blank" class="github-link" title="GitHub">
            <svg height="20" width="20" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"></path>
            </svg>
          </a>
        </div>
      </div>
    </header>
    
    <main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="fade-slide" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    
    <footer class="app-footer">
      <div class="footer-container">
        <div class="footer-left">
          <div class="footer-logo">BaiduIndexHunter</div>
          <div class="footer-desc">仅供个人学习研究使用的非商业项目</div>
          <div class="copyright">© {{ new Date().getFullYear() }} v{{ appStore.version }}</div>
        </div>
        <div class="footer-right">
          <a href="#" @click.prevent="router.push('/about')">关于项目</a>
          <a href="#" @click.prevent="router.push('/privacy')">使用条款</a>
          <a href="#" @click.prevent="router.push('/data-collection')">开始采集</a>
        </div>
      </div>
    </footer>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  /* 现代 SaaS 色彩体系 (Light Mode) */
  --color-primary: #4f46e5; /* Indigo 600 */
  --color-primary-hover: #4338ca; /* Indigo 700 */
  --color-primary-light: #e0e7ff; /* Indigo 100 */
  
  --color-bg-body: #ffffff;
  --color-bg-surface: #ffffff;
  --color-bg-subtle: #f8fafc; /* Slate 50 */
  
  --color-text-main: #0f172a; /* Slate 900 */
  --color-text-secondary: #64748b; /* Slate 500 */
  --color-text-tertiary: #94a3b8; /* Slate 400 */
  
  --color-border: #e2e8f0; /* Slate 200 */
  --color-border-hover: #cbd5e1; /* Slate 300 */
  
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  --shadow-primary: 0 4px 14px 0 rgba(79, 70, 229, 0.3);
  
  --font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --header-height: 64px;
  --max-width: 1280px;
  --radius-base: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
}

/* 深色模式变量覆盖 */
.dark-mode {
  --color-primary: #6366f1; /* Indigo 500 */
  --color-primary-hover: #818cf8; /* Indigo 400 */
  --color-primary-light: #312e81; /* Indigo 900 */
  
  --color-bg-body: #020617; /* Slate 950 */
  --color-bg-surface: #0f172a; /* Slate 900 */
  --color-bg-subtle: #1e293b; /* Slate 800 */
  
  --color-text-main: #f8fafc; /* Slate 50 */
  --color-text-secondary: #cbd5e1; /* Slate 300 */
  --color-text-tertiary: #64748b; /* Slate 500 */
  
  --color-border: #1e293b; /* Slate 800 */
  --color-border-hover: #334155; /* Slate 700 */
  
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
  --shadow-primary: 0 4px 14px 0 rgba(99, 102, 241, 0.3);
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  padding: 0;
  font-family: var(--font-family);
  background-color: var(--color-bg-body);
  color: var(--color-text-main);
  transition: background-color 0.3s ease, color 0.3s ease;
  -webkit-font-smoothing: antialiased;
}

/* 覆盖 Element Plus 默认样式以匹配新主题 */
:root {
  --el-color-primary: var(--color-primary);
  --el-color-primary-light-3: #818cf8;
  --el-color-primary-light-5: #a5b4fc;
  --el-color-primary-light-7: #c7d2fe;
  --el-color-primary-light-9: #e0e7ff;
  --el-bg-color: var(--color-bg-surface);
  --el-text-color-primary: var(--color-text-main);
  --el-text-color-regular: var(--color-text-secondary);
  --el-border-color: var(--color-border);
  --el-border-radius-base: var(--radius-base);
}

.dark-mode {
  --el-bg-color: var(--color-bg-surface);
  --el-bg-color-overlay: var(--color-bg-subtle);
  --el-fill-color-blank: var(--color-bg-body);
}
</style>

<style scoped>
.app-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* 头部导航栏 */
.app-header {
  height: var(--header-height);
  background-color: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  z-index: 100;
  transition: all 0.3s ease;
}

.dark-mode .app-header {
  background-color: rgba(15, 23, 42, 0.8);
}

.header-container {
  max-width: var(--max-width);
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

/* Logo 区域 */
.logo-area {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  user-select: none;
}

.logo-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, var(--color-primary), #8b5cf6);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
}

.logo-icon img {
  width: 100%;
  height: 100%;
  filter: brightness(0) invert(1);
}

.logo-text {
  font-size: 1.25rem;
  font-weight: 700;
  letter-spacing: -0.5px;
  color: var(--color-text-main);
  display: flex;
  align-items: center;
}

.logo-suffix {
  color: var(--color-primary);
}

.version-tag {
  font-size: 0.75rem;
  font-weight: 600;
  border-radius: 100px;
  padding: 0 8px;
  height: 20px;
  line-height: 18px;
}

/* 导航菜单 */
.app-nav {
  flex: 1;
  display: flex;
  justify-content: center;
  margin: 0 40px;
}

.nav-menu {
  background: transparent !important;
  border: none !important;
  height: var(--header-height);
  display: flex;
  align-items: center;
}

.nav-item {
  height: 40px !important;
  line-height: 40px !important;
  margin: 0 4px !important;
  border-radius: 6px !important;
  border: none !important;
  color: var(--color-text-secondary) !important;
  font-weight: 500 !important;
  font-size: 0.95rem !important;
  transition: all 0.2s ease !important;
  background: transparent !important;
}

.nav-item:hover {
  color: var(--color-primary) !important;
  background-color: var(--color-bg-subtle) !important;
}

.nav-item.is-active {
  color: var(--color-primary) !important;
  background-color: var(--color-primary-light) !important;
  font-weight: 600 !important;
}

/* 右侧工具栏 */
.header-tools {
  display: flex;
  align-items: center;
  gap: 16px;
}

.theme-toggle-btn {
  background: transparent;
  border: 1px solid var(--color-border);
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.theme-toggle-btn:hover {
  border-color: var(--color-text-tertiary);
  color: var(--color-text-main);
  background-color: var(--color-bg-subtle);
}

.language-btn {
  background: transparent;
  border: 1px solid var(--color-border);
  height: 36px;
  padding: 0 12px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  transition: all 0.2s;
  color: var(--color-text-secondary);
  font-weight: 500;
  font-size: 0.9rem;
}

.language-btn:hover {
  border-color: var(--color-text-tertiary);
  color: var(--color-text-main);
  background-color: var(--color-bg-subtle);
}

.language-flag {
  font-size: 1.1rem;
}

.github-link {
  color: var(--color-text-secondary);
  transition: color 0.2s;
  display: flex;
  align-items: center;
}

.github-link:hover {
  color: var(--color-text-main);
}

/* 主内容区域 */
.app-main {
  flex: 1;
  width: 100%;
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 32px 24px;
}

/* 页面过渡动画 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

/* 页脚 */
.app-footer {
  border-top: 1px solid var(--color-border);
  background-color: var(--color-bg-subtle);
  padding: 48px 0;
  margin-top: auto;
}

.footer-container {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.footer-left {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.footer-logo {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-text-main);
}

.footer-desc {
  font-size: 0.9rem;
  color: var(--color-text-tertiary);
}

.copyright {
  font-size: 0.85rem;
  color: var(--color-text-tertiary);
  margin-top: 16px;
}

.footer-right {
  display: flex;
  gap: 24px;
}

.footer-right a {
  text-decoration: none;
  color: var(--color-text-secondary);
  font-size: 0.9rem;
  transition: color 0.2s;
}

.footer-right a:hover {
  color: var(--color-primary);
}

/* 响应式调整 */
@media (max-width: 768px) {
  .app-nav {
    display: none; /* 移动端暂时隐藏菜单，后续可加汉堡菜单 */
  }
  
  .header-container {
    justify-content: space-between;
  }
  
  .footer-container {
    flex-direction: column;
    gap: 32px;
    align-items: center;
    text-align: center;
  }
}
</style>
