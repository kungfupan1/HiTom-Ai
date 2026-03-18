<template>
  <div class="login-page">
    <div class="login-card">
      <h1>🤖 Hi-Tom-AI</h1>
      <p class="subtitle">管理后台登录</p>

      <el-form :model="form" :rules="rules" ref="formRef" @submit.prevent="handleLogin">
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="用户名"
            prefix-icon="User"
            size="large"
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
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            @click="handleLogin"
            style="width: 100%"
          >
            登 录
          </el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const router = useRouter()
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

      // 先存储 token，这样后续请求才能携带认证头
      localStorage.setItem('admin_token', res.access_token)

      // 再检查是否是管理员
      const userRes = await request.get('/users/me')

      if (userRes.role !== 'admin') {
        // 不是管理员，清除 token
        localStorage.removeItem('admin_token')
        ElMessage.error('您不是管理员，无法登录后台')
        return
      }

      localStorage.setItem('admin_name', userRes.username)

      ElMessage.success('登录成功')
      router.push('/dashboard')
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
  background: linear-gradient(135deg, #1e1e2d 0%, #2d2d3d 100%);
}

.login-card {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
}

.login-card h1 {
  text-align: center;
  margin-bottom: 8px;
  font-size: 28px;
}

.subtitle {
  text-align: center;
  color: #888;
  margin-bottom: 30px;
}
</style>