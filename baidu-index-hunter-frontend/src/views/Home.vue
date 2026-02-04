<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
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

const { t } = useI18n()
const router = useRouter()

const goToDataCollection = () => {
  router.push('/data-collection')
}

const features = computed(() => [
  {
    title: t('home.features.efficient.title'),
    description: t('home.features.efficient.desc'),
    icon: Lightning
  },
  {
    title: t('home.features.multiData.title'),
    description: t('home.features.multiData.desc'),
    icon: DataAnalysis
  },
  {
    title: t('home.features.timeDimension.title'),
    description: t('home.features.timeDimension.desc'),
    icon: Calendar
  },
  {
    title: t('home.features.multiTerminal.title'),
    description: t('home.features.multiTerminal.desc'),
    icon: Monitor
  },
  {
    title: t('home.features.smartExport.title'),
    description: t('home.features.smartExport.desc'),
    icon: DocumentCopy
  },
  {
    title: t('home.features.stable.title'),
    description: t('home.features.stable.desc'),
    icon: Connection
  }
])

// 使用流程步骤
const workflowSteps = computed(() => [
  {
    title: t('home.workflow.step1.title'),
    description: t('home.workflow.step1.desc'),
    icon: Edit
  },
  {
    title: t('home.workflow.step2.title'),
    description: t('home.workflow.step2.desc'),
    icon: Calendar
  },
  {
    title: t('home.workflow.step3.title'),
    description: t('home.workflow.step3.desc'),
    icon: Location
  },
  {
    title: t('home.workflow.step4.title'),
    description: t('home.workflow.step4.desc'),
    icon: DataAnalysis
  },
  {
    title: t('home.workflow.step5.title'),
    description: t('home.workflow.step5.desc'),
    icon: Download
  }
])
</script>

<template>
  <div class="home-container">
    <!-- 主横幅区域 -->
    <section class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">BaiduIndexHunter</h1>
        <p class="hero-subtitle">{{ t('home.subtitle') }}</p>
        <div class="hero-buttons">
          <el-button type="primary" size="large" @click="goToDataCollection">
            {{ t('home.startNow') }}
          </el-button>
          <el-button size="large" @click="router.push('/about')">{{ t('home.learnMore') }}</el-button>
        </div>
      </div>
      <div class="hero-image">
        <img src="../assets/logo.svg" alt="BaiduIndexHunter" />
      </div>
    </section>

    <!-- 特性介绍区域 -->
    <section class="features-section">
      <h2 class="section-title">{{ t('home.featuresTitle') }}</h2>
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
      <h2 class="section-title">{{ t('home.workflowTitle') }}</h2>
      
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
        <h2 class="cta-title">{{ t('home.cta.title') }}</h2>
        <p class="cta-description">{{ t('home.cta.description') }}</p>
        <el-button type="primary" size="large" @click="goToDataCollection" class="cta-button">
          {{ t('home.cta.button') }}
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

/* 主横幅区域样式 - 极简风格 */
.hero-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 100px;
  padding: 100px 0 60px;
  position: relative;
}

/* 移除之前的圆球背景，改用极淡的顶部光晕 */
.hero-section::before {
  content: '';
  position: absolute;
  top: -100px;
  left: 50%;
  transform: translateX(-50%);
  width: 100vw;
  height: 600px;
  background: radial-gradient(50% 50% at 50% 50%, rgba(37, 99, 235, 0.05) 0%, rgba(255, 255, 255, 0) 100%);
  z-index: -1;
  pointer-events: none;
}

.hero-section::after {
  display: none;
}

.hero-content {
  flex: 1;
  padding-right: 80px;
  z-index: 1;
}

.hero-title {
  font-size: 4rem;
  font-weight: 800;
  margin-bottom: 24px;
  color: var(--text-primary);
  /* 移除文字渐变，改用纯深色，更高级 */
  background: none;
  -webkit-text-fill-color: initial;
  line-height: 1.1;
  letter-spacing: -1.5px;
}

.hero-subtitle {
  font-size: 1.25rem;
  color: var(--text-regular);
  margin-bottom: 48px;
  line-height: 1.6;
  max-width: 540px;
}

.hero-buttons {
  display: flex;
  gap: 16px;
}

.hero-buttons .el-button--primary {
  background-color: var(--primary-color);
  border: none;
  font-weight: 600;
  padding: 24px 32px;
  font-size: 1rem;
  border-radius: var(--radius-md);
  box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);
  transition: all 0.2s ease;
}

.hero-buttons .el-button--primary:hover {
  background-color: var(--primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.3);
}

.hero-buttons .el-button--default {
  background-color: white;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
  font-weight: 500;
  padding: 24px 32px;
  font-size: 1rem;
  border-radius: var(--radius-md);
  transition: all 0.2s ease;
  box-shadow: var(--shadow-sm);
}

.hero-buttons .el-button--default:hover {
  background-color: var(--background-color);
  border-color: var(--text-secondary);
  color: var(--text-primary);
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
  max-width: 420px;
  /* 更自然的投影 */
  filter: drop-shadow(0 25px 50px rgba(0, 0, 0, 0.08));
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.hero-image img:hover {
  transform: scale(1.02);
}

/* 特性区域样式 */
.section-title {
  text-align: center;
  font-size: 2.25rem;
  font-weight: 800;
  margin-bottom: 80px;
  color: var(--text-primary);
  letter-spacing: -0.5px;
}

.features-section {
  margin-bottom: 160px;
  padding: 0 20px;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 32px;
}

.feature-card {
  background-color: var(--bg-card);
  border-radius: var(--radius-lg);
  padding: 40px 32px;
  border: 1px solid var(--border-color);
  box-shadow: none;
  transition: all 0.3s ease;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  text-align: left;
}

.feature-card:hover {
  transform: translateY(-4px);
  border-color: var(--primary-color);
  box-shadow: var(--shadow-lg);
}

.feature-icon {
  margin-bottom: 24px;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  /* 极淡的蓝色背景 */
  background-color: var(--primary-light);
  border-radius: 12px;
  color: var(--primary-color);
  transition: transform 0.3s ease;
}

.feature-card:hover .feature-icon {
  transform: none; /* 移除旋转动画，保持稳重 */
  background-color: var(--primary-color);
  color: white;
}

.feature-title {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 12px;
  color: var(--text-primary);
}

.feature-description {
  color: var(--text-secondary);
  line-height: 1.6;
  font-size: 1rem;
  text-align: left;
}

/* 工作流程区域样式 */
.workflow-section {
  margin-bottom: 160px;
  padding: 0; /* 移除背景容器 */
  background-color: transparent;
  box-shadow: none;
  overflow: visible;
}

.workflow-container {
  position: relative;
  padding: 0;
}

.workflow-progress {
  display: none; /* 移除进度条线条，改用更简洁的布局 */
}

.steps-container {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 24px;
}

.workflow-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: auto;
  text-align: center;
  position: relative;
  transition: all 0.3s ease;
}

.workflow-step:hover {
  transform: translateY(-5px);
}

.step-number {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 16px;
  text-transform: uppercase;
  letter-spacing: 1px;
  background: none;
  border: none;
  box-shadow: none;
  width: auto;
  height: auto;
}

.step-icon-container {
  width: 80px;
  height: 80px;
  background-color: var(--bg-card);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  box-shadow: var(--shadow-md);
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
  color: var(--text-regular);
}

.workflow-step:hover .step-icon-container {
  box-shadow: var(--shadow-lg);
  border-color: var(--primary-color);
  color: var(--primary-color);
  transform: none;
}

.step-title {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.step-description {
  color: var(--text-secondary);
  font-size: 0.875rem;
  line-height: 1.5;
}

/* 箭头连接 */
.workflow-step:not(:last-child)::after {
  content: '→';
  position: absolute;
  top: 65px; /* 对齐图标中心 */
  right: -20px;
  font-size: 24px;
  color: var(--border-color);
  font-family: sans-serif;
  font-weight: 300;
}

/* 开始使用区域样式 - 深色主题 */
.cta-section {
  background-color: #0f172a; /* Slate 900 - 深邃午夜色 */
  /* 移除复杂的背景图片 */
  background-image: radial-gradient(circle at 50% 0%, #1e293b 0%, #0f172a 100%);
  padding: 100px 40px;
  border-radius: 24px;
  margin-bottom: 60px;
  text-align: center;
  color: white;
  box-shadow: var(--shadow-2xl);
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.cta-section::before {
  display: none;
}

.cta-title {
  font-size: 3rem;
  margin-bottom: 24px;
  font-weight: 800;
  letter-spacing: -1px;
  color: white; /* 确保是纯白 */
}

.cta-description {
  font-size: 1.25rem;
  margin-bottom: 48px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.6;
  color: #94a3b8; /* Slate 400 */
}

.cta-button {
  background-color: white !important;
  color: #0f172a !important; /* 深色文字 */
  font-weight: 600 !important;
  padding: 20px 40px !important;
  font-size: 1.1rem !important;
  border: none !important;
  border-radius: var(--radius-md) !important;
  box-shadow: 0 0 0 0 transparent !important;
  transition: all 0.2s ease !important;
}

.cta-button:hover {
  background-color: #f1f5f9 !important; /* Slate 100 */
  transform: translateY(-2px) !important;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .steps-container {
    grid-template-columns: repeat(3, 1fr);
  }
  
  .workflow-step:not(:last-child)::after {
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
  
  .steps-container {
    grid-template-columns: 1fr;
    gap: 40px;
  }
  
  .workflow-step {
    width: 100%;
  }
  
  .cta-title {
    font-size: 2.25rem;
  }
  
  .cta-description {
    font-size: 1.1rem;
  }
}
</style> 