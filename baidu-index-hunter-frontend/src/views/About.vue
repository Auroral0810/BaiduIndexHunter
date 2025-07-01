<script setup>
import { ref } from 'vue'
import {
  Lightning,
  DataAnalysis,
  User,
  DocumentCopy
} from '@element-plus/icons-vue'
import avatar from '../assets/avatar.jpg'

const version = ref('1.0.0')
const releaseDate = ref('2025-6-26')

const developer = {
  name: '俞云烽',
  role: '全栈开发',
  avatar: avatar,
  school: '南京审计大学',
  description: '负责BaiduIndexHunter项目的全部设计与开发，包括后端数据爬取、前端界面实现和数据分析功能。'
}

const features = ref([
  {
    title: '高效爬取',
    description: '智能Cookie管理和负载均衡，确保稳定可靠的数据获取',
    icon: Lightning
  },
  {
    title: '多维数据',
    description: '支持搜索指数、媒体指数、需求图谱等多种数据类型',
    icon: DataAnalysis
  },
  {
    title: '易于使用',
    description: '直观的用户界面，简化复杂操作，快速获取所需数据',
    icon: User
  },
  {
    title: '灵活导出',
    description: '支持多种格式导出，便于进一步分析和处理',
    icon: DocumentCopy
  }
])

// FAQ 数据
const faqs = ref([
  {
    question: 'BaiduIndexHunter是什么？',
    answer: 'BaiduIndexHunter是一个高效、稳定的百度指数数据采集和分析工具，帮助您获取关键词搜索趋势、地域分布等重要数据。'
  },
  {
    question: '如何开始使用？',
    answer: '首先在配置页面设置您的API密钥和爬虫参数，然后前往数据采集页面，输入您想要分析的关键词、选择时间范围和地域即可开始获取数据。'
  },
  {
    question: '数据采集需要多长时间？',
    answer: '采集时间取决于关键词数量、时间范围和选择的地域数量。为避免IP被封，系统设计了智能爬取策略，通常每个请求会有一定间隔。大量数据采集可能需要较长时间。'
  },
  {
    question: '支持哪些数据导出格式？',
    answer: '当前支持CSV、Excel、JSON格式导出，未来将支持更多格式。'
  },
  {
    question: '遇到问题如何联系？',
    answer: '您可以通过GitHub提交Issue或发送邮件至15968588744@163.com获取帮助。我会尽快回复您的问题。'
  }
])
</script>

<template>
  <div class="about-container">
    <section class="hero-section">
      <h1 class="page-title gradient-text">关于BaiduIndexHunter</h1>
      <p class="subtitle">高效、稳定的百度指数数据采集和分析工具</p>
      <div class="version-info">
        <el-tag effect="dark" class="version-tag">v{{ version }}</el-tag>
        <span class="release-date">发布于: {{ releaseDate }}</span>
      </div>
    </section>
    
    <div class="content-wrapper">
      <div class="left-column">
        <section class="intro-section">
          <h2>项目介绍</h2>
          <div class="intro-text">
            <p>BaiduIndexHunter是一个专为营销人员、数据分析师和研究人员设计的工具，旨在帮助用户高效获取和分析百度指数数据。</p>
            <p>通过我们的应用，您可以轻松监控关键词趋势、了解用户需求变化，支持您的市场决策和研究工作。我们致力于提供最稳定、最高效的数据采集体验。</p>
            <p>该项目采用Python后端和Vue.js前端构建，具有良好的可扩展性和定制能力。无论您是需要简单的数据导出，还是复杂的数据分析，BaiduIndexHunter都能满足您的需求。</p>
          </div>
        </section>
        
        <section class="developer-section">
          <h2>开发者信息</h2>
          <div class="developer-card">
            <div class="developer-avatar">
              <img :src="developer.avatar" alt="开发者头像">
            </div>
            <div class="developer-info">
              <h3>{{ developer.name }}</h3>
              <div class="developer-role">{{ developer.role }}</div>
              <div class="developer-school">{{ developer.school }}</div>
              <p class="developer-description">{{ developer.description }}</p>
              <div class="contact-links">
                <a href="https://github.com/Auroral0810" target="_blank" class="contact-link">
                  <i class="github-icon"></i>
                  <span>GitHub</span>
                </a>
                <a href="mailto:15968588744@163.com" class="contact-link">
                  <i class="email-icon"></i>
                  <span>Email</span>
                </a>
              </div>
            </div>
          </div>
        </section>
        
        <section class="faq-section">
          <h2>常见问题</h2>
          <el-collapse accordion>
            <el-collapse-item v-for="(faq, index) in faqs" :key="index" :title="faq.question">
              <div class="faq-answer">{{ faq.answer }}</div>
            </el-collapse-item>
          </el-collapse>
        </section>
      </div>
      
      <div class="right-column">
        <section class="features-section">
          <h2>核心特性</h2>
          <div class="features-list">
            <div v-for="(feature, index) in features" :key="index" class="feature-item">
              <div class="feature-icon">
                <el-icon :size="32" color="#4facfe">
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
          <h2>技术栈</h2>
          <div class="tech-list">
            <div class="tech-category">
              <h3>前端</h3>
              <ul>
                <li>Vue 3 + Composition API</li>
                <li>Element Plus</li>
                <li>Vue Router</li>
                <li>Pinia 状态管理</li>
              </ul>
            </div>
            <div class="tech-category">
              <h3>后端</h3>
              <ul>
                <li>Python</li>
                <li>Flask</li>
                <li>Redis</li>
                <li>MySQL</li>
              </ul>
            </div>
            <div class="tech-category">
              <h3>数据处理</h3>
              <ul>
                <li>Pandas</li>
                <li>NumPy</li>
                <li>ECharts 数据可视化</li>
              </ul>
            </div>
          </div>
        </section>
        
        <section class="contact-section">
          <h2>联系我们</h2>
          <div class="contact-info">
            <p><strong>GitHub:</strong> <a href="https://github.com/Auroral0810/baidu-index-hunter" target="_blank">github.com/Auroral0810/baidu-index-hunter</a></p>
            <p><strong>邮箱:</strong> 15968588744@163.com</p>
            <p><strong>官方网站:</strong> <a href="https://www.baiduindexhunter.com" target="_blank">www.baiduindexhunter.com</a></p>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<style scoped>
.about-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.hero-section {
  text-align: center;
  margin-bottom: 40px;
  padding-bottom: 40px;
  border-bottom: 1px solid var(--border-lighter);
}

.page-title {
  font-size: 2.5rem;
  color: #303133;
  margin-bottom: 15px;
}

.subtitle {
  font-size: 1.2rem;
  color: #606266;
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
  color: #909399;
  font-size: 0.9rem;
}

.content-wrapper {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 40px;
}

.left-column, .right-column {
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.intro-section, .developer-section, .faq-section,
.features-section, .tech-stack-section, .contact-section {
  background-color: white;
  border-radius: var(--border-radius-large);
  padding: 30px;
  box-shadow: var(--shadow-light);
}

h2 {
  font-size: 1.8rem;
  margin-bottom: 25px;
  color: var(--text-primary);
  position: relative;
  padding-bottom: 10px;
}

h2:after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  width: 40px;
  height: 3px;
  background: var(--primary-gradient);
  border-radius: 3px;
}

.intro-text {
  font-size: 1.05rem;
  line-height: 1.8;
  color: var(--text-regular);
}

.intro-text p {
  margin-bottom: 15px;
}

.developer-card {
  display: flex;
  gap: 25px;
  background-color: #f9f9f9;
  border-radius: var(--border-radius-medium);
  padding: 25px;
  box-shadow: var(--shadow-light);
}

.developer-avatar {
  flex-shrink: 0;
}

.developer-avatar img {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  object-fit: cover;
  border: 4px solid white;
  box-shadow: 0 10px 25px rgba(79, 172, 254, 0.2);
}

.developer-info h3 {
  font-size: 1.5rem;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.developer-role {
  color: var(--primary-color);
  font-weight: 600;
  margin-bottom: 5px;
}

.developer-school {
  color: var(--text-secondary);
  margin-bottom: 15px;
  font-size: 0.95rem;
}

.developer-description {
  line-height: 1.6;
  margin-bottom: 20px;
  color: var(--text-regular);
}

.contact-links {
  display: flex;
  gap: 15px;
}

.contact-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background-color: #f0f2f5;
  border-radius: 20px;
  color: var(--text-regular);
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.contact-link:hover {
  background-color: var(--primary-color);
  color: white;
}

.faq-answer {
  padding: 10px 0;
  color: var(--text-regular);
  line-height: 1.6;
}

.features-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.feature-item {
  display: flex;
  gap: 15px;
  padding: 15px;
  border-radius: var(--border-radius-medium);
  transition: all 0.3s ease;
}

.feature-item:hover {
  background-color: #f9f9f9;
  transform: translateX(5px);
}

.feature-icon {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--primary-light);
  border-radius: 50%;
  flex-shrink: 0;
}

.feature-title {
  font-size: 1.2rem;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.feature-description {
  color: var(--text-regular);
  font-size: 0.95rem;
  line-height: 1.5;
}

.tech-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.tech-category h3 {
  font-size: 1.1rem;
  margin-bottom: 10px;
  color: var(--text-primary);
}

.tech-category ul {
  list-style-type: none;
  margin: 0;
  padding: 0;
}

.tech-category ul li {
  padding: 5px 0;
  color: var(--text-regular);
  position: relative;
  padding-left: 20px;
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
}

.contact-info {
  line-height: 2;
}

.contact-info a {
  color: var(--primary-color);
  text-decoration: none;
}

.contact-info a:hover {
  text-decoration: underline;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .content-wrapper {
    grid-template-columns: 1fr;
  }
  
  .right-column {
    order: -1;
  }
  
  .features-section {
    margin-bottom: 0;
  }
}

@media (max-width: 768px) {
  .page-title {
    font-size: 2rem;
  }
  
  .subtitle {
    font-size: 1rem;
  }
  
  .developer-card {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  .developer-avatar img {
    margin-bottom: 15px;
  }
  
  h2:after {
    left: 50%;
    transform: translateX(-50%);
  }
  
  h2 {
    text-align: center;
  }
  
  .contact-links {
    justify-content: center;
  }
}
</style> 