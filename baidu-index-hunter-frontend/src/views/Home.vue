<script setup>
import { ref } from 'vue'
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
  Download,
  ArrowRight,
  Grid,
  Collection,
  Switch,
  VideoPlay
} from '@element-plus/icons-vue'


const router = useRouter()
const { t: $t } = useI18n()

const goToDataCollection = () => {
  router.push('/data-collection')
}

const features = ref([
  {
    title: $t('views.home.1uq3y8'),
    description: $t('views.home.6441b1'),
    icon: Lightning
  },
  {
    title: $t('views.home.jp2c1d'),
    description: $t('views.home.e56nq1'),
    icon: DataAnalysis
  },
  {
    title: $t('views.home.2w06tf'),
    description: $t('views.home.1m15x3'),
    icon: Calendar
  },
  {
    title: $t('views.home.i7o6ab'),
    description: $t('views.home.h1lxb7'),
    icon: Monitor
  },
  {
    title: $t('views.home.0xwgl8'),
    description: $t('views.home.dvs5el'),
    icon: DocumentCopy
  },
  {
    title: $t('views.home.1k8p9p'),
    description: $t('views.home.577224'),
    icon: Connection
  }
])

const workflowSteps = [
  {
    title: $t('views.home.165t48'),
    description: $t('views.home.j5akxa'),
    icon: Grid
  },
  {
    title: $t('views.home.j4j3l8'),
    description: $t('views.home.rc6u59'),
    icon: Edit
  },
  {
    title: $t('views.home.m3rv57'),
    description: $t('views.home.v168tu'),
    icon: Location
  },
  {
    title: $t('views.home.4820q1'),
    description: $t('views.home.pn314p'),
    icon: Calendar
  },
  {
    title: $t('views.home.5fnsx4'),
    description: $t('views.home.x6r7r2'),
    icon: Collection
  },
  {
    title: $t('views.home.v8q34v'),
    description: $t('views.home.y36i39'),
    icon: Switch
  },
  {
    title: $t('views.home.6k0l5s'),
    description: $t('views.home.o99urw'),
    icon: VideoPlay
  }
]
</script>

<template>
  <div class="home-wrapper">
    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-content">
        <div class="hero-badge">
          <span>{{$t('views.home.s3x4h8')}}</span>
          <span class="badge-arrow">→</span>
        </div>
        <h1 class="hero-title">{{$t('views.home.k581r2')}}<br>
          <span class="text-gradient">{{$t('views.home.fy2895')}}</span>
        </h1>
        <p class="hero-subtitle">{{$t('views.home.5h470p')}}<span class="highlight">{{$t('views.home.o14lgn')}}</span>、<span class="highlight">{{$t('views.home.0czn5k')}}</span>、<span class="highlight">{{$t('views.home.xxljf7')}}</span>{{$t('views.home.hhg7e8')}}</p>
        <div class="hero-actions">
          <button class="btn btn-primary" @click="goToDataCollection">{{$t('views.home.43rq8f')}}<el-icon class="btn-icon"><ArrowRight /></el-icon>
          </button>
          <button class="btn btn-secondary" @click="router.push('/about')">{{$t('views.home.0219gl')}}</button>
        </div>
        
        <div class="hero-stats">
          <div class="stat-item">
            <div class="stat-value">99.9%</div>
            <div class="stat-label">{{$t('views.home.c75e2d')}}</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-value">100+</div>
            <div class="stat-label">{{$t('views.home.2rfl1j')}}</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-value">24h</div>
            <div class="stat-label">{{$t('views.home.cfidk6')}}</div>
          </div>
        </div>
      </div>
      
      <div class="hero-visual">
        <div class="visual-card main-card">
          <div class="card-header">
            <div class="window-dots">
              <span></span><span></span><span></span>
            </div>
            <div class="window-title">{{$t('views.home.4iknky')}}</div>
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
            <div class="ft-title">{{$t('views.home.2l9pkd')}}</div>
            <div class="ft-desc">{{$t('views.home.l65qr6')}}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="features-section">
      <div class="section-header">
        <h2 class="section-title">{{$t('views.home.j8u6oj')}}</h2>
        <p class="section-desc">{{$t('views.home.ey34p5')}}</p>
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
        <h2 class="section-title">{{$t('views.home.kv3meg')}}</h2>
        <p class="section-desc">{{$t('views.home.253trm')}}</p>
        </div>
        
      <div class="workflow-grid">
        <div v-for="(step, index) in workflowSteps" :key="index" class="step-card">
          <div class="step-badge">{{ index + 1 }}</div>
          <div class="step-icon">
            <el-icon><component :is="step.icon" /></el-icon>
          </div>
          <h3 class="step-title">{{ step.title }}</h3>
          <p class="step-desc">{{ step.description }}</p>
          <div class="step-connector" v-if="index < workflowSteps.length - 1"></div>
        </div>
      </div>
    </section>

    <!-- CTA Section (New Design) -->
    <section class="cta-section-new">
      <div class="cta-overlay"></div>
      <div class="cta-container-new">
        <h2 class="cta-title-new">{{$t('views.home.n1l0nb')}}</h2>
        <p class="cta-desc-new">{{$t('views.home.z4lrx6')}}</p>
        
        <div class="cta-input-group">
          <button class="cta-btn-new" @click="goToDataCollection">{{$t('views.home.srrdh4')}}<el-icon><ArrowRight /></el-icon>
          </button>
        </div>
        
        <div class="cta-footer-text">
          <span>{{$t('views.home.3s33n3')}}</span>
          <span class="dot">•</span>
          <span>{{$t('views.home.65prg3')}}</span>
          <span class="dot">•</span>
          <span>{{$t('views.home.i15nso')}}</span>
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
  background: var(--glass-bg);
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

/* Workflow - New Grid Design */
.workflow-section {
  padding: 100px 24px;
  background-color: var(--color-bg-subtle);
}

.workflow-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
  max-width: var(--max-width);
  margin: 0 auto;
}

.step-card {
  background: var(--color-bg-surface);
  border-radius: 16px;
  padding: 24px;
  border: 1px solid var(--color-border);
  position: relative;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.step-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
  border-color: var(--color-primary-light);
}

.step-badge {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 24px;
  height: 24px;
  background-color: var(--color-bg-subtle);
  color: var(--color-text-tertiary);
  border-radius: 50%;
  font-size: 0.75rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.step-card:hover .step-badge {
  background-color: var(--color-primary);
  color: white;
}

.step-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  background-color: var(--color-bg-subtle);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  margin-bottom: 20px;
}

.step-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-main);
  margin-bottom: 8px;
}

.step-desc {
  font-size: 0.85rem;
  color: var(--color-text-secondary);
  line-height: 1.4;
}

/* CTA Section - Dark Theme */
.cta-section-new {
  position: relative;
  background-color: #0f172a; /* Slate 900 */
  padding: 100px 24px;
  overflow: hidden;
}

/* 网格背景装饰 */
.cta-section-new::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image: 
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: radial-gradient(circle at center, black 40%, transparent 100%);
  -webkit-mask-image: radial-gradient(circle at center, black 40%, transparent 100%);
  z-index: 1;
}

.cta-container-new {
  max-width: 800px;
  margin: 0 auto;
  text-align: center;
  position: relative;
  z-index: 2;
}

.cta-title-new {
  font-size: 3rem;
  font-weight: 800;
  color: white;
  margin-bottom: 24px;
  letter-spacing: -1px;
}

.cta-desc-new {
  font-size: 1.25rem;
  color: #94a3b8; /* Slate 400 */
  margin-bottom: 48px;
  line-height: 1.6;
}

.cta-btn-new {
  background-color: white;
  color: #0f172a;
  border: none;
  padding: 16px 32px;
  font-size: 1.1rem;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.cta-btn-new:hover {
  background-color: #f1f5f9;
  transform: translateY(-2px);
  box-shadow: 0 10px 25px -5px rgba(255, 255, 255, 0.1);
}

.cta-footer-text {
  margin-top: 32px;
  font-size: 0.9rem;
  color: #64748b;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.dot {
  color: #334155;
}

/* 响应式 */
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
  
  .workflow-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 640px) {
  .hero-title {
    font-size: 2.5rem;
  }
  
  .features-grid {
    grid-template-columns: 1fr;
  }
  
  .workflow-grid {
    grid-template-columns: 1fr;
  }
  
  .card-1 {
    display: none;
  }
  
  .cta-title-new {
    font-size: 2rem;
  }
}
</style> 
