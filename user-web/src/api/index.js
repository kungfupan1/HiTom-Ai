import request from './request'

// 获取视频模型列表
export const getVideoModels = () => {
  return request.get('/api/models', { params: { model_type: 'video' } })
}

// 获取图片模型列表
export const getImageModels = () => {
  return request.get('/api/models', { params: { model_type: 'image' } })
}

// 计算费用
export const calculateCost = (data) => {
  return request.post('/api/calculate-cost', data)
}

// 预扣积分
export const reservePoints = (data) => {
  return request.post('/api/points/reserve', data)
}

// 确认扣费
export const confirmPoints = (deductionId) => {
  return request.post('/api/points/confirm', { deduction_id: deductionId })
}

// 退还积分
export const refundPoints = (deductionId, reason) => {
  return request.post('/api/points/refund', { deduction_id: deductionId, reason })
}

// 获取费用说明
export const getPricingInfo = () => {
  return request.get('/api/config/pricing-info')
}

// Vercel Functions API（需要配置 Vercel URL）
const VERCEL_URL = '' // 在系统配置中设置

// 生成视频
export const generateVideo = async (data) => {
  const url = VERCEL_URL ? `${VERCEL_URL}/api/ai/generate-video` : '/api/ai/generate-video'
  return request.post(url, data)
}

// 查询视频状态
export const getVideoStatus = async (taskId, model) => {
  const url = VERCEL_URL ? `${VERCEL_URL}/api/ai/video-status` : '/api/ai/video-status'
  return request.get(url, { params: { task_id: taskId, model } })
}

// 生成图片
export const generateImage = async (data) => {
  const url = VERCEL_URL ? `${VERCEL_URL}/api/ai/generate-image` : '/api/ai/generate-image'
  return request.post(url, data)
}