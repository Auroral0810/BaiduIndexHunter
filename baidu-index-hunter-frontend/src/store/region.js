import { defineStore } from 'pinia'
import axios from 'axios'

export const useRegionStore = defineStore('region', {
  state: () => ({
    provinces: {},
    provinceCities: {},
    allCities: {},
    loading: false,
    error: null,
    initialized: false,
    apiBaseUrl: 'http://127.0.0.1:5001/api'
  }),
  
  getters: {
    getProvincesList: (state) => state.provinces,
    getProvinceCities: (state) => state.provinceCities,
    getAllCities: (state) => state.allCities,
    isLoading: (state) => state.loading,
    getError: (state) => state.error,
    isInitialized: (state) => state.initialized,
    
    getProvinceName: (state) => (provinceCode) => {
      if (state.provinces[provinceCode]) {
        return state.provinces[provinceCode].name;
      }
      return provinceCode;
    },
    
    getCityName: (state) => (cityCode) => {
      if (cityCode === '0') {
        return '全国';
      }
      
      if (state.allCities[cityCode]) {
        return state.allCities[cityCode].name;
      }
      
      for (const provinceCode in state.provinceCities) {
        const province = state.provinceCities[provinceCode];
        if (province.cities && province.cities[cityCode]) {
          return province.cities[cityCode].name;
        }
      }
      
      return cityCode;
    }
  },
  
  actions: {
    setApiBaseUrl(url) {
      this.apiBaseUrl = url;
    },
    
    async fetchRegionData() {
      if (this.initialized) return;
      
      this.loading = true;
      this.error = null;
      
      try {
        // 获取所有省份
        const provincesResponse = await axios.get(`${this.apiBaseUrl}/region/provinces`);
        if (provincesResponse.data.code === 0 || provincesResponse.data.code === 10000) {
          this.provinces = provincesResponse.data.data.provinces || {};
        }
        
        // 获取省份城市关系
        const citiesResponse = await axios.get(`${this.apiBaseUrl}/region/province/cities`);
        if (citiesResponse.data.code === 0 || citiesResponse.data.code === 10000) {
          this.provinceCities = citiesResponse.data.data.provinces || {};
          
          // 构建所有城市的映射
          const allCities = {};
          
          // 添加全国选项
          allCities['0'] = { name: '全国', code: '0' };
          
          // 添加所有城市
          for (const provinceCode in this.provinceCities) {
            const province = this.provinceCities[provinceCode];
            if (province.cities) {
              Object.keys(province.cities).forEach(cityCode => {
                allCities[cityCode] = province.cities[cityCode];
              });
            }
          }
          
          this.allCities = allCities;
        }
        
        this.initialized = true;
      } catch (error) {
        console.error('获取区域数据出错:', error);
        this.error = '网络错误，请稍后重试';
      } finally {
        this.loading = false;
      }
    },
    
    // 验证导入的城市代码是否存在
    validateCityCodes(cityCodes) {
      if (!this.initialized) {
        throw new Error('区域数据尚未初始化，请先调用 fetchRegionData');
      }
      
      const validCodes = [];
      const invalidCodes = [];
      
      cityCodes.forEach(code => {
        // 检查是否是省份代码
        if (this.provinces[code]) {
          validCodes.push(code);
        }
        // 检查是否是城市代码
        else if (this.allCities[code] || code === '0') {
          validCodes.push(code);
        }
        else {
          invalidCodes.push(code);
        }
      });
      
      return {
        validCodes,
        invalidCodes
      };
    }
  }
}) 