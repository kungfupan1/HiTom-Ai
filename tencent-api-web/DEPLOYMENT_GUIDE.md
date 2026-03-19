# 腾讯云函数部署设计文档

## 一、项目背景

### 1.1 目标
将 Hi-Tom-AI 项目的 AI 接口从 Vercel 迁移到腾讯云函数（SCF），解决 Vercel 免费版 10 秒超时限制问题。

### 1.2 需要部署的函数
| 函数名 | 功能 | 超时时间 | 环境变量 |
|--------|------|----------|----------|
| analyze-images | 看图生成文案 | 120秒 | MODELSCOPE_API_KEY |
| generate-video | 视频生成 | 60秒 | T8STAR_API_KEY |
| video-status | 视频状态查询 | 30秒 | T8STAR_API_KEY |
| generate-image | 图片生成 | 60秒 | T8STAR_API_KEY |

### 1.3 API 端点设计
```
POST /api/ai/analyze-images   - 看图生成文案
POST /api/ai/generate-video   - 生成视频
GET  /api/ai/video-status     - 查询视频状态
POST /api/ai/generate-image   - 生成图片
```

---

## 二、当前遇到的问题

### 2.1 错误信息
```
{"errorMessage":"127 code exit unexpected: /usr/bin/env: bash\r/var/lang/node16/bin/node app.js: No such file or directory"}
```

### 2.2 问题原因分析
1. Windows 换行符（CRLF）污染了 `scf_bootstrap` 文件
2. `scf_bootstrap` 是腾讯云自动生成的启动脚本，不能有 `\r` 字符
3. 上传文件夹时，Windows 环境可能带入错误的换行符

### 2.4 解决方案建议
1. 使用腾讯云控制台的「在线编辑器」直接编辑代码
2. 或者在 Linux/Mac 环境打包后上传
3. 或者使用 Serverless Framework CLI 部署

---

## 三、腾讯云函数类型说明

**重要**：腾讯云函数有两种类型，必须选择正确的类型：

| 类型 | 入口文件 | Handler 格式 | 适用场景 |
|------|----------|--------------|----------|
| **事件函数** | index.js | exports.main_handler | API 网关触发、定时触发 |
| **Web 函数** | app.js | Express 应用 | 函数 URL 触发、HTTP 直接访问 |

**推荐使用「事件函数」+ API 网关**，但 API 网关将于 2025年6月停止服务。

**如果使用「函数 URL」触发，必须使用「Web 函数」格式。**

---

## 四、代码设计

### 4.1 事件函数格式（推荐）

**文件结构：**
```
analyze-images/
├── index.js          # 主入口
├── package.json
└── node_modules/
```

**index.js 模板：**
```javascript
/**
 * 看图生成文案 API - 腾讯云事件函数
 */
const axios = require('axios')

const MODELSCOPE_API_KEY = process.env.MODELSCOPE_API_KEY || ''

// CORS 响应头
const HEADERS = {
  'Content-Type': 'application/json',
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization'
}

// 成功响应
function success(data) {
  return {
    statusCode: 200,
    headers: HEADERS,
    body: JSON.stringify({ status: 'success', ...data })
  }
}

// 错误响应
function error(message, statusCode = 500) {
  return {
    statusCode,
    headers: HEADERS,
    body: JSON.stringify({ status: 'error', message })
  }
}

// OPTIONS 预检
function handleOptions() {
  return { statusCode: 200, headers: HEADERS, body: '' }
}

// 解析请求体
function parseBody(event) {
  if (event.body) {
    try {
      return JSON.parse(event.body)
    } catch (e) {
      return {}
    }
  }
  return {}
}

// 语言映射
const LANG_MAP = {
  "中文": "Chinese", "简体中文": "Simplified Chinese", "繁体中文": "Traditional Chinese",
  "英语": "English", "英文": "English",
  "日语": "Japanese", "日文": "Japanese",
  "韩语": "Korean", "韩文": "Korean",
  "法语": "French", "德语": "German", "俄语": "Russian",
  "西班牙语": "Spanish", "葡萄牙语": "Portuguese", "意大利语": "Italian"
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

    if (!images || images.length === 0) {
      return error('缺少图片数据', 400)
    }

    if (!MODELSCOPE_API_KEY) {
      return error('MODELSCOPE_API_KEY 未配置', 500)
    }

    const productType = product_type || '通用产品'
    const designStyle = design_style || '现代简约'
    const targetLang = LANG_MAP[target_lang] || 'Chinese'
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
- TARGET LANGUAGE: ${targetLang}
[Task]
Analyze these product images. Write catchy 'Main Title' and 'Subtitle'.
[Requirement]
Generate exactly ${targetNum} distinct sets.
[Format]:
${formatParts.join('\n\n')}
(Direct output only. Language: ${targetLang})
`

    const contentList = [{ type: 'text', text: promptText }]
    const validImages = images.filter(img => img).slice(0, 3)

    for (const imgBase64 of validImages) {
      let imgUrl = imgBase64
      if (!imgBase64.startsWith('data:image')) {
        imgUrl = `data:image/jpeg;base64,${imgBase64}`
      }
      contentList.push({ type: 'image_url', image_url: { url: imgUrl } })
    }

    const response = await axios.post(
      'https://api-inference.modelscope.cn/v1/chat/completions',
      {
        model: 'Qwen/Qwen3-VL-30B-A3B-Instruct',
        messages: [{ role: 'user', content: contentList }],
        max_tokens: 1500,
        temperature: 0.7
      },
      {
        headers: {
          'Authorization': `Bearer ${MODELSCOPE_API_KEY}`,
          'Content-Type': 'application/json'
        },
        timeout: 120000
      }
    )

    let content = response.data.choices[0].message.content.trim()
    content = content.replace(/\*\*/g, '').replace(/##/g, '')

    return success({ content })

  } catch (err) {
    console.error('[analyze-images] Error:', err.message)
    if (err.response) {
      return error(err.response.data?.error?.message || 'API 请求失败', err.response.status || 500)
    }
    return error(err.message || '服务器错误')
  }
}
```

**package.json：**
```json
{
  "name": "analyze-images",
  "version": "1.0.0",
  "main": "index.js",
  "dependencies": {
    "axios": "^1.6.0"
  }
}
```

---

### 4.2 Web 函数格式（函数 URL 触发）

**文件结构：**
```
analyze-images/
├── app.js            # Express 应用
├── package.json
└── node_modules/
```

**app.js 模板：**
```javascript
const express = require('express')
const cors = require('cors')
const axios = require('axios')

const app = express()
app.use(cors())
app.use(express.json({ limit: '50mb' }))

const MODELSCOPE_API_KEY = process.env.MODELSCOPE_API_KEY || ''

const LANG_MAP = {
  "中文": "Chinese", "英语": "English", "日语": "Japanese", "韩语": "Korean"
}

app.get('/', (req, res) => {
  res.json({ status: 'ok', service: 'analyze-images' })
})

app.post('/api/ai/analyze-images', async (req, res) => {
  try {
    const { images, product_type, design_style, target_lang, target_num } = req.body
    if (!images || images.length === 0) {
      return res.status(400).json({ status: 'error', message: '缺少图片数据' })
    }

    const productType = product_type || '通用产品'
    const targetLang = LANG_MAP[target_lang] || 'Chinese'
    const targetNum = target_num || 1

    const promptText = `[Role] E-commerce Copywriter in ${targetLang}.
[Task] Analyze product images, write catchy title and subtitle.
Generate ${targetNum} sets. Output in ${targetLang}.`

    const contentList = [{ type: 'text', text: promptText }]
    const validImages = images.filter(img => img).slice(0, 3)

    for (const imgBase64 of validImages) {
      let imgUrl = imgBase64.startsWith('data:image') ? imgBase64 : `data:image/jpeg;base64,${imgBase64}`
      contentList.push({ type: 'image_url', image_url: { url: imgUrl } })
    }

    const response = await axios.post(
      'https://api-inference.modelscope.cn/v1/chat/completions',
      {
        model: 'Qwen/Qwen3-VL-30B-A3B-Instruct',
        messages: [{ role: 'user', content: contentList }],
        max_tokens: 1500
      },
      {
        headers: { 'Authorization': `Bearer ${MODELSCOPE_API_KEY}` },
        timeout: 120000
      }
    )

    let content = response.data.choices[0].message.content.trim()
    content = content.replace(/\*\*/g, '').replace(/##/g, '')

    res.json({ status: 'success', content })
  } catch (err) {
    res.status(500).json({ status: 'error', message: err.message })
  }
})

module.exports = app
```

**package.json：**
```json
{
  "name": "analyze-images",
  "version": "1.0.0",
  "main": "app.js",
  "dependencies": {
    "axios": "^1.6.0",
    "cors": "^2.8.5",
    "express": "^4.18.2"
  }
}
```

---

## 五、部署步骤

### 方案 A：控制台手动部署（推荐新手）

#### 步骤 1：创建函数
1. 登录腾讯云控制台：https://console.cloud.tencent.com/scf
2. 点击「新建」→「从头创建」
3. 选择函数类型：
   - **事件函数**：用于 API 网关
   - **Web 函数**：用于函数 URL
4. 填写配置：
   - 函数名称：`analyze-images`
   - 运行环境：Node.js 16.13
   - 超时时间：120 秒
   - 内存：256 MB
5. 环境变量：
   - `MODELSCOPE_API_KEY` = `ms-904194b2-24f4-40fa-994a-d23694510f21`

#### 步骤 2：上传代码
**方法 1：在线编辑（推荐，避免换行符问题）**
1. 创建时选择「空白函数」模板
2. 创建成功后，进入「函数代码」
3. 在线编辑器中粘贴代码
4. 在「终端」中运行 `npm install axios` 安装依赖
5. 点击「部署」

**方法 2：本地上传**
1. 在本地创建文件夹，放入 index.js 和 package.json
2. 运行 `npm install` 安装依赖
3. 将整个文件夹打包成 zip（确保在 Linux/Mac 环境打包，避免 CRLF）
4. 上传 zip 文件

#### 步骤 3：配置触发器
- **API 网关**（事件函数）：路径 `/api/ai/analyze-images`，方法 POST
- **函数 URL**（Web 函数）：自动生成，直接访问

#### 步骤 4：测试
```bash
# 健康检查（Web 函数）
curl https://你的函数URL/

# 完整测试
curl -X POST https://你的函数URL/api/ai/analyze-images \
  -H "Content-Type: application/json" \
  -d '{"images": ["base64图片数据"], "product_type": "测试产品"}'
```

---

### 方案 B：Serverless Framework CLI 部署

#### 步骤 1：安装
```bash
npm install -g serverless
```

#### 步骤 2：配置凭证
```bash
serverless config credentials --provider tencent \
  --secret_id YOUR_SECRET_ID \
  --secret_key YOUR_SECRET_KEY
```

#### 步骤 3：创建 serverless.yml
```yaml
service: hi-tom-ai

provider:
  name: tencent
  runtime: Nodejs16.13
  region: ap-guangzhou

functions:
  analyze-images:
    handler: index.main_handler
    timeout: 120
    memorySize: 256
    environment:
      MODELSCOPE_API_KEY: ms-904194b2-24f4-40fa-994a-d23694510f21
    events:
      - apigw:
          path: /api/ai/analyze-images
          method: POST
```

#### 步骤 4：部署
```bash
serverless deploy
```

---

## 六、其他三个函数的代码

### 6.1 generate-video

```javascript
// index.js - 事件函数格式
const axios = require('axios')

const T8STAR_API_KEY = process.env.T8STAR_API_KEY || ''

const HEADERS = {
  'Content-Type': 'application/json',
  'Access-Control-Allow-Origin': '*'
}

function success(data) {
  return { statusCode: 200, headers: HEADERS, body: JSON.stringify({ status: 'success', ...data }) }
}

function error(message, statusCode = 500) {
  return { statusCode, headers: HEADERS, body: JSON.stringify({ status: 'error', message }) }
}

function handleOptions() {
  return { statusCode: 200, headers: HEADERS, body: '' }
}

function parseBody(event) {
  try { return JSON.parse(event.body) } catch { return {} }
}

exports.main_handler = async (event, context) => {
  if (event.httpMethod === 'OPTIONS') return handleOptions()
  if (event.httpMethod !== 'POST') return error('Method not allowed', 405)

  try {
    const { model, prompt, duration, ratio, images } = parseBody(event)

    if (!model || !prompt) return error('缺少必要参数', 400)
    if (!T8STAR_API_KEY) return error('T8STAR_API_KEY 未配置', 500)

    const payload = {
      model,
      prompt,
      aspect_ratio: ratio || '9:16',
      duration: String(duration || 10),
      private: true
    }

    if (images && images.length > 0) payload.images = [images[0]]

    const response = await axios.post(
      'https://ai.t8star.cn/v2/videos/generations',
      payload,
      { headers: { 'Authorization': `Bearer ${T8STAR_API_KEY}` }, timeout: 60000 }
    )

    return success({ task_id: response.data.task_id })
  } catch (err) {
    return error(err.response?.data?.message || err.message)
  }
}
```

### 6.2 video-status

```javascript
// index.js - 事件函数格式
const axios = require('axios')

const T8STAR_API_KEY = process.env.T8STAR_API_KEY || ''

const HEADERS = {
  'Content-Type': 'application/json',
  'Access-Control-Allow-Origin': '*'
}

function success(data) {
  return { statusCode: 200, headers: HEADERS, body: JSON.stringify({ status: 'success', ...data }) }
}

function error(message, statusCode = 500) {
  return { statusCode, headers: HEADERS, body: JSON.stringify({ status: 'error', message }) }
}

exports.main_handler = async (event, context) => {
  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 200, headers: HEADERS, body: '' }
  }

  try {
    const query = event.queryStringParameters || {}
    const { task_id } = query

    if (!task_id) return error('缺少 task_id', 400)
    if (!T8STAR_API_KEY) return error('T8STAR_API_KEY 未配置', 500)

    const response = await axios.get(
      `https://ai.t8star.cn/v2/videos/generations/${task_id}`,
      { headers: { 'Authorization': `Bearer ${T8STAR_API_KEY}` }, timeout: 30000 }
    )

    const result = response.data
    const status = result.status || result.data?.status || 'PENDING'
    const videoUrl = result.data?.output || result.video_url

    return success({
      status: status.toUpperCase(),
      task_id,
      video_url: videoUrl || null
    })
  } catch (err) {
    return error(err.response?.data?.message || err.message)
  }
}
```

### 6.3 generate-image

```javascript
// index.js - 事件函数格式
const axios = require('axios')

const T8STAR_API_KEY = process.env.T8STAR_API_KEY || ''

const HEADERS = {
  'Content-Type': 'application/json',
  'Access-Control-Allow-Origin': '*'
}

function success(data) {
  return { statusCode: 200, headers: HEADERS, body: JSON.stringify({ status: 'success', ...data }) }
}

function error(message, statusCode = 500) {
  return { statusCode, headers: HEADERS, body: JSON.stringify({ status: 'error', message }) }
}

function handleOptions() {
  return { statusCode: 200, headers: HEADERS, body: '' }
}

function parseBody(event) {
  try { return JSON.parse(event.body) } catch { return {} }
}

exports.main_handler = async (event, context) => {
  if (event.httpMethod === 'OPTIONS') return handleOptions()
  if (event.httpMethod !== 'POST') return error('Method not allowed', 405)

  try {
    const { model, prompt, size } = parseBody(event)

    if (!model || !prompt) return error('缺少必要参数', 400)
    if (!T8STAR_API_KEY) return error('T8STAR_API_KEY 未配置', 500)

    const response = await axios.post(
      'https://ai.t8star.cn/v1/images/generations',
      { model, prompt, response_format: 'url' },
      { headers: { 'Authorization': `Bearer ${T8STAR_API_KEY}` }, timeout: 60000 }
    )

    const images = response.data.data?.map(item => item.url) || []

    return success({ images })
  } catch (err) {
    return error(err.response?.data?.message || err.message)
  }
}
```

---

## 七、API Keys

```
MODELSCOPE_API_KEY = ms-904194b2-24f4-40fa-994a-d23694510f21
T8STAR_API_KEY = sk-xxx (需要用户提供)
```

---

## 八、验收标准

部署完成后，需要验证：

1. **健康检查**（Web 函数）：
   ```bash
   curl https://函数URL/
   # 期望返回: {"status":"ok","service":"analyze-images"}
   ```

2. **analyze-images 测试**：
   ```bash
   curl -X POST https://函数URL/api/ai/analyze-images \
     -H "Content-Type: application/json" \
     -d '{"images": ["test"], "product_type": "测试"}'
   # 期望返回: {"status":"success","content":"..."}
   ```

3. **其他三个函数同样测试**

---

## 九、注意事项

1. **换行符问题**：Windows 环境上传可能导致 CRLF 问题，建议使用在线编辑器或 Linux 环境
2. **超时设置**：analyze-images 需要设置 120 秒超时
3. **内存设置**：建议 256MB
4. **环境变量**：务必正确配置 API Key
5. **CORS**：确保响应头包含 `Access-Control-Allow-Origin: *`