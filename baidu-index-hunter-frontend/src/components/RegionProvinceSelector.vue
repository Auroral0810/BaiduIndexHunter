<template>
  <div class="region-province-selector">
    <!-- 选择区域 -->
    <div class="selector-container">
      <!-- 左侧：全国和省份列表 -->
      <div class="province-list">
        <!-- 全国选项 -->
        <div class="province-item special-item" @click="toggleNationwide">
          <el-checkbox
            v-model="nationwideSelected"
            @change="handleNationwideCheck"
            @click.stop
          >{{ $t("components-RegionProvinceSelector-1") || "全国" }}</el-checkbox>
        </div>
        <!-- 省份操作按钮 -->
        <div class="province-actions">
          <el-button link size="small" @click="selectAllProvinces">
            {{ $t("components-RegionProvinceSelector-2") || "全选省份" }}
          </el-button>
          <el-button link size="small" @click="unselectAllProvinces">
            {{ $t("components-RegionProvinceSelector-3") || "取消全选" }}
          </el-button>
        </div>
        <!-- 省份列表 -->
        <div
          class="province-item"
          v-for="(province, code) in provincesList"
          :key="code"
          :class="{ active: provinceChecked[code] }"
        >
          <el-checkbox
            v-model="provinceChecked[code]"
            @change="(val) => handleProvinceCheck(code, val)"
            @click.stop
          >{{ province.name }}</el-checkbox>
        </div>
      </div>
      <!-- 右侧：说明信息 -->
      <div class="info-panel">
        <div class="info-content">
          <el-icon><InfoFilled /></el-icon>
          <div class="info-text">
            <p>{{ $t("components-RegionProvinceSelector-4") || "地域分布查询说明" }}</p>
            <ul>
              <li>{{ $t("components-RegionProvinceSelector-5") || "选择「全国」将返回各省份的分布数据" }}</li>
              <li>{{ $t("components-RegionProvinceSelector-6") || "选择省份将返回该省份下各城市的分布数据" }}</li>
              <li>{{ $t("components-RegionProvinceSelector-7") || "可同时选择全国和多个省份进行查询" }}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
    <!-- 已选区域展示 -->
    <div class="selected-regions" v-if="hasSelection">
      <div class="selected-header">
        <span>{{ $t("components-RegionProvinceSelector-8") || "已选地区" }}（{{ selectionCount }}）</span>
        <el-button link size="small" @click="clearAllSelection">
          {{ $t("components-RegionProvinceSelector-9") || "清空" }}
        </el-button>
      </div>
      <div class="selected-tags">
        <!-- 全国标签 -->
        <el-tag
          v-if="nationwideSelected"
          closable
          size="small"
          @close="unselectNationwide"
          class="region-tag"
        >{{ $t("components-RegionProvinceSelector-10") || "全国" }}</el-tag>
        <!-- 省份标签 -->
        <el-tag
          v-for="provinceCode in selectedProvincesList"
          :key="'p-' + provinceCode"
          closable
          size="small"
          @close="unselectProvince(provinceCode)"
          class="region-tag"
        >{{ getProvinceName(provinceCode) }}</el-tag>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { ref, reactive, computed, onMounted, watch } from "vue";
import { InfoFilled } from "@element-plus/icons-vue";
import { useRegionStore } from "../store/region";

const { t } = useI18n();

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => [],
  },
  apiBaseUrl: {
    type: String,
    default: "http://127.0.0.1:5001/api",
  },
});

const emit = defineEmits(["update:modelValue", "change"]);

// 使用 Pinia store
const regionStore = useRegionStore();

// 状态
const nationwideSelected = ref(false);
const provinceChecked = reactive<Record<string, boolean>>({});
const loading = ref(false);
const isUpdating = ref(false);

// 从 store 获取省份数据
const provincesList = computed(() => regionStore.getProvincesList);

// 获取选中的省份代码列表
const selectedProvincesList = computed(() => {
  return Object.keys(provinceChecked).filter((code) => provinceChecked[code]);
});

// 是否有选择
const hasSelection = computed(() => {
  return nationwideSelected.value || selectedProvincesList.value.length > 0;
});

// 选择数量
const selectionCount = computed(() => {
  let count = nationwideSelected.value ? 1 : 0;
  count += selectedProvincesList.value.length;
  return count;
});

// 获取省份名称
const getProvinceName = (provinceCode: string) => {
  return regionStore.getProvinceName(provinceCode);
};

// 生成最终的选中值
const generateFinalSelection = () => {
  if (isUpdating.value) return;

  const result: string[] = [];

  // 如果选中了全国，添加 "0"
  if (nationwideSelected.value) {
    result.push("0");
  }

  // 添加选中的省份代码
  result.push(...selectedProvincesList.value);

  // Deep equality check
  const currentVal = props.modelValue || [];
  const isSame =
    result.length === currentVal.length &&
    result.every((val) => currentVal.includes(val)) &&
    currentVal.every((val) => result.includes(val));

  if (!isSame) {
    emit("update:modelValue", result);
    emit("change", result);
  }
};

// 监听选中状态变化
watch(
  [nationwideSelected, provinceChecked],
  () => {
    generateFinalSelection();
  },
  { deep: true }
);

// 初始值设置
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal && Array.isArray(newVal)) {
      // Deep equality check
      const currentSelected: string[] = [];
      if (nationwideSelected.value) currentSelected.push("0");
      Object.keys(provinceChecked).forEach((code) => {
        if (provinceChecked[code]) currentSelected.push(code);
      });

      const isSame =
        newVal.length === currentSelected.length &&
        newVal.every((val) => currentSelected.includes(val)) &&
        currentSelected.every((val) => newVal.includes(val));

      if (isSame) return;

      if (isUpdating.value) return;
      isUpdating.value = true;

      // 重置状态
      nationwideSelected.value = false;
      Object.keys(provinceChecked).forEach((code) => {
        provinceChecked[code] = false;
      });

      // 设置新的选中状态
      newVal.forEach((code: string) => {
        if (code === "0") {
          nationwideSelected.value = true;
        } else if (provincesList.value[code]) {
          provinceChecked[code] = true;
        }
      });

      isUpdating.value = false;
    }
  },
  { immediate: true }
);

// 切换全国选择
const toggleNationwide = () => {
  if (isUpdating.value) return;
  nationwideSelected.value = !nationwideSelected.value;
};

// 处理全国选项变化
const handleNationwideCheck = (isChecked: boolean) => {
  if (isUpdating.value) return;
  nationwideSelected.value = isChecked;
};

// 取消选择全国
const unselectNationwide = () => {
  if (isUpdating.value) return;
  nationwideSelected.value = false;
};

// 选择所有省份
const selectAllProvinces = () => {
  if (isUpdating.value) return;
  isUpdating.value = true;
  Object.keys(provincesList.value).forEach((code) => {
    provinceChecked[code] = true;
  });
  isUpdating.value = false;
  generateFinalSelection();
};

// 取消选择所有省份
const unselectAllProvinces = () => {
  if (isUpdating.value) return;
  isUpdating.value = true;
  Object.keys(provinceChecked).forEach((code) => {
    provinceChecked[code] = false;
  });
  isUpdating.value = false;
  generateFinalSelection();
};

// 处理省份选中状态变化
const handleProvinceCheck = (provinceCode: string, isChecked: boolean) => {
  if (isUpdating.value) return;
  provinceChecked[provinceCode] = isChecked;
};

// 取消选择省份
const unselectProvince = (provinceCode: string) => {
  if (isUpdating.value) return;
  provinceChecked[provinceCode] = false;
};

// 清空所有选择
const clearAllSelection = () => {
  isUpdating.value = true;
  nationwideSelected.value = false;
  Object.keys(provinceChecked).forEach((code) => {
    provinceChecked[code] = false;
  });
  isUpdating.value = false;
  generateFinalSelection();
};

// 组件挂载时获取数据
onMounted(async () => {
  loading.value = true;

  try {
    // 设置 API 基础 URL
    regionStore.setApiBaseUrl(props.apiBaseUrl);

    // 从 store 获取数据
    await regionStore.fetchRegionData();

    // 初始化省份选中状态
    Object.keys(provincesList.value).forEach((code) => {
      if (provinceChecked[code] === undefined) {
        provinceChecked[code] = false;
      }
    });

    // 如果有初始选中的值，设置选中状态
    if (props.modelValue && props.modelValue.length > 0) {
      isUpdating.value = true;

      props.modelValue.forEach((code: string) => {
        if (code === "0") {
          nationwideSelected.value = true;
        } else if (provincesList.value[code]) {
          provinceChecked[code] = true;
        }
      });

      isUpdating.value = false;
    }
  } catch (err) {
    console.error("加载地区数据失败", err);
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.region-province-selector {
  width: 100%;
}

.selector-container {
  display: flex;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  overflow: hidden;
  height: 350px;
  background-color: var(--color-bg-surface);
}

.province-list {
  width: 200px;
  border-right: 1px solid var(--color-border);
  overflow-y: auto;
  background-color: var(--color-bg-subtle);
}

.province-actions {
  display: flex;
  justify-content: space-around;
  padding: 10px 5px;
  border-bottom: 1px solid var(--color-border);
  background-color: var(--color-bg-surface);
}

.special-item {
  background-color: var(--color-bg-subtle);
  border-bottom: 1px solid var(--color-border);
  font-weight: 600;
}

.province-item {
  padding: 10px 15px;
  cursor: pointer;
  transition: all 0.3s;
}

.province-item:hover {
  background-color: var(--color-bg-subtle);
}

.province-item.active {
  background-color: var(--color-primary-light);
  color: var(--color-primary);
}

.info-panel {
  flex: 1;
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-bg-surface);
}

.info-content {
  display: flex;
  align-items: flex-start;
  gap: 15px;
  padding: 20px;
  background-color: var(--color-bg-subtle);
  border-radius: 8px;
  max-width: 400px;
}

.info-content .el-icon {
  font-size: 24px;
  color: var(--color-primary);
  flex-shrink: 0;
}

.info-text p {
  margin: 0 0 10px 0;
  font-weight: 600;
  color: var(--color-text-primary);
}

.info-text ul {
  margin: 0;
  padding-left: 20px;
  color: var(--color-text-secondary);
}

.info-text li {
  margin-bottom: 8px;
  line-height: 1.5;
}

.selected-regions {
  margin-top: 15px;
  padding: 10px;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background-color: var(--color-bg-surface);
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

.region-tag {
  margin-right: 8px;
  margin-bottom: 8px;
}

@media (max-width: 768px) {
  .selector-container {
    flex-direction: column;
    height: auto;
  }

  .province-list {
    width: 100%;
    height: 250px;
    border-right: none;
    border-bottom: 1px solid var(--color-border);
  }

  .info-panel {
    padding: 15px;
  }
}
</style>
