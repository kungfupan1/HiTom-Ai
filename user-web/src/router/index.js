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
    redirect: '/ai/video',
    children: [
      {
        path: 'ai/video',
        name: 'VideoTool',
        component: () => import('@/views/ai/VideoTool.vue'),
        meta: { title: '视频生成' }
      },
      {
        path: 'ai/image',
        name: 'ImageTool',
        component: () => import('@/views/ai/ImageTool.vue'),
        meta: { title: '图片生成' }
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