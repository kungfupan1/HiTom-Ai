import request from './request'

// 获取视频模型列表
export const getVideoModels = () => {
  return request.get('/api/models', { params: { model_type: 'video' } })
}

// 获取图片模型列表
export const getImageModels = () => {
  return request.get('/api/models', { params: { model_type: 'image' } })
}

// 计算费用
export const calculateCost = (data) => {
  return request.post('/api/calculate-cost', data)
}

// 预扣积分
export const reservePoints = (data) => {
  return request.post('/api/points/reserve', data)
}

// 确认扣费
export const confirmPoints = (deductionId) => {
  return request.post('/api/points/confirm', { deduction_id: deductionId })
}

// 退还积分
export const refundPoints = (deductionId, reason) => {
  return request.post('/api/points/refund', { deduction_id: deductionId, reason })
}

// 获取费用说明（包含 tencent_function_url）
export const getPricingInfo = () => {
  return request.get('/api/config/pricing-info')
}

// ==========================================
// 腾讯云函数 AI 代理 API（占位符模式）
// ==========================================

/**
 * 通用 AI 请求函数
 * @param {string} placeholder - 占位符类型：'MODELSCOPE_API_KEY' 或 'T8STAR_API_KEY'
 * @param {string} targetUrl - 目标 AI API 地址
 * @param {object} body - 请求体数据
 * @param {object} options - 额外选项（如 timeout）
 */
async function callAI(placeholder, targetUrl, body, options = {}) {
  // 从后端获取腾讯云函数 URL
  const config = await getPricingInfo()
  const functionUrl = config.tencent_function_url

  if (!functionUrl) {
    throw new Error('腾讯云函数 URL 未配置，请在管理后台设置 tencent_function_url')
  }

  // 构建请求体：包含 target_url 和业务数据
  const payload = {
    target_url: targetUrl,
    target_method: options.method || 'POST', // 👈 动态获取请求方法
    ...body
  }

  // 发送到腾讯云函数，Authorization 头使用占位符
  return request.post(functionUrl, payload, {
    headers: {
      'Authorization': `Bearer ${placeholder}`
    },
    timeout: options.timeout || 60000
  })
}

// API 端点配置
const AI_ENDPOINTS = {
  // ModelScope 端点
  ANALYZE_IMAGES: {
    url: 'https://api-inference.modelscope.cn/v1/chat/completions',
    placeholder: 'MODELSCOPE_API_KEY'
  },
  // T8Star 端点
  GENERATE_VIDEO: {
    url: 'https://ai.t8star.cn/v2/videos/generations',
    placeholder: 'T8STAR_API_KEY'
  },
  VIDEO_STATUS: {
    url: 'https://ai.t8star.cn/v2/videos/generations',  // 需要拼接 task_id
    placeholder: 'T8STAR_API_KEY'
  },
  GENERATE_IMAGE: {
    url: 'https://ai.t8star.cn/v1/images/generations',
    placeholder: 'T8STAR_API_KEY'
  }
}

/**
 * 看图生成文案
 * @param {object} data - { images, product_type, design_style, target_lang, target_num }
 */
export const analyzeImages = (data) => {
  return callAI(
    AI_ENDPOINTS.ANALYZE_IMAGES.placeholder,
    AI_ENDPOINTS.ANALYZE_IMAGES.url,
    {
      model: 'Qwen/Qwen3-VL-30B-A3B-Instruct',
      messages: buildAnalyzeMessages(data),
      max_tokens: 1500,
      temperature: 0.7
    },
    { timeout: 120000 }  // 2分钟超时
  )
}

/**
 * 构建看图写文案的消息格式
 */
function buildAnalyzeMessages(data) {
  const { images, product_type, design_style, target_lang, target_num } = data

  const productType = product_type || '通用产品'
  const designStyle = design_style || '现代简约'
  const targetLang = target_lang || 'Chinese'
  const targetNum = target_num || 1

  // 构建格式模板
  const formatParts = []
  for (let i = 1; i <= targetNum; i++) {
    formatParts.push(`Set ${i}:\nMain Title: ...\nSubtitle: ...`)
  }

  const promptText = `
[Role] Senior E-commerce Copywriter specialized in **${targetLang}**.
[Input Info]
- Product Category: ${productType}
- Desired Style: ${designStyle}
- **TARGET LANGUAGE: ${targetLang}**
[Task]
Analyze these product images. Write catchy 'Main Title' and 'Subtitle'.
[Requirement]
Generate exactly **${targetNum} distinct sets**.
[CRITICAL RULES]
1. **OUTPUT MUST BE IN ${targetLang}**.
2. Do NOT use English unless the target language is English.
[Format]:
${formatParts.join('\n\n')}
(Direct output only. Language: ${targetLang})
`

  // 构建消息内容
  const content = [{ type: 'text', text: promptText }]

  // 添加图片
  const validImages = (images || []).filter(img => img).slice(0, 3)
  for (const imgBase64 of validImages) {
    let imgUrl = imgBase64
    if (!imgBase64.startsWith('data:image')) {
      imgUrl = `data:image/jpeg;base64,${imgBase64}`
    }
    content.push({
      type: 'image_url',
      image_url: { url: imgUrl }
    })
  }

  return [{ role: 'user', content }]
}

/**
 * 生成视频
 * @param {object} data - { model, prompt, duration, ratio, resolution, images }
 */
export const generateVideo = (data) => {
  const { model, prompt, duration, ratio, resolution, images } = data

  // 根据模型构建不同的请求体
  const payload = {
    model,
    prompt
  }

  // 比例处理
  const aspectRatio = ratio || '9:16'
  if (model === 'grok-video-3') {
    payload.ratio = aspectRatio
  } else {
    payload.aspect_ratio = aspectRatio
    payload.private = true
  }

  // 🚨 修复 1：智能时长映射 (Sora 强校验 4, 8, 12)
  const dur = parseInt(duration || 10, 10)
  if (model === 'grok-video-3') {
    // grok 接受数字
    payload.duration = dur
  } else if (model.includes('sora')) {
    // sora 只能接受指定的字符串秒数，我们做个向下兼容映射
    if (dur <= 5) {
      payload.duration = '4'
    } else if (dur <= 10) {
      payload.duration = '8'
    } else {
      payload.duration = '12'
    }
  } else {
    // 其他模型默认传字符串
    payload.duration = String(dur)
  }

  // 分辨率处理
  payload.hd = (resolution === '1080P')

  // 参考图
  if (images && images.length > 0) {
    payload.images = [images[0]]
  }

  // 🚨 修复 2：将超时时间从 60 秒延长到 3 分钟 (180000ms)，给 Grok 充足的缓冲时间
  return callAI(
    AI_ENDPOINTS.GENERATE_VIDEO.placeholder,
    AI_ENDPOINTS.GENERATE_VIDEO.url,
    payload,
    { timeout: 180000 }
  )
}

/**
 * 查询视频状态
 * @param {string} taskId - 任务ID
 * @param {string} model - 模型名称（可选，用于状态映射）
 */
export const getVideoStatus = (taskId, model) => {
  // 视频状态是 GET 请求，需要特殊处理
  const targetUrl = `${AI_ENDPOINTS.VIDEO_STATUS.url}/${taskId}`

  return callAI(
    AI_ENDPOINTS.VIDEO_STATUS.placeholder,
    targetUrl,
    {},  // GET 请求没有 body
    { timeout: 30000, method: 'GET' } // 👈 明确使用 GET
  )
}

/**
 * 生成图片
 * @param {object} data - { model, prompt, size, images }
 */
export const generateImage = (data) => {
  const { model, prompt, size, images } = data

  const payload = {
    model,
    prompt,
    response_format: 'url'
  }

  if (size) payload.size = size
  if (images && images.length > 0) payload.image = images

  return callAI(
    AI_ENDPOINTS.GENERATE_IMAGE.placeholder,
    AI_ENDPOINTS.GENERATE_IMAGE.url,
    payload,
    { timeout: 60000 }
  )
}

/**
 * 翻译文本
 * @param {object} data - { text, target_lang }
 */
export const translateText = (data) => {
  const { text, target_lang } = data
  const targetLang = target_lang || 'Chinese'

  const promptText = `
[Role] Professional Translator.
[Task] Translate the following content into **${targetLang}**.
[Rule] Output ONLY the translated text. No explanations.

[Content]:
${text}
`

  return callAI(
    AI_ENDPOINTS.ANALYZE_IMAGES.placeholder,
    AI_ENDPOINTS.ANALYZE_IMAGES.url,
    {
      model: 'Qwen/Qwen3-VL-30B-A3B-Instruct',
      messages: [{ role: 'user', content: promptText }],
      max_tokens: 2000,
      temperature: 0.3
    },
    { timeout: 60000 }
  )
}

/**
 * 生图提示词规划
 * @param {object} data - { images, product_type, selling_points, design_style, target_lang, num_screens }
 */
export const planImagePrompts = (data) => {
  const { images, product_type, selling_points, design_style, target_lang, num_screens } = data

  const productType = product_type || '通用产品'
  const designStyle = design_style || '现代简约'
  const targetLang = target_lang || 'Chinese'
  const numScreens = num_screens || 1

  const promptText = `
[Role] Expert E-commerce Visual Designer.
[Task] Plan ${numScreens} distinct image generation prompts for a product detail page.

[Product Info]
- Product: ${productType}
- Selling Points: ${selling_points}
- Design Style: ${designStyle}
- Target Language: ${targetLang}

[Output Format]
Return a JSON array with ${numScreens} prompt strings. Each prompt should be detailed and suitable for AI image generation.
Example: ["prompt 1...", "prompt 2...", "prompt 3..."]

[Requirements]
1. Each prompt should describe a complete scene
2. Include product placement, lighting, background
3. Make prompts suitable for e-commerce use
4. Output ONLY the JSON array, no other text
`

  // 构建消息内容
  const content = [{ type: 'text', text: promptText }]

  // 添加图片
  const validImages = (images || []).filter(img => img).slice(0, 3)
  for (const imgBase64 of validImages) {
    let imgUrl = imgBase64
    if (!imgBase64.startsWith('data:image')) {
      imgUrl = `data:image/jpeg;base64,${imgBase64}`
    }
    content.push({
      type: 'image_url',
      image_url: { url: imgUrl }
    })
  }

  return callAI(
    AI_ENDPOINTS.ANALYZE_IMAGES.placeholder,
    AI_ENDPOINTS.ANALYZE_IMAGES.url,
    {
      model: 'Qwen/Qwen3-VL-30B-A3B-Instruct',
      messages: [{ role: 'user', content }],
      max_tokens: 4000,
      temperature: 0.7
    },
    { timeout: 120000 }
  )
}