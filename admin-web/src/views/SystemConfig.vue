<template>
  <div class="system-config">
    <el-card>
      <template #header>
        <span>系统配置</span>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        label-width="140px"
        class="config-form"
      >
        <el-divider content-position="left">积分规则</el-divider>

        <el-form-item label="注册赠送积分">
          <el-input-number v-model="form.signup_bonus" :min="0" />
        </el-form-item>

        <el-divider content-position="left">服务配置</el-divider>

        <el-form-item label="腾讯云函数 URL">
          <el-input
            v-model="form.tencent_function_url"
            placeholder="https://xxx.ap-guangzhou.tencentscf.com"
          />
          <div class="form-tip">AI 生成服务的腾讯云函数地址，必须配置才能使用 AI 功能</div>
        </el-form-item>

        <el-divider content-position="left">AI 系统提示词配置</el-divider>

        <el-collapse v-model="activePromptCollapse" class="prompt-collapse">
          <!-- 1. 看图写卖点提示词 -->
          <el-collapse-item title="看图写卖点提示词 (电商主图)" name="selling">
            <template #title>
              <div class="collapse-title">
                <span class="title-text">看图写卖点提示词</span>
                <el-tag type="success" size="small">电商主图</el-tag>
              </div>
            </template>
            <el-form-item label="系统提示词">
              <el-input
                v-model="form.image_selling_points_prompt"
                type="textarea"
                :rows="12"
                placeholder="根据产品图片生成多组卖点文案..."
              />
            </el-form-item>
            <div class="form-tip variables-tip">
              <strong>支持变量:</strong>
              <el-tag size="small" v-for="v in ['{lang_eng}', '{product_type}', '{design_style}', '{target_num}', '{format_example}']" :key="v" class="var-tag">{{ v }}</el-tag>
            </div>
            <el-button size="small" @click="resetPrompt('selling')">恢复默认</el-button>
          </el-collapse-item>

          <!-- 2. 生图提示词规划 -->
          <el-collapse-item title="生图提示词规划 (电商主图)" name="image">
            <template #title>
              <div class="collapse-title">
                <span class="title-text">生图提示词规划</span>
                <el-tag type="primary" size="small">电商主图</el-tag>
              </div>
            </template>
            <el-form-item label="系统提示词">
              <el-input
                v-model="form.image_generation_prompt"
                type="textarea"
                :rows="18"
                placeholder="根据产品信息和卖点规划多屏详情页的生图提示词..."
              />
            </el-form-item>
            <div class="form-tip variables-tip">
              <strong>支持变量:</strong>
              <el-tag size="small" v-for="v in ['{num_screens}', '{lang_eng}', '{product_type}', '{selling_points}', '{design_style}']" :key="v" class="var-tag">{{ v }}</el-tag>
            </div>
            <el-button size="small" @click="resetPrompt('image')">恢复默认</el-button>
          </el-collapse-item>

          <!-- 3. 视频分镜提示词 -->
          <el-collapse-item title="视频分镜提示词 (视频生成)" name="video">
            <template #title>
              <div class="collapse-title">
                <span class="title-text">视频分镜提示词</span>
                <el-tag type="danger" size="small">视频生成</el-tag>
              </div>
            </template>
            <el-form-item label="系统提示词">
              <el-input
                v-model="form.video_script_prompt"
                type="textarea"
                :rows="16"
                placeholder="根据产品信息生成视频分镜脚本..."
              />
            </el-form-item>
            <div class="form-tip variables-tip">
              <strong>支持变量:</strong>
              <el-tag size="small" v-for="v in ['{target_lang}', '{region_sel}', '{style_sel}', '{category}', '{region_prompt}', '{text_instruction}', '{overlay_action}', '{output_req}']" :key="v" class="var-tag">{{ v }}</el-tag>
            </div>
            <el-button size="small" @click="resetPrompt('video')">恢复默认</el-button>
          </el-collapse-item>
        </el-collapse>

        <el-form-item>
          <el-button type="primary" @click="handleSave" :loading="loading">
            保存配置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- API 密钥管理 -->
    <el-card class="api-keys-card">
      <template #header>
        <div class="card-header">
          <span>API 密钥管理</span>
          <el-tag type="info" size="small">支持多 Key 负载均衡</el-tag>
        </div>
      </template>

      <el-row :gutter="24">
        <!-- T8Star Keys -->
        <el-col :xs="24" :lg="12">
          <div class="key-section">
            <div class="key-section-header">
              <span class="key-section-title">T8Star</span>
              <span class="key-section-desc">视频生成服务</span>
              <el-tag :type="t8starKeys.length > 0 ? 'success' : 'danger'" size="small">
                {{ t8starKeys.length }} 个
              </el-tag>
            </div>

            <div class="key-list">
              <div v-for="key in t8starKeys" :key="key.id" class="key-item">
                <span class="key-name">{{ key.key_name }}</span>
                <div class="key-input-wrap">
                  <el-input
                    v-model="key.inputValue"
                    :placeholder="key.key_value || '输入新的 API Key'"
                    show-password
                    size="default"
                  />
                </div>
                <div class="key-actions">
                  <el-button
                    type="success"
                    :icon="Check"
                    circle
                    size="small"
                    @click="saveKey(key)"
                    :loading="key.saving"
                    title="保存"
                  />
                  <el-button
                    type="danger"
                    :icon="Delete"
                    circle
                    size="small"
                    @click="deleteKey(key)"
                    title="删除"
                  />
                </div>
              </div>

              <!-- 添加新 Key -->
              <div v-if="newT8starKey.visible" class="key-item key-item-new">
                <span class="key-name">{{ newT8starKey.name }}</span>
                <div class="key-input-wrap">
                  <el-input
                    v-model="newT8starKey.value"
                    placeholder="输入 API Key"
                    show-password
                    size="default"
                  />
                </div>
                <div class="key-actions">
                  <el-button
                    type="success"
                    :icon="Check"
                    circle
                    size="small"
                    @click="confirmAddKey('t8star')"
                    :loading="newT8starKey.saving"
                    title="保存"
                  />
                  <el-button
                    type="info"
                    :icon="Close"
                    circle
                    size="small"
                    @click="cancelAddKey('t8star')"
                    title="取消"
                  />
                </div>
              </div>

              <el-button
                v-if="!newT8starKey.visible"
                type="primary"
                :icon="Plus"
                size="small"
                plain
                @click="showAddKey('t8star')"
              >
                添加 Key
              </el-button>
            </div>
          </div>
        </el-col>

        <!-- ModelScope Keys -->
        <el-col :xs="24" :lg="12">
          <div class="key-section">
            <div class="key-section-header">
              <span class="key-section-title">ModelScope</span>
              <span class="key-section-desc">看图文案服务</span>
              <el-tag :type="modelscopeKeys.length > 0 ? 'success' : 'danger'" size="small">
                {{ modelscopeKeys.length }} 个
              </el-tag>
            </div>

            <div class="key-list">
              <div v-for="key in modelscopeKeys" :key="key.id" class="key-item">
                <span class="key-name">{{ key.key_name }}</span>
                <div class="key-input-wrap">
                  <el-input
                    v-model="key.inputValue"
                    :placeholder="key.key_value || '输入新的 API Key'"
                    show-password
                    size="default"
                  />
                </div>
                <div class="key-actions">
                  <el-button
                    type="success"
                    :icon="Check"
                    circle
                    size="small"
                    @click="saveKey(key)"
                    :loading="key.saving"
                    title="保存"
                  />
                  <el-button
                    type="danger"
                    :icon="Delete"
                    circle
                    size="small"
                    @click="deleteKey(key)"
                    title="删除"
                  />
                </div>
              </div>

              <!-- 添加新 Key -->
              <div v-if="newModelscopeKey.visible" class="key-item key-item-new">
                <span class="key-name">{{ newModelscopeKey.name }}</span>
                <div class="key-input-wrap">
                  <el-input
                    v-model="newModelscopeKey.value"
                    placeholder="输入 API Key"
                    show-password
                    size="default"
                  />
                </div>
                <div class="key-actions">
                  <el-button
                    type="success"
                    :icon="Check"
                    circle
                    size="small"
                    @click="confirmAddKey('modelscope')"
                    :loading="newModelscopeKey.saving"
                    title="保存"
                  />
                  <el-button
                    type="info"
                    :icon="Close"
                    circle
                    size="small"
                    @click="cancelAddKey('modelscope')"
                    title="取消"
                  />
                </div>
              </div>

              <el-button
                v-if="!newModelscopeKey.visible"
                type="primary"
                :icon="Plus"
                size="small"
                plain
                @click="showAddKey('modelscope')"
              >
                添加 Key
              </el-button>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Check, Close, Plus, Delete } from '@element-plus/icons-vue'
import request from '@/api/request'

const formRef = ref(null)
const loading = ref(false)
const activePromptCollapse = ref(['selling'])

const form = reactive({
  signup_bonus: 0,
  tencent_function_url: '',
  // 三个独立的系统提示词
  image_selling_points_prompt: '',
  image_generation_prompt: '',
  video_script_prompt: ''
})

// 默认提示词模板
const DEFAULT_PROMPTS = {
  selling: `[Role] Senior E-commerce Copywriter specialized in **{lang_eng}**.

[Input Info]
- Product Category: {product_type}
- Desired Style: {design_style}
- **TARGET LANGUAGE: {lang_eng}**

[Task]
Analyze these product images. Combine visual features with "{product_type}" to write catchy 'Main Title' and 'Subtitle'.

[Requirement]
Generate exactly **{target_num} distinct sets**.

[CRITICAL RULES]
1. **OUTPUT MUST BE IN {lang_eng}**.
2. Do NOT use English unless the target language is English.
3. Even if the input is Chinese/English, translate your thoughts to **{lang_eng}**.

[Format]:
{format_example}

(Direct output only. Language: {lang_eng})`,

  image: `[角色] 你是一名资深电商详情页设计师与 AI 文生图提示词工程师。
[任务目标] 根据产品信息，规划并生成 **{num_screens} 屏** 详情页的文生图提示词。

[强制语言规则 - STRICTLY ENFORCED]
1. **目标语言锁定**：所有的"主文案"和"副文案"必须严格使用 **{lang_eng}**。
2. **拒绝干扰**：即使用户的【核心卖点】或【产品名称】中包含其他语言（如英文、中文混合），你必须将其翻译或转换为 **{lang_eng}** 输出。
3. **纯净性**：绝对禁止中英混杂。如果是英文目标语言，不要出现任何汉字；如果是中文目标语言，不要出现非必要的英文。

[视觉纯净规则 - 绝对禁止]
1. **文字隔离**：画面中除主副文案外，**严禁**出现任何装饰性汉字、印章。
2. **字体隔离**：必须使用国际通用术语：如 "Sans-serif", "Serif", "Bold Modern Font"。
3. **元素隔离**：必须使用符合该语言语境的背景元素。

[强制执行规则]
1. **数量严格匹配**：用户要求生成 {num_screens} 屏，你必须输出 **{num_screens} 条** 独立的提示词。
2. **输出结构**：每屏内容必须包含："主文案、副文案、设计与排版、画面主体与构图、画质与细节"。
3. **多图参考**：用户提供了多张参考图，请综合分析这些图片的特征（角度、细节、场景）来规划画面。

[输出格式模板]
请严格按照以下格式输出（不要输出表格，只输出文本段落）：

第1屏：
主文案："..."
副文案："..."
文案设计与排版：...
画面主体与构图：...
画质与细节：...

第2屏：
...
（以此类推，直到第 {num_screens} 屏）`,

  video: `You are an expert AI Video Director for E-commerce.
Task: Write a structured video prompt for Sora.

CONTEXT:
- {text_instruction}
- Region: {region_sel}
- Style: {style_sel}
- Category: {category}

MANDATORY FORMAT:
[Type]: {style_sel} Video
[Structure]: Hook -> Demo -> Benefit -> CTA
{region_prompt}

[Actions]:
- (Scene 1: Hook) Opening. Dialogue in {target_lang}: "..."
- (Scene 2: Demo) Action.
{overlay_action}
- (Scene 4: CTA) Presenter recommending. Dialogue in {target_lang}: "..."

[Camera]: ...
[Sound]: ...`
}

const apiKeys = ref([])

// 新增 Key 的临时状态
const newT8starKey = reactive({
  visible: false,
  name: '',
  value: '',
  saving: false
})

const newModelscopeKey = reactive({
  visible: false,
  name: '',
  value: '',
  saving: false
})

const t8starKeys = computed(() => apiKeys.value.filter(k => k.provider === 't8star'))
const modelscopeKeys = computed(() => apiKeys.value.filter(k => k.provider === 'modelscope'))

// 生成 Key 名称（避免重复）
const generateKeyName = (provider) => {
  const keys = apiKeys.value.filter(k => k.provider === provider)
  let maxNum = 0
  const prefix = `${provider}_key_`
  for (const k of keys) {
    if (k.key_name && k.key_name.startsWith(prefix)) {
      const num = parseInt(k.key_name.replace(prefix, ''), 10)
      if (!isNaN(num) && num > maxNum) {
        maxNum = num
      }
    }
  }
  return `${prefix}${maxNum + 1}`
}

// 加载配置
const loadConfig = async () => {
  try {
    const res = await request.get('/admin/config')
    form.signup_bonus = parseInt(res.signup_bonus?.value || '0')
    form.tencent_function_url = res.tencent_function_url?.value || ''
    // 加载三个系统提示词
    form.image_selling_points_prompt = res.image_selling_points_prompt?.value || DEFAULT_PROMPTS.selling
    form.image_generation_prompt = res.image_generation_prompt?.value || DEFAULT_PROMPTS.image
    form.video_script_prompt = res.video_script_prompt?.value || DEFAULT_PROMPTS.video
  } catch (error) {
    console.error(error)
  }
}

// 加载 API Keys
const loadAPIKeys = async () => {
  try {
    const res = await request.get('/admin/api-keys')
    apiKeys.value = res.map(k => ({
      ...k,
      inputValue: '',
      saving: false
    }))
  } catch (error) {
    console.error(error)
  }
}

// 保存配置
const handleSave = async () => {
  loading.value = true
  try {
    await request.put('/admin/config', {
      configs: {
        signup_bonus: String(form.signup_bonus),
        tencent_function_url: form.tencent_function_url,
        // 保存三个系统提示词
        image_selling_points_prompt: form.image_selling_points_prompt,
        image_generation_prompt: form.image_generation_prompt,
        video_script_prompt: form.video_script_prompt
      }
    })
    ElMessage.success('保存成功')
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 恢复默认提示词
const resetPrompt = (type) => {
  if (type === 'selling') {
    form.image_selling_points_prompt = DEFAULT_PROMPTS.selling
  } else if (type === 'image') {
    form.image_generation_prompt = DEFAULT_PROMPTS.image
  } else if (type === 'video') {
    form.video_script_prompt = DEFAULT_PROMPTS.video
  }
  ElMessage.success('已恢复默认提示词')
}

// 显示添加 Key 输入框
const showAddKey = (provider) => {
  if (provider === 't8star') {
    newT8starKey.visible = true
    newT8starKey.name = generateKeyName('t8star')
    newT8starKey.value = ''
    newT8starKey.saving = false
  } else {
    newModelscopeKey.visible = true
    newModelscopeKey.name = generateKeyName('modelscope')
    newModelscopeKey.value = ''
    newModelscopeKey.saving = false
  }
}

// 取消添加
const cancelAddKey = (provider) => {
  if (provider === 't8star') {
    newT8starKey.visible = false
    newT8starKey.value = ''
  } else {
    newModelscopeKey.visible = false
    newModelscopeKey.value = ''
  }
}

// 确认添加 Key
const confirmAddKey = async (provider) => {
  const keyData = provider === 't8star' ? newT8starKey : newModelscopeKey

  if (!keyData.value) {
    return ElMessage.warning('请输入 API Key')
  }

  keyData.saving = true
  try {
    await request.post('/admin/api-keys', {
      provider: provider,
      key_name: keyData.name,
      key_value: keyData.value,
      description: ''
    })
    ElMessage.success('添加成功')
    keyData.visible = false
    keyData.value = ''
    loadAPIKeys()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '添加失败')
  } finally {
    keyData.saving = false
  }
}

// 保存 Key（更新）
const saveKey = async (key) => {
  if (!key.inputValue) {
    return ElMessage.warning('请输入新的 API Key 值')
  }

  key.saving = true
  try {
    await request.put(`/admin/api-keys/${key.id}`, {
      key_value: key.inputValue
    })
    ElMessage.success('更新成功')
    loadAPIKeys()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '更新失败')
  } finally {
    key.saving = false
  }
}

// 删除 Key
const deleteKey = async (key) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 "${key.key_name}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await request.delete(`/admin/api-keys/${key.id}`)
    ElMessage.success('删除成功')
    loadAPIKeys()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadConfig()
  loadAPIKeys()
})
</script>

<style scoped>
.system-config {
  padding: 0;
}

.config-form {
  max-width: 800px;
}

.form-tip {
  margin-left: 8px;
  color: #909399;
  font-size: 12px;
}

.variables-tip {
  margin: 10px 0;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

.var-tag {
  margin: 2px 4px;
}

.prompt-collapse {
  margin-bottom: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.prompt-collapse :deep(.el-collapse-item__header) {
  background: #f5f7fa;
  padding: 0 16px;
  height: 50px;
}

.prompt-collapse :deep(.el-collapse-item__wrap) {
  border-bottom: none;
}

.prompt-collapse :deep(.el-collapse-item__content) {
  padding: 16px;
}

.collapse-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-text {
  font-weight: 600;
  color: #303133;
}

.api-keys-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.key-section {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
  height: 100%;
  min-height: 200px;
}

.key-section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.key-section-title {
  font-weight: 600;
  font-size: 15px;
  color: #303133;
}

.key-section-desc {
  font-size: 12px;
  color: #909399;
}

.key-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.key-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #fff;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
  flex-wrap: wrap;
}

.key-item-new {
  border: 1px dashed #409eff;
  background: #ecf5ff;
}

.key-name {
  min-width: 120px;
  font-size: 13px;
  color: #606266;
  font-family: monospace;
}

.key-input-wrap {
  flex: 1;
  min-width: 200px;
}

.key-actions {
  display: flex;
  gap: 8px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .key-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .key-name {
    min-width: auto;
  }

  .key-input-wrap {
    width: 100%;
  }

  .key-actions {
    align-self: flex-end;
  }
}
</style>