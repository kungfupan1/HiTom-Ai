/**
 * 看图生成文案 API
 * POST /api/ai/analyze-images
 * 复刻自 MyWebTool ai_service.py 的 generate_selling_points_from_images 逻辑
 */

const fetch = require('node-fetch')
const { getModelScopeKey } = require('../../lib/api-key-fetcher')

// 语言映射
const LANG_MAP = {
  "中文": "Chinese", "简体中文": "Simplified Chinese", "繁体中文": "Traditional Chinese",
  "英语": "English", "英文": "English",
  "日语": "Japanese", "日文": "Japanese",
  "韩语": "Korean", "韩文": "Korean",
  "法语": "French", "德语": "German", "俄语": "Russian",
  "西班牙语": "Spanish", "葡萄牙语": "Portuguese", "意大利语": "Italian",
  "荷兰语": "Dutch", "波兰语": "Polish", "瑞典语": "Swedish",
  "越南语": "Vietnamese", "泰语": "Thai", "印尼语": "Indonesian",
  "马来语": "Malay", "菲律宾语": "Filipino", "印地语": "Hindi",
  "阿拉伯语": "Arabic", "土耳其语": "Turkish"
}

module.exports = async (req, res) => {
  // 处理 CORS
  res.setHeader('Access-Control-Allow-Origin', '*')
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS')
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')

  if (req.method === 'OPTIONS') {
    return res.status(200).end()
  }

  if (req.method !== 'POST') {
    return res.status(405).json({ status: 'error', message: 'Method not allowed' })
  }

  try {
    const body = typeof req.body === 'string' ? JSON.parse(req.body) : req.body
    const { images, product_type, design_style, target_lang, target_num } = body

    // 验证必填参数
    if (!images || images.length === 0) {
      return res.status(400).json({
        status: 'error',
        message: '缺少图片数据'
      })
    }

    // 获取 API Key - 支持从后端数据库获取（负载均衡）
    let apiKey
    try {
      apiKey = await getModelScopeKey()
    } catch (e) {
      return res.status(500).json({
        status: 'error',
        message: e.message || 'API Key 获取失败'
      })
    }

    // 参数处理
    const productType = product_type || '通用产品'
    const designStyle = design_style || '现代简约'
    const targetLang = LANG_MAP[target_lang] || 'Chinese'
    const targetNum = target_num || 1

    // 构建动态格式模板
    const formatParts = []
    for (let i = 1; i <= targetNum; i++) {
      formatParts.push(`Set ${i}:\nMain Title: ...\nSubtitle: ...`)
    }
    const formatExample = formatParts.join('\n\n')

    // 构建强约束 Prompt - 复刻 MyWebTool 的逻辑
    const promptText = `
[Role] Senior E-commerce Copywriter specialized in **${targetLang}**.

[Input Info]
- Product Category: ${productType}
- Desired Style: ${designStyle}
- **TARGET LANGUAGE: ${targetLang}**

[Task]
Analyze these product images. Combine visual features with "${productType}" to write catchy 'Main Title' and 'Subtitle'.

[Requirement]
Generate exactly **${targetNum} distinct sets**.

[CRITICAL RULES]
1. **OUTPUT MUST BE IN ${targetLang}**.
2. Do NOT use English unless the target language is English.
3. Even if the input is Chinese/English, translate your thoughts to **${targetLang}**.

[Format]:
${formatExample}

(Direct output only. Language: ${targetLang})
`

    // 构建消息内容 - 支持多图
    const contentList = [{ type: 'text', text: promptText }]

    // 处理图片 - 只取前3张
    const validImages = images.filter(img => img).slice(0, 3)
    for (const imgBase64 of validImages) {
      // 确保图片格式正确
      let imgUrl = imgBase64
      if (!imgBase64.startsWith('data:image')) {
        imgUrl = `data:image/jpeg;base64,${imgBase64}`
      }
      contentList.push({
        type: 'image_url',
        image_url: { url: imgUrl }
      })
    }

    const payload = {
      model: 'Qwen/Qwen3-VL-30B-A3B-Instruct',
      messages: [{ role: 'user', content: contentList }],
      max_tokens: 1500,
      temperature: 0.7
    }

    const endpoint = 'https://api-inference.modelscope.cn/v1/chat/completions'

    console.log(`[analyze-images] Product: ${productType}, Language: ${targetLang}, Images: ${validImages.length}`)

    // 发送请求
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    })

    const result = await response.json()

    if (!response.ok) {
      console.error('[analyze-images] API Error:', result)
      return res.status(response.status).json({
        status: 'error',
        message: result.error?.message || result.message || 'API 请求失败',
        detail: result
      })
    }

    // 提取并清理内容
    let content = result.choices[0].message.content.trim()
    content = content.replace(/\*\*/g, '').replace(/##/g, '')

    console.log(`[analyze-images] Success, content length: ${content.length}`)

    return res.status(200).json({
      status: 'success',
      content: content
    })

  } catch (error) {
    console.error('[analyze-images] Error:', error)
    return res.status(500).json({
      status: 'error',
      message: error.message || '服务器错误'
    })
  }
}