<template>
  <div class="task-container">
    <div class="task-header">
      <h2>人群属性采集</h2>
      <div class="task-desc">获取百度指数人群属性数据，包括性别、年龄、学历等人口统计学特征</div>
    </div>
    
    <el-card class="task-card">
      <template #header>
        <div class="card-header">
          <span>设置参数</span>
        </div>
      </template>
      
      <el-form :model="formData" label-width="120px" class="task-form">
        <!-- 关键词设置 -->
        <el-divider content-position="left">关键词设置</el-divider>
        
        <el-form-item label="关键词输入">
          <el-input
            v-model="batchKeywords"
            type="textarea"
            :rows="4"
            placeholder="每行输入一个关键词，批量添加"
          />
          <div class="keywords-actions">
            <el-button type="primary" @click="addBatchKeywords" :disabled="!batchKeywords.trim()">
              <el-icon><Plus /></el-icon>添加关键词
            </el-button>
            <span class="keywords-tip">每行一个关键词</span>
          </div>
        </el-form-item>
        
        <el-form-item label="文件导入">
          <el-upload
            class="upload-area"
            action="#"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handleKeywordsFileChange"
            accept=".xlsx,.csv,.txt"
          >
            <el-button type="primary" plain>
              <el-icon><Upload /></el-icon>选择文件
            </el-button>
            <div class="upload-tip">支持.xlsx, .csv, .txt格式</div>
          </el-upload>
          <div class="file-import-options">
            <el-checkbox v-model="skipFirstLine">跳过第一行（标题行）</el-checkbox>
          </div>
        </el-form-item>
        
        <el-form-item label="已添加关键词" v-if="formData.keywords.length > 0">
          <div class="keywords-tags-container">
            <div class="keywords-tags">
              <el-tag
                v-for="(keyword, index) in formData.keywords"
                :key="index"
                closable
                @close="removeKeyword(index)"
                class="keyword-tag"
                :type="keywordCheckResults[keyword.value] === false ? 'danger' : keywordCheckResults[keyword.value] === true ? 'success' : ''"
              >
                {{ keyword.value }}
                <el-tooltip v-if="keywordCheckResults[keyword.value] === false" content="该关键词在百度指数中不存在" placement="top">
                  <el-icon class="keyword-warning"><Warning /></el-icon>
                </el-tooltip>
              </el-tag>
            </div>
            <div class="keywords-actions">
              <el-button type="danger" plain size="small" @click="clearKeywords">
                <el-icon><Delete /></el-icon>清空关键词
              </el-button>
              <el-button type="primary" plain size="small" @click="checkKeywords" :loading="checkingKeywords">
                <el-icon><Check /></el-icon>检查关键词
              </el-button>
              <el-button type="warning" plain size="small" @click="removeInvalidKeywords" :disabled="!hasInvalidKeywords">
                <el-icon><Close /></el-icon>清除不存在的关键词
              </el-button>
              <div class="keywords-count">共 {{ formData.keywords.length }} 个关键词</div>
            </div>
          </div>
        </el-form-item>

        
        <!-- 输出设置 -->
        <el-divider content-position="left">输出设置</el-divider>
        
        <el-form-item label="数据来源">
          <el-radio-group v-model="formData.kind">
            <el-radio-button label="all">PC+移动</el-radio-button>
            <el-radio-button label="pc">PC</el-radio-button>
            <el-radio-button label="wise">移动</el-radio-button>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="输出格式">
          <el-radio-group v-model="formData.output_format">
            <el-radio label="csv">CSV格式</el-radio>
            <el-radio label="excel">Excel格式</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="批处理大小">
          <el-input-number 
            v-model="formData.batch_size" 
            :min="1" 
            :max="50"
            controls-position="right"
          />
          <div class="input-tip">每批处理的关键词数量，默认为10</div>
        </el-form-item>
        
        <!-- 任务设置 -->
        <el-divider content-position="left">任务设置</el-divider>
        
        <el-form-item label="恢复任务">
          <el-switch v-model="formData.resume" active-text="是" inactive-text="否" />
        </el-form-item>
        
        <el-form-item label="任务ID" v-if="formData.resume">
          <el-input v-model="formData.task_id" placeholder="请输入要恢复的任务ID" />
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
          <el-button 
            type="primary" 
            @click="showTaskOverview" 
            :disabled="!canSubmit"
            size="large"
          >
            <el-icon><Check /></el-icon>提交任务
          </el-button>
          <el-button @click="resetForm" size="large">
            <el-icon><Refresh /></el-icon>重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-dialog
      v-model="successDialogVisible"
      title="任务提交成功"
      width="500px"
    >
      <div class="success-content">
        <el-result icon="success" title="任务已成功提交" :sub-title="`任务ID: ${taskId}`">
          <template #extra>
            <el-button type="primary" @click="goToTaskList">查看任务列表</el-button>
            <el-button @click="successDialogVisible = false">继续提交</el-button>
          </template>
        </el-result>
      </div>
    </el-dialog>
    
    <!-- 关键词检查结果对话框 -->
    <el-dialog
      v-model="checkResultDialogVisible"
      title="关键词检查结果"
      width="500px"
      modal
      append-to-body
      :close-on-click-modal="false"
      :show-close="true"
    >
      <div class="check-result-content">
        <el-alert
          v-if="checkResults.existsCount > 0"
          type="success"
          :title="`${checkResults.existsCount} 个关键词存在`"
          :closable="false"
          show-icon
        />
        <el-alert
          v-if="checkResults.notExistsCount > 0"
          type="warning"
          :title="`${checkResults.notExistsCount} 个关键词不存在`"
          :closable="false"
          show-icon
          style="margin-top: 10px;"
        />
        
        <div v-if="checkResults.notExistsCount > 0" class="invalid-keywords">
          <p>不存在的关键词：</p>
          <div class="keywords-list">
            <el-tag
              v-for="(keyword, index) in checkResults.notExistsKeywords"
              :key="index"
              type="danger"
              class="keyword-tag"
              style="margin: 5px;"
            >
              {{ keyword }}
            </el-tag>
          </div>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="checkResultDialogVisible = false">关闭</el-button>
          <el-button 
            type="warning" 
            @click="removeInvalidKeywordsFromDialog" 
            :disabled="checkResults.notExistsCount === 0"
          >
            清除不存在的关键词
          </el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 导入结果对话框 -->
    <el-dialog
      v-model="importResultDialogVisible"
      :title="importResultTitle"
      width="500px"
      modal
      append-to-body
      :close-on-click-modal="false"
      :show-close="true"
    >
      <div class="import-result-content">
        <el-alert
          v-if="importResults.validItems.length > 0"
          type="success"
          :title="`成功导入 ${importResults.validItems.length} 个关键词`"
          :closable="false"
          show-icon
        />
        <el-alert
          v-if="importResults.invalidItems.length > 0"
          type="warning"
          :title="`${importResults.invalidItems.length} 个关键词无效或重复`"
          :closable="false"
          show-icon
          style="margin-top: 10px;"
        />
        
        <div v-if="importResults.invalidItems.length > 0" class="invalid-keywords">
          <p>无效或重复的关键词：</p>
          <div class="keywords-list">
            <el-tag
              v-for="(item, index) in importResults.invalidItems.slice(0, 20)"
              :key="index"
              type="danger"
              class="keyword-tag"
              style="margin: 5px;"
            >
              {{ item }}
            </el-tag>
            <el-tag v-if="importResults.invalidItems.length > 20" type="info">
              ...等 {{ importResults.invalidItems.length - 20 }} 个
            </el-tag>
          </div>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="importResultDialogVisible = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 添加任务概览对话框 -->
    <el-dialog
      v-model="taskOverviewDialogVisible"
      title="任务概览"
      width="600px"
      :close-on-click-modal="false"
    >
      <div class="task-overview">
        <el-descriptions title="任务参数确认" :column="1" border>
          <el-descriptions-item label="任务类型">
            <el-tag>人群属性采集</el-tag>
          </el-descriptions-item>
          
          <el-descriptions-item label="关键词">
            <div class="overview-keywords">
              <span class="overview-count">共 {{ formData.keywords.length }} 个关键词</span>
              <div class="overview-tags">
                <el-tag 
                  v-for="(keyword, index) in formData.keywords.slice(0, 10)" 
                  :key="index"
                  size="small"
                  class="overview-tag"
                >
                  {{ keyword.value }}
                </el-tag>
                <el-tag v-if="formData.keywords.length > 10" type="info" size="small">
                  ...等 {{ formData.keywords.length - 10 }} 个
                </el-tag>
              </div>
            </div>
          </el-descriptions-item>
          
          <el-descriptions-item label="输出设置">
            <div>输出格式: {{ formData.output_format === 'csv' ? 'CSV格式' : 'Excel格式' }}</div>
            <div>批处理大小: {{ formData.batch_size }}</div>
          </el-descriptions-item>
          
          <el-descriptions-item label="其他选项">
            <div>数据来源: {{ formData.kind === 'all' ? 'PC+移动' : (formData.kind === 'pc' ? 'PC' : '移动') }}</div>
            <div>优先级: {{ formData.priority }}</div>
            <div v-if="formData.resume">恢复任务ID: {{ formData.task_id }}</div>
          </el-descriptions-item>
        </el-descriptions>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="taskOverviewDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmSubmitTask" :loading="submitting">
            确认提交
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Upload, Check, Refresh, Warning, Close } from '@element-plus/icons-vue'
import axios from 'axios'
import * as XLSX from 'xlsx'

const API_BASE_URL = 'http://127.0.0.1:5001/api'
const router = useRouter()

// 表单数据
const formData = reactive({
  keywords: [] as { value: string }[],
  output_format: 'csv',
  batch_size: 10,
  resume: false,
  task_id: '',
  priority: 5,
  kind: 'all'
})

// 关键词输入
const batchKeywords = ref('')
const skipFirstLine = ref(true)

// 状态
const submitting = ref(false)
const taskId = ref('')
const successDialogVisible = ref(false)

// 导入结果
const importResultDialogVisible = ref(false)
const importResultTitle = ref('')
const importResults = reactive({
  validItems: [] as string[],
  invalidItems: [] as string[]
})

// 任务概览对话框
const taskOverviewDialogVisible = ref(false)

// 关键词检查结果
const keywordCheckResults = reactive<Record<string, boolean | null>>({})
const checkingKeywords = ref(false)
const checkResultDialogVisible = ref(false)
const checkResults = reactive({
  existsCount: 0,
  notExistsCount: 0,
  notExistsKeywords: [] as string[]
})

// 优先级标记
const priorityMarks = {
  1: '低',
  5: '中',
  10: '高'
}

// 计算是否可以提交
const canSubmit = computed(() => {
  // 必须有关键词
  if (formData.keywords.length === 0) return false
  
  // 恢复任务时需要任务ID
  if (formData.resume && !formData.task_id.trim()) return false
  
  return true
})

// 计算是否有不存在的关键词
const hasInvalidKeywords = computed(() => {
  return Object.values(keywordCheckResults).some(result => result === false);
});

// 检查关键词
const checkKeywords = async () => {
  if (formData.keywords.length === 0) {
    ElMessage.warning('请先添加关键词')
    return
  }
  
  checkingKeywords.value = true
  
  try {
    const keywords = formData.keywords.map(k => k.value)
    const response = await axios.post(`${API_BASE_URL}/word-check/check`, { words: keywords })
    
    if (response.data.code === 10000) {
      const results = response.data.data.results
      
      // 更新检查结果
      for (const word in results) {
        keywordCheckResults[word] = results[word].exists
      }
      
      // 统计结果
      checkResults.existsCount = Object.values(results).filter(r => r.exists).length
      checkResults.notExistsCount = Object.values(results).filter(r => !r.exists).length
      
      // 获取不存在的关键词列表
      checkResults.notExistsKeywords = []
      for (const word in results) {
        if (!results[word].exists) {
          checkResults.notExistsKeywords.push(word)
        }
      }
      
      // 显示检查结果对话框
      checkResultDialogVisible.value = true
    } else {
      ElMessage.error(`检查失败: ${response.data.msg}`)
    }
  } catch (error) {
    console.error('检查关键词错误:', error)
    ElMessage.error('检查关键词失败，请检查网络连接')
  } finally {
    checkingKeywords.value = false
  }
}

// 批量添加关键词
const addBatchKeywords = () => {
  if (!batchKeywords.value.trim()) return
  
  const lines = batchKeywords.value.split('\n').filter(line => line.trim())
  let addedCount = 0
  let duplicateCount = 0
  
  lines.forEach(line => {
    const keyword = line.trim()
    if (keyword && !formData.keywords.some(k => k.value === keyword)) {
      formData.keywords.push({ value: keyword })
      keywordCheckResults[keyword] = null // 重置检查结果
      addedCount++
    } else if (keyword) {
      duplicateCount++
    }
  })
  
  if (addedCount > 0) {
    ElMessage.success(`成功添加 ${addedCount} 个关键词`)
  }
  
  if (duplicateCount > 0) {
    ElMessage.warning(`${duplicateCount} 个关键词重复，已忽略`)
  }
  
  batchKeywords.value = ''
}

// 移除关键词
const removeKeyword = (index: number) => {
  const keyword = formData.keywords[index].value
  delete keywordCheckResults[keyword]
  formData.keywords.splice(index, 1)
}

// 清空关键词
const clearKeywords = () => {
  ElMessageBox.confirm('确定要清空所有关键词吗?', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    formData.keywords = []
    Object.keys(keywordCheckResults).forEach(key => {
      delete keywordCheckResults[key]
    })
  }).catch(() => {})
}

// 清除不存在的关键词
const removeInvalidKeywords = () => {
  if (!hasInvalidKeywords.value) return;
  
  ElMessageBox.confirm('确定要清除所有不存在的关键词吗?', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(() => {
    const invalidKeywords = [];
    
    // 找出不存在的关键词
    formData.keywords = formData.keywords.filter(keyword => {
      const exists = keywordCheckResults[keyword.value] !== false;
      if (!exists) {
        invalidKeywords.push(keyword.value);
        delete keywordCheckResults[keyword.value];
      }
      return exists;
    });
    
    if (invalidKeywords.length > 0) {
      ElMessage.success(`已清除 ${invalidKeywords.length} 个不存在的关键词`);
    }
  }).catch(() => {});
}

// 从对话框中清除不存在的关键词
const removeInvalidKeywordsFromDialog = () => {
  const invalidKeywords = [];
  
  // 找出不存在的关键词
  formData.keywords = formData.keywords.filter(keyword => {
    const exists = keywordCheckResults[keyword.value] !== false;
    if (!exists) {
      invalidKeywords.push(keyword.value);
      delete keywordCheckResults[keyword.value];
    }
    return exists;
  });
  
  if (invalidKeywords.length > 0) {
    ElMessage.success(`已清除 ${invalidKeywords.length} 个不存在的关键词`);
    checkResultDialogVisible.value = false;
  }
}

// 处理关键词文件上传
const handleKeywordsFileChange = async (file: any) => {
  if (!file) return;
  
  try {
    const keywords = await readFileContent(file.raw, skipFirstLine.value);
    
    if (keywords.length === 0) {
      ElMessage.warning('文件中未找到有效关键词');
      return;
    }
    
    // 过滤已存在的关键词
    const validKeywords = [];
    const invalidKeywords = [];
    
    keywords.forEach(keyword => {
      const trimmedKeyword = keyword.trim();
      if (trimmedKeyword && !formData.keywords.some(k => k.value === trimmedKeyword)) {
        validKeywords.push(trimmedKeyword);
      } else if (trimmedKeyword) {
        invalidKeywords.push(trimmedKeyword);
      }
    });
    
    // 添加有效关键词
    validKeywords.forEach(keyword => {
      formData.keywords.push({ value: keyword });
      keywordCheckResults[keyword] = null; // 重置检查结果
    });
    
    // 显示导入结果
    importResults.validItems = validKeywords;
    importResults.invalidItems = invalidKeywords;
    importResultTitle.value = '关键词导入结果';
    importResultDialogVisible.value = true;
  } catch (error) {
    console.error('读取文件错误:', error);
    ElMessage.error('文件读取失败，请检查文件格式');
  }
};

// 读取文件内容
const readFileContent = (file: File, skipFirstLine: boolean): Promise<string[]> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (e) => {
      try {
        const result = e.target?.result;
        if (!result) {
          resolve([]);
          return;
        }
        
        let lines: string[] = [];
        
        // 根据文件类型处理
        if (file.name.endsWith('.xlsx')) {
          const data = new Uint8Array(result as ArrayBuffer);
          const workbook = XLSX.read(data, { type: 'array' });
          const firstSheet = workbook.Sheets[workbook.SheetNames[0]];
          const jsonData = XLSX.utils.sheet_to_json(firstSheet, { header: 1 }) as any[][];
          
          lines = jsonData.map(row => row[0]?.toString() || '');
        } else if (file.name.endsWith('.csv') || file.name.endsWith('.txt')) {
          lines = (result as string).split(/\r\n|\n/);
        }
        
        // 跳过第一行
        if (skipFirstLine && lines.length > 0) {
          lines = lines.slice(1);
        }
        
        // 过滤空行
        lines = lines.filter(line => line.trim() !== '');
        
        resolve(lines);
      } catch (error) {
        reject(error);
      }
    };
    
    reader.onerror = () => {
      reject(new Error('文件读取失败'));
    };
    
    if (file.name.endsWith('.xlsx')) {
      reader.readAsArrayBuffer(file);
    } else {
      reader.readAsText(file);
    }
  });
};

// 提交任务
const submitTask = async () => {
  submitting.value = true
  
  try {
    // 准备参数
    const params: any = {
      taskType: 'demographic_attributes',
      parameters: {
        keywords: formData.keywords.map(k => k.value),
        output_format: formData.output_format,
        batch_size: formData.batch_size,
        resume: formData.resume,
        kind: formData.kind
      },
      priority: formData.priority
    }
    
    // 添加任务ID（如果是恢复任务）
    if (formData.resume && formData.task_id) {
      params.parameters.task_id = formData.task_id
    }
    
    const response = await axios.post(`${API_BASE_URL}/task/create`, params)
    
    if (response.data.code === 10000) {
      taskId.value = response.data.data.taskId
      successDialogVisible.value = true
    } else {
      ElMessage.error(`任务提交失败: ${response.data.msg}`)
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
  formData.keywords = []
  formData.output_format = 'csv'
  formData.batch_size = 10
  formData.resume = false
  formData.task_id = ''
  formData.priority = 5
  formData.kind = 'all'
  batchKeywords.value = ''
}

// 前往任务列表页面
const goToTaskList = () => {
  router.push({ path: '/data-collection', query: { tab: 'task_list' } })
  successDialogVisible.value = false
}

// 显示任务概览
const showTaskOverview = () => {
  taskOverviewDialogVisible.value = true;
};

// 确认提交任务
const confirmSubmitTask = async () => {
  taskOverviewDialogVisible.value = false;
  submitTask();
};
</script>

<style scoped>
.task-container {
  padding: 20px;
  max-width: 900px;
  margin: 0 auto;
}

.task-header {
  margin-bottom: 20px;
  text-align: center;
}

.task-header h2 {
  font-size: 28px;
  color: #409EFF;
  margin-bottom: 10px;
}

.task-desc {
  color: #606266;
  font-size: 14px;
}

.task-card {
  margin-bottom: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
}

.task-form {
  padding: 10px 20px;
}

.keywords-actions {
  display: flex;
  align-items: center;
  margin-top: 10px;
  gap: 10px;
}

.keywords-tip, .input-tip {
  color: #909399;
  font-size: 12px;
}

.input-tip {
  margin-top: 5px;
  margin-left: 5px;
}

.keywords-tags-container {
  width: 100%;
}

.keywords-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
  max-height: 120px;
  overflow-y: auto;
  padding: 5px;
  border: 1px solid #EBEEF5;
  border-radius: 4px;
}

.keyword-tag {
  margin-bottom: 4px;
  display: flex;
  align-items: center;
}

.keyword-warning {
  margin-left: 4px;
  color: #F56C6C;
}

.keywords-count {
  font-size: 14px;
  color: #909399;
}

.upload-area {
  display: flex;
  align-items: center;
}

.upload-tip {
  margin-left: 10px;
  font-size: 12px;
  color: #909399;
}

.success-content {
  text-align: center;
}

.file-import-options {
  margin-top: 8px;
  display: flex;
  align-items: center;
}

.import-result-content {
  padding: 10px;
}

.invalid-keywords {
  margin-top: 15px;
  padding: 10px;
  background-color: #f8f8f8;
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
}

.invalid-keywords p {
  font-weight: bold;
  margin-bottom: 5px;
}

.keywords-list {
  margin-top: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.keyword-tag {
  margin: 5px;
}

.task-overview {
  padding: 20px;
}

.overview-keywords {
  margin-top: 10px;
}

.overview-count {
  font-weight: bold;
  margin-right: 10px;
}

.overview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.overview-tag {
  background-color: #f0f9eb;
  color: #67c23a;
  border-color: #67c23a;
}
</style> 