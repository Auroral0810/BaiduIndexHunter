import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import i18n from './i18n'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { createPinia } from 'pinia'
import './assets/main.scss'
import locale from 'element-plus/dist/locale/zh-cn.mjs'

// 创建应用实例
const app = createApp(App)
const pinia = createPinia()

// 注册所有Element Plus图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// 使用插件
app.use(router)
app.use(i18n)
app.use(ElementPlus, { locale })
app.use(pinia)

// 挂载应用
app.mount('#app')
