/**
 * 看图生成文案 API
 * 腾讯云函数版本
 */

const axios = require('axios')
const { getModelScopeKey } = require('../lib/config')
const { success, error, handleOptions, parseBody } = require('../lib/response')

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
    const { images, product_type, design_style, target_lang, target_num } = body

    // 验证必填参数
    if (!images || images.length === 0) {
      return error('缺少图片数据', 400)
    }

    // 获取 API Key
    const apiKey = getModelScopeKey()

    // 参数处理
    const productType = product_type || '通用产品'
    const designStyle = design_style || '现代简约'
    const targetLang = LANG_MAP[target_lang] || 'Chinese'
    const targetNum = target_num || 1

    // 构建格式模板
    const formatParts = []
    for (let i = 1; i <= targetNum; i++) {
      formatParts.push(`Set ${i}:\nMain Title: ...\nSubtitle: ...`)
    }
    const formatExample = formatParts.join('\n\n')

    // 构建 Prompt
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

    // 构建消息内容
    const contentList = [{ type: 'text', text: promptText }]

    // 处理图片 - 只取前3张
    const validImages = images.filter(img => img).slice(0, 3)
    for (const imgBase64 of validImages) {
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

    console.log(`[analyze-images] Product: ${productType}, Language: ${targetLang}, Images: ${validImages.length}`)

    // 发送请求
    const response = await axios.post(
      'https://api-inference.modelscope.cn/v1/chat/completions',
      payload,
      {
        headers: {
          'Authorization': `Bearer ${apiKey}`,
          'Content-Type': 'application/json'
        },
        timeout: 120000 // 2分钟超时
      }
    )

    // 提取并清理内容
    let content = response.data.choices[0].message.content.trim()
    content = content.replace(/\*\*/g, '').replace(/##/g, '')

    console.log(`[analyze-images] Success, content length: ${content.length}`)

    return success({ content })

  } catch (err) {
    console.error('[analyze-images] Error:', err.message)
    if (err.response) {
      console.error('[analyze-images] API Error:', err.response.data)
      return error(
        err.response.data?.error?.message || err.response.data?.message || 'API 请求失败',
        err.response.status || 500,
        err.response.data
      )
    }
    return error(err.message || '服务器错误')
  }
}