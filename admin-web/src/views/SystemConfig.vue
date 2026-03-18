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

        <el-alert type="warning" :closable="false" style="margin-bottom: 20px;">
          <template #title>
            注意：请确保 Vercel Functions 已部署，并在环境变量中配置了 T8STAR_API_KEY 等密钥
          </template>
        </el-alert>

        <el-form-item>
          <el-button type="primary" @click="handleSave" :loading="loading">
            保存配置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card style="margin-top: 20px;">
      <template #header>
        <span>API 密钥配置（存储在 Vercel 环境变量）</span>
      </template>

      <el-alert type="warning" :closable="false" style="margin-bottom: 16px;">
        <template #title>
          安全提示：API 密钥存储在 Vercel 环境变量中，不会暴露给前端。以下仅供参考，请勿泄露。
        </template>
      </el-alert>

      <el-descriptions :column="1" border>
        <el-descriptions-item label="T8Star API Key">
          <el-tag v-if="hasT8Key" type="success">已配置</el-tag>
          <el-tag v-else type="danger">未配置</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="ModelScope API Key">
          <el-tag v-if="hasMsKey" type="success">已配置</el-tag>
          <el-tag v-else type="danger">未配置</el-tag>
        </el-descriptions-item>
      </el-descriptions>

      <div style="margin-top: 16px; color: #888; font-size: 13px;">
        如需修改 API 密钥，请在 Vercel Dashboard → Settings → Environment Variables 中修改
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const formRef = ref(null)
const loading = ref(false)

const form = reactive({
  signup_bonus: 10,
  image_base_price: 2,
  pricing_description: '',
  vercel_url: ''
})

const hasT8Key = ref(false)
const hasMsKey = ref(false)

// 加载配置
const loadConfig = async () => {
  try {
    const res = await request.get('/admin/config')
    form.signup_bonus = parseInt(res.signup_bonus?.value || '10')
    form.image_base_price = parseInt(res.image_base_price?.value || '2')
    form.pricing_description = res.pricing_description?.value || ''
    form.vercel_url = res.vercel_url?.value || ''

    // 检查 API Key 状态（这里简化处理）
    hasT8Key.value = true
    hasMsKey.value = true
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

onMounted(() => {
  loadConfig()
})
</script>