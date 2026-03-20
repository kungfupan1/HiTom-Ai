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
 * 生成图片 (参考旧项目 MyWebTool 的 generate_image_workflow)
 * @param {object} data - { model, prompt, aspect_ratio, resolution, images, seed }
 */
export const generateImage = (data) => {
  const { prompt, aspect_ratio, resolution, images, seed } = data

  // 计算尺寸 (复刻旧项目逻辑)
  const ratioMap = {
    '1:1': [1, 1], '2:3': [2, 3], '3:2': [3, 2], '3:4': [3, 4], '4:3': [4, 3],
    '4:5': [4, 5], '5:4': [5, 4], '9:16': [9, 16], '16:9': [16, 9], '21:9': [21, 9]
  }
  const sizeMap = { '1K': 1024, '2K': 2048, '4K': 4096 }

  const ratio = aspect_ratio || '3:4'
  const res = resolution || '1K'
  const [wRatio, hRatio] = ratioMap[ratio] || [1, 1]
  const baseSize = sizeMap[res] || 1024

  let width, height
  if (wRatio >= hRatio) {
    width = baseSize
    height = Math.round(baseSize * hRatio / wRatio)
  } else {
    height = baseSize
    width = Math.round(baseSize * wRatio / hRatio)
  }
  const pixelSize = `${width}x${height}`

  // 确定模型
  const modelName = resolution === '4K' ? 'nano-banana-2-4k' : 'nano-banana-2'

  // 处理 seed
  const finalSeed = seed && seed !== -1 ? seed : Date.now()

  // 构建最终 prompt
  const finalPrompt = `${prompt} --seed ${finalSeed}`

  // 处理参考图 (只取前5张)
  let imgList = null
  if (images && images.length > 0) {
    imgList = images.slice(0, 5).map(img => {
      if (!img.startsWith('data:image')) {
        return `data:image/jpeg;base64,${img}`
      }
      return img
    })
  }

  const payload = {
    model: modelName,
    prompt: finalPrompt,
    size: pixelSize,
    response_format: 'url',
    image: imgList
  }

  return callAI(
    AI_ENDPOINTS.GENERATE_IMAGE.placeholder,
    AI_ENDPOINTS.GENERATE_IMAGE.url,
    payload,
    { timeout: 120000 }
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
 * 生图提示词规划 (参考旧项目 MyWebTool 的详细 Prompt)
 * @param {object} data - { images, product_type, selling_points, design_style, target_lang, num_screens }
 */
export const planImagePrompts = (data) => {
  const { images, product_type, selling_points, design_style, target_lang, num_screens } = data

  const productType = product_type || '通用产品'
  const designStyle = design_style || '现代简约'
  const targetLang = target_lang || '中文'
  const numScreens = num_screens || 1

  // 语言映射
  const langMap = {
    "中文": "Chinese", "简体中文": "Simplified Chinese", "繁体中文": "Traditional Chinese",
    "英语": "English", "英文": "English", "日语": "Japanese", "日文": "Japanese",
    "韩语": "Korean", "韩文": "Korean", "法语": "French", "德语": "German",
    "俄语": "Russian", "西班牙语": "Spanish", "葡萄牙语": "Portuguese", "意大利语": "Italian",
    "荷兰语": "Dutch", "波兰语": "Polish", "瑞典语": "Swedish",
    "越南语": "Vietnamese", "泰语": "Thai", "印尼语": "Indonesian",
    "马来语": "Malay", "菲律宾语": "Filipino", "印地语": "Hindi",
    "阿拉伯语": "Arabic", "土耳其语": "Turkish"
  }
  const langEng = langMap[targetLang] || 'Chinese'

  // 详细 System Instruction (复刻旧项目)
  const systemInstruction = `[角色] 你是一名资深电商详情页设计师与 AI 文生图提示词工程师。
[任务目标] 根据产品信息，规划并生成 **${numScreens} 屏** 详情页的文生图提示词。

[强制语言规则 - STRICTLY ENFORCED]
1. **目标语言锁定**：所有的"主文案"和"副文案"必须严格使用 **${langEng}**。
2. **拒绝干扰**：即使用户的【核心卖点】或【产品名称】中包含其他语言（如英文、中文混合），你必须将其翻译或转换为 **${langEng}** 输出。
3. **纯净性**：绝对禁止中英混杂。如果是英文目标语言，不要出现任何汉字；如果是中文目标语言，不要出现非必要的英文。

[视觉纯净规则 - 绝对禁止]
1. **文字隔离**：画面中除主副文案外，**严禁**出现任何装饰性汉字、印章。
2. **字体隔离**：必须使用国际通用术语：如 "Sans-serif", "Serif", "Bold Modern Font"。
3. **元素隔离**：必须使用符合该语言语境的背景元素。

[强制执行规则]
1. **数量严格匹配**：用户要求生成 ${numScreens} 屏，你必须输出 **${numScreens} 条** 独立的提示词。
2. **输出结构**：每屏内容必须包含："主文案、副文案、设计与排版、画面主体与构图、画质与细节"。
3. **多图参考**：用户提供了多张参考图，请综合分析这些图片的特征（角度、细节、场景）来规划画面。

[输出格式模板]
请严格按照以下格式输出（不要输出表格，只输出文本段落）：

第1屏：
主文案："..."
副文案："..."
文案设计与排版：...
画面主体与构图：...
画质与细节：...

第2屏：
...
（以此类推，直到第 ${numScreens} 屏）`

  // 用户请求
  const userReq = `【产品信息】
1. 产品类型: ${productType}
2. 核心卖点: ${selling_points || ''}
3. 设计风格: ${designStyle}

【重要配置】
**目标语言 (Target Language): ${langEng}** (请确保文案只使用 ${langEng})

【执行要求】
请基于以上信息，发挥创意，规划出 **${numScreens} 屏** 的画面。
(请参考附带的所有图片作为产品外观依据)

请直接开始按顺序输出每一屏的内容。`

  // 构建消息内容
  const userContent = [{ type: 'text', text: userReq }]

  // 添加图片
  const validImages = (images || []).filter(img => img).slice(0, 5)
  for (const imgBase64 of validImages) {
    let imgUrl = imgBase64
    if (!imgBase64.startsWith('data:image')) {
      imgUrl = `data:image/jpeg;base64,${imgBase64}`
    }
    userContent.push({
      type: 'image_url',
      image_url: { url: imgUrl }
    })
  }

  return callAI(
    AI_ENDPOINTS.ANALYZE_IMAGES.placeholder,
    AI_ENDPOINTS.ANALYZE_IMAGES.url,
    {
      model: 'Qwen/Qwen3-VL-30B-A3B-Instruct',
      messages: [
        { role: 'system', content: systemInstruction },
        { role: 'user', content: userContent }
      ],
      max_tokens: 4000,
      temperature: 0.7
    },
    { timeout: 180000 }
  )
}