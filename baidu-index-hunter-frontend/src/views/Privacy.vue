<script setup>
import { ref } from 'vue'

const lastUpdated = ref('2025-6-26')
</script>

<template>
  <div class="privacy-container">
    <h1 class="page-title">隐私政策</h1>
    <p class="last-updated">最后更新: {{ lastUpdated }}</p>
    
    <div class="privacy-content">
      <section class="privacy-section">
        <h2>引言</h2>
        <p>BaiduIndexHunter（"我们"、"我们的"或"本应用"）尊重并保护所有使用服务用户的个人隐私权。为了给您提供更准确、更优质的服务，本应用会按照本隐私政策的规定使用和披露您的个人信息。请您仔细阅读本隐私政策。</p>
      </section>
      
      <section class="privacy-section">
        <h2>信息收集</h2>
        <p>我们收集的信息类型取决于您如何使用我们的服务。主要包括：</p>
        <ul>
          <li><strong>账户信息</strong>：当您注册BaiduIndexHunter账户时，我们会收集您提供的信息，如用户名、电子邮件地址和密码。</li>
          <li><strong>使用数据</strong>：我们会收集您如何使用我们服务的数据，包括您搜索的关键词、数据采集配置和操作日志。</li>
          <li><strong>设备信息</strong>：我们可能会收集有关您使用我们服务的设备的信息，如IP地址、浏览器类型和操作系统版本。</li>
          <li><strong>Cookie信息</strong>：为提供更个性化的服务，我们会使用Cookie来存储和获取信息。您可以通过浏览器设置拒绝Cookie，但这可能会影响部分功能的正常使用。</li>
        </ul>
      </section>
      
      <section class="privacy-section">
        <h2>信息使用</h2>
        <p>我们使用收集的信息主要用于：</p>
        <ul>
          <li>提供、维护和改进我们的服务</li>
          <li>开发新的服务和功能</li>
          <li>了解您如何使用我们的服务</li>
          <li>个性化您的体验并提供定制化内容</li>
          <li>向您发送技术通知、更新和安全警报</li>
          <li>提供客户支持并回应您的请求</li>
          <li>监控和分析趋势、使用情况和活动</li>
        </ul>
      </section>
      
      <section class="privacy-section">
        <h2>信息共享</h2>
        <p>我们不会将您的个人信息出售、出租或与任何第三方共享，除非有以下情况之一：</p>
        <ul>
          <li><strong>经您授权</strong>：获得您的明确同意后</li>
          <li><strong>法律要求</strong>：遵守法律法规的要求、法院命令或其他法律程序</li>
          <li><strong>保护权利</strong>：保护BaiduIndexHunter、我们的用户或公众的权利、财产或安全</li>
          <li><strong>业务转让</strong>：在合并、收购或资产出售的情况下</li>
        </ul>
      </section>
      
      <section class="privacy-section">
        <h2>数据安全</h2>
        <p>我们非常重视您的个人信息安全，并采取合理的物理、技术和管理措施保护您的个人信息不被未经授权的访问、披露、使用、修改或丢失。这些措施包括但不限于：</p>
        <ul>
          <li>使用加密技术保护数据传输和存储</li>
          <li>实施访问控制机制，确保只有授权人员才能访问个人信息</li>
          <li>定期安全评估和审计</li>
        </ul>
        <p>但请注意，尽管我们已采取合理措施保护您的信息，但互联网上的传输方法或电子存储方法并不是100%安全的。因此，我们不能保证信息的绝对安全。</p>
      </section>
      
      <section class="privacy-section">
        <h2>Cookie政策</h2>
        <p>我们使用Cookie和类似技术来提供和支持我们的服务。当您首次访问我们的网站时，我们可能会请求您的许可来使用Cookie。</p>
        <p><strong>什么是Cookie？</strong> Cookie是存储在您设备上的小型文本文件，它们帮助我们提供更好的用户体验、理解用户行为并保护您的账户安全。</p>
        <p><strong>我们如何使用Cookie？</strong> 我们使用Cookie来：</p>
        <ul>
          <li>记住您的登录状态和偏好设置</li>
          <li>提高网站性能和速度</li>
          <li>分析网站流量和使用情况</li>
          <li>防止欺诈活动和改善安全性</li>
        </ul>
        <p><strong>如何管理Cookie？</strong> 大多数浏览器允许您查看和删除Cookie，以及选择是否接受Cookie。但请注意，如果您选择禁用Cookie，您可能无法使用我们服务的所有功能。</p>
      </section>
      
      <section class="privacy-section">
        <h2>第三方服务</h2>
        <p>我们的服务可能包含指向第三方网站或服务的链接，这些第三方网站或服务有其自己的隐私政策。我们对这些第三方网站或服务的内容、隐私政策或实践不负责任。建议您在使用这些网站或服务前阅读它们的隐私政策。</p>
      </section>
      
      <section class="privacy-section">
        <h2>儿童隐私</h2>
        <p>我们的服务不面向13岁以下的儿童。我们不会故意收集13岁以下儿童的个人信息。如果您是父母或监护人，并且您知道您的孩子向我们提供了个人信息，请联系我们。如果我们发现我们在未获得可验证的父母同意的情况下收集了13岁以下儿童的个人信息，我们会采取措施删除该信息。</p>
      </section>
      
      <section class="privacy-section">
        <h2>您的权利</h2>
        <p>根据适用的数据保护法律，您可能有以下权利：</p>
        <ul>
          <li><strong>访问权</strong>：您有权请求访问我们持有的关于您的个人信息</li>
          <li><strong>更正权</strong>：您有权要求更正不准确的个人信息</li>
          <li><strong>删除权</strong>：在某些情况下，您有权要求删除您的个人信息</li>
          <li><strong>限制处理权</strong>：在某些情况下，您有权要求限制对您个人信息的处理</li>
          <li><strong>数据可携性权</strong>：您有权以结构化、常用和机器可读的格式接收您提供给我们的个人信息</li>
          <li><strong>反对权</strong>：在某些情况下，您有权反对我们处理您的个人信息</li>
        </ul>
        <p>如需行使这些权利，请通过下方联系方式与我们联系。</p>
      </section>
      
      <section class="privacy-section">
        <h2>隐私政策更新</h2>
        <p>我们可能会不时更新本隐私政策。当我们更新隐私政策时，我们会在网站上发布更新后的版本，并更新最后修改日期。对于重大更改，我们可能会通过在网站上发布通知或直接向您发送通知来通知您。我们鼓励您定期查看本隐私政策，以了解我们如何保护您的信息。</p>
      </section>
      
      <section class="privacy-section">
        <h2>联系我们</h2>
        <p>如果您对本隐私政策有任何疑问、意见或请求，请通过以下方式联系我们：</p>
        <p><strong>电子邮件</strong>：privacy@baiduindexhunter.com</p>
        <p>我们会在合理的时间范围内回复您的请求。</p>
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