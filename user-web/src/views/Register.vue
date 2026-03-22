<template>
  <div class="register-page">
    <div class="register-card cyber-glass">
      <h1 class="gradient-text">🤖 Hi-Tom-AI</h1>
      <p class="subtitle">注册新账号</p>

      <el-form :model="form" :rules="rules" ref="formRef">
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
          />
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="确认密码"
            prefix-icon="Lock"
            size="large"
            show-password
            class="cyber-input"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleRegister"
            class="neon-btn"
            style="width: 100%"
          >
            注 册
          </el-button>
        </el-form-item>

        <div class="login-link">
          已有账号？<router-link to="/login">立即登录</router-link>
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

const router = useRouter()
const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

const validateConfirm = (rule, value, callback) => {
  if (value !== form.password) {
    callback(new Error('两次密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度 3-20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    { validator: validateConfirm, trigger: 'blur' }
  ]
}

// 接力式预加载 - 注册页渲染后立即开始
const preloadComponents = () => {
  import('@/layout/MainLayout.vue')
    .then(() => import('@/views/ai/VideoTool.vue'))
    .then(() => import('@/views/ai/ImageTool.vue'))
    .then(() => import('@/views/ai/GeneralVideoTool.vue'))
    .then(() => import('@/views/service/ComingSoon.vue'))
    .then(() => import('@/views/shrimp/OpenClawDeploy.vue'))
    .catch(err => console.warn('预加载组件失败:', err))
}

onMounted(() => {
  preloadComponents()
})

const handleRegister = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      await request.post('/auth/register', {
        username: form.username,
        password: form.password
      })

      ElMessage.success('注册成功，请登录')
      router.push('/login')
    } catch (error) {
      console.error(error)
    } finally {
      loading.value = false
    }
  })
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%);
}

.register-card {
  width: 400px;
  padding: 40px;
  border-radius: 16px;
}

.register-card h1 {
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

.login-link {
  text-align: center;
  color: #888;
  font-size: 14px;
}

.login-link a {
  color: #00f260;
  text-decoration: none;
}
</style>