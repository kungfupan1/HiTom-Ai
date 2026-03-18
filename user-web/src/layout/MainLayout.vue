<template>
  <div class="main-layout">
    <el-container>
      <!-- 侧边栏 -->
      <el-aside :width="isCollapse ? '64px' : '220px'" class="sidebar">
        <div class="logo">
          <span v-if="!isCollapse">🤖 Hi-Tom-AI</span>
          <span v-else>🤖</span>
        </div>

        <el-menu
          :default-active="activeMenu"
          router
          background-color="transparent"
          text-color="#b0b0b0"
          active-text-color="#00f260"
          :collapse="isCollapse"
        >
          <el-menu-item index="/ai/video">
            <el-icon><VideoCamera /></el-icon>
            <template #title>视频生成</template>
          </el-menu-item>
          <el-menu-item index="/ai/image">
            <el-icon><Picture /></el-icon>
            <template #title>图片生成</template>
          </el-menu-item>
        </el-menu>

        <div class="collapse-btn" @click="isCollapse = !isCollapse">
          <el-icon>
            <Expand v-if="isCollapse" />
            <Fold v-else />
          </el-icon>
        </div>
      </el-aside>

      <!-- 主内容区 -->
      <el-container>
        <el-header class="header">
          <div class="header-left">
            <span class="page-title">{{ pageTitle }}</span>
          </div>
          <div class="header-right">
            <div class="points-display">
              <el-icon><Coin /></el-icon>
              <span>{{ userStore.points }} 积分</span>
            </div>
            <el-dropdown @command="handleCommand">
              <span class="user-info">
                {{ userStore.username }}
                <el-icon><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="logout">退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>

        <el-main class="main-content">
          <router-view @refresh-points="refreshPoints" />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapse = ref(false)
const activeMenu = computed(() => route.path)
const pageTitle = computed(() => route.meta?.title || 'Hi-Tom-AI')

const refreshPoints = () => {
  userStore.refreshPoints()
}

const handleCommand = (command) => {
  if (command === 'logout') {
    userStore.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.main-layout {
  min-height: 100vh;
  background: linear-gradient(135deg, #0a0a0f 0%, #1a1a2e 100%);
}

.el-container {
  min-height: 100vh;
}

.sidebar {
  background: rgba(0, 0, 0, 0.3);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  transition: width 0.3s;
  position: relative;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.el-menu {
  border-right: none;
}

.collapse-btn {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  cursor: pointer;
  color: #888;
  transition: color 0.3s;
}

.collapse-btn:hover {
  color: #00f260;
}

.header {
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 24px;
}

.points-display {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #00f260;
  font-weight: bold;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #fff;
  cursor: pointer;
}

.main-content {
  padding: 24px;
}
</style>