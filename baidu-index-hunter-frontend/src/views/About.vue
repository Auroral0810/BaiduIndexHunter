<script setup>
import { ref } from 'vue'
import {
  Lightning,
  DataAnalysis,
  User,
  DocumentCopy,
  TrendCharts,
  Monitor
} from '@element-plus/icons-vue'

const version = ref('1.0.0')
const releaseDate = ref('2025-6-26')

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
    answer: 'BaiduIndexHunter是一个高效、稳定的百度指数数据采集和分析工具，帮助您获取关键词搜索趋势、地域分布等重要数据。'
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
    question: '产品技术支持与售后',
    answer: '我们提供完善的技术支持服务，包括安装部署指导、使用培训、问题排查等。购买后可获得专属技术支持渠道，响应时间不超过24小时。'
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
          <h2>产品介绍</h2>
          <div class="intro-text">
            <p>BaiduIndexHunter是一个专为营销人员、数据分析师和研究人员设计的专业工具，旨在帮助用户高效获取和分析百度指数数据。</p>
            <p>通过本产品，您可以轻松监控关键词趋势、了解用户需求变化、分析地域分布特征，为您的市场决策和研究工作提供强有力的数据支撑。我们致力于提供最稳定、最高效的数据采集体验。</p>
            <p>本产品采用先进的分布式架构设计，支持多账号协同工作，内置智能限流机制，确保数据采集的稳定性和可靠性。无论您是需要简单的数据导出，还是复杂的数据分析，BaiduIndexHunter都能满足您的需求。</p>
          </div>
        </section>
        
        <section class="advantages-section">
          <h2>产品优势</h2>
          <div class="advantages-list">
            <div class="advantage-item">
              <div class="advantage-number">01</div>
              <div class="advantage-content">
                <h3>企业级稳定性</h3>
                <p>采用多Cookie池轮换机制，智能故障转移，确保7x24小时稳定运行，数据采集成功率高达99%以上。</p>
              </div>
            </div>
            <div class="advantage-item">
              <div class="advantage-number">02</div>
              <div class="advantage-content">
                <h3>高性能并发处理</h3>
                <p>支持多任务并发执行，智能负载均衡，相比传统方案效率提升300%，大幅缩短数据获取时间。</p>
              </div>
            </div>
            <div class="advantage-item">
              <div class="advantage-number">03</div>
              <div class="advantage-content">
                <h3>全面的数据覆盖</h3>
                <p>支持搜索指数、资讯指数、需求图谱、人群画像、地域分布、兴趣分布等全方位数据采集，满足各类分析需求。</p>
              </div>
            </div>
            <div class="advantage-item">
              <div class="advantage-number">04</div>
              <div class="advantage-content">
                <h3>断点续传机制</h3>
                <p>采集过程中如遇异常中断，系统自动保存进度，重启后可从断点继续，避免重复劳动和时间浪费。</p>
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
                <li>Python + Flask框架</li>
                <li>Redis 缓存与队列</li>
                <li>MySQL 数据存储</li>
                <li>多线程任务调度</li>
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
        
        <section class="service-section">
          <h2>服务支持</h2>
          <div class="service-content">
            <div class="service-item">
              <h3>💼 企业定制服务</h3>
              <p>根据您的业务需求，提供定制化功能开发和系统集成服务。</p>
            </div>
            <div class="service-item">
              <h3>🔧 技术支持</h3>
              <p>提供安装部署指导、使用培训、问题排查等全方位技术支持。</p>
            </div>
            <div class="service-item">
              <h3>📈 数据分析咨询</h3>
              <p>协助您解读数据，提供专业的市场分析建议和决策支持。</p>
            </div>
            <div class="service-item">
              <h3>🔄 持续更新维护</h3>
              <p>定期更新系统功能，及时适配百度指数平台变化，确保长期稳定使用。</p>
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

.intro-section, .advantages-section, .faq-section,
.features-section, .tech-stack-section, .service-section {
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

.advantages-list {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.advantage-item {
  display: flex;
  gap: 20px;
  padding: 20px;
  background-color: #f9f9f9;
  border-radius: var(--border-radius-medium);
  transition: all 0.3s ease;
}

.advantage-item:hover {
  transform: translateX(5px);
  box-shadow: var(--shadow-light);
}

.advantage-number {
  font-size: 2rem;
  font-weight: bold;
  color: var(--primary-color);
  width: 60px;
  height: 60px;
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
  font-size: 1.2rem;
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

.service-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.service-item {
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: var(--border-radius-medium);
  transition: all 0.3s ease;
}

.service-item:hover {
  background-color: #f0f2f5;
  transform: translateY(-2px);
}

.service-item h3 {
  font-size: 1.1rem;
  margin-bottom: 8px;
  color: var(--text-primary);
}

.service-item p {
  color: var(--text-regular);
  line-height: 1.6;
  font-size: 0.95rem;
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
  
  .advantage-item {
    flex-direction: column;
    align-items: center;
    text-align: center;
  }
  
  h2:after {
    left: 50%;
    transform: translateX(-50%);
  }
  
  h2 {
    text-align: center;
  }
}
</style> 