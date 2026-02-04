import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh_cn.js'
import en from './locales/en.js'
import zhTW from './locales/zh-TW.js'
import ja from './locales/ja.js'
import ko from './locales/ko.js'
import ru from './locales/ru.js'
import fr from './locales/fr.js'
import de from './locales/de.js'
import es from './locales/es.js'

// 从 localStorage 获取保存的语言，默认为中文简体
const getStoredLanguage = () => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('language') || 'zh-CN'
  }
  return 'zh-CN'
}

const i18n = createI18n({
  legacy: false, // 使用 Composition API
  locale: getStoredLanguage(),
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'zh-TW': zhTW,
    'en': en,
    'ja': ja,
    'ko': ko,
    'ru': ru,
    'fr': fr,
    'de': de,
    'es': es
  }
})

export default i18n
