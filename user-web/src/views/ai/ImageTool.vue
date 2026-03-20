<template>
  <div class="image-tool">
    <div class="cyber-container">
      <el-card class="cyber-glass" shadow="never">
        <template #header>
          <div class="card-header">
            <span class="gradient-text">🎨 图片生成控制台</span>
            <el-tag effect="dark" round color="#0575e6" style="border:none;">{{ currentModel?.config_schema?.model_info?.display_name || currentModel?.display_name || 'AI绘图' }}</el-tag>
          </div>
        </template>

        <el-row :gutter="24">
          <el-col :xs="24" :sm="24" :md="10" :lg="10">
            <el-form :model="dynamicFormData" label-position="top">
              <!-- 动态模型选择 -->
              <el-form-item label="选择模型">
                <el-select v-model="selectedModelId" style="width: 100%" class="cyber-select" popper-class="cyber-popper" @change="onModelChange">
                  <el-option
                    v-for="model in models"
                    :key="model.model_id"
                    :label="model.config_schema?.model_info?.display_name || model.display_name"
                    :value="model.model_id"
                  />
                </el-select>
              </el-form-item>

              <!-- ===== 动态渲染 UI Schema ===== -->
              <template v-for="field in uiSchema" :key="field.field_name">
                <template v-if="field.field_name !== 'model' && field.field_name !== 'ref_images' && field.field_name !== 'images'">
                  <!-- input 类型 -->
                  <el-form-item v-if="field.ui_type === 'input'" :label="field.label + (field.required ? ' (必填)' : '')">
                    <el-input
                      v-model="dynamicFormData[field.field_name]"
                      :placeholder="field.placeholder || ''"
                      class="cyber-input"
                    />
                  </el-form-item>

                  <!-- textarea 类型 -->
                  <el-form-item v-else-if="field.ui_type === 'textarea'" :label="field.label + (field.required ? ' (必填)' : '')">
                    <el-input
                      v-model="dynamicFormData[field.field_name]"
                      type="textarea"
                      :rows="field.rows || 6"
                      :placeholder="field.placeholder || ''"
                      resize="none"
                      :maxlength="field.max_length || 5000"
                      show-word-limit
                      class="cyber-input"
                    />
                  </el-form-item>

                  <!-- select 类型 -->
                  <el-form-item v-else-if="field.ui_type === 'select'" :label="field.label">
                    <el-select
                      v-model="dynamicFormData[field.field_name]"
                      class="cyber-select"
                      popper-class="cyber-popper"
                      :filterable="field.filterable || false"
                      @change="field.affects_pricing ? calculateCost() : null"
                    >
                      <el-option
                        v-for="opt in field.options"
                        :key="opt.value"
                        :value="opt.value"
                        :label="opt.label"
                      />
                    </el-select>
                  </el-form-item>

                  <!-- input-number 类型 -->
                  <el-form-item v-else-if="field.ui_type === 'input-number'" :label="field.label">
                    <el-input-number
                      v-model="dynamicFormData[field.field_name]"
                      :min="field.min || 1"
                      :max="field.max || 10"
                      class="cyber-input-number"
                      @change="field.affects_pricing ? calculateCost() : null"
                    />
                  </el-form-item>
                </template>
              </template>

              <!-- 参考图片上传 (特殊字段) -->
              <el-form-item v-if="hasUploadField" label="参考图片">
                <el-upload
                  action="#"
                  list-type="picture-card"
                  :auto-upload="false"
                  :limit="uploadMaxCount"
                  :on-change="handleFileChange"
                  :on-remove="handleRemove"
                  multiple
                  class="cyber-upload"
                >
                  <el-icon><Plus /></el-icon>
                </el-upload>
              </el-form-item>

              <!-- 费用信息 -->
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
              </div>

              <el-button
                type="primary"
                size="large"
                class="neon-btn"
                style="width: 100%; margin-top: 20px;"
                @click="handleGenerate"
                :loading="generating"
                :disabled="!canGenerate"
              >
                {{ generating ? '生成中...' : `开始生成 (消耗${costInfo.cost}积分)` }}
              </el-button>
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
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Download, Plus } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import request from '@/api/request'
import { generateImage } from '@/api/index'
import { saveAs } from 'file-saver'
import JSZip from 'jszip'

const userStore = useUserStore()

// ========== 状态 ==========
const models = ref([])
const currentModel = ref(null)
const selectedModelId = ref('')
const generating = ref(false)
const generatedImages = ref([])
const fileList = ref([])
const imageBase64List = ref([])

// ========== 动态表单数据 ==========
const dynamicFormData = reactive({})

// 计算属性：UI Schema
const uiSchema = computed(() => {
  return currentModel.value?.config_schema?.ui_schema || []
})

// 计算属性：是否有上传字段
const hasUploadField = computed(() => {
  return uiSchema.value.some(f => f.ui_type === 'upload')
})

// 计算属性：上传最大数量
const uploadMaxCount = computed(() => {
  const uploadField = uiSchema.value.find(f => f.ui_type === 'upload')
  return uploadField?.max_count || 5
})

// ========== 费用计算 ==========
const costInfo = ref({ cost: 0, breakdown: null })

const canGenerate = computed(() => {
  const requiredFields = uiSchema.value.filter(f => f.required).map(f => f.field_name)
  const hasAllRequired = requiredFields.every(f => dynamicFormData[f])
  return selectedModelId.value && dynamicFormData.prompt && costInfo.value.cost > 0 && !generating.value
})

const remainingPoints = computed(() => {
  return userStore.points - costInfo.value.cost
})

// ========== 加载模型 ==========
const loadModels = async () => {
  try {
    const res = await request.get('/api/models?model_type=image')
    models.value = res
    if (res.length > 0) {
      selectedModelId.value = res[0].model_id
      await onModelChange()
    }
  } catch (error) {
    console.error('加载模型失败:', error)
    ElMessage.error('加载模型列表失败')
  }
}

// ========== 模型切换（含防呆逻辑）==========
const onModelChange = async () => {
  if (!selectedModelId.value) return

  try {
    const res = await request.get(`/api/models/${selectedModelId.value}`)
    currentModel.value = res

    // 确保 config_schema 存在
    if (typeof res.config_schema === 'string') {
      try {
        res.config_schema = JSON.parse(res.config_schema)
      } catch {}
    }

    const schema = res.config_schema?.ui_schema || []

    // ===== 防呆逻辑 =====
    schema.forEach(field => {
      const oldValue = dynamicFormData[field.field_name]

      if (field.ui_type === 'select' && field.options) {
        const validValues = field.options.map(o => o.value)
        if (oldValue === undefined || !validValues.includes(oldValue)) {
          dynamicFormData[field.field_name] = field.default_value ?? validValues[0]
        }
      } else if (field.ui_type === 'input-number') {
        const num = Number(oldValue)
        if (isNaN(num) || num < (field.min || 1) || num > (field.max || 10)) {
          dynamicFormData[field.field_name] = field.default_value ?? field.min ?? 1
        }
      } else {
        if (oldValue === undefined) {
          dynamicFormData[field.field_name] = field.default_value ?? ''
        }
      }
    })

    await calculateCost()
  } catch (error) {
    console.error('加载模型详情失败:', error)
  }
}

// ========== 费用计算 ==========
const calculateCost = async () => {
  if (!selectedModelId.value) return

  try {
    const res = await request.post('/api/calculate-cost', {
      model_id: selectedModelId.value,
      resolution: dynamicFormData.resolution,
      ratio: dynamicFormData.aspect_ratio || dynamicFormData.ratio,
      count: dynamicFormData.num_images || dynamicFormData.count || 1
    })
    costInfo.value = res
  } catch (error) {
    console.error('计算费用失败:', error)
    // 使用 config_schema 中的计费规则
    const pricingRules = currentModel.value?.config_schema?.pricing_rules
    if (pricingRules?.mode === 'fixed') {
      costInfo.value = { cost: pricingRules.fixed_cost || 2 }
    }
  }
}

// ========== 文件处理 ==========
const handleFileChange = (uploadFile, uploadFiles) => {
  fileList.value = uploadFiles
  convertImagesToBase64()
}

const handleRemove = (file, uploadFiles) => {
  fileList.value = uploadFiles
  convertImagesToBase64()
}

const convertImagesToBase64 = () => {
  imageBase64List.value = []
  fileList.value.forEach(file => {
    const reader = new FileReader()
    reader.readAsDataURL(file.raw)
    reader.onload = () => {
      imageBase64List.value.push(reader.result)
    }
  })
}

// ========== 开始生成 ==========
const handleGenerate = async () => {
  if (userStore.points < costInfo.value.cost) {
    ElMessage.warning('积分不足，请充值')
    return
  }

  try {
    await ElMessageBox.confirm(
      `即将消耗 ${costInfo.value.cost} 积分生成图片，确认继续？`,
      '费用确认',
      { confirmButtonText: '确认', cancelButtonText: '取消' }
    )
  } catch {
    return
  }

  generating.value = true
  let deductionId = null

  try {
    // 预扣积分
    const reserveRes = await request.post('/api/points/reserve', {
      amount: costInfo.value.cost,
      model_id: selectedModelId.value
    })
    deductionId = reserveRes.deduction_id

    // 调用图片生成 API
    ElMessage.info('正在生成图片，请稍候...')

    const requestData = {
      model: selectedModelId.value,
      prompt: dynamicFormData.prompt,
      size: dynamicFormData.resolution || dynamicFormData.size,
      images: imageBase64List.value
    }

    // 添加动态参数
    const requestMapping = currentModel.value?.config_schema?.request_mapping?.dynamic_params || {}
    Object.keys(requestMapping).forEach(key => {
      if (dynamicFormData[key] !== undefined) {
        const targetKey = requestMapping[key]
        if (targetKey !== key) {
          requestData[targetKey] = dynamicFormData[key]
        }
      }
    })

    const imageRes = await generateImage(requestData)

    // 确认扣费
    await request.post('/api/points/confirm', { deduction_id: deductionId })

    // 刷新积分
    userStore.refreshPoints()

    // 解析结果 - 使用 response_mapping
    const responseMapping = currentModel.value?.config_schema?.response_mapping || {}
    const resultUrlPath = responseMapping.result_url_path || 'data[0].url'

    const images = imageRes.images || [getJsonValue(imageRes, resultUrlPath)].filter(Boolean) ||
                   imageRes.data?.map(d => d.url) || []
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
    ElMessage.error(error.response?.data?.detail || error.message || '图片生成失败')
  } finally {
    generating.value = false
  }
}

// ========== JSON Path 解析 ==========
const getJsonValue = (obj, path) => {
  if (!path || !obj) return null
  const keys = path.split('.')
  let value = obj

  for (const key of keys) {
    const arrayMatch = key.match(/^(\w+)\[(\d+)\]$/)
    if (arrayMatch) {
      const [, arrKey, index] = arrayMatch
      value = value?.[arrKey]?.[parseInt(index)]
    } else {
      value = value?.[key]
    }
    if (value === undefined) return null
  }

  return value
}

// ========== 下载功能 ==========
const downloadSingleImage = (url, suffix) => {
  const fileName = `Image_${Date.now()}_${suffix}.png`
  saveAs(url, fileName)
}

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
.image-tool { padding: 0px; }

.cyber-glass {
  background: rgba(0, 0, 0, 0.4) !important;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 12px;
  color: #fff;
  box-shadow: none !important;
}

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

:deep(.el-select__wrapper) {
  background-color: rgba(0, 0, 0, 0.3) !important;
  box-shadow: none !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  border-radius: 8px !important;
}

:deep(.el-select__selected-item) { color: #fff !important; }
:deep(.el-form-item__label) { color: #a0aec0 !important; }

:deep(.el-upload--picture-card) {
  background-color: rgba(0, 0, 0, 0.3) !important;
  border: 1px dashed rgba(255, 255, 255, 0.3) !important;
  color: #a0aec0 !important;
  border-radius: 8px !important;
}

.neon-btn {
  background: linear-gradient(90deg, #7f00ff, #e100ff) !important;
  border: none !important;
  box-shadow: 0 4px 15px rgba(127, 0, 255, 0.4);
  color: #fff;
}

.neon-btn:hover { opacity: 0.9; }
.neon-btn:disabled { opacity: 0.5; }

.cyber-action-btn {
  background: rgba(0, 242, 96, 0.1) !important;
  border: 1px solid #00f260 !important;
  color: #00f260 !important;
}

.gradient-text {
  font-size: 16px;
  font-weight: 800;
  background: linear-gradient(90deg, #00f260, #0575e6);
  -webkit-background-clip: text;
  color: transparent;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.gallery-area {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  padding: 15px;
  min-height: 400px;
}

:deep(.el-empty__description p) { color: #718096 !important; }

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

.img-card-wrapper:hover .hover-mask { opacity: 1; }
.mask-actions { display: flex; gap: 10px; }

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

.cost-panel {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 15px;
  margin-top: 20px;
}

.cost-header { margin-bottom: 10px; }
.cost-items { display: flex; flex-direction: column; gap: 8px; }

.cost-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.cost-item:last-child { border-bottom: none; }

.cost-item .value {
  font-weight: bold;
  font-size: 16px;
  color: #fff;
}

.cost-item .value.cost { color: #00f260; }
.cost-item .value.warning { color: #ff4757; }

@media screen and (max-width: 768px) {
  .right-panel-col { margin-top: 20px; }
}
</style>

<style>
.cyber-popper.el-popper {
  background: rgba(0, 0, 0, 0.4) !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  backdrop-filter: blur(20px);
  color: #fff !important;
}

.cyber-popper .el-select-dropdown__item { color: #a0aec0 !important; }
.cyber-popper .el-select-dropdown__item.is-hovering,
.cyber-popper .el-select-dropdown__item:hover {
  background: rgba(255, 255, 255, 0.1) !important;
  color: #fff !important;
}
.cyber-popper .el-select-dropdown__item.is-selected { color: #00f260 !important; font-weight: bold; }
</style>