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
        <div v-if="loading && historyList.length === 0" class="loading-state">
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
            <!-- 删除按钮 - 右上角圆形叉 -->
            <div class="delete-btn" @click.stop="confirmDelete(item)">
              <el-icon><Close /></el-icon>
            </div>

            <!-- 左侧预览区域 -->
            <div
              class="preview-area"
              :class="{
                'preview-success': item.previewStatus === 'success',
                'preview-failed': item.previewStatus === 'failed'
              }"
              @click="handlePreviewClick(item)"
            >
              <!-- 初始状态：点击下载 -->
              <template v-if="!item.previewStatus || item.previewStatus === 'initial'">
                <el-icon class="preview-icon"><Download /></el-icon>
                <span class="preview-text">点击下载</span>
              </template>

              <!-- 加载中 -->
              <template v-else-if="item.previewStatus === 'loading'">
                <el-icon class="is-loading preview-icon"><Loading /></el-icon>
                <span class="preview-text">加载中</span>
              </template>

              <!-- 加载失败/已清理 -->
              <template v-else-if="item.previewStatus === 'failed'">
                <el-icon class="preview-icon failed-icon"><WarningFilled /></el-icon>
                <span class="preview-text failed-text">已清理</span>
                <span class="retry-hint">点击重试</span>
              </template>

              <!-- 加载成功 -->
              <template v-else-if="item.previewStatus === 'success'">
                <!-- 图片缩略图 -->
                <img
                  v-if="item.task_type === 'image'"
                  :src="item.previewUrl"
                  class="preview-image"
                  @click.stop="openImagePreview(item.previewUrl)"
                />
                <!-- 视频缩略图 -->
                <video
                  v-else-if="item.task_type === 'video'"
                  :src="item.previewUrl"
                  class="preview-video"
                  preload="metadata"
                  @click.stop="openVideoFullscreen"
                  muted
                />
              </template>
            </div>

            <!-- 右侧信息区域 -->
            <div class="info-area">
              <div class="info-header">
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

              <div class="info-body">
                <div class="info-row">
                  <span class="label">模型:</span>
                  <span class="value">{{ item.model_id || '未知' }}</span>
                  <span class="label" style="margin-left: 12px;">消耗:</span>
                  <span class="value highlight">{{ item.cost_points }} 积分</span>
                </div>
                <div v-if="item.prompt_summary" class="info-row">
                  <span class="label">提示词:</span>
                  <span class="value prompt-text">{{ item.prompt_summary }}</span>
                </div>
                <div v-if="item.params_json" class="info-row">
                  <span class="label">参数:</span>
                  <span class="value params-text">{{ formatParams(item.params_json) }}</span>
                </div>
              </div>

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

    <!-- 全窗口图片预览 (Teleport 到 body) -->
    <Teleport to="body">
      <transition name="fade">
        <div v-if="imagePreviewVisible" class="fullscreen-preview" @click="closeImagePreview">
          <div class="preview-close-btn" @click="closeImagePreview">
            <el-icon><Close /></el-icon>
          </div>
          <img :src="imagePreviewUrl" class="fullscreen-image" @click.stop />
        </div>
      </transition>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { ArrowDown, Loading, Download, WarningFilled, Close } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '@/api/request'
import { getCachedMedia, fetchAndCacheMedia, deleteCachedMedia } from '@/utils/mediaCache'

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

// 全窗口图片预览状态
const imagePreviewVisible = ref(false)
const imagePreviewUrl = ref('')

// 根据传入的 fixedType 确定查询类型
const queryType = props.fixedType || ''

// 切换展开
const toggleExpand = () => {
  expanded.value = !expanded.value
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
    // 初始化每条记录的预览状态，并检查缓存
    historyList.value = await Promise.all((res.items || []).map(async item => {
      // 检查缓存
      const cached = await getCachedMedia(item.result_url)
      return {
        ...item,
        previewStatus: cached ? 'success' : 'initial',  // 如果有缓存直接显示成功
        previewUrl: cached ? cached.blobUrl : null
      }
    }))
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

// 处理预览点击
const handlePreviewClick = async (item) => {
  // 如果已经成功，不重复下载
  if (item.previewStatus === 'success') {
    return
  }

  // 开始下载
  item.previewStatus = 'loading'

  try {
    // 使用缓存工具下载并缓存
    const result = await fetchAndCacheMedia(item.result_url, item.task_type)

    // 成功
    item.previewUrl = result.blobUrl
    item.previewStatus = 'success'

    if (result.fromCache) {
      ElMessage.success('已从缓存加载')
    } else {
      ElMessage.success('加载成功')
    }
  } catch (e) {
    console.error('加载失败', e)
    item.previewStatus = 'failed'
    // 失败不弹提示，用户可以看到"已清理"状态
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

    // 删除缓存
    await deleteCachedMedia(item.result_url)

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

// 打开全窗口图片预览
const openImagePreview = (url) => {
  imagePreviewUrl.value = url
  imagePreviewVisible.value = true
  document.body.style.overflow = 'hidden'
}

// 关闭图片预览
const closeImagePreview = () => {
  imagePreviewVisible.value = false
  document.body.style.overflow = ''
}

// 视频全屏播放
const openVideoFullscreen = (e) => {
  const video = e.target
  if (video.requestFullscreen) {
    video.requestFullscreen()
  } else if (video.webkitRequestFullscreen) {
    video.webkitRequestFullscreen()
  } else if (video.msRequestFullscreen) {
    video.msRequestFullscreen()
  }
  video.play()
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

.history-content {
  margin-top: 12px;
  overflow: hidden;
}

/* 展开/折叠动画 */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.4s ease;
  max-height: 2000px;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 30px 16px;
  color: #718096;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.loading-state .el-icon {
  font-size: 24px;
}

.empty-state .el-icon {
  font-size: 24px;
}

.cards-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 0 4px;
}

/* 卡片样式：左侧预览 + 右侧信息 */
.history-card {
  display: flex;
  gap: 16px;
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 12px;
  animation: cardSlideIn 0.4s ease forwards;
  animation-delay: var(--delay, 0s);
  opacity: 0;
  transform: translateY(-20px);
  position: relative;
}

/* 右上角删除按钮 */
.delete-btn {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: rgba(255, 80, 80, 0.2);
  border: 1px solid rgba(255, 80, 80, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  z-index: 10;
}

.delete-btn:hover {
  background: rgba(255, 80, 80, 0.5);
  border-color: rgba(255, 80, 80, 0.8);
  transform: scale(1.1);
}

.delete-btn .el-icon {
  font-size: 14px;
  color: #ff6464;
}

@keyframes cardSlideIn {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 左侧预览区域 */
.preview-area {
  width: 150px;
  height: 150px;
  min-width: 150px;
  background: rgba(0, 0, 0, 0.5);
  border: 1px dashed rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  overflow: hidden;
}

.preview-area:hover {
  border-color: rgba(0, 242, 96, 0.5);
  background: rgba(0, 0, 0, 0.6);
}

.preview-icon {
  font-size: 28px;
  color: #a0aec0;
  margin-bottom: 4px;
}

.preview-text {
  font-size: 12px;
  color: #718096;
}

.preview-area.preview-success {
  border: 1px solid rgba(0, 242, 96, 0.3);
  cursor: default;
}

.preview-area.preview-success:hover {
  border-color: rgba(0, 242, 96, 0.5);
}

.preview-area.preview-failed {
  border-color: rgba(255, 100, 100, 0.3);
  background: rgba(255, 100, 100, 0.1);
}

.failed-icon {
  color: #ff6464;
}

.failed-text {
  color: #ff6464;
}

.retry-hint {
  font-size: 10px;
  color: #718096;
  margin-top: 4px;
}

.preview-image,
.preview-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 6px;
}

/* 右侧信息区域 */
.info-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  padding-right: 32px;
}

.info-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.card-time {
  font-size: 12px;
  color: #718096;
}

.info-body {
  flex: 1;
}

.info-row {
  display: flex;
  font-size: 13px;
  margin-bottom: 4px;
  align-items: flex-start;
}

.info-row .label {
  color: #718096;
  flex-shrink: 0;
}

.info-row .value {
  color: #e2e8f0;
  margin-left: 4px;
}

.info-row .value.highlight {
  color: #00f260;
  font-weight: bold;
}

.prompt-text {
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
}

.params-text {
  font-size: 12px;
  color: #a0aec0;
}

.pagination-wrapper {
  margin-top: 16px;
  padding: 12px 0 4px;
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

/* 图片预览遮罩层适配 */
:deep(.el-image-viewer__wrapper) {
  background: rgba(0, 0, 0, 0.95);
  z-index: 9999 !important;
}

:deep(.el-image-viewer__close) {
  color: #fff;
}
</style>

<style>
/* 全窗口图片预览样式 (Teleport 到 body，不用 scoped) */
.fullscreen-preview {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.95);
  z-index: 99999;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: zoom-out;
}

.fullscreen-image {
  max-width: 95vw;
  max-height: 95vh;
  object-fit: contain;
  border-radius: 8px;
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.5);
}

.preview-close-btn {
  position: absolute;
  top: 20px;
  right: 20px;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s;
  color: #fff;
  font-size: 24px;
}

.preview-close-btn:hover {
  background: rgba(255, 80, 80, 0.5);
  border-color: rgba(255, 80, 80, 0.8);
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>