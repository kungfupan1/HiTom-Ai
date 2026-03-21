import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

// 创建 axios 实例
const request = axios.create({
  baseURL: '',
  timeout: 60000
})

// 是否正在刷新令牌
let isRefreshing = false
// 等待令牌刷新的请求队列
let refreshSubscribers = []

// 添加订阅者（等待令牌刷新后重试）
function subscribeTokenRefresh(callback) {
  refreshSubscribers.push(callback)
}

// 通知所有订阅者
function onRefreshed(token) {
  refreshSubscribers.forEach(callback => callback(token))
  refreshSubscribers = []
}

// 刷新令牌失败
function onRefreshFailed() {
  refreshSubscribers = []
  localStorage.removeItem('user_token')
  localStorage.removeItem('refresh_token')
  router.push('/login')
  ElMessage.error('登录已过期，请重新登录')
}

// 刷新令牌
async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) {
    return null
  }

  try {
    const response = await axios.post('/auth/refresh', {
      refresh_token: refreshToken
    })
    const { access_token, refresh_token } = response.data
    localStorage.setItem('user_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    return access_token
  } catch (error) {
    return null
  }
}

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
  async error => {
    const status = error.response?.status
    const message = error.response?.data?.detail || error.response?.data?.message || '请求失败'

    if (status === 401) {
      // 尝试刷新令牌
      if (!isRefreshing) {
        isRefreshing = true
        const newToken = await refreshAccessToken()

        if (newToken) {
          isRefreshing = false
          // 通知等待的请求重试
          onRefreshed(newToken)
          // 重试当前请求
          error.config.headers.Authorization = `Bearer ${newToken}`
          return request(error.config)
        } else {
          isRefreshing = false
          onRefreshFailed()
          return Promise.reject(error)
        }
      } else {
        // 正在刷新，将请求加入队列等待
        return new Promise(resolve => {
          subscribeTokenRefresh(token => {
            error.config.headers.Authorization = `Bearer ${token}`
            resolve(request(error.config))
          })
        })
      }
    } else {
      ElMessage.error(message)
    }

    return Promise.reject(error)
  }
)

export default request