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
        <h1 class="hero-title">BaiduIndexHunter</h1>
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
  margin-bottom: 100px;
  padding: 80px 40px;
  background: white;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  position: relative;
  overflow: hidden;
}

/* 背景装饰元素 */
.hero-section::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -20%;
  width: 800px;
  height: 800px;
  background: radial-gradient(circle, rgba(59, 130, 246, 0.05) 0%, transparent 70%);
  border-radius: 50%;
  z-index: 0;
}

.hero-section::after {
  content: '';
  position: absolute;
  bottom: -30%;
  left: -10%;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.05) 0%, transparent 70%);
  border-radius: 50%;
  z-index: 0;
}

.hero-content {
  flex: 1;
  padding-right: 60px;
  z-index: 1;
}

.hero-title {
  font-size: 4rem;
  font-weight: 800;
  margin-bottom: 24px;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.1;
  letter-spacing: -1px;
}

.hero-subtitle {
  font-size: 1.5rem;
  color: var(--text-regular);
  margin-bottom: 40px;
  line-height: 1.6;
  max-width: 600px;
}

.hero-buttons {
  display: flex;
  gap: 20px;
}

.hero-buttons .el-button--primary {
  background: var(--primary-color);
  border: none;
  font-weight: 600;
  padding: 24px 36px;
  font-size: 1.1rem;
  border-radius: var(--radius-full);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 6px -1px rgba(59, 130, 246, 0.3);
}

.hero-buttons .el-button--primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 15px -3px rgba(59, 130, 246, 0.4);
  background: var(--primary-hover);
}

.hero-buttons .el-button--default {
  border: 2px solid var(--border-color);
  color: var(--text-primary);
  font-weight: 600;
  padding: 24px 36px;
  font-size: 1.1rem;
  border-radius: var(--radius-full);
  transition: all 0.3s ease;
  background: transparent;
}

.hero-buttons .el-button--default:hover {
  border-color: var(--primary-color);
  color: var(--primary-color);
  background-color: rgba(59, 130, 246, 0.05);
}

.hero-image {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  max-width: 45%;
  z-index: 1;
  position: relative;
}

.hero-image img {
  width: 100%;
  max-width: 400px;
  filter: drop-shadow(0 20px 40px rgba(0, 0, 0, 0.1));
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.hero-image img:hover {
  transform: scale(1.05) rotate(2deg);
}

/* 特性区域样式 */
.section-title {
  text-align: center;
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 60px;
  color: var(--text-primary);
  position: relative;
  letter-spacing: -0.5px;
}

.features-section {
  margin-bottom: 120px;
  padding: 0 20px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 40px;
}

.feature-card {
  background-color: white;
  border-radius: var(--radius-lg);
  padding: 40px 30px;
  box-shadow: var(--shadow-md);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  border: 1px solid rgba(0, 0, 0, 0.02);
}

.feature-card:hover {
  transform: translateY(-10px);
  box-shadow: var(--shadow-xl);
  border-color: rgba(59, 130, 246, 0.1);
}

.feature-icon {
  margin-bottom: 24px;
  width: 80px;
  height: 80px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(139, 92, 246, 0.1) 100%);
  border-radius: 24px;
  color: var(--primary-color);
  transition: transform 0.3s ease;
}

.feature-card:hover .feature-icon {
  transform: scale(1.1) rotate(5deg);
}

.feature-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 16px;
  text-align: center;
  color: var(--text-primary);
}

.feature-description {
  color: var(--text-regular);
  text-align: center;
  line-height: 1.7;
  font-size: 1.05rem;
}

/* 工作流程区域样式 */
.workflow-section {
  margin-bottom: 120px;
  padding: 80px 0;
  background-color: white;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  position: relative;
  overflow: hidden;
}

.workflow-container {
  position: relative;
  padding: 40px 60px;
}

.workflow-progress {
  position: absolute;
  top: 150px;
  left: 100px;
  right: 100px;
  display: flex;
  justify-content: center;
  z-index: 1;
}

.progress-line {
  height: 3px;
  background: linear-gradient(90deg, #e5e7eb 0%, #e5e7eb 100%);
  width: 100%;
  border-radius: 2px;
  position: relative;
  overflow: hidden;
}

.progress-line::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: var(--primary-gradient);
  transform: translateX(-100%);
  animation: progressFlow 3s infinite ease-in-out;
}

@keyframes progressFlow {
  0% { transform: translateX(-100%); }
  50% { transform: translateX(0); }
  100% { transform: translateX(100%); }
}

.steps-container {
  display: flex;
  justify-content: space-between;
  position: relative;
  z-index: 2;
  gap: 30px;
}

.workflow-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 200px;
  text-align: center;
  position: relative;
  transition: all 0.3s ease;
}

.workflow-step:hover {
  transform: translateY(-5px);
}

.step-number {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  color: var(--primary-color);
  border: 2px solid var(--primary-color);
  border-radius: 50%;
  font-weight: 800;
  font-size: 20px;
  box-shadow: 0 4px 10px rgba(59, 130, 246, 0.2);
  margin-bottom: 20px;
  z-index: 2;
  position: relative;
}

.step-icon-container {
  width: 120px;
  height: 120px;
  background-color: white;
  border-radius: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
  color: var(--primary-color);
}

.workflow-step:hover .step-icon-container {
  box-shadow: var(--shadow-xl);
  border-color: var(--primary-color);
  background: var(--primary-light);
  transform: scale(1.05);
}

.step-title {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.step-description {
  color: var(--text-regular);
  font-size: 0.95rem;
  line-height: 1.5;
}

/* 开始使用区域样式 */
.cta-section {
  background: var(--primary-gradient);
  padding: 100px 40px;
  border-radius: var(--radius-lg);
  margin-bottom: 60px;
  text-align: center;
  color: white;
  box-shadow: var(--shadow-xl);
  position: relative;
  overflow: hidden;
}

.cta-section::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
}

.cta-content {
  position: relative;
  z-index: 1;
}

.cta-title {
  font-size: 3rem;
  margin-bottom: 24px;
  font-weight: 800;
  letter-spacing: -1px;
}

.cta-description {
  font-size: 1.25rem;
  margin-bottom: 48px;
  max-width: 700px;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.6;
  opacity: 0.95;
}

.cta-button {
  background-color: white !important;
  color: var(--primary-color) !important;
  font-weight: 700 !important;
  padding: 24px 48px !important;
  font-size: 1.25rem !important;
  border: none !important;
  border-radius: var(--radius-full) !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1) !important;
}

.cta-button:hover {
  transform: translateY(-4px) scale(1.02) !important;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2) !important;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .steps-container {
    flex-wrap: wrap;
    justify-content: center;
  }
  
  .workflow-progress {
    display: none;
  }
}

@media (max-width: 768px) {
  .hero-section {
    flex-direction: column;
    padding: 60px 20px;
    text-align: center;
  }

  .hero-title {
    font-size: 3rem;
  }

  .hero-content {
    padding-right: 0;
    margin-bottom: 60px;
  }
  
  .hero-buttons {
    justify-content: center;
  }

  .hero-image {
    max-width: 80%;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .workflow-step {
    width: 100%;
    margin-bottom: 40px;
  }
  
  .cta-title {
    font-size: 2.25rem;
  }
  
  .cta-description {
    font-size: 1.1rem;
  }
}
</style> 