<template>
  <div class="model-manage">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>模型列表</span>
          <el-button type="primary" @click="handleAdd">
            <el-icon><Plus /></el-icon>
            添加模型
          </el-button>
        </div>
      </template>

      <el-table :data="models" v-loading="loading" stripe>
        <el-table-column prop="model_id" label="模型ID" width="150" />
        <el-table-column prop="display_name" label="显示名称" width="180" />
        <el-table-column prop="model_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="row.model_type === 'video' ? 'danger' : 'primary'">
              {{ row.model_type === 'video' ? '视频' : '图片' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="billing_mode" label="计费模式" width="120">
          <template #default="{ row }">
            {{ row.billing_mode === 'duration' ? '按时长' : '按次' }}
          </template>
        </el-table-column>
        <el-table-column prop="is_enabled" label="状态" width="100">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_enabled"
              @change="handleToggle(row)"
            />
          </template>
        </el-table-column>
        <el-table-column prop="base_url" label="API地址" show-overflow-tooltip />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleEdit(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button type="primary" link @click="handlePricing(row)">
              <el-icon><PriceTag /></el-icon>
              计费
            </el-button>
            <el-popconfirm
              title="确定删除该模型？"
              @confirm="handleDelete(row)"
            >
              <template #reference>
                <el-button type="danger" link>
                  <el-icon><Delete /></el-icon>
                  删除
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 计费配置弹窗 -->
    <el-dialog
      v-model="pricingDialogVisible"
      title="计费配置"
      width="800px"
    >
      <div v-if="currentModel">
        <h4 style="margin-bottom: 16px;">{{ currentModel.display_name }} - 计费规则</h4>

        <el-tabs>
          <el-tab-pane label="时长/次数定价" v-if="currentModel.billing_mode === 'duration'">
            <el-table :data="durationPricing" size="small">
              <el-table-column prop="pricing_key" label="时长(秒)" width="150">
                <template #default="{ row }">
                  {{ row.pricing_key }}秒
                </template>
              </el-table-column>
              <el-table-column prop="price" label="积分" width="150">
                <template #default="{ row }">
                  <el-input-number v-model="row.price" :min="0" size="small" />
                </template>
              </el-table-column>
              <el-table-column prop="is_available" label="可用">
                <template #default="{ row }">
                  <el-switch v-model="row.is_available" size="small" />
                </template>
              </el-table-column>
            </el-table>
            <el-button type="primary" link @click="addDurationPricing" style="margin-top: 12px;">
              + 添加时长
            </el-button>
          </el-tab-pane>

          <el-tab-pane label="分辨率加价">
            <el-table :data="resolutionPricing" size="small">
              <el-table-column prop="pricing_key" label="分辨率" width="150" />
              <el-table-column prop="price" label="额外积分" width="150">
                <template #default="{ row }">
                  <el-input-number v-model="row.price" :min="0" size="small" />
                </template>
              </el-table-column>
              <el-table-column prop="is_available" label="可用">
                <template #default="{ row }">
                  <el-switch v-model="row.is_available" size="small" />
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="比例加价">
            <el-table :data="ratioPricing" size="small">
              <el-table-column prop="pricing_key" label="比例" width="150" />
              <el-table-column prop="price" label="额外积分" width="150">
                <template #default="{ row }">
                  <el-input-number v-model="row.price" :min="0" size="small" />
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>

          <el-tab-pane label="费用说明">
            <el-input
              v-model="currentModel.pricing_description"
              type="textarea"
              :rows="5"
              placeholder="输入展示给用户的费用说明"
            />
          </el-tab-pane>
        </el-tabs>
      </div>

      <template #footer>
        <el-button @click="pricingDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="savePricing" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import request from '@/api/request'

const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const models = ref([])
const pricingDialogVisible = ref(false)
const currentModel = ref(null)

// 计费规则
const durationPricing = ref([])
const resolutionPricing = ref([])
const ratioPricing = ref([])

// 加载模型列表
const loadModels = async () => {
  loading.value = true
  try {
    const res = await request.get('/admin/models')
    models.value = res
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

// 启用/禁用
const handleToggle = async (row) => {
  try {
    await request.post(`/admin/models/${row.id}/toggle`)
    ElMessage.success(row.is_enabled ? '已启用' : '已禁用')
  } catch (error) {
    row.is_enabled = !row.is_enabled
  }
}

// 添加模型
const handleAdd = () => {
  router.push('/models/edit')
}

// 编辑模型
const handleEdit = (row) => {
  router.push(`/models/edit/${row.id}`)
}

// 删除模型
const handleDelete = async (row) => {
  try {
    await request.delete(`/admin/models/${row.id}`)
    ElMessage.success('删除成功')
    loadModels()
  } catch (error) {
    console.error(error)
  }
}

// 打开计费配置
const handlePricing = (row) => {
  currentModel.value = { ...row }

  // 分类计费规则
  durationPricing.value = (row.pricing_rules || [])
    .filter(r => r.pricing_type === 'duration')
    .sort((a, b) => a.sort_order - b.sort_order)

  resolutionPricing.value = (row.pricing_rules || [])
    .filter(r => r.pricing_type === 'resolution')
    .sort((a, b) => a.sort_order - b.sort_order)

  ratioPricing.value = (row.pricing_rules || [])
    .filter(r => r.pricing_type === 'ratio')
    .sort((a, b) => a.sort_order - b.sort_order)

  pricingDialogVisible.value = true
}

// 添加时长定价
const addDurationPricing = () => {
  durationPricing.value.push({
    pricing_type: 'duration',
    pricing_key: '10',
    price: 2,
    is_available: true,
    sort_order: durationPricing.value.length + 1
  })
}

// 保存计费配置
const savePricing = async () => {
  saving.value = true
  try {
    // 合并所有计费规则
    const allRules = [
      ...durationPricing.value,
      ...resolutionPricing.value,
      ...ratioPricing.value
    ]

    await request.put(`/admin/models/${currentModel.value.id}`, {
      pricing_description: currentModel.value.pricing_description,
      pricing_rules: allRules
    })

    ElMessage.success('保存成功')
    pricingDialogVisible.value = false
    loadModels()
  } catch (error) {
    console.error(error)
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadModels()
})
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    align-items: flex-start;
  }

  :deep(.el-table) {
    font-size: 13px;
  }

  :deep(.el-table .el-button) {
    padding: 4px 8px;
  }
}
</style>