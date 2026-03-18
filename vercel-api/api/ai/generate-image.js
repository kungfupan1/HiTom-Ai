/**
 * 图片生成 API
 * POST /api/ai/generate-image
 */

const fetch = require('node-fetch')
const { getApiKeyAsync } = require('../lib/provider-mapper')

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
    const { model, prompt, size, images, deduction_id } = body

    // 验证必填参数
    if (!model || !prompt) {
      return res.status(400).json({
        status: 'error',
        message: '缺少必要参数：model 或 prompt'
      })
    }

    // 获取 API Key - 支持从后端数据库获取（负载均衡）
    let apiKey
    try {
      apiKey = await getApiKeyAsync('t8star')
    } catch (e) {
      return res.status(500).json({
        status: 'error',
        message: e.message || 'API Key 获取失败'
      })
    }

    // 构建请求参数
    const apiParams = {
      model: model,
      prompt: prompt,
      response_format: 'url'
    }

    if (size) apiParams.size = size
    if (images && images.length > 0) apiParams.image = images

    // API 端点
    const endpoint = 'https://ai.t8star.cn/v1/images/generations'

    console.log(`[generate-image] Model: ${model}`)

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
      console.error('[generate-image] API Error:', result)
      return res.status(response.status).json({
        status: 'error',
        message: result.error?.message || result.message || 'API 请求失败',
        detail: result
      })
    }

    // 返回结果
    const images = result.data?.map(item => item.url) || []

    console.log(`[generate-image] Success, ${images.length} images`)

    return res.status(200).json({
      status: 'success',
      images: images,
      deduction_id
    })

  } catch (error) {
    console.error('[generate-image] Error:', error)
    return res.status(500).json({
      status: 'error',
      message: error.message || '服务器错误'
    })
  }
}