<template>
  <div class="openclaw-page">
    <div class="page-header">
      <h2>🦐 OpenClaw 部署服务</h2>
      <p class="subtitle">专业的 AI 智能体部署解决方案</p>
    </div>

    <div class="cards-container">
      <div
        v-for="card in cards"
        :key="card.id"
        class="service-card"
        @click="showContactModal(card)"
      >
        <div class="card-icon">{{ card.icon }}</div>
        <div class="card-content">
          <h3>{{ card.title }}</h3>
          <p class="description">{{ card.description }}</p>
          <div class="tags">
            <span v-for="tag in card.tags" :key="tag" class="tag">{{ tag }}</span>
          </div>
          <div class="price">
            <span class="price-label">价格：</span>
            <span class="price-value">{{ card.price }}</span>
          </div>
        </div>
        <div class="card-action">
          <el-button type="primary" round>联系部署</el-button>
        </div>
      </div>
    </div>

    <!-- 联系方式弹窗 -->
    <el-dialog
      v-model="contactDialogVisible"
      :title="currentCard?.title"
      width="400px"
      class="contact-dialog"
      :show-close="true"
    >
      <div class="contact-content">
        <div class="contact-icon">{{ currentCard?.icon }}</div>
        <h3>{{ currentCard?.title }}</h3>
        <p class="contact-desc">{{ currentCard?.description }}</p>
        <div class="contact-method">
          <div class="contact-label">付费安装请联系微信</div>
          <div class="contact-wechat">
            <el-icon size="20"><ChatDotRound /></el-icon>
            <span class="wechat-id">{{ modalContent }}</span>
            <el-button type="primary" size="small" @click="copyWechat">复制</el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { ChatDotRound } from '@element-plus/icons-vue'
import request from '../../api/request'

// 硬编码默认数据
const defaultCards = [
  {
    id: 1,
    title: 'OpenClaw',
    icon: '🦐',
    description: '开源版 AI 智能体框架，支持多模型接入，适合技术团队二次开发',
    price: '¥499起',
    tags: ['开源', '可定制']
  },
  {
    id: 2,
    title: 'QClaw',
    icon: '🎯',
    description: '企业级 AI 智能体，集成主流大模型，开箱即用',
    price: '¥599起',
    tags: ['企业版', '技术支持']
  },
  {
    id: 3,
    title: 'AutoClaw',
    icon: '⚡',
    description: '自动化 AI 工作流引擎，支持任务编排和定时执行',
    price: '¥399起',
    tags: ['自动化', '工作流']
  },
  {
    id: 4,
    title: 'OneClaw',
    icon: '🔹',
    description: '轻量级单功能智能体，快速部署单一任务场景',
    price: '¥99起',
    tags: ['轻量', '快速部署']
  },
  {
    id: 5,
    title: 'JVS Claw',
    icon: '🔗',
    description: '多平台集成版，支持企业微信、钉钉、飞书等主流平台',
    price: '¥799起',
    tags: ['多平台', '企业集成']
  },
  {
    id: 6,
    title: 'Kimi Claw',
    icon: '🌙',
    description: '基于月之暗面 Kimi 模型的智能体，擅长长文本理解和生成',
    price: '¥299起',
    tags: ['Kimi', '长文本']
  }
]

const cards = ref(defaultCards)
const contactDialogVisible = ref(false)
const currentCard = ref(null)
const modalContent = ref('waterborn911') // 默认微信号

const loadConfig = async () => {
  try {
    const res = await request.get('/api/content-config/shrimp_openclaw')
    if (res?.config?.modal_content) {
      modalContent.value = res.config.modal_content
    }
  } catch (e) {
    // 接口失败，使用默认值
  }
}

const showContactModal = (card) => {
  currentCard.value = card
  contactDialogVisible.value = true
}

const copyWechat = () => {
  navigator.clipboard.writeText(modalContent.value)
  ElMessage.success('已复制')
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.openclaw-page {
  padding: 0;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
}

.page-header h2 {
  font-size: 28px;
  color: #e2e8f0;
  margin: 0 0 10px;
}

.subtitle {
  color: #a0aec0;
  font-size: 16px;
  margin: 0;
}

.cards-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.service-card {
  display: flex;
  align-items: center;
  padding: 24px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.service-card:hover {
  background: rgba(0, 0, 0, 0.5);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateX(5px);
}

.card-icon {
  font-size: 48px;
  margin-right: 24px;
  flex-shrink: 0;
}

.card-content {
  flex: 1;
}

.card-content h3 {
  font-size: 20px;
  color: #fff;
  margin: 0 0 8px;
}

.description {
  color: #a0aec0;
  font-size: 14px;
  margin: 0 0 12px;
  line-height: 1.6;
}

.tags {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.tag {
  background: rgba(127, 0, 255, 0.2);
  border: 1px solid rgba(127, 0, 255, 0.5);
  color: #c792ea;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
}

.price {
  margin-top: 8px;
}

.price-label {
  color: #a0aec0;
  font-size: 14px;
}

.price-value {
  color: #ffd700;
  font-size: 16px;
  font-weight: bold;
}

.card-action {
  margin-left: 20px;
}

/* 弹窗样式 */
.contact-content {
  text-align: center;
  padding: 20px 0;
}

.contact-icon {
  font-size: 60px;
  margin-bottom: 15px;
}

.contact-content h3 {
  font-size: 24px;
  color: #333;
  margin: 0 0 15px;
}

.contact-desc {
  color: #666;
  font-size: 14px;
  margin: 0 0 25px;
  line-height: 1.6;
}

.contact-method {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 20px;
}

.contact-label {
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  margin-bottom: 10px;
}

.contact-wechat {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #fff;
}

.wechat-id {
  font-size: 18px;
  font-weight: bold;
  letter-spacing: 1px;
}

/* 响应式 */
@media (max-width: 768px) {
  .service-card {
    flex-direction: column;
    text-align: center;
  }

  .card-icon {
    margin-right: 0;
    margin-bottom: 15px;
  }

  .card-action {
    margin-left: 0;
    margin-top: 15px;
  }

  .tags {
    justify-content: center;
  }
}
</style>

<style>
/* 全局弹窗样式 */
.contact-dialog {
  backdrop-filter: blur(10px);
}

.contact-dialog .el-dialog {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.contact-dialog .el-dialog__header {
  padding: 20px 20px 0;
  border-bottom: none;
}

.contact-dialog .el-dialog__title {
  font-size: 20px;
  font-weight: bold;
  color: #333;
}

.contact-dialog .el-dialog__body {
  padding: 10px 20px 20px;
}
</style>