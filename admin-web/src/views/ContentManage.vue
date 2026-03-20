<template>
  <div class="content-manage">
    <el-card>
      <template #header>
        <span>内容管理</span>
      </template>

      <el-collapse v-model="activeNames" accordion>
        <!-- 云端养虾 -->
        <el-collapse-item title="云端养虾" name="shrimp">
          <div class="category-desc">AI 智能体部署与 Skills 市场</div>

          <el-collapse v-model="activeItems" accordion>
            <el-collapse-item name="shrimp_openclaw">
              <template #title>
                <span class="item-title">OpenClaw 部署</span>
                <el-switch v-model="configs.shrimp_openclaw.config.enabled" size="small" @click.stop />
              </template>

              <el-form label-width="100px" class="config-form">
                <el-form-item label="是否展示">
                  <el-switch v-model="configs.shrimp_openclaw.config.enabled" />
                </el-form-item>
                <el-form-item label="弹窗内容">
                  <el-input
                    v-model="configs.shrimp_openclaw.config.modal_content"
                    type="textarea"
                    :rows="4"
                    placeholder="不填则显示默认内容：请私聊联系站长即可"
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveConfig('shrimp_openclaw')">保存</el-button>
                </el-form-item>
              </el-form>
            </el-collapse-item>

            <el-collapse-item name="shrimp_skills">
              <template #title>
                <span class="item-title">Skills 市场</span>
                <el-switch v-model="configs.shrimp_skills.config.enabled" size="small" @click.stop />
              </template>

              <el-form label-width="100px" class="config-form">
                <el-form-item label="是否展示">
                  <el-switch v-model="configs.shrimp_skills.config.enabled" />
                </el-form-item>
                <el-form-item label="弹窗内容">
                  <el-input
                    v-model="configs.shrimp_skills.config.modal_content"
                    type="textarea"
                    :rows="4"
                    placeholder="不填则显示默认内容"
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveConfig('shrimp_skills')">保存</el-button>
                </el-form-item>
              </el-form>
            </el-collapse-item>

            <el-collapse-item name="shrimp_ai_staff">
              <template #title>
                <span class="item-title">AI 员工打造</span>
                <el-switch v-model="configs.shrimp_ai_staff.config.enabled" size="small" @click.stop />
              </template>

              <el-form label-width="100px" class="config-form">
                <el-form-item label="是否展示">
                  <el-switch v-model="configs.shrimp_ai_staff.config.enabled" />
                </el-form-item>
                <el-form-item label="弹窗内容">
                  <el-input
                    v-model="configs.shrimp_ai_staff.config.modal_content"
                    type="textarea"
                    :rows="4"
                    placeholder="不填则显示默认内容"
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveConfig('shrimp_ai_staff')">保存</el-button>
                </el-form-item>
              </el-form>
            </el-collapse-item>
          </el-collapse>
        </el-collapse-item>

        <!-- 跨境服务资源 -->
        <el-collapse-item title="跨境服务资源" name="service">
          <div class="category-desc">跨境电商一站式服务资源</div>

          <el-collapse v-model="activeItems" accordion>
            <el-collapse-item name="service_shop">
              <template #title>
                <span class="item-title">店铺买卖/租赁</span>
                <el-switch v-model="configs.service_shop.config.enabled" size="small" @click.stop />
              </template>

              <el-form label-width="100px" class="config-form">
                <el-form-item label="是否展示">
                  <el-switch v-model="configs.service_shop.config.enabled" />
                </el-form-item>
                <el-form-item label="弹窗内容">
                  <el-input
                    v-model="configs.service_shop.config.modal_content"
                    type="textarea"
                    :rows="4"
                    placeholder="不填则显示默认内容"
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveConfig('service_shop')">保存</el-button>
                </el-form-item>
              </el-form>
            </el-collapse-item>

            <el-collapse-item name="service_course">
              <template #title>
                <span class="item-title">课程+陪跑</span>
                <el-switch v-model="configs.service_course.config.enabled" size="small" @click.stop />
              </template>

              <el-form label-width="100px" class="config-form">
                <el-form-item label="是否展示">
                  <el-switch v-model="configs.service_course.config.enabled" />
                </el-form-item>
                <el-form-item label="弹窗内容">
                  <el-input
                    v-model="configs.service_course.config.modal_content"
                    type="textarea"
                    :rows="4"
                    placeholder="不填则显示默认内容"
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveConfig('service_course')">保存</el-button>
                </el-form-item>
              </el-form>
            </el-collapse-item>

            <el-collapse-item name="service_logistics">
              <template #title>
                <span class="item-title">货代/小包/海外仓</span>
                <el-switch v-model="configs.service_logistics.config.enabled" size="small" @click.stop />
              </template>

              <el-form label-width="100px" class="config-form">
                <el-form-item label="是否展示">
                  <el-switch v-model="configs.service_logistics.config.enabled" />
                </el-form-item>
                <el-form-item label="弹窗内容">
                  <el-input
                    v-model="configs.service_logistics.config.modal_content"
                    type="textarea"
                    :rows="4"
                    placeholder="不填则显示默认内容"
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveConfig('service_logistics')">保存</el-button>
                </el-form-item>
              </el-form>
            </el-collapse-item>

            <el-collapse-item name="service_software">
              <template #title>
                <span class="item-title">增强软件</span>
                <el-switch v-model="configs.service_software.config.enabled" size="small" @click.stop />
              </template>

              <el-form label-width="100px" class="config-form">
                <el-form-item label="是否展示">
                  <el-switch v-model="configs.service_software.config.enabled" />
                </el-form-item>
                <el-form-item label="弹窗内容">
                  <el-input
                    v-model="configs.service_software.config.modal_content"
                    type="textarea"
                    :rows="4"
                    placeholder="不填则显示默认内容"
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveConfig('service_software')">保存</el-button>
                </el-form-item>
              </el-form>
            </el-collapse-item>

            <el-collapse-item name="service_network">
              <template #title>
                <span class="item-title">网络&硬件服务</span>
                <el-switch v-model="configs.service_network.config.enabled" size="small" @click.stop />
              </template>

              <el-form label-width="100px" class="config-form">
                <el-form-item label="是否展示">
                  <el-switch v-model="configs.service_network.config.enabled" />
                </el-form-item>
                <el-form-item label="弹窗内容">
                  <el-input
                    v-model="configs.service_network.config.modal_content"
                    type="textarea"
                    :rows="4"
                    placeholder="不填则显示默认内容"
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveConfig('service_network')">保存</el-button>
                </el-form-item>
              </el-form>
            </el-collapse-item>

            <el-collapse-item name="service_other">
              <template #title>
                <span class="item-title">其他合作</span>
                <el-switch v-model="configs.service_other.config.enabled" size="small" @click.stop />
              </template>

              <el-form label-width="100px" class="config-form">
                <el-form-item label="是否展示">
                  <el-switch v-model="configs.service_other.config.enabled" />
                </el-form-item>
                <el-form-item label="弹窗内容">
                  <el-input
                    v-model="configs.service_other.config.modal_content"
                    type="textarea"
                    :rows="4"
                    placeholder="不填则显示默认内容"
                  />
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" @click="saveConfig('service_other')">保存</el-button>
                </el-form-item>
              </el-form>
            </el-collapse-item>
          </el-collapse>
        </el-collapse-item>
      </el-collapse>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import request from '@/api/request'
import { ElMessage } from 'element-plus'

const activeNames = ref(['shrimp'])
const activeItems = ref([])

// 默认配置
const defaultConfig = {
  enabled: true,
  modal_content: ''
}

// 所有配置
const configKeys = [
  'shrimp_openclaw', 'shrimp_skills', 'shrimp_ai_staff',
  'service_shop', 'service_course', 'service_logistics',
  'service_software', 'service_network', 'service_other'
]

const configs = reactive({})

// 初始化配置
configKeys.forEach(key => {
  configs[key] = { config: { ...defaultConfig } }
})

const loadConfigs = async () => {
  try {
    const res = await request.get('/admin/content-configs')
    Object.keys(res).forEach(key => {
      if (configs[key]) {
        configs[key].config = { ...defaultConfig, ...res[key].config }
      }
    })
  } catch (e) {
    ElMessage.error('加载配置失败')
  }
}

const saveConfig = async (key) => {
  try {
    await request.put(`/admin/content-configs/${key}`, {
      config: configs[key].config
    })
    ElMessage.success('保存成功')
  } catch (e) {
    ElMessage.error('保存失败')
  }
}

onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.content-manage {
  padding: 0;
}

.category-desc {
  color: #999;
  font-size: 13px;
  margin-bottom: 15px;
  padding-left: 10px;
}

.item-title {
  font-weight: 500;
}

.config-form {
  margin-top: 15px;
  padding: 15px;
  background: #f9f9f9;
  border-radius: 8px;
}

:deep(.el-collapse-item__header) {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

:deep(.el-collapse-item__content) {
  padding: 10px 0;
}
</style>