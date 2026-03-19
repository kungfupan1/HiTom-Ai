/**
 * 视频生成 API
 * 腾讯云函数版本
 */

const axios = require('axios')
const { getT8StarKey } = require('../lib/config')
const { success, error, handleOptions, parseBody } = require('../lib/response')

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

exports.main_handler = async (event, context) => {
  // 处理 OPTIONS 预检请求
  if (event.httpMethod === 'OPTIONS') {
    return handleOptions()
  }

  // 只接受 POST 请求
  if (event.httpMethod !== 'POST') {
    return error('Method not allowed', 405)
  }

  try {
    const body = parseBody(event)
    const { model, prompt, duration, ratio, resolution, images, deduction_id } = body

    // 验证必填参数
    if (!model || !prompt) {
      return error('缺少必要参数：model 或 prompt', 400)
    }

    // 获取 API Key
    const apiKey = getT8StarKey()

    // 获取模型配置
    const modelConfig = MODEL_CONFIGS[model] || MODEL_CONFIGS['sora-2']

    // 构建请求 payload
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

    // 处理分辨率
    if (resolution === '1080P') {
      payload.hd = true
    } else {
      payload.hd = false
    }

    // 处理参考图
    if (images && images.length > 0) {
      payload.images = [images[0]]
    }

    console.log(`[generate-video] Model: ${model}, Duration: ${payload.duration}, Ratio: ${aspectRatio}`)

    // 发送请求
    const response = await axios.post(
      'https://ai.t8star.cn/v2/videos/generations',
      payload,
      {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json'
        },
        timeout: 60000
      }
    )

    console.log(`[generate-video] Success, task_id: ${response.data.task_id}`)

    return success({
      task_id: response.data.task_id,
      deduction_id
    })

  } catch (err) {
    console.error('[generate-video] Error:', err.message)
    if (err.response) {
      console.error('[generate-video] API Error:', err.response.data)
      return error(
        err.response.data?.error?.message || err.response.data?.message || 'API 请求失败',
        err.response.status || 500,
        err.response.data
      )
    }
    return error(err.message || '服务器错误')
  }
}