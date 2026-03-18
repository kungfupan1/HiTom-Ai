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
        style="max-width: 600px;"
      >
        <el-divider content-position="left">积分规则</el-divider>

        <el-form-item label="注册赠送积分">
          <el-input-number v-model="form.signup_bonus" :min="0" />
          <span style="margin-left: 8px; color: #888;">新用户注册赠送</span>
        </el-form-item>

        <el-form-item label="图片生成基础价">
          <el-input-number v-model="form.image_base_price" :min="0" />
          <span style="margin-left: 8px; color: #888;">积分/张</span>
        </el-form-item>

        <el-divider content-position="left">费用说明</el-divider>

        <el-form-item label="费用说明文案">
          <el-input
            v-model="form.pricing_description"
            type="textarea"
            :rows="8"
            placeholder="展示给用户的费用说明，支持换行"
          />
        </el-form-item>

        <el-alert type="info" :closable="false" style="margin-bottom: 20px;">
          <template #title>
            提示：此费用说明将在用户端页面展示，帮助用户了解计费规则
          </template>
        </el-alert>

        <el-divider content-position="left">Vercel Functions 配置</el-divider>

        <el-form-item label="Vercel URL">
          <el-input v-model="form.vercel_url" placeholder="https://your-app.vercel.app" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSave" :loading="loading">
            保存配置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- API 密钥管理 -->
    <el-card style="margin-top: 20px;">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>API 密钥管理</span>
          <el-button type="primary" size="small" @click="showAddDialog">
            + 添加密钥
          </el-button>
        </div>
      </template>

      <el-alert type="info" :closable="false" style="margin-bottom: 16px;">
        <template #title>
          支持配置多个 API Key 实现负载均衡（薅羊毛策略），系统会随机选择一个可用的 Key
        </template>
      </el-alert>

      <!-- T8Star Keys -->
      <div class="key-section">
        <div class="key-section-header">
          <span class="key-section-title">🎬 T8Star API Keys（视频生成）</span>
          <el-tag :type="t8starKeys.length > 0 ? 'success' : 'danger'" size="small">
            {{ t8starKeys.length }} 个可用
          </el-tag>
        </div>
        <el-table :data="t8starKeys" stripe v-if="t8starKeys.length > 0">
          <el-table-column prop="key_name" label="名称" width="180" />
          <el-table-column prop="key_value" label="Key（已掩码）" />
          <el-table-column prop="use_count" label="使用次数" width="100" />
          <el-table-column prop="is_enabled" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_enabled ? 'success' : 'info'" size="small">
                {{ row.is_enabled ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="showEditDialog(row)">编辑</el-button>
              <el-button link type="primary" size="small" @click="toggleKeyStatus(row)">
                {{ row.is_enabled ? '禁用' : '启用' }}
              </el-button>
              <el-button link type="danger" size="small" @click="handleDeleteKey(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无 T8Star API Key" :image-size="60" />
      </div>

      <!-- ModelScope Keys -->
      <div class="key-section" style="margin-top: 20px;">
        <div class="key-section-header">
          <span class="key-section-title">🤖 ModelScope API Keys（看图文案）</span>
          <el-tag :type="modelscopeKeys.length > 0 ? 'success' : 'danger'" size="small">
            {{ modelscopeKeys.length }} 个可用
          </el-tag>
        </div>
        <el-table :data="modelscopeKeys" stripe v-if="modelscopeKeys.length > 0">
          <el-table-column prop="key_name" label="名称" width="180" />
          <el-table-column prop="key_value" label="Key（已掩码）" />
          <el-table-column prop="use_count" label="使用次数" width="100" />
          <el-table-column prop="is_enabled" label="状态" width="80">
            <template #default="{ row }">
              <el-tag :type="row.is_enabled ? 'success' : 'info'" size="small">
                {{ row.is_enabled ? '启用' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="180">
            <template #default="{ row }">
              <el-button link type="primary" size="small" @click="showEditDialog(row)">编辑</el-button>
              <el-button link type="primary" size="small" @click="toggleKeyStatus(row)">
                {{ row.is_enabled ? '禁用' : '启用' }}
              </el-button>
              <el-button link type="danger" size="small" @click="handleDeleteKey(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-else description="暂无 ModelScope API Key" :image-size="60" />
      </div>
    </el-card>

    <!-- 添加/编辑 API Key 弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑 API Key' : '添加 API Key'"
      width="500px"
    >
      <el-form :model="keyForm" label-width="100px">
        <el-form-item label="Provider">
          <el-select v-model="keyForm.provider" placeholder="选择提供商" :disabled="isEdit">
            <el-option label="T8Star（视频生成）" value="t8star" />
            <el-option label="ModelScope（看图文案）" value="modelscope" />
          </el-select>
        </el-form-item>
        <el-form-item label="Key 名称">
          <el-input v-model="keyForm.key_name" placeholder="如：t8star_key_1, modelscope_key_2" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input
            v-model="keyForm.key_value"
            type="password"
            show-password
            placeholder="输入完整的 API Key"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="keyForm.description" placeholder="可选备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSaveKey" :loading="savingKey">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

const formRef = ref(null)
const loading = ref(false)
const savingKey = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)

const form = reactive({
  signup_bonus: 10,
  image_base_price: 2,
  pricing_description: '',
  vercel_url: ''
})

const apiKeys = ref([])
const keyForm = reactive({
  id: null,
  provider: 't8star',
  key_name: '',
  key_value: '',
  description: ''
})

const t8starKeys = computed(() => apiKeys.value.filter(k => k.provider === 't8star'))
const modelscopeKeys = computed(() => apiKeys.value.filter(k => k.provider === 'modelscope'))

// 加载配置
const loadConfig = async () => {
  try {
    const res = await request.get('/admin/config')
    form.signup_bonus = parseInt(res.signup_bonus?.value || '10')
    form.image_base_price = parseInt(res.image_base_price?.value || '2')
    form.pricing_description = res.pricing_description?.value || ''
    form.vercel_url = res.vercel_url?.value || ''
  } catch (error) {
    console.error(error)
  }
}

// 加载 API Keys
const loadAPIKeys = async () => {
  try {
    const res = await request.get('/admin/api-keys')
    apiKeys.value = res
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
        vercel_url: form.vercel_url
      }
    })
    ElMessage.success('保存成功')
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 显示添加弹窗
const showAddDialog = () => {
  isEdit.value = false
  keyForm.id = null
  keyForm.provider = 't8star'
  keyForm.key_name = ''
  keyForm.key_value = ''
  keyForm.description = ''
  dialogVisible.value = true
}

// 显示编辑弹窗
const showEditDialog = (row) => {
  isEdit.value = true
  keyForm.id = row.id
  keyForm.provider = row.provider
  keyForm.key_name = row.key_name
  keyForm.key_value = '' // 编辑时不显示原值，需要重新输入
  keyForm.description = row.description || ''
  dialogVisible.value = true
}

// 保存 API Key
const handleSaveKey = async () => {
  if (!keyForm.key_name) {
    return ElMessage.warning('请输入 Key 名称')
  }
  if (!isEdit.value && !keyForm.key_value) {
    return ElMessage.warning('请输入 API Key')
  }

  savingKey.value = true
  try {
    if (isEdit.value) {
      const updateData = { description: keyForm.description }
      if (keyForm.key_value) {
        updateData.key_value = keyForm.key_value
      }
      await request.put(`/admin/api-keys/${keyForm.id}`, updateData)
      ElMessage.success('更新成功')
    } else {
      await request.post('/admin/api-keys', {
        provider: keyForm.provider,
        key_name: keyForm.key_name,
        key_value: keyForm.key_value,
        description: keyForm.description
      })
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    loadAPIKeys()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    savingKey.value = false
  }
}

// 切换 Key 状态
const toggleKeyStatus = async (row) => {
  try {
    await request.put(`/admin/api-keys/${row.id}`, {
      is_enabled: !row.is_enabled
    })
    ElMessage.success(row.is_enabled ? '已禁用' : '已启用')
    loadAPIKeys()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

// 删除 Key
const handleDeleteKey = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除 "${row.key_name}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await request.delete(`/admin/api-keys/${row.id}`)
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
.key-section {
  background: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
}

.key-section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.key-section-title {
  font-weight: 600;
  font-size: 14px;
  color: #303133;
}
</style>