import { defineStore } from 'pinia'
import axios from 'axios'

export const useConfigStore = defineStore('config', {
  state: () => ({
    configs: {},
    loading: false,
    error: null,
    initialized: false,
    apiBaseUrl: 'http://127.0.0.1:5001/api'
  }),
  
  getters: {
    getConfigs: (state) => state.configs,
    getConfigByKey: (state) => (key) => state.configs[key],
    getConfigsByPrefix: (state) => (prefix) => {
      const result = {};
      for (const key in state.configs) {
        if (key.startsWith(`${prefix}.`)) {
          result[key] = state.configs[key];
        }
      }
      return result;
    },
    isLoading: (state) => state.loading,
    getError: (state) => state.error,
    isInitialized: (state) => state.initialized
  },
  
  actions: {
    setApiBaseUrl(url) {
      this.apiBaseUrl = url;
    },
    
    async fetchConfigs() {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.get(`${this.apiBaseUrl}/config/list`);
        if (response.data.code === 0 || response.data.code === 10000) {
          this.configs = response.data.data || {};
          this.initialized = true;
        } else {
          this.error = response.data.message || '获取配置失败';
        }
      } catch (error) {
        console.error('获取配置数据出错:', error);
        this.error = '网络错误，请稍后重试';
      } finally {
        this.loading = false;
      }
    },
    
    async saveConfigs(configsToSave) {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.post(`${this.apiBaseUrl}/config/batch_set`, configsToSave);
        if (response.data.code === 0 || response.data.code === 10000) {
          // 更新本地存储的配置
          for (const key in configsToSave) {
            this.configs[key] = configsToSave[key];
          }
          return true;
        } else {
          this.error = response.data.message || '保存配置失败';
          return false;
        }
      } catch (error) {
        console.error('保存配置数据出错:', error);
        this.error = '网络错误，请稍后重试';
        return false;
      } finally {
        this.loading = false;
      }
    },
    
    async saveConfigsByPrefix(prefix) {
      const configsToSave = this.getConfigsByPrefix(prefix);
      return await this.saveConfigs(configsToSave);
    },
    
    async resetConfigs() {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await axios.post(`${this.apiBaseUrl}/config/init_defaults`);
        if (response.data.code === 0 || response.data.code === 10000) {
          // 重新获取配置
          await this.fetchConfigs();
          return true;
        } else {
          this.error = response.data.message || '重置配置失败';
          return false;
        }
      } catch (error) {
        console.error('重置配置数据出错:', error);
        this.error = '网络错误，请稍后重试';
        return false;
      } finally {
        this.loading = false;
      }
    },
    
    updateConfig(key, value) {
      this.configs[key] = value;
    }
  }
}) 