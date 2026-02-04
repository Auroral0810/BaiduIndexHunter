/**
 * 应用全局状态管理
 * 包含主题切换和语言切换功能
 */
import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

// 支持的语言列表
export const SUPPORTED_LANGUAGES = [
  { code: 'zh-CN', name: '简体中文', flag: '🇨🇳' },
  { code: 'zh-TW', name: '繁體中文', flag: '🇹🇼' },
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'ja', name: '日本語', flag: '🇯🇵' },
  { code: 'ko', name: '한국어', flag: '🇰🇷' },
  { code: 'ru', name: 'Русский', flag: '🇷🇺' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
]

// 主题列表
export const THEMES = [
  { code: 'light', name: '浅色', icon: 'Sunny' },
  { code: 'dark', name: '深色', icon: 'Moon' },
]

export const useAppStore = defineStore('app', () => {
  // 当前主题
  const theme = ref(localStorage.getItem('theme') || 'light')

  // 当前语言
  const language = ref(localStorage.getItem('language') || 'zh-CN')

  // 应用版本
  const version = ref('2.0.0')

  // 切换主题
  const setTheme = (newTheme) => {
    theme.value = newTheme
    localStorage.setItem('theme', newTheme)
    applyTheme(newTheme)
  }

  // 切换语言
  const setLanguage = (newLanguage) => {
    language.value = newLanguage
    localStorage.setItem('language', newLanguage)
    // 触发语言变更事件，供 i18n 使用
    window.dispatchEvent(new CustomEvent('language-change', { detail: newLanguage }))
  }

  // 应用主题到 DOM
  const applyTheme = (themeName) => {
    const root = document.documentElement

    // 移除之前的类
    root.classList.remove('dark', 'light')
    root.classList.add(themeName)
  }

  // 初始化主题
  const initTheme = () => {
    applyTheme(theme.value)
  }

  // 获取当前语言信息
  const getCurrentLanguage = () => {
    return SUPPORTED_LANGUAGES.find(lang => lang.code === language.value) || SUPPORTED_LANGUAGES[0]
  }

  // 是否是深色主题
  const isDark = () => theme.value === 'dark'

  return {
    theme,
    language,
    version,
    setTheme,
    setLanguage,
    initTheme,
    getCurrentLanguage,
    isDark,
    SUPPORTED_LANGUAGES,
    THEMES,
  }
})
