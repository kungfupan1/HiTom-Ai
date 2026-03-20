<template>
  <div class="coming-soon">
    <div class="content">
      <div class="icon-wrapper">
        <el-icon :size="60" color="#00f260"><Loading /></el-icon>
      </div>
      <h2>{{ pageTitle }}</h2>
      <div class="divider"></div>
      <div class="coming-soon-text">
        <span class="text-gradient">✨ 开发中</span>
        <span class="dots">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </span>
        <span class="text-gradient">敬请期待</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Loading } from '@element-plus/icons-vue'

const route = useRoute()

// 根据路由动态显示标题
const pageTitle = computed(() => {
  return route.meta?.title || '功能开发中'
})
</script>

<style scoped>
.coming-soon {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.content {
  text-align: center;
  padding: 40px;
}

.icon-wrapper {
  margin-bottom: 20px;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.1); opacity: 0.8; }
}

h2 {
  color: #e2e8f0;
  margin: 0 0 20px;
  font-size: 28px;
  font-weight: 700;
}

.divider {
  width: 80px;
  height: 2px;
  background: linear-gradient(90deg, #00f260, #0575e6);
  margin: 0 auto 30px;
  border-radius: 2px;
}

.coming-soon-text {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.text-gradient {
  font-size: 18px;
  font-weight: 600;
  background: linear-gradient(90deg, #00f260, #0575e6);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.dots {
  display: flex;
  gap: 4px;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #00f260;
  animation: bounce 1.4s ease-in-out infinite;
}

.dot:nth-child(1) { animation-delay: 0s; }
.dot:nth-child(2) { animation-delay: 0.2s; }
.dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-8px); }
}
</style>