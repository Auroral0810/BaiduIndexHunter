<script setup>
import { ref, watch, onMounted, computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { useAppStore, SUPPORTED_LANGUAGES } from "./store/app";
import { Sunny, Moon } from "@element-plus/icons-vue";
import { useI18n } from "vue-i18n";

const { t: $t, locale } = useI18n();
const router = useRouter();
const route = useRoute();
const appStore = useAppStore();
const activeIndex = ref("1");

// 监听当前路由以更新菜单高亮项
const routeMap = {
  "/": "1",
  "/data-collection": "2",
  "/cookie-manager": "3",
  "/dashboard": "4",
  "/settings": "5",
  "/about": "6",
  "/privacy": "7",
};

// 根据当前路径更新激活的菜单项
const updateActiveMenu = () => {
  const path = route.path;
  activeIndex.value = routeMap[path] || "1";
};

// 监听路由变化
watch(
  () => route.path,
  () => {
    updateActiveMenu();
  },
);

// 初始更新菜单项
updateActiveMenu();

const handleSelect = (key) => {
  switch (key) {
    case "1":
      router.push("/");
      break;
    case "2":
      router.push("/data-collection");
      break;
    case "3":
      router.push("/cookie-manager");
      break;
    case "4":
      router.push("/dashboard");
      break;
    case "5":
      router.push("/settings");
      break;
    case "6":
      router.push("/about");
      break;
    case "7":
      router.push("/privacy");
      break;
  }
};

// 主题切换
const isDark = computed(() => appStore.theme === "dark");
const toggleTheme = () => {
  appStore.setTheme(isDark.value ? "light" : "dark");
};

// 语言切换
const currentLanguage = computed(() => appStore.getCurrentLanguage());
const handleLanguageChange = (langCode) => {
  appStore.setLanguage(langCode);
  locale.value = langCode; // 实际更新 vue-i18n 的 locale
};

// 初始化主题和语言
onMounted(() => {
  appStore.initTheme();
  // 从 localStorage 恢复语言设置
  const savedLanguage = localStorage.getItem("language") || "zh-CN";
  locale.value = savedLanguage;
});
</script>

<template>
  <div class="app-wrapper">
    <header class="app-header">
      <div class="header-container">
        <div class="logo-area" @click="router.push('/')">
          <img src="@/assets/logo.svg" alt="Logo" class="logo-image" />
          <div class="logo-text">
            <span>BaiduIndex</span> <span class="logo-suffix">Hunter</span>
          </div>
          <el-tag size="small" type="primary" effect="light" class="version-tag"
            >v {{ appStore.version }}</el-tag
          >
        </div>
        <nav class="app-nav">
          <el-menu
            :default-active="activeIndex"
            mode="horizontal"
            @select="handleSelect"
            class="nav-menu"
            :ellipsis="false"
            ><el-menu-item index="1" class="nav-item">{{
              $t("src-App-19c2993710803cda7-1")
            }}</el-menu-item>
            <el-menu-item index="2" class="nav-item">{{
              $t("src-App-19c2993710803cda7-2")
            }}</el-menu-item>
            <el-menu-item index="3" class="nav-item">{{
              $t("src-App-19c2993710803cda7-3")
            }}</el-menu-item>
            <el-menu-item index="4" class="nav-item">{{
              $t("src-App-19c2993710803cda7-4")
            }}</el-menu-item>
            <el-menu-item index="5" class="nav-item">{{
              $t("src-App-19c2993710803cda7-5")
            }}</el-menu-item>
            <el-menu-item index="6" class="nav-item">{{
              $t("src-App-19c2993710803cda7-6")
            }}</el-menu-item>
            <el-menu-item index="7" class="nav-item">{{
              $t("src-App-19c2993710803cda7-7")
            }}</el-menu-item></el-menu
          >
        </nav>
        <!-- 右侧工具栏 -->
        <div class="header-tools">
          <!-- 主题切换按钮 -->
          <button
            class="theme-toggle-btn"
            @click="toggleTheme"
            :title="
              isDark
                ? $t('src-App-19c2993710803cda7-8')
                : $t('src-App-19c2993710803cda7-9')
            "
          >
            <el-icon v-if="isDark" class="theme-icon"><Moon /></el-icon>
            <el-icon v-else class="theme-icon"><Sunny /></el-icon>
          </button>
          <!-- 语言切换 -->
          <el-dropdown
            trigger="click"
            @command="handleLanguageChange"
            popper-class="language-popper"
            ><button class="language-btn">
              <span class="language-flag">{{ currentLanguage.flag }}</span>
              <span class="language-code">{{
                currentLanguage.code.split("-")[0].toUpperCase()
              }}</span>
            </button>
            <template #dropdown
              ><el-dropdown-menu
                ><el-dropdown-item
                  v-for="lang in SUPPORTED_LANGUAGES"
                  :key="lang.code"
                  :command="lang.code"
                  :class="{ 'is-active': appStore.language === lang.code }"
                  ><span class="dropdown-flag">{{ lang.flag }}</span>
                  <span class="dropdown-name">{{
                    lang.name
                  }}</span></el-dropdown-item
                ></el-dropdown-menu
              ></template
            ></el-dropdown
          >
        </div>
      </div>
    </header>
    <main class="app-main">
      <router-view v-slot="{ Component }"
        ><transition name="fade-slide" mode="out-in"
          ><component :is="Component" /></transition
      ></router-view>
    </main>
    <footer class="app-footer">
      <div class="footer-container">
        <div class="footer-left">
          <div class="footer-logo">BaiduIndexHunter</div>
          <div class="footer-desc">
            {{ $t("src-App-19c2993710803cda7-10") }}
          </div>
          <div class="copyright">
            © {{ new Date().getFullYear() }} v {{ appStore.version }}
          </div>
        </div>
        <div class="footer-right">
          <a href="#" @click.prevent="router.push('/about')">{{
            $t("src-App-19c2993710803cda7-11")
          }}</a>
          <a href="#" @click.prevent="router.push('/privacy')">{{
            $t("src-App-19c2993710803cda7-12")
          }}</a>
          <a href="#" @click.prevent="router.push('/data-collection')">{{
            $t("src-App-19c2993710803cda7-13")
          }}</a>
        </div>
      </div>
    </footer>
  </div>
</template>

<style>
@import url("https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap");

:root {
  /* 现代 SaaS 色彩体系 (Light Mode) */
  --color-primary: #4f46e5;
  --color-primary-hover: #4338ca;
  --color-primary-light: rgba(79, 70, 229, 0.1);
  --color-primary-gradient: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);

  --color-success: #10b981;
  --color-warning: #f59e0b;
  --color-danger: #ef4444;
  --color-info: #64748b;

  --color-bg-body: #f8fafc;
  --color-bg-surface: #ffffff;
  --color-bg-subtle: #f1f5f9;

  --color-text-main: #0f172a;
  --color-text-secondary: #475569;
  --color-text-tertiary: #94a3b8;

  --color-border: #e2e8f0;
  --color-border-hover: #cbd5e1;

  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md:
    0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -1px rgba(0, 0, 0, 0.04);
  --shadow-lg:
    0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.03);
  --shadow-xl:
    0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  --shadow-primary: 0 4px 14px 0 rgba(79, 70, 229, 0.25);

  --glass-bg: rgba(255, 255, 255, 0.7);
  --glass-border: rgba(255, 255, 255, 0.4);
  --glass-blur: blur(12px);

  --font-family:
    "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  --header-height: 72px;
  --max-width: 1400px;
  --radius-base: 10px;
  --radius-lg: 16px;
  --radius-xl: 24px;
}

/* 深色模式变量覆盖 */
/* 深色模式变量覆盖 */
html.dark {
  --color-primary: #6366f1;
  --color-primary-hover: #818cf8;
  --color-primary-light: rgba(99, 102, 241, 0.15);
  --color-primary-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);

  --color-bg-body: #020617;
  --color-bg-surface: #0f172a;
  --color-bg-subtle: #1e293b;

  --color-text-main: #f8fafc;
  --color-text-secondary: #cbd5e1;
  --color-text-tertiary: #64748b;

  --color-border: #1e293b;
  --color-border-hover: #334155;

  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.4);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.4);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.4);
  --shadow-xl: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
  --shadow-primary: 0 4px 14px 0 rgba(99, 102, 241, 0.3);

  --glass-bg: rgba(15, 23, 42, 0.75);
  --glass-border: rgba(255, 255, 255, 0.1);
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
  transition:
    background-color 0.3s ease,
    color 0.3s ease;
  -webkit-font-smoothing: antialiased;
}

/* 覆盖 Element Plus 默认样式以匹配新主题 */
:root {
  --el-color-primary: #4f46e5;
  --el-color-primary-light-3: #818cf8;
  --el-color-primary-light-5: #a5b4fc;
  --el-color-primary-light-7: #c7d2fe;
  --el-color-primary-light-9: #e0e7ff;
  --el-menu-active-color: #4f46e5;
  --el-menu-hover-text-color: #4f46e5;
  --el-bg-color: var(--color-bg-surface);
  --el-text-color-primary: var(--color-text-main);
  --el-text-color-regular: var(--color-text-secondary);
  --el-border-color: var(--color-border);
  --el-border-radius-base: var(--radius-base);
}

html.dark {
  --el-color-primary: #818cf8;
  --el-menu-active-color: #818cf8;
  --el-menu-hover-text-color: #818cf8;
}

html.dark {
  --el-bg-color: var(--color-bg-surface);
  --el-bg-color-overlay: var(--color-bg-subtle);
  --el-fill-color-blank: var(--color-bg-body);
}

/* 强制覆盖 Element Plus 菜单激活颜色 */
.el-menu--horizontal .el-menu-item.is-active {
  color: #4f46e5 !important;
  border-bottom-color: transparent !important;
}

.el-menu--horizontal .el-menu-item:not(.is-disabled):hover {
  color: #4f46e5 !important;
}

html.dark .el-menu--horizontal .el-menu-item.is-active {
  color: #818cf8 !important;
}

html.dark .el-menu--horizontal .el-menu-item:not(.is-disabled):hover {
  color: #818cf8 !important;
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

html.dark .app-header {
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

.logo-image {
  height: 32px;
  width: auto;
  object-fit: contain;
  transition: transform 0.3s ease;
}

.logo-area:hover .logo-image {
  transform: scale(1.05);
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
  color: #4f46e5 !important;
  background-color: var(--color-bg-subtle) !important;
}

/* 深色模式下 hover 颜色 */
html.dark .nav-item:hover {
  color: #818cf8 !important;
}

.nav-item.is-active {
  color: #4f46e5 !important;
  background-color: var(--color-primary-light) !important;
  font-weight: 600 !important;
}

/* 深色模式下激活菜单的颜色 */
html.dark .nav-item.is-active {
  color: #818cf8 !important;
}

/* 覆盖 Element Plus 菜单的默认激活样式 */
:deep(.el-menu--horizontal .el-menu-item.is-active) {
  color: #4f46e5 !important;
  border-bottom: none !important;
}

:deep(.el-menu--horizontal .el-menu-item:not(.is-disabled):hover) {
  color: #4f46e5 !important;
}

/* 深色模式下的 Element Plus 菜单覆盖 */
:global(html.dark) :deep(.el-menu--horizontal .el-menu-item.is-active) {
  color: #818cf8 !important;
}

:global(html.dark) :deep(.el-menu--horizontal .el-menu-item:not(.is-disabled):hover) {
  color: #818cf8 !important;
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

.language-code {
  font-size: 0.8rem;
  font-weight: 600;
}

/* 语言下拉菜单样式 */
.dropdown-flag {
  font-size: 1.2rem;
  margin-right: 10px;
}

.dropdown-name {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

/* 语言下拉菜单项激活状态 */
:deep(.el-dropdown-menu__item.is-active) {
  background-color: var(--color-primary-light);
  color: var(--color-primary);
}

:deep(.el-dropdown-menu__item.is-active .dropdown-name) {
  color: var(--color-primary);
  font-weight: 600;
}

:deep(.el-dropdown-menu__item) {
  display: flex;
  align-items: center;
  padding: 10px 16px;
}

:deep(.el-dropdown-menu__item:hover) {
  background-color: var(--color-bg-subtle);
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
  transition:
    opacity 0.3s ease,
    transform 0.3s ease;
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
