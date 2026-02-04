import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { createPinia } from 'pinia'
import './assets/main.scss'

// Element Plus 多语言支持
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import zhTw from 'element-plus/dist/locale/zh-tw.mjs'
import en from 'element-plus/dist/locale/en.mjs'
import ja from 'element-plus/dist/locale/ja.mjs'

// i18n 国际化
import i18n from './i18n'

// 获取保存的语言设置
const savedLocale = localStorage.getItem('ui.language') || 'zh_CN'

// Element Plus 语言映射
const elementLocaleMap = {
  'zh_CN': zhCn,
  'zh_TW': zhTw,
  'en': en,
  'ja': ja
}

// 创建应用实例
const app = createApp(App)
const pinia = createPinia()

// 注册所有Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 创建CSS变量
const style = document.createElement('style')
style.innerHTML = `
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
  --shadow-medium: 0 4px 16px rgba(0, 0, 0, 0.12);
  --content-width: 1200px;
  --border-radius-small: 4px;
  --border-radius-medium: 8px;
  --border-radius-large: 12px;
}
`
document.head.appendChild(style)

// 应用保存的主题
const savedTheme = localStorage.getItem('ui.theme') || 'light'
if (savedTheme === 'dark') {
  document.documentElement.classList.add('dark')
}

// 使用插件
app.use(router)
app.use(ElementPlus, { locale: elementLocaleMap[savedLocale] || zhCn })
app.use(pinia)
app.use(i18n)

// 挂载应用
app.mount('#app')
