<script setup>
import { ref } from 'vue'
import {
  Lightning,
  DataAnalysis,
  User,
  DocumentCopy,
  TrendCharts,
  Monitor,
  Warning,
  InfoFilled
} from '@element-plus/icons-vue'

const version = ref('2.0.0')
const releaseDate = ref('2026-02-04')

const features = ref([
  {
    title: '高效爬取',
    description: '智能Cookie管理和负载均衡，确保稳定可靠的数据获取',
    icon: Lightning
  },
  {
    title: '多维数据',
    description: '支持搜索指数、资讯指数、需求图谱等多种数据类型',
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
  },
  {
    title: '实时监控',
    description: '实时监控任务执行状态，及时发现和处理异常情况',
    icon: Monitor
  },
  {
    title: '趋势分析',
    description: '内置趋势分析工具，帮助您洞察市场动态和用户需求',
    icon: TrendCharts
  }
])

// FAQ 数据
const faqs = ref([
  {
    question: 'BaiduIndexHunter是什么？',
    answer: 'BaiduIndexHunter是一个用于学习研究的百度指数数据采集工具，帮助您了解关键词搜索趋势、地域分布等数据采集技术。'
  },
  {
    question: '如何开始使用？',
    answer: '首先在配置页面设置您的数据库和Redis连接信息，然后添加您的百度账号Cookie，最后在数据采集页面输入关键词、选择时间范围和地域即可开始获取数据。'
  },
  {
    question: '数据采集需要多长时间？',
    answer: '采集时间取决于关键词数量、时间范围和选择的地域数量。系统采用智能爬取策略，通常每个请求间隔0.1-0.3秒。大量数据采集建议使用任务调度功能，系统会自动完成采集。'
  },
  {
    question: '支持哪些数据导出格式？',
    answer: '当前支持CSV、Excel、JSON格式导出。导出的数据包含完整的时间序列信息，可直接导入Excel或其他数据分析工具进行深度分析。'
  },
  {
    question: '如何保证数据采集的稳定性？',
    answer: '系统内置Cookie池管理机制，支持多账号轮换使用；采用智能限流策略，避免触发反爬机制；提供任务断点续传功能，异常中断后可自动恢复。'
  },
  {
    question: '本项目的使用范围是什么？',
    answer: '本项目仅供个人学习和技术研究使用，不得用于任何商业用途。使用本工具时请遵守相关法律法规和百度的服务条款。'
  }
])
</script>

<template>
  <div class="about-container">
    <section class="hero-section">
      <h1 class="page-title gradient-text">关于 BaiduIndexHunter</h1>
      <p class="subtitle">个人学习与技术研究项目</p>
      <div class="version-info">
        <el-tag effect="dark" class="version-tag">v{{ version }}</el-tag>
        <span class="release-date">更新于: {{ releaseDate }}</span>
      </div>
    </section>

    <!-- 重要声明 -->
    <section class="disclaimer-section">
      <el-alert
        title="免责声明"
        type="warning"
        :closable="false"
        show-icon
      >
        <template #default>
          <div class="disclaimer-content">
            <p><strong>本项目仅供个人学习和技术研究使用，严禁用于任何商业用途。</strong></p>
            <p>使用本工具进行数据采集时，请遵守相关法律法规及百度的服务条款。如因使用本工具产生的任何法律责任或后果，由使用者自行承担，本项目作者概不负责。</p>
            <p>本项目为非开源、非商用的个人项目，请勿将其用于任何盈利目的。</p>
          </div>
        </template>
      </el-alert>
    </section>
    
    <div class="content-wrapper">
      <div class="left-column">
        <section class="intro-section">
          <h2>项目介绍</h2>
          <div class="intro-text">
            <p>BaiduIndexHunter 是一个用于学习爬虫技术和数据分析的个人项目，旨在帮助开发者了解百度指数数据的采集方法和相关技术实现。</p>
            <p>通过本项目，您可以学习关键词趋势分析、数据可视化、任务调度等技术，为您的技术学习和研究工作提供参考。</p>
            <p>本项目采用 Scrapy 框架进行数据采集，支持多账号协同工作，内置智能限流机制，是学习分布式爬虫架构的良好实践案例。</p>
          </div>
        </section>
        
        <section class="advantages-section">
          <h2>技术特点</h2>
          <div class="advantages-list">
            <div class="advantage-item">
              <div class="advantage-number">01</div>
              <div class="advantage-content">
                <h3>Scrapy 框架</h3>
                <p>采用 Scrapy 爬虫框架，支持断点续传、优雅退出、中间件扩展等特性，是学习工业级爬虫的优秀案例。</p>
              </div>
            </div>
            <div class="advantage-item">
              <div class="advantage-number">02</div>
              <div class="advantage-content">
                <h3>高性能并发处理</h3>
                <p>支持多任务并发执行，智能负载均衡，学习如何提升爬虫效率的技术实现。</p>
              </div>
            </div>
            <div class="advantage-item">
              <div class="advantage-number">03</div>
              <div class="advantage-content">
                <h3>全面的数据覆盖</h3>
                <p>支持搜索指数、资讯指数、需求图谱、人群画像、地域分布、兴趣分布等多维度数据采集学习。</p>
              </div>
            </div>
            <div class="advantage-item">
              <div class="advantage-number">04</div>
              <div class="advantage-content">
                <h3>断点续传机制</h3>
                <p>采集过程中如遇异常中断，系统自动保存进度，重启后可从断点继续，学习状态持久化技术。</p>
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
                <el-icon :size="24" color="#4facfe">
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
          <h2>技术架构</h2>
          <div class="tech-list">
            <div class="tech-category">
              <h3>前端技术</h3>
              <ul>
                <li>Vue 3 + Composition API</li>
                <li>Element Plus UI组件库</li>
                <li>Vue Router 路由管理</li>
                <li>Pinia 状态管理</li>
                <li>ECharts 数据可视化</li>
              </ul>
            </div>
            <div class="tech-category">
              <h3>后端技术</h3>
              <ul>
                <li>Python + Flask 框架</li>
                <li>Scrapy 爬虫框架</li>
                <li>Redis 缓存与队列</li>
                <li>MySQL 数据存储</li>
                <li>智能Cookie池管理</li>
              </ul>
            </div>
            <div class="tech-category">
              <h3>数据处理</h3>
              <ul>
                <li>Pandas 数据分析</li>
                <li>NumPy 科学计算</li>
                <li>多格式数据导出</li>
                <li>实时数据流处理</li>
              </ul>
            </div>
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
  padding-bottom: 60px;
}

.hero-section {
  text-align: center;
  margin-bottom: 30px;
  padding-bottom: 30px;
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

.disclaimer-section {
  margin-bottom: 30px;
}

.disclaimer-content {
  line-height: 1.8;
}

.disclaimer-content p {
  margin: 8px 0;
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
  background-color: white;
  border-radius: var(--border-radius-large);
  padding: 30px;
  box-shadow: var(--shadow-light);
  border: 1px solid var(--border-lighter);
}

h2 {
  font-size: 1.6rem;
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
  font-size: 1.05rem;
  line-height: 1.8;
  color: var(--text-regular);
}

.intro-text p {
  margin-bottom: 15px;
}

.advantages-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.advantage-item {
  display: flex;
  gap: 20px;
  padding: 20px;
  background-color: #f8fafc;
  border-radius: var(--border-radius-medium);
  transition: all 0.3s ease;
  border: 1px solid transparent;
}

.advantage-item:hover {
  transform: translateX(5px);
  background-color: white;
  box-shadow: var(--shadow-medium);
  border-color: var(--primary-light);
}

.advantage-number {
  font-size: 2rem;
  font-weight: bold;
  color: var(--primary-color);
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  flex-shrink: 0;
}

.advantage-content h3 {
  font-size: 1.15rem;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.advantage-content p {
  color: var(--text-regular);
  line-height: 1.6;
}

.faq-answer {
  padding: 10px 0;
  color: var(--text-regular);
  line-height: 1.6;
}

/* Features List Styles */
.features-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.feature-item {
  display: flex;
  gap: 15px;
  padding: 15px;
  border-radius: var(--border-radius-medium);
  transition: all 0.3s ease;
  align-items: flex-start;
}

.feature-item:hover {
  background-color: #f8fafc;
}

.feature-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--primary-light);
  border-radius: 10px;
  flex-shrink: 0;
}

.feature-title {
  font-size: 1.1rem;
  margin-bottom: 5px;
  color: var(--text-primary);
}

.feature-description {
  color: var(--text-secondary);
  font-size: 0.9rem;
  line-height: 1.5;
}

/* Tech Stack Styles */
.tech-list {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.tech-category h3 {
  font-size: 1.1rem;
  margin-bottom: 10px;
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
  padding: 6px 0;
  color: var(--text-regular);
  position: relative;
  padding-left: 18px;
  font-size: 0.95rem;
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

/* 响应式设计 */
@media (max-width: 1024px) {
  .content-wrapper {
    grid-template-columns: 1fr;
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
}
</style>
