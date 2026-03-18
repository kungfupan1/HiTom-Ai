<template>
  <div class="main-layout">
    <el-container>
      <!-- 移动端遮罩 -->
      <div
        v-if="sidebarVisible"
        class="sidebar-overlay"
        @click="sidebarVisible = false"
      ></div>

      <!-- 侧边栏 -->
      <el-aside
        :width="sidebarVisible ? '220px' : '0px'"
        class="sidebar"
        :class="{ 'sidebar-collapsed': !sidebarVisible }"
      >
        <div class="logo">
          <h2>Hi-Tom-AI</h2>
          <span class="subtitle">管理后台</span>
        </div>
        <el-menu
          :default-active="activeMenu"
          router
          background-color="#1e1e2d"
          text-color="#b0b0b0"
          active-text-color="#00f260"
        >
          <el-menu-item index="/dashboard">
            <el-icon><DataLine /></el-icon>
            <span>控制台</span>
          </el-menu-item>
          <el-menu-item index="/models">
            <el-icon><Grid /></el-icon>
            <span>模型管理</span>
          </el-menu-item>
          <el-menu-item index="/config">
            <el-icon><Setting /></el-icon>
            <span>系统配置</span>
          </el-menu-item>
          <el-menu-item index="/users">
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </el-menu-item>
        </el-menu>
      </el-aside>

      <!-- 主内容区 -->
      <el-container>
        <el-header class="header">
          <div class="header-left">
            <el-button
              class="menu-toggle"
              @click="sidebarVisible = !sidebarVisible"
            >
              <el-icon><Expand v-if="!sidebarVisible" /><Fold v-else /></el-icon>
            </el-button>
            <span class="page-title">{{ pageTitle }}</span>
          </div>
          <div class="header-right">
            <span class="admin-name">{{ adminName }}</span>
            <el-button type="text" @click="logout" class="logout-btn">
              <el-icon><SwitchButton /></el-icon>
              <span class="logout-text">退出</span>
            </el-button>
          </div>
        </el-header>

        <el-main class="main-content">
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const sidebarVisible = ref(true)
const activeMenu = computed(() => route.path)
const pageTitle = computed(() => route.meta?.title || '管理后台')
const adminName = computed(() => localStorage.getItem('admin_name') || '管理员')

const logout = () => {
  localStorage.removeItem('admin_token')
  localStorage.removeItem('admin_name')
  router.push('/login')
}

// 响应式处理
const handleResize = () => {
  if (window.innerWidth < 992) {
    sidebarVisible.value = false
  } else {
    sidebarVisible.value = true
  }
}

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.main-layout {
  height: 100vh;
  overflow: hidden;
}

.el-container {
  height: 100%;
}

.sidebar {
  background-color: #1e1e2d;
  height: 100vh;
  overflow-y: auto;
  overflow-x: hidden;
  transition: width 0.3s ease;
  flex-shrink: 0;
}

.sidebar-collapsed {
  width: 0 !important;
}

.sidebar-overlay {
  display: none;
}

.logo {
  padding: 20px;
  text-align: center;
  border-bottom: 1px solid #2d2d3d;
  white-space: nowrap;
}

.logo h2 {
  color: #409eff;
  font-size: 18px;
  margin: 0;
}

.logo .subtitle {
  color: #888;
  font-size: 12px;
}

.el-menu {
  border-right: none;
}

.header {
  background: #fff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 56px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.menu-toggle {
  display: none;
  border: none;
  background: transparent;
  padding: 8px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.admin-name {
  color: #666;
}

.logout-btn {
  color: #f56c6c;
}

.main-content {
  background: #f5f7fa;
  padding: 24px;
  overflow-y: auto;
  overflow-x: hidden;
}

/* 平板和移动端响应式 */
@media (max-width: 992px) {
  .menu-toggle {
    display: block;
  }

  .sidebar {
    position: fixed;
    left: 0;
    top: 0;
    z-index: 1000;
    box-shadow: 2px 0 8px rgba(0,0,0,0.15);
  }

  .sidebar-collapsed {
    left: -220px;
  }

  .sidebar-overlay {
    display: block;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.3);
    z-index: 999;
  }

  .header {
    padding: 0 16px;
  }

  .page-title {
    font-size: 16px;
  }

  .main-content {
    padding: 16px;
  }
}

@media (max-width: 576px) {
  .admin-name {
    display: none;
  }

  .logout-text {
    display: none;
  }

  .page-title {
    font-size: 15px;
  }

  .main-content {
    padding: 12px;
  }
}
</style>