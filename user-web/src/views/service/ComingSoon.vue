<template>
  <div class="coming-soon">
    <div class="content">
      <el-icon :size="80" color="#00f260"><VideoCamera /></el-icon>
      <h2>普通视频生成</h2>
      <p class="desc">开发中，敬请期待...</p>
      <el-button type="primary" disabled>即将上线</el-button>
    </div>
  </div>
</template>

<script setup>
import { VideoCamera } from '@element-plus/icons-vue'
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