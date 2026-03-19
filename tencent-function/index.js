'use strict';

/**
 * Hi-Tom-AI 腾讯云函数 - API Key 替换代理
 *
 * 功能：前端发送带占位符的请求，云函数替换为真实 API Key 后转发到 AI 服务商
 *
 * 占位符：
 *   - MODELSCOPE_API_KEY → 替换为 ModelScope Key
 *   - T8STAR_API_KEY → 替换为 T8Star Key
 *
 * 请求格式：
 *   Headers: { Authorization: "Bearer T8STAR_API_KEY" }  ← 占位符
 *   Body: {
 *     target_url: "https://ai.t8star.cn/v2/videos/generations",  ← 真实 API 地址
 *     model: "sora-2",
 *     prompt: "...",
 *     ...
 *   }
 */

// ==========================================
// 1. API Key 密钥池
// ==========================================
const KEY_POOL = {
  modelscope: [
    // TODO: 填入你的 ModelScope API Keys
    "ms-904194b2-24f4-40fa-994a-d23694510f21"
  ],
  t8star: [
    // TODO: 填入你的 T8Star API Keys
    "sk-t8star-key-01"
  ]
};

// ==========================================
// 2. 工具函数
// ==========================================

/**
 * 从密钥池随机选择一个 Key
 */
function getRandomKey(provider) {
  const keys = KEY_POOL[provider];
  if (!keys || keys.length === 0) {
    throw new Error(`密钥池中没有 ${provider} 的 Key`);
  }
  return keys[Math.floor(Math.random() * keys.length)];
}

/**
 * 检测占位符类型
 * @returns {'modelscope' | 't8star' | null}
 */
function detectPlaceholderType(str) {
  if (str.includes('MODELSCOPE_API_KEY')) return 'modelscope';
  if (str.includes('T8STAR_API_KEY')) return 't8star';
  return null;
}

/**
 * 替换字符串中的占位符
 */
function replacePlaceholder(str, placeholder, realKey) {
  const regex = new RegExp(placeholder, 'g');
  return str.replace(regex, realKey);
}

// ==========================================
// 3. 云函数主入口
// ==========================================
exports.main_handler = async (event, context) => {
  console.log('[云函数] 收到请求:', event.httpMethod, event.path);

  // CORS 响应头
  const corsHeaders = {
    'Content-Type': 'application/json',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization'
  };

  // 处理 OPTIONS 预检请求
  if (event.httpMethod === 'OPTIONS') {
    return { statusCode: 200, headers: corsHeaders, body: '' };
  }

  try {
    // ==========================================
    // 4. 解析请求
    // ==========================================

    const rawBody = event.body || '';
    const rawHeadersStr = JSON.stringify(event.headers || {});

    // 检测占位符类型（优先从 headers 检测，因为 Authorization 在 headers 中）
    let placeholderType = detectPlaceholderType(rawHeadersStr) || detectPlaceholderType(rawBody);

    if (!placeholderType) {
      console.error('[云函数] 未找到占位符');
      return {
        statusCode: 400,
        headers: corsHeaders,
        body: JSON.stringify({
          status: 'error',
          message: '请求中未找到 MODELSCOPE_API_KEY 或 T8STAR_API_KEY 占位符'
        })
      };
    }

    // ==========================================
    // 5. 替换占位符
    // ==========================================

    const placeholder = placeholderType === 'modelscope' ? 'MODELSCOPE_API_KEY' : 'T8STAR_API_KEY';
    const realKey = getRandomKey(placeholderType);

    console.log(`[云函数] 检测到占位符: ${placeholder}, 替换为密钥: ${realKey.substring(0, 10)}...`);

    // 替换 headers 中的占位符
    let finalHeadersStr = replacePlaceholder(rawHeadersStr, placeholder, realKey);
    const finalHeaders = JSON.parse(finalHeadersStr);

    // 删除不需要转发的 headers
    delete finalHeaders['host'];
    delete finalHeaders['content-length'];

    // ==========================================
    // 6. 解析 target_url 并准备请求体
    // ==========================================

    let targetUrl = '';
    let finalBody = rawBody;
    let httpMethod = event.httpMethod || 'POST';

    // 解析请求体
    let bodyObj = {};
    if (rawBody) {
      try {
        bodyObj = JSON.parse(rawBody);
      } catch (e) {
        // 如果不是 JSON，保持原样
        bodyObj = {};
      }
    }

    // 从请求体提取 target_url
    if (bodyObj.target_url) {
      targetUrl = bodyObj.target_url;
      delete bodyObj.target_url;  // 不转发给 AI 商

      // 替换 body 中的占位符（如果有）
      const bodyStr = JSON.stringify(bodyObj);
      finalBody = replacePlaceholder(bodyStr, placeholder, realKey);

      console.log(`[云函数] 目标 URL: ${targetUrl}`);
    }

    // 如果没有 target_url，返回错误
    if (!targetUrl) {
      console.error('[云函数] 缺少 target_url');
      return {
        statusCode: 400,
        headers: corsHeaders,
        body: JSON.stringify({
          status: 'error',
          message: '请求体中缺少 target_url 字段'
        })
      };
    }

    // ==========================================
    // 7. 处理 GET 请求（如视频状态查询）
    // ==========================================

    const fetchOptions = {
      method: httpMethod,
      headers: finalHeaders
    };

    // GET 请求不需要 body
    if (httpMethod !== 'GET' && finalBody) {
      fetchOptions.body = finalBody;
    }

    console.log(`[云函数] 转发请求: ${httpMethod} ${targetUrl}`);

    // ==========================================
    // 8. 发起真实请求
    // ==========================================

    const response = await fetch(targetUrl, fetchOptions);
    const responseText = await response.text();

    console.log(`[云函数] 收到响应: ${response.status}`);

    // ==========================================
    // 9. 返回结果
    // ==========================================

    return {
      statusCode: response.status,
      headers: corsHeaders,
      body: responseText
    };

  } catch (error) {
    console.error('[云函数] 错误:', error.message);
    return {
      statusCode: 500,
      headers: corsHeaders,
      body: JSON.stringify({
        status: 'error',
        message: '云函数处理失败',
        detail: error.message
      })
    };
  }
};