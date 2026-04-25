<template>
  <div class="image-tool">
    <el-row :gutter="20">
      <el-col :xs="24" :sm="24" :md="11" :lg="11">
        <el-card class="cyber-glass" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="gradient-text">🖼️ 商品图生成控制台</span>
              <div class="tab-buttons">
                <div
                  class="tab-btn"
                  :class="{ active: activeTab === 'generate' }"
                  @click="activeTab = 'generate'"
                >
                  🎨 商品图生成
                </div>
                <div
                  class="tab-btn"
                  :class="{ active: activeTab === 'regenerate' }"
                  @click="activeTab = 'regenerate'"
                >
                  🖌️ 图片再编辑
                </div>
              </div>
            </div>
          </template>

          <!-- 模型选择器 (两个 Tab 共享) -->
          <el-form label-position="top">
            <el-form-item label="生成模型">
              <el-select v-model="selectedModelId" style="width: 100%" class="cyber-select" popper-class="cyber-popper" @change="onModelChange">
                <el-option v-for="m in models" :key="m.model_id" :value="m.model_id" :label="m.config_schema?.model_info?.display_name || m.display_name" />
              </el-select>
            </el-form-item>
          </el-form>

          <!-- ===== Tab 1: 商品图生成 ===== -->
          <template v-if="activeTab === 'generate'">
            <el-form label-position="top">
              <el-form-item label="产品名称 (必填)">
                <el-input v-model="form.product_type" placeholder="例如：高端商务手提包" class="cyber-input" />
              </el-form-item>

              <el-form-item label="设计风格">
                 <el-select v-model="form.design_style" style="width: 100%" filterable allow-create default-first-option class="cyber-select" popper-class="cyber-popper">
                   <el-option v-for="opt in designStyleOptions" :key="opt.value" :value="opt.value" :label="opt.label" />
                 </el-select>
              </el-form-item>

              <div class="label-box">
                <span class="label-text">核心卖点 (必填)</span>
                <el-tooltip content="请先在下方上传图片，然后点击此按钮" placement="top" :disabled="fileList.length > 0">
                  <el-button type="primary" plain round size="small" class="optimize-btn" @click="analyzeImages" :loading="analyzing" :disabled="fileList.length === 0">
                    {{ analyzing ? '正在分析...' : '✨ 看图自动生成文案' }}
                  </el-button>
                </el-tooltip>
              </div>

              <el-form-item>
                <el-input v-model="form.selling_points" type="textarea" :rows="6" placeholder="在此输入卖点..." resize="none" maxlength="5000" show-word-limit class="cyber-input" />
              </el-form-item>

              <!-- 参考图片上传 -->
              <el-form-item :label="`参考图片 (最多${uploadMaxCount}张，支持拖拽)`">
                <el-upload action="#" list-type="picture-card" :auto-upload="false" :limit="uploadMaxCount" :on-change="handleFileChange" :on-remove="handleRemove" multiple drag class="cyber-upload">
                  <el-icon><Plus /></el-icon>
                </el-upload>
              </el-form-item>

              <!-- 参数：一行2个布局 -->
              <el-row :gutter="10">
                <el-col :span="12">
                  <el-form-item label="目标语言">
                      <el-select v-model="form.target_lang" style="width: 100%" filterable placeholder="请选择语言" class="cyber-select" popper-class="cyber-popper">
                        <el-option v-for="opt in targetLangOptions" :key="opt.value" :value="opt.value" :label="opt.label" />
                      </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                   <el-form-item label="生成数量">
                     <el-input-number v-model="form.num_images" :min="1" :max="10" style="width: 100%" class="cyber-input-number" />
                </el-form-item>
                </el-col>
              </el-row>

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

              <div style="display: flex; gap: 10px; margin-top: 10px;">
                  <el-button type="primary" size="large" class="neon-btn" style="flex: 1" @click="generateImage" :loading="loading" :disabled="stopped">
                    🚀 开始生成 ({{ costInfo.cost || form.num_images * unitPrice }} 积分)
                  </el-button>
                  <el-button type="danger" size="large" class="stop-btn" style="width: 100px" @click="stopTask" :disabled="!loading">
                    停止
                  </el-button>
              </div>
            </el-form>
          </template>

          <!-- ===== Tab 2: 图片再编辑 ===== -->
          <template v-else-if="activeTab === 'regenerate'">
            <el-form label-position="top">
              <!-- 参考图片上传 -->
              <el-form-item label="原图 (可上传多张融合生成)">
                <el-upload action="#" list-type="picture-card" :auto-upload="false" :limit="5" :on-change="handleFileChange" :on-remove="handleRemove" multiple drag class="cyber-upload">
                  <el-icon><Plus /></el-icon>
                </el-upload>
              </el-form-item>

              <el-form-item label="修改指令 (必填)">
                <el-input v-model="regenForm.prompt" type="textarea" :rows="4" placeholder="例如：把背景变成雪天，增加光照..." class="cyber-input" />
              </el-form-item>

              <el-form-item label="重绘幅度 (强度 0.1~1.0)">
                <el-slider v-model="regenForm.strength" :min="0.1" :max="1.0" :step="0.1" show-input class="cyber-slider" />
                <div class="slider-hint">0.1 = 微调 (保留原图) | 1.0 = 重画 (仅参考构图)</div>
              </el-form-item>

              <el-row :gutter="10">
                <el-col :span="12">
                  <el-form-item label="画面比例">
                    <el-select v-model="regenForm.aspect_ratio" style="width: 100%" class="cyber-select" popper-class="cyber-popper">
                      <el-option v-for="opt in aspectRatioOptions" :key="opt.value" :value="opt.value" :label="opt.label" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="12">
                   <el-form-item label="分辨率">
                    <el-select v-model="regenForm.resolution" style="width: 100%" class="cyber-select" popper-class="cyber-popper">
                      <el-option v-for="opt in resolutionOptions" :key="opt.value" :value="opt.value" :label="opt.label" />
                    </el-select>
                  </el-form-item>
                </el-col>
              </el-row>

              <el-button type="primary" size="large" class="neon-btn" style="width: 100%" @click="regenerateImage" :loading="regenLoading" :disabled="regenLoading || fileList.length === 0">
                🚀 开始再编辑（{{ unitPrice }}积分）
              </el-button>
            </el-form>
          </template>
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
              <img
                :src="img"
                class="generated-img"
                @click="openImagePreview(img)"
              />
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

    <!-- 全窗口图片预览 (Teleport 到 body) -->
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
import { analyzeImages as analyzeImagesAPI, planImagePrompts as planImagePromptsAPI, generateImage as generateImageAPI, getValueByPath } from '../../api/index'
import { Plus, ZoomIn, Download, Close, ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { saveAs } from 'file-saver'
import JSZip from 'jszip'
import HistoryPanel from '@/components/HistoryPanel.vue'
import { cacheMedia } from '@/utils/mediaCache'
import { compressImage } from '@/utils/imageCompress'

const emit = defineEmits(['refresh-points', 'log'])

// ========== Tab 切换 ==========
const activeTab = ref('generate')

// ========== 模型配置 ==========
const models = ref([])
const selectedModelId = ref('')
const currentModel = ref(null)
const costInfo = ref({ cost: 0 })  // 费用信息
const currentDeductionId = ref(null)  // 预扣ID

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

const designStyleOptions = computed(() => {
  return getUiOptions('design_style') || [
    { label: '简约 Ins 风', value: '简约 Ins 风' }, { label: '高级奢华', value: '高级奢华' },
    { label: '科技感', value: '科技感' }, { label: '清新自然', value: '清新自然' },
    { label: '赛博朋克', value: '赛博朋克' }, { label: '国潮风', value: '国潮风' }
  ]
})

const targetLangOptions = computed(() => {
  return getUiOptions('target_lang') || [
    { label: '日语', value: '日语' }, { label: '英语', value: '英语' },
    { label: '中文', value: '中文' }, { label: '韩语', value: '韩语' },
    { label: '法语', value: '法语' }, { label: '德语', value: '德语' },
    { label: '俄语', value: '俄语' }, { label: '西班牙语', value: '西班牙语' },
    { label: '阿拉伯语', value: '阿拉伯语' }, { label: '葡萄牙语', value: '葡萄牙语' },
    { label: '越南语', value: '越南语' }, { label: '泰语', value: '泰语' },
    { label: '印尼语', value: '印尼语' }, { label: '意大利语', value: '意大利语' },
    { label: '马来语', value: '马来语' }
  ]
})

const uploadMaxCount = computed(() => {
  const refField = currentModel.value?.config_schema?.ui_schema?.find(f => f.field_name === 'ref_images')
  return refField?.max_count || 5
})

// 从 ui_schema 读取字段默认值
const getUiDefault = (fieldName, fallback) => {
  const schema = currentModel.value?.config_schema?.ui_schema
  if (!schema) return fallback
  const field = schema.find(f => f.field_name === fieldName)
  return field?.default_value ?? fallback
}

// 加载图片模型列表
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

// 切换模型
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
    form.design_style = getUiDefault('design_style', '简约 Ins 风')
    form.target_lang = getUiDefault('target_lang', '中文')
    const numField = res.config_schema?.ui_schema?.find(f => f.field_name === 'num_images')
    if (numField) form.num_images = numField.default_value ?? 1

    regenForm.aspect_ratio = form.aspect_ratio
    regenForm.resolution = form.resolution

    await calculateCost()
  } catch (e) {
    console.error('加载模型详情失败', e)
  }
}

// 计算费用
const calculateCost = async () => {
  if (!currentModel.value) return

  try {
    const res = await request.post('/api/calculate-cost', {
      model_id: selectedModelId.value,
      count: form.num_images
    })
    costInfo.value = res
  } catch (e) {
    console.error('计算费用失败', e)
    const pricingRules = currentModel.value?.config_schema?.pricing_rules
    if (pricingRules?.mode === 'dynamic') {
      const basePrice = pricingRules.base_price || 0
      costInfo.value = { cost: basePrice * form.num_images }
    } else {
      const fixedPrice = pricingRules?.fixed_price || 0
      costInfo.value = { cost: fixedPrice * form.num_images }
    }
  }
}

// ========== 历史记录面板 ref ==========
const historyPanelRef = ref(null)

// ========== 商品图生成变量 ==========
const loading = ref(false)
const analyzing = ref(false)
const stopped = ref(false)
const fileList = ref([])
const imageBase64List = ref([])
const generatedImages = ref([])

// 全窗口图片预览状态
const imagePreviewVisible = ref(false)
const imagePreviewUrl = ref('')
const currentImageIndex = ref(0)

const form = reactive({
  product_type: '',
  design_style: '简约 Ins 风',
  selling_points: '',
  target_lang: '中文',
  aspect_ratio: '3:4',
  resolution: '1K',
  num_images: 1,
  seed: -1
})

// ========== 图片再生成变量 ==========
const regenLoading = ref(false)
const regenForm = reactive({
  prompt: '',
  strength: 0.6,
  aspect_ratio: '3:4',
  resolution: '1K'
})

// === 通用方法 ===
const fileToBase64 = async (file) => {
  return new Promise((resolve) => {
    const reader = new FileReader()
    reader.readAsDataURL(file.raw || file)
    reader.onload = async () => {
      // 压缩图片到 400KB 以内，最大边 2048px
      const compressed = await compressImage(reader.result, 400, 200, 2048)
      resolve(compressed)
    }
  })
}

// === 文件处理 ===
const handleFileChange = async (file, fileListRef) => {
  fileList.value = fileListRef
  imageBase64List.value = await Promise.all(fileList.value.map(f => fileToBase64(f)))
  emit('log', `已加载 ${fileList.value.length} 张参考图`)
}
const handleRemove = async (file, fileListRef) => {
  fileList.value = fileListRef
  await handleFileChange(null, fileListRef)
}

// 全窗口图片预览
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

// === Tab 1: 商品图生成 - 分析图片 ===
const analyzeImages = async () => {
  if (imageBase64List.value.length === 0) return ElMessage.warning('请先上传图片')
  analyzing.value = true
  const pType = form.product_type || "通用产品"
  const count = form.num_images || 1
  emit('log', `正在分析 ${imageBase64List.value.length} 张图片...`)
  try {
    const res = await analyzeImagesAPI({
      images: imageBase64List.value,
      product_type: pType,
      design_style: form.design_style,
      target_lang: form.target_lang,
      target_num: count
    }, currentModel.value?.config_schema)

    let content = res.choices?.[0]?.message?.content || ''
    if (content) {
      if (content.includes("Set 1:")) {
        content = content.replace(/Set \d+:/g, "").trim()
      }
      form.selling_points = content
      ElMessage.success('卖点生成成功')
    } else {
      emit('log', `分析失败: 响应格式错误`)
      ElMessage.error('分析失败')
    }
  } catch (e) {
    ElMessage.error('分析失败')
    emit('log', `网络请求错误: ${e.message || e}`)
  } finally {
    analyzing.value = false
  }
}

// === Tab 1: 商品图生成 - 生成图片 ===
const generateImage = async () => {
  if (!form.product_type || !form.selling_points) return ElMessage.warning('请填写完整信息')

  // 计算总费用
  const totalCost = unitPrice.value * form.num_images

  // 检查积分是否足够
  const userStore = (await import('@/stores/user')).useUserStore()
  if (userStore.points < totalCost) {
    return ElMessage.warning('积分不足，请充值')
  }

  // 确认扣费
  try {
    await ElMessageBox.confirm(
      `即将消耗 ${totalCost} 积分生成 ${form.num_images} 张图片，确认继续？`,
      '费用确认',
      { confirmButtonText: '确认', cancelButtonText: '取消' }
    )
  } catch {
    return
  }

  loading.value = true
  stopped.value = false
  currentDeductionId.value = null
  let successCount = 0

  // 预扣积分
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

  emit('log', `正在规划 ${form.num_images} 张图片的拍摄方案...`)
  let promptList = []

  try {
    const res = await planImagePromptsAPI({
      images: imageBase64List.value,
      product_type: form.product_type,
      selling_points: form.selling_points,
      design_style: form.design_style,
      target_lang: form.target_lang,
      num_screens: form.num_images
    }, currentModel.value?.config_schema)

    const content = res.choices?.[0]?.message?.content || ''

    try {
      let cleanContent = content.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim()

      try {
        promptList = JSON.parse(cleanContent)
        if (!Array.isArray(promptList)) {
          promptList = [String(promptList)]
        }
      } catch {
        const parts = content.split(/["']?第\d+屏["\']?[：:]/)
        promptList = parts
          .map(p => p.trim())
          .filter(p => p.length > 10)
          .map(p => {
            const mainTextMatch = p.match(/主文案[：:]["'""]([^"'""]+)["'""]/)
            const subTextMatch = p.match(/副文案[：:]["'""]([^"'""]+)["'""]/)
            const designMatch = p.match(/文案设计与排版[：:](.+?)(?=画面主体|$)/s)
            const sceneMatch = p.match(/画面主体与构图[：:](.+?)(?=画质|$)/s)
            const qualityMatch = p.match(/画质与细节[：:](.+?)$/s)

            let prompt = ''
            if (mainTextMatch) prompt += `Main text: "${mainTextMatch[1]}". `
            if (subTextMatch) prompt += `Subtitle: "${subTextMatch[1]}". `
            if (designMatch) prompt += designMatch[1].trim() + '. '
            if (sceneMatch) prompt += sceneMatch[1].trim() + '. '
            if (qualityMatch) prompt += qualityMatch[1].trim()

            return prompt || p
          })
      }
    } catch {
      promptList = content.split('\n').filter(line => line.trim().length > 20)
    }

    if (promptList.length === 0) {
      promptList = [form.selling_points]
    }

    emit('log', `方案规划完成，共 ${promptList.length} 个方案`)
    promptList.forEach((p, index) => {
      emit('log', `[方案 ${index + 1}]:\n${p}`)
    })
  } catch (e) {
    ElMessage.error('方案规划失败')
    emit('log', `规划失败: ${e.message || e}`)
    // 退还预扣积分
    if (currentDeductionId.value) {
      try {
        await request.post('/api/points/refund', {
          deduction_id: currentDeductionId.value,
          reason: '方案规划失败'
        })
        emit('log', '积分已退还')
      } catch (err) {}
    }
    loading.value = false
    return
  }

  emit('log', `开始批量渲染 (共 ${promptList.length} 张)...`)
  for (let i = 0; i < promptList.length; i++) {
    if (stopped.value) {
      emit('log', '任务已手动停止')
      break
    }
    const currentPrompt = promptList[i]
    emit('log', `[第 ${i+1}/${promptList.length} 张] 正在请求云端绘图...`)
    try {
      const res = await generateImageAPI({
        model: selectedModelId.value,
        prompt: currentPrompt,
        aspect_ratio: form.aspect_ratio,
        resolution: form.resolution,
        images: imageBase64List.value,
        seed: form.seed
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

        saveImageHistory(url, currentPrompt)
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

  loading.value = false
  stopped.value = false

  // 确认或退还积分
  if (successCount > 0) {
    // 成功，确认扣费
    if (currentDeductionId.value) {
      try {
        await request.post('/api/points/confirm', { deduction_id: currentDeductionId.value })
        emit('log', '积分扣费已确认')
        emit('refresh-points')
      } catch (e) {
        console.error('确认扣费失败', e)
      }
    }
    ElMessage.success(`任务结束，成功 ${successCount} 张`)
    emit('log', `任务全部结束`)
  } else {
    // 全部失败，退还积分
    if (currentDeductionId.value) {
      try {
        await request.post('/api/points/refund', {
          deduction_id: currentDeductionId.value,
          reason: '图片生成全部失败'
        })
        emit('log', '积分已退还')
        emit('refresh-points')
      } catch (e) {
        console.error('退还积分失败', e)
      }
    }
    emit('log', '任务失败，积分已退还')
  }
}

// === Tab 2: 图片再编辑 - 生成1张图 ===
const regenerateImage = async () => {
  if (imageBase64List.value.length === 0) return ElMessage.warning('请先上传原图')
  if (!regenForm.prompt.trim()) return ElMessage.warning('请输入修改指令')

  // 固定费用：不管上传几张图，只生成1张，扣单价
  const totalCost = unitPrice.value

  // 检查积分是否足够
  const userStore = (await import('@/stores/user')).useUserStore()
  if (userStore.points < totalCost) {
    return ElMessage.warning('积分不足，请充值')
  }

  // 确认扣费
  try {
    await ElMessageBox.confirm(
      `即将消耗 ${totalCost} 积分进行图片再编辑，确认继续？`,
      '费用确认',
      { confirmButtonText: '确认', cancelButtonText: '取消' }
    )
  } catch {
    return
  }

  regenLoading.value = true
  currentDeductionId.value = null

  // 预扣积分
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
    regenLoading.value = false
    return
  }

  emit('log', `开始图片再编辑（${imageBase64List.value.length}张参考图）...`)

  try {
    // 调用生成 API，传入所有图片作为参考，生成1张
    const res = await generateImageAPI({
      model: selectedModelId.value,
      prompt: regenForm.prompt,
      aspect_ratio: regenForm.aspect_ratio,
      resolution: regenForm.resolution,
      images: imageBase64List.value,  // 传入所有参考图
      seed: Date.now()
    }, currentModel.value?.config_schema)

    const resultPath = currentModel.value?.config_schema?.response_mapping?.result_url_path
    const url = (resultPath ? getValueByPath(res, resultPath) : null) || res.data?.[0]?.url || res.data?.url
    if (url) {
      generatedImages.value.unshift(url)
      emit('log', `图片再编辑成功！`)

      try {
        const response = await fetch(url)
        if (response.ok) {
          const blob = await response.blob()
          await cacheMedia(url, blob, 'image')
        }
      } catch (e) {
        console.warn('缓存图片失败', e)
      }

      saveImageHistory(url, regenForm.prompt)

      // 确认扣费
      if (currentDeductionId.value) {
        await request.post('/api/points/confirm', { deduction_id: currentDeductionId.value })
        emit('log', '积分扣费已确认')
        emit('refresh-points')
      }
      ElMessage.success('图片再编辑完成')
    } else {
      ElMessage.error('生成失败')
      emit('log', `服务端拒绝: ${JSON.stringify(res)}`)
      // 退还积分
      if (currentDeductionId.value) {
        await request.post('/api/points/refund', {
          deduction_id: currentDeductionId.value,
          reason: '图片再编辑失败'
        })
        emit('log', '积分已退还')
        emit('refresh-points')
      }
    }
  } catch (e) {
    let errMsg = e.message || '未知错误'
    if (errMsg.includes('timeout')) errMsg = '请求超时(后端仍在运行)'
    ElMessage.error('请求出错')
    emit('log', `异常: ${errMsg}`)
    // 退还积分
    if (currentDeductionId.value) {
      try {
        await request.post('/api/points/refund', {
          deduction_id: currentDeductionId.value,
          reason: '图片再编辑异常'
        })
        emit('log', '积分已退还')
        emit('refresh-points')
      } catch (err) {}
    }
  }

  regenLoading.value = false
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
        aspect_ratio: activeTab.value === 'generate' ? form.aspect_ratio : regenForm.aspect_ratio,
        resolution: activeTab.value === 'generate' ? form.resolution : regenForm.resolution
      },
      result_url: resultUrl,
      cost_points: costInfo.value.cost || unitPrice.value
    })

    if (historyPanelRef.value) {
      historyPanelRef.value.refresh()
    }
  } catch (e) {
    console.error('保存历史记录失败', e)
  }
}

const stopTask = () => { stopped.value = true; loading.value = false; emit('log', '用户请求停止任务...'); ElMessage.info('已请求停止后续任务') }
const downloadSingleImage = (url, suffix) => { const fileName = `Product_${Date.now()}_${suffix}.png`; saveAs(url, fileName) }
const downloadAllImages = async () => { const zip = new JSZip(); const folder = zip.folder("images"); emit('log', '正在打包下载所有图片...')
  try { for (let i = 0; i < generatedImages.value.length; i++) { const url = generatedImages.value[i]; const fileName = `Product_${i + 1}.png`; const response = await fetch(url); const blob = await response.blob(); folder.file(fileName, blob) } zip.generateAsync({ type: "blob" }).then((content) => { saveAs(content, `Batch_Images_${Date.now()}.zip`); emit('log', '打包下载完成') }) } catch (e) { emit('log', `打包失败: ${e}`); ElMessage.error('打包下载失败') } }
const SESSION_KEY = 'image_tool_data'; const saveStateToSession = () => { sessionStorage.setItem(SESSION_KEY, JSON.stringify({ form, regenForm, images: generatedImages.value, activeTab: activeTab.value })) }; const restoreStateFromSession = () => { const data = sessionStorage.getItem(SESSION_KEY); if (data) { try { const parsed = JSON.parse(data); Object.assign(form, parsed.form); Object.assign(regenForm, parsed.regenForm || {}); generatedImages.value = parsed.images || []; if (parsed.activeTab) activeTab.value = parsed.activeTab } catch (e) {} } }; watch(form, saveStateToSession, { deep: true }); watch(regenForm, saveStateToSession, { deep: true }); watch(generatedImages, saveStateToSession, { deep: true }); watch(activeTab, saveStateToSession); watch(() => form.num_images, () => { calculateCost() }); onMounted(() => { loadModels(); restoreStateFromSession() })
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

/* Tab 按钮样式 - 大标签页效果 */
.tab-buttons {
  display: flex;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.tab-btn {
  padding: 10px 20px;
  font-size: 14px;
  font-weight: 600;
  color: #a0aec0;
  cursor: pointer;
  transition: all 0.3s;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  white-space: nowrap;
}
.tab-btn:last-child {
  border-right: none;
}
.tab-btn:hover {
  color: #00f260;
  background: rgba(255, 255, 255, 0.05);
}
.tab-btn.active {
  background: rgba(255, 255, 255, 0.1);
  color: #00f260;
  box-shadow: inset 0 -2px 0 #00f260;
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
:deep(.el-select__selected-item) { color: #fff !important; }
:deep(.el-form-item__label) { color: #a0aec0 !important; }

:deep(.el-upload--picture-card), :deep(.el-upload-dragger) {
  background-color: rgba(0, 0, 0, 0.3) !important;
  border: 1px dashed rgba(255, 255, 255, 0.3) !important;
  color: #a0aec0 !important;
  border-radius: 8px !important;
}
:deep(.el-upload--picture-card:hover) { border-color: #0575e6 !important; color: #fff !important; }

/* 拖拽上传区域内部 */
:deep(.el-upload-dragger) {
  background-color: transparent !important;
  border: none !important;
}

/* 已上传图片列表项 */
:deep(.el-upload-list--picture-card .el-upload-list__item) {
  background-color: rgba(0, 0, 0, 0.3) !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  border-radius: 8px !important;
}

/* 删除按钮样式 */
:deep(.el-upload-list__item-delete),
:deep(.el-upload-list__item-status-label) {
  background-color: rgba(0, 0, 0, 0.5) !important;
}

/* Slider 样式 */
.cyber-slider {
  padding: 0 10px;
}
:deep(.el-slider__runway) {
  background-color: rgba(255, 255, 255, 0.1) !important;
}
:deep(.el-slider__bar) {
  background: linear-gradient(90deg, #00f260, #0575e6) !important;
}
:deep(.el-slider__button) {
  border-color: #00f260 !important;
}
:deep(.el-input-number__decrease),
:deep(.el-input-number__increase) {
  background: transparent !important;
}
.slider-hint {
  font-size: 12px;
  color: #a0aec0;
  margin-top: 5px;
}

/* 4. 按钮 & 文本 */
.gradient-text { font-size: 18px; font-weight: 800; background: linear-gradient(90deg, #00f260, #0575e6); -webkit-background-clip: text; color: transparent; text-shadow: 0 0 10px rgba(5, 117, 230, 0.3); }
.label-box { display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 5px; }
.label-text { font-weight: bold; color: #e2e8f0; }

.neon-btn { background: linear-gradient(90deg, #7f00ff, #e100ff) !important; border: none; box-shadow: 0 4px 15px rgba(127, 0, 255, 0.4); color: #fff; }
.neon-btn:hover { opacity: 0.9; }
.optimize-btn {
  background: transparent !important;
  border: 1px solid #e6a23c !important;
  color: #e6a23c !important;
  font-size: 14px !important;
  font-weight: 600 !important;
}
.stop-btn { background: #ff0055 !important; border: none !important; box-shadow: 0 4px 15px rgba(255, 0, 85, 0.4); color: #fff; }
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
.image-slot { display: flex; justify-content: center; align-items: center; width: 100%; height: 150px; background: rgba(255,255,255,0.05); color: #718096; font-size: 12px; }

/* 6. 响应式布局间距 */
@media screen and (max-width: 768px) {
  .right-panel-col {
    margin-top: 20px;
  }
  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }
  .tab-buttons {
    width: 100%;
    margin-top: 10px;
  }
  .tab-btn {
    flex: 1;
    text-align: center;
    padding: 10px 10px;
    font-size: 13px;
  }
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
  background: rgba(255, 255, 255, 0.1) !important; color: #fff !important;
}
.cyber-popper .el-select-dropdown__item.is-selected { color: #00f260 !important; font-weight: bold; }

/* 全窗口图片预览样式 (Teleport 到 body，不用 scoped) */
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
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  color: #fff;
  font-size: 24px;
}

.preview-close-btn:hover {
  background: rgba(255, 80, 80, 0.5);
  border-color: rgba(255, 80, 80, 0.8);
}

.preview-nav {
  position: absolute;
  bottom: 30px;
  display: flex;
  align-items: center;
  gap: 20px;
}

.nav-btn {
  background: rgba(255, 255, 255, 0.1) !important;
  border: 1px solid rgba(255, 255, 255, 0.2) !important;
  color: #fff !important;
  width: 44px;
  height: 44px;
}

.nav-btn:hover:not(:disabled) {
  background: rgba(0, 242, 96, 0.3) !important;
  border-color: #00f260 !important;
}

.nav-btn:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.preview-counter {
  color: #fff;
  font-size: 16px;
  font-weight: 500;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>