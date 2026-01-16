<script setup>
import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()
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
</script>

<template>
  <div class="app-wrapper">
    <header class="app-header">
      <div class="header-content">
        <div class="logo" @click="router.push('/')">
          <img src="./assets/logo.svg" alt="BaiduIndexHunter" class="logo-img">
          <span class="logo-text">BaiduIndexHunter</span>
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
              <span>关于我们</span>
            </el-menu-item>
            <el-menu-item index="7" class="nav-item">
              <el-icon><i-ep-lock /></el-icon>
              <span>隐私政策</span>
            </el-menu-item>
          </el-menu>
        </nav>
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
          © {{ new Date().getFullYear() }} BaiduIndexHunter - 高效的百度指数数据采集与分析工具
        </div>
        <div class="footer-links">
          <a href="#" @click.prevent="router.push('/about')">关于我们</a>
          <a href="#" @click.prevent="router.push('/privacy')">隐私政策</a>
        </div>
      </div>
    </footer>
  </div>
</template>

<style>
:root {
  /* 品牌色系 - 现代蓝紫渐变 */
  --primary-color: #3b82f6;
  --primary-hover: #2563eb;
  --primary-light: #eff6ff;
  --primary-gradient: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  --secondary-gradient: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
  
  /* 文字颜色 */
  --text-primary: #111827;
  --text-regular: #4b5563;
  --text-secondary: #9ca3af;
  --text-placeholder: #d1d5db;
  
  /* 背景颜色 */
  --background-color: #f3f4f6;
  --surface-color: #ffffff;
  --border-color: #e5e7eb;
  
  /* 阴影系统 */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  
  /* 圆角 */
  --radius-sm: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 1rem;
  --radius-full: 9999px;
  
  --content-width: 1280px;
}

body {
  margin: 0;
  padding: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  color: var(--text-regular);
  background-color: var(--background-color);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* 滚动条美化 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
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
  background-image: 
    radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.05) 0px, transparent 50%),
    radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.05) 0px, transparent 50%);
  background-attachment: fixed;
}

.app-header {
  background-color: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  position: sticky;
  top: 0;
  z-index: 1000;
  border-bottom: 1px solid rgba(229, 231, 235, 0.5);
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
  background-color: rgba(59, 130, 246, 0.05);
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

.app-nav {
  height: 100%;
  display: flex;
  align-items: center;
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

/* 导航项下划线动画 */
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

/* 页面过渡动画优化 */
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
