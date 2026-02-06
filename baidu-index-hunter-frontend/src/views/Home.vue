<script setup>
import { ref, computed } from 'vue'
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
  VideoPlay,
  User,
  Star,
  TrendCharts
} from '@element-plus/icons-vue'


const router = useRouter()
const { t: $t } = useI18n()

const goToDataCollection = () => {
  router.push('/data-collection')
}

const features = computed(() => [
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

const workflowSteps = computed(() => [
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
])

const dataDefinitions = computed(() => [
  {
    title: $t('views.home.data_region_title'),
    desc: $t('views.home.data_region_desc'),
    algo: $t('views.home.data_region_algo'),
    icon: Location,
    color: '#3b82f6'
  },
  {
    title: $t('views.home.data_demographic_title'),
    desc: $t('views.home.data_demographic_desc'),
    algo: $t('views.home.data_demographic_algo'),
    icon: User,
    color: '#8b5cf6'
  },
  {
    title: $t('views.home.data_interest_title'),
    desc: $t('views.home.data_interest_desc'),
    algo: '', // No specific algo label in text, but fits the pattern
    icon: Star, // Need import
    color: '#ec4899'
  },
  {
    title: $t('views.home.data_graph_title'),
    desc: $t('views.home.data_graph_desc'),
    algo: $t('views.home.data_graph_algo'),
    icon: Connection,
    color: '#10b981'
  },
  {
    title: $t('views.home.data_search_title'),
    desc: $t('views.home.data_search_desc'),
    algo: $t('views.home.data_search_algo'),
    icon: DataAnalysis,
    color: '#f59e0b'
  },
  {
    title: $t('views.home.data_feed_title'),
    desc: $t('views.home.data_feed_desc'),
    algo: $t('views.home.data_feed_algo'),
    icon: DocumentCopy,
    color: '#6366f1'
  }
])

const activeTab = ref(0)
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
        <div class="visual-carousel-wrapper">
          <el-carousel :interval="4000" type="card" height="360px" indicator-position="none">
            <el-carousel-item v-for="(item, index) in dataDefinitions" :key="index" class="visual-carousel-item">
              <div class="visual-card-content" :style="{ borderColor: item.color }">
                <div class="visual-icon-bg" :style="{ backgroundColor: item.color + '15', color: item.color }">
                  <el-icon><component :is="item.icon" /></el-icon>
                </div>
                <h3 class="visual-title" :style="{ color: item.color }">{{ item.title }}</h3>
                <p class="visual-desc">{{ item.desc }}</p>
                <div class="visual-bg-blob" :style="{ background: item.color }"></div>
              </div>
            </el-carousel-item>
          </el-carousel>
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

    <!-- Definitions Section -->
    <section class="definitions-section">
      <div class="section-header">
        <h2 class="section-title">{{$t('views.home.data_definitions_title')}}</h2>
        <p class="section-desc">{{$t('views.home.data_definitions_subtitle')}}</p>
      </div>
      
      <div class="feature-showcase">
        <div class="feature-tabs">
          <div 
            v-for="(item, index) in dataDefinitions" 
            :key="index" 
            class="feature-tab"
            :class="{ active: activeTab === index }"
            @click="activeTab = index"
            :style="{ '--tab-color': item.color }"
          >
            <div class="tab-icon">
              <el-icon><component :is="item.icon" /></el-icon>
            </div>
            <span class="tab-label">{{ item.title }}</span>
            <div class="tab-indicator" v-if="activeTab === index"></div>
          </div>
        </div>

        <div class="feature-content-wrapper">
           <transition name="fade-slide" mode="out-in">
             <div :key="activeTab" class="feature-detail-card" :style="{ borderColor: dataDefinitions[activeTab].color }">
               <div class="detail-header">
                 <div class="detail-icon" :style="{ backgroundColor: dataDefinitions[activeTab].color }">
                   <el-icon><component :is="dataDefinitions[activeTab].icon" /></el-icon>
                 </div>
                 <h3 class="detail-title">{{ dataDefinitions[activeTab].title }}</h3>
               </div>
               
               <div class="detail-body">
                 <p class="detail-desc">{{ dataDefinitions[activeTab].desc }}</p>
                 
                 <div class="detail-algo" v-if="dataDefinitions[activeTab].algo">
                   <div class="algo-badge" :style="{ color: dataDefinitions[activeTab].color, backgroundColor: dataDefinitions[activeTab].color + '15' }">
                     <el-icon><DataAnalysis /></el-icon>
                     <span>Algorithm</span>
                   </div>
                   <p>{{ dataDefinitions[activeTab].algo }}</p>
                 </div>
               </div>
               
               <div class="detail-bg-decoration" :style="{ background: dataDefinitions[activeTab].color }"></div>
             </div>
           </transition>
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
  background-image: radial-gradient(var(--color-border) 1px, transparent 1px);
  background-size: 40px 40px;
  background-attachment: fixed;
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

/* CTA Section - Theme Aware */
.cta-section-new {
  position: relative;
  background-color: var(--color-bg-subtle);
  padding: 100px 24px;
  overflow: hidden;
}

/* 网格背景装饰 - 适配主题 */
.cta-section-new::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background-image: 
    linear-gradient(var(--color-border) 1px, transparent 1px),
    linear-gradient(90deg, var(--color-border) 1px, transparent 1px);
  background-size: 40px 40px;
  opacity: 0.3;
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
  color: var(--color-text-main);
  margin-bottom: 24px;
  letter-spacing: -1px;
}

.cta-desc-new {
  font-size: 1.25rem;
  color: var(--color-text-secondary);
  margin-bottom: 48px;
  line-height: 1.6;
}

.cta-btn-new {
  background-color: var(--color-primary);
  color: white;
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
  box-shadow: 0 4px 6px rgba(79, 70, 229, 0.2);
}

.cta-btn-new:hover {
  background-color: var(--color-primary-hover);
  transform: translateY(-2px);
  box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.3);
}

.cta-footer-text {
  margin-top: 32px;
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.dot {
  color: var(--color-text-tertiary);
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

/* Hero Visual Carousel */
.visual-carousel-wrapper {
  width: 500px;
  margin: 0 auto;
}

.visual-carousel-item {
  border-radius: 16px;
  overflow: visible;
}

.visual-card-content {
  background: var(--color-bg-surface);
  border: 1px solid;
  border-radius: 16px;
  padding: 32px;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  position: relative;
  overflow: hidden;
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
  transition: all 0.3s;
}

.visual-icon-bg {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2.5rem;
  margin-bottom: 24px;
  z-index: 2;
}

.visual-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 16px;
  z-index: 2;
}

.visual-desc {
  font-size: 1rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
  z-index: 2;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.visual-bg-blob {
  position: absolute;
  top: -50%;
  right: -50%;
  width: 200%;
  height: 200%;
  border-radius: 40%;
  opacity: 0.05;
  filter: blur(60px);
  z-index: 1;
  animation: rotate 20s infinite linear;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Definitions Section */
.definitions-section {
  padding: 80px 24px;
  background-color: var(--color-bg-body);
}

.feature-showcase {
  display: flex;
  gap: 40px;
  max-width: var(--max-width);
  margin: 0 auto;
  min-height: 500px;
}

.feature-tabs {
  flex: 0 0 320px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.feature-tab {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.feature-tab:hover {
  transform: translateX(8px);
  border-color: var(--tab-color);
  background: var(--color-bg-subtle);
}

.feature-tab.active {
  background: var(--color-bg-surface);
  border-color: var(--tab-color);
  box-shadow: 0 8px 16px -4px rgba(0, 0, 0, 0.1);
  z-index: 2;
}

.feature-tab.active .tab-icon {
  background-color: var(--tab-color);
  color: white;
}

.feature-tab.active .tab-label {
  color: var(--color-text-main);
  font-weight: 700;
}

.tab-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background-color: var(--color-bg-subtle);
  color: var(--tab-color);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  transition: all 0.3s;
}

.tab-label {
  font-size: 1.1rem;
  font-weight: 500;
  color: var(--color-text-secondary);
  transition: all 0.3s;
}

.tab-indicator {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background-color: var(--tab-color);
  border-radius: 4px 0 0 4px;
}

.feature-content-wrapper {
  flex: 1;
  position: relative;
}

.feature-detail-card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid;
  border-radius: 24px;
  padding: 48px;
  height: 100%;
  position: relative;
  overflow: hidden;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.05);
}

:root[class~="dark"] .feature-detail-card {
  background: rgba(30, 30, 30, 0.6);
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 32px;
  position: relative;
  z-index: 2;
}

.detail-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 2rem;
  box-shadow: 0 10px 20px rgba(0,0,0,0.1);
}

.detail-title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text-main);
}

.detail-body {
  position: relative;
  z-index: 2;
}

.detail-desc {
  font-size: 1.25rem;
  line-height: 1.6;
  color: var(--color-text-secondary);
  margin-bottom: 40px;
  max-width: 80%;
}

.detail-algo {
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 24px;
  display: inline-block;
  max-width: 100%;
}

.algo-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  border-radius: 100px;
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 16px;
}

.detail-bg-decoration {
  position: absolute;
  top: -20%;
  right: -20%;
  width: 60%;
  height: 60%;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.1;
  z-index: 1;
}

/* Animations */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.4s ease;
}

.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

@media (max-width: 1024px) {
  .feature-showcase {
    flex-direction: column;
    min-height: auto;
  }
  
  .feature-tabs {
    flex: none;
    flex-direction: row;
    overflow-x: auto;
    padding-bottom: 16px;
  }
  
  .feature-tab {
    flex: 0 0 auto;
    width: 200px;
  }
  
  .detail-desc {
    max-width: 100%;
  }
}

/* Global Entry Animations */
.hero-section,
.features-section,
.workflow-section,
.definitions-section,
.cta-section-new {
  animation: fade-in-up 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
  opacity: 0;
}

.hero-section { animation-delay: 0.1s; }
.features-section { animation-delay: 0.2s; }
.workflow-section { animation-delay: 0.3s; }
.definitions-section { animation-delay: 0.4s; }
.cta-section-new { animation-delay: 0.5s; }

@keyframes fade-in-up {
  from {
    opacity: 0;
    transform: translateY(40px);
    filter: blur(4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
    filter: blur(0);
  }
}
</style> 
