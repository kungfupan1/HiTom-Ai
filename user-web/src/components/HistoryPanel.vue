<template>
  <div class="history-panel">
    <!-- 折叠头部 -->
    <div class="history-header cyber-glass" @click="toggleExpand">
      <div class="header-left">
        <span class="gradient-text">📚 生成历史</span>
        <el-tag size="small" type="info" effect="dark" round>{{ total }} 条记录</el-tag>
      </div>
      <div class="header-right">
        <el-icon class="expand-icon" :class="{ rotated: expanded }">
          <ArrowDown />
        </el-icon>
      </div>
    </div>

    <!-- 展开内容 -->
    <transition name="expand">
      <div v-show="expanded" class="history-content">
        <div v-if="loading" class="loading-state">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>加载中...</span>
        </div>

        <div v-else-if="historyList.length === 0" class="empty-state">
          <span>暂无历史记录</span>
        </div>

        <div v-else class="cards-container">
          <div
            v-for="(item, index) in historyList"
            :key="item.id"
            class="history-card"
            :style="{ '--delay': index * 0.05 + 's' }"
          >
            <div class="card-header">
              <el-tag
                :type="getTagType(item.task_type)"
                size="small"
                effect="dark"
                round
              >
                {{ getTagLabel(item.task_type) }}
              </el-tag>
              <span class="card-time">{{ formatTime(item.create_time) }}</span>
            </div>

            <div class="card-body">
              <div class="card-info">
                <div class="info-row">
                  <span class="label">模型:</span>
                  <span class="value">{{ item.model_id || '未知' }}</span>
                </div>
                <div class="info-row">
                  <span class="label">消耗:</span>
                  <span class="value highlight">{{ item.cost_points }} 积分</span>
                </div>
                <div v-if="item.prompt_summary" class="info-row prompt-row">
                  <span class="label">提示词:</span>
                  <span class="value prompt-text">{{ item.prompt_summary }}</span>
                </div>
                <div v-if="item.params_json" class="info-row params-row">
                  <span class="label">参数:</span>
                  <span class="value params-text">{{ formatParams(item.params_json) }}</span>
                </div>
              </div>
            </div>

            <div class="card-footer">
              <el-button
                type="primary"
                size="small"
                class="download-btn"
                @click="downloadResult(item)"
              >
                <el-icon><Download /></el-icon>
                下载{{ getDownloadLabel(item.task_type) }}
              </el-button>
              <el-button
                type="danger"
                size="small"
                text
                @click="confirmDelete(item)"
              >
                删除
              </el-button>
            </div>
          </div>
        </div>

        <!-- 分页 -->
        <div v-if="totalPages > 1" class="pagination-wrapper">
          <el-pagination
            v-model:current-page="currentPage"
            :page-size="pageSize"
            :total="total"
            layout="prev, pager, next, jumper"
            small
            background
            @current-change="loadHistory"
          />
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { ArrowDown, Loading, Download } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'

const props = defineProps({
  // 固定类型：传入后隐藏筛选器，只显示该类型记录
  fixedType: {
    type: String,
    default: '' // video, image, text
  }
})

// 状态
const expanded = ref(false)
const loading = ref(false)
const historyList = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const totalPages = ref(0)

// 根据传入的 fixedType 确定查询类型
const queryType = props.fixedType || ''

// 切换展开
const toggleExpand = () => {
  expanded.value = !expanded.value
  if (expanded.value && historyList.value.length === 0) {
    loadHistory()
  }
}

// 加载历史记录
const loadHistory = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    // 如果有固定类型，使用固定类型
    if (queryType) {
      params.task_type = queryType
    }

    const res = await request.get('/api/history', { params })
    historyList.value = res.items || []
    total.value = res.total || 0
    totalPages.value = res.total_pages || 0
  } catch (e) {
    console.error('加载历史记录失败', e)
    ElMessage.error('加载历史记录失败')
  } finally {
    loading.value = false
  }
}

// 获取标签类型
const getTagType = (taskType) => {
  const typeMap = {
    video: 'danger',
    image: 'success',
    text: 'warning'
  }
  return typeMap[taskType] || 'info'
}

// 获取标签文字
const getTagLabel = (taskType) => {
  const labelMap = {
    video: '视频',
    image: '图片',
    text: '文案'
  }
  return labelMap[taskType] || taskType
}

// 获取下载按钮文字
const getDownloadLabel = (taskType) => {
  const labelMap = {
    video: '视频',
    image: '图片',
    text: '文件'
  }
  return labelMap[taskType] || '文件'
}

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now - date

  // 今天
  if (diff < 86400000 && date.getDate() === now.getDate()) {
    return `今天 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  }
  // 昨天
  const yesterday = new Date(now)
  yesterday.setDate(yesterday.getDate() - 1)
  if (date.getDate() === yesterday.getDate()) {
    return `昨天 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  }
  // 其他
  return `${date.getMonth() + 1}/${date.getDate()} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

// 格式化参数
const formatParams = (params) => {
  if (!params) return ''
  const parts = []
  if (params.duration) parts.push(`${params.duration}秒`)
  if (params.resolution) parts.push(params.resolution)
  if (params.aspect_ratio || params.ratio) parts.push(params.aspect_ratio || params.ratio)
  return parts.join(' | ') || JSON.stringify(params)
}

// 下载结果
const downloadResult = async (item) => {
  if (!item.result_url) {
    ElMessage.warning('该记录没有可下载的结果')
    return
  }

  try {
    ElMessage.info('开始下载...')

    // 获取文件
    const response = await fetch(item.result_url)
    const blob = await response.blob()

    // 创建下载链接
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url

    // 根据类型设置文件名
    const ext = item.task_type === 'video' ? 'mp4' : item.task_type === 'image' ? 'png' : 'txt'
    a.download = `${item.task_type}_${item.id}_${Date.now()}.${ext}`

    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)

    ElMessage.success('下载完成')
  } catch (e) {
    console.error('下载失败', e)
    // 降级方案：直接打开链接
    window.open(item.result_url, '_blank')
    ElMessage.warning('请在新窗口中保存文件')
  }
}

// 确认删除
const confirmDelete = async (item) => {
  try {
    await ElMessageBox.confirm('确定要删除这条历史记录吗？删除后无法恢复。', '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await request.delete(`/api/history/${item.id}`)
    ElMessage.success('删除成功')

    // 从列表中移除
    historyList.value = historyList.value.filter(h => h.id !== item.id)
    total.value -= 1

    // 如果当前页空了，加载上一页
    if (historyList.value.length === 0 && currentPage.value > 1) {
      currentPage.value -= 1
      loadHistory()
    }
  } catch (e) {
    if (e !== 'cancel') {
      console.error('删除失败', e)
      ElMessage.error('删除失败')
    }
  }
}

// 暴露方法给父组件
defineExpose({
  refresh: loadHistory,
  expand: () => { expanded.value = true; loadHistory() }
})

onMounted(() => {
  // 挂载时加载一次，获取正确的记录总数
  loadHistory()
})
</script>

<style scoped>
.history-panel {
  margin-top: 16px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  cursor: pointer;
  border-radius: 12px;
  transition: all 0.3s;
  user-select: none;
}

.history-header:hover {
  background: rgba(0, 0, 0, 0.5);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.expand-icon {
  transition: transform 0.3s ease;
  font-size: 18px;
  color: #a0aec0;
}

.expand-icon.rotated {
  transform: rotate(180deg);
}

.filter-select {
  width: 120px;
}

.history-content {
  margin-top: 12px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  padding: 16px;
  overflow: hidden;
}

/* 展开/折叠动画 */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.4s ease;
  max-height: 1000px;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 40px;
  color: #718096;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.loading-state .el-icon {
  font-size: 24px;
}

.cards-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-card {
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px 16px;
  animation: cardSlideIn 0.4s ease forwards;
  animation-delay: var(--delay, 0s);
  opacity: 0;
  transform: translateY(-20px);
}

@keyframes cardSlideIn {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.card-time {
  font-size: 12px;
  color: #718096;
}

.card-body {
  margin-bottom: 12px;
}

.info-row {
  display: flex;
  font-size: 13px;
  margin-bottom: 6px;
}

.info-row .label {
  color: #718096;
  width: 60px;
  flex-shrink: 0;
}

.info-row .value {
  color: #e2e8f0;
  flex: 1;
}

.info-row .value.highlight {
  color: #00f260;
  font-weight: bold;
}

.prompt-row .prompt-text {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.params-row .params-text {
  font-size: 12px;
  color: #a0aec0;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.download-btn {
  background: rgba(0, 242, 96, 0.2) !important;
  border: 1px solid rgba(0, 242, 96, 0.3) !important;
  color: #00f260 !important;
}

.download-btn:hover {
  background: rgba(0, 242, 96, 0.3) !important;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

/* Element Plus 暗色主题适配 */
:deep(.el-pagination.is-background .el-pager li) {
  background: rgba(0, 0, 0, 0.4);
  color: #a0aec0;
}

:deep(.el-pagination.is-background .el-pager li.is-active) {
  background: linear-gradient(90deg, #00f260, #0575e6);
  color: #fff;
}

:deep(.el-pagination.is-background .btn-prev),
:deep(.el-pagination.is-background .btn-next) {
  background: rgba(0, 0, 0, 0.4);
  color: #a0aec0;
}

:deep(.el-select .el-input__wrapper) {
  background: rgba(0, 0, 0, 0.3) !important;
}
</style>