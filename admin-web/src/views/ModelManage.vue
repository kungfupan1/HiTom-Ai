<template>
  <div class="model-manage">
    <!-- 页面头部 -->
    <div class="page-header">
      <h2>模型管理</h2>
      <el-button type="primary" @click="handleAdd">
        <el-icon><Plus /></el-icon>
        新增模型
      </el-button>
    </div>

    <!-- 模型卡片列表 -->
    <div v-loading="loading" class="model-cards">
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="model in models" :key="model.id">
          <el-card class="model-card" shadow="hover">
            <template #header>
              <div class="card-header">
                <div class="model-title">
                  <el-tag :type="getTypeTag(model.config_schema?.model_info?.model_type)" size="small">
                    {{ getTypeLabel(model.config_schema?.model_info?.model_type) }}
                  </el-tag>
                  <span class="model-name">{{ model.config_schema?.model_info?.display_name || model.display_name }}</span>
                </div>
                <el-switch v-model="model.is_enabled" @change="handleToggle(model)" size="small" />
              </div>
            </template>

            <div class="model-info">
              <div class="info-row">
                <span class="label">模型ID:</span>
                <span class="value">{{ model.config_schema?.model_info?.model_id || model.model_id }}</span>
              </div>
              <div class="info-row">
                <span class="label">提供商:</span>
                <span class="value">{{ model.config_schema?.model_info?.provider || model.api_provider || '-' }}</span>
              </div>
              <div class="info-row">
                <span class="label">计费模式:</span>
                <span class="value">{{ getPricingMode(model.config_schema?.pricing_rules) }}</span>
              </div>
              <div class="info-row url-row">
                <span class="label">API地址:</span>
                <el-tooltip :content="model.config_schema?.api_contract?.endpoint_url || model.base_url + model.endpoint" placement="top">
                  <span class="value url-text">{{ model.config_schema?.api_contract?.endpoint_url || (model.base_url + model.endpoint) }}</span>
                </el-tooltip>
              </div>
            </div>

            <!-- 参数标签 -->
            <div class="param-tags" v-if="model.config_schema?.ui_schema?.length">
              <el-tag v-for="ui in model.config_schema.ui_schema.slice(0, 4)" :key="ui.field_name" size="small" type="info" class="param-tag">
                {{ ui.label }}
              </el-tag>
              <el-tag v-if="model.config_schema.ui_schema.length > 4" size="small" type="info" class="param-tag">
                +{{ model.config_schema.ui_schema.length - 4 }}
              </el-tag>
            </div>

            <template #footer>
              <div class="card-actions">
                <el-button type="primary" link size="small" @click="handleEdit(model)">
                  <el-icon><Edit /></el-icon>
                  编辑
                </el-button>
                <el-popconfirm title="确定删除该模型？" @confirm="handleDelete(model)">
                  <template #reference>
                    <el-button type="danger" link size="small">
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-button>
                  </template>
                </el-popconfirm>
              </div>
            </template>
          </el-card>
        </el-col>
      </el-row>

      <!-- 空状态 -->
      <el-empty v-if="!loading && models.length === 0" description="暂无模型，点击上方按钮添加" />
    </div>

    <!-- JSON 编辑器弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑模型' : '新增模型'"
      width="90%"
      top="5vh"
      :close-on-click-modal="false"
      class="json-editor-dialog"
    >
      <div class="editor-container">
        <!-- 左侧：JSON 编辑器 -->
        <div class="editor-main">
          <div class="editor-header">
            <span>配置 JSON</span>
            <div class="editor-actions">
              <el-button size="small" @click="formatJson">格式化</el-button>
              <el-dropdown @command="loadTemplate" trigger="click">
                <el-button size="small">
                  加载模板 <el-icon class="el-icon--right"><ArrowDown /></el-icon>
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="video">视频模型模板 (Grok)</el-dropdown-item>
                    <el-dropdown-item command="text">文案模型模板 (Qwen)</el-dropdown-item>
                    <el-dropdown-item command="image">商品图模型模板</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
          <el-input
            v-model="jsonContent"
            type="textarea"
            :rows="25"
            placeholder="请输入模型配置 JSON..."
            class="json-textarea"
            :class="{ 'has-error': jsonError }"
          />
          <div class="error-message" v-if="jsonError">
            <el-icon><WarningFilled /></el-icon>
            {{ jsonError }}
          </div>
        </div>

        <!-- 右侧：预览面板 -->
        <div class="editor-preview">
          <div class="preview-header">配置预览</div>
          <div class="preview-content" v-if="parsedConfig">
            <div class="preview-section">
              <h4>基本信息</h4>
              <p><strong>模型ID:</strong> {{ parsedConfig.model_info?.model_id }}</p>
              <p><strong>显示名称:</strong> {{ parsedConfig.model_info?.display_name }}</p>
              <p><strong>类型:</strong> {{ parsedConfig.model_info?.model_type }}</p>
              <p><strong>提供商:</strong> {{ parsedConfig.model_info?.provider }}</p>
            </div>
            <div class="preview-section">
              <h4>API 配置</h4>
              <p><strong>端点:</strong> {{ parsedConfig.api_contract?.endpoint_url }}</p>
              <p><strong>占位符:</strong> {{ parsedConfig.api_contract?.placeholder }}</p>
            </div>
            <div class="preview-section">
              <h4>计费规则</h4>
              <p><strong>模式:</strong> {{ parsedConfig.pricing_rules?.mode === 'fixed' ? '固定计费' : '动态计费' }}</p>
              <p v-if="parsedConfig.pricing_rules?.mode === 'fixed'">
                <strong>固定费用:</strong> {{ parsedConfig.pricing_rules?.fixed_cost }} 积分
              </p>
              <p v-else>
                <strong>单价:</strong> {{ parsedConfig.pricing_rules?.unit_price }} 积分/{{ parsedConfig.pricing_rules?.multiply_by_field }}
              </p>
            </div>
            <div class="preview-section" v-if="parsedConfig.ui_schema?.length">
              <h4>UI 字段 ({{ parsedConfig.ui_schema.length }}个)</h4>
              <el-tag v-for="ui in parsedConfig.ui_schema" :key="ui.field_name" size="small" class="preview-tag">
                {{ ui.label }} ({{ ui.ui_type }})
              </el-tag>
            </div>
          </div>
          <el-empty v-else description="JSON 格式正确后显示预览" :image-size="60" />
        </div>
      </div>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSave" :loading="saving" :disabled="!!jsonError">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Edit, Delete, ArrowDown, WarningFilled } from '@element-plus/icons-vue'
import request from '@/api/request'

// 状态
const loading = ref(false)
const saving = ref(false)
const models = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentModel = ref(null)
const jsonContent = ref('')
const jsonError = ref('')

// JSON 模板
const JSON_TEMPLATES = {
  video: {
    model_info: {
      model_id: "grok-video-3",
      display_name: "Grok Video 3.0",
      model_type: "video",
      provider: "T8Star",
      description: "xAI Grok 视频生成模型"
    },
    api_contract: {
      endpoint_url: "https://ai.t8star.cn/v2/videos/generations",
      status_url: "https://ai.t8star.cn/v2/videos/generations/{task_id}",
      placeholder: "T8STAR_API_KEY",
      method: "POST",
      status_method: "GET",
      timeout: 180000
    },
    pricing_rules: {
      mode: "dynamic",
      unit_price: 2,
      multiply_by_field: "duration",
      duration_pricing: { "5": 2, "10": 2, "15": 5, "25": 25 },
      resolution_pricing: { "720P": 0, "1080P": 2 }
    },
    ui_schema: [
      { field_name: "aspect_ratio", label: "画面比例", ui_type: "select", options: [{"label": "9:16", "value": "9:16"}, {"label": "16:9", "value": "16:9"}], default_value: "9:16", required: true },
      { field_name: "duration", label: "时长(秒)", ui_type: "select", options: [{"label": "5秒", "value": 5}, {"label": "10秒", "value": 10}], default_value: 10, required: true }
    ],
    request_mapping: {
      dynamic_params: { "model": "model", "prompt": "prompt", "duration": "duration", "aspect_ratio": "ratio" },
      static_params: {}
    },
    response_mapping: {
      task_id_path: "task_id",
      status_path: "status",
      progress_path: "progress",
      result_url_path: "data.output",
      error_path: "fail_reason"
    }
  },
  text: {
    model_info: {
      model_id: "Qwen/Qwen3-VL-30B-A3B-Instruct",
      display_name: "Qwen3-VL 看图写文案",
      model_type: "text",
      provider: "ModelScope",
      description: "通义千问视觉语言模型"
    },
    api_contract: {
      endpoint_url: "https://api-inference.modelscope.cn/v1/chat/completions",
      placeholder: "MODELSCOPE_API_KEY",
      method: "POST",
      timeout: 120000
    },
    pricing_rules: {
      mode: "fixed",
      fixed_cost: 0
    },
    ui_schema: [
      { field_name: "product_type", label: "产品类型", ui_type: "input", default_value: "通用产品" },
      { field_name: "target_lang", label: "目标语言", ui_type: "select", options: [{"label": "中文", "value": "中文"}, {"label": "英语", "value": "英语"}], default_value: "中文" }
    ],
    request_mapping: {
      dynamic_params: { "model": "model", "messages": "messages" },
      static_params: { "model": "Qwen/Qwen3-VL-30B-A3B-Instruct", "max_tokens": 1500, "temperature": 0.7 }
    },
    response_mapping: {
      content_path: "choices[0].message.content"
    }
  },
  image: {
    model_info: {
      model_id: "nano-banana-2",
      display_name: "商品图生成",
      model_type: "image",
      provider: "T8Star",
      description: "电商商品图生成模型"
    },
    api_contract: {
      endpoint_url: "https://ai.t8star.cn/v1/images/generations",
      placeholder: "T8STAR_API_KEY",
      method: "POST",
      timeout: 120000
    },
    pricing_rules: {
      mode: "fixed",
      fixed_cost: 2
    },
    ui_schema: [
      { field_name: "aspect_ratio", label: "画面比例", ui_type: "select", options: [{"label": "3:4", "value": "3:4"}, {"label": "1:1", "value": "1:1"}], default_value: "3:4" },
      { field_name: "resolution", label: "分辨率", ui_type: "select", options: [{"label": "1K", "value": "1K"}, {"label": "2K", "value": "2K"}], default_value: "1K" }
    ],
    request_mapping: {
      dynamic_params: { "model": "model", "prompt": "prompt", "size": "size" },
      static_params: { "response_format": "url" }
    },
    response_mapping: {
      result_url_path: "data[0].url"
    }
  }
}

// 解析后的配置（用于预览）
const parsedConfig = computed(() => {
  if (!jsonContent.value || jsonError.value) return null
  try {
    return JSON.parse(jsonContent.value)
  } catch {
    return null
  }
})

// 监听 JSON 变化进行校验
watch(jsonContent, (val) => {
  if (!val) {
    jsonError.value = ''
    return
  }
  try {
    JSON.parse(val)
    jsonError.value = ''
  } catch (e) {
    jsonError.value = `JSON 格式错误: ${e.message}`
  }
})

// 加载模型列表
const loadModels = async () => {
  loading.value = true
  try {
    const res = await request.get('/admin/models')
    models.value = res.map(m => {
      // 尝试解析 config_schema
      if (m.config_schema && typeof m.config_schema === 'string') {
        try {
          m.config_schema = JSON.parse(m.config_schema)
        } catch {}
      }
      return m
    })
  } catch (error) {
    console.error(error)
    ElMessage.error('加载模型列表失败')
  } finally {
    loading.value = false
  }
}

// 新增模型
const handleAdd = () => {
  isEdit.value = false
  currentModel.value = null
  jsonContent.value = JSON.stringify(JSON_TEMPLATES.video, null, 2)
  jsonError.value = ''
  dialogVisible.value = true
}

// 编辑模型
const handleEdit = (model) => {
  isEdit.value = true
  currentModel.value = model
  // 优先使用 config_schema，否则构建兼容格式
  if (model.config_schema) {
    jsonContent.value = JSON.stringify(model.config_schema, null, 2)
  } else {
    // 兼容旧数据，构建 config_schema
    const schema = {
      model_info: {
        model_id: model.model_id,
        display_name: model.display_name,
        model_type: model.model_type,
        provider: model.api_provider,
        description: ''
      },
      api_contract: {
        endpoint_url: model.base_url + model.endpoint,
        placeholder: model.api_provider === 't8star' ? 'T8STAR_API_KEY' : 'MODELSCOPE_API_KEY',
        method: 'POST'
      },
      pricing_rules: {
        mode: model.billing_mode === 'duration' ? 'dynamic' : 'fixed',
        fixed_cost: model.base_price
      },
      ui_schema: [],
      request_mapping: model.request_mapping || {},
      response_mapping: model.response_mapping || {}
    }
    jsonContent.value = JSON.stringify(schema, null, 2)
  }
  jsonError.value = ''
  dialogVisible.value = true
}

// 删除模型
const handleDelete = async (model) => {
  try {
    await request.delete(`/admin/models/${model.id}`)
    ElMessage.success('删除成功')
    loadModels()
  } catch (error) {
    console.error(error)
    ElMessage.error('删除失败')
  }
}

// 启用/禁用
const handleToggle = async (model) => {
  try {
    await request.post(`/admin/models/${model.id}/toggle`)
    ElMessage.success(model.is_enabled ? '已启用' : '已禁用')
  } catch (error) {
    model.is_enabled = !model.is_enabled
    ElMessage.error('操作失败')
  }
}

// 加载模板
const loadTemplate = (type) => {
  jsonContent.value = JSON.stringify(JSON_TEMPLATES[type], null, 2)
}

// 格式化 JSON
const formatJson = () => {
  try {
    const parsed = JSON.parse(jsonContent.value)
    jsonContent.value = JSON.stringify(parsed, null, 2)
    ElMessage.success('格式化成功')
  } catch (e) {
    ElMessage.error('JSON 格式错误，无法格式化')
  }
}

// 保存模型
const handleSave = async () => {
  if (jsonError.value) return

  let config
  try {
    config = JSON.parse(jsonContent.value)
  } catch (e) {
    ElMessage.error('JSON 格式错误')
    return
  }

  // 校验必填字段
  if (!config.model_info?.model_id) {
    ElMessage.error('model_info.model_id 不能为空')
    return
  }
  if (!config.model_info?.display_name) {
    ElMessage.error('model_info.display_name 不能为空')
    return
  }
  if (!config.model_info?.model_type) {
    ElMessage.error('model_info.model_type 不能为空')
    return
  }
  if (!config.api_contract?.endpoint_url) {
    ElMessage.error('api_contract.endpoint_url 不能为空')
    return
  }

  saving.value = true
  try {
    const payload = {
      model_id: config.model_info.model_id,
      display_name: config.model_info.display_name,
      model_type: config.model_info.model_type,
      api_provider: config.model_info.provider,
      is_enabled: true,
      config_schema: config,  // 发送解析后的对象，而不是字符串
      // 兼容旧字段
      base_url: '',
      endpoint: '',
      billing_mode: config.pricing_rules?.mode === 'fixed' ? 'per_use' : 'duration',
      base_price: config.pricing_rules?.fixed_cost || 0
    }

    // 解析 URL
    try {
      const url = new URL(config.api_contract.endpoint_url)
      payload.base_url = url.origin
      payload.endpoint = url.pathname
    } catch {}

    if (isEdit.value && currentModel.value) {
      await request.put(`/admin/models/${currentModel.value.id}`, payload)
      ElMessage.success('更新成功')
    } else {
      await request.post('/admin/models', payload)
      ElMessage.success('创建成功')
    }

    dialogVisible.value = false
    loadModels()
  } catch (error) {
    console.error(error)
    ElMessage.error(error.response?.data?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

// 辅助函数
const getTypeTag = (type) => {
  const map = { video: 'danger', image: 'primary', text: 'success' }
  return map[type] || 'info'
}

const getTypeLabel = (type) => {
  const map = { video: '视频', image: '图片', text: '文案' }
  return map[type] || type || '未知'
}

const getPricingMode = (pricing) => {
  if (!pricing) return '-'
  if (pricing.mode === 'fixed') return `固定 ${pricing.fixed_cost || 0} 积分`
  return `动态 (单价: ${pricing.unit_price || 0})`
}

onMounted(() => {
  loadModels()
})
</script>

<style scoped>
.model-manage {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

/* 卡片样式 */
.model-cards {
  min-height: 400px;
}

.model-card {
  margin-bottom: 20px;
  transition: all 0.3s;
}

.model-card:hover {
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.model-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.model-name {
  font-weight: 600;
  color: #303133;
}

.model-info {
  font-size: 13px;
}

.info-row {
  display: flex;
  margin-bottom: 8px;
}

.info-row .label {
  color: #909399;
  width: 70px;
  flex-shrink: 0;
}

.info-row .value {
  color: #606266;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.url-row .value {
  max-width: 180px;
}

.url-text {
  cursor: pointer;
  color: #409eff;
}

.param-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

.param-tag {
  font-size: 11px;
}

.card-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* JSON 编辑器弹窗 */
.json-editor-dialog :deep(.el-dialog__body) {
  padding: 10px 20px;
}

.editor-container {
  display: flex;
  gap: 20px;
  height: 70vh;
}

.editor-main {
  flex: 2;
  display: flex;
  flex-direction: column;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-weight: 600;
  color: #303133;
}

.editor-actions {
  display: flex;
  gap: 8px;
}

.json-textarea {
  flex: 1;
}

.json-textarea :deep(.el-textarea__inner) {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
  line-height: 1.5;
  background-color: #f8f9fa;
}

.json-textarea.has-error :deep(.el-textarea__inner) {
  border-color: #f56c6c;
}

.error-message {
  color: #f56c6c;
  font-size: 12px;
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.editor-preview {
  flex: 1;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 16px;
  overflow-y: auto;
}

.preview-header {
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e4e7ed;
}

.preview-section {
  margin-bottom: 16px;
}

.preview-section h4 {
  margin: 0 0 8px;
  font-size: 14px;
  color: #409eff;
}

.preview-section p {
  margin: 4px 0;
  font-size: 13px;
  color: #606266;
}

.preview-tag {
  margin: 2px;
}

/* 响应式 */
@media (max-width: 1200px) {
  .editor-container {
    flex-direction: column;
    height: auto;
  }

  .editor-main {
    min-height: 400px;
  }

  .editor-preview {
    max-height: 300px;
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>