<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Lightning, 
  DataAnalysis, 
  Calendar, 
  Monitor, 
  DocumentCopy, 
  Connection,
  Edit,
  Location,
  Download
} from '@element-plus/icons-vue'

const router = useRouter()

const goToDataCollection = () => {
  router.push('/data-collection')
}

const features = ref([
  {
    title: '高效爬取',
    description: '优化的爬取策略，智能管理Cookie，确保爬取效率和成功率',
    icon: Lightning
  },
  {
    title: '多维度数据',
    description: '支持搜索指数、媒体指数等多维度数据采集，满足不同研究需求',
    icon: DataAnalysis
  },
  {
    title: '丰富的时间维度',
    description: '支持日度、周度数据，可灵活选择时间范围和对比时间',
    icon: Calendar
  },
  {
    title: '多终端支持',
    description: '区分PC和移动端数据，全面了解用户行为特征',
    icon: Monitor
  },
  {
    title: '智能导出',
    description: '支持Excel、CSV等多种格式导出，数据处理更便捷',
    icon: DocumentCopy
  },
  {
    title: '稳定可靠',
    description: '智能Cookie池管理，保障长时间稳定采集',
    icon: Connection
  }
])

// 使用流程步骤
const workflowSteps = [
  {
    title: '选择关键词',
    description: '输入关键词或上传文件',
    icon: Edit
  },
  {
    title: '选择时间范围',
    description: '自定义采集的时间范围',
    icon: Calendar
  },
  {
    title: '选择城市',
    description: '全国或特定城市数据',
    icon: Location
  },
  {
    title: '选择数据类型',
    description: '搜索指数、媒体指数等',
    icon: DataAnalysis
  },
  {
    title: '开始采集',
    description: '一键获取所需数据',
    icon: Download
  }
]
</script>

<template>
  <div class="home-container">
    <!-- 主横幅区域 -->
    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">百度指数猎手</h1>
        <p class="hero-subtitle">高效、稳定的百度指数数据采集工具</p>
        <div class="hero-buttons">
          <el-button type="primary" size="large" @click="goToDataCollection">
            开始采集
          </el-button>
          <el-button size="large" @click="router.push('/about')">了解更多</el-button>
        </div>
      </div>
      <div class="hero-image">
        <img src="../assets/logo.svg" alt="百度指数数据可视化" />
      </div>
    </section>

    <!-- 特性介绍区域 -->
    <section class="features-section">
      <h2 class="section-title">核心特性</h2>
      <div class="features-grid">
        <div v-for="(feature, index) in features" :key="index" class="feature-card">
          <div class="feature-icon">
            <el-icon :size="48" :color="'#4facfe'">
              <component :is="feature.icon" />
            </el-icon>
          </div>
          <h3 class="feature-title">{{ feature.title }}</h3>
          <p class="feature-description">{{ feature.description }}</p>
        </div>
      </div>
    </section>

    <!-- 使用流程区域 -->
    <section class="workflow-section">
      <h2 class="section-title">使用流程</h2>
      
      <div class="workflow-container">
        <div class="workflow-progress">
          <div class="progress-line"></div>
        </div>
        
        <div class="steps-container">
          <div v-for="(step, index) in workflowSteps" :key="index" class="workflow-step">
            <div class="step-number">{{ index + 1 }}</div>
            <div class="step-icon-container">
              <el-icon :size="64" color="#4facfe">
                <component :is="step.icon" />
              </el-icon>
            </div>
            <h3 class="step-title">{{ step.title }}</h3>
            <p class="step-description">{{ step.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- 开始使用区域 -->
    <section class="cta-section">
      <div class="cta-content">
        <h2 class="cta-title">准备好开始采集数据了吗？</h2>
        <p class="cta-description">
          只需简单几步，即可获取您需要的百度指数数据，助力您的研究与决策。
        </p>
        <el-button type="primary" size="large" @click="goToDataCollection" class="cta-button">
          立即开始
        </el-button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-container {
  max-width: 1200px;
  margin: 0 auto;
}

/* 主横幅区域样式 */
.hero-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 80px;
  padding: 60px 20px;
  background: linear-gradient(to right, rgba(79, 172, 254, 0.05), rgba(0, 242, 254, 0.05));
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.03);
}

.hero-content {
  flex: 1;
  padding-right: 40px;
}

.hero-title {
  font-size: 3.5rem;
  font-weight: 700;
  margin-bottom: 16px;
  background: linear-gradient(to right, #4facfe, #00f2fe);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.2;
}

.hero-subtitle {
  font-size: 1.5rem;
  color: #606266;
  margin-bottom: 32px;
  line-height: 1.5;
}

.hero-buttons {
  display: flex;
  gap: 16px;
}

.hero-buttons .el-button--primary {
  background: linear-gradient(to right, #4facfe, #00f2fe);
  border: none;
  font-weight: 500;
  padding: 12px 24px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.hero-buttons .el-button--primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(79, 172, 254, 0.4);
}

.hero-buttons .el-button--default {
  border-color: #4facfe;
  color: #4facfe;
  font-weight: 500;
  padding: 12px 24px;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.hero-buttons .el-button--default:hover {
  background-color: rgba(79, 172, 254, 0.05);
}

.hero-image {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  max-width: 40%;
}

.hero-image img {
  width: 100%;
  max-width: 320px;
  border-radius: 12px;
  transition: transform 0.5s ease;
}

.hero-image img:hover {
  transform: scale(1.05);
}

/* 特性区域样式 */
.section-title {
  text-align: center;
  font-size: 2.2rem;
  margin-bottom: 50px;
  color: #303133;
  position: relative;
  padding-bottom: 15px;
}

.section-title::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 60px;
  height: 3px;
  background: linear-gradient(to right, #4facfe, #00f2fe);
  border-radius: 3px;
}

.features-section {
  margin-bottom: 80px;
  padding: 0 20px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 30px;
}

.feature-card {
  background-color: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.feature-card:hover {
  transform: translateY(-10px);
  box-shadow: 0 15px 35px rgba(79, 172, 254, 0.1);
}

.feature-icon {
  margin-bottom: 20px;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(79, 172, 254, 0.1);
  border-radius: 50%;
}

.feature-title {
  font-size: 1.4rem;
  font-weight: 600;
  margin-bottom: 15px;
  text-align: center;
  color: #303133;
}

.feature-description {
  color: #606266;
  text-align: center;
  line-height: 1.6;
}

/* 工作流程区域样式 */
.workflow-section {
  margin-bottom: 80px;
  padding: 60px 30px;
  background-color: white;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.05);
  position: relative;
  overflow: hidden;
}

.workflow-container {
  position: relative;
  padding: 30px 0;
}

.workflow-progress {
  position: absolute;
  top: 140px;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  z-index: 1;
}

.progress-line {
  height: 4px;
  background: linear-gradient(to right, #4facfe, #00f2fe);
  width: 80%;
  border-radius: 2px;
}

.steps-container {
  display: flex;
  justify-content: space-around;
  flex-wrap: wrap;
  position: relative;
  z-index: 2;
  gap: 20px;
}

.workflow-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 180px;
  text-align: center;
  position: relative;
  transition: all 0.3s ease;
  margin-bottom: 20px;
}

.workflow-step:hover {
  transform: translateY(-8px);
}

.step-number {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(to right, #4facfe, #00f2fe);
  color: white;
  border-radius: 50%;
  font-weight: bold;
  font-size: 18px;
  box-shadow: 0 6px 15px rgba(79, 172, 254, 0.3);
  margin-bottom: 15px;
}

.step-icon-container {
  width: 120px;
  height: 120px;
  background-color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(79, 172, 254, 0.1);
  transition: all 0.3s ease;
}

.workflow-step:hover .step-icon-container {
  box-shadow: 0 15px 30px rgba(79, 172, 254, 0.25);
  border-color: rgba(79, 172, 254, 0.3);
}

.step-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #303133;
}

.step-description {
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

/* 开始使用区域样式 */
.cta-section {
  background: linear-gradient(to right, #4facfe, #00f2fe);
  padding: 80px 40px;
  border-radius: 16px;
  margin-bottom: 60px;
  text-align: center;
  color: white;
  box-shadow: 0 15px 30px rgba(79, 172, 254, 0.2);
}

.cta-title {
  font-size: 2.5rem;
  margin-bottom: 20px;
  font-weight: 700;
}

.cta-description {
  font-size: 1.25rem;
  margin-bottom: 40px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.6;
  opacity: 0.9;
}

.cta-button {
  background-color: white !important;
  color: #4facfe !important;
  font-weight: 600 !important;
  padding: 15px 40px !important;
  font-size: 1.1rem !important;
  border: none !important;
  border-radius: 8px !important;
  transition: all 0.3s ease !important;
}

.cta-button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1) !important;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .progress-line {
    width: 90%;
  }
  
  .workflow-step {
    width: 160px;
  }
  
  .step-icon-container {
    width: 100px;
    height: 100px;
  }
}

@media (max-width: 991px) {
  .workflow-progress {
    display: none;
  }
  
  .steps-container {
    flex-wrap: wrap;
    justify-content: center;
    gap: 30px;
  }
  
  .workflow-step {
    width: 200px;
  }
}

@media (max-width: 768px) {
  .hero-section {
    flex-direction: column;
    padding: 40px 20px;
  }

  .hero-title {
    font-size: 2.5rem;
  }

  .hero-content {
    padding-right: 0;
    margin-bottom: 40px;
    text-align: center;
  }
  
  .hero-buttons {
    justify-content: center;
  }

  .hero-image {
    max-width: 80%;
  }
  
  .section-title {
    font-size: 1.8rem;
  }
  
  .workflow-step {
    width: 100%;
    max-width: 280px;
  }
  
  .cta-title {
    font-size: 2rem;
  }
}
</style> 