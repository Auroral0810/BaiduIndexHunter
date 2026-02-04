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
  Download,
  ArrowRight
} from '@element-plus/icons-vue'

const router = useRouter()

const goToDataCollection = () => {
  router.push('/data-collection')
}

const features = ref([
  {
    title: '高效爬取引擎',
    description: '采用 Scrapy 框架构建，内置智能 Cookie 轮换与请求限流策略，确保数据获取的高效性与稳定性。',
    icon: Lightning
  },
  {
    title: '全维度数据洞察',
    description: '深度整合搜索指数、资讯指数、需求图谱及人群画像，为您提供全方位的市场数据支持。',
    icon: DataAnalysis
  },
  {
    title: '灵活的时间跨度',
    description: '支持从2006年至今的历史数据回溯，亦可精确至小时级的实时监控，满足多样化的分析场景。',
    icon: Calendar
  },
  {
    title: '多终端行为分析',
    description: '精准区分 PC 端与移动端用户行为，帮助您全面了解不同场景下的用户搜索习惯。',
    icon: Monitor
  },
  {
    title: '专业级数据导出',
    description: '一键导出标准 CSV/Excel 格式，清洗后的结构化数据可直接用于 Tableau、Python 等工具分析。',
    icon: DocumentCopy
  },
  {
    title: '企业级稳定性',
    description: '基于 Redis 的任务队列与断点续传机制，即使在网络波动下也能保证任务的完整执行。',
    icon: Connection
  }
])

const workflowSteps = [
  {
    title: '定义关键词',
    description: '批量导入或手动输入目标关键词',
    icon: Edit
  },
  {
    title: '设定范围',
    description: '选择时间跨度与目标地域',
    icon: Calendar
  },
  {
    title: '智能采集',
    description: '系统自动调度任务进行采集',
    icon: Lightning
  },
  {
    title: '数据导出',
    description: '获取清洗后的结构化报表',
    icon: Download
  }
]
</script>

<template>
  <div class="home-wrapper">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-content">
        <div class="hero-badge">
          <span>v2.0.0 正式发布</span>
          <span class="badge-arrow">→</span>
        </div>
        <h1 class="hero-title">
          数据驱动决策，<br>
          <span class="text-gradient">洞察市场先机</span>
        </h1>
        <p class="hero-subtitle">
          BaiduIndexHunter 是一款专业级百度指数采集工具，致力于为分析师与营销人员提供
          <span class="highlight">高效</span>、<span class="highlight">稳定</span>、<span class="highlight">精准</span>
          的数据获取服务。
        </p>
        <div class="hero-actions">
          <button class="btn btn-primary" @click="goToDataCollection">
            立即开始采集
            <el-icon class="btn-icon"><ArrowRight /></el-icon>
          </button>
          <button class="btn btn-secondary" @click="router.push('/about')">
            了解更多
          </button>
        </div>
        
        <div class="hero-stats">
          <div class="stat-item">
            <div class="stat-value">99.9%</div>
            <div class="stat-label">采集成功率</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-value">100+</div>
            <div class="stat-label">城市覆盖</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-value">24h</div>
            <div class="stat-label">全天候运行</div>
          </div>
        </div>
      </div>
      
      <div class="hero-visual">
        <div class="visual-card main-card">
          <div class="card-header">
            <div class="window-dots">
              <span></span><span></span><span></span>
            </div>
            <div class="window-title">实时数据监控</div>
          </div>
          <div class="card-body">
            <div class="chart-placeholder">
              <svg viewBox="0 0 400 200" xmlns="http://www.w3.org/2000/svg">
                <path d="M0,150 C50,150 50,100 100,100 C150,100 150,180 200,180 C250,180 250,50 300,50 C350,50 350,120 400,120 L400,200 L0,200 Z" fill="url(#gradient)" opacity="0.2" />
                <path d="M0,150 C50,150 50,100 100,100 C150,100 150,180 200,180 C250,180 250,50 300,50 C350,50 350,120 400,120" fill="none" stroke="var(--color-primary)" stroke-width="3" />
                <defs>
                  <linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:var(--color-primary);stop-opacity:1" />
                    <stop offset="100%" style="stop-color:var(--color-primary);stop-opacity:0" />
                  </linearGradient>
                </defs>
              </svg>
            </div>
            <div class="data-row">
              <div class="data-block" style="width: 60%"></div>
              <div class="data-block" style="width: 30%"></div>
            </div>
            <div class="data-row">
              <div class="data-block" style="width: 40%"></div>
              <div class="data-block" style="width: 50%"></div>
            </div>
          </div>
        </div>
        <div class="visual-card floating-card card-1">
          <div class="float-icon"><el-icon><Lightning /></el-icon></div>
          <div class="float-text">
            <div class="ft-title">任务完成</div>
            <div class="ft-desc">1,240 条数据已导出</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features-section">
      <div class="section-header">
        <h2 class="section-title">为什么选择我们</h2>
        <p class="section-desc">专为数据分析师打造，解决传统采集工具的不稳定、难维护痛点</p>
      </div>
      
      <div class="features-grid">
        <div v-for="(feature, index) in features" :key="index" class="feature-card">
          <div class="feature-icon-wrapper">
            <el-icon><component :is="feature.icon" /></el-icon>
          </div>
          <h3 class="feature-title">{{ feature.title }}</h3>
          <p class="feature-desc">{{ feature.description }}</p>
        </div>
      </div>
    </section>

    <!-- Workflow Section -->
    <section class="workflow-section">
      <div class="section-header">
        <h2 class="section-title">极简操作流程</h2>
        <p class="section-desc">仅需简单的四个步骤，即可获取您所需的高价值数据</p>
      </div>
      
      <div class="workflow-steps">
        <div v-for="(step, index) in workflowSteps" :key="index" class="step-item">
          <div class="step-line" v-if="index < workflowSteps.length - 1"></div>
          <div class="step-icon">
            <el-icon><component :is="step.icon" /></el-icon>
          </div>
          <div class="step-content">
            <div class="step-number">0{{ index + 1 }}</div>
            <h3 class="step-title">{{ step.title }}</h3>
            <p class="step-desc">{{ step.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="cta-section">
      <div class="cta-container">
        <div class="cta-content">
          <h2 class="cta-title">准备好开始探索了吗？</h2>
          <p class="cta-desc">立即开始使用 BaiduIndexHunter，释放数据的无限潜力。</p>
          <div class="cta-actions">
            <button class="btn btn-white" @click="goToDataCollection">
              免费开始使用
            </button>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home-wrapper {
  overflow-x: hidden;
}

/* 通用按钮样式 */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 1rem;
  transition: all 0.2s ease;
  cursor: pointer;
  border: 1px solid transparent;
  gap: 8px;
}

.btn-primary {
  background-color: var(--color-primary);
  color: white;
  box-shadow: 0 4px 6px rgba(79, 70, 229, 0.2);
}

.btn-primary:hover {
  background-color: var(--color-primary-hover);
  transform: translateY(-1px);
  box-shadow: 0 6px 10px rgba(79, 70, 229, 0.3);
}

.btn-secondary {
  background-color: transparent;
  color: var(--color-text-main);
  border-color: var(--color-border);
}

.btn-secondary:hover {
  background-color: var(--color-bg-subtle);
  border-color: var(--color-text-secondary);
}

.btn-white {
  background-color: white;
  color: var(--color-primary);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.btn-white:hover {
  background-color: #f8fafc;
  transform: translateY(-1px);
}

/* Hero Section */
.hero-section {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 80px 0;
  max-width: var(--max-width);
  margin: 0 auto;
  min-height: 600px;
  gap: 60px;
}

.hero-content {
  flex: 1;
  max-width: 600px;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background-color: var(--color-bg-subtle);
  border: 1px solid var(--color-border);
  border-radius: 100px;
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  margin-bottom: 24px;
  cursor: default;
}

.badge-arrow {
  color: var(--color-primary);
}

.hero-title {
  font-size: 3.5rem;
  line-height: 1.1;
  font-weight: 800;
  color: var(--color-text-main);
  margin-bottom: 24px;
  letter-spacing: -1px;
}

.text-gradient {
  background: linear-gradient(135deg, var(--color-primary) 0%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-subtitle {
  font-size: 1.15rem;
  line-height: 1.6;
  color: var(--color-text-secondary);
  margin-bottom: 40px;
}

.highlight {
  color: var(--color-primary);
  font-weight: 600;
}

.hero-actions {
  display: flex;
  gap: 16px;
  margin-bottom: 60px;
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 32px;
  padding-top: 32px;
  border-top: 1px solid var(--color-border);
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-main);
}

.stat-label {
  font-size: 0.85rem;
  color: var(--color-text-tertiary);
}

.stat-divider {
  width: 1px;
  height: 40px;
  background-color: var(--color-border);
}

/* Hero Visual */
.hero-visual {
  flex: 1;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
}

.visual-card {
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  box-shadow: var(--shadow-lg);
}

.main-card {
  width: 480px;
  height: 320px;
  display: flex;
  flex-direction: column;
  z-index: 10;
  overflow: hidden;
}

.card-header {
  padding: 16px;
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  gap: 16px;
}

.window-dots {
  display: flex;
  gap: 6px;
}

.window-dots span {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: var(--color-border);
}

.window-dots span:nth-child(1) { background-color: #ef4444; }
.window-dots span:nth-child(2) { background-color: #eab308; }
.window-dots span:nth-child(3) { background-color: #22c55e; }

.window-title {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--color-text-tertiary);
}

.card-body {
  flex: 1;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.chart-placeholder {
  flex: 1;
  background-color: var(--color-bg-subtle);
  border-radius: 8px;
  overflow: hidden;
}

.data-row {
  display: flex;
  gap: 12px;
}

.data-block {
  height: 12px;
  background-color: var(--color-bg-subtle);
  border-radius: 6px;
}

.floating-card {
  position: absolute;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(12px);
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 20;
  animation: float 6s ease-in-out infinite;
}

.card-1 {
  bottom: -30px;
  left: -40px;
  width: 240px;
}

.float-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background-color: var(--color-primary-light);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
}

.ft-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--color-text-main);
}

.ft-desc {
  font-size: 0.8rem;
  color: var(--color-text-secondary);
}

@keyframes float {
  0% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
  100% { transform: translateY(0px); }
}

/* Section Header */
.section-header {
  text-align: center;
  margin-bottom: 60px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

.section-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text-main);
  margin-bottom: 16px;
}

.section-desc {
  font-size: 1.1rem;
  color: var(--color-text-secondary);
  line-height: 1.5;
}

/* Features */
.features-section {
  padding: 100px 24px;
  background-color: var(--color-bg-body);
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 32px;
  max-width: var(--max-width);
  margin: 0 auto;
}

.feature-card {
  background-color: var(--color-bg-surface);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 32px;
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
  border-color: var(--color-primary);
  box-shadow: var(--shadow-lg);
}

.feature-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background-color: var(--color-bg-subtle);
  color: var(--color-text-main);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  margin-bottom: 24px;
  transition: all 0.3s ease;
}

.feature-card:hover .feature-icon-wrapper {
  background-color: var(--color-primary);
  color: white;
}

.feature-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--color-text-main);
  margin-bottom: 12px;
}

.feature-desc {
  font-size: 0.95rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
}

/* Workflow */
.workflow-section {
  padding: 100px 24px;
  background-color: var(--color-bg-subtle);
}

.workflow-steps {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 32px;
  max-width: var(--max-width);
  margin: 0 auto;
}

.step-item {
  position: relative;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.step-line {
  position: absolute;
  top: 32px;
  left: 50%;
  width: 100%;
  height: 2px;
  background: linear-gradient(90deg, var(--color-border) 0%, var(--color-border) 50%, transparent 100%);
  z-index: 0;
}

.step-icon {
  width: 64px;
  height: 64px;
  border-radius: 20px;
  background-color: var(--color-bg-surface);
  border: 1px solid var(--color-border);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.8rem;
  margin-bottom: 24px;
  position: relative;
  z-index: 1;
  box-shadow: var(--shadow-sm);
}

.step-number {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--color-primary);
  opacity: 0.8;
  margin-bottom: 8px;
  letter-spacing: 1px;
}

.step-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--color-text-main);
  margin-bottom: 8px;
}

.step-desc {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
}

/* CTA */
.cta-section {
  padding: 100px 24px;
  background-color: var(--color-bg-body);
}

.cta-container {
  max-width: var(--max-width);
  margin: 0 auto;
  background: linear-gradient(135deg, var(--color-primary) 0%, #4338ca 100%);
  border-radius: 24px;
  padding: 80px 40px;
  text-align: center;
  color: white;
  position: relative;
  overflow: hidden;
}

.cta-content {
  position: relative;
  z-index: 10;
}

.cta-title {
  font-size: 2.5rem;
  font-weight: 800;
  margin-bottom: 24px;
}

.cta-desc {
  font-size: 1.25rem;
  opacity: 0.9;
  margin-bottom: 40px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
}

/* Dark Mode 适配 */
:global(.dark-mode) .visual-card {
  background-color: #1e293b;
  border-color: #334155;
}

:global(.dark-mode) .floating-card {
  background: rgba(30, 41, 59, 0.9);
}

:global(.dark-mode) .chart-placeholder {
  background-color: #0f172a;
}

:global(.dark-mode) .data-block {
  background-color: #0f172a;
}

@media (max-width: 1024px) {
  .hero-section {
    flex-direction: column;
    text-align: center;
    padding: 60px 24px;
  }
  
  .hero-content {
    max-width: 100%;
  }
  
  .hero-actions {
    justify-content: center;
  }
  
  .hero-stats {
    justify-content: center;
  }
  
  .hero-visual {
    width: 100%;
    margin-top: 40px;
  }
  
  .main-card {
    width: 100%;
    max-width: 480px;
  }
  
  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .workflow-steps {
    grid-template-columns: repeat(2, 1fr);
    gap: 48px;
  }
  
  .step-line {
    display: none;
  }
}

@media (max-width: 640px) {
  .hero-title {
    font-size: 2.5rem;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .workflow-steps {
    grid-template-columns: 1fr;
  }
  
  .card-1 {
    display: none;
  }
}
</style>
