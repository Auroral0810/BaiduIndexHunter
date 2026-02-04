<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t, tm } = useI18n()
const lastUpdated = '2026-02-04'

// 使用 tm() 获取数组类型的翻译
const projectNatureItems = computed(() => tm('privacy.sections.projectNature.items') || [])
const dataItems = computed(() => tm('privacy.sections.dataNote.items') || [])
const cookieItems = computed(() => tm('privacy.sections.cookieNote.items') || [])
const riskItems = computed(() => tm('privacy.sections.risks.items') || [])
const disclaimerItems = computed(() => tm('privacy.sections.disclaimerTerms.items') || [])
const complianceItems = computed(() => tm('privacy.sections.compliance.items') || [])
</script>

<template>
  <div class="privacy-container">
    <h1 class="page-title">{{ t('privacy.title') }}</h1>
    <p class="last-updated">{{ t('privacy.lastUpdated') }}: {{ lastUpdated }}</p>
    
    <div class="privacy-content">
      <!-- 免责声明 -->
      <el-alert
        :title="t('privacy.disclaimer.title')"
        type="warning"
        :closable="false"
        show-icon
        class="disclaimer-alert"
      >
        <template #default>
          <p>{{ t('privacy.disclaimer.content') }}</p>
        </template>
      </el-alert>

      <section class="privacy-section">
        <h2>{{ t('privacy.sections.projectNature.title') }}</h2>
        <p>{{ t('privacy.sections.projectNature.intro') }}</p>
        <ul>
          <li v-for="(item, index) in projectNatureItems" :key="index">
            {{ item }}
          </li>
        </ul>
      </section>
      
      <section class="privacy-section">
        <h2>{{ t('privacy.sections.dataNote.title') }}</h2>
        <p>{{ t('privacy.sections.dataNote.intro') }}</p>
        <ul>
          <li v-for="(item, index) in dataItems" :key="index">
            {{ item }}
          </li>
        </ul>
      </section>
      
      <section class="privacy-section">
        <h2>{{ t('privacy.sections.cookieNote.title') }}</h2>
        <p>{{ t('privacy.sections.cookieNote.intro') }}</p>
        <ul>
          <li v-for="(item, index) in cookieItems" :key="index">
            {{ item }}
          </li>
        </ul>
      </section>
      
      <section class="privacy-section">
        <h2>{{ t('privacy.sections.risks.title') }}</h2>
        <p>{{ t('privacy.sections.risks.intro') }}</p>
        <ul>
          <li v-for="(item, index) in riskItems" :key="index">
            {{ item }}
          </li>
        </ul>
        <p><strong>{{ t('privacy.sections.risks.note') }}</strong></p>
      </section>
      
      <section class="privacy-section">
        <h2>{{ t('privacy.sections.disclaimerTerms.title') }}</h2>
        <ul>
          <li v-for="(item, index) in disclaimerItems" :key="index">
            {{ item }}
          </li>
        </ul>
      </section>
      
      <section class="privacy-section">
        <h2>{{ t('privacy.sections.compliance.title') }}</h2>
        <p>{{ t('privacy.sections.compliance.intro') }}</p>
        <ul>
          <li v-for="(item, index) in complianceItems" :key="index">
            {{ item }}
          </li>
        </ul>
      </section>
      
      <section class="privacy-section">
        <h2>{{ t('privacy.sections.contact.title') }}</h2>
        <p>{{ t('privacy.sections.contact.content') }}</p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.privacy-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.page-title {
  font-size: 2rem;
  color: var(--text-primary);
  margin-bottom: 10px;
  text-align: center;
}

.last-updated {
  text-align: center;
  color: var(--text-secondary);
  margin-bottom: 20px;
  font-style: italic;
}

.disclaimer-alert {
  margin-bottom: 30px;
}

.disclaimer-alert p {
  margin: 5px 0;
  line-height: 1.6;
}

.privacy-content {
  background-color: var(--bg-card);
  border-radius: 12px;
  box-shadow: var(--shadow-sm);
  padding: 30px;
  border: 1px solid var(--border-color);
}

.privacy-section {
  margin-bottom: 30px;
}

.privacy-section:last-child {
  margin-bottom: 0;
}

.privacy-section h2 {
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 10px;
  margin-bottom: 15px;
  font-size: 1.4rem;
}

.privacy-section p {
  line-height: 1.7;
  margin-bottom: 15px;
  color: var(--text-regular);
}

.privacy-section ul {
  padding-left: 20px;
  margin-bottom: 15px;
}

.privacy-section li {
  margin-bottom: 8px;
  line-height: 1.6;
  color: var(--text-regular);
}

strong {
  color: var(--text-primary);
}

@media (max-width: 768px) {
  .privacy-content {
    padding: 20px;
  }
  
  .page-title {
    font-size: 1.6rem;
  }
  
  .privacy-section h2 {
    font-size: 1.2rem;
  }
}
</style>
