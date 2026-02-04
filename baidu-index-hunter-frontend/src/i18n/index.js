import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh-CN'
import zhTW from './locales/zh-TW'
import en from './locales/en'
import ja from './locales/ja'

// 从 localStorage 获取语言设置，默认简体中文
const savedLocale = localStorage.getItem('ui.language') || 'zh_CN'

// 映射语言代码
const localeMap = {
  'zh_CN': 'zh-CN',
  'zh_TW': 'zh-TW',
  'en': 'en',
  'ja': 'ja'
}

const i18n = createI18n({
  legacy: false, // 使用 Composition API 模式
  locale: localeMap[savedLocale] || 'zh-CN',
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'zh-TW': zhTW,
    'en': en,
    'ja': ja
  }
})

// 切换语言的辅助函数
export function setLocale(locale) {
  const mappedLocale = localeMap[locale] || locale
  i18n.global.locale.value = mappedLocale
  localStorage.setItem('ui.language', locale)
  document.querySelector('html').setAttribute('lang', mappedLocale)
}

// 获取当前语言
export function getLocale() {
  return i18n.global.locale.value
}

export default i18n
