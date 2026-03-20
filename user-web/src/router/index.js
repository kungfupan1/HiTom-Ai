import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: '注册' }
  },
  {
    path: '/',
    component: () => import('@/layout/MainLayout.vue'),
    redirect: '/ai/image',
    children: [
      // AI 制图智能体
      {
        path: 'ai/image',
        name: 'ImageTool',
        component: () => import('@/views/ai/ImageTool.vue'),
        meta: { title: '商品图生成' }
      },
      {
        path: 'ai/video',
        name: 'VideoTool',
        component: () => import('@/views/ai/VideoTool.vue'),
        meta: { title: '带货视频生成' }
      },
      {
        path: 'ai/video/general',
        name: 'GeneralVideoTool',
        component: () => import('@/views/service/ComingSoon.vue'),
        meta: { title: '普通视频生成' }
      },
      // 跨境服务资源
      {
        path: 'service/shop',
        name: 'ServiceShop',
        component: () => import('@/views/service/ComingSoon.vue'),
        meta: { title: '店铺买卖/租赁' }
      },
      {
        path: 'service/course',
        name: 'ServiceCourse',
        component: () => import('@/views/service/ComingSoon.vue'),
        meta: { title: '课程+陪跑' }
      },
      {
        path: 'service/logistics',
        name: 'ServiceLogistics',
        component: () => import('@/views/service/ComingSoon.vue'),
        meta: { title: '货代/小包/海外仓' }
      },
      {
        path: 'service/software',
        name: 'ServiceSoftware',
        component: () => import('@/views/service/ComingSoon.vue'),
        meta: { title: '增强软件' }
      },
      {
        path: 'service/network',
        name: 'ServiceNetwork',
        component: () => import('@/views/service/ComingSoon.vue'),
        meta: { title: '网络&硬件服务' }
      },
      {
        path: 'service/other',
        name: 'ServiceOther',
        component: () => import('@/views/service/ComingSoon.vue'),
        meta: { title: '其他合作' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  if (!['/login', '/register'].includes(to.path) && !userStore.isLoggedIn) {
    next('/login')
  } else {
    next()
  }
})

export default router