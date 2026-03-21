<template>
  <div class="image-tool">
    <el-row :gutter="20">
      <el-col :xs="24" :sm="24" :md="10" :lg="10">
        <el-card class="cyber-glass" shadow="never">
          <template #header>
            <div class="card-header">
              <span class="gradient-text">🖼️ 商品图生成控制台</span>
              <el-tag effect="dark" round color="#00f260" style="border:none; box-shadow: 0 0 10px rgba(0,242,96,0.4)">AI生图</el-tag>
            </div>
          </template>

          <el-form label-position="top">
            <el-form-item label="产品名称 (必填)">
              <el-input v-model="form.product_type" placeholder="例如：高端商务手提包" class="cyber-input" />
            </el-form-item>

            <el-form-item label="设计风格">
               <el-select v-model="form.design_style" style="width: 100%" filterable allow-create default-first-option class="cyber-select" popper-class="cyber-popper">
                 <el-option value="简约 Ins 风" label="简约 Ins 风" />
                 <el-option value="高级奢华" label="高级奢华" />
                 <el-option value="科技感" label="科技感" />
                 <el-option value="清新自然" label="清新自然" />
                 <el-option value="赛博朋克" label="赛博朋克" />
                 <el-option value="国潮风" label="国潮风" />
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
            <el-form-item label="参考图片 (最多5张，支持拖拽)">
              <el-upload action="#" list-type="picture-card" :auto-upload="false" :limit="5" :on-change="handleFileChange" :on-remove="handleRemove" multiple drag class="cyber-upload">
                <el-icon><Plus /></el-icon>
              </el-upload>
            </el-form-item>

            <!-- 参数：一行2个布局 -->
            <el-row :gutter="10">
              <el-col :span="12">
                <el-form-item label="目标语言">
                    <el-select v-model="form.target_lang" style="width: 100%" filterable placeholder="请选择语言" class="cyber-select" popper-class="cyber-popper">
                      <el-option value="日语" label="日语" />
                      <el-option value="英语" label="英语" />
                      <el-option value="中文" label="中文" />
                      <el-option value="韩语" label="韩语" />
                      <el-option value="法语" label="法语" />
                      <el-option value="德语" label="德语" />
                      <el-option value="俄语" label="俄语" />
                      <el-option value="西班牙语" label="西班牙语" />
                      <el-option value="阿拉伯语" label="阿拉伯语" />
                      <el-option value="葡萄牙语" label="葡萄牙语" />
                      <el-option value="越南语" label="越南语" />
                      <el-option value="泰语" label="泰语" />
                      <el-option value="印尼语" label="印尼语" />
                      <el-option value="意大利语" label="意大利语" />
                      <el-option value="马来语" label="马来语" />
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
                    <el-option value="3:4" label="3:4" />
                    <el-option value="1:1" label="1:1" />
                    <el-option value="16:9" label="16:9" />
                    <el-option value="9:16" label="9:16" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                 <el-form-item label="分辨率">
                  <el-select v-model="form.resolution" style="width: 100%" class="cyber-select" popper-class="cyber-popper">
                    <el-option value="1K" label="1K" />
                    <el-option value="2K" label="2K" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <div style="display: flex; gap: 10px; margin-top: 10px;">
                <el-button type="primary" size="large" class="neon-btn" style="flex: 1" @click="generateImage" :loading="loading" :disabled="stopped">
                  🚀 开始生成 ({{ form.num_images * 2 }} 积分)
                </el-button>
                <el-button type="danger" size="large" class="stop-btn" style="width: 100px" @click="stopTask" :disabled="!loading">
                  停止
                </el-button>
            </div>
          </el-form>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="24" :md="14" :lg="14" class="right-panel-col">
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
              <el-image
                :src="img"
                :preview-src-list="generatedImages"
                :initial-index="index"
                class="generated-img"
                :lazy="true"
                ref="imageRefs"
              >
                <template #placeholder><div class="image-slot">加载中...</div></template>
              </el-image>
              <div class="hover-mask">
                  <div class="mask-actions">
                      <el-tooltip content="预览大图" placement="top">
                        <el-button circle type="info" class="mask-btn" @click="openPreview(index)"><el-icon><ZoomIn /></el-icon></el-button>
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
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, watch } from 'vue'
import request from '../../api/request'
import { analyzeImages as analyzeImagesAPI, planImagePrompts as planImagePromptsAPI, generateImage as generateImageAPI } from '../../api/index'
import { Plus, ZoomIn, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { saveAs } from 'file-saver'
import JSZip from 'jszip'
import HistoryPanel from '@/components/HistoryPanel.vue'

const emit = defineEmits(['refresh-points', 'log'])

// ========== 历史记录面板 ref ==========
const historyPanelRef = ref(null)

// --- 变量 ---
const loading = ref(false)
const analyzing = ref(false)
const stopped = ref(false)
const fileList = ref([])
const imageBase64List = ref([])
const generatedImages = ref([])
const imageRefs = ref([])

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

// === 通用方法 ===
const fileToBase64 = (file) => {
  return new Promise((resolve) => {
    const reader = new FileReader()
    reader.readAsDataURL(file.raw || file)
    reader.onload = () => resolve(reader.result)
  })
}

// === 单任务逻辑 ===
const handleFileChange = async (file, fileListRef) => {
  fileList.value = fileListRef
  imageBase64List.value = await Promise.all(fileList.value.map(f => fileToBase64(f)))
  emit('log', `已加载 ${fileList.value.length} 张参考图`)
}
const handleRemove = (file, fileListRef) => {
  fileList.value = fileListRef
  handleFileChange(null, fileListRef)
}

const openPreview = (index) => {
    if(imageRefs.value && imageRefs.value[index]) {
        imageRefs.value[index].showViewer = true
        document.querySelector(`.image-grid .img-card-wrapper:nth-child(${index+1}) .el-image__inner`).click()
    }
}

const analyzeImages = async () => {
  if (imageBase64List.value.length === 0) return ElMessage.warning('请先上传图片')
  analyzing.value = true
  const pType = form.product_type || "通用产品"
  const count = form.num_images || 1
  emit('log', `正在分析 ${imageBase64List.value.length} 张图片...`)
  try {
    // 通过腾讯云函数代理调用 ModelScope
    const res = await analyzeImagesAPI({
      images: imageBase64List.value,
      product_type: pType,
      design_style: form.design_style,
      target_lang: form.target_lang,
      target_num: count
    })

    // 解析响应
    let content = res.choices?.[0]?.message?.content || ''
    if (content) {
      // 清理格式
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

const generateImage = async () => {
  if (!form.product_type || !form.selling_points) return ElMessage.warning('请填写完整信息')
  loading.value = true
  stopped.value = false
  let successCount = 0
  emit('log', `正在规划 ${form.num_images} 张图片的拍摄方案...`)
  let promptList = []

  try {
    // 通过腾讯云函数代理调用 ModelScope 进行提示词规划
    const res = await planImagePromptsAPI({
      images: imageBase64List.value,
      product_type: form.product_type,
      selling_points: form.selling_points,
      design_style: form.design_style,
      target_lang: form.target_lang,
      num_screens: form.num_images
    })

    // 解析响应 (支持详细文本格式和 JSON 格式)
    const content = res.choices?.[0]?.message?.content || ''

    // 尝试解析 JSON 数组
    try {
      // 清理可能的 markdown 代码块
      let cleanContent = content.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim()

      // 首先尝试 JSON 解析
      try {
        promptList = JSON.parse(cleanContent)
        if (!Array.isArray(promptList)) {
          promptList = [String(promptList)]
        }
      } catch {
        // 如果不是 JSON，按 "第N屏" 分割 (复刻旧项目逻辑)
        const parts = content.split(/["']?第\d+屏["\']?[：:]/)
        promptList = parts
          .map(p => p.trim())
          .filter(p => p.length > 10)
          .map(p => {
            // 提取完整内容作为一个 prompt
            // 如果包含主文案等结构，提取关键信息
            const mainTextMatch = p.match(/主文案[：:]["'""]([^"'""]+)["'""]/)
            const subTextMatch = p.match(/副文案[：:]["'""]([^"'""]+)["'""]/)
            const designMatch = p.match(/文案设计与排版[：:](.+?)(?=画面主体|$)/s)
            const sceneMatch = p.match(/画面主体与构图[：:](.+?)(?=画质|$)/s)
            const qualityMatch = p.match(/画质与细节[：:](.+?)$/s)

            // 构建完整的 prompt
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
      // 最后兜底
      promptList = content.split('\n').filter(line => line.trim().length > 20)
    }

    if (promptList.length === 0) {
      promptList = [form.selling_points]
    }

    emit('log', `方案规划完成，共 ${promptList.length} 个方案`)
    // 完整输出每个方案 (不截断)
    promptList.forEach((p, index) => {
      emit('log', `[方案 ${index + 1}]:\n${p}`)
    })
  } catch (e) {
    ElMessage.error('方案规划失败')
    emit('log', `规划失败: ${e.message || e}`)
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
      // 通过腾讯云函数代理调用 T8Star 图片生成 API
      const res = await generateImageAPI({
        prompt: currentPrompt,
        aspect_ratio: form.aspect_ratio,
        resolution: form.resolution,
        images: imageBase64List.value,
        seed: form.seed
      })

      // 解析响应
      const url = res.data?.[0]?.url || res.data?.url
      if (url) {
        generatedImages.value.unshift(url)
        emit('refresh-points')
        emit('log', `第 ${i+1} 张生成成功！`)
        successCount++

        // 保存历史记录
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
  if (successCount > 0) {
    ElMessage.success(`任务结束，成功 ${successCount} 张`)
    emit('log', `任务全部结束`)
  }
}

// ========== 保存历史记录 ==========
const saveImageHistory = async (resultUrl, prompt) => {
  try {
    await request.post('/api/history', {
      task_type: 'image',
      model_id: 'nano-banana-2',
      status: 'success',
      prompt_summary: prompt?.substring(0, 200) || '',
      params_json: {
        aspect_ratio: form.aspect_ratio,
        resolution: form.resolution
      },
      result_url: resultUrl,
      cost_points: 2 // 图片固定 2 积分
    })

    // 刷新历史记录面板
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
const SESSION_KEY = 'image_tool_data'; const saveStateToSession = () => { sessionStorage.setItem(SESSION_KEY, JSON.stringify({ form, images: generatedImages.value })) }; const restoreStateFromSession = () => { const data = sessionStorage.getItem(SESSION_KEY); if (data) { try { const parsed = JSON.parse(data); Object.assign(form, parsed.form); generatedImages.value = parsed.images || [] } catch (e) {} } }; watch(form, saveStateToSession, { deep: true }); watch(generatedImages, saveStateToSession, { deep: true }); onMounted(() => restoreStateFromSession())
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
.card-header { display: flex; justify-content: space-between; align-items: center; }
:deep(.el-card__header) { border-bottom: 1px solid rgba(255, 255, 255, 0.1); }

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
.generated-img { width: 100%; height: auto; min-height: 120px; display: block; }
.hover-mask { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.7); opacity: 0; transition: opacity 0.3s; display: flex; justify-content: center; align-items: center; z-index: 10; }
.img-card-wrapper:hover .hover-mask { opacity: 1; }
.mask-actions { display: flex; gap: 10px; }
.image-slot { display: flex; justify-content: center; align-items: center; width: 100%; height: 150px; background: rgba(255,255,255,0.05); color: #718096; font-size: 12px; }

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
</style>