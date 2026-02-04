<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Sunny, Moon } from '@element-plus/icons-vue'
import { setLocale } from './i18n'

const { t, locale } = useI18n()
const router = useRouter()
const route = useRoute()
const activeIndex = ref('1')

// 版本号
const version = 'v2.0'

// 主题状态
const isDark = ref(localStorage.getItem('ui.theme') === 'dark')

// 语言状态
const currentLang = ref(localStorage.getItem('ui.language') || 'zh_CN')

// 语言选项
const languageOptions = [
  { value: 'zh_CN', label: '简体中文', flag: '🇨🇳' },
  { value: 'zh_TW', label: '繁體中文', flag: '🇹🇼' },
  { value: 'en', label: 'English', flag: '🇺🇸' },
  { value: 'ja', label: '日本語', flag: '🇯🇵' }
]

// 切换主题
const toggleTheme = () => {
  isDark.value = !isDark.value
  const theme = isDark.value ? 'dark' : 'light'
  localStorage.setItem('ui.theme', theme)
  applyTheme(theme)
}

// 应用主题
const applyTheme = (theme) => {
  if (theme === 'dark') {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
}

// 切换语言
const changeLanguage = (lang) => {
  currentLang.value = lang
  setLocale(lang)
}

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
    case '1': router.push('/'); break
    case '2': router.push('/data-collection'); break
    case '3': router.push('/cookie-manager'); break
    case '4': router.push('/dashboard'); break
    case '5': router.push('/settings'); break
    case '6': router.push('/about'); break
    case '7': router.push('/privacy'); break
  }
}

// 当前年份
const currentYear = new Date().getFullYear()

// 初始化主题
onMounted(() => {
  applyTheme(isDark.value ? 'dark' : 'light')
})
</script>

<template>
  <div class="app-wrapper">
    <header class="app-header">
      <div class="header-content">
        <div class="logo" @click="router.push('/')">
          <img src="./assets/logo.svg" alt="BaiduIndexHunter" class="logo-img">
          <span class="logo-text">BaiduIndexHunter</span>
          <el-tag size="small" type="info" class="version-tag">{{ version }}</el-tag>
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
              <span>{{ t('nav.home') }}</span>
            </el-menu-item>
            <el-menu-item index="2" class="nav-item">
              <el-icon><i-ep-data-line /></el-icon>
              <span>{{ t('nav.dataCollection') }}</span>
            </el-menu-item>
            <el-menu-item index="3" class="nav-item">
              <el-icon><i-ep-data-line /></el-icon>
              <span>{{ t('nav.cookieManager') }}</span>
            </el-menu-item>
            <el-menu-item index="4" class="nav-item">
              <el-icon><i-ep-data-analysis /></el-icon>
              <span>{{ t('nav.dashboard') }}</span>
            </el-menu-item>
            <el-menu-item index="5" class="nav-item">
              <el-icon><i-ep-setting /></el-icon>
              <span>{{ t('nav.settings') }}</span>
            </el-menu-item>
            <el-menu-item index="6" class="nav-item">
              <el-icon><i-ep-info-filled /></el-icon>
              <span>{{ t('nav.about') }}</span>
            </el-menu-item>
            <el-menu-item index="7" class="nav-item">
              <el-icon><i-ep-lock /></el-icon>
              <span>{{ t('nav.privacy') }}</span>
            </el-menu-item>
          </el-menu>
        </nav>
        
        <!-- 右侧工具栏 -->
        <div class="header-tools">
          <!-- 主题切换按钮 -->
          <el-tooltip :content="isDark ? t('settings.ui.themeLight') : t('settings.ui.themeDark')" placement="bottom">
            <el-button 
              class="theme-toggle" 
              circle 
              @click="toggleTheme"
            >
              <el-icon :size="18">
                <Moon v-if="!isDark" />
                <Sunny v-else />
              </el-icon>
            </el-button>
          </el-tooltip>
          
          <!-- 语言切换下拉框 -->
          <el-dropdown trigger="click" @command="changeLanguage">
            <el-button class="lang-toggle">
              <span class="lang-flag">{{ languageOptions.find(l => l.value === currentLang)?.flag }}</span>
              <span class="lang-text">{{ languageOptions.find(l => l.value === currentLang)?.label }}</span>
              <el-icon class="el-icon--right"><i-ep-arrow-down /></el-icon>
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item 
                  v-for="lang in languageOptions" 
                  :key="lang.value" 
                  :command="lang.value"
                  :class="{ 'is-active': currentLang === lang.value }"
                >
                  <span class="lang-flag">{{ lang.flag }}</span>
                  <span>{{ lang.label }}</span>
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
        <div class="disclaimer">
          <span class="disclaimer-text">{{ t('footer.disclaimer') }}</span>
        </div>
        <div class="footer-bottom">
          <div class="copyright">
            © {{ currentYear }} BaiduIndexHunter {{ version }} - {{ t('common.learningProject') }}
          </div>
          <div class="footer-links">
            <a href="#" @click.prevent="router.push('/about')">{{ t('footer.aboutProject') }}</a>
            <a href="#" @click.prevent="router.push('/privacy')">{{ t('footer.privacyPolicy') }}</a>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<style>
/* ==================== 浅色模式（默认） ==================== */
:root {
  --primary-color: #2563eb;
  --primary-hover: #1d4ed8;
  --primary-light: #eff6ff;
  --primary-gradient: linear-gradient(135deg, #2563eb 0%, #1e40af 100%);
  
  --text-primary: #0f172a;
  --text-regular: #334155;
  --text-secondary: #64748b;
  --text-placeholder: #94a3b8;
  
  --bg-page: #f8fafc;
  --bg-card: #ffffff;
  --bg-elevated: #ffffff;
  --bg-input: #ffffff;
  
  --border-color: #e2e8f0;
  --border-light: #f1f5f9;
  
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  
  --header-bg: rgba(255, 255, 255, 0.95);
  --footer-bg: #ffffff;
  --warning-color: #d97706;
  --success-color: #16a34a;
  --error-color: #dc2626;
  
  --content-width: 1200px;
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  
  /* 过渡时间 */
  --transition-fast: 0.15s;
  --transition-normal: 0.25s;
}

/* ==================== 深色模式 ==================== */
html.dark {
  --primary-color: #60a5fa;
  --primary-hover: #3b82f6;
  --primary-light: rgba(59, 130, 246, 0.15);
  --primary-gradient: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  
  --text-primary: #f1f5f9;
  --text-regular: #e2e8f0;
  --text-secondary: #94a3b8;
  --text-placeholder: #64748b;
  
  --bg-page: #0f172a;
  --bg-card: #1e293b;
  --bg-elevated: #334155;
  --bg-input: #1e293b;
  
  --border-color: #334155;
  --border-light: #475569;
  
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.3);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
  
  --header-bg: rgba(30, 41, 59, 0.95);
  --footer-bg: #1e293b;
  --warning-color: #fbbf24;
  --success-color: #4ade80;
  --error-color: #f87171;
}

/* ==================== 基础样式 ==================== */
* {
  transition: background-color var(--transition-normal) ease,
              border-color var(--transition-normal) ease,
              box-shadow var(--transition-normal) ease;
}

body {
  margin: 0;
  padding: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: var(--text-regular);
  background-color: var(--bg-page);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 滚动条 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: var(--bg-page);
}

::-webkit-scrollbar-thumb {
  background: var(--text-placeholder);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-secondary);
}

/* ==================== Element Plus 深色模式覆盖 ==================== */
html.dark .el-card {
  background-color: var(--bg-card);
  border-color: var(--border-color);
  color: var(--text-regular);
}

html.dark .el-card__header {
  border-bottom-color: var(--border-color);
  color: var(--text-primary);
}

html.dark .el-menu {
  background-color: transparent;
  border-color: var(--border-color);
}

html.dark .el-menu-item {
  color: var(--text-regular);
}

html.dark .el-menu-item:hover,
html.dark .el-menu-item:focus {
  background-color: var(--primary-light) !important;
  color: var(--primary-color) !important;
}

html.dark .el-menu-item.is-active {
  color: var(--primary-color) !important;
}

html.dark .el-input__wrapper {
  background-color: var(--bg-input);
  box-shadow: 0 0 0 1px var(--border-color) inset !important;
}

html.dark .el-input__inner {
  color: var(--text-primary);
}

html.dark .el-input__inner::placeholder {
  color: var(--text-placeholder);
}

html.dark .el-select__wrapper {
  background-color: var(--bg-input);
  box-shadow: 0 0 0 1px var(--border-color) inset !important;
}

html.dark .el-select__placeholder {
  color: var(--text-placeholder);
}

html.dark .el-select__selected-item {
  color: var(--text-primary);
}

html.dark .el-button--default {
  background-color: var(--bg-elevated);
  border-color: var(--border-color);
  color: var(--text-regular);
}

html.dark .el-button--default:hover {
  background-color: var(--border-color);
  border-color: var(--primary-color);
  color: var(--primary-color);
}

html.dark .el-table {
  background-color: var(--bg-card);
  color: var(--text-regular);
  --el-table-bg-color: var(--bg-card);
  --el-table-tr-bg-color: var(--bg-card);
  --el-table-header-bg-color: var(--bg-elevated);
  --el-table-row-hover-bg-color: var(--primary-light);
  --el-table-border-color: var(--border-color);
  --el-table-text-color: var(--text-regular);
  --el-table-header-text-color: var(--text-primary);
}

html.dark .el-table th.el-table__cell {
  background-color: var(--bg-elevated);
  color: var(--text-primary);
}

html.dark .el-table tr {
  background-color: var(--bg-card);
}

html.dark .el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell {
  background-color: var(--bg-elevated);
}

html.dark .el-table__body tr:hover > td.el-table__cell {
  background-color: var(--primary-light) !important;
}

html.dark .el-table__cell {
  border-bottom-color: var(--border-color);
}

html.dark .el-pagination {
  color: var(--text-regular);
  --el-pagination-bg-color: var(--bg-elevated);
  --el-pagination-text-color: var(--text-regular);
  --el-pagination-button-disabled-bg-color: var(--bg-card);
}

html.dark .el-pagination button,
html.dark .el-pager li {
  background-color: var(--bg-elevated);
  color: var(--text-regular);
}

html.dark .el-pager li.is-active {
  color: var(--primary-color);
}

html.dark .el-tag {
  background-color: var(--primary-light);
  border-color: transparent;
  color: var(--primary-color);
}

html.dark .el-tag--success {
  --el-tag-bg-color: rgba(74, 222, 128, 0.1);
  --el-tag-border-color: transparent;
  --el-tag-text-color: var(--success-color);
}

html.dark .el-tag--warning {
  --el-tag-bg-color: rgba(251, 191, 36, 0.1);
  --el-tag-border-color: transparent;
  --el-tag-text-color: var(--warning-color);
}

html.dark .el-tag--danger {
  --el-tag-bg-color: rgba(248, 113, 113, 0.1);
  --el-tag-border-color: transparent;
  --el-tag-text-color: var(--error-color);
}

html.dark .el-tag--info {
  background-color: var(--bg-elevated);
  color: var(--text-secondary);
}

html.dark .el-alert {
  background-color: var(--bg-elevated);
  border-color: var(--border-color);
}

html.dark .el-alert--warning {
  background-color: rgba(251, 191, 36, 0.1);
  border-color: rgba(251, 191, 36, 0.3);
}

html.dark .el-alert--warning .el-alert__title,
html.dark .el-alert--warning .el-alert__description {
  color: var(--warning-color);
}

html.dark .el-alert--info {
  background-color: rgba(96, 165, 250, 0.1);
  border-color: rgba(96, 165, 250, 0.3);
}

html.dark .el-collapse-item__header {
  background-color: var(--bg-card);
  color: var(--text-primary);
  border-bottom-color: var(--border-color);
}

html.dark .el-collapse-item__wrap {
  background-color: var(--bg-card);
  border-bottom-color: var(--border-color);
}

html.dark .el-collapse-item__content {
  color: var(--text-regular);
}

html.dark .el-divider {
  border-color: var(--border-color);
}

html.dark .el-form-item__label {
  color: var(--text-primary);
}

html.dark .el-radio-button__inner {
  background-color: var(--bg-card);
  border-color: var(--border-color);
  color: var(--text-regular);
}

html.dark .el-radio-button__original-radio:checked + .el-radio-button__inner {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
  color: white;
}

html.dark .el-switch__core {
  border-color: var(--border-color);
  background-color: var(--bg-elevated);
}

html.dark .el-switch.is-checked .el-switch__core {
  background-color: var(--primary-color);
  border-color: var(--primary-color);
}

html.dark .el-input-number__decrease,
html.dark .el-input-number__increase {
  background-color: var(--bg-elevated);
  border-color: var(--border-color);
  color: var(--text-regular);
}

html.dark .el-empty__description {
  color: var(--text-secondary);
}

html.dark .el-dropdown-menu {
  background-color: var(--bg-card);
  border-color: var(--border-color);
}

html.dark .el-dropdown-menu__item {
  color: var(--text-regular);
}

html.dark .el-dropdown-menu__item:hover {
  background-color: var(--primary-light);
  color: var(--primary-color);
}

html.dark .el-tabs__header {
  background-color: var(--bg-card);
}

html.dark .el-tabs__item {
  color: var(--text-regular);
}

html.dark .el-tabs__item.is-active {
  color: var(--primary-color);
}

html.dark .el-statistic__head {
  color: var(--text-secondary);
}

html.dark .el-statistic__content {
  color: var(--text-primary);
}

/* 标题样式 */
html.dark h1, html.dark h2, html.dark h3, html.dark h4, html.dark h5, html.dark h6 {
  color: var(--text-primary);
}

/* 链接样式 */
html.dark a {
  color: var(--primary-color);
}

html.dark a:hover {
  color: var(--primary-hover);
}
</style>

<style scoped>
.app-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: var(--bg-page);
}

.app-header {
  background-color: var(--header-bg);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  position: sticky;
  top: 0;
  z-index: 1000;
  border-bottom: 1px solid var(--border-color);
}

.header-content {
  max-width: var(--content-width);
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 64px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 6px;
  border-radius: var(--radius-md);
  transition: background-color var(--transition-fast);
}

.logo:hover {
  background-color: var(--primary-light);
}

.logo-img {
  height: 32px;
  width: 32px;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.version-tag {
  font-size: 10px;
  padding: 0 5px;
  height: 18px;
  line-height: 16px;
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
  height: 64px;
}

.nav-item {
  font-size: 13px;
  font-weight: 500;
  height: 64px !important;
  line-height: 64px !important;
  padding: 0 14px !important;
  color: var(--text-regular) !important;
  position: relative;
}

.nav-item .el-icon {
  margin-right: 4px;
  font-size: 15px;
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
  height: 2px;
  background: var(--primary-gradient);
  transition: width var(--transition-fast), left var(--transition-fast);
  border-radius: 2px 2px 0 0;
}

.nav-item:hover::after,
.nav-item.is-active::after {
  width: 70%;
  left: 15%;
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
  gap: 8px;
}

.theme-toggle {
  width: 36px;
  height: 36px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-card);
  color: var(--text-regular);
  transition: all var(--transition-fast);
}

.theme-toggle:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
  background-color: var(--primary-light);
}

.lang-toggle {
  height: 36px;
  padding: 0 12px;
  border: 1px solid var(--border-color);
  background-color: var(--bg-card);
  color: var(--text-regular);
  transition: all var(--transition-fast);
}

.lang-toggle:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
  background-color: var(--primary-light);
}

.lang-flag {
  margin-right: 6px;
  font-size: 14px;
}

.lang-text {
  font-size: 13px;
}

.app-main {
  flex: 1;
  padding: 24px;
  max-width: var(--content-width);
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}

.app-footer {
  background-color: var(--footer-bg);
  padding: 24px;
  border-top: 1px solid var(--border-color);
  margin-top: auto;
}

.footer-content {
  max-width: var(--content-width);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.disclaimer {
  text-align: center;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border-color);
}

.disclaimer-text {
  color: var(--warning-color);
  font-size: 12px;
  line-height: 1.5;
}

.footer-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.copyright {
  color: var(--text-secondary);
  font-size: 12px;
}

.footer-links {
  display: flex;
  gap: 20px;
}

.footer-links a {
  color: var(--text-secondary);
  font-size: 12px;
  text-decoration: none;
  transition: color var(--transition-fast);
}

.footer-links a:hover {
  color: var(--primary-color);
}

/* 页面过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式 */
@media screen and (max-width: 1200px) {
  .nav-item {
    padding: 0 10px !important;
    font-size: 12px;
  }
  
  .nav-item .el-icon {
    display: none;
  }
  
  .lang-text {
    display: none;
  }
}

@media screen and (max-width: 768px) {
  .header-content {
    height: auto;
    padding: 10px;
    flex-wrap: wrap;
  }
  
  .logo {
    order: 1;
  }
  
  .header-tools {
    order: 2;
  }
  
  .app-nav {
    order: 3;
    width: 100%;
    margin-top: 8px;
  }
  
  .nav-menu {
    height: auto;
    width: 100%;
    display: flex;
    overflow-x: auto;
  }
  
  .nav-item {
    height: 40px !important;
    line-height: 40px !important;
    flex-shrink: 0;
  }
  
  .nav-item::after {
    display: none;
  }
  
  .app-main {
    padding: 16px;
  }
  
  .footer-bottom {
    flex-direction: column;
    gap: 8px;
    text-align: center;
  }
}
</style>
