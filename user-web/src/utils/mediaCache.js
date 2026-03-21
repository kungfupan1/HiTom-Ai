/**
 * 媒体缓存工具 - 使用 IndexedDB 存储图片和视频
 */

const DB_NAME = 'hi-tom-media-cache'
const DB_VERSION = 1
const STORE_NAME = 'media'

let db = null

// 初始化数据库
const initDB = () => {
  return new Promise((resolve, reject) => {
    if (db) {
      resolve(db)
      return
    }

    const request = indexedDB.open(DB_NAME, DB_VERSION)

    request.onerror = () => {
      console.error('IndexedDB 打开失败')
      reject(request.error)
    }

    request.onsuccess = () => {
      db = request.result
      resolve(db)
    }

    request.onupgradeneeded = (event) => {
      const database = event.target.result
      if (!database.objectStoreNames.contains(STORE_NAME)) {
        database.createObjectStore(STORE_NAME, { keyPath: 'url' })
      }
    }
  })
}

/**
 * 缓存媒体文件
 * @param {string} url - 原始 URL
 * @param {Blob} blob - 文件 blob
 * @param {string} type - 类型 'image' 或 'video'
 */
export const cacheMedia = async (url, blob, type = 'image') => {
  try {
    const database = await initDB()
    const tx = database.transaction(STORE_NAME, 'readwrite')
    const store = tx.objectStore(STORE_NAME)

    const data = {
      url,
      blob,
      type,
      timestamp: Date.now()
    }

    store.put(data)

    return new Promise((resolve, reject) => {
      tx.oncomplete = () => resolve(true)
      tx.onerror = () => reject(tx.error)
    })
  } catch (e) {
    console.error('缓存媒体失败', e)
    return false
  }
}

/**
 * 获取缓存的媒体文件
 * @param {string} url - 原始 URL
 * @returns {Promise<{blob: Blob, blobUrl: string, type: string} | null>}
 */
export const getCachedMedia = async (url) => {
  try {
    const database = await initDB()
    const tx = database.transaction(STORE_NAME, 'readonly')
    const store = tx.objectStore(STORE_NAME)

    const request = store.get(url)

    return new Promise((resolve, reject) => {
      request.onsuccess = () => {
        const data = request.result
        if (data && data.blob) {
          const blobUrl = URL.createObjectURL(data.blob)
          resolve({
            blob: data.blob,
            blobUrl,
            type: data.type
          })
        } else {
          resolve(null)
        }
      }
      request.onerror = () => reject(request.error)
    })
  } catch (e) {
    console.error('获取缓存失败', e)
    return null
  }
}

/**
 * 删除缓存的媒体文件
 * @param {string} url - 原始 URL
 */
export const deleteCachedMedia = async (url) => {
  try {
    const database = await initDB()
    const tx = database.transaction(STORE_NAME, 'readwrite')
    const store = tx.objectStore(STORE_NAME)

    store.delete(url)

    return new Promise((resolve, reject) => {
      tx.oncomplete = () => resolve(true)
      tx.onerror = () => reject(tx.error)
    })
  } catch (e) {
    console.error('删除缓存失败', e)
    return false
  }
}

/**
 * 清理过期缓存（超过 7 天）
 */
export const cleanExpiredCache = async () => {
  try {
    const database = await initDB()
    const tx = database.transaction(STORE_NAME, 'readwrite')
    const store = tx.objectStore(STORE_NAME)

    const request = store.openCursor()
    const now = Date.now()
    const expireTime = 7 * 24 * 60 * 60 * 1000 // 7 天

    request.onsuccess = (event) => {
      const cursor = event.target.result
      if (cursor) {
        const data = cursor.value
        if (now - data.timestamp > expireTime) {
          cursor.delete()
        }
        cursor.continue()
      }
    }
  } catch (e) {
    console.error('清理缓存失败', e)
  }
}

/**
 * 下载并缓存媒体文件
 * @param {string} url - 原始 URL
 * @param {string} type - 类型 'image' 或 'video'
 * @returns {Promise<{blobUrl: string, fromCache: boolean}>}
 */
export const fetchAndCacheMedia = async (url, type = 'image') => {
  // 先检查缓存
  const cached = await getCachedMedia(url)
  if (cached) {
    return { blobUrl: cached.blobUrl, fromCache: true }
  }

  // 下载
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error('下载失败')
  }

  const blob = await response.blob()

  // 缓存
  await cacheMedia(url, blob, type)

  // 返回 blob URL
  const blobUrl = URL.createObjectURL(blob)
  return { blobUrl, fromCache: false }
}

// 页面加载时清理过期缓存
if (typeof window !== 'undefined') {
  cleanExpiredCache()
}