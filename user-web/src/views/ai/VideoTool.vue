<template>
  <div class="video-tool">
    <el-row :gutter="20">
      <el-col :xs="24" :sm="24" :md="10" :lg="10">
        <el-card class="cyber-glass" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="gradient-text">🎬 视频生成控制台</span>
              <el-tag effect="dark" round color="#ff0055" style="border:none; box-shadow: 0 0 10px rgba(255,0,85,0.4)">{{ currentModel?.display_name || 'AI视频' }}</el-tag>
            </div>
          </template>

          <el-form :model="form" label-position="top">
            <!-- 动态模型选择 -->
            <el-form-item label="生成模型">
              <el-select v-model="form.model" style="width: 100%" class="cyber-select" popper-class="cyber-popper" @change="onModelChange">
                <el-option v-for="m in models" :key="m.model_id" :value="m.model_id" :label="m.display_name" />
              </el-select>
            </el-form-item>

            <el-form-item label="产品名称 (必填)">
              <el-input v-model="form.product_type" placeholder="例如：潮汕菜脯" class="cyber-input" />
            </el-form-item>

            <div class="label-box">
              <span class="label-text">核心卖点 (必填)</span>
              <el-tooltip content="请先在下方上传图片，然后点击此按钮" placement="top" :disabled="fileList.length > 0">
                <el-button
                  type="primary"
                  plain
                  round
                  size="small"
                  class="optimize-btn"
                  @click="analyzeImages"
                  :loading="analyzing"
                  :disabled="fileList.length === 0"
                >
                  <el-icon class="el-icon--left"><MagicStick /></el-icon>
                  {{ analyzing ? '正在分析...' : '✨ 看图自动生成文案' }}
                </el-button>
              </el-tooltip>
            </div>

            <el-form-item>
              <el-input
                v-model="form.selling_points"
                type="textarea"
                :rows="6"
                placeholder="在此处输入文案，或者上传图片后点击上方「看图自动生成文案」按钮..."
                resize="none"
                maxlength="5000"
                show-word-limit
                class="cyber-input"
              />
            </el-form-item>

            <el-form-item label="参考图片 (最多5张)">
              <el-upload
                action="#"
                list-type="picture-card"
                :auto-upload="false"
                :limit="5"
                :on-change="handleFileChange"
                :on-remove="handleRemove"
                multiple
                class="cyber-upload"
              >
                <el-icon><Plus /></el-icon>
              </el-upload>
            </el-form-item>

            <el-divider content-position="left" class="cyber-divider">策略配置</el-divider>

            <el-row :gutter="10">
              <el-col :span="12">
                <el-form-item label="投放地区">
                  <el-select v-model="form.region" class="cyber-select" popper-class="cyber-popper">
                    <el-option value="东亚 (中日韩)" label="东亚 (中日韩)" />
                    <el-option value="东南亚" label="东南亚" />
                    <el-option value="欧美" label="欧美" />
                    <el-option value="中东" label="中东" />
                    <el-option value="非洲" label="非洲" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="目标语言">
                  <el-select v-model="form.language" filterable placeholder="请选择语言" class="cyber-select" popper-class="cyber-popper">
                    <el-option value="日语 (Japanese)" label="日语" />
                    <el-option value="英语 (English)" label="英语" />
                    <el-option value="中文 (Chinese)" label="中文" />
                    <el-option value="韩语 (Korean)" label="韩语" />
                    <el-option value="法语 (French)" label="法语" />
                    <el-option value="德语 (German)" label="德语" />
                    <el-option value="俄语 (Russian)" label="俄语" />
                    <el-option value="西班牙语 (Spanish)" label="西班牙语" />
                    <el-option value="阿拉伯语 (Arabic)" label="阿拉伯语" />
                    <el-option value="葡萄牙语 (Portuguese)" label="葡萄牙语" />
                    <el-option value="越南语 (Vietnamese)" label="越南语" />
                    <el-option value="泰语 (Thai)" label="泰语" />
                    <el-option value="印尼语 (Indonesian)" label="印尼语" />
                    <el-option value="意大利语 (Italian)" label="意大利语" />
                    <el-option value="马来语 (Malay)" label="马来语" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="10">
              <el-col :span="12">
                <el-form-item label="产品类目">
                  <el-select v-model="form.category" class="cyber-select" popper-class="cyber-popper">
                    <el-option value="食品饮料" label="食品饮料" />
                    <el-option value="美妆护肤" label="美妆护肤" />
                    <el-option value="数码家电" label="数码家电" />
                    <el-option value="服装配饰" label="服装配饰" />
                    <el-option value="家居日用" label="家居日用" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="视频风格">
                  <el-select v-model="form.style" placeholder="请选择风格" class="cyber-select" popper-class="cyber-popper">
                    <el-option value="UGC 种草" label="UGC 种草" />
                    <el-option value="产品口播" label="产品口播" />
                    <el-option value="产品演示" label="产品演示" />
                    <el-option value="TVC 广告" label="TVC 广告" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-divider content-position="left" class="cyber-divider">技术参数</el-divider>

            <el-row :gutter="10">
              <el-col :span="12">
                <el-form-item label="画面比例">
                  <el-select v-model="form.aspect_ratio" class="cyber-select" popper-class="cyber-popper" @change="calculateCost">
                    <el-option v-for="r in (currentModel?.frontend_config?.ratios || ['9:16', '16:9', '1:1'])" :key="r" :value="r" :label="getRatioLabel(r)" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="时长(秒)">
                  <el-select v-model="form.duration" class="cyber-select" popper-class="cyber-popper" @change="calculateCost">
                    <el-option v-for="d in (currentModel?.frontend_config?.durations || [5, 10, 15, 25])" :key="d" :value="d" :label="d + '秒'" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="10">
              <el-col :span="12">
                <el-form-item label="分辨率">
                  <el-select v-model="form.resolution" class="cyber-select" popper-class="cyber-popper" @change="calculateCost">
                    <el-option v-for="res in (currentModel?.frontend_config?.resolutions || [{value: '720P', label: '标清'}, {value: '1080P', label: '高清'}])" :key="res.value" :value="res.value" :label="res.label" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item>
              <el-checkbox v-model="form.hd" label="高清模式 (HD)" border class="cyber-checkbox" />
            </el-form-item>

            <!-- 费用信息 -->
            <div class="cost-info-box">
              <div class="cost-row">
                <span>当前积分</span>
                <span class="cost-value">{{ userStore.points }}</span>
              </div>
              <div class="cost-row">
                <span>消耗积分</span>
                <span class="cost-value highlight">{{ costInfo.cost }}</span>
              </div>
              <div class="cost-row">
                <span>剩余积分</span>
                <span class="cost-value">{{ userStore.points - costInfo.cost }}</span>
              </div>
            </div>

            <el-button type="primary" size="large" style="width: 100%" class="neon-btn" @click="submitTask" :loading="loading" :disabled="loading || !canGenerate">
              {{ loading ? '生成中...' : `🚀 立即生成 (消耗${costInfo.cost}积分)` }}
            </el-button>
          </el-form>
        </el-card>

        <!-- 费用说明卡片 -->
        <el-card v-if="currentModel?.pricing_description" class="cyber-glass pricing-card" shadow="never" style="margin-top: 16px;">
          <template #header>
            <span class="gradient-text">💰 费用说明</span>
          </template>
          <div class="pricing-desc" v-html="formatDescription(currentModel.pricing_description)"></div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="24" :md="14" :lg="14" class="right-panel-col">
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
            <p style="color: #a0aec0; font-size: 12px;">(Sora生成较慢，请耐心等待 3-5 分钟)</p>
            <div class="script-box" v-if="scriptContent">
               <h4 style="color: #00f260;">📝 AI 编写的分镜脚本：</h4>
               <pre>{{ scriptContent }}</pre>
            </div>
          </div>

          <div v-if="videoUrl" class="result-state">
            <el-alert title="生成成功！" type="success" show-icon style="margin-bottom: 20px; background: rgba(0,242,96,0.1); border-color: #00f260; color: #00f260;" />
            <video :src="videoUrl" controls autoplay style="width: 100%; max-height: 600px; background: black; border-radius: 8px; border: 1px solid #333;"></video>
            <div style="margin-top: 20px; text-align: center;">
               <el-button type="success" size="large" class="cyber-action-btn" tag="a" :href="videoUrl" target="_blank">⬇️ 下载视频文件</el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { Plus, MagicStick } from '@element-plus/icons-vue'
import { reactive, ref, computed, onMounted, onUnmounted } from 'vue'
import request from '@/api/request'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'

const emit = defineEmits(['refresh-points'])
const userStore = useUserStore()

const loading = ref(false)
const analyzing = ref(false)
const taskId = ref('')
const taskStatus = ref('')
const progress = ref(0)
const videoUrl = ref('')
const scriptContent = ref('')
const fileList = ref([])
const imageBase64List = ref([])

// 模型相关
const models = ref([])
const currentModel = ref(null)

const form = reactive({
  model: '',
  product_type: '',
  selling_points: '',
  region: '东亚 (中日韩)',
  language: '日语 (Japanese)',
  category: '食品饮料',
  style: 'UGC 种草',
  aspect_ratio: '9:16',
  duration: 10,
  resolution: '720P',
  hd: false
})

// 费用计算
const costInfo = ref({ cost: 0, breakdown: null })

const canGenerate = computed(() => {
  return form.model && form.product_type && form.selling_points && costInfo.value.cost > 0
})

// 加载模型列表
const loadModels = async () => {
  try {
    const res = await request.get('/api/models?model_type=video')
    models.value = res
    if (res.length > 0) {
      form.model = res[0].model_id
      await onModelChange()
    }
  } catch (e) {
    console.error('加载模型失败', e)
  }
}

// 模型切换
const onModelChange = async () => {
  if (!form.model) return
  try {
    const res = await request.get(`/api/models/${form.model}`)
    currentModel.value = res

    // 设置默认值
    if (res.frontend_config?.durations?.length) {
      form.duration = res.frontend_config.durations[0]
    }
    if (res.frontend_config?.ratios?.length) {
      form.aspect_ratio = res.frontend_config.ratios[0]
    }
    if (res.frontend_config?.resolutions?.length) {
      form.resolution = res.frontend_config.resolutions[0].value
    }

    await calculateCost()
  } catch (e) {
    console.error('加载模型详情失败', e)
  }
}

// 计算费用
const calculateCost = async () => {
  if (!form.model) return
  try {
    const res = await request.post('/api/calculate-cost', {
      model_id: form.model,
      duration: form.duration,
      resolution: form.resolution,
      ratio: form.aspect_ratio,
      count: 1
    })
    costInfo.value = res
  } catch (e) {
    console.error('计算费用失败', e)
  }
}

// 比例标签
const getRatioLabel = (r) => {
  const labels = { '9:16': '9:16 (手机竖屏)', '16:9': '16:9 (横屏)', '1:1': '1:1 (方形)', '2:3': '2:3', '3:2': '3:2' }
  return labels[r] || r
}

// 格式化描述
const formatDescription = (text) => {
  return text?.replace(/\n/g, '<br>') || ''
}

// 文件处理
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

// 图片分析（暂时简化）
const analyzeImages = async () => {
  if (imageBase64List.value.length === 0) return ElMessage.warning('请先上传图片')
  analyzing.value = true
  try {
    // 这里可以调用后端的图片分析接口
    ElMessage.info('图片分析功能待接入')
  } catch (e) {
    ElMessage.error('分析失败')
  } finally {
    analyzing.value = false
  }
}

// 提交任务
const submitTask = async () => {
  if (!form.product_type || !form.selling_points) {
    return ElMessage.warning('请填写完整信息')
  }

  // 检查积分
  if (userStore.points < costInfo.value.cost) {
    return ElMessage.warning('积分不足，请充值')
  }

  // 确认弹窗
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

    // 3. 构建提示词
    const prompt = `产品: ${form.product_type}\n卖点: ${form.selling_points}\n风格: ${form.style}\n类目: ${form.category}\n语言: ${form.language}\n地区: ${form.region}`

    // 4. 调用 Vercel Functions 生成视频
    const videoRes = await request.post(`${vercelUrl}/api/ai/generate-video`, {
      model: form.model,
      prompt: prompt,
      duration: form.duration,
      ratio: form.aspect_ratio,
      resolution: form.resolution,
      images: imageBase64List.value,
      deduction_id: deductionId
    })

    taskId.value = videoRes.task_id

    // 5. 确认扣费
    await request.post('/api/points/confirm', { deduction_id: deductionId })

    // 6. 刷新积分
    userStore.refreshPoints()
    emit('refresh-points')

    // 7. 开始轮询状态
    startStatusPolling(vercelUrl)

    ElMessage.success('视频生成任务已提交')
  } catch (e) {
    // 退还积分
    if (deductionId) {
      try {
        await request.post('/api/points/refund', {
          deduction_id: deductionId,
          reason: '生成失败'
        })
      } catch (err) {}
    }
    ElMessage.error(e.message || '提交失败')
    loading.value = false
    taskStatus.value = ''
  }
}

// 状态轮询
let statusTimer = null

const startStatusPolling = (vercelUrl) => {
  stopStatusPolling()
  statusTimer = setInterval(async () => {
    try {
      const res = await request.get(`${vercelUrl}/api/ai/video-status?task_id=${taskId.value}&model=${form.model}`)

      const status = res.status
      const prog = res.progress || 0
      progress.value = Math.min(99, parseInt(prog))

      if (status === 'SUCCESS') {
        clearInterval(statusTimer)
        progress.value = 100
        videoUrl.value = res.video_url
        taskStatus.value = 'success'
        loading.value = false
        ElMessage.success('视频生成完成！')
      } else if (status === 'FAILURE') {
        clearInterval(statusTimer)
        taskStatus.value = 'fail'
        loading.value = false
        ElMessage.error('生成失败: ' + (res.error || '未知错误'))
      }
    } catch (e) {
      console.error('状态查询失败', e)
    }
  }, 5000)
}

const stopStatusPolling = () => {
  if (statusTimer) {
    clearInterval(statusTimer)
    statusTimer = null
  }
}

onMounted(() => {
  loadModels()
})

onUnmounted(() => {
  stopStatusPolling()
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

:deep(.el-checkbox__inner) { background: rgba(0,0,0,0.3) !important; border-color: rgba(255,255,255,0.3) !important; }
:deep(.el-checkbox__label) { color: #a0aec0 !important; }
:deep(.el-checkbox__input.is-checked .el-checkbox__inner) { background: #00f260 !important; border-color: #00f260 !important; }
:deep(.el-checkbox__input.is-checked + .el-checkbox__label) { color: #00f260 !important; }

/* 4. 按钮 & 文本 */
.gradient-text { font-size: 18px; font-weight: 800; background: linear-gradient(90deg, #00f260, #0575e6); -webkit-background-clip: text; color: transparent; text-shadow: 0 0 10px rgba(5, 117, 230, 0.3); }
.label-box { display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 5px; }
.label-text { font-weight: bold; color: #e2e8f0; }

.neon-btn { background: linear-gradient(90deg, #7f00ff, #e100ff) !important; border: none; box-shadow: 0 4px 15px rgba(127, 0, 255, 0.4); color: #fff; }
.neon-btn:hover { opacity: 0.9; }
.optimize-btn { background: transparent !important; border: 1px solid #e6a23c !important; color: #e6a23c !important; }
.cyber-action-btn { background: rgba(0, 242, 96, 0.2) !important; border: 1px solid #00f260 !important; color: #00f260 !important; }
.cyber-divider { border-color: rgba(255,255,255,0.1); }
:deep(.el-divider__text) { background-color: transparent; color: #00f260; }

/* 费用信息框 */
.cost-info-box {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 16px;
}
.cost-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  font-size: 14px;
  color: #a0aec0;
}
.cost-value {
  font-weight: bold;
  color: #fff;
}
.cost-value.highlight {
  color: #00f260;
  font-size: 18px;
}

/* 费用说明 */
.pricing-card :deep(.el-card__header) {
  padding: 12px 16px;
}
.pricing-desc {
  font-size: 13px;
  line-height: 1.8;
  color: #a0aec0;
}

/* 5. 结果区 */
.empty-state { padding: 50px 0; text-align: center; color: #718096; }
.placeholder-icon { font-size: 60px; margin-bottom: 20px; opacity: 0.5; color: #a0aec0; }
.processing-state { text-align: center; padding: 40px; }
.script-box {
  margin-top: 30px; text-align: left;
  background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.1);
  padding: 15px; border-radius: 4px; font-size: 13px; color: #a0aec0;
  max-height: 200px; overflow-y: auto; white-space: pre-wrap;
}
.result-state { text-align: center; }

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
.cyber-popper .el-popper__arrow::before {
  background: rgba(0, 0, 0, 0.4) !important; border: 1px solid rgba(255, 255, 255, 0.15) !important;
}
</style>