<script setup>
import { useRouter } from 'vue-router'
import { HomeFilled } from '@element-plus/icons-vue'

const router = useRouter()

const handleGoHome = () => {
  router.push('/')
}
</script>

<template>
  <div class="not-found-container">
    <div class="content">
      <div class="error-code">404</div>
      <div class="message-box">
        <h1 class="title">{{ $t('views.notfound.h1') }}</h1>
        <p class="description">{{ $t('views.notfound.desc') }}</p>
        <button class="home-btn" @click="handleGoHome">
          <el-icon><HomeFilled /></el-icon>
          <span>{{ $t('views.notfound.btn') }}</span>
        </button>
      </div>
      
      <!-- Background Elements -->
      <div class="bg-circle circle-1"></div>
      <div class="bg-circle circle-2"></div>
      <div class="bg-grid"></div>
    </div>
  </div>
</template>

<style scoped>
.not-found-container {
  height: 100vh;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: var(--color-bg-body);
  position: relative;
  overflow: hidden;
}

.content {
  position: relative;
  z-index: 10;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.error-code {
  font-size: 12rem;
  font-weight: 900;
  line-height: 1;
  background: linear-gradient(135deg, var(--color-primary) 0%, #a855f7 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  opacity: 0.8;
  letter-spacing: -5px;
  animation: float 6s ease-in-out infinite;
  text-shadow: 0 10px 30px rgba(79, 70, 229, 0.3);
  position: relative;
  z-index: 5;
}

.message-box {
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  padding: 40px 60px;
  border-radius: 24px;
  border: 1px solid var(--glass-border);
  box-shadow: var(--shadow-xl);
  margin-top: -40px;
  max-width: 500px;
  animation: slideUp 0.8s ease-out;
  position: relative;
  z-index: 5;
}

.title {
  font-size: 2rem;
  font-weight: 700;
  color: var(--color-text-main);
  margin-bottom: 16px;
}

.description {
  color: var(--color-text-secondary);
  margin-bottom: 32px;
  line-height: 1.6;
  font-size: 1.1rem;
}

.home-btn {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  padding: 14px 32px;
  background: var(--color-primary-gradient);
  border: none;
  border-radius: 50px;
  color: white;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 10px 20px rgba(79, 70, 229, 0.3);
}

.home-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 15px 30px rgba(79, 70, 229, 0.4);
}

.home-btn:active {
  transform: translateY(1px);
}

/* Background Elements */
.bg-circle {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  z-index: 1;
  opacity: 0.6;
}

.circle-1 {
  width: 400px;
  height: 400px;
  background: var(--color-primary);
  top: -100px;
  right: -100px;
  opacity: 0.15;
}

.circle-2 {
  width: 300px;
  height: 300px;
  background: #a855f7;
  bottom: -50px;
  left: -50px;
  opacity: 0.15;
}

.bg-grid {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image: radial-gradient(var(--color-border) 1px, transparent 1px);
  background-size: 40px 40px;
  opacity: 0.5;
  z-index: 0;
}

@keyframes float {
  0% { transform: translateY(0px) rotate(0deg); }
  50% { transform: translateY(-20px) rotate(2deg); }
  100% { transform: translateY(0px) rotate(0deg); }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(40px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
