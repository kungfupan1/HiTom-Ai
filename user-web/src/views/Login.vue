<template>
  <div class="login-page">
    <div class="login-card cyber-glass">
      <h1 class="gradient-text">🤖 Hi-Tom-AI</h1>
      <p class="subtitle">智能创作平台</p>

      <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            prefix-icon="User"
            size="large"
            class="cyber-input"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            size="large"
            show-password
            class="cyber-input"
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleLogin"
            class="neon-btn"
            style="width: 100%"
          >
            登 录
          </el-button>
        </el-form-item>

        <div class="register-link">
          还没有账号？<router-link to="/register">立即注册</router-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/api/request'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

// 接力式预加载 - 登录页渲染后立即开始
const preloadComponents = () => {
  // 预加载顺序：MainLayout → VideoTool → ImageTool → 其他组件
  import('@/layout/MainLayout.vue')
    .then(() => import('@/views/ai/VideoTool.vue'))
    .then(() => import('@/views/ai/ImageTool.vue'))
    .then(() => import('@/views/ai/GeneralVideoTool.vue'))
    .then(() => import('@/views/service/ComingSoon.vue'))
    .then(() => import('@/views/shrimp/OpenClawDeploy.vue'))
    .catch(err => console.warn('预加载组件失败:', err))
}

onMounted(() => {
  // 登录页已渲染，启动接力预加载
  preloadComponents()
})

const handleLogin = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      const formData = new FormData()
      formData.append('username', form.username)
      formData.append('password', form.password)

      const res = await request.post('/auth/token', formData)
      // 传入整个响应对象，包含 access_token 和 refresh_token
      await userStore.login(res)

      ElMessage.success('登录成功')
      router.push('/')
    } catch (error) {
      console.error(error)
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%);
}

.login-card {
  width: 400px;
  padding: 40px;
  border-radius: 16px;
}

.login-card h1 {
  text-align: center;
  font-size: 28px;
  margin-bottom: 8px;
}

.subtitle {
  text-align: center;
  color: #888;
  margin-bottom: 30px;
}

:deep(.el-input__wrapper) {
  background: rgba(0, 0, 0, 0.3) !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  box-shadow: none !important;
}

:deep(.el-input__inner) {
  color: #fff !important;
}

.register-link {
  text-align: center;
  color: #888;
  font-size: 14px;
}

.register-link a {
  color: #00f260;
  text-decoration: none;
}
</style>