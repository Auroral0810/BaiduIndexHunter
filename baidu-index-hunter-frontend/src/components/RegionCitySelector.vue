<template>
  <div class="region-city-selector">
    <!-- 省份和城市选择区域 -->
    <div class="selector-container">
      <!-- 省份选择 -->
      <div class="province-list">
        <!-- 全国选项 -->
        <div class="province-item special-item" @click="selectNationwide">
          <el-checkbox 
            v-model="nationwideSelected"
            @change="handleNationwideCheck"
            @click.stop
          >
            全国
          </el-checkbox>
        </div>
        
        <!-- 省份选择操作 -->
        <div class="province-actions">
          <el-button type="text" size="small" @click="selectAllProvinces">全选省份</el-button>
          <el-button type="text" size="small" @click="unselectAllProvinces">取消全选</el-button>
        </div>
        
        <!-- 全选地级市按钮 -->
        <div class="province-actions">
          <el-button type="text" size="small" @click="selectAllCities">全选地级市</el-button>
          <el-button type="text" size="small" @click="unselectAllCities">取消全选</el-button>
        </div>
        
        <!-- 省份列表 -->
        <div class="province-item" 
          v-for="(province, code) in provincesList" 
          :key="code"
          :class="{ active: selectedProvince === code }"
          @click="selectProvince(code)"
        >
          <el-checkbox 
            v-model="provinceChecked[code]"
            @change="(val) => handleProvinceCheck(code, val)"
            @click.stop
          >
            {{ province.name }}
          </el-checkbox>
        </div>
      </div>
      
      <!-- 城市选择 -->
      <div class="city-list">
        <div v-if="selectedProvince && currentProvinceCities">
          <div class="city-header">
            <span class="province-name">{{ getCurrentProvinceName() }}</span>
            <div class="actions">
              <el-button type="text" size="small" @click="selectAllCitiesInProvince">全选</el-button>
              <el-button type="text" size="small" @click="unselectAllCitiesInProvince">取消全选</el-button>
            </div>
          </div>
          
          <div class="city-grid">
            <div 
              v-for="(city, cityCode) in currentProvinceCities" 
              :key="cityCode" 
              class="city-item"
            >
              <el-checkbox 
                v-model="cityChecked[cityCode]"
                @change="() => handleCityCheck(cityCode)"
              >
                {{ city.name }}
              </el-checkbox>
            </div>
          </div>
        </div>
        <div v-else class="no-city-selected">
          请选择左侧省份
        </div>
      </div>
    </div>
    
    <!-- 已选城市展示区域 -->
    <div class="selected-cities" v-if="hasSelectedCities || nationwideSelected || hasSelectedProvinces">
      <div class="selected-header">
        <span>已选择区域:</span>
        <el-button type="text" size="small" @click="clearAllSelection">清空选择</el-button>
      </div>
      <div class="selected-tags">
        <!-- 全国标签 -->
        <el-tag
          v-if="nationwideSelected"
          closable
          size="small"
          @close="unselectNationwide"
          class="city-tag"
        >
          全国
        </el-tag>
        
        <!-- 省份标签 -->
        <el-tag
          v-for="provinceCode in selectedProvincesList"
          :key="'p-' + provinceCode"
          closable
          size="small"
          @close="unselectProvince(provinceCode)"
          class="city-tag"
        >
          {{ getProvinceName(provinceCode) }}
        </el-tag>
        
        <!-- 城市标签 (显示选中的城市) -->
        <el-tag
          v-for="cityCode in displayedCityCodes"
          :key="'c-' + cityCode"
          closable
          size="small"
          @close="unselectCity(cityCode)"
          class="city-tag"
        >
          {{ getCityName(cityCode) }}
        </el-tag>

        <!-- 剩余数量提示/展开按钮 -->
        <el-tag
          v-if="remainingCityCount > 0"
          type="info"
          size="small"
          class="city-tag expand-tag"
          @click="showAllCities = true"
        >
          +{{ remainingCityCount }} 更多...
        </el-tag>

        <!-- 收起按钮 -->
        <el-button 
          v-if="showAllCities && selectedCityCodesList.length > CITY_DISPLAY_LIMIT" 
          type="primary" 
          link
          size="small" 
          @click="showAllCities = false"
          class="collapse-btn"
        >
          收起
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useRegionStore } from '../store/region';

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  },
  apiBaseUrl: {
    type: String,
    default: 'http://127.0.0.1:5001/api'
  }
});

const emit = defineEmits(['update:modelValue', 'change']);

// 使用Pinia store
const regionStore = useRegionStore();

// 数据结构
const selectedProvince = ref('');
const provinceChecked = reactive({});
const cityChecked = reactive({});
const loading = ref(false);
const error = ref('');
const nationwideSelected = ref(false);
const selectedProvinceDirectly = reactive({});
const isUpdating = ref(false);

// 从store获取省份和城市数据
const provincesList = computed(() => regionStore.getProvincesList);
const provinceCities = computed(() => regionStore.getProvinceCities);

// 当前选中省份的城市
const currentProvinceCities = computed(() => {
  if (!selectedProvince.value || !provinceCities.value[selectedProvince.value]) {
    return null;
  }
  return provinceCities.value[selectedProvince.value].cities || {};
});

// 是否有选中的城市
const hasSelectedCities = computed(() => {
  return Object.values(cityChecked).some(checked => checked === true);
});

// 是否有选中的省份
const hasSelectedProvinces = computed(() => {
  return Object.values(selectedProvinceDirectly).some(checked => checked === true);
});

// 获取当前省份名称
const getCurrentProvinceName = () => {
  return regionStore.getProvinceName(selectedProvince.value);
};

// 获取省份名称
const getProvinceName = (provinceCode) => {
  return regionStore.getProvinceName(provinceCode);
};

// 获取选中的省份代码列表
const selectedProvincesList = computed(() => {
  return Object.keys(selectedProvinceDirectly).filter(code => selectedProvinceDirectly[code]);
});

// 获取选中的城市代码列表
const selectedCityCodesList = computed(() => {
  return Object.keys(cityChecked).filter(code => cityChecked[code]);
});

// 显示控制
const showAllCities = ref(false);
const CITY_DISPLAY_LIMIT = 20;

const displayedCityCodes = computed(() => {
  if (showAllCities.value) {
    return selectedCityCodesList.value;
  }
  return selectedCityCodesList.value.slice(0, CITY_DISPLAY_LIMIT);
});

const remainingCityCount = computed(() => {
  return selectedCityCodesList.value.length - displayedCityCodes.value.length;
});

// 获取城市名称
const getCityName = (cityCode) => {
  return regionStore.getCityName(cityCode);
};

// 清空所有选择
const clearAllSelection = () => {
  clearProvinceAndCitySelection();
  nationwideSelected.value = false;
};

// 清空省份和城市选择
const clearProvinceAndCitySelection = () => {
  Object.keys(cityChecked).forEach(code => {
    cityChecked[code] = false;
  });
  
  Object.keys(provinceChecked).forEach(code => {
    provinceChecked[code] = false;
  });
  
  Object.keys(selectedProvinceDirectly).forEach(code => {
    selectedProvinceDirectly[code] = false;
  });
};

// 生成最终的选中值
const generateFinalSelection = () => {
  if (isUpdating.value) return;
  
  let result = [];
  
  // 如果选中了全国，添加全国代码，但不阻止添加其他省市
  if (nationwideSelected.value) {
    result.push('0'); // 0代表全国
  }
  
  // 添加选中的省份代码
  const selectedProvinces = selectedProvincesList.value;
  result = [...result, ...selectedProvinces];
  
  // 添加选中的城市代码
  const selectedCities = selectedCityCodesList.value;
  result = [...result, ...selectedCities];
  
  emit('update:modelValue', result);
  emit('change', result);
};

// 监听选中状态变化，更新v-model
watch([cityChecked, selectedProvinceDirectly, nationwideSelected], () => {
  generateFinalSelection();
}, { deep: true });

// 初始值设置
watch(() => props.modelValue, (newVal) => {
  if (newVal && Array.isArray(newVal)) {
    isUpdating.value = true;
    
    // 重置所有选中状态
    clearAllSelection();
    
    // 设置新的选中状态（允许同时选中全国和其他省市）
    newVal.forEach(code => {
      if (code === '0') {
        nationwideSelected.value = true;
      }
      // 检查是否是省份代码
      else if (provincesList.value[code]) {
        selectedProvinceDirectly[code] = true;
        provinceChecked[code] = true;
      } else {
        // 否则视为城市代码
        cityChecked[code] = true;
      }
    });
    
    isUpdating.value = false;
  }
}, { immediate: true });

// 选择全国
const selectNationwide = () => {
  if (isUpdating.value) return;
  isUpdating.value = true;
  nationwideSelected.value = !nationwideSelected.value;
  isUpdating.value = false;
};

// 取消选择全国
const unselectNationwide = () => {
  if (isUpdating.value) return;
  isUpdating.value = true;
  nationwideSelected.value = false;
  isUpdating.value = false;
};

// 处理全国选项变化
const handleNationwideCheck = (isChecked) => {
  if (isUpdating.value) return;
  isUpdating.value = true;
  nationwideSelected.value = isChecked;
  isUpdating.value = false;
};

// 选择所有省份
const selectAllProvinces = () => {
  if (isUpdating.value) return;
  
  isUpdating.value = true;
  Object.keys(provincesList.value).forEach(code => {
    selectedProvinceDirectly[code] = true;
    provinceChecked[code] = true;
  });
  isUpdating.value = false;
};

// 取消选择所有省份
const unselectAllProvinces = () => {
  if (isUpdating.value) return;
  
  isUpdating.value = true;
  Object.keys(selectedProvinceDirectly).forEach(code => {
    selectedProvinceDirectly[code] = false;
    provinceChecked[code] = false;
  });
  isUpdating.value = false;
};

// 选择省份
const selectProvince = (code) => {
  selectedProvince.value = code;
};

// 处理省份选中状态变化
const handleProvinceCheck = (provinceCode, isChecked) => {
  if (isUpdating.value) return;
  isUpdating.value = true;
  
  selectedProvinceDirectly[provinceCode] = isChecked;
  provinceChecked[provinceCode] = isChecked;
  
  isUpdating.value = false;
};

// 取消选择省份
const unselectProvince = (provinceCode) => {
  if (isUpdating.value) return;
  isUpdating.value = true;
  selectedProvinceDirectly[provinceCode] = false;
  provinceChecked[provinceCode] = false;
  isUpdating.value = false;
};

// 处理城市选中状态变化
const handleCityCheck = (cityCode) => {
  if (isUpdating.value) return;
  isUpdating.value = true;
  isUpdating.value = false;
};

// 选择当前省份下的所有城市
const selectAllCitiesInProvince = () => {
  if (isUpdating.value) return;
  if (!selectedProvince.value || !provinceCities.value[selectedProvince.value]) return;
  
  isUpdating.value = true;
  // 选中省份
  selectedProvinceDirectly[selectedProvince.value] = true;
  provinceChecked[selectedProvince.value] = true;
  
  // 同时选中该省份下的所有城市
  const province = provinceCities.value[selectedProvince.value];
  if (province && province.cities) {
    Object.keys(province.cities).forEach(cityCode => {
      cityChecked[cityCode] = true;
    });
  }
  isUpdating.value = false;
};

// 取消选择当前省份下的所有城市
const unselectAllCitiesInProvince = () => {
  if (isUpdating.value) return;
  if (!selectedProvince.value) return;
  
  isUpdating.value = true;
  selectedProvinceDirectly[selectedProvince.value] = false;
  provinceChecked[selectedProvince.value] = false;
  
  const province = provinceCities.value[selectedProvince.value];
  if (province && province.cities) {
    Object.keys(province.cities).forEach(cityCode => {
      cityChecked[cityCode] = false;
    });
  }
  isUpdating.value = false;
};

// 选择所有地级市
const selectAllCities = () => {
  if (isUpdating.value) return;
  
  isUpdating.value = true;
  
  // 清除省份选择
  Object.keys(selectedProvinceDirectly).forEach(code => {
    selectedProvinceDirectly[code] = false;
    provinceChecked[code] = false;
  });
  
  // 选中所有城市
  for (const provinceCode in provinceCities.value) {
    const province = provinceCities.value[provinceCode];
    if (province.cities) {
      Object.keys(province.cities).forEach(cityCode => {
        cityChecked[cityCode] = true;
      });
    }
  }
  
  isUpdating.value = false;
};

// 取消选择所有地级市
const unselectAllCities = () => {
  if (isUpdating.value) return;
  
  isUpdating.value = true;
  
  // 取消选中所有城市
  Object.keys(cityChecked).forEach(cityCode => {
    cityChecked[cityCode] = false;
  });
  
  isUpdating.value = false;
};

// 取消选择单个城市
const unselectCity = (cityCode) => {
  if (isUpdating.value) return;
  isUpdating.value = true;
  cityChecked[cityCode] = false;
  isUpdating.value = false;
};

// 组件挂载时获取数据
onMounted(async () => {
  loading.value = true;
  
  try {
    // 设置API基础URL
    regionStore.setApiBaseUrl(props.apiBaseUrl);
    
    // 从store获取数据
    await regionStore.fetchRegionData();
    
    // 初始化省份选中状态
    Object.keys(provincesList.value).forEach(code => {
      provinceChecked[code] = false;
      selectedProvinceDirectly[code] = false;
    });
    
    // 初始化城市选中状态
    for (const provinceCode in provinceCities.value) {
      const province = provinceCities.value[provinceCode];
      if (province.cities) {
        Object.keys(province.cities).forEach(cityCode => {
          cityChecked[cityCode] = false;
        });
      }
    }
    
    // 如果有初始选中的值，设置选中状态
    if (props.modelValue && props.modelValue.length > 0) {
      isUpdating.value = true;
      
      props.modelValue.forEach(code => {
        if (code === '0') {
          nationwideSelected.value = true;
        } else if (provincesList.value[code]) {
          selectedProvinceDirectly[code] = true;
          provinceChecked[code] = true;
        } else {
          cityChecked[code] = true;
        }
      });
      
      isUpdating.value = false;
    }
    
    // 默认选中第一个省份
    if (Object.keys(provincesList.value).length > 0) {
      selectedProvince.value = Object.keys(provincesList.value)[0];
    }
  } catch (err) {
    console.error('获取数据出错:', err);
    error.value = '网络错误，请稍后重试';
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.region-city-selector {
  width: 100%;
}

.selector-container {
  display: flex;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
  overflow: hidden;
  height: 400px;
}

.province-list {
  width: 180px;
  border-right: 1px solid #EBEEF5;
  overflow-y: auto;
  background-color: #F5F7FA;
}

.province-actions {
  display: flex;
  justify-content: space-around;
  padding: 10px 5px;
  border-bottom: 1px solid #EBEEF5;
  background-color: #FFFFFF;
}

.special-item {
  background-color: #E6F1FC;
  border-bottom: 1px solid #EBEEF5;
}

.province-item {
  padding: 10px 15px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.province-item:hover {
  background-color: #EBEEF5;
}

.province-item.active {
  background-color: #E6F1FC;
  color: #409EFF;
}

.city-list {
  flex: 1;
  padding: 15px;
  overflow-y: auto;
}

.city-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #EBEEF5;
}

.province-name {
  font-size: 16px;
  font-weight: bold;
}

.city-grid {
  display: flex;
  flex-wrap: wrap;
}

.city-item {
  width: 33.33%;
  padding: 8px 10px;
  box-sizing: border-box;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.city-item :deep(.el-checkbox__label) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.no-city-selected {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #909399;
}

.selected-cities {
  margin-top: 15px;
  padding: 10px;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
}

.selected-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.selected-tags {
  display: flex;
  flex-wrap: wrap;
}

.city-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

.expand-tag {
  cursor: pointer;
}

.expand-tag:hover {
  opacity: 0.8;
}

.collapse-btn {
  margin-bottom: 8px;
  vertical-align: middle;
}

@media (max-width: 768px) {
  .selector-container {
    flex-direction: column;
    height: auto;
  }
  
  .province-list {
    width: 100%;
    height: 200px;
    border-right: none;
    border-bottom: 1px solid #EBEEF5;
  }
  
  .city-item {
    width: 33.33%;
  }
}
</style> 