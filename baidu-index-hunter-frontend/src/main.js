import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { createPinia } from 'pinia'
import './assets/main.scss'
import locale from 'element-plus/dist/locale/zh-cn.mjs'

// 创建应用实例
const app = createApp(App)

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
  --content-width: 1200px;
}
`
document.head.appendChild(style)

// 使用插件
app.use(router)
app.use(ElementPlus, { locale })
app.use(createPinia())

// 挂载应用
app.mount('#app')
