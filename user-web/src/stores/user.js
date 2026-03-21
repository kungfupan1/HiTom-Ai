import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/api/request'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('user_token') || '')
  const refreshToken = ref(localStorage.getItem('refresh_token') || '')
  const userInfo = ref(null)

  const isLoggedIn = computed(() => !!token.value)
  const points = computed(() => userInfo.value?.points || 0)
  const username = computed(() => userInfo.value?.username || '')

  // 初始化
  const init = async () => {
    if (token.value) {
      await fetchUserInfo()
    }
  }

  // 获取用户信息
  const fetchUserInfo = async () => {
    try {
      const res = await request.get('/users/me')
      userInfo.value = res
    } catch (error) {
      logout()
    }
  }

  // 登录
  const login = async (loginData) => {
    // 支持两种调用方式：旧版只传 token，新版传对象
    if (typeof loginData === 'string') {
      token.value = loginData
      localStorage.setItem('user_token', loginData)
    } else {
      token.value = loginData.access_token
      refreshToken.value = loginData.refresh_token
      localStorage.setItem('user_token', loginData.access_token)
      localStorage.setItem('refresh_token', loginData.refresh_token)
    }
    await fetchUserInfo()
  }

  // 登出
  const logout = () => {
    token.value = ''
    refreshToken.value = ''
    userInfo.value = null
    localStorage.removeItem('user_token')
    localStorage.removeItem('refresh_token')
  }

  // 刷新积分
  const refreshPoints = async () => {
    await fetchUserInfo()
  }

  return {
    token,
    refreshToken,
    userInfo,
    isLoggedIn,
    points,
    username,
    init,
    fetchUserInfo,
    login,
    logout,
    refreshPoints
  }
})