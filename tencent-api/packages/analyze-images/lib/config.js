/**
 * 配置管理
 */

// API Keys - 在腾讯云函数环境变量中配置
const T8STAR_API_KEY = process.env.T8STAR_API_KEY || ''
const MODELSCOPE_API_KEY = process.env.MODELSCOPE_API_KEY || ''

/**
 * 获取 T8Star API Key
 */
function getT8StarKey() {
  if (!T8STAR_API_KEY) {
    throw new Error('T8STAR_API_KEY 未配置')
  }
  return T8STAR_API_KEY
}

/**
 * 获取 ModelScope API Key
 */
function getModelScopeKey() {
  if (!MODELSCOPE_API_KEY) {
    throw new Error('MODELSCOPE_API_KEY 未配置')
  }
  return MODELSCOPE_API_KEY
}

module.exports = {
  getT8StarKey,
  getModelScopeKey
}