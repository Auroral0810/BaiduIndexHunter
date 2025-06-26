import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/Home.vue'),
    meta: {
      title: '主页 - 百度指数猎手'
    }
  },
  {
    path: '/data-collection',
    name: 'DataCollection',
    component: () => import('../views/DataCollection.vue'),
    meta: {
      title: '数据采集 - 百度指数猎手'
    }
  },
  {
    path: '/settings',
    name: 'Settings',
    component: () => import('../views/Settings.vue'),
    meta: {
      title: '配置信息 - 百度指数猎手'
    }
  },
  {
    path: '/about',
    name: 'About',
    component: () => import('../views/About.vue'),
    meta: {
      title: '关于我们 - 百度指数猎手'
    }
  },
  {
    path: '/privacy',
    name: 'Privacy',
    component: () => import('../views/Privacy.vue'),
    meta: {
      title: '隐私政策 - 百度指数猎手'
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