/**
 * 视频生成 API
 * POST /api/ai/generate-video
 * 复刻自 MyWebTool ai_service.py 的 submit_video_task 逻辑
 */

const fetch = require('node-fetch')
const { getT8StarKey } = require('../../lib/api-key-fetcher')

// 不同模型的参数配置
const MODEL_CONFIGS = {
  'sora-2': {
    mapFields: { ratio: 'aspect_ratio' },
    defaults: { private: true },
    durationAsString: true
  },
  'sora-2-pro': {
    mapFields: { ratio: 'aspect_ratio' },
    defaults: { private: true },
    durationAsString: true
  },
  'grok-video-3': {
    mapFields: { ratio: 'ratio' },
    defaults: {},
    durationAsInt: true
  }
}

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

    // 获取 API Key - 支持从后端数据库获取（负载均衡）
    let apiKey
    try {
      apiKey = await getT8StarKey()
    } catch (e) {
      return res.status(500).json({
        status: 'error',
        message: e.message || 'API Key 获取失败'
      })
    }

    // 获取模型配置
    const modelConfig = MODEL_CONFIGS[model] || MODEL_CONFIGS['sora-2']

    // 构建请求 payload - 复刻 MyWebTool 的 submit_video_task 逻辑
    const payload = {
      model: model,
      prompt: prompt,
      private: true
    }

    // 处理 aspect_ratio/ratio
    const aspectRatio = ratio || '9:16'
    if (modelConfig.mapFields.ratio === 'aspect_ratio') {
      payload.aspect_ratio = aspectRatio
    } else {
      payload.ratio = aspectRatio
    }

    // 处理 duration
    const dur = duration || 10
    if (modelConfig.durationAsString) {
      payload.duration = String(dur)
    } else if (modelConfig.durationAsInt) {
      payload.duration = parseInt(dur)
    } else {
      payload.duration = dur
    }

    // 处理 hd/分辨率
    if (resolution === '1080P') {
      payload.hd = true
    } else {
      payload.hd = false
    }

    // 处理参考图 - Sora 支持首图参考
    if (images && images.length > 0) {
      payload.images = [images[0]]
    }

    // API 端点
    const endpoint = 'https://ai.t8star.cn/v2/videos/generations'

    console.log(`[generate-video] Model: ${model}, Duration: ${payload.duration}, Ratio: ${aspectRatio}`)
    console.log(`[generate-video] Payload:`, JSON.stringify(payload, null, 2))

    // 发送请求
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
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