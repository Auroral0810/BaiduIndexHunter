/**
 * 国际化配置
 * 语言文件放在 locales 目录下
 */

// 默认语言
export const defaultLocale = 'zh-CN'

// 支持的语言
export const supportedLocales = [
  'zh-CN',  // 简体中文
  'zh-TW',  // 繁体中文
  'en',     // 英语
  'ja',     // 日语
  'ko',     // 韩语
  'ru',     // 俄语
  'fr',     // 法语
  'de',     // 德语
  'es',     // 西班牙语
]

// 语言文件缓存
const localeMessages = {}

/**
 * 加载语言文件
 * @param {string} locale 语言代码
 */
export async function loadLocale(locale) {
  if (localeMessages[locale]) {
    return localeMessages[locale]
  }
  
  try {
    const messages = await import(`./locales/${locale}.js`)
    localeMessages[locale] = messages.default
    return messages.default
  } catch (e) {
    console.warn(`Language file for ${locale} not found, falling back to ${defaultLocale}`)
    return null
  }
}

/**
 * 获取翻译文本
 * @param {string} key 翻译键
 * @param {string} locale 语言代码
 */
export function t(key, locale = defaultLocale) {
  const messages = localeMessages[locale] || localeMessages[defaultLocale] || {}
  
  // 支持嵌套键 如 'menu.home'
  const keys = key.split('.')
  let value = messages
  
  for (const k of keys) {
    if (value && typeof value === 'object' && k in value) {
      value = value[k]
    } else {
      return key // 未找到翻译，返回原键
    }
  }
  
  return typeof value === 'string' ? value : key
}

export default {
  defaultLocale,
  supportedLocales,
  loadLocale,
  t,
}
