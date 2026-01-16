import { defineStore } from 'pinia'
import request from '../utils/request'

export const useConfigStore = defineStore('config', {
  state: () => ({
    configs: {},
    loading: false,
    error: null,
    initialized: false
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
    async fetchConfigs() {
      this.loading = true;
      this.error = null;
      
      try {
        const response = await request.get('/config/list');
        // request拦截器已经处理了 code !== 10000 的情况并返回response.data
        // 这里response是后端返回的完整json对象
        this.configs = response.data || {};
        this.initialized = true;
      } catch (error) {
        console.error('获取配置数据出错:', error);
        this.error = error.message || '获取配置失败';
      } finally {
        this.loading = false;
      }
    },
    
    async saveConfigs(configsToSave) {
      this.loading = true;
      this.error = null;
      
      try {
        await request.post('/config/batch_set', configsToSave);
        // 保存成功后，本地状态已经是最新的（因为是v-model绑定的），
        // 但为了保险起见，可以重新获取一次，或者直接认为本地已经是新的
        // 这里我们不需要手动更新 this.configs，因为 Settings.vue 是直接修改的 store state
        return true;
      } catch (error) {
        console.error('保存配置数据出错:', error);
        this.error = error.message || '保存配置失败';
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
        await request.post('/config/init_defaults');
        // 重新获取配置
        await this.fetchConfigs();
        return true;
      } catch (error) {
        console.error('重置配置数据出错:', error);
        this.error = error.message || '重置配置失败';
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