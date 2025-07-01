<template>
  <div class="task-container">
    <h2>人群属性采集</h2>
    
    <el-form :model="formData" label-width="120px" class="task-form">
      <el-form-item label="关键词">
        <el-input
          v-model="formData.keywords"
          type="textarea"
          :rows="4"
          placeholder="请输入关键词，多个关键词请用逗号、空格或换行分隔"
        />
      </el-form-item>
      
      <el-form-item label="城市">
        <el-select
          v-model="formData.cityCode"
          placeholder="请选择城市"
          style="width: 100%"
          filterable
        >
          <el-option
            v-for="city in cityOptions"
            :key="city.code"
            :label="city.name"
            :value="city.code"
          />
        </el-select>
      </el-form-item>
      
      <el-form-item label="属性类型">
        <el-select
          v-model="formData.attributeType"
          placeholder="请选择属性类型"
          style="width: 100%"
        >
          <el-option label="年龄分布" value="age" />
          <el-option label="性别分布" value="gender" />
          <el-option label="学历水平" value="education" />
        </el-select>
      </el-form-item>
      
      <el-form-item label="优先级">
        <el-slider
          v-model="formData.priority"
          :marks="priorityMarks"
          :min="1"
          :max="10"
          :step="1"
          show-stops
        />
      </el-form-item>
      
      <el-form-item>
        <el-button type="primary" @click="submitTask" :loading="submitting">
          提交任务
        </el-button>
        <el-button @click="resetForm">重置</el-button>
      </el-form-item>
    </el-form>
    
    <div v-if="taskId" class="task-result">
      <el-alert
        title="任务已提交成功"
        type="success"
        show-icon
        :closable="false"
      >
        <template #default>
          任务ID: {{ taskId }}
          <el-button type="text" @click="goToTaskList">查看任务列表</el-button>
        </template>
      </el-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:4000/api'
const router = useRouter()

// 表单数据
const formData = reactive({
  keywords: '',
  cityCode: '',
  attributeType: 'age',
  priority: 5
})

// 优先级标记
const priorityMarks = {
  1: '低',
  5: '中',
  10: '高'
}

// 城市选项
interface City {
  code: string;
  name: string;
}
const cityOptions = ref<City[]>([])
const submitting = ref(false)
const taskId = ref('')

// 获取城市列表
const getCityOptions = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/city/list`)
    cityOptions.value = response.data.data || []
  } catch (error) {
    ElMessage.error('获取城市列表失败')
    console.error('获取城市列表错误:', error)
  }
}

// 提交任务
const submitTask = async () => {
  // 表单验证
  if (!formData.keywords.trim()) {
    ElMessage.warning('请输入关键词')
    return
  }
  if (!formData.cityCode) {
    ElMessage.warning('请选择城市')
    return
  }
  if (!formData.attributeType) {
    ElMessage.warning('请选择属性类型')
    return
  }
  
  // 处理关键词，转换为数组
  const keywords = formData.keywords
    .split(/[,，\s\n]+/)
    .filter(keyword => keyword.trim().length > 0)
    .map(keyword => keyword.trim())
  
  if (keywords.length === 0) {
    ElMessage.warning('请输入有效关键词')
    return
  }
  
  submitting.value = true
  
  try {
    const response = await axios.post(`${API_BASE_URL}/task/create`, {
      taskType: 'demographic_attributes',
      parameters: {
        keywords,
        cityCode: formData.cityCode,
        attributeType: formData.attributeType
      },
      priority: formData.priority
    })
    
    if (response.data.code === 0) {
      ElMessage.success('任务提交成功')
      taskId.value = response.data.data.taskId
    } else {
      ElMessage.error(`任务提交失败: ${response.data.message}`)
    }
  } catch (error) {
    ElMessage.error('任务提交失败，请检查网络连接')
    console.error('提交任务错误:', error)
  } finally {
    submitting.value = false
  }
}

// 重置表单
const resetForm = () => {
  formData.keywords = ''
  formData.cityCode = ''
  formData.attributeType = 'age'
  formData.priority = 5
  taskId.value = ''
}

// 前往任务列表页面
const goToTaskList = () => {
  router.push({ path: '/data-collection', query: { tab: 'task_list' } })
}

// 页面加载时获取城市列表
onMounted(() => {
  getCityOptions()
})
</script>

<style scoped>
.task-container {
  padding: 20px;
}

.task-form {
  max-width: 600px;
}

.task-result {
  margin-top: 20px;
}
</style> 