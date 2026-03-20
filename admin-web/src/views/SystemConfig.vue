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

        <el-row :gutter="20">
          <el-col :xs="24" :sm="12">
            <el-form-item label="注册赠送积分">
              <el-input-number v-model="form.signup_bonus" :min="0" />
            </el-form-item>
          </el-col>
          <el-col :xs="24" :sm="12">
            <el-form-item label="图片生成基础价">
              <el-input-number v-model="form.image_base_price" :min="0" />
              <span class="form-tip">积分/张</span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">费用说明</el-divider>

        <el-form-item label="费用说明文案">
          <el-input
            v-model="form.pricing_description"
            type="textarea"
            :rows="6"
            placeholder="展示给用户的费用说明，支持换行"
          />
        </el-form-item>

        <el-divider content-position="left">服务配置</el-divider>

        <el-form-item label="腾讯云函数 URL">
          <el-input
            v-model="form.tencent_function_url"
            placeholder="https://xxx.ap-guangzhou.tencentscf.com"
          />
          <div class="form-tip">AI 生成服务的腾讯云函数地址，必须配置才能使用 AI 功能</div>
        </el-form-item>

        <el-divider content-position="left">AI 提示词配置</el-divider>

        <el-form-item label="文案生成系统提示词">
          <el-input
            v-model="form.text_system_prompt"
            type="textarea"
            :rows="10"
            placeholder="用于看图写文案功能的系统提示词，支持变量替换..."
          />
          <div class="form-tip">
            支持变量: {target_lang} 目标语言、{product_type} 产品类型、{design_style} 设计风格、{target_num} 生成数量
          </div>
        </el-form-item>

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

const form = reactive({
  signup_bonus: 10,
  image_base_price: 2,
  pricing_description: '',
  tencent_function_url: '',
  text_system_prompt: ''
})

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
    form.signup_bonus = parseInt(res.signup_bonus?.value || '10')
    form.image_base_price = parseInt(res.image_base_price?.value || '2')
    form.pricing_description = res.pricing_description?.value || ''
    form.tencent_function_url = res.tencent_function_url?.value || ''
    form.text_system_prompt = res.text_system_prompt?.value || ''
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
        image_base_price: String(form.image_base_price),
        pricing_description: form.pricing_description,
        tencent_function_url: form.tencent_function_url,
        text_system_prompt: form.text_system_prompt
      }
    })
    ElMessage.success('保存成功')
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
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