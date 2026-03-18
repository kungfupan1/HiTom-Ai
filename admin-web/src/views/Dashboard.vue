<template>
  <div class="dashboard">
    <el-row :gutter="20">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
            <el-icon><User /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.userCount }}</div>
            <div class="stat-label">注册用户</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <el-icon><Grid /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.modelCount }}</div>
            <div class="stat-label">可用模型</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
            <el-icon><VideoCamera /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.videoCount }}</div>
            <div class="stat-label">视频生成次数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
            <el-icon><Picture /></el-icon>
          </div>
          <div class="stat-info">
            <div class="stat-value">{{ stats.imageCount }}</div>
            <div class="stat-label">图片生成次数</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :xs="24" :lg="12">
        <el-card>
          <template #header>
            <span>快速操作</span>
          </template>
          <div class="quick-actions">
            <el-button type="primary" @click="$router.push('/models')">
              <el-icon><Plus /></el-icon>
              添加模型
            </el-button>
            <el-button @click="$router.push('/config')">
              <el-icon><Setting /></el-icon>
              系统配置
            </el-button>
            <el-button @click="$router.push('/users')">
              <el-icon><User /></el-icon>
              用户管理
            </el-button>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :lg="12">
        <el-card>
          <template #header>
            <span>系统信息</span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="系统版本">1.0.0</el-descriptions-item>
            <el-descriptions-item label="后端状态">
              <el-tag type="success" v-if="backendStatus">正常</el-tag>
              <el-tag type="danger" v-else>离线</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="Vercel Functions">已配置</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import request from '@/api/request'

const stats = reactive({
  userCount: 0,
  modelCount: 0,
  videoCount: 0,
  imageCount: 0
})

const backendStatus = ref(false)

onMounted(async () => {
  try {
    await request.get('/health')
    backendStatus.value = true
  } catch {
    backendStatus.value = false
  }

  // 加载统计数据
  try {
    const res = await request.get('/admin/stats')
    stats.userCount = res.userCount || 0
    stats.modelCount = res.modelCount || 0
    stats.videoCount = res.videoCount || 0
    stats.imageCount = res.imageCount || 0
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
})
</script>

<style scoped>
.stat-card {
  display: flex;
  align-items: center;
  padding: 20px;
  margin-bottom: 20px;
}

.stat-card :deep(.el-card__body) {
  display: flex;
  width: 100%;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  flex-shrink: 0;
}

.stat-icon .el-icon {
  font-size: 28px;
  color: #fff;
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-label {
  color: #888;
  font-size: 14px;
  margin-top: 4px;
}

.quick-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* 响应式 */
@media (max-width: 768px) {
  .stat-card {
    padding: 16px;
  }

  .stat-icon {
    width: 50px;
    height: 50px;
  }

  .stat-icon .el-icon {
    font-size: 24px;
  }

  .stat-value {
    font-size: 24px;
  }

  .quick-actions {
    flex-direction: column;
  }

  .quick-actions .el-button {
    width: 100%;
    justify-content: center;
  }
}
</style>