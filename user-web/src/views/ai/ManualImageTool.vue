<template>
  <div class="image-tool">
    <el-row :gutter="20">
      <el-col :xs="24" :sm="24" :md="11" :lg="11">
        <el-card class="cyber-glass" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="gradient-text">✏️ 手动图片生成</span>
              <el-tag effect="dark" round color="#ff0055" style="border:none; box-shadow: 0 0 10px rgba(255,0,85,0.4)">{{ currentModel?.config_schema?.model_info?.display_name || currentModel?.display_name || 'AI图片' }}</el-tag>
            </div>
          </template>

          <el-form label-position="top">
            <!-- 模型选择器 -->
            <el-form-item label="生成模型">
              <el-select v-model="selectedModelId" style="width: 100%" class="cyber-select" popper-class="cyber-popper" @change="onModelChange">
                <el-option v-for="m in models" :key="m.model_id" :value="m.model_id" :label="m.config_schema?.model_info?.display_name || m.display_name" />
              </el-select>
            </el-form-item>

            <!-- 参考图片上传 (可选) -->
            <el-form-item :label="`参考图片 (可选，最多${uploadMaxCount}张，支持拖拽)`">
              <el-upload action="#" list-type="picture-card" :auto-upload="false" :limit="uploadMaxCount" :on-change="handleFileChange" :on-remove="handleRemove" multiple drag class="cyber-upload">
                <el-icon><Plus /></el-icon>
              </el-upload>
            </el-form-item>

            <el-form-item label="生成指令 (必填)">
              <el-input v-model="form.prompt" type="textarea" :rows="4" placeholder="描述你想生成的图片，例如：一只白色的猫坐在窗台上，阳光照射，温馨风格..." class="cyber-input" />
            </el-form-item>

            <el-row :gutter="10">
              <el-col :span="12">
                <el-form-item label="画面比例">
                  <el-select v-model="form.aspect_ratio" style="width: 100%" class="cyber-select" popper-class="cyber-popper">
                    <el-option v-for="opt in aspectRatioOptions" :key="opt.value" :value="opt.value" :label="opt.label" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="分辨率">
                  <el-select v-model="form.resolution" style="width: 100%" class="cyber-select" popper-class="cyber-popper">
                    <el-option v-for="opt in resolutionOptions" :key="opt.value" :value="opt.value" :label="opt.label" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item v-if="numImagesConfig" label="生成数量">
              <el-input-number v-model="form.num_images" :min="numImagesConfig.min || 1" :max="numImagesConfig.max || 10" style="width: 100%" class="cyber-input-number" />
            </el-form-item>

            <el-button type="primary" size="large" class="neon-btn" style="width: 100%" @click="manualGenerate" :loading="loading" :disabled="loading">
              🚀 开始生成（{{ unitPrice * form.num_images }}积分）
            </el-button>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="24" :md="13" :lg="13" class="right-panel-col">
        <el-card class="cyber-glass" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="gradient-text">📷 任务看板</span>
              <el-button v-if="generatedImages.length > 0" type="success" size="small" class="cyber-action-btn" @click="downloadAllImages">一键打包下载</el-button>
            </div>
          </template>

          <div v-if="generatedImages.length === 0" class="empty-state">
            <div class="placeholder-icon">🖼️</div>
            <p>暂无任务，请在左侧提交</p>
          </div>

          <div v-else class="image-grid">
            <div v-for="(img, index) in generatedImages" :key="index" class="img-card-wrapper">
              <img :src="img" class="generated-img" @click="openImagePreview(img)" />
              <div class="hover-mask">
                <div class="mask-actions">
                  <el-tooltip content="预览大图" placement="top">
                    <el-button circle type="info" class="mask-btn" @click="openImagePreview(img)"><el-icon><ZoomIn /></el-icon></el-button>
                  </el-tooltip>
                  <el-tooltip content="下载原图" placement="top">
                    <el-button circle type="success" class="mask-btn" @click="downloadSingleImage(img, index)"><el-icon><Download /></el-icon></el-button>
                  </el-tooltip>
                </div>
              </div>
            </div>
          </div>
        </el-card>

        <!-- 历史记录面板 -->
        <HistoryPanel ref="historyPanelRef" fixed-type="image" />
      </el-col>
    </el-row>

    <!-- 全窗口图片预览 -->
    <Teleport to="body">
      <transition name="fade">
        <div v-if="imagePreviewVisible" class="fullscreen-preview" @click="closeImagePreview">
          <div class="preview-close-btn" @click="closeImagePreview">
            <el-icon><Close /></el-icon>
          </div>
          <img :src="imagePreviewUrl" class="fullscreen-image" @click.stop />
          <div class="preview-nav">
            <el-button circle class="nav-btn" @click.stop="prevImage" :disabled="currentImageIndex === 0">
              <el-icon><ArrowLeft /></el-icon>
            </el-button>
            <span class="preview-counter">{{ currentImageIndex + 1 }} / {{ generatedImages.length }}</span>
            <el-button circle class="nav-btn" @click.stop="nextImage" :disabled="currentImageIndex === generatedImages.length - 1">
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, watch, computed } from 'vue'
import request from '../../api/request'
import { generateImage as generateImageAPI, getValueByPath } from '../../api/index'
import { Plus, ZoomIn, Download, Close, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { saveAs } from 'file-saver'
import JSZip from 'jszip'
import HistoryPanel from '@/components/HistoryPanel.vue'
import { cacheMedia } from '@/utils/mediaCache'
import { compressImage } from '@/utils/imageCompress'

const emit = defineEmits(['refresh-points', 'log'])

// ========== 模型配置 ==========
const models = ref([])
const selectedModelId = ref('')
const currentModel = ref(null)
const currentDeductionId = ref(null)

const unitPrice = computed(() => {
  const pricingRules = currentModel.value?.config_schema?.pricing_rules
  if (pricingRules?.mode === 'dynamic') {
    return pricingRules.base_price || 0
  } else {
    return pricingRules?.fixed_price || 0
  }
})

// 从模型 ui_schema 动态读取下拉选项
const getUiOptions = (fieldName) => {
  const schema = currentModel.value?.config_schema?.ui_schema
  if (!schema) return null
  const field = schema.find(f => f.field_name === fieldName)
  return field?.options || null
}

const aspectRatioOptions = computed(() => {
  return getUiOptions('aspect_ratio') || [
    { label: '3:4', value: '3:4' }, { label: '1:1', value: '1:1' },
    { label: '16:9', value: '16:9' }, { label: '9:16', value: '9:16' }
  ]
})

const resolutionOptions = computed(() => {
  return getUiOptions('resolution') || [
    { label: '1K', value: '1K' }, { label: '2K', value: '2K' }
  ]
})

const uploadMaxCount = computed(() => {
  const refField = currentModel.value?.config_schema?.ui_schema?.find(f => f.field_name === 'ref_images')
  return refField?.max_count || 5
})

const numImagesConfig = computed(() => {
  const field = currentModel.value?.config_schema?.ui_schema?.find(f => f.field_name === 'num_images')
  return field || null
})

const getUiDefault = (fieldName, fallback) => {
  const schema = currentModel.value?.config_schema?.ui_schema
  if (!schema) return fallback
  const field = schema.find(f => f.field_name === fieldName)
  return field?.default_value ?? fallback
}

const loadModels = async () => {
  try {
    const res = await request.get('/api/models?model_type=image')
    models.value = res
    if (res.length > 0) {
      selectedModelId.value = res[0].model_id
      await onModelChange()
    }
  } catch (e) {
    console.error('加载模型列表失败', e)
  }
}

const onModelChange = async () => {
  if (!selectedModelId.value) return
  try {
    const res = await request.get(`/api/models/${selectedModelId.value}`)
    if (typeof res.config_schema === 'string') {
      try { res.config_schema = JSON.parse(res.config_schema) } catch {}
    }
    currentModel.value = res

    // 从 ui_schema 更新表单默认值
    form.aspect_ratio = getUiDefault('aspect_ratio', '3:4')
    form.resolution = getUiDefault('resolution', '1K')
    if (numImagesConfig.value) {
      form.num_images = numImagesConfig.value.default_value ?? 1
    }
  } catch (e) {
    console.error('加载模型详情失败', e)
  }
}

// ========== 表单状态 ==========
const loading = ref(false)
const fileList = ref([])
const imageBase64List = ref([])
const generatedImages = ref([])
const historyPanelRef = ref(null)

const form = reactive({
  prompt: '',
  aspect_ratio: '3:4',
  resolution: '1K',
  num_images: 1
})

// 全窗口图片预览状态
const imagePreviewVisible = ref(false)
const imagePreviewUrl = ref('')
const currentImageIndex = ref(0)

// === 通用方法 ===
const fileToBase64 = async (file) => {
  return new Promise((resolve) => {
    const reader = new FileReader()
    reader.readAsDataURL(file.raw || file)
    reader.onload = async () => {
      const compressed = await compressImage(reader.result, 400, 200, 2048)
      resolve(compressed)
    }
  })
}

const handleFileChange = async (file, fileListRef) => {
  fileList.value = fileListRef
  imageBase64List.value = await Promise.all(fileList.value.map(f => fileToBase64(f)))
  emit('log', `已加载 ${fileList.value.length} 张参考图`)
}

const handleRemove = async (file, fileListRef) => {
  fileList.value = fileListRef
  await handleFileChange(null, fileListRef)
}

const openImagePreview = (url) => {
  imagePreviewUrl.value = url
  currentImageIndex.value = generatedImages.value.indexOf(url)
  imagePreviewVisible.value = true
  document.body.style.overflow = 'hidden'
}

const closeImagePreview = () => {
  imagePreviewVisible.value = false
  document.body.style.overflow = ''
}

const prevImage = () => {
  if (currentImageIndex.value > 0) {
    currentImageIndex.value--
    imagePreviewUrl.value = generatedImages.value[currentImageIndex.value]
  }
}

const nextImage = () => {
  if (currentImageIndex.value < generatedImages.value.length - 1) {
    currentImageIndex.value++
    imagePreviewUrl.value = generatedImages.value[currentImageIndex.value]
  }
}

// ========== 手动图片生成 ==========
const manualGenerate = async () => {
  if (!form.prompt.trim()) return ElMessage.warning('请输入生成指令')

  const totalCost = unitPrice.value * form.num_images

  const userStore = (await import('@/stores/user')).useUserStore()
  if (userStore.points < totalCost) {
    return ElMessage.warning('积分不足，请充值')
  }

  try {
    await ElMessageBox.confirm(
      `即将消耗 ${totalCost} 积分进行图片生成，确认继续？`,
      '费用确认',
      { confirmButtonText: '确认', cancelButtonText: '取消' }
    )
  } catch {
    return
  }

  loading.value = true
  currentDeductionId.value = null

  emit('log', '预扣积分...')
  try {
    const reserveRes = await request.post('/api/points/reserve', {
      amount: totalCost,
      model_id: selectedModelId.value
    })
    currentDeductionId.value = reserveRes.deduction_id
    emit('log', `预扣成功，deduction_id: ${currentDeductionId.value}`)
  } catch (e) {
    emit('log', `预扣积分失败: ${e.message || e}`)
    ElMessage.error('积分预扣失败')
    loading.value = false
    return
  }

  emit('log', `开始手动图片生成 ${form.num_images} 张${imageBase64List.value.length > 0 ? `（${imageBase64List.value.length}张参考图）` : ''}...`)

  let successCount = 0
  for (let i = 0; i < form.num_images; i++) {
    emit('log', `[第 ${i+1}/${form.num_images} 张] 正在请求云端绘图...`)
    try {
      const res = await generateImageAPI({
        model: selectedModelId.value,
        prompt: form.prompt,
        aspect_ratio: form.aspect_ratio,
        resolution: form.resolution,
        images: imageBase64List.value.length > 0 ? imageBase64List.value : undefined,
        seed: Date.now() + i
      }, currentModel.value?.config_schema)

      const resultPath = currentModel.value?.config_schema?.response_mapping?.result_url_path
      const url = (resultPath ? getValueByPath(res, resultPath) : null) || res.data?.[0]?.url || res.data?.url
      if (url) {
        generatedImages.value.unshift(url)
        emit('refresh-points')
        emit('log', `第 ${i+1} 张生成成功！`)
        successCount++

        try {
          const response = await fetch(url)
          if (response.ok) {
            const blob = await response.blob()
            await cacheMedia(url, blob, 'image')
          }
        } catch (e) {
          console.warn('缓存图片失败', e)
        }

        saveImageHistory(url, form.prompt)
      } else {
        ElMessage.error(`第 ${i+1} 张失败`)
        emit('log', `第 ${i+1} 张服务端拒绝: ${JSON.stringify(res)}`)
      }
    } catch (e) {
      let errMsg = e.message || '未知错误'
      if (errMsg.includes('timeout')) errMsg = '请求超时(后端仍在运行)'
      ElMessage.error(`第 ${i+1} 张请求出错`)
      emit('log', `第 ${i+1} 张异常: ${errMsg}`)
    }
  }

  // 确认或退还积分
  if (successCount > 0) {
    if (currentDeductionId.value) {
      try {
        await request.post('/api/points/confirm', { deduction_id: currentDeductionId.value })
        emit('log', '积分扣费已确认')
        emit('refresh-points')
      } catch (e) {
        console.error('确认扣费失败', e)
      }
    }
    ElMessage.success(`生成完成，成功 ${successCount} 张`)
    emit('log', `任务全部结束`)
  } else {
    if (currentDeductionId.value) {
      try {
        await request.post('/api/points/refund', {
          deduction_id: currentDeductionId.value,
          reason: '手动图片生成全部失败'
        })
        emit('log', '积分已退还')
        emit('refresh-points')
      } catch (err) {}
    }
  }

  loading.value = false
}

// ========== 保存历史记录 ==========
const saveImageHistory = async (resultUrl, prompt) => {
  try {
    await request.post('/api/history', {
      task_type: 'image',
      model_id: selectedModelId.value,
      status: 'success',
      prompt_summary: prompt || '',
      params_json: {
        aspect_ratio: form.aspect_ratio,
        resolution: form.resolution
      },
      result_url: resultUrl,
      cost_points: unitPrice.value
    })
    if (historyPanelRef.value) {
      historyPanelRef.value.refresh()
    }
  } catch (e) {
    console.error('保存历史记录失败', e)
  }
}

const downloadSingleImage = (url, suffix) => { const fileName = `Manual_${Date.now()}_${suffix}.png`; saveAs(url, fileName) }
const downloadAllImages = async () => {
  const zip = new JSZip()
  const folder = zip.folder("images")
  emit('log', '正在打包下载所有图片...')
  try {
    for (let i = 0; i < generatedImages.value.length; i++) {
      const url = generatedImages.value[i]
      const fileName = `Manual_${i + 1}.png`
      const response = await fetch(url)
      const blob = await response.blob()
      folder.file(fileName, blob)
    }
    zip.generateAsync({ type: "blob" }).then((content) => {
      saveAs(content, `Manual_Images_${Date.now()}.zip`)
      emit('log', '打包下载完成')
    })
  } catch (e) {
    emit('log', `打包失败: ${e}`)
    ElMessage.error('打包下载失败')
  }
}

// Session persistence
const SESSION_KEY = 'manual_image_tool_data'
const saveStateToSession = () => {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify({ form, images: generatedImages.value }))
}
const restoreStateFromSession = () => {
  const data = sessionStorage.getItem(SESSION_KEY)
  if (data) {
    try {
      const parsed = JSON.parse(data)
      Object.assign(form, parsed.form || {})
      generatedImages.value = parsed.images || []
    } catch (e) {}
  }
}

watch(form, saveStateToSession, { deep: true })
watch(generatedImages, saveStateToSession, { deep: true })
onMounted(() => { loadModels(); restoreStateFromSession() })
</script>

<style scoped>
.image-tool { padding: 0px; }

/* 1. 赛博玻璃容器 */
.cyber-glass {
  background: rgba(0, 0, 0, 0.4) !important;
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  border-radius: 12px;
  color: #fff;
  transition: all 0.3s;
  box-shadow: none !important;
}
:deep(.el-card) { background: transparent; border: none; color: #fff; }
.card-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
:deep(.el-card__header) { border-bottom: 1px solid rgba(255, 255, 255, 0.1); }

/* 2. 输入框样式 */
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
:deep(.el-select__selected-item) { color: #fff !important; }
:deep(.el-form-item__label) { color: #a0aec0 !important; }

:deep(.el-upload--picture-card), :deep(.el-upload-dragger) {
  background-color: rgba(0, 0, 0, 0.3) !important;
  border: 1px dashed rgba(255, 255, 255, 0.3) !important;
  color: #a0aec0 !important;
  border-radius: 8px !important;
}
:deep(.el-upload--picture-card:hover) { border-color: #0575e6 !important; color: #fff !important; }
:deep(.el-upload-dragger) {
  background-color: transparent !important;
  border: none !important;
}
:deep(.el-upload-list--picture-card .el-upload-list__item) {
  background-color: rgba(0, 0, 0, 0.3) !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  border-radius: 8px !important;
}
:deep(.el-upload-list__item-delete),
:deep(.el-upload-list__item-status-label) {
  background-color: rgba(0, 0, 0, 0.5) !important;
}

/* 4. 按钮 & 文本 */
.gradient-text { font-size: 18px; font-weight: 800; background: linear-gradient(90deg, #00f260, #0575e6); -webkit-background-clip: text; color: transparent; text-shadow: 0 0 10px rgba(5, 117, 230, 0.3); }
.neon-btn { background: linear-gradient(90deg, #7f00ff, #e100ff) !important; border: none; box-shadow: 0 4px 15px rgba(127, 0, 255, 0.4); color: #fff; }
.neon-btn:hover { opacity: 0.9; }
.cyber-action-btn { background: rgba(0,242,96,0.1) !important; border: 1px solid #00f260 !important; color: #00f260 !important; }
.mask-btn { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: #fff; }
.mask-btn:hover { background: #00f260; border-color: #00f260; color: #000; }

/* 5. 结果区 */
.empty-state { text-align: center; padding: 50px 0; color: #718096; }
.placeholder-icon { font-size: 60px; margin-bottom: 20px; opacity: 0.5; color: #a0aec0; }
.image-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 15px; }
.img-card-wrapper { position: relative; border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; overflow: hidden; background: rgba(255,255,255,0.05); }
.generated-img { width: 100%; height: auto; min-height: 120px; display: block; cursor: pointer; transition: transform 0.3s; }
.generated-img:hover { transform: scale(1.02); }
.hover-mask { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.7); opacity: 0; transition: opacity 0.3s; display: flex; justify-content: center; align-items: center; z-index: 10; }
.img-card-wrapper:hover .hover-mask { opacity: 1; }
.mask-actions { display: flex; gap: 10px; }

/* 6. 响应式 */
@media screen and (max-width: 768px) {
  .right-panel-col { margin-top: 20px; }
  .card-header { flex-direction: column; align-items: flex-start; }
}
</style>

<style>
.fullscreen-preview {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  z-index: 99999;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: zoom-out;
}
.fullscreen-image {
  max-width: 90vw;
  max-height: 85vh;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.5);
}
.preview-close-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 40px;
  height: 40px;
  background: rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #fff;
  font-size: 20px;
  transition: all 0.3s;
}
.preview-close-btn:hover { background: rgba(255, 0, 0, 0.5); }
.preview-nav {
  position: absolute;
  bottom: 30px;
  display: flex;
  align-items: center;
  gap: 15px;
}
.nav-btn { background: rgba(0, 0, 0, 0.5) !important; border: 1px solid rgba(255, 255, 255, 0.3) !important; color: #fff !important; }
.nav-btn:hover { background: rgba(0, 242, 96, 0.3) !important; border-color: #00f260 !important; }
.preview-counter { color: #fff; font-size: 16px; }
</style>
