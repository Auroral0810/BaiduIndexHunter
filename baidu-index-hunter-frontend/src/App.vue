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
  '/settings': '4',
  '/about': '5',
  '/privacy': '6'
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
      router.push('/settings')
      break
    case '5':
      router.push('/about')
      break
    case '6':
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
              <el-icon><i-ep-setting /></el-icon>
              <span>配置信息</span>
            </el-menu-item>
            <el-menu-item index="5" class="nav-item">
              <el-icon><i-ep-info-filled /></el-icon>
              <span>关于我们</span>
            </el-menu-item>
            <el-menu-item index="6" class="nav-item">
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
          <a href="https://github.com/Auroral0810/baidu-index-hunter" target="_blank">GitHub</a>
        </div>
      </div>
    </footer>
  </div>
</template>

<style>
:root {
  --primary-color: #4facfe;
  --primary-light: #f0f9ff;
  --primary-gradient: linear-gradient(to right, #4facfe, #00f2fe);
  --text-primary: #303133;
  --text-regular: #606266;
  --text-secondary: #909399;
  --border-color: #DCDFE6;
  --border-lighter: #EBEEF5;
  --background-color: #f5f7fa;
  --white: #ffffff;
  --shadow-light: 0 2px 12px rgba(0, 0, 0, 0.08);
  --shadow-hover: 0 10px 20px rgba(79, 172, 254, 0.15);
  --content-width: 1200px;
}

body {
  margin: 0;
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  color: var(--text-regular);
  background-color: var(--background-color);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
</style>

<style scoped>
.app-wrapper {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.app-header {
  background-color: var(--white);
  box-shadow: var(--shadow-light);
  position: sticky;
  top: 0;
  z-index: 1000;
  padding: 0;
  border-bottom: 1px solid var(--border-lighter);
}

.header-content {
  max-width: var(--content-width);
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 64px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.logo:hover {
  transform: scale(1.02);
}

.logo-img {
  height: 36px;
  width: 36px;
}

.logo-text {
  font-size: 20px;
  font-weight: 600;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.app-nav {
  height: 100%;
}

.nav-menu {
  height: 64px;
  border-bottom: none !important;
}

.nav-item {
  font-size: 15px;
  height: 64px !important;
  line-height: 64px !important;
  padding: 0 16px !important;
  transition: all 0.25s ease;
}

.nav-item .el-icon {
  margin-right: 6px;
  font-size: 16px;
}

.nav-item:hover {
  color: var(--primary-color) !important;
  background-color: var(--primary-light) !important;
}

.nav-item.is-active {
  color: var(--primary-color) !important;
  border-bottom: 2px solid var(--primary-color) !important;
}

.app-main {
  flex: 1;
  padding: 24px 20px;
  max-width: var(--content-width);
  width: 100%;
  margin: 0 auto;
  box-sizing: border-box;
}

.app-footer {
  background-color: var(--white);
  padding: 24px 20px;
  border-top: 1px solid var(--border-lighter);
  margin-top: auto;
}

.footer-content {
  max-width: var(--content-width);
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.copyright {
  color: var(--text-secondary);
  font-size: 13px;
}

.footer-links {
  display: flex;
  gap: 20px;
}

.footer-links a {
  color: var(--text-secondary);
  font-size: 13px;
  text-decoration: none;
  transition: color 0.2s ease;
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

@media screen and (max-width: 768px) {
  .header-content {
    flex-direction: column;
    height: auto;
    padding: 10px;
  }
  
  .logo {
    margin-bottom: 10px;
  }
  
  .app-nav,
  .nav-menu {
    width: 100%;
  }
  
  .nav-item {
    padding: 0 10px !important;
    height: 48px !important;
    line-height: 48px !important;
  }
  
  .app-main {
    padding: 16px;
  }
  
  .footer-content {
    flex-direction: column;
    gap: 10px;
    text-align: center;
  }
  
  .footer-links {
    justify-content: center;
  }
}
</style>
