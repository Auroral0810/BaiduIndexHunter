<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import {
  Lightning,
  DataAnalysis,
  User,
  DocumentCopy,
  TrendCharts,
  Monitor,
  WarningFilled,
  InfoFilled,
  Document,
  Cpu
} from '@element-plus/icons-vue'

const { t } = useI18n()

const version = 'v2.0'
const releaseDate = '2026-02-04'

const features = computed(() => [
  {
    title: t('about.coreFeatures.efficient.title'),
    description: t('about.coreFeatures.efficient.desc'),
    icon: Lightning
  },
  {
    title: t('about.coreFeatures.multiData.title'),
    description: t('about.coreFeatures.multiData.desc'),
    icon: DataAnalysis
  },
  {
    title: t('about.coreFeatures.easyUse.title'),
    description: t('about.coreFeatures.easyUse.desc'),
    icon: User
  },
  {
    title: t('about.coreFeatures.export.title'),
    description: t('about.coreFeatures.export.desc'),
    icon: DocumentCopy
  },
  {
    title: t('about.coreFeatures.monitor.title'),
    description: t('about.coreFeatures.monitor.desc'),
    icon: Monitor
  },
  {
    title: t('about.coreFeatures.trend.title'),
    description: t('about.coreFeatures.trend.desc'),
    icon: TrendCharts
  }
])

const faqs = computed(() => [
  { question: t('about.faq.q1'), answer: t('about.faq.a1') },
  { question: t('about.faq.q2'), answer: t('about.faq.a2') },
  { question: t('about.faq.q3'), answer: t('about.faq.a3') },
  { question: t('about.faq.q4'), answer: t('about.faq.a4') },
  { question: t('about.faq.q5'), answer: t('about.faq.a5') },
  { question: t('about.faq.q6'), answer: t('about.faq.a6') },
])
</script>

<template>
  <div class="about-container">
    <!-- 免责声明 -->
    <section class="disclaimer-section">
      <el-alert
        :title="t('about.disclaimer.title')"
        type="warning"
        :closable="false"
        show-icon>
        <template #default>
          <p><strong>{{ t('about.disclaimer.content1') }}</strong></p>
          <p>{{ t('about.disclaimer.content2') }}</p>
        </template>
      </el-alert>
    </section>

    <section class="hero-section">
      <h1 class="page-title gradient-text">{{ t('about.title') }}</h1>
      <p class="subtitle">{{ t('about.subtitle') }}</p>
      <div class="version-info">
        <el-tag effect="dark" class="version-tag">{{ version }}</el-tag>
        <span class="release-date">{{ releaseDate }}</span>
      </div>
    </section>
    
    <div class="content-wrapper">
      <div class="left-column">
        <section class="intro-section">
          <h2>{{ t('about.intro.title') }}</h2>
          <div class="intro-text">
            <p>{{ t('about.intro.p1') }}</p>
            <p>{{ t('about.intro.p2') }}</p>
            <p>{{ t('about.intro.p3') }}</p>
          </div>
        </section>
        
        <section class="advantages-section">
          <h2>{{ t('about.features.title') }}</h2>
          <div class="advantages-list">
            <div class="advantage-item">
              <div class="advantage-number">01</div>
              <div class="advantage-content">
                <h3>{{ t('about.features.scrapy.title') }}</h3>
                <p>{{ t('about.features.scrapy.desc') }}</p>
              </div>
            </div>
            <div class="advantage-item">
              <div class="advantage-number">02</div>
              <div class="advantage-content">
                <h3>{{ t('about.features.scheduler.title') }}</h3>
                <p>{{ t('about.features.scheduler.desc') }}</p>
              </div>
            </div>
            <div class="advantage-item">
              <div class="advantage-number">03</div>
              <div class="advantage-content">
                <h3>{{ t('about.features.dataTypes.title') }}</h3>
                <p>{{ t('about.features.dataTypes.desc') }}</p>
              </div>
            </div>
            <div class="advantage-item">
              <div class="advantage-number">04</div>
              <div class="advantage-content">
                <h3>{{ t('about.features.resume.title') }}</h3>
                <p>{{ t('about.features.resume.desc') }}</p>
              </div>
            </div>
          </div>
        </section>
        
        <section class="faq-section">
          <h2>{{ t('about.faq.title') }}</h2>
          <el-collapse accordion>
            <el-collapse-item v-for="(faq, index) in faqs" :key="index" :title="faq.question">
              <div class="faq-answer">{{ faq.answer }}</div>
            </el-collapse-item>
          </el-collapse>
        </section>
      </div>
      
      <div class="right-column">
        <section class="features-section">
          <h2>{{ t('about.coreFeatures.title') }}</h2>
          <div class="features-list">
            <div v-for="(feature, index) in features" :key="index" class="feature-item">
              <div class="feature-icon">
                <el-icon :size="24" color="var(--primary-color)">
                  <component :is="feature.icon" />
                </el-icon>
              </div>
              <div class="feature-content">
                <h3 class="feature-title">{{ feature.title }}</h3>
                <p class="feature-description">{{ feature.description }}</p>
              </div>
            </div>
          </div>
        </section>
        
        <section class="tech-stack-section">
          <h2>{{ t('about.techStack.title') }}</h2>
          <div class="tech-list">
            <div class="tech-category">
              <h3>{{ t('about.techStack.frontend') }}</h3>
              <ul>
                <li>Vue 3 + Composition API</li>
                <li>Element Plus UI</li>
                <li>Vue Router</li>
                <li>Pinia</li>
                <li>ECharts</li>
              </ul>
            </div>
            <div class="tech-category">
              <h3>{{ t('about.techStack.backend') }}</h3>
              <ul>
                <li>Python + Flask</li>
                <li>Scrapy</li>
                <li>Redis</li>
                <li>MySQL</li>
                <li>WebSocket</li>
              </ul>
            </div>
            <div class="tech-category">
              <h3>{{ t('about.techStack.dataProcess') }}</h3>
              <ul>
                <li>Pandas</li>
                <li>NumPy</li>
                <li>CSV / Excel / JSON</li>
              </ul>
            </div>
          </div>
        </section>
      </div>
    </div>

    <!-- 项目信息 -->
    <section class="project-info-section">
      <div class="project-info-header">
        <h2>{{ t('about.projectInfo.title') }}</h2>
      </div>
      <div class="project-info-content">
        <div class="project-info-item">
          <div class="project-info-icon-wrapper" style="background-color: var(--primary-light);">
            <el-icon :size="32" color="var(--primary-color)">
              <Document />
            </el-icon>
          </div>
          <h3>{{ t('about.projectInfo.personalProject.title') }}</h3>
          <p>{{ t('about.projectInfo.personalProject.desc') }}</p>
        </div>
        <div class="project-info-item">
          <div class="project-info-icon-wrapper warning-bg">
            <el-icon :size="32" color="var(--warning-color)">
              <WarningFilled />
            </el-icon>
          </div>
          <h3>{{ t('about.projectInfo.disclaimer.title') }}</h3>
          <p>{{ t('about.projectInfo.disclaimer.desc') }}</p>
        </div>
        <div class="project-info-item">
          <div class="project-info-icon-wrapper success-bg">
            <el-icon :size="32" color="var(--success-color)">
              <Cpu />
            </el-icon>
          </div>
          <h3>{{ t('about.projectInfo.techLearning.title') }}</h3>
          <p>{{ t('about.projectInfo.techLearning.desc') }}</p>
        </div>
        <div class="project-info-item">
          <div class="project-info-icon-wrapper error-bg">
            <el-icon :size="32" color="var(--error-color)">
              <InfoFilled />
            </el-icon>
          </div>
          <h3>{{ t('about.projectInfo.localUse.title') }}</h3>
          <p>{{ t('about.projectInfo.localUse.desc') }}</p>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.about-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  padding-bottom: 60px;
}

.disclaimer-section {
  margin-bottom: 30px;
}

.disclaimer-section p {
  margin: 5px 0;
  line-height: 1.6;
}

.hero-section {
  text-align: center;
  margin-bottom: 40px;
  padding-bottom: 40px;
  border-bottom: 1px solid var(--border-color);
}

.page-title {
  font-size: 2.5rem;
  color: var(--text-primary);
  margin-bottom: 15px;
}

.gradient-text {
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  font-size: 1.2rem;
  color: var(--text-secondary);
  margin-bottom: 20px;
}

.version-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.version-tag {
  background: var(--primary-gradient);
  border: none;
}

.release-date {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.content-wrapper {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 30px;
  margin-bottom: 40px;
}

.left-column, .right-column {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.intro-section, .advantages-section, .faq-section,
.features-section, .tech-stack-section {
  background-color: var(--bg-card);
  border-radius: 12px;
  padding: 30px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

h2 {
  font-size: 1.5rem;
  margin-bottom: 25px;
  color: var(--text-primary);
  position: relative;
  padding-bottom: 10px;
  display: inline-block;
}

h2:after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: var(--primary-gradient);
  border-radius: 3px;
  opacity: 0.6;
}

.intro-text {
  font-size: 1rem;
  line-height: 1.8;
  color: var(--text-regular);
}

.intro-text p {
  margin-bottom: 15px;
}

.advantages-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.advantage-item {
  display: flex;
  gap: 16px;
  padding: 16px;
  background-color: var(--bg-page);
  border-radius: 8px;
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.advantage-item:hover {
  transform: translateX(5px);
  background-color: var(--bg-card);
  box-shadow: var(--shadow-md);
  border-color: var(--primary-light);
}

.advantage-number {
  font-size: 1.5rem;
  font-weight: bold;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--primary-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  flex-shrink: 0;
}

.advantage-content h3 {
  font-size: 1.1rem;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.advantage-content p {
  color: var(--text-regular);
  line-height: 1.6;
  font-size: 0.95rem;
}

.faq-answer {
  padding: 10px 0;
  color: var(--text-regular);
  line-height: 1.6;
}

.features-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.feature-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
  align-items: flex-start;
}

.feature-item:hover {
  background-color: var(--bg-page);
}

.feature-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--primary-light);
  border-radius: 8px;
  flex-shrink: 0;
}

.feature-title {
  font-size: 1rem;
  margin-bottom: 4px;
  color: var(--text-primary);
}

.feature-description {
  color: var(--text-secondary);
  font-size: 0.85rem;
  line-height: 1.5;
}

.tech-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.tech-category h3 {
  font-size: 1rem;
  margin-bottom: 8px;
  color: var(--text-primary);
  border: none;
  padding: 0;
}

.tech-category h3:after {
  display: none;
}

.tech-category ul {
  list-style-type: none;
  margin: 0;
  padding: 0;
}

.tech-category ul li {
  padding: 4px 0;
  color: var(--text-regular);
  position: relative;
  padding-left: 16px;
  font-size: 0.9rem;
}

.tech-category ul li:before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--primary-color);
  opacity: 0.7;
}

/* Project Info Section */
.project-info-section {
  background: var(--bg-card);
  border-radius: 12px;
  padding: 40px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

.project-info-header {
  text-align: center;
  margin-bottom: 40px;
}

.project-info-header h2 {
  font-size: 1.6rem;
  margin-bottom: 10px;
}

.project-info-header h2:after {
  left: 50%;
  transform: translateX(-50%);
  width: 60px;
}

.project-info-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 24px;
}

.project-info-item {
  padding: 24px 16px;
  background-color: var(--bg-page);
  border-radius: 8px;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  border: 1px solid var(--border-color);
}

.project-info-item:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
}

.project-info-icon-wrapper {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  background-color: var(--primary-light);
}

.warning-bg {
  background-color: rgba(217, 119, 6, 0.1);
}

.success-bg {
  background-color: rgba(22, 163, 74, 0.1);
}

.error-bg {
  background-color: rgba(220, 38, 38, 0.1);
}

.project-info-item h3 {
  font-size: 1.1rem;
  margin-bottom: 12px;
  color: var(--text-primary);
  border: none;
  padding: 0;
}

.project-info-item h3:after {
  display: none;
}

.project-info-item p {
  color: var(--text-regular);
  line-height: 1.6;
  font-size: 0.9rem;
}

/* 响应式 */
@media (max-width: 1024px) {
  .content-wrapper {
    grid-template-columns: 1fr;
  }
  
  .project-info-content {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .page-title {
    font-size: 2rem;
  }
  
  .subtitle {
    font-size: 1rem;
  }
  
  .advantage-item {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  .project-info-content {
    grid-template-columns: 1fr;
  }
}
</style>
