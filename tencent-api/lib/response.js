/**
 * API 网关响应工具
 */

/**
 * 成功响应
 */
function success(data) {
  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type,Authorization'
    },
    body: JSON.stringify({
      status: 'success',
      ...data
    })
  }
}

/**
 * 错误响应
 */
function error(message, statusCode = 500, detail = null) {
  return {
    statusCode,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type,Authorization'
    },
    body: JSON.stringify({
      status: 'error',
      message,
      ...(detail && { detail })
    })
  }
}

/**
 * 处理 OPTIONS 预检请求
 */
function handleOptions() {
  return {
    statusCode: 200,
    headers: {
      'Content-Type': 'application/json',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type,Authorization'
    },
    body: ''
  }
}

/**
 * 解析请求体
 */
function parseBody(event) {
  if (event.body) {
    try {
      return typeof event.body === 'string' ? JSON.parse(event.body) : event.body
    } catch (e) {
      return null
    }
  }
  return null
}

/**
 * 获取查询参数
 */
function getQueryParams(event) {
  return event.queryStringParameters || {}
}

module.exports = {
  success,
  error,
  handleOptions,
  parseBody,
  getQueryParams
}