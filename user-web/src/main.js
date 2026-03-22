import { createApp } from 'vue'
import { createPinia } from 'pinia'
// Element Plus 样式
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'
import { useUserStore } from './stores/user'
import { registerIcons } from './plugins/icons'

const app = createApp(App)

// 注册常用图标
registerIcons(app)

app.use(createPinia())
app.use(router)

// 初始化用户状态
const userStore = useUserStore()
userStore.init()

app.mount('#app')

// 隐藏首屏加载提示
const loadingEl = document.getElementById('app-loading')
if (loadingEl) {
  loadingEl.classList.add('fade-out')
  setTimeout(() => loadingEl.remove(), 300)
}