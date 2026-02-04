import { createI18n } from 'vue-i18n'
import zhCN from './locales/zh_CN.js'
import en from './locales/en.js'
import zhTW from './locales/zh-TW.js'
import ja from './locales/ja.js'
import ko from './locales/ko.js'
import ru from './locales/ru.js'
import fr from './locales/fr.js'
import de from './locales/de.js'
import es from './locales/es.js'

const i18n = createI18n({
  legacy: false, // Set to false to use Composition API
  locale: 'zh-CN',
  fallbackLocale: 'zh-CN',
  messages: {
    'en': en,
    'zh-CN': zhCN,
    'zh-TW': zhTW,
    'ja': ja,
    'ko': ko,
    'ru': ru,
    'fr': fr,
    'de': de,
    'es': es
  }
})

export default i18n
