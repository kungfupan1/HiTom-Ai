/**
 * 图片生成 API
 * 腾讯云函数版本
 */

const axios = require('axios')
const { getT8StarKey } = require('../lib/config')
const { success, error, handleOptions, parseBody } = require('../lib/response')

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
    const { model, prompt, size, images, deduction_id } = body

    // 验证必填参数
    if (!model || !prompt) {
      return error('缺少必要参数：model 或 prompt', 400)
    }

    // 获取 API Key
    const apiKey = getT8StarKey()

    // 构建请求参数
    const apiParams = {
      model: model,
      prompt: prompt,
      response_format: 'url'
    }

    if (size) apiParams.size = size
    if (images && images.length > 0) apiParams.image = images

    console.log(`[generate-image] Model: ${model}`)

    // 发送请求
    const response = await axios.post(
      'https://ai.t8star.cn/v1/images/generations',
      apiParams,
      {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json'
        },
        timeout: 60000
      }
    )

    // 返回结果
    const imageUrls = response.data.data?.map(item => item.url) || []

    console.log(`[generate-image] Success, ${imageUrls.length} images`)

    return success({
      images: imageUrls,
      deduction_id
    })

  } catch (err) {
    console.error('[generate-image] Error:', err.message)
    if (err.response) {
      console.error('[generate-image] API Error:', err.response.data)
      return error(
        err.response.data?.error?.message || err.response.data?.message || 'API 请求失败',
        err.response.status || 500,
        err.response.data
      )
    }
    return error(err.message || '服务器错误')
  }
}