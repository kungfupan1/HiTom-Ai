/**
 * 视频状态查询 API
 * 腾讯云函数版本
 */

const axios = require('axios')
const { getT8StarKey } = require('../lib/config')
const { success, error, handleOptions, getQueryParams } = require('../lib/response')

// 状态映射
const STATUS_MAP = {
  'sora-2': {
    'succeeded': 'SUCCESS',
    'failed': 'FAILURE',
    'processing': 'PROCESSING',
    'pending': 'PENDING',
    'success': 'SUCCESS',
    'failure': 'FAILURE',
    'queued': 'PENDING'
  }
}

function mapResponseStatus(model, apiStatus) {
  const modelMap = STATUS_MAP[model] || STATUS_MAP['sora-2']
  return modelMap[apiStatus?.toLowerCase()] || apiStatus || 'PENDING'
}

exports.main_handler = async (event, context) => {
  // 处理 OPTIONS 预检请求
  if (event.httpMethod === 'OPTIONS') {
    return handleOptions()
  }

  // 只接受 GET 请求
  if (event.httpMethod !== 'GET') {
    return error('Method not allowed', 405)
  }

  try {
    const params = getQueryParams(event)
    const { task_id, model } = params

    if (!task_id) {
      return error('缺少 task_id 参数', 400)
    }

    // 获取 API Key
    const apiKey = getT8StarKey()

    console.log(`[video-status] Querying task: ${task_id}`)

    // 发送请求
    const response = await axios.get(
      `https://ai.t8star.cn/v2/videos/generations/${task_id}`,
      {
        headers: {
          'Authorization': `Bearer ${apiKey}`
        },
        timeout: 30000
      }
    )

    const result = response.data

    // 映射状态
    const apiStatus = result.status || result.data?.status
    const normalizedStatus = mapResponseStatus(model || 'sora-2', apiStatus)

    // 提取视频 URL
    const videoUrl = result.data?.output || result.video_url || result.data?.video_url

    // 提取进度
    const progress = result.progress || result.data?.progress || '0%'

    console.log(`[video-status] Task: ${task_id}, Status: ${normalizedStatus}`)

    return success({
      status: normalizedStatus,
      task_id: task_id,
      progress: progress,
      video_url: videoUrl || null,
      fail_reason: result.fail_reason || result.data?.fail_reason || null
    })

  } catch (err) {
    console.error('[video-status] Error:', err.message)
    if (err.response) {
      console.error('[video-status] API Error:', err.response.data)
      return error(
        err.response.data?.error?.message || err.response.data?.message || '查询失败',
        err.response.status || 500,
        err.response.data
      )
    }
    return error(err.message || '服务器错误')
  }
}