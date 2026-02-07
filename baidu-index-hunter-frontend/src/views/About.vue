<script setup>
import { ref, computed } from 'vue'
import {
  Cpu,
  Connection,
  TrendCharts
} from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
import { Warning } from '@element-plus/icons-vue'

const { t: $t } = useI18n()
const version = ref('2.0.0')
const releaseDate = ref('2026-02-04')

// 使用 computed 确保语言切换时动态更新
const highlights = computed(() => [
  {
    title: $t('views.about.y816mf'),
    desc: $t('views.about.1if70z'),
    icon: Cpu
  },
  {
    title: $t('views.about.5emg22'),
    desc: $t('views.about.bl21jn'),
    icon: Connection
  },
  {
    title: $t('views.about.4013rs'),
    desc: $t('views.about.z68385'),
    icon: TrendCharts
  }
])

const techStack = [
  { name: 'Vue 3', type: 'frontend' },
  { name: 'TypeScript', type: 'frontend' },
  { name: 'Element Plus', type: 'frontend' },
  { name: 'ECharts 5', type: 'frontend' },
  { name: 'Python 3', type: 'backend' },
  { name: 'Scrapy', type: 'backend' },
  { name: 'Flask', type: 'backend' },
  { name: 'Redis', type: 'backend' },
  { name: 'MySQL', type: 'backend' },
  { name: 'Pandas', type: 'data' }
]

// FAQ 数据（使用 computed 确保语言切换时动态更新）
const faqs = computed(() => [
  {
    question: $t('views.about.94e3yr'),
    answer: $t('views.about.17zopd')
  },
  {
    question: $t('views.about.a0wi54'),
    answer: $t('views.about.3524s8')
  },
  {
    question: $t('views.about.69t54p'),
    answer: $t('views.about.o12vtd')
  },
  {
    question: $t('views.about.sx9w99'),
    answer: $t('views.about.124m68')
  }
])
</script>

<template>
  <div class="about-page">
    <!-- Header Section -->
    <section class="about-header">
      <div class="header-content">
        <h1 class="page-title">{{$t('views.about.1502dh')}}<span class="gradient-text">BaiduIndexHunter</span></h1>
        <p class="page-subtitle">{{$t('views.about.183der')}}</p>
        <div class="version-badge">
          <span class="v-tag">Version {{ version }}</span>
          <span class="v-date">Updated {{ releaseDate }}</span>
        </div>
      </div>
    </section>

    <!-- Highlights Grid -->
    <section class="highlights-section">
      <div class="highlights-grid">
        <div v-for="(item, index) in highlights" :key="index" class="highlight-card">
          <div class="icon-box">
            <el-icon><component :is="item.icon" /></el-icon>
          </div>
          <h3>{{ item.title }}</h3>
          <p>{{ item.desc }}</p>
        </div>
      </div>
    </section>

    <!-- Main Content -->
    <div class="main-content">
      <div class="content-left">
        <!-- Project Intro -->
        <section class="info-block intro-block">
          <h2 class="section-title">{{$t('views.about.pzb4pb')}}</h2>
          <div class="text-content">
            <p>{{$t('views.about.z41w17')}}<strong>{{$t('views.about.r7y794')}}</strong>、<strong>{{$t('views.about.m363f8')}}</strong>、<strong>{{$t('views.about.1x15r2')}}</strong>{{$t('views.about.6w1u47')}}</p>
            <p>{{$t('views.about.v97ce4')}}<strong>{{$t('views.about.u8884t')}}</strong>{{$t('views.about.7lg3s2')}}</p>
          </div>
        </section>

        <!-- Tech Stack -->
        <section class="info-block tech-block">
          <h2 class="section-title">{{$t('views.about.e2f7m8')}}</h2>
          <div class="tech-tags">
            <span 
              v-for="tech in techStack" 
              :key="tech.name" 
              class="tech-tag"
              :class="tech.type"
            >
              {{ tech.name }}
            </span>
          </div>
        </section>

        <!-- Disclaimer -->
        <section class="disclaimer-box">
          <div class="disclaimer-icon">
            <el-icon><Warning /></el-icon>
          </div>
          <div class="disclaimer-text">
            <h4>{{$t('views.about.5d4e39')}}</h4>
            <p>{{$t('views.about.3o4x62')}}</p>
          </div>
        </section>
      </div>

      <div class="content-right">
        <!-- FAQ -->
        <section class="faq-block">
          <h2 class="section-title">{{$t('views.about.s4x24w')}}</h2>
          <div class="faq-list">
            <div v-for="(faq, index) in faqs" :key="index" class="faq-item">
              <div class="faq-q">{{ faq.question }}</div>
              <div class="faq-a">{{ faq.answer }}</div>
            </div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.about-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 24px 80px;
}

/* Header */
.about-header {
  text-align: center;
  margin-bottom: 80px;
  padding-top: 40px;
}

.page-title {
  font-size: 3rem;
  font-weight: 800;
  color: var(--color-text-main);
  margin-bottom: 16px;
  letter-spacing: -1px;
}

.gradient-text {
  background: linear-gradient(135deg, var(--color-primary) 0%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.page-subtitle {
  font-size: 1.25rem;
  color: var(--color-text-secondary);
  margin-bottom: 32px;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.6;
}

.version-badge {
  display: inline-flex;
  align-items: center;
  background: var(--color-bg-subtle);
  border: 1px solid var(--color-border);
  border-radius: 100px;
  padding: 4px;
  font-size: 0.85rem;
}

.v-tag {
  background: var(--color-primary);
  color: white;
  padding: 2px 10px;
  border-radius: 100px;
  font-weight: 600;
}

.v-date {
  padding: 0 12px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

/* Highlights */
.highlights-section {
  margin-bottom: 80px;
}

.highlights-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 32px;
}

.highlight-card {
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: 32px;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.highlight-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-lg);
  border-color: var(--color-primary-light);
}

.icon-box {
  width: 48px;
  height: 48px;
  background: var(--color-bg-subtle);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-primary);
  font-size: 1.5rem;
  margin-bottom: 20px;
}

.highlight-card h3 {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 12px;
  color: var(--color-text-main);
}

.highlight-card p {
  color: var(--color-text-secondary);
  line-height: 1.6;
  font-size: 0.95rem;
}

/* Main Content Layout */
.main-content {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: 60px;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 24px;
  color: var(--color-text-main);
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-title::before {
  content: '';
  display: block;
  width: 4px;
  height: 24px;
  background: var(--color-primary);
  border-radius: 2px;
}

/* Intro & Text */
.text-content p {
  font-size: 1.05rem;
  line-height: 1.8;
  color: var(--color-text-regular);
  margin-bottom: 20px;
}

.text-content strong {
  color: var(--color-text-main);
  font-weight: 600;
}

.info-block {
  margin-bottom: 48px;
}

/* Tech Tags */
.tech-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.tech-tag {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  background: var(--color-bg-subtle);
  color: var(--color-text-secondary);
  border: 1px solid var(--color-border);
  transition: all 0.2s;
}

.tech-tag:hover {
  border-color: var(--color-primary);
  color: var(--color-primary);
  background: var(--color-bg-surface);
}

.tech-tag.frontend { border-left: 3px solid #64748b; }
.tech-tag.backend { border-left: 3px solid #4f46e5; }
.tech-tag.data { border-left: 3px solid #10b981; }

/* Disclaimer */
.disclaimer-box {
  background: rgba(239, 68, 68, 0.05);
  border: 1px solid rgba(239, 68, 68, 0.2);
  border-radius: 12px;
  padding: 24px;
  display: flex;
  gap: 16px;
  margin-top: 40px;
}

.disclaimer-icon {
  color: #ef4444;
  font-size: 1.5rem;
  padding-top: 2px;
}

.disclaimer-text h4 {
  color: #991b1b;
  font-weight: 700;
  margin-bottom: 8px;
  font-size: 1rem;
}

.disclaimer-text p {
  color: #7f1d1d;
  font-size: 0.9rem;
  line-height: 1.5;
  margin: 0;
}

/* FAQ */
.faq-list {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.faq-item {
  background: var(--color-bg-subtle);
  border-radius: 12px;
  padding: 24px;
  border: 1px solid transparent;
  transition: all 0.2s;
}

.faq-item:hover {
  background: var(--color-bg-surface);
  border-color: var(--color-border);
  box-shadow: var(--shadow-md);
}

.faq-q {
  font-weight: 700;
  color: var(--color-text-main);
  margin-bottom: 12px;
  font-size: 1.05rem;
}

.faq-a {
  color: var(--color-text-secondary);
  line-height: 1.6;
  font-size: 0.95rem;
}

/* Responsive */
@media (max-width: 900px) {
  .highlights-grid {
    grid-template-columns: 1fr;
  }
  
  .main-content {
    grid-template-columns: 1fr;
    gap: 40px;
  }
  
  .page-title {
    font-size: 2.25rem;
  }
}
</style>
