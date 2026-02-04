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
    
    if (themeName === 'dark') {
      root.classList.add('dark')
      root.style.setProperty('--background-color', '#1a1a2e')
      root.style.setProperty('--surface-color', '#16213e')
      root.style.setProperty('--text-primary', '#e4e6eb')
      root.style.setProperty('--text-regular', '#b0b3b8')
      root.style.setProperty('--text-secondary', '#8a8d91')
      root.style.setProperty('--border-color', '#3a3a4a')
      root.style.setProperty('--border-lighter', '#2d2d3a')
      root.style.setProperty('--shadow-sm', '0 1px 2px 0 rgba(0, 0, 0, 0.3)')
      root.style.setProperty('--shadow-md', '0 4px 6px -1px rgba(0, 0, 0, 0.3)')
      root.style.setProperty('--shadow-lg', '0 10px 15px -3px rgba(0, 0, 0, 0.3)')
    } else {
      root.classList.remove('dark')
      root.style.setProperty('--background-color', '#f8fafc')
      root.style.setProperty('--surface-color', '#ffffff')
      root.style.setProperty('--text-primary', '#0f172a')
      root.style.setProperty('--text-regular', '#334155')
      root.style.setProperty('--text-secondary', '#64748b')
      root.style.setProperty('--border-color', '#e2e8f0')
      root.style.setProperty('--border-lighter', '#f1f5f9')
      root.style.setProperty('--shadow-sm', '0 1px 2px 0 rgba(0, 0, 0, 0.05)')
      root.style.setProperty('--shadow-md', '0 4px 6px -1px rgba(0, 0, 0, 0.05)')
      root.style.setProperty('--shadow-lg', '0 10px 15px -3px rgba(0, 0, 0, 0.05)')
    }
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
