import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: {
      title: '主页 - BaiduIndexHunter'
    }
  },
  {
    path: '/data-collection',
    name: 'DataCollection',
    component: () => import('../views/DataCollection.vue'),
    meta: {
      title: '数据采集 - BaiduIndexHunter'
    }
  },
  {
    path: '/cookie-manager',
    name: 'CookieManager',
    component: () => import('../views/CookieManager.vue'),
    meta: {
      title: 'Cookie管理 - BaiduIndexHunter'
    }
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/dashboard/Dashboard.vue'),
    meta: {
      title: '数据大屏 - BaiduIndexHunter'
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue'),
    meta: {
      title: '配置信息 - BaiduIndexHunter'
    }
  },
  {
    path: '/about',
    name: 'About',
    component: () => import('../views/About.vue'),
    meta: {
      title: '关于我们 - BaiduIndexHunter'
    }
  },
  {
    path: '/privacy',
    name: 'Privacy',
    component: () => import('../views/Privacy.vue'),
    meta: {
      title: '隐私政策 - BaiduIndexHunter'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由前置守卫，设置页面标题
router.beforeEach((to, from, next) => {
  if (to.meta.title) {
    document.title = to.meta.title
  }
  next()
})

export default router 