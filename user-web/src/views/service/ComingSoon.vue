<template>
  <div class="coming-soon">
    <div class="content">
      <el-icon :size="80" color="#00f260"><Loading /></el-icon>
      <h2>{{ pageTitle }}</h2>
      <p class="desc">开发中，敬请期待...</p>
      <el-button type="primary" disabled>即将上线</el-button>
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
h2 {
  color: #e2e8f0;
  margin: 20px 0 10px;
  font-size: 24px;
}
.desc {
  color: #a0aec0;
  margin-bottom: 20px;
}
</style>