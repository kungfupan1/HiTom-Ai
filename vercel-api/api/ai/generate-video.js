/**
 * 视频生成 API
 * POST /api/ai/generate-video
 */

const fetch = require('node-fetch')
const { mapRequestParams, getApiKey } = require('../lib/provider-mapper')

module.exports = async (req, res) => {
  // 处理 CORS
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')

  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ status: 'error', message: 'Method not allowed' })
  }

  try {
    const body = typeof req.body === 'string' ? JSON.parse(req.body) : req.body
    const { model, prompt, duration, ratio, resolution, images, deduction_id } = body

    // 验证必填参数
    if (!model || !prompt) {
      return res.status(400).json({
        status: 'error',
        message: '缺少必要参数：model 或 prompt'
      })
    }

    // 获取 API Key
    const apiKey = getApiKey('t8star')
    if (!apiKey) {
      return res.status(500).json({
        status: 'error',
        message: 'API Key 未配置'
      })
    }

    // 构建请求参数
    const params = { prompt, duration, ratio, resolution, images }
    const apiParams = mapRequestParams(model, params)

    // API 端点
    const endpoint = 'https://ai.t8star.cn/v2/videos/generations'

    console.log(`[generate-video] Model: ${model}, Duration: ${duration}`)

    // 发送请求
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(apiParams)
    })

    const result = await response.json()

    if (!response.ok) {
      console.error('[generate-video] API Error:', result)
      return res.status(response.status).json({
        status: 'error',
        message: result.error?.message || result.message || 'API 请求失败',
        detail: result
      })
    }

    // 返回结果
    console.log(`[generate-video] Success, task_id: ${result.task_id}`)
    return res.status(200).json({
      status: 'success',
      task_id: result.task_id,
      deduction_id
    })

  } catch (error) {
    console.error('[generate-video] Error:', error)
    return res.status(500).json({
      status: 'error',
      message: error.message || '服务器错误'
    })
  }
}