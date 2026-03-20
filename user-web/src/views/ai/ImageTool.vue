<template>
  <div class="image-tool">
    <div class="cyber-container">
      <el-tabs v-model="activeTab" type="border-card" class="cyber-tabs">

        <el-tab-pane label="单任务生成" name="single">
          <el-row :gutter="24">
            <el-col :xs="24" :sm="24" :md="10" :lg="10">
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
                      {{ analyzing ? '正在分析...' : '看图生成文案' }}
                    </el-button>
                  </el-tooltip>
                </div>

                <el-form-item>
                  <el-input v-model="form.selling_points" type="textarea" :rows="8" placeholder="在此输入卖点..." resize="none" maxlength="5000" show-word-limit class="cyber-input" />
                </el-form-item>

                <el-row :gutter="10">
                  <el-col :span="16">
                    <el-form-item label="目标语言">
                        <el-select v-model="form.target_lang" filterable placeholder="请选择语言" class="cyber-select" popper-class="cyber-popper" @change="(val) => { form.target_lang = val; console.log('语言切换为:', val) }">
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
                  <el-col :span="8">
                     <el-form-item label=" ">
                       <el-button type="danger" plain style="width: 100%" class="stop-btn" @click="translateText" :loading="translating">仅翻译</el-button>
                     </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="参考图片 (最多5张)">
                  <el-upload action="#" list-type="picture-card" :auto-upload="false" :limit="5" :on-change="handleFileChange" :on-remove="handleRemove" multiple drag class="cyber-upload">
                    <el-icon><Plus /></el-icon>
                  </el-upload>
                </el-form-item>

                <el-row :gutter="10">
                  <el-col :span="12">
                    <el-form-item label="画面比例">
                      <el-select v-model="form.aspect_ratio" class="cyber-select" popper-class="cyber-popper">
                        <el-option value="3:4" label="3:4" />
                        <el-option value="1:1" label="1:1" />
                        <el-option value="16:9" label="16:9" />
                        <el-option value="9:16" label="9:16" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                     <el-form-item label="分辨率">
                      <el-select v-model="form.resolution" class="cyber-select" popper-class="cyber-popper">
                        <el-option value="1K" label="1K" />
                        <el-option value="2K" label="2K" />
                      </el-select>
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item label="生成数量">
                   <el-input-number v-model="form.num_images" :min="1" :max="10" class="cyber-input-number" />
                </el-form-item>

                <div style="display: flex; gap: 10px; margin-top: 10px;">
                    <el-button type="primary" size="large" class="neon-btn" style="flex: 1" @click="generateImage" :loading="loading" :disabled="stopped">
                      开始生成 ({{ form.num_images * 2 }} 积分)
                    </el-button>
                    <el-button type="danger" size="large" class="stop-btn" style="width: 100px" @click="stopTask" :disabled="!loading">
                      停止
                    </el-button>
                </div>
              </el-form>
            </el-col>

            <el-col :xs="24" :sm="24" :md="14" :lg="14" class="right-panel-col">
              <div class="result-header">
                 <span class="gradient-text">生成结果 ({{ generatedImages.length }})</span>
                 <el-button v-if="generatedImages.length > 0" type="success" size="small" class="cyber-action-btn" @click="downloadAllImages">一键打包下载 ZIP</el-button>
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
                      ref="imageRefs"
                    >
                      <template #placeholder><div class="image-slot">加载中...</div></template>
                    </el-image>
                    <div class="hover-mask">
                        <div class="mask-actions">
                            <el-tooltip content="预览大图" placement="top">
                              <el-button circle type="info" class="mask-btn" @click="openPreview(index)"><el-icon><ZoomIn /></el-icon></el-button>
                            </el-tooltip>
                            <el-tooltip content="去修图" placement="top">
                              <el-button circle type="primary" class="mask-btn" @click="sendToEdit(img)"><el-icon><Edit /></el-icon></el-button>
                            </el-tooltip>
                            <el-tooltip content="下载原图" placement="top">
                               <el-button circle type="success" class="mask-btn" @click="downloadSingleImage(img, index)"><el-icon><Download /></el-icon></el-button>
                            </el-tooltip>
                        </div>
                    </div>
                  </div>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-tab-pane>

        <el-tab-pane label="图片再修改" name="edit">
          <el-row :gutter="24">
            <el-col :xs="24" :sm="24" :md="10" :lg="10">
              <el-form label-position="top">
                 <el-form-item label="上传原图 (支持多张批量修改)">
                    <el-upload
                      v-model:file-list="editFileList"
                      action="#"
                      list-type="picture-card"
                      :auto-upload="false"
                      :limit="5"
                      :on-change="handleEditFileChange"
                      :on-remove="handleEditRemove"
                      multiple
                      drag
                      class="cyber-upload"
                    >
                      <el-icon><Plus /></el-icon>
                    </el-upload>
                 </el-form-item>

                 <el-form-item label="修改指令 (必填)">
                   <el-input v-model="editForm.prompt" type="textarea" :rows="4" placeholder="例如：把背景变成雪天，增加光照..." class="cyber-input" />
                 </el-form-item>

                 <el-form-item label="重绘幅度 (强度 0.1~1.0)">
                    <el-slider v-model="editForm.strength" :min="0.1" :max="1.0" :step="0.1" show-input class="cyber-slider" />
                    <div style="font-size: 12px; color: #a0aec0; margin-top: 5px;">0.1 = 微调 (保留原图) | 1.0 = 重画 (仅参考构图)</div>
                 </el-form-item>

                 <el-button type="success" size="large" style="width: 100%" class="neon-btn" @click="editImage" :loading="editing" :disabled="editFileList.length === 0">
                  开始修改 (预计消耗 2 积分)
                </el-button>
              </el-form>
            </el-col>

            <el-col :xs="24" :sm="24" :md="14" :lg="14" class="right-panel-col">
               <div class="result-header">
                 <span class="gradient-text">修改结果 ({{ editedImages.length }})</span>
               </div>
               <div class="gallery-area cyber-glass-inset">
                  <el-empty v-if="editedImages.length === 0" description="修改后的图片将显示在这里" :image-size="100" />
                  <div v-else class="image-grid">
                      <div v-for="(img, index) in editedImages" :key="index" class="img-card-wrapper cyber-border">
                        <el-image :src="img" :preview-src-list="editedImages" :initial-index="index" class="generated-img" />
                        <div style="padding: 10px; text-align: center; background: rgba(0,0,0,0.5);">
                            <el-button type="success" link size="small" class="cyber-action-btn" @click="downloadSingleImage(img, 'edited_'+index)">下载</el-button>
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
import { reactive, ref, onMounted, watch } from 'vue'
import request from '../../api/request'
import { Plus, ZoomIn, Edit, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { saveAs } from 'file-saver'
import JSZip from 'jszip'

const emit = defineEmits(['refresh-points', 'log'])
const activeTab = ref('single')

// --- 单任务变量 ---
const loading = ref(false)
const analyzing = ref(false)
const translating = ref(false)
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

// --- 再修改变量 ---
const editing = ref(false)
const editFileList = ref([])
const editServerPaths = ref([])
const editedImages = ref([])
const editForm = reactive({
  prompt: '',
  strength: 0.6
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

const sendToEdit = async (imgUrl) => {
    emit('log', '正在将图片发送到修图台...')
    try {
        const response = await fetch(imgUrl)
        const blob = await response.blob()
        const file = new File([blob], `generated_${Date.now()}.png`, { type: "image/png" })
        const formData = new FormData()
        formData.append('file', file)
        const res = await request.post('/api/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
        if (res.status === 'success') {
            const uploadFile = { name: file.name, uid: Date.now(), status: 'ready', raw: file, url: URL.createObjectURL(file), serverPath: res.path }
            editFileList.value.push(uploadFile)
            activeTab.value = 'edit'
            ElMessage.success('图片已发送并准备就绪')
            emit('log', `图片已自动上传至修图台`)
        } else { throw new Error(res.msg) }
    } catch (e) { ElMessage.error('传输失败'); emit('log', `传输失败: ${e.message}`) }
}

const editServerPath = ref('')

const handleEditFileChange = async (uploadFile, uploadFiles) => {
  editFileList.value = uploadFiles
  if (uploadFile.status === 'ready') {
    const formData = new FormData()
    formData.append('file', uploadFile.raw)
    emit('log', `正在上传: ${uploadFile.name}...`)
    try {
      const res = await request.post('/api/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
      if (res.status === 'success') {
        uploadFile.serverPath = res.path; uploadFile.status = 'success'; emit('log', `上传成功`)
      } else {
        emit('log', `上传失败: ${res.msg}`); const idx = editFileList.value.indexOf(uploadFile); if (idx !== -1) editFileList.value.splice(idx, 1)
      }
    } catch (e) { emit('log', `网络错误`); const idx = editFileList.value.indexOf(uploadFile); if (idx !== -1) editFileList.value.splice(idx, 1) }
  }
}

const handleEditRemove = (file, uploadFiles) => { editFileList.value = uploadFiles; emit('log', `已移除图片`) }

const editImage = async () => {
  const validFiles = editFileList.value.filter(f => f.serverPath)
  if (validFiles.length === 0) return ElMessage.warning('请等待图片上传完成')
  if (!editForm.prompt) return ElMessage.warning('请输入修改指令')
  editing.value = true; editedImages.value = []; emit('log', `开始批量修改 ${validFiles.length} 张图片...`)
  try {
    for(let i=0; i<validFiles.length; i++) {
        const fileObj = validFiles[i]
        emit('log', `[${i+1}/${validFiles.length}] 正在处理: ${fileObj.name}`)
        const res = await request.post('/api/edit/image', { image_base64: fileObj.serverPath, prompt: editForm.prompt, strength: editForm.strength })
        if (res.status === 'success') {
          editedImages.value.unshift(res.url); emit('refresh-points'); emit('log', `修改成功！`); downloadSingleImage(res.url, `edited_${i}`)
        } else { ElMessage.error(res.msg); emit('log', `修改失败: ${res.msg}`) }
    }
    ElMessage.success('批量修改完成')
  } catch (e) { ElMessage.error('请求失败'); emit('log', `网络错误: ${e}`) } finally { editing.value = false }
}

const analyzeImages = async () => {
  if (imageBase64List.value.length === 0) return ElMessage.warning('请先上传图片')
  analyzing.value = true; const pType = form.product_type || "通用产品"; const count = form.num_images || 1; emit('log', `正在分析 ${imageBase64List.value.length} 张图片...`)
  try {
    const res = await request.post('/api/analyze/images', { images: imageBase64List.value, product_type: pType, design_style: form.design_style, target_lang: form.target_lang, target_num: count })
    if (res.status === 'success') {
      let cleanContent = res.content; if (cleanContent.includes("Set 1:")) { cleanContent = cleanContent.replace(/Set \d+:/g, "").trim() }
      form.selling_points = cleanContent; ElMessage.success('卖点生成成功')
    } else { emit('log', `分析失败: ${res.msg}`); ElMessage.error(res.msg) }
  } catch (e) { ElMessage.error('分析失败'); emit('log', `网络请求错误: ${e}`) } finally { analyzing.value = false }
}

const translateText = async () => {
    if(!form.selling_points) return ElMessage.warning('请先输入文案')
    translating.value = true; emit('log', `正在将文案翻译为：${form.target_lang}...`)
    try {
        const res = await request.post('/api/translate', { text: form.selling_points, target_lang: form.target_lang })
        if(res.status === 'success') { form.selling_points = res.content; ElMessage.success('翻译完成'); emit('log', `翻译成功`) } else { emit('log', `翻译失败: ${res.msg}`) }
    } catch(e) { ElMessage.error('翻译失败') } finally { translating.value = false }
}

const generateImage = async () => {
  if (!form.product_type || !form.selling_points) return ElMessage.warning('请填写完整信息')
  loading.value = true; stopped.value = false; let successCount = 0; emit('log', `正在规划 ${form.num_images} 张图片的拍摄方案...`); let promptList = []
  try {
      const payload = { ...form, ref_images: imageBase64List.value }
      const resPlan = await request.post('/api/plan/images', payload)
      if (resPlan.status === 'success') {
          promptList = resPlan.prompts; emit('log', `方案规划完成`); promptList.forEach((p, index) => emit('log', `[方案 ${index + 1}]: ${p}\n---`))
      } else { throw new Error(resPlan.msg) }
  } catch (e) { ElMessage.error('方案规划失败'); emit('log', `规划失败: ${e.message}`); loading.value = false; return }
  emit('log', `开始批量渲染 (共 ${promptList.length} 张)...`)
  for (let i = 0; i < promptList.length; i++) {
      if (stopped.value) { emit('log', '任务已手动停止'); break; }
      const currentPrompt = promptList[i]; emit('log', `[第 ${i+1}/${promptList.length} 张] 正在请求云端绘图...`)
      try {
          const payload = { ...form, ref_images: imageBase64List.value, num_images: 1, specific_prompt: currentPrompt }; const res = await request.post('/api/generate/image', payload)
          if (res.status === 'success') { generatedImages.value.unshift(res.url); emit('refresh-points'); emit('log', `第 ${i+1} 张生成成功！`); successCount++ } else { ElMessage.error(`第 ${i+1} 张失败`); emit('log', `第 ${i+1} 张服务端拒绝: ${res.msg}`) }
      } catch (e) { let errMsg = e.message || '未知错误'; if (errMsg.includes('timeout')) errMsg = '请求超时(后端仍在运行)'; ElMessage.error(`第 ${i+1} 张请求出错`); emit('log', `第 ${i+1} 张异常: ${errMsg}`) }
  }
  loading.value = false; stopped.value = false; if (successCount > 0) { ElMessage.success(`任务结束，成功 ${successCount} 张`); emit('log', `任务全部结束`) }
}

const stopTask = () => { stopped.value = true; loading.value = false; emit('log', '用户请求停止任务...'); ElMessage.info('已请求停止后续任务') }
const downloadSingleImage = (url, suffix) => { const fileName = `Product_${Date.now()}_${suffix}.png`; saveAs(url, fileName) }
const downloadAllImages = async () => { const zip = new JSZip(); const folder = zip.folder("images"); emit('log', '正在打包下载所有图片...')
  try { for (let i = 0; i < generatedImages.value.length; i++) { const url = generatedImages.value[i]; const fileName = `Product_${i + 1}.png`; const response = await fetch(url); const blob = await response.blob(); folder.file(fileName, blob) } zip.generateAsync({ type: "blob" }).then((content) => { saveAs(content, `Batch_Images_${Date.now()}.zip`); emit('log', '打包下载完成') }) } catch (e) { emit('log', `打包失败: ${e}`); ElMessage.error('打包下载失败') } }
const SESSION_KEY = 'image_tool_data'; const saveStateToSession = () => { sessionStorage.setItem(SESSION_KEY, JSON.stringify({ form, images: generatedImages.value })) }; const restoreStateFromSession = () => { const data = sessionStorage.getItem(SESSION_KEY); if (data) { try { const parsed = JSON.parse(data); Object.assign(form, parsed.form); generatedImages.value = parsed.images || [] } catch (e) {} } }; watch(form, saveStateToSession, { deep: true }); watch(generatedImages, saveStateToSession, { deep: true }); onMounted(() => restoreStateFromSession())
</script>

<style scoped>
.image-tool { padding: 0px; }

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
  color: #a0aec0 !important; font-weight: 700; border-right: 1px solid rgba(255, 255, 255, 0.05) !important; border-left: none !important;
}
:deep(.el-tabs__item.is-active) {
  background: rgba(255, 255, 255, 0.08) !important;
  color: #00f260 !important;
  border-bottom: none !important;
}
:deep(.el-tabs__content) { padding: 20px !important; }

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

:deep(.el-slider__runway) { background-color: rgba(255,255,255,0.2) !important; }
:deep(.el-slider__bar) { background-color: #00f260 !important; }
:deep(.el-slider__button) { border-color: #00f260 !important; }

/* 4. 按钮 & 文本 */
.neon-btn { background: linear-gradient(90deg, #7f00ff, #e100ff) !important; border: none !important; box-shadow: 0 4px 15px rgba(127,0,255,0.4); color: #fff; }
.neon-btn:hover { opacity: 0.9; }
.optimize-btn { background: transparent !important; border: 1px solid #e6a23c !important; color: #e6a23c !important; }
.stop-btn { background: #ff0055 !important; border: none !important; box-shadow: 0 4px 15px rgba(255, 0, 85, 0.4); color: #fff; }
.cyber-action-btn { background: rgba(0,242,96,0.1) !important; border: 1px solid #00f260 !important; color: #00f260 !important; }
.mask-btn { background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: #fff; }
.mask-btn:hover { background: #00f260; border-color: #00f260; color: #000; }

.label-box { display: flex; justify-content: space-between; align-items: center; width: 100%; margin-bottom: 5px; }
.label-text { font-size: 14px; color: #a0aec0; font-weight: 700; }
.result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.gradient-text { font-size: 16px; font-weight: 800; background: linear-gradient(90deg, #00f260, #0575e6); -webkit-background-clip: text; color: transparent; }

/* 5. 结果区 */
.gallery-area { background: rgba(0, 0, 0, 0.2); border-radius: 12px; padding: 15px; min-height: 400px; }
.empty-state { text-align: center; padding: 40px; color: #718096; }
:deep(.el-empty__description p) { color: #718096 !important; }
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
    margin-top: 20px; /* 手机端上下堆叠时，给下半部分增加间距 */
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