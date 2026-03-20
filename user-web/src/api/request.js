import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 创建 axios 实例
const request = axios.create({
  baseURL: '',
  timeout: 60000
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('user_token')
    if (token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    const status = error.response?.status
    const message = error.response?.data?.detail || error.response?.data?.message || '请求失败'

    if (status === 401) {
      localStorage.removeItem('user_token')
      router.push('/login')
      ElMessage.error('登录已过期，请重新登录')
    } else {
      ElMessage.error(message)
    }

    return Promise.reject(error)
  }
)

export default request