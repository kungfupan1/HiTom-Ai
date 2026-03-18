/**
 * 视频状态查询 API
 * GET /api/ai/video-status?task_id=xxx&model=xxx
 */

const fetch = require('node-fetch')
const { mapResponseStatus, getApiKeyAsync } = require('../lib/provider-mapper')

module.exports = async (req, res) => {
  // 处理 CORS
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')

  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }

  if (req.method !== 'GET') {
    return res.status(405).json({ status: 'error', message: 'Method not allowed' })
  }

  try {
    const { task_id, model } = req.query

    if (!task_id) {
      return res.status(400).json({
        status: 'error',
        message: '缺少 task_id 参数'
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

    // API 端点
    const endpoint = `https://ai.t8star.cn/v2/videos/generations/${task_id}`

    console.log(`[video-status] Querying task: ${task_id}`)

    // 发送请求
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${apiKey}`
      }
    })

    const result = await response.json()

    if (!response.ok) {
      console.error('[video-status] API Error:', result)
      return res.status(response.status).json({
        status: 'error',
        message: result.error?.message || result.message || '查询失败',
        detail: result
      })
    }

    // 映射状态
    const apiStatus = result.status || result.data?.status
    const normalizedStatus = mapResponseStatus(model || 'sora-2', apiStatus)

    // 提取视频 URL
    const videoUrl = result.data?.output || result.video_url || result.data?.video_url

    // 提取进度
    const progress = result.progress || result.data?.progress || '0%'

    console.log(`[video-status] Task: ${task_id}, Status: ${normalizedStatus}`)

    return res.status(200).json({
      status: normalizedStatus,
      task_id: task_id,
      progress: progress,
      video_url: videoUrl || null,
      fail_reason: result.fail_reason || result.data?.fail_reason || null
    })

  } catch (error) {
    console.error('[video-status] Error:', error)
    return res.status(500).json({
      status: 'error',
      message: error.message || '服务器错误'
    })
  }
}