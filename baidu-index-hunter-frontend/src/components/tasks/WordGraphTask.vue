<template>
  <div class="task-container">
    <h2>需求图谱采集</h2>
    
    <el-form :model="formData" label-width="120px" class="task-form">
      <el-form-item label="关键词">
        <el-input
          v-model="formData.keywords"
          type="textarea"
          :rows="4"
          placeholder="请输入关键词，多个关键词请用逗号、空格或换行分隔"
        />
      </el-form-item>
      
      <el-form-item label="数据类型">
        <el-radio-group v-model="formData.dataType">
          <el-radio label="all">整体趋势</el-radio>
          <el-radio label="pc">PC趋势</el-radio>
          <el-radio label="wise">移动趋势</el-radio>
        </el-radio-group>
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
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const API_BASE_URL = 'http://localhost:4000/api'
const router = useRouter()

// 表单数据
const formData = reactive({
  keywords: '',
  dataType: 'all',
  priority: 5
})

// 优先级标记
const priorityMarks = {
  1: '低',
  5: '中',
  10: '高'
}

const submitting = ref(false)
const taskId = ref('')

// 提交任务
const submitTask = async () => {
  // 表单验证
  if (!formData.keywords.trim()) {
    ElMessage.warning('请输入关键词')
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
      taskType: 'word_graph',
      parameters: {
        keywords,
        dataType: formData.dataType
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
  formData.dataType = 'all'
  formData.priority = 5
  taskId.value = ''
}

// 前往任务列表页面
const goToTaskList = () => {
  router.push({ path: '/data-collection', query: { tab: 'task_list' } })
}
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