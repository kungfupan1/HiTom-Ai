/**
 * 工具函数 - Provider 参数映射引擎
 */

const { getT8StarKey, getModelScopeKey } = require('./api-key-fetcher')

/**
 * 参数映射配置
 * 定义前端参数到 API 参数的映射规则
 */
const PARAM_MAPPINGS = {
  // Sora-2 参数映射
  'sora-2': {
    fieldMapping: {
      ratio: 'aspect_ratio',
      images: 'images'
    },
    typeConverters: {
      duration: (val) => String(val),
      hd: (val) => val === true || val === '1080P'
    },
    defaultValues: {
      private: true
    }
  },
  'sora-2-pro': {
    fieldMapping: {
      ratio: 'aspect_ratio',
      images: 'images'
    },
    typeConverters: {
      duration: (val) => String(val),
      hd: (val) => val === true || val === '1080P'
    },
    defaultValues: {
      private: true
    }
  },
  // Grok Video 3 参数映射
  'grok-video-3': {
    fieldMapping: {
      // Grok 用 ratio，不用 aspect_ratio
      ratio: 'ratio',
      images: 'images'
    },
    typeConverters: {
      duration: (val) => parseInt(val), // Grok 要整数
      resolution: (val) => val // 直接传递
    },
    defaultValues: {}
  }
}

/**
 * 状态映射配置
 * 将不同 API 的状态统一为标准状态
 */
const STATUS_MAPPINGS = {
  'sora-2': {
    SUCCESS: 'SUCCESS',
    FAILURE: 'FAILURE',
    processing: 'PROCESSING'
  },
  'sora-2-pro': {
    SUCCESS: 'SUCCESS',
    FAILURE: 'FAILURE',
    processing: 'PROCESSING'
  },
  'grok-video-3': {
    SUCCESS: 'SUCCESS',
    FAILURE: 'FAILURE',
    IN_PROGRESS: 'PROCESSING',
    NOT_START: 'PENDING'
  }
}

/**
 * 映射请求参数
 * @param {string} modelId - 模型ID
 * @param {object} params - 前端传入的参数
 * @param {object} modelConfig - 模型配置（从后端获取）
 * @returns {object} - 映射后的 API 请求参数
 */
function mapRequestParams(modelId, params, modelConfig) {
  const mapping = PARAM_MAPPINGS[modelId] || { fieldMapping: {}, typeConverters: {}, defaultValues: {} }
  const result = {}

  // 1. 添加模型名
  result.model = modelId

  // 2. 处理 prompt（必传）
  result.prompt = params.prompt || ''

  // 3. 根据映射规则转换参数
  for (const [frontKey, value] of Object.entries(params)) {
    if (frontKey === 'model' || frontKey === 'prompt') continue

    // 获取映射后的字段名
    const apiKey = mapping.fieldMapping[frontKey] || frontKey

    // 类型转换
    let convertedValue = value
    if (mapping.typeConverters[frontKey]) {
      convertedValue = mapping.typeConverters[frontKey](value)
    }

    result[apiKey] = convertedValue
  }

  // 4. 添加默认值
  for (const [key, value] of Object.entries(mapping.defaultValues || {})) {
    if (result[key] === undefined) {
      result[key] = value
    }
  }

  return result
}

/**
 * 映射响应状态
 * @param {string} modelId - 模型ID
 * @param {string} apiStatus - API 返回的状态
 * @returns {string} - 统一后的状态
 */
function mapResponseStatus(modelId, apiStatus) {
  const mapping = STATUS_MAPPINGS[modelId] || {}
  return mapping[apiStatus] || apiStatus
}

/**
 * 从响应中提取数据
 * @param {object} response - API 响应
 * @param {object} mapping - 响应映射规则
 * @returns {object} - 提取后的数据
 */
function extractResponseData(response, mapping) {
  const result = {}

  if (!mapping) {
    return response
  }

  // 提取 task_id
  if (mapping.task_id) {
    result.task_id = response.task_id || response.data?.task_id
  }

  // 提取状态
  if (mapping.status) {
    result.status = response.status || response.data?.status
  }

  // 提取视频 URL
  if (mapping.video_url) {
    result.video_url = response.data?.output || response.video_url || response.data?.video_url
  }

  // 提取进度
  result.progress = response.progress || response.data?.progress || '0%'

  return result
}

/**
 * 获取 API Key（同步版本，仅从环境变量获取，用于兼容）
 * @param {string} provider - 服务商名称
 * @returns {string} - API Key
 */
function getApiKey(provider) {
  const keys = {
    't8star': process.env.T8STAR_API_KEY,
    'modelscope': process.env.MODELSCOPE_API_KEY
  }
  return keys[provider] || process.env.T8STAR_API_KEY
}

/**
 * 获取 API Key（异步版本，支持从后端数据库获取）
 * @param {string} provider - 服务商名称
 * @returns {Promise<string>} - API Key
 */
async function getApiKeyAsync(provider) {
  if (provider === 't8star') {
    return await getT8StarKey()
  } else if (provider === 'modelscope') {
    return await getModelScopeKey()
  }
  return await getT8StarKey()
}

module.exports = {
  PARAM_MAPPINGS,
  STATUS_MAPPINGS,
  mapRequestParams,
  mapResponseStatus,
  extractResponseData,
  getApiKey,
  getApiKeyAsync
}