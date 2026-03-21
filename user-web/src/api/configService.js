/**
 * 模型配置服务
 * 用于获取和管理模型的完整配置信息
 */
import request from './request'

// 配置缓存
const configCache = new Map()
const CACHE_DURATION = 5 * 60 * 1000 // 5分钟缓存

/**
 * 获取模型完整配置
 * @param {string} modelId - 模型ID
 * @returns {Promise<object>} 模型配置
 */
export async function getModelConfig(modelId) {
  // 检查缓存
  const cached = configCache.get(modelId)
  if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
    return cached.config
  }

  try {
    const model = await request.get(`/api/models/${modelId}`)

    // 缓存配置
    configCache.set(modelId, {
      config: model,
      timestamp: Date.now()
    })

    return model
  } catch (error) {
    console.error(`[ConfigService] 获取模型配置失败: ${modelId}`, error)
    return null
  }
}

/**
 * 获取多个模型配置
 * @param {string} modelType - 模型类型 (video/image/text)
 * @returns {Promise<array>} 模型列表
 */
export async function getModelList(modelType = null) {
  try {
    const params = modelType ? { model_type: modelType } : {}
    return await request.get('/api/models', { params })
  } catch (error) {
    console.error('[ConfigService] 获取模型列表失败', error)
    return []
  }
}

/**
 * 清除配置缓存
 */
export function clearConfigCache() {
  configCache.clear()
}

/**
 * 从模型配置获取 API 端点信息
 * @param {object} model - 模型配置对象
 * @returns {object} { url, placeholder }
 */
export function getApiEndpoint(model) {
  if (!model || !model.config_schema) {
    return null
  }

  const apiContract = model.config_schema?.api_contract
  if (!apiContract) {
    return null
  }

  return {
    url: apiContract.endpoint_url || model.base_url + model.endpoint,
    placeholder: model.api_provider === 'modelscope' ? 'MODELSCOPE_API_KEY' : 'T8STAR_API_KEY'
  }
}

/**
 * 从模型配置构建请求参数
 * @param {object} model - 模型配置对象
 * @param {object} formData - 用户表单数据
 * @returns {object} 构建后的请求参数
 */
export function buildRequestPayload(model, formData) {
  if (!model || !model.config_schema?.request_mapping) {
    // 没有配置，返回原始数据
    return formData
  }

  const requestMapping = model.config_schema.request_mapping
  const payload = {}

  // 1. 添加静态参数
  if (requestMapping.static_params) {
    Object.assign(payload, requestMapping.static_params)
  }

  // 2. 映射动态参数
  if (requestMapping.dynamic_params) {
    for (const [sourceField, targetField] of Object.entries(requestMapping.dynamic_params)) {
      if (formData[sourceField] !== undefined) {
        payload[targetField] = formData[sourceField]
      }
    }
  }

  return payload
}

/**
 * API 端点配置（默认值，用于 fallback）
 */
export const DEFAULT_ENDPOINTS = {
  MODELSCOPE_CHAT: {
    url: 'https://api-inference.modelscope.cn/v1/chat/completions',
    placeholder: 'MODELSCOPE_API_KEY'
  },
  T8STAR_VIDEO: {
    url: 'https://ai.t8star.cn/v2/videos/generations',
    placeholder: 'T8STAR_API_KEY'
  },
  T8STAR_IMAGE: {
    url: 'https://ai.t8star.cn/v1/images/generations',
    placeholder: 'T8STAR_API_KEY'
  }
}

export default {
  getModelConfig,
  getModelList,
  clearConfigCache,
  getApiEndpoint,
  buildRequestPayload,
  DEFAULT_ENDPOINTS
}