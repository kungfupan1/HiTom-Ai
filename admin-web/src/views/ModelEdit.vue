<template>
  <div class="model-edit">
    <el-card>
      <template #header>
        <div class="card-header">
          <el-button @click="$router.back()">
            <el-icon><ArrowLeft /></el-icon>
            返回
          </el-button>
          <span>{{ isEdit ? '编辑模型' : '添加模型' }}</span>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        style="max-width: 800px;"
      >
        <el-divider content-position="left">基本信息</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="模型ID" prop="model_id">
              <el-input
                v-model="form.model_id"
                placeholder="如: sora-2, grok-video-3"
                :disabled="isEdit"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="显示名称" prop="display_name">
              <el-input v-model="form.display_name" placeholder="如: Sora-2 标准版" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="模型类型" prop="model_type">
              <el-select v-model="form.model_type" style="width: 100%;">
                <el-option value="video" label="视频" />
                <el-option value="image" label="图片" />
                <el-option value="text" label="文本" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="排序">
              <el-input-number v-model="form.sort_order" :min="0" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">API 配置</el-divider>

        <el-row :gutter="20">
          <el-col :span="16">
            <el-form-item label="Base URL" prop="base_url">
              <el-input v-model="form.base_url" placeholder="https://ai.t8star.cn" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="API 提供商">
              <el-input v-model="form.api_provider" placeholder="t8star" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="Endpoint" prop="endpoint">
          <el-input v-model="form.endpoint" placeholder="/v2/videos/generations" />
        </el-form-item>

        <el-divider content-position="left">计费配置</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="计费模式">
              <el-radio-group v-model="form.billing_mode">
                <el-radio value="per_use">按次计费</el-radio>
                <el-radio value="duration">按时长计费</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="基础价格" v-if="form.billing_mode === 'per_use'">
              <el-input-number v-model="form.base_price" :min="0" />
              <span style="margin-left: 8px; color: #888;">积分/次</span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">参数映射</el-divider>

        <el-alert
          type="info"
          :closable="false"
          style="margin-bottom: 16px;"
        >
          <template #title>
            参数映射说明：将前端参数映射到 API 参数。格式：前端参数名 → API参数名
          </template>
        </el-alert>

        <el-form-item label="请求参数映射">
          <el-input
            v-model="requestMappingStr"
            type="textarea"
            :rows="8"
            placeholder='{
  "model": "{model}",
  "prompt": "{prompt}",
  "aspect_ratio": "{ratio}",
  "duration": "{duration}"
}'
          />
        </el-form-item>

        <el-form-item label="响应解析映射">
          <el-input
            v-model="responseMappingStr"
            type="textarea"
            :rows="4"
            placeholder='{
  "task_id": "$.task_id",
  "status": "$.status",
  "video_url": "$.data.output"
}'
          />
        </el-form-item>

        <el-form-item label="状态枚举映射">
          <el-input
            v-model="statusMappingStr"
            type="textarea"
            :rows="4"
            placeholder='{
  "success": "SUCCESS",
  "failure": "FAILURE",
  "processing": "PROCESSING"
}'
          />
        </el-form-item>

        <el-divider content-position="left">前端配置</el-divider>

        <el-form-item label="前端配置JSON">
          <el-input
            v-model="frontendConfigStr"
            type="textarea"
            :rows="6"
            placeholder='{
  "durations": [5, 10, 15, 25],
  "ratios": ["9:16", "16:9", "1:1"],
  "resolutions": [{"value": "720P", "label": "标清"}, {"value": "1080P", "label": "高清"}]
}'
          />
        </el-form-item>

        <el-divider content-position="left">费用说明</el-divider>

        <el-form-item label="展示给用户">
          <el-input
            v-model="form.pricing_description"
            type="textarea"
            :rows="4"
            placeholder="Sora-2 视频生成：&#10;5-10秒：2积分 | 15秒：5积分 | 25秒：25积分&#10;高清(1080P)：额外+2积分"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="loading">
            {{ isEdit ? '保存修改' : '创建模型' }}
          </el-button>
          <el-button @click="$router.back()">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const route = useRoute()
const router = useRouter()

const formRef = ref(null)
const loading = ref(false)

const isEdit = computed(() => !!route.params.id)
const modelId = computed(() => route.params.id)

const form = reactive({
  model_id: '',
  display_name: '',
  model_type: 'video',
  is_enabled: true,
  sort_order: 0,
  base_url: 'https://ai.t8star.cn',
  endpoint: '/v2/videos/generations',
  api_provider: 't8star',
  billing_mode: 'duration',
  base_price: 0,
  request_mapping: {},
  response_mapping: {},
  status_mapping: {},
  frontend_config: {},
  pricing_description: ''
})

// JSON 字符串形式的映射
const requestMappingStr = ref('')
const responseMappingStr = ref('')
const statusMappingStr = ref('')
const frontendConfigStr = ref('')

const rules = {
  model_id: [{ required: true, message: '请输入模型ID', trigger: 'blur' }],
  display_name: [{ required: true, message: '请输入显示名称', trigger: 'blur' }],
  model_type: [{ required: true, message: '请选择模型类型', trigger: 'change' }],
  base_url: [{ required: true, message: '请输入 Base URL', trigger: 'blur' }],
  endpoint: [{ required: true, message: '请输入 Endpoint', trigger: 'blur' }]
}

// 加载模型数据
const loadModel = async () => {
  if (!isEdit.value) return

  try {
    // 需要通过数字ID获取，这里先获取列表再找
    const models = await request.get('/admin/models')
    const model = models.find(m => m.id == modelId.value)

    if (!model) {
      ElMessage.error('模型不存在')
      router.back()
      return
    }

    Object.assign(form, model)

    // JSON 格式化
    requestMappingStr.value = JSON.stringify(model.request_mapping || {}, null, 2)
    responseMappingStr.value = JSON.stringify(model.response_mapping || {}, null, 2)
    statusMappingStr.value = JSON.stringify(model.status_mapping || {}, null, 2)
    frontendConfigStr.value = JSON.stringify(model.frontend_config || {}, null, 2)
  } catch (error) {
    console.error(error)
  }
}

// 提交
const handleSubmit = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    // 解析 JSON
    try {
      form.request_mapping = JSON.parse(requestMappingStr.value || '{}')
      form.response_mapping = JSON.parse(responseMappingStr.value || '{}')
      form.status_mapping = JSON.parse(statusMappingStr.value || '{}')
      form.frontend_config = JSON.parse(frontendConfigStr.value || '{}')
    } catch (e) {
      ElMessage.error('JSON 格式错误，请检查参数映射配置')
      return
    }

    loading.value = true
    try {
      if (isEdit.value) {
        await request.put(`/admin/models/${modelId.value}`, form)
        ElMessage.success('修改成功')
      } else {
        await request.post('/admin/models', form)
        ElMessage.success('创建成功')
      }
      router.push('/models')
    } catch (error) {
      console.error(error)
    } finally {
      loading.value = false
    }
  })
}

onMounted(() => {
  loadModel()
})
</script>

<style scoped>
.card-header {
  display: flex;
  align-items: center;
  gap: 16px;
}
</style>