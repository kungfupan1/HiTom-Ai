<template>
  <div class="main-layout">
    <el-container class="layout-container">
      <!-- 侧边栏 -->
      <el-aside :width="isCollapse ? '64px' : '220px'" class="sidebar dark-glass">
        <div class="logo">
          <span v-if="!isCollapse" class="gradient-text">✨ HiTom-AI</span>
          <span v-else class="gradient-text">✨</span>
        </div>

        <el-menu
          :default-active="activeMenu"
          router
          background-color="transparent"
          text-color="#b0b0b0"
          active-text-color="#00f260"
          :collapse="isCollapse"
          class="glass-menu"
        >
          <el-sub-menu index="ai">
            <template #title>
              <el-icon class="gradient-icon"><MagicStick /></el-icon>
              <span v-show="!isCollapse">商品图/视频</span>
            </template>
            <el-menu-item index="/ai/image">🎨 商品图生成</el-menu-item>
            <el-menu-item index="/ai/image/manual">✏️ 手动图片生成</el-menu-item>
            <el-menu-item index="/ai/video">🎬 带货视频生成</el-menu-item>
            <el-menu-item index="/ai/video/general">✨ 手动视频生成</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="shrimp" v-if="hasEnabledShrimpItems">
            <template #title>
              <el-icon class="gradient-icon"><Cpu /></el-icon>
              <span v-show="!isCollapse">云端养虾</span>
            </template>
            <el-menu-item v-if="contentConfigs.shrimp_openclaw" index="/shrimp/openclaw">🦐 OpenClaw部署</el-menu-item>
            <el-menu-item v-if="contentConfigs.shrimp_skills" index="/shrimp/skills">🛒 Skills市场</el-menu-item>
            <el-menu-item v-if="contentConfigs.shrimp_ai_staff" index="/shrimp/ai-staff">🤖 AI员工打造</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="service" v-if="hasEnabledServiceItems">
            <template #title>
              <el-icon class="gradient-icon"><Shop /></el-icon>
              <span v-show="!isCollapse">跨境服务资源</span>
            </template>
            <el-menu-item v-if="contentConfigs.service_shop" index="/service/shop">🏪 店铺买卖/租赁</el-menu-item>
            <el-menu-item v-if="contentConfigs.service_course" index="/service/course">📚 课程+陪跑</el-menu-item>
            <el-menu-item v-if="contentConfigs.service_logistics" index="/service/logistics">📦 货代/小包/海外仓</el-menu-item>
            <el-menu-item v-if="contentConfigs.service_software" index="/service/software">💻 增强软件</el-menu-item>
            <el-menu-item v-if="contentConfigs.service_network" index="/service/network">🌐 网络&硬件服务</el-menu-item>
            <el-menu-item v-if="contentConfigs.service_other" index="/service/other">🤝 其他合作</el-menu-item>
          </el-sub-menu>
        </el-menu>

        <div class="collapse-btn" @click="isCollapse = !isCollapse">
          <el-icon>
            <Expand v-if="isCollapse" />
            <Fold v-else />
          </el-icon>
        </div>
      </el-aside>

      <!-- 主内容区 -->
      <el-container class="right-container">
        <el-header class="header dark-glass-light">
          <div class="header-left">
            <span class="page-title">{{ pageTitle }}</span>
          </div>
          <div class="header-right">
            <el-button
              type="primary"
              link
              @click="showLogs = !showLogs"
              style="margin-right: 15px; color: #a0aec0;"
            >
              <el-icon style="margin-right:4px"><Document /></el-icon>
              {{ showLogs ? '隐藏日志' : '显示日志' }}
            </el-button>

            <div class="points-display">
              <el-icon><Coin /></el-icon>
              <span>{{ userStore.points }} 积分</span>
            </div>
            <el-dropdown @command="handleCommand">
              <span class="user-info">
                <div class="avatar-circle">{{ userStore.username?.charAt(0)?.toUpperCase() || 'U' }}</div>
                <span class="username-text">{{ userStore.username }}</span>
                <el-icon><ArrowDown /></el-icon>
              </span>
              <template #dropdown>
                <el-dropdown-menu class="dark-dropdown">
                  <el-dropdown-item command="changePassword">🔑 修改密码</el-dropdown-item>
                  <el-dropdown-item command="logout">🚪 退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </el-header>

        <el-container style="overflow: hidden; position: relative;">
          <el-main class="main-content">
            <router-view @refresh-points="refreshPoints" @log="handleLog" />
          </el-main>

          <!-- 右侧日志栏 -->
          <transition name="slide-fade">
            <el-aside v-show="showLogs" width="320px" class="right-log-aside cyber-panel">
              <div class="log-header">
                <span>📝 SYSTEM MONITOR</span>
                <el-button link type="primary" size="small" @click="logs=[]">CLEAR</el-button>
              </div>
              <div class="log-container" ref="logContainer">
                <div v-if="logs.length === 0" class="empty-log">
                  <el-icon size="40" color="#333"><Loading /></el-icon>
                  <p>SYSTEM READY...</p>
                </div>
                <div v-for="(log, index) in logs" :key="index" class="log-item">
                  <span class="log-time">[{{ log.time }}]</span>
                  <span class="log-content">{{ log.msg }}</span>
                </div>
              </div>
            </el-aside>
          </transition>
        </el-container>
      </el-container>
    </el-container>

    <!-- 修改密码对话框 -->
    <el-dialog
      v-model="changePasswordVisible"
      title="修改密码"
      width="400px"
      class="dark-dialog"
      :close-on-click-modal="false"
    >
      <el-form :model="passwordForm" label-width="80px" :rules="passwordRules" ref="passwordFormRef">
        <el-form-item label="旧密码" prop="oldPassword">
          <el-input
            v-model="passwordForm.oldPassword"
            type="password"
            placeholder="请输入旧密码"
            show-password
            class="cyber-input"
          />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="passwordForm.newPassword"
            type="password"
            placeholder="请输入新密码（至少6位）"
            show-password
            class="cyber-input"
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
            show-password
            class="cyber-input"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="changePasswordVisible = false">取消</el-button>
        <el-button type="primary" @click="submitChangePassword" :loading="passwordLoading">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, onMounted, onUnmounted, reactive } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { Document, Loading, MagicStick, Shop, Cpu } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const isCollapse = ref(false)
const showLogs = ref(true)
const logs = ref([])
const logContainer = ref(null)

// 内容配置（动态菜单）
const contentConfigs = reactive({
  shrimp_openclaw: true,
  shrimp_skills: true,
  shrimp_ai_staff: true,
  service_shop: true,
  service_course: true,
  service_logistics: true,
  service_software: true,
  service_network: true,
  service_other: true
})

// 计算是否有启用的子菜单项
const hasEnabledShrimpItems = computed(() =>
  contentConfigs.shrimp_openclaw || contentConfigs.shrimp_skills || contentConfigs.shrimp_ai_staff
)
const hasEnabledServiceItems = computed(() =>
  contentConfigs.service_shop || contentConfigs.service_course || contentConfigs.service_logistics ||
  contentConfigs.service_software || contentConfigs.service_network || contentConfigs.service_other
)

// 加载内容配置
const loadContentConfigs = async () => {
  try {
    const res = await request.get('/api/content-configs-enabled')
    if (res && res.configs) {
      Object.keys(res.configs).forEach(key => {
        if (key in contentConfigs) {
          contentConfigs[key] = res.configs[key]
        }
      })
      // 保存到 localStorage 供路由守卫使用
      localStorage.setItem('contentConfigs', JSON.stringify(res.configs))
    }
  } catch (e) {
    // 加载失败，使用默认值（全部显示）
    console.warn('加载内容配置失败，使用默认配置')
  }
}

// 修改密码相关
const changePasswordVisible = ref(false)
const passwordLoading = ref(false)
const passwordFormRef = ref(null)
const passwordForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

// 用于追踪是否是自动收起（用户手动收起时不应该自动展开）
const autoCollapsedLog = ref(false)
const autoCollapsedSidebar = ref(false)

// 响应式断点
const LOG_COLLAPSE_WIDTH = 1400  // 收起日志栏
const SIDEBAR_COLLAPSE_WIDTH = 800  // 收起侧边栏
const MIN_WIDTH = 600  // 最小宽度

const handleResize = () => {
  const width = window.innerWidth

  // 自动收起/展开日志栏
  if (width < LOG_COLLAPSE_WIDTH && !autoCollapsedLog.value && showLogs.value) {
    showLogs.value = false
    autoCollapsedLog.value = true
  } else if (width >= LOG_COLLAPSE_WIDTH && autoCollapsedLog.value) {
    showLogs.value = true
    autoCollapsedLog.value = false
  }

  // 自动收起/展开侧边栏
  if (width < SIDEBAR_COLLAPSE_WIDTH && !autoCollapsedSidebar.value && !isCollapse.value) {
    isCollapse.value = true
    autoCollapsedSidebar.value = true
  } else if (width >= SIDEBAR_COLLAPSE_WIDTH && autoCollapsedSidebar.value) {
    isCollapse.value = false
    autoCollapsedSidebar.value = false
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  // 初始检查
  handleResize()
  // 加载内容配置
  loadContentConfigs()
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})

const activeMenu = computed(() => route.path)
const pageTitle = computed(() => route.meta?.title || 'HiTom-AI')

const refreshPoints = () => {
  userStore.refreshPoints()
}

const handleLog = (msg) => {
  const time = new Date().toLocaleTimeString('en-US', { hour12: false })
  logs.value.push({ time, msg })
  if (logs.value.length > 200) logs.value.shift()
  nextTick(() => {
    if (logContainer.value) logContainer.value.scrollTop = logContainer.value.scrollHeight
  })
}

const handleCommand = (command) => {
  if (command === 'logout') {
    userStore.logout()
    router.push('/login')
  } else if (command === 'changePassword') {
    changePasswordVisible.value = true
    // 重置表单
    passwordForm.oldPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
  }
}

const submitChangePassword = async () => {
  if (!passwordFormRef.value) return

  try {
    await passwordFormRef.value.validate()
  } catch {
    return
  }

  passwordLoading.value = true
  try {
    await request.post('/auth/change-password', {
      old_password: passwordForm.oldPassword,
      new_password: passwordForm.newPassword
    })
    ElMessage.success('密码修改成功')
    changePasswordVisible.value = false
  } catch (e) {
    const msg = e.response?.data?.detail || '密码修改失败'
    ElMessage.error(msg)
  } finally {
    passwordLoading.value = false
  }
}
</script>

<style scoped>
/* ================= 全局暗黑背景 ================= */
.main-layout {
  min-width: 600px;
  max-width: 1920px;
  margin: 0 auto;
}

.layout-container {
  height: 100vh;
  display: flex;
  /* 深渊暗色渐变动画背景 */
  background: linear-gradient(135deg, #df52ad 0%, #0f0c29 15%, #302b63 30%, #24243e 50%, #302b63 75%, #df52ad 100%);
  background-size: 200% 200%;
  animation: bgAnimation 20s ease infinite;
  color: #e2e8f0;
}

@keyframes bgAnimation {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

/* ================= 1. 左侧侧边栏 (黑曜石玻璃) ================= */
.sidebar {
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  transition: width 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
  position: relative;
  display: flex;
  flex-direction: column;
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.6);
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.gradient-text {
  font-size: 20px;
  font-weight: 900;
  background: linear-gradient(90deg, #00f260, #0575e6);
  -webkit-background-clip: text;
  color: transparent;
  text-shadow: 0 0 10px rgba(5, 117, 230, 0.3);
  letter-spacing: 1px;
}

.el-menu {
  border-right: none;
  flex: 1;
}

.glass-menu {
  background: transparent !important;
  border-right: none !important;
  padding: 10px;
}

/* 覆盖 Element Plus 菜单样式 */

/* 大类（子菜单标题）样式 */
:deep(.el-sub-menu__title) {
  border-radius: 8px;
  margin-bottom: 5px;
  color: #fff !important;  /* 大类颜色更亮 */
  font-weight: 700;        /* 大类加粗 */
  font-size: 16px;         /* 大类字体更大 */
  transition: all 0.3s;
}

:deep(.el-sub-menu__title:hover) {
  background-color: rgba(255, 255, 255, 0.12) !important;
  color: #fff !important;
}

/* 大类图标 */
:deep(.el-sub-menu__title .el-icon) {
  color: #00f260;  /* 大类图标用亮绿色 */
}

/* 小类（菜单项）样式 */
:deep(.el-menu-item) {
  border-radius: 8px;
  margin-bottom: 5px;
  color: #a0aec0 !important;  /* 小类颜色稍淡 */
  font-weight: 500;            /* 小类不加粗 */
  font-size: 14px;             /* 小类字体稍小 */
  transition: all 0.3s;
  padding-left: 50px !important;
  min-width: auto;
}

:deep(.el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.08) !important;
  color: #fff !important;
}

/* 激活状态：电光紫高亮 */
:deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, #7f00ff 0%, #e100ff 100%) !important;
  color: white !important;
  box-shadow: 0 0 15px rgba(127, 0, 255, 0.5);
  border: 1px solid rgba(255,255,255,0.2);
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

/* ================= 2. 顶部 Header (深空悬浮) ================= */
.header {
  background: rgba(20, 20, 30, 0.7);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 60px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

.page-title {
  font-size: 18px;
  font-weight: 700;
  color: #e2e8f0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.points-display {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(0,0,0,0.3);
  border: 1px solid #ffd700;
  padding: 4px 12px;
  border-radius: 20px;
  color: #ffd700;
  font-size: 13px;
  font-weight: bold;
  box-shadow: 0 0 8px rgba(255, 215, 0, 0.2);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #e2e8f0;
  cursor: pointer;
  padding: 5px 10px;
  border-radius: 20px;
  transition: background 0.3s;
}

.user-info:hover {
  background: rgba(255,255,255,0.1);
}

.avatar-circle {
  width: 32px;
  height: 32px;
  background: #2d3748;
  border: 1px solid #718096;
  color: #fff;
  border-radius: 50%;
  text-align: center;
  line-height: 32px;
  font-weight: bold;
  font-size: 14px;
}

.username-text {
  font-weight: 600;
  color: #e2e8f0;
}

/* ================= 3. 内容区 ================= */
.main-content {
  padding: 24px;
  overflow-y: auto;
  background: transparent;
}

/* ================= 4. 右侧日志栏 (赛博终端) ================= */
.right-log-aside {
  z-index: 20;
  background: #000;
  border-left: 1px solid #333;
  display: flex;
  flex-direction: column;
  box-shadow: -4px 0 24px rgba(0,0,0,0.5);
  font-family: 'Courier New', Courier, monospace;
}

.log-header {
  height: 50px;
  background: #111;
  color: #0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 15px;
  font-size: 14px;
  font-weight: bold;
  border-bottom: 1px solid #333;
  letter-spacing: 1px;
}

.log-container {
  flex: 1;
  padding: 15px;
  overflow-y: auto;
  font-size: 12px;
  /* CRT扫描线效果 */
  background-image: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
  background-size: 100% 2px, 3px 100%;
}

.log-item {
  margin-bottom: 8px;
  line-height: 1.4;
  border-bottom: 1px dashed #222;
  padding-bottom: 4px;
}

.log-time {
  color: #555;
  margin-right: 10px;
}

.log-content {
  color: #0f0;
  text-shadow: 0 0 2px #0f0;
}

.empty-log {
  margin-top: 50px;
  text-align: center;
  color: #333;
}

/* 滚动条深色化 */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-thumb { background: #444; border-radius: 3px; }
::-webkit-scrollbar-track { background: #111; }

/* 动画效果 */
.slide-fade-enter-active, .slide-fade-leave-active { transition: all 0.3s ease; }
.slide-fade-enter-from, .slide-fade-leave-to { transform: translateX(20px); opacity: 0; }

/* 响应式 */
@media screen and (max-width: 1100px) {
  /* 自动收起日志栏 */
  .right-log-aside {
    display: none !important;
  }
}

@media screen and (max-width: 800px) {
  /* 自动收起侧边栏 */
  .sidebar {
    width: 64px !important;
  }
  .collapse-btn {
    display: none;
  }
}
</style>

<style>
/* 下拉菜单暗色主题 */
.dark-dropdown {
  background: rgba(0, 0, 0, 0.9) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
}
.dark-dropdown .el-dropdown-menu__item {
  color: #a0aec0 !important;
}
.dark-dropdown .el-dropdown-menu__item:hover {
  background: rgba(255, 255, 255, 0.1) !important;
  color: #fff !important;
}

/* 暗色对话框 */
.dark-dialog .el-dialog {
  background: rgba(20, 20, 30, 0.95) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 12px !important;
}
.dark-dialog .el-dialog__header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
.dark-dialog .el-dialog__title {
  color: #e2e8f0 !important;
}
.dark-dialog .el-form-item__label {
  color: #a0aec0 !important;
}
.dark-dialog .el-input__wrapper {
  background: rgba(0, 0, 0, 0.3) !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  box-shadow: none !important;
}
.dark-dialog .el-input__inner {
  color: #fff !important;
}
</style>