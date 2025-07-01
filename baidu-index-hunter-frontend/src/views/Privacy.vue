<script setup>
import { ref } from 'vue'

const lastUpdated = ref('2025-7-1')  // 更新为今天的日期
</script>

<template>
  <div class="privacy-container">
    <h1 class="page-title">隐私政策</h1>
    <p class="last-updated">最后更新: {{ lastUpdated }}</p>
    
    <div class="privacy-content">
      <section class="privacy-section">
        <h2>引言</h2>
        <p>BaiduIndexHunter（"我们"、"我们的"或"本应用"）致力于保护用户隐私，您的个人信息将仅在合法的范围内使用。为了提供更加优质的服务，我们可能会收集并使用您的个人信息。请您在使用本应用前仔细阅读本隐私政策。</p>
      </section>
      
      <section class="privacy-section">
        <h2>信息收集</h2>
        <p>我们收集的信息包括但不限于以下几类：</p>
        <ul>
          <li><strong>账户信息</strong>：当您注册账户时，我们会收集您的用户名、电子邮件地址、密码等信息。</li>
          <li><strong>使用数据</strong>：为了优化服务，我们会收集您使用爬虫功能的记录，包括查询关键词、任务进度等数据。</li>
          <li><strong>设备信息</strong>：我们可能会收集您的设备信息，如IP地址、浏览器类型和操作系统版本。</li>
          <li><strong>Cookie信息</strong>：我们使用Cookie来提高用户体验，您可选择通过浏览器设置拒绝Cookie。</li>
        </ul>
      </section>
      
      <section class="privacy-section">
        <h2>信息使用</h2>
        <p>我们使用您的个人信息以提供、维护和优化我们的服务，具体用途包括：</p>
        <ul>
          <li>改进我们的爬虫系统和服务功能</li>
          <li>分析用户行为，以优化爬虫任务管理和提高任务执行效率</li>
          <li>根据您的需求推荐相关功能，并优化用户体验</li>
          <li>向您发送必要的技术通知、更新和安全警报</li>
        </ul>
      </section>
      
      <section class="privacy-section">
        <h2>信息共享</h2>
        <p>我们不会出售、出租或泄露您的个人信息，但在以下情况下可能会披露您的信息：</p>
        <ul>
          <li><strong>经您同意</strong>：我们会在获得您明确同意后共享您的信息。</li>
          <li><strong>法律要求</strong>：遵守法律法规、法院命令或其他合法程序。</li>
          <li><strong>保护权利</strong>：当我们需要保护本应用、我们的用户或公众的安全时。</li>
        </ul>
      </section>
      
      <section class="privacy-section">
        <h2>数据安全</h2>
        <p>我们采取物理、技术和管理措施保障您的个人信息的安全。具体措施包括：</p>
        <ul>
          <li>数据加密：传输和存储时采用加密技术。</li>
          <li>访问控制：确保只有授权人员可以访问个人信息。</li>
          <li>安全审计：定期进行安全审查与评估。</li>
        </ul>
        <p>尽管采取了这些措施，但无法完全保证信息在互联网上的安全，因此我们无法确保100%的安全性。</p>
      </section>
      
      <section class="privacy-section">
        <h2>Cookie政策</h2>
        <p>我们使用Cookie和类似技术来提供更个性化的服务，帮助我们优化网站性能并分析使用情况。您可以选择禁用Cookie，但这可能影响一些功能的使用。</p>
        <p><strong>如何管理Cookie？</strong> 您可以通过浏览器设置管理Cookie的使用。如果禁用Cookie，某些功能可能无法使用。</p>
      </section>
      
      <section class="privacy-section">
        <h2>第三方服务</h2>
        <p>本应用可能包含指向第三方服务的链接，这些服务有其独立的隐私政策。我们建议您在访问这些网站前阅读其隐私政策。</p>
      </section>
      
      <section class="privacy-section">
        <h2>儿童隐私</h2>
        <p>本应用不适用于13岁以下儿童，我们不会故意收集13岁以下儿童的个人信息。如发现未获得父母同意的情况下收集了13岁以下儿童的个人信息，我们将采取措施删除该信息。</p>
      </section>
      
      <section class="privacy-section">
        <h2>您的权利</h2>
        <p>根据适用法律，您有以下权利：</p>
        <ul>
          <li><strong>访问权</strong>：请求查看我们存储的个人信息。</li>
          <li><strong>更正权</strong>：请求修改或补充不准确的个人信息。</li>
          <li><strong>删除权</strong>：在特定情况下，要求删除您的个人信息。</li>
          <li><strong>数据携带权</strong>：要求以结构化格式接收并传输您的个人信息。</li>
        </ul>
        <p>如需行使这些权利，请通过以下联系方式联系我们。</p>
      </section>
      
      <section class="privacy-section">
        <h2>隐私政策更新</h2>
        <p>本隐私政策可能会不时更新。我们会在页面上发布更新版本，并注明更新日期。重大变更将通过通知用户的方式进行提示。</p>
      </section>
      
      <section class="privacy-section">
        <h2>联系我们</h2>
        <p>如果您对本隐私政策有任何问题或建议，请通过以下方式联系我们：</p>
        <p><strong>电子邮件</strong>15968588744@163.com</p>
        <p>我们将尽快回复您的请求。</p>
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