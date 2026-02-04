<script setup>
import { ref } from 'vue'

const lastUpdated = ref('2026-02-04')
</script>

<template>
  <div class="privacy-container">
    <h1 class="page-title">使用条款与免责声明</h1>
    <p class="last-updated">最后更新: {{ lastUpdated }}</p>
    
    <div class="privacy-content">
      <section class="privacy-section warning-section">
        <h2>重要声明</h2>
        <el-alert
          title="请仔细阅读以下内容"
          type="warning"
          :closable="false"
          show-icon
        >
          <template #default>
            <p>使用本工具即表示您已阅读、理解并同意以下所有条款。如不同意，请立即停止使用。</p>
          </template>
        </el-alert>
      </section>

      <section class="privacy-section">
        <h2>项目性质</h2>
        <p>BaiduIndexHunter（以下简称"本项目"）是一个<strong>仅供个人学习和技术研究</strong>的项目。</p>
        <ul>
          <li><strong>非商业用途</strong>：本项目不得用于任何商业目的，包括但不限于出售、出租、提供付费服务等。</li>
          <li><strong>非开源项目</strong>：本项目为个人私有项目，未经授权不得复制、分发或修改。</li>
          <li><strong>学习研究</strong>：本项目仅用于学习爬虫技术、数据分析和软件架构等技术知识。</li>
        </ul>
      </section>
      
      <section class="privacy-section">
        <h2>免责声明</h2>
        <p>使用本项目前，请务必了解以下免责条款：</p>
        <ul>
          <li><strong>法律责任</strong>：使用本工具进行数据采集所产生的任何法律责任由使用者自行承担，项目作者概不负责。</li>
          <li><strong>服务条款</strong>：使用者应自行遵守百度及相关平台的服务条款和使用协议。</li>
          <li><strong>数据准确性</strong>：本项目不保证采集数据的准确性、完整性或时效性。</li>
          <li><strong>服务中断</strong>：本项目可能因各种原因无法正常工作，作者不承担任何服务中断的责任。</li>
          <li><strong>商业损失</strong>：如因使用本项目进行商业活动而产生的任何损失，作者不承担任何责任。</li>
        </ul>
      </section>

      <section class="privacy-section">
        <h2>使用限制</h2>
        <p>使用本项目时，您同意遵守以下限制：</p>
        <ul>
          <li>不得将本项目用于任何商业用途</li>
          <li>不得将采集的数据用于违法活动</li>
          <li>不得滥用本工具对目标网站造成过大负载</li>
          <li>不得将本项目的代码或功能转售给他人</li>
          <li>应合理控制采集频率，避免影响目标网站正常运行</li>
        </ul>
      </section>
      
      <section class="privacy-section">
        <h2>数据说明</h2>
        <p>关于本项目处理的数据：</p>
        <ul>
          <li><strong>本地存储</strong>：所有数据均存储在您的本地设备上，不会上传至任何外部服务器。</li>
          <li><strong>Cookie信息</strong>：您提供的Cookie仅用于数据采集，存储在本地数据库中。</li>
          <li><strong>采集数据</strong>：采集的百度指数数据仅保存在您的本地环境中。</li>
        </ul>
      </section>
      
      <section class="privacy-section">
        <h2>知识产权</h2>
        <p>本项目的相关知识产权说明：</p>
        <ul>
          <li>本项目的代码、设计和文档归项目作者所有。</li>
          <li>百度指数相关商标和数据归百度公司所有。</li>
          <li>本项目使用的开源组件遵循各自的开源协议。</li>
        </ul>
      </section>

      <section class="privacy-section">
        <h2>条款变更</h2>
        <p>本使用条款可能会不时更新。继续使用本项目即表示您接受更新后的条款。</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.privacy-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
  color: #333;
}

.page-title {
  font-size: 2.2rem;
  color: #303133;
  margin-bottom: 10px;
  text-align: center;
}

.last-updated {
  text-align: center;
  color: #909399;
  margin-bottom: 40px;
  font-style: italic;
}

.privacy-content {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 30px;
}

.privacy-section {
  margin-bottom: 30px;
}

.warning-section {
  margin-bottom: 40px;
}

.privacy-section h2 {
  color: #303133;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 10px;
  margin-bottom: 15px;
  font-size: 1.5rem;
}

.privacy-section p {
  line-height: 1.7;
  margin-bottom: 15px;
  color: #606266;
}

.privacy-section ul {
  padding-left: 20px;
  margin-bottom: 15px;
}

.privacy-section li {
  margin-bottom: 8px;
  line-height: 1.6;
  color: #606266;
}

strong {
  color: #303133;
}

@media (max-width: 768px) {
  .privacy-content {
    padding: 20px;
  }
  
  .page-title {
    font-size: 1.8rem;
  }
  
  .privacy-section h2 {
    font-size: 1.3rem;
  }
}
</style>
