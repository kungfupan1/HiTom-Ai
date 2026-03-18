/**
 * API Key 获取工具
 * 从后端数据库获取 API Key，支持负载均衡/薅羊毛策略
 */

const fetch = require('node-fetch')

/**
 * 从后端获取指定 provider 的 API Key
 * @param {string} provider - t8star 或 modelscope
 * @param {string} backendUrl - 后端 URL
 * @param {string} secret - 内部认证密钥
 * @returns {Promise<string>} API Key
 */
async function getAPIKey(provider, backendUrl, secret) {
  if (!backendUrl) {
    throw new Error('BACKEND_URL 未配置')
  }

  const url = `${backendUrl}/api/keys/${provider}?secret=${encodeURIComponent(secret || 'hi-tom-ai-internal-secret')}`

  try {
    const response = await fetch(url)
    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || `获取 API Key 失败: ${response.status}`)
    }

    const data = await response.json()
    return data.key
  } catch (error) {
    console.error(`[getAPIKey] 获取 ${provider} API Key 失败:`, error.message)
    throw error
  }
}

/**
 * 获取 T8Star API Key
 * 优先从后端数据库获取，如果失败则回退到环境变量
 */
async function getT8StarKey() {
  const backendUrl = process.env.BACKEND_URL
  const secret = process.env.BACKEND_SECRET

  // 优先尝试从后端获取
  if (backendUrl) {
    try {
      return await getAPIKey('t8star', backendUrl, secret)
    } catch (e) {
      console.warn('[getT8StarKey] 从后端获取失败，回退到环境变量:', e.message)
    }
  }

  // 回退到环境变量
  const key = process.env.T8STAR_API_KEY
  if (!key) {
    throw new Error('T8STAR_API_KEY 未配置')
  }
  return key
}

/**
 * 获取 ModelScope API Key
 * 优先从后端数据库获取（支持多 Key 负载均衡），如果失败则回退到环境变量
 */
async function getModelScopeKey() {
  const backendUrl = process.env.BACKEND_URL
  const secret = process.env.BACKEND_SECRET

  // 优先尝试从后端获取
  if (backendUrl) {
    try {
      return await getAPIKey('modelscope', backendUrl, secret)
    } catch (e) {
      console.warn('[getModelScopeKey] 从后端获取失败，回退到环境变量:', e.message)
    }
  }

  // 回退到环境变量
  const key = process.env.MODELSCOPE_API_KEY
  if (!key) {
    throw new Error('MODELSCOPE_API_KEY 未配置')
  }
  return key
}

module.exports = {
  getAPIKey,
  getT8StarKey,
  getModelScopeKey
}