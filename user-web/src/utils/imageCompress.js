/**
 * 图片压缩工具
 * 将图片压缩到指定大小范围和尺寸限制
 */

/**
 * 压缩图片到指定大小和尺寸
 * @param {string} base64 - 原始图片的 base64 字符串
 * @param {number} maxSizeKB - 目标最大大小（KB），默认 200KB
 * @param {number} minSizeKB - 目标最小大小（KB），默认 100KB
 * @param {number} maxDimension - 最大边长（像素），默认 2048
 * @returns {Promise<string>} - 压缩后的 base64 字符串
 */
export async function compressImage(base64, maxSizeKB = 400, minSizeKB = 200, maxDimension = 2048) {
  return new Promise((resolve, reject) => {
    // 如果不是 base64 图片，直接返回
    if (!base64.startsWith('data:image')) {
      resolve(base64)
      return
    }

    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')

      // 原始尺寸
      let width = img.width
      let height = img.height

      // 计算当前图片大小（KB）
      const currentSizeKB = getBase64Size(base64)

      // 如果尺寸超过限制，先缩小尺寸
      if (width > maxDimension || height > maxDimension) {
        const ratio = Math.min(maxDimension / width, maxDimension / height)
        width = Math.floor(width * ratio)
        height = Math.floor(height * ratio)
        console.log(`图片尺寸超限，缩放到: ${width}x${height}`)
      }

      // 如果已经足够小且尺寸不超标，直接返回
      if (currentSizeKB <= maxSizeKB && width === img.width && height === img.height) {
        resolve(base64)
        return
      }

      // 目标大小（字节）
      const maxSizeBytes = maxSizeKB * 1024

      // 二分法查找合适的质量
      let low = 0.1
      let high = 0.9
      let result = base64
      let attempts = 0
      const maxAttempts = 10

      while (attempts < maxAttempts) {
        const mid = (low + high) / 2

        canvas.width = width
        canvas.height = height
        ctx.drawImage(img, 0, 0, width, height)

        const compressed = canvas.toDataURL('image/jpeg', mid)
        const size = getBase64Size(compressed) * 1024

        if (size <= maxSizeBytes) {
          result = compressed
          high = mid
        } else {
          low = mid
        }

        attempts++
      }

      const finalSizeKB = getBase64Size(result)
      console.log(`图片压缩: ${currentSizeKB}KB -> ${finalSizeKB}KB, 尺寸: ${width}x${height}`)

      resolve(result)
    }

    img.onerror = () => {
      reject(new Error('图片加载失败'))
    }

    img.src = base64
  })
}

/**
 * 获取 base64 字符串的大小（KB）
 */
function getBase64Size(base64) {
  // 移除 data:image/xxx;base64, 前缀
  const base64String = base64.split(',')[1] || base64
  // base64 字符串每 4 个字符表示 3 个字节
  const bytes = (base64String.length * 3) / 4
  return Math.round(bytes / 1024)
}

/**
 * 批量压缩图片
 * @param {string[]} base64List - base64 字符串数组
 * @param {number} maxSizeKB - 目标最大大小（KB）
 * @param {number} minSizeKB - 目标最小大小（KB）
 * @returns {Promise<string[]>} - 压缩后的 base64 数组
 */
export async function compressImages(base64List, maxSizeKB = 400, minSizeKB = 300) {
  const results = []
  for (const base64 of base64List) {
    const compressed = await compressImage(base64, maxSizeKB, minSizeKB)
    results.push(compressed)
  }
  return results
}