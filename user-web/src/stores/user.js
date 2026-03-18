import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import request from '@/api/request'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('user_token') || '')
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
  const login = async (loginToken) => {
    token.value = loginToken
    localStorage.setItem('user_token', loginToken)
    await fetchUserInfo()
  }

  // 登出
  const logout = () => {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('user_token')
  }

  // 刷新积分
  const refreshPoints = async () => {
    await fetchUserInfo()
  }

  return {
    token,
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