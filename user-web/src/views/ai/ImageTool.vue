<template>
  <div class="image-tool">
    <div class="cyber-container">
      <el-tabs v-model="activeTab" type="border-card" class="cyber-tabs">

        <el-tab-pane label="单任务生成" name="single">
          <el-row :gutter="24">
            <el-col :xs="24" :sm="24" :md="10" :lg="10">
              <el-form label-position="top">
                <!-- 动态模型选择 -->
                <el-form-item label="选择模型">
                  <el-select v-model="form.model" style="width: 100%" class="cyber-select" popper-class="cyber-popper" @change="onModelChange">
                    <el-option
                      v-for="model in models"
                      :key="model.model_id"
                      :label="model.display_name"
                      :value="model.model_id"
                    />
                  </el-select>
                </el-form-item>

                <el-form-item label="提示词 (必填)">
                  <el-input
                    v-model="form.prompt"
                    type="textarea"
                    :rows="6"
                    placeholder="描述你想生成的图片内容..."
                    class="cyber-input"
                    maxlength="5000"
                    show-word-limit
                  />
                </el-form-item>

                <el-row :gutter="10">
                  <el-col :span="12">
                    <el-form-item label="画面比例">
                      <el-select v-model="form.ratio" class="cyber-select" popper-class="cyber-popper" @change="calculateCost">
                        <el-option
                          v-for="r in (currentModel?.frontend_config?.ratios || ['1:1', '3:4', '16:9', '9:16'])"
                          :key="r"
                          :value="r"
                          :label="r"
                        />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item label="分辨率">
                      <el-select v-model="form.resolution" class="cyber-select" popper-class="cyber-popper" @change="calculateCost">
                        <el-option
                          v-for="res in (currentModel?.frontend_config?.resolutions || [{value: '1024x1024', label: '1K'}, {value: '2048x2048', label: '2K'}])"
                          :key="res.value || res"
                          :value="res.value || res"
                          :label="res.label || res"
                        />
                      </el-select>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="生成数量">
                  <el-input-number v-model="form.count" :min="1" :max="4" class="cyber-input-number" @change="calculateCost" />
                </el-form-item>

                <!-- 费用说明区域 -->
                <div class="cost-panel cyber-glass">
                  <div class="cost-header">
                    <span class="gradient-text">费用明细</span>
                  </div>
                  <div class="cost-items">
                    <div class="cost-item">
                      <span>当前积分</span>
                      <span class="value">{{ userStore.points }}</span>
                    </div>
                    <div class="cost-item">
                      <span>消耗积分</span>
                      <span class="value cost">{{ costInfo.cost }}</span>
                    </div>
                    <div class="cost-item">
                      <span>剩余积分</span>
                      <span class="value" :class="{ warning: remainingPoints < 0 }">{{ remainingPoints }}</span>
                    </div>
                  </div>
                  <div v-if="pricingDescription" class="pricing-desc">
                    <el-icon><InfoFilled /></el-icon>
                    <span>{{ pricingDescription }}</span>
                  </div>
                </div>

                <div style="display: flex; gap: 10px; margin-top: 20px;">
                  <el-button
                    type="primary"
                    size="large"
                    class="neon-btn"
                    style="flex: 1"
                    @click="handleGenerate"
                    :loading="generating"
                    :disabled="!canGenerate"
                  >
                    开始生成
                  </el-button>
                </div>
              </el-form>
            </el-col>

            <el-col :xs="24" :sm="24" :md="14" :lg="14" class="right-panel-col">
              <div class="result-header">
                <span class="gradient-text">生成结果 ({{ generatedImages.length }})</span>
                <el-button
                  v-if="generatedImages.length > 0"
                  type="success"
                  size="small"
                  class="cyber-action-btn"
                  @click="downloadAllImages"
                >
                  一键打包下载
                </el-button>
              </div>

              <div class="gallery-area cyber-glass-inset">
                <el-empty v-if="generatedImages.length === 0" description="生成的图片将显示在这里" :image-size="100" />
                <div v-else class="image-grid">
                  <div v-for="(img, index) in generatedImages" :key="index" class="img-card-wrapper cyber-border">
                    <el-image
                      :src="img"
                      :preview-src-list="generatedImages"
                      :initial-index="index"
                      class="generated-img"
                      :lazy="true"
                    >
                      <template #placeholder>
                        <div class="image-slot">加载中...</div>
                      </template>
                    </el-image>
                    <div class="hover-mask">
                      <div class="mask-actions">
                        <el-tooltip content="下载原图" placement="top">
                          <el-button circle type="success" class="mask-btn" @click="downloadSingleImage(img, index)">
                            <el-icon><Download /></el-icon>
                          </el-button>
                        </el-tooltip>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-tab-pane>

      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, InfoFilled } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import request from '@/api/request'
import { saveAs } from 'file-saver'
import JSZip from 'jszip'

const userStore = useUserStore()

const activeTab = ref('single')
const models = ref([])
const currentModel = ref(null)
const generating = ref(false)
const generatedImages = ref([])
const pricingDescription = ref('')

const form = reactive({
  model: '',
  prompt: '',
  ratio: '1:1',
  resolution: '1024x1024',
  count: 1
})

const costInfo = ref({
  cost: 0,
  breakdown: null
})

const canGenerate = computed(() => {
  return form.model && form.prompt && costInfo.value.cost > 0 && !generating.value
})

const remainingPoints = computed(() => {
  return userStore.points - costInfo.value.cost
})

// 加载模型列表
const loadModels = async () => {
  try {
    const res = await request.get('/api/models?model_type=image')
    models.value = res
    if (res.length > 0) {
      form.model = res[0].model_id
      await onModelChange()
    }
  } catch (error) {
    console.error('加载模型失败:', error)
    ElMessage.error('加载模型列表失败')
  }
}

// 模型切换
const onModelChange = async () => {
  if (!form.model) return

  try {
    const res = await request.get(`/api/models/${form.model}`)
    currentModel.value = res

    // 设置默认值
    if (res.frontend_config?.ratios?.length) {
      form.ratio = res.frontend_config.ratios[0]
    }
    if (res.frontend_config?.resolutions?.length) {
      const firstRes = res.frontend_config.resolutions[0]
      form.resolution = firstRes.value || firstRes
    }

    // 获取费用说明
    if (res.pricing_description) {
      pricingDescription.value = res.pricing_description
    }

    await calculateCost()
  } catch (error) {
    console.error('加载模型详情失败:', error)
  }
}

// 计算费用
const calculateCost = async () => {
  if (!form.model) return

  try {
    const res = await request.post('/api/calculate-cost', {
      model_id: form.model,
      resolution: form.resolution,
      ratio: form.ratio,
      count: form.count
    })
    costInfo.value = res
    if (res.description) {
      pricingDescription.value = res.description
    }
  } catch (error) {
    console.error('计算费用失败:', error)
  }
}

// 开始生成
const handleGenerate = async () => {
  if (userStore.points < costInfo.value.cost) {
    ElMessage.warning('积分不足，请充值')
    return
  }

  try {
    await ElMessageBox.confirm(
      `即将消耗 ${costInfo.value.cost} 积分生成 ${form.count} 张图片，确认继续？`,
      '费用确认',
      { confirmButtonText: '确认', cancelButtonText: '取消' }
    )
  } catch {
    return
  }

  generating.value = true
  let deductionId = null

  try {
    // 1. 预扣积分
    const reserveRes = await request.post('/api/points/reserve', {
      amount: costInfo.value.cost,
      model_id: form.model
    })
    deductionId = reserveRes.deduction_id

    // 2. 获取 Vercel URL
    const configRes = await request.get('/api/config/pricing-info')
    const vercelUrl = configRes.vercel_url || ''

    // 3. 调用 Vercel Functions 生成图片
    ElMessage.info('正在生成图片，请稍候...')
    const imageRes = await request.post(`${vercelUrl}/api/ai/generate-image`, {
      model: form.model,
      prompt: form.prompt,
      ratio: form.ratio,
      resolution: form.resolution,
      n: form.count,
      deduction_id: deductionId
    })

    // 4. 确认扣费
    await request.post('/api/points/confirm', { deduction_id: deductionId })

    // 5. 刷新积分
    userStore.refreshPoints()

    // 6. 显示结果
    const images = imageRes.images || imageRes.data?.map(d => d.url) || []
    generatedImages.value = [...images, ...generatedImages.value]

    ElMessage.success(`成功生成 ${images.length} 张图片`)
  } catch (error) {
    // 退还积分
    if (deductionId) {
      try {
        await request.post('/api/points/refund', {
          deduction_id: deductionId,
          reason: '生成失败'
        })
      } catch (e) {}
    }
    console.error('生成失败:', error)
    ElMessage.error(error.response?.data?.detail || '图片生成失败')
  } finally {
    generating.value = false
  }
}

// 下载单张图片
const downloadSingleImage = (url, suffix) => {
  const fileName = `Image_${Date.now()}_${suffix}.png`
  saveAs(url, fileName)
}

// 打包下载所有图片
const downloadAllImages = async () => {
  if (generatedImages.value.length === 0) return

  const zip = new JSZip()
  const folder = zip.folder("images")

  ElMessage.info('正在打包图片...')

  try {
    for (let i = 0; i < generatedImages.value.length; i++) {
      const url = generatedImages.value[i]
      const fileName = `Image_${i + 1}.png`
      const response = await fetch(url)
      const blob = await response.blob()
      folder.file(fileName, blob)
    }

    const content = await zip.generateAsync({ type: "blob" })
    saveAs(content, `Images_${Date.now()}.zip`)
    ElMessage.success('打包下载完成')
  } catch (error) {
    console.error('打包失败:', error)
    ElMessage.error('打包下载失败')
  }
}

onMounted(() => {
  loadModels()
})
</script>

<style scoped>
.image-tool {
  padding: 0px;
}

/* 1. 赛博 Tabs 容器 */
.cyber-tabs {
  background: rgba(0, 0, 0, 0.4) !important;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 12px !important;
  overflow: hidden;
  box-shadow: none !important;
}

:deep(.el-tabs__header) {
  background: rgba(0, 0, 0, 0.3) !important;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
  margin-bottom: 20px;
}

:deep(.el-tabs__item) {
  color: #a0aec0 !important;
  font-weight: 700;
  border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
  border-left: none !important;
}

:deep(.el-tabs__item.is-active) {
  background: rgba(255, 255, 255, 0.08) !important;
  color: #00f260 !important;
  border-bottom: none !important;
}

:deep(.el-tabs__content) {
  padding: 20px !important;
}

/* 2. 核心修复：输入框去灰 & 去双层 */
:deep(.el-input__wrapper),
:deep(.el-textarea__inner),
:deep(.el-input-number__decrease),
:deep(.el-input-number__increase) {
  background-color: rgba(0, 0, 0, 0.3) !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  box-shadow: none !important;
  color: #fff !important;
  border-radius: 8px !important;
}

:deep(.el-input__wrapper.is-focus),
:deep(.el-textarea__inner:focus) {
  border-color: #0575e6 !important;
  box-shadow: 0 0 8px rgba(5, 117, 230, 0.5) !important;
}

/* 3. 其他控件 */
:deep(.el-select__wrapper) {
  background-color: rgba(0, 0, 0, 0.3) !important;
  box-shadow: none !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  border-radius: 8px !important;
}

:deep(.el-select__selected-item) {
  color: #fff !important;
}

:deep(.el-form-item__label) {
  color: #a0aec0 !important;
}

/* 4. 按钮 & 文本 */
.neon-btn {
  background: linear-gradient(90deg, #7f00ff, #e100ff) !important;
  border: none !important;
  box-shadow: 0 4px 15px rgba(127, 0, 255, 0.4);
  color: #fff;
}

.neon-btn:hover {
  opacity: 0.9;
}

.neon-btn:disabled {
  opacity: 0.5;
}

.cyber-action-btn {
  background: rgba(0, 242, 96, 0.1) !important;
  border: 1px solid #00f260 !important;
  color: #00f260 !important;
}

.mask-btn {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
}

.mask-btn:hover {
  background: #00f260;
  border-color: #00f260;
  color: #000;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.gradient-text {
  font-size: 16px;
  font-weight: 800;
  background: linear-gradient(90deg, #00f260, #0575e6);
  -webkit-background-clip: text;
  color: transparent;
}

/* 5. 结果区 */
.gallery-area {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  padding: 15px;
  min-height: 400px;
}

:deep(.el-empty__description p) {
  color: #718096 !important;
}

.image-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 15px;
}

.img-card-wrapper {
  position: relative;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.05);
}

.generated-img {
  width: 100%;
  height: auto;
  min-height: 120px;
  display: block;
}

.hover-mask {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.7);
  opacity: 0;
  transition: opacity 0.3s;
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 10;
}

.img-card-wrapper:hover .hover-mask {
  opacity: 1;
}

.mask-actions {
  display: flex;
  gap: 10px;
}

.image-slot {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  height: 150px;
  background: rgba(255, 255, 255, 0.05);
  color: #718096;
  font-size: 12px;
}

/* 6. 费用面板 */
.cost-panel {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 15px;
  margin-top: 20px;
}

.cost-header {
  margin-bottom: 10px;
}

.cost-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cost-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.cost-item:last-child {
  border-bottom: none;
}

.cost-item .value {
  font-weight: bold;
  font-size: 16px;
  color: #fff;
}

.cost-item .value.cost {
  color: #00f260;
}

.cost-item .value.warning {
  color: #ff4757;
}

.pricing-desc {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 10px;
  padding: 10px;
  background: rgba(5, 117, 230, 0.1);
  border-radius: 8px;
  font-size: 12px;
  color: #a0aec0;
}

.pricing-desc .el-icon {
  color: #0575e6;
  margin-top: 2px;
}

/* 7. 响应式布局间距 */
@media screen and (max-width: 768px) {
  .right-panel-col {
    margin-top: 20px;
  }
}
</style>

<style>
/* 全局 Popper 样式 */
.cyber-popper.el-popper {
  background: rgba(0, 0, 0, 0.4) !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  backdrop-filter: blur(20px);
  color: #fff !important;
}

.cyber-popper .el-select-dropdown__item {
  color: #a0aec0 !important;
}

.cyber-popper .el-select-dropdown__item.is-hovering,
.cyber-popper .el-select-dropdown__item:hover {
  background: rgba(255, 255, 255, 0.1) !important;
  color: #fff !important;
}

.cyber-popper .el-select-dropdown__item.is-selected {
  color: #00f260 !important;
  font-weight: bold;
}

.cyber-popper .el-popper__arrow::before {
  background: rgba(0, 0, 0, 0.4) !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
}
</style>