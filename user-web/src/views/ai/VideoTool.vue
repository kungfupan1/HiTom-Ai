<template>
  <div class="video-tool">
    <el-row :gutter="20">
      <el-col :xs="24" :sm="24" :md="11" :lg="11">
        <el-card class="cyber-glass" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="gradient-text">🎬 视频生成控制台</span>
              <el-tag effect="dark" round color="#ff0055" style="border:none; box-shadow: 0 0 10px rgba(255,0,85,0.4)">{{ currentModel?.config_schema?.model_info?.display_name || currentModel?.display_name || 'AI视频' }}</el-tag>
            </div>
          </template>

          <el-form :model="dynamicFormData" label-position="top">
            <!-- 动态模型选择 -->
            <el-form-item label="生成模型">
              <el-select v-model="selectedModelId" style="width: 100%" class="cyber-select" popper-class="cyber-popper" @change="onModelChange">
                <el-option v-for="m in models" :key="m.model_id" :value="m.model_id" :label="m.config_schema?.model_info?.display_name || m.display_name" />
              </el-select>
            </el-form-item>

            <!-- ===== 动态渲染 UI Schema ===== -->
            <template v-for="field in uiSchema" :key="field.field_name">
              <!-- 跳过模型ID字段，已在上方显示 -->
              <template v-if="field.field_name !== 'model' && field.field_name !== 'images'">
                <!-- input 类型 -->
                <el-form-item v-if="field.ui_type === 'input'" :label="field.label + (field.required ? ' (必填)' : '')">
                  <el-input
                    v-model="dynamicFormData[field.field_name]"
                    :placeholder="field.placeholder || ''"
                    class="cyber-input"
                  />
                </el-form-item>

                <!-- textarea 类型 (核心卖点) -->
                <template v-else-if="field.ui_type === 'textarea'">
                  <div class="label-box">
                    <span class="label-text">{{ field.label }}{{ field.required ? ' (必填)' : '' }}</span>
                    <el-tooltip v-if="field.field_name === 'selling_points'" content="请先在下方上传图片，然后点击此按钮" placement="top" :disabled="fileList.length > 0">
                      <el-button type="primary" plain round size="small" class="optimize-btn" @click="analyzeImages" :loading="analyzing" :disabled="fileList.length === 0">
                        {{ analyzing ? '正在分析...' : '✨ 看图自动生成文案' }}
                      </el-button>
                    </el-tooltip>
                  </div>
                  <el-form-item>
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
                </template>
              </template>
            </template>

            <!-- 参考图片上传 (紧跟核心卖点下方) -->
            <el-form-item label="参考图片 (最多5张，支持拖拽)">
              <el-upload
                action="#"
                list-type="picture-card"
                :auto-upload="false"
                :limit="5"
                :on-change="handleFileChange"
                :on-remove="handleRemove"
                multiple
                drag
                class="cyber-upload"
              >
                <el-icon><Plus /></el-icon>
              </el-upload>
            </el-form-item>

            <!-- 其他参数：一行2个布局 -->
            <template v-for="(group, idx) in optionFieldGroups" :key="idx">
              <el-row :gutter="10">
                <el-col v-for="field in group" :key="field.field_name" :span="12">
                  <!-- select 类型 -->
                  <el-form-item v-if="field.ui_type === 'select'" :label="field.label">
                    <el-select
                      v-model="dynamicFormData[field.field_name]"
                      style="width: 100%"
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
                      style="width: 100%"
                      class="cyber-input-number"
                      @change="field.affects_pricing ? calculateCost() : null"
                    />
                  </el-form-item>

                  <!-- switch 类型 -->
                  <el-form-item v-else-if="field.ui_type === 'switch'" :label="field.label">
                    <el-switch
                      v-model="dynamicFormData[field.field_name]"
                      :active-text="field.active_text || '是'"
                      :inactive-text="field.inactive_text || '否'"
                      inline-prompt
                      style="--el-switch-on-color: #00f260; --el-switch-off-color: #444;"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
            </template>

            <el-button type="primary" size="large" style="width: 100%" class="neon-btn" @click="submitTask" :loading="loading" :disabled="loading || !canGenerate">
              {{ loading ? '生成中...' : `🚀 立即生成 (消耗${costInfo.cost}积分)` }}
            </el-button>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="24" :md="13" :lg="13" class="right-panel-col">
        <el-card class="cyber-glass" shadow="never">
          <template #header>
             <span class="gradient-text">🎥 任务看板</span>
          </template>

          <div v-if="!taskStatus && !videoUrl" class="empty-state">
            <div class="placeholder-icon">🎞️</div>
            <p>暂无任务，请在左侧提交</p>
          </div>

          <div v-if="taskStatus === 'processing'" class="processing-state">
            <el-progress type="dashboard" :percentage="progress" color="#00f260" :stroke-width="10" />
            <p style="margin-top: 20px; font-weight: bold; color: #fff;">正在渲染视频...</p>
            <p style="color: #a0aec0; font-size: 12px;">(视频生成较慢，请耐心等待)</p>
          </div>

          <div v-if="videoUrl" class="result-state">
            <el-alert title="生成成功！" type="success" show-icon style="margin-bottom: 20px; background: rgba(0,242,96,0.1); border-color: #00f260; color: #00f260;" />
            <!-- 缩略预览（点击放大） -->
            <div class="video-preview-wrapper" @click="openVideoPreview">
              <video
                ref="videoPlayerRef"
                :src="videoUrl"
                preload="metadata"
                class="video-preview-thumb"
                muted
              ></video>
              <div class="play-overlay">
                <span class="play-icon">▶</span>
                <span class="play-text">点击预览</span>
              </div>
            </div>
            <div style="margin-top: 20px; text-align: center;">
               <el-button type="success" size="large" class="cyber-action-btn" tag="a" :href="videoUrl" target="_blank">⬇️ 下载视频文件</el-button>
            </div>
          </div>
        </el-card>

        <!-- 历史记录面板 -->
        <HistoryPanel ref="historyPanelRef" fixed-type="video" />
      </el-col>
    </el-row>

    <!-- 全屏视频预览弹窗 -->
    <Teleport to="body">
      <transition name="fade">
        <div v-if="videoPreviewVisible" class="fullscreen-video-preview" @click="closeVideoPreview">
          <div class="preview-close-btn" @click="closeVideoPreview">
            <el-icon><Close /></el-icon>
          </div>
          <video
            :src="videoUrl"
            controls
            autoplay
            class="fullscreen-video"
            @click.stop
          ></video>
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup>
import { Plus, Close } from '@element-plus/icons-vue'
import { reactive, ref, computed, onMounted, onUnmounted, watch } from 'vue'
import request from '@/api/request'
import { generateVideo, getVideoStatus, analyzeImages as analyzeImagesAPI, generateVideoScript, getPricingInfo, submitTask as submitTaskAPI, getTaskStatus as getDirectTaskStatus, confirmTask, refundTask } from '@/api/index'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import HistoryPanel from '@/components/HistoryPanel.vue'
import { cacheMedia } from '@/utils/mediaCache'
import { compressImage } from '@/utils/imageCompress'

const emit = defineEmits(['refresh-points', 'log'])
const userStore = useUserStore()

// ========== 历史记录面板 ref ==========
const historyPanelRef = ref(null)

// ========== 视频播放器 ref ==========
const videoPlayerRef = ref(null)

// ========== 状态 ==========
const loading = ref(false)
const analyzing = ref(false)
const taskId = ref('')
const taskStatus = ref('')
const progress = ref(0)
const videoUrl = ref('')
const fileList = ref([])
const imageBase64List = ref([])
const currentDeductionId = ref(null)
const videoScriptPrompt = ref('')  // 视频脚本提示词配置

// ========== 视频预览弹窗 ==========
const videoPreviewVisible = ref(false)

// ========== 模型相关 ==========
const models = ref([])
const currentModel = ref(null)
const selectedModelId = ref('')

// ========== 动态表单数据 ==========
const dynamicFormData = reactive({})

// 计算属性：UI Schema
const uiSchema = computed(() => {
  return currentModel.value?.config_schema?.ui_schema || []
})

// 计算属性：选项类型字段（select、input-number），用于一行2个布局
const optionFields = computed(() => {
  return uiSchema.value.filter(f =>
    f.field_name !== 'model' &&
    f.field_name !== 'images' &&
    (f.ui_type === 'select' || f.ui_type === 'input-number' || f.ui_type === 'switch')
  )
})

// 计算属性：选项字段分组（每2个一组）
const optionFieldGroups = computed(() => {
  const groups = []
  for (let i = 0; i < optionFields.value.length; i += 2) {
    groups.push(optionFields.value.slice(i, i + 2))
  }
  return groups
})

// ========== 费用计算 ==========
const costInfo = ref({ cost: 0, breakdown: null })

const canGenerate = computed(() => {
  // 检查必填字段
  const requiredFields = uiSchema.value.filter(f => f.required).map(f => f.field_name)
  const hasAllRequired = requiredFields.every(f => dynamicFormData[f])
  return selectedModelId.value && hasAllRequired && costInfo.value.cost > 0
})

// ========== 加载模型 ==========
const loadModels = async () => {
  try {
    // 并行加载模型列表和系统配置
    const [res, config] = await Promise.all([
      request.get('/api/models?model_type=video'),
      getPricingInfo()
    ])

    models.value = res
    videoScriptPrompt.value = config.video_script_prompt || ''

    if (res.length > 0) {
      selectedModelId.value = res[0].model_id
      await onModelChange()
    }
  } catch (e) {
    console.error('加载模型失败', e)
    ElMessage.error('加载模型失败')
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

    // ===== 防呆逻辑：检查旧值是否在新 options 内 =====
    schema.forEach(field => {
      const oldValue = dynamicFormData[field.field_name]

      if (field.ui_type === 'select' && field.options) {
        const validValues = field.options.map(o => o.value)
        if (oldValue === undefined || !validValues.includes(oldValue)) {
          // 不合法，覆盖为默认值
          dynamicFormData[field.field_name] = field.default_value ?? validValues[0]
        }
      } else if (field.ui_type === 'input-number') {
        // 数字类型校验
        const num = Number(oldValue)
        if (isNaN(num) || num < (field.min || 1) || num > (field.max || 10)) {
          dynamicFormData[field.field_name] = field.default_value ?? field.min ?? 1
        }
      } else {
        // 其他类型直接使用默认值
        if (oldValue === undefined) {
          dynamicFormData[field.field_name] = field.default_value ?? ''
        }
      }
    })

    await calculateCost()
  } catch (e) {
    console.error('加载模型详情失败', e)
  }
}

// ========== 费用计算 ==========
const calculateCost = async () => {
  if (!selectedModelId.value) return

  try {
    const res = await request.post('/api/calculate-cost', {
      model_id: selectedModelId.value,
      duration: dynamicFormData.duration,
      resolution: dynamicFormData.resolution,
      ratio: dynamicFormData.aspect_ratio,
      count: 1
    })
    costInfo.value = res
  } catch (e) {
    console.error('计算费用失败', e)
    // 使用 config_schema 中的计费规则（简化版备用逻辑）
    const pricingRules = currentModel.value?.config_schema?.pricing_rules
    if (pricingRules?.mode === 'dynamic') {
      // 动态加价模式: base_price + add_price
      let total = pricingRules.base_price || 0
      const addPrice = pricingRules.add_price || {}

      // 时长加价
      const duration = dynamicFormData.duration
      if (addPrice.duration && duration) {
        total += addPrice.duration[String(duration)] || 0
      }
      // 分辨率加价
      const resolution = dynamicFormData.resolution
      if (addPrice.resolution && resolution) {
        total += addPrice.resolution[resolution] || 0
      }
      // 比例加价
      const aspectRatio = dynamicFormData.aspect_ratio
      if (addPrice.aspect_ratio && aspectRatio) {
        total += addPrice.aspect_ratio[aspectRatio] || 0
      }

      costInfo.value = { cost: total }
    } else {
      // 固定价格模式: fixed_price
      const fixedPrice = pricingRules?.fixed_price || 0
      costInfo.value = { cost: fixedPrice }
    }
  }
}

// ========== 文件处理 ==========
const handleFileChange = async (uploadFile, uploadFiles) => {
  fileList.value = uploadFiles
  await convertImagesToBase64()
}

const handleRemove = async (file, uploadFiles) => {
  fileList.value = uploadFiles
  await convertImagesToBase64()
}

const convertImagesToBase64 = async () => {
  imageBase64List.value = []
  for (const file of fileList.value) {
    const reader = new FileReader()
    const base64 = await new Promise((resolve, reject) => {
      reader.readAsDataURL(file.raw)
      reader.onload = () => resolve(reader.result)
      reader.onerror = reject
    })
    // 压缩图片到 400KB 以内，最大边 2048px
    const compressed = await compressImage(base64, 400, 200, 2048)
    imageBase64List.value.push(compressed)
  }
}

// ========== 图片分析 ==========
const analyzeImages = async () => {
  if (imageBase64List.value.length === 0) return ElMessage.warning('请先上传图片')
  analyzing.value = true
  emit('log', '开始分析图片...')

  try {
    // 通过腾讯云函数代理调用 ModelScope
    const res = await analyzeImagesAPI({
      images: imageBase64List.value,
      product_type: dynamicFormData.product_type || '通用产品',
      design_style: dynamicFormData.style || '简约风格',
      target_lang: dynamicFormData.language || '中文',
      target_num: 1
    })

    // 解析响应
    const content = res.choices?.[0]?.message?.content || ''
    if (content) {
      dynamicFormData.selling_points = content
      ElMessage.success('文案生成成功！')
      emit('log', '文案生成成功！')
    } else {
      ElMessage.error('分析失败: 响应格式错误')
      emit('log', '分析失败: 响应格式错误')
    }
  } catch (e) {
    console.error('分析失败', e)
    ElMessage.error('分析失败: ' + (e.message || '未知错误'))
    emit('log', '分析失败: ' + (e.message || '未知错误'))
  } finally {
    analyzing.value = false
  }
}

// ========== 提交任务 ==========
const submitTask = async () => {
  // 检查必填字段
  const requiredFields = uiSchema.value.filter(f => f.required).map(f => f.field_name)
  for (const f of requiredFields) {
    if (!dynamicFormData[f]) {
      return ElMessage.warning(`请填写 ${uiSchema.value.find(u => u.field_name === f)?.label || f}`)
    }
  }

  if (userStore.points < costInfo.value.cost) {
    return ElMessage.warning('积分不足，请充值')
  }

  try {
    await ElMessageBox.confirm(
      `即将消耗 ${costInfo.value.cost} 积分生成视频，确认继续？`,
      '费用确认',
      { confirmButtonText: '确认', cancelButtonText: '取消' }
    )
  } catch {
    return
  }

  loading.value = true
  taskStatus.value = 'processing'
  progress.value = 5
  videoUrl.value = ''
  currentDeductionId.value = null

  emit('log', '开始视频生成任务...')

  // 判断是否使用后端直接调用模式
  const useCloudFunction = currentModel.value?.use_cloud_function !== false

  if (!useCloudFunction) {
    // ========== 后端直接调用模式 ==========
    emit('log', '使用后端直接调用模式...')
    await submitDirectMode()
  } else {
    // ========== 云函数代理模式（原有逻辑）==========
    emit('log', '使用云函数代理模式...')
    await submitCloudFunctionMode()
  }
}

// ========== 云函数代理模式（原有逻辑）==========
const submitCloudFunctionMode = async () => {
  try {
    // 步骤1: 预扣积分
    emit('log', '步骤1: 预扣积分...')
    const reserveRes = await request.post('/api/points/reserve', {
      amount: costInfo.value.cost,
      model_id: selectedModelId.value
    })
    currentDeductionId.value = reserveRes.deduction_id
    emit('log', `预扣成功，deduction_id: ${currentDeductionId.value}`)

    // 步骤2: 调用 AI 生成视频脚本
    emit('log', '步骤2: 调用 AI 生成视频脚本...')

    const scriptData = {
      images: imageBase64List.value,
      product_type: dynamicFormData.product_type,
      selling_points: dynamicFormData.selling_points,
      style: dynamicFormData.style,
      language: dynamicFormData.language,
      region: dynamicFormData.region,
      category: dynamicFormData.category,
      subtitle: dynamicFormData.subtitle !== false
    }

    const scriptRes = await generateVideoScript(scriptData, videoScriptPrompt.value)
    const videoScript = scriptRes?.choices?.[0]?.message?.content || ''

    if (!videoScript) {
      throw new Error('视频脚本生成失败，请重试')
    }

    // 打印生成的脚本到日志窗口
    emit('log', '===== AI 生成的视频脚本 =====')
    emit('log', videoScript)
    emit('log', '=============================')

    // 步骤3: 调用视频生成 API
    emit('log', `步骤3: 调用 ${selectedModelId.value} 生成视频...`)
    const videoRes = await generateVideo({
      model: selectedModelId.value,
      prompt: videoScript,  // 使用 AI 生成的脚本作为 prompt
      duration: dynamicFormData.duration,
      ratio: dynamicFormData.aspect_ratio,
      resolution: dynamicFormData.resolution,
      images: imageBase64List.value
    }, currentModel.value?.config_schema)  // 传入模型配置，使用 request_mapping

    const actualTaskId = videoRes?.data?.task_id || videoRes?.task_id
    if (!actualTaskId) throw new Error('未获取到任务ID')

    taskId.value = actualTaskId
    emit('log', `任务已提交，task_id: ${taskId.value}`)

    // 步骤4: 确认扣费
    await request.post('/api/points/confirm', { deduction_id: currentDeductionId.value })
    emit('log', '积分扣费已确认')

    userStore.refreshPoints()
    emit('refresh-points')

    // 步骤5: 开始轮询
    emit('log', '开始轮询生成状态...')
    startStatusPolling()

    ElMessage.success('视频生成任务已提交')
  } catch (e) {
    // 失败退款
    if (currentDeductionId.value) {
      try {
        await request.post('/api/points/refund', {
          deduction_id: currentDeductionId.value,
          reason: '提交任务失败'
        })
        emit('log', '积分已退还')
      } catch (err) {}
    }
    emit('log', `错误: ${e.message || '提交失败'}`)
    ElMessage.error(e.message || '提交失败')
    loading.value = false
    taskStatus.value = ''
  }
}

// ========== 后端直接调用模式（新增）==========
const submitDirectMode = async () => {
  try {
    // 步骤1: 调用 AI 生成视频脚本（仍然使用云函数代理）
    emit('log', '步骤1: 调用 AI 生成视频脚本...')

    const scriptData = {
      images: imageBase64List.value,
      product_type: dynamicFormData.product_type,
      selling_points: dynamicFormData.selling_points,
      style: dynamicFormData.style,
      language: dynamicFormData.language,
      region: dynamicFormData.region,
      category: dynamicFormData.category,
      subtitle: dynamicFormData.subtitle !== false
    }

    const scriptRes = await generateVideoScript(scriptData, videoScriptPrompt.value)
    const videoScript = scriptRes?.choices?.[0]?.message?.content || ''

    if (!videoScript) {
      throw new Error('视频脚本生成失败，请重试')
    }

    // 打印生成的脚本到日志窗口
    emit('log', '===== AI 生成的视频脚本 =====')
    emit('log', videoScript)
    emit('log', '=============================')

    // 步骤2: 提交任务到后端（后端会自动预扣积分）
    emit('log', '步骤2: 提交任务到后端...')
    const submitResult = await submitTaskAPI({
      model_id: selectedModelId.value,
      prompt: videoScript,
      images: imageBase64List.value,
      params: {
        duration: dynamicFormData.duration,
        aspect_ratio: dynamicFormData.aspect_ratio,
        resolution: dynamicFormData.resolution
      }
    })

    if (submitResult.mode !== 'direct') {
      // 如果后端返回的是云函数模式，回退到云函数逻辑
      emit('log', '后端返回云函数模式，切换...')
      loading.value = false
      taskStatus.value = ''
      return await submitCloudFunctionMode()
    }

    taskId.value = submitResult.task_id
    currentDeductionId.value = submitResult.deduction_id
    emit('log', `任务已提交，task_id: ${taskId.value}`)
    emit('log', `预计等待时间: ${submitResult.estimated_time || 300}秒`)

    userStore.refreshPoints()
    emit('refresh-points')

    // 步骤3: 开始轮询（后端直接模式）
    emit('log', '开始轮询生成状态...')
    startDirectModePolling()

    ElMessage.success('视频生成任务已提交')
  } catch (e) {
    emit('log', `错误: ${e.message || '提交失败'}`)
    ElMessage.error(e.message || '提交失败')
    loading.value = false
    taskStatus.value = ''
  }
}

// ========== 后端直接模式轮询 ==========
let directModeTimer = null
let directModeAttempts = 0
const DIRECT_MODE_CONFIG = {
  interval: 30000,      // 30秒轮询间隔
  maxAttempts: 20       // 最大20次 = 10分钟
}

const startDirectModePolling = () => {
  stopDirectModePolling()
  directModeAttempts = 0

  directModeTimer = setInterval(async () => {
    directModeAttempts++

    if (directModeAttempts > DIRECT_MODE_CONFIG.maxAttempts) {
      // 超时
      clearInterval(directModeTimer)
      taskStatus.value = 'timeout'
      loading.value = false
      emit('log', '任务超时，正在退还积分...')

      try {
        await refundTask(taskId.value)
        userStore.refreshPoints()
        emit('refresh-points')
        emit('log', '积分已退还')
        ElMessage.warning('生成超时，积分已退还')
      } catch (e) {
        emit('log', '退还积分失败: ' + (e.message || '未知错误'))
      }
      return
    }

    try {
      const result = await getDirectTaskStatus(taskId.value)

      if (!result.success) {
        emit('log', `状态查询失败: ${result.error || '未知错误'}`)
        return
      }

      const task = result.task
      const status = task?.status

      emit('log', `轮询 #${directModeAttempts}: 状态=${status}`)

      // 更新进度
      if (task?.progress) {
        progress.value = Math.min(99, parseInt(task.progress))
      }

      if (status === 'success') {
        // 成功
        clearInterval(directModeTimer)
        progress.value = 100
        videoUrl.value = task.result_url
        taskStatus.value = 'success'
        loading.value = false

        // 确认扣费
        try {
          await confirmTask(taskId.value)
          emit('log', '扣费已确认')
        } catch (e) {
          emit('log', '确认扣费失败（可能已确认）')
        }

        userStore.refreshPoints()
        emit('refresh-points')
        ElMessage.success('视频生成完成！')

        // 缓存视频
        try {
          const response = await fetch(task.result_url)
          if (response.ok) {
            const blob = await response.blob()
            await cacheMedia(task.result_url, blob, 'video')
          }
        } catch (e) {
          console.warn('缓存视频失败', e)
        }

        // 保存历史记录
        saveHistory(task.result_url)
      }
      else if (status === 'failed' || status === 'timeout') {
        // 失败/超时
        clearInterval(directModeTimer)
        taskStatus.value = 'fail'
        loading.value = false

        if (result.refunded) {
          emit('log', '任务失败，积分已自动退还')
          ElMessage.error('生成失败，积分已退还')
        } else {
          emit('log', '任务失败，正在退还积分...')
          try {
            await refundTask(taskId.value)
            emit('log', '积分已退还')
            ElMessage.error('生成失败，积分已退还')
          } catch (e) {
            emit('log', '退还积分失败: ' + (e.message || '未知错误'))
          }
        }

        userStore.refreshPoints()
        emit('refresh-points')
      }
      // 其他状态继续轮询
    } catch (e) {
      emit('log', `轮询异常: ${e.message || '未知错误'}`)
    }
  }, DIRECT_MODE_CONFIG.interval)
}

const stopDirectModePolling = () => {
  if (directModeTimer) {
    clearInterval(directModeTimer)
    directModeTimer = null
  }
}

// ========== 状态轮询（使用 response_mapping 解析）==========
let statusTimer = null
let errorCount = 0

const startStatusPolling = () => {
  stopStatusPolling()
  errorCount = 0

  const responseMapping = currentModel.value?.config_schema?.response_mapping || {}
  const pollingConfig = currentModel.value?.config_schema?.polling_config || { interval: 15000 }

  statusTimer = setInterval(async () => {
    try {
      const res = await getVideoStatus(taskId.value, selectedModelId.value)

      // ===== 使用 response_mapping 提取状态 =====
      const statusPath = responseMapping.status_path || 'status'
      const progressPath = responseMapping.progress_path || 'progress'
      const resultUrlPath = responseMapping.result_url_path || 'data.output'
      const errorPath = responseMapping.error_path || 'fail_reason'

      // 解析 JSON Path
      const apiStatus = getJsonValue(res, statusPath) || 'pending'
      const rawStatus = String(apiStatus).toLowerCase()
      const errMsg = getJsonValue(res, errorPath) || '未知错误'
      const prog = getJsonValue(res, progressPath) || 0

      progress.value = Math.min(99, parseInt(prog))

      // 状态映射
      const statusMapping = responseMapping.status_mapping || {
        success: ['success', 'completed', 'succeeded'],
        processing: ['processing', 'pending', 'running'],
        failed: ['failed', 'error', 'failure', 'rejected', 'canceled']
      }

      if (statusMapping.success?.some(s => rawStatus.includes(s))) {
        clearInterval(statusTimer)
        progress.value = 100
        const resultUrl = getJsonValue(res, resultUrlPath)
        videoUrl.value = resultUrl
        taskStatus.value = 'success'
        loading.value = false
        ElMessage.success('视频生成完成！')

        // 缓存视频
        try {
          const response = await fetch(resultUrl)
          if (response.ok) {
            const blob = await response.blob()
            await cacheMedia(resultUrl, blob, 'video')
          }
        } catch (e) {
          console.warn('缓存视频失败', e)
        }

        // 保存生成历史记录
        saveHistory(resultUrl)
      }
      else if (statusMapping.failed?.some(s => rawStatus.includes(s)) || (errMsg && errMsg !== '未知错误' && errMsg.includes('失败'))) {
        clearInterval(statusTimer)
        taskStatus.value = 'fail'
        loading.value = false
        ElMessage.error('任务生成失败: ' + errMsg)
        emit('log', `任务失败: ${errMsg}`)

        // 自动退款
        if (currentDeductionId.value) {
          try {
            await request.post('/api/points/refund', {
              deduction_id: currentDeductionId.value,
              reason: '视频生成失败: ' + errMsg
            })
            userStore.refreshPoints()
            emit('refresh-points')
            emit('log', '积分已自动退还')
          } catch (err) {}
        }
      } else {
        errorCount = 0
      }

      if (errorCount >= 5) {
        clearInterval(statusTimer)
        taskStatus.value = 'fail'
        loading.value = false
        ElMessage.error('无法解析任务状态')
      }
    } catch (e) {
      console.error('状态查询异常', e)
      errorCount++
      if (errorCount >= 5) {
        clearInterval(statusTimer)
        taskStatus.value = 'fail'
        loading.value = false
        ElMessage.error('查询状态网络异常')
      }
    }
  }, pollingConfig.interval || 15000)
}

// JSON Path 解析工具
const getJsonValue = (obj, path) => {
  if (!path || !obj) return null

  // 处理简单的点分隔路径，如 "data.output"
  const keys = path.split('.')
  let value = obj

  for (const key of keys) {
    // 处理数组索引，如 "data[0].url"
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

const stopStatusPolling = () => {
  if (statusTimer) {
    clearInterval(statusTimer)
    statusTimer = null
  }
}

// ========== 视频预览弹窗 ==========
const openVideoPreview = () => {
  videoPreviewVisible.value = true
  document.body.style.overflow = 'hidden'
}

const closeVideoPreview = () => {
  videoPreviewVisible.value = false
  document.body.style.overflow = ''
}

// ========== 保存历史记录 ==========
const saveHistory = async (resultUrl) => {
  try {
    // 构建 prompt 摘要
    const promptSummary = `产品: ${dynamicFormData.product_type || ''}\n卖点: ${dynamicFormData.selling_points || ''}`

    await request.post('/api/history', {
      task_type: 'video',
      model_id: selectedModelId.value,
      task_id: taskId.value,
      status: 'success',
      prompt_summary: promptSummary,
      params_json: {
        duration: dynamicFormData.duration,
        resolution: dynamicFormData.resolution,
        aspect_ratio: dynamicFormData.aspect_ratio
      },
      result_url: resultUrl,
      cost_points: costInfo.value.cost
    })

    // 刷新历史记录面板
    if (historyPanelRef.value) {
      historyPanelRef.value.refresh()
    }

    emit('log', '历史记录已保存')
  } catch (e) {
    console.error('保存历史记录失败', e)
    // 不影响用户体验，静默失败
  }
}

// ========== 生命周期 ==========
onMounted(() => {
  loadModels()
})

onUnmounted(() => {
  stopStatusPolling()
  stopDirectModePolling()
})
</script>

<style scoped>
.video-tool { padding: 0px; }

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
.card-header { display: flex; justify-content: space-between; align-items: center; }
:deep(.el-card__header) { border-bottom: 1px solid rgba(255, 255, 255, 0.1); }

/* 2. 核心修复：输入框去灰 & 去双层 */
:deep(.el-input__wrapper),
:deep(.el-textarea__inner) {
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
:deep(.el-form-item__label) { color: #a0aec0 !important; width: 100%; }

:deep(.el-upload--picture-card) {
  background-color: rgba(0, 0, 0, 0.3) !important;
  border: 1px dashed rgba(255, 255, 255, 0.3) !important;
  color: #a0aec0 !important;
  border-radius: 8px;
}
:deep(.el-upload--picture-card:hover) { border-color: #0575e6 !important; color: #fff !important; }

/* 拖拽上传区域 */
:deep(.el-upload-dragger) {
  background-color: transparent !important;
  border: none !important;
  border-radius: 8px !important;
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
.cyber-action-btn { background: rgba(0, 242, 96, 0.2) !important; border: 1px solid #00f260 !important; color: #00f260 !important; }

/* 5. 结果区 */
.empty-state { padding: 50px 0; text-align: center; color: #718096; }
.placeholder-icon { font-size: 60px; margin-bottom: 20px; opacity: 0.5; color: #a0aec0; }
.processing-state { text-align: center; padding: 40px; }
.result-state { text-align: center; }

/* 视频缩略预览 */
.video-preview-wrapper {
  position: relative;
  display: inline-block;
  border-radius: 8px;
  overflow: hidden;
  cursor: pointer;
  background: #000;
  border: 1px solid rgba(255, 255, 255, 0.2);
  transition: all 0.3s;
}

.video-preview-wrapper:hover {
  border-color: #00f260;
  box-shadow: 0 0 20px rgba(0, 242, 96, 0.3);
}

.video-preview-thumb {
  display: block;
  max-height: 300px;
  max-width: 100%;
  object-fit: contain;
}

.play-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.4);
  opacity: 0;
  transition: opacity 0.3s;
}

.video-preview-wrapper:hover .play-overlay {
  opacity: 1;
}

.play-icon {
  font-size: 48px;
  color: #fff;
  text-shadow: 0 0 20px rgba(0, 242, 96, 0.8);
}

.play-text {
  margin-top: 8px;
  font-size: 14px;
  color: #fff;
}

/* 6. 响应式布局间距 */
@media screen and (max-width: 768px) {
  .right-panel-col {
    margin-top: 20px;
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

/* 全屏视频预览弹窗 */
.fullscreen-video-preview {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.5);
  z-index: 99999;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: zoom-out;
}

.fullscreen-video {
  max-width: 90vw;
  max-height: 85vh;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 0 40px rgba(0, 0, 0, 0.8);
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