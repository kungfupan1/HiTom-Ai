import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

// 内容配置 key 和路由 path 的映射
const contentConfigRouteMap = {
  '/shrimp/openclaw': 'shrimp_openclaw',
  '/shrimp/skills': 'shrimp_skills',
  '/shrimp/ai-staff': 'shrimp_ai_staff',
  '/service/shop': 'service_shop',
  '/service/course': 'service_course',
  '/service/logistics': 'service_logistics',
  '/service/software': 'service_software',
  '/service/network': 'service_network',
  '/service/other': 'service_other'
}

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
        component: () => import('@/views/ai/GeneralVideoTool.vue'),
        meta: { title: '普通视频生成' }
      },
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
      },
      {
        path: 'shrimp/openclaw',
        name: 'ShrimpOpenClaw',
        component: () => import('@/views/shrimp/OpenClawDeploy.vue'),
        meta: { title: 'OpenClaw部署' }
      },
      {
        path: 'shrimp/skills',
        name: 'ShrimpSkills',
        component: () => import('@/views/service/ComingSoon.vue'),
        meta: { title: 'Skills市场' }
      },
      {
        path: 'shrimp/ai-staff',
        name: 'ShrimpAIStaff',
        component: () => import('@/views/service/ComingSoon.vue'),
        meta: { title: 'AI员工打造' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 获取内容配置启用状态
function isContentEnabled(path) {
  const configKey = contentConfigRouteMap[path]
  if (!configKey) return true // 非内容配置页面，放行

  // 从 localStorage 获取配置
  try {
    const configs = JSON.parse(localStorage.getItem('contentConfigs') || '{}')
    // 如果没有配置，默认启用
    return configs[configKey] !== false
  } catch {
    return true
  }
}

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  // 检查登录状态
  if (!['/login', '/register'].includes(to.path) && !userStore.isLoggedIn) {
    next('/login')
    return
  }

  // 检查内容配置启用状态
  if (!isContentEnabled(to.path)) {
    // 跳转到首页
    next('/ai/image')
    return
  }

  next()
})

export default router