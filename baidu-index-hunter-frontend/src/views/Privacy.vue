<script setup>
import { ref } from 'vue'
import { Warning, InfoFilled } from '@element-plus/icons-vue'
import { useI18n } from 'vue-i18n'
const { t: $t } = useI18n()
const lastUpdated = ref('2026-02-04')
</script>

<template>
  <div class="privacy-page">
    <header class="privacy-header">
      <h1 class="page-title">{{$t('views.privacy.s235yk')}}</h1>
      <p class="last-updated">{{$t('views.privacy.h5s6kb')}}{{ lastUpdated }}</p>
    </header>

    <div class="privacy-container">
      <!-- 核心提示 -->
      <div class="notice-box warning">
        <div class="icon"><el-icon><Warning /></el-icon></div>
        <div class="content">
          <h4>{{$t('views.privacy.h1c30b')}}</h4>
          <p>{{$t('views.privacy.e134p8')}}</p>
        </div>
      </div>

      <article class="privacy-content">
        <section>
          <h2>{{$t('views.privacy.b6r88l')}}</h2>
          <p>{{$t('views.privacy.s8vj2d')}}<strong>{{$t('views.privacy.e03co4')}}</strong>{{$t('views.privacy.udoyxl')}}</p>
          <ul>
            <li><strong>{{$t('views.privacy.3uv9gk')}}</strong>{{$t('views.privacy.9d6b89')}}</li>
            <li><strong>{{$t('views.privacy.8r1k14')}}</strong>{{$t('views.privacy.dyy432')}}</li>
          </ul>
        </section>

        <section>
          <h2>{{$t('views.privacy.713nu0')}}</h2>
          <p>{{$t('views.privacy.iqgq27')}}</p>
          <ul>
            <li><strong>{{$t('views.privacy.mkc761')}}</strong>{{$t('views.privacy.8iig8g')}}</li>
            <li><strong>{{$t('views.privacy.txq15p')}}</strong>{{$t('views.privacy.ubk42n')}}</li>
            <li><strong>{{$t('views.privacy.0b2sm5')}}</strong>{{$t('views.privacy.ejrobp')}}</li>
          </ul>
        </section>

        <section>
          <h2>{{$t('views.privacy.694y53')}}</h2>
          <div class="notice-box info">
            <div class="icon"><el-icon><InfoFilled /></el-icon></div>
            <div class="content">
              <p>{{$t('views.privacy.433f25')}}</p>
            </div>
          </div>
          <p>{{$t('views.privacy.v332js')}}</p>
          <ul>
            <li>{{$t('views.privacy.9ue76a')}}</li>
            <li>{{$t('views.privacy.r09huq')}}</li>
            <li>{{$t('views.privacy.c3b520')}}</li>
          </ul>
        </section>

        <section>
          <h2>{{$t('views.privacy.27qftz')}}</h2>
          <p>{{$t('views.privacy.3bg723')}}</p>
          <ul>
            <li><strong>{{$t('views.privacy.ck5753')}}</strong>{{$t('views.privacy.b91mv3')}}</li>
            <li><strong>{{$t('views.privacy.zz3h3w')}}</strong>{{$t('views.privacy.k411bo')}}</li>
          </ul>
        </section>

        <section>
          <h2>{{$t('views.privacy.18573h')}}</h2>
          <p>{{$t('views.privacy.4x7z98')}}</p>
        </section>
      </article>
    </div>
  </div>
</template>

<style scoped>
.privacy-page {
  padding: 60px 24px 100px;
  background-color: var(--color-bg-body);
  min-height: 100vh;
}

.privacy-header {
  text-align: center;
  margin-bottom: 60px;
}

.page-title {
  font-size: 2.5rem;
  font-weight: 800;
  color: var(--color-text-main);
  margin-bottom: 12px;
  letter-spacing: -0.5px;
}

.last-updated {
  color: var(--color-text-secondary);
  font-size: 0.95rem;
}

.privacy-container {
  max-width: 800px; /* 窄屏阅读体验更好 */
  margin: 0 auto;
}

/* Notice Box */
.notice-box {
  display: flex;
  gap: 16px;
  padding: 20px;
  border-radius: 12px;
  margin-bottom: 40px;
}

.notice-box.warning {
  background: rgba(245, 158, 11, 0.1);
  border: 1px solid rgba(245, 158, 11, 0.2);
  color: #b45309;
}

.notice-box.info {
  background: var(--color-bg-subtle);
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  margin: 20px 0;
  padding: 16px;
}

.notice-box .icon {
  font-size: 1.5rem;
  padding-top: 2px;
}

.notice-box h4 {
  font-weight: 700;
  margin-bottom: 8px;
  color: inherit;
}

.notice-box p {
  margin: 0;
  line-height: 1.6;
  font-size: 0.95rem;
  color: inherit;
}

/* Content Typography */
.privacy-content section {
  margin-bottom: 48px;
}

h2 {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--color-text-main);
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-border);
}

p {
  font-size: 1.05rem;
  line-height: 1.8;
  color: var(--color-text-regular);
  margin-bottom: 16px;
}

ul {
  padding-left: 20px;
  margin-bottom: 24px;
}

li {
  font-size: 1.05rem;
  line-height: 1.7;
  color: var(--color-text-regular);
  margin-bottom: 12px;
  position: relative;
  padding-left: 8px;
}

strong {
  color: var(--color-text-main);
  font-weight: 600;
}

/* Dark Mode Adaptation via CSS Variables */
/* Assuming global variables are set in App.vue, this will adapt automatically */

@media (max-width: 640px) {
  .page-title {
    font-size: 2rem;
  }
  
  .privacy-page {
    padding-top: 40px;
  }
}
</style>
