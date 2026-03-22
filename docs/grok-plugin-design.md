# Grok 视频生成插件 - 详细设计文档

> 版本：v1.0
> 日期：2026-03-22
> 作者：Claude

---

## 一、项目概述

### 1.1 背景

Hi-Tom-AI 平台需要集成 Grok 视频生成能力，但 Grok API 价格昂贵。本方案通过浏览器插件自动化操作 Grok 网页版，实现低成本视频生成。

### 1.2 目标

- 用户通过 Hi-Tom-AI 前端发起 Grok 视频生成请求
- 后端转发任务到运行在 Win Server 上的浏览器插件
- 插件自动操作 Grok 页面生成视频
- 视频上传到云存储，返回公开 URL 给用户

### 1.3 系统边界

```
┌─────────────────────────────────────────────────────────────────────┐
│                          系统范围                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  【包含】                                                           │
│  ├── Chrome 浏览器插件（Manifest V3）                               │
│  ├── 后端 WebSocket API                                            │
│  ├── 任务队列管理                                                   │
│  └── 腾讯云 COS 上传                                                │
│                                                                     │
│  【不包含】                                                         │
│  ├── Grok 账号管理（使用现有账号）                                   │
│  └── Grok 页面异常处理（验证码等，需人工介入）                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 二、系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│   用户浏览器                                           Win Server          │
│   ┌──────────┐                                        ┌──────────────────┐  │
│   │          │  ①任务请求        ②任务转发            │                  │  │
│   │  前端    │ ─────────────→  ┌──────────┐ ───────→ │  Chrome 浏览器   │  │
│   │          │                 │          │          │  ┌────────────┐  │  │
│   └──────────┘                 │  后端    │          │  │ Grok 页面   │  │  │
│        ↑                       │  FastAPI │          │  │            │  │  │
│        │                       │          │          │  └────────────┘  │  │
│        │                       └──────────┘          │        ↑         │  │
│        │                            │                │  ┌────┴────┐    │  │
│        │                            │                │  │  插件   │    │  │
│        │  ⑥返回视频URL             │                │  └─────────┘    │  │
│        └────────────────────────────┘                └──────────────────┘  │
│                                    ↑                       │                │
│                                    │                       │                │
│                                    │ ⑤URL通知             │ ③DOM操作       │
│                                    │                       ↓                │
│                                    │              ┌──────────────┐          │
│                                    │              │   Grok CDN   │          │
│                                    │              └──────────────┘          │
│                                    │                       │                │
│                                    │              ④下载视频                 │
│                                    │                       │                │
│                                    │                       ↓                │
│                                    │              ┌──────────────┐          │
│                                    └──────────────│   腾讯云COS  │          │
│                                                    └──────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 数据流

```
┌─────────────────────────────────────────────────────────────────┐
│                        数据流详情                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ① 前端 → 后端                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ POST /api/grok-video/generate                           │   │
│  │ {                                                       │   │
│  │   "prompt": "一只猫在跳舞",                              │   │
│  │   "images": ["base64..."],                              │   │
│  │   "ratio": "16:9",                                      │   │
│  │   "resolution": "1080p",                                │   │
│  │   "duration": 10                                        │   │
│  │ }                                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│  数据量：几 KB                                                   │
│                                                                 │
│  ② 后端 → 插件                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ WebSocket 消息                                           │   │
│  │ {                                                       │   │
│  │   "type": "task",                                       │   │
│  │   "task_id": "uuid-xxx",                                │   │
│  │   "prompt": "...",                                      │   │
│  │   "images": ["base64..."],                              │   │
│  │   "params": { "ratio": "16:9", ... }                    │   │
│  │ }                                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│  数据量：几 KB - 几百 KB（含图片）                                │
│                                                                 │
│  ③ 插件 → Grok 页面                                             │
│  DOM 操作：填入提示词、上传图片、选择参数、点击生成               │
│  数据量：本地操作，无网络传输                                     │
│                                                                 │
│  ④ 插件 ← Grok CDN                                              │
│  下载视频文件                                                    │
│  数据量：几 MB - 几十 MB                                         │
│                                                                 │
│  ⑤ 插件 → 腾讯云 COS                                            │
│  上传视频文件                                                    │
│  数据量：几 MB - 几十 MB                                         │
│                                                                 │
│  ⑥ 插件 → 后端 → 前端                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ {                                                       │   │
│  │   "type": "result",                                     │   │
│  │   "task_id": "uuid-xxx",                                │   │
│  │   "status": "success",                                  │   │
│  │   "video_url": "https://xxx.cos.ap-guangzhou.myqcloud.com/xxx.mp4" │
│  │ }                                                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│  数据量：几十字节                                                 │
│                                                                 │
│  前端直接从 COS 下载视频播放                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 技术栈

| 组件 | 技术选型 | 说明 |
|------|----------|------|
| 浏览器插件 | Chrome Extension Manifest V3 | 最新标准 |
| 通信协议 | WebSocket | 实时双向通信 |
| 后端 | FastAPI + WebSocket | 复用现有后端 |
| 云存储 | 腾讯云 COS | 视频存储 |
| 文件上传 | STS 临时凭证 | 安全上传 |

---

## 三、详细设计

### 3.1 浏览器插件架构

```
grok-plugin/
├── manifest.json           # 插件配置文件
├── background.js           # Service Worker（后台服务）
├── content.js              # 内容脚本（注入 Grok 页面）
├── popup/
│   ├── popup.html          # 弹窗界面
│   └── popup.js            # 弹窗逻辑
├── utils/
│   ├── websocket.js        # WebSocket 管理
│   ├── grok-operator.js    # Grok 页面操作
│   ├── video-handler.js    # 视频下载上传
│   └── cos-uploader.js     # COS 上传
└── styles/
    └── popup.css
```

### 3.2 插件组件职责

#### 3.2.1 manifest.json

```json
{
  "manifest_version": 3,
  "name": "Hi-Tom-AI Grok Assistant",
  "version": "1.0.0",
  "description": "自动化 Grok 视频生成",
  "permissions": [
    "storage",
    "activeTab",
    "scripting"
  ],
  "host_permissions": [
    "https://grok.com/*",
    "https://assets.grok.com/*",
    "wss://your-backend.com/*",
    "https://*.cos.ap-guangzhou.myqcloud.com/*"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "content_scripts": [
    {
      "matches": ["https://grok.com/*"],
      "js": ["content.js"],
      "run_at": "document_idle"
    }
  ],
  "action": {
    "default_popup": "popup/popup.html",
    "default_icon": {
      "16": "icons/icon16.png",
      "48": "icons/icon48.png",
      "128": "icons/icon128.png"
    }
  }
}
```

#### 3.2.2 background.js（Service Worker）

**职责：**
- 管理 WebSocket 连接
- 接收后端任务
- 协调 content.js 执行
- 处理任务状态

**核心逻辑：**

```javascript
// WebSocket 连接管理
class WebSocketManager {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.reconnectDelay = 1000;
    this.maxReconnectDelay = 30000;
    this.isConnecting = false;
  }

  connect() {
    if (this.isConnecting || this.ws?.readyState === WebSocket.OPEN) return;

    this.isConnecting = true;
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log('[WS] 连接成功');
      this.reconnectDelay = 1000;
      this.isConnecting = false;
      this.send({ type: 'register', client: 'grok-plugin' });
    };

    this.ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onclose = () => {
      this.isConnecting = false;
      console.log('[WS] 连接断开，准备重连');
      setTimeout(() => this.connect(), this.reconnectDelay);
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, this.maxReconnectDelay);
    };

    this.ws.onerror = (error) => {
      console.error('[WS] 错误:', error);
      this.ws.close();
    };
  }

  async handleMessage(message) {
    switch (message.type) {
      case 'task':
        await this.executeTask(message);
        break;
      case 'ping':
        this.send({ type: 'pong' });
        break;
    }
  }

  async executeTask(task) {
    try {
      // 发送任务到 content.js
      const response = await chrome.tabs.sendMessage(this.grokTabId, {
        action: 'generateVideo',
        task: task
      });

      this.send({
        type: 'result',
        task_id: task.task_id,
        status: 'success',
        video_url: response.videoUrl
      });
    } catch (error) {
      this.send({
        type: 'result',
        task_id: task.task_id,
        status: 'failed',
        error: error.message
      });
    }
  }

  send(data) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
}

// 初始化
const wsManager = new WebSocketManager('wss://your-backend.com/ws/grok-plugin');
wsManager.connect();

// 心跳保活
setInterval(() => wsManager.send({ type: 'heartbeat' }), 30000);
```

#### 3.2.3 content.js（内容脚本）

**职责：**
- 注入到 Grok 页面
- 执行 DOM 操作
- 监听页面变化
- 下载并上传视频

**核心逻辑：**

```javascript
// Grok 页面操作器
class GrokOperator {
  constructor() {
    this.selectors = {
      // 提示词输入框
      promptInput: 'textarea[placeholder*="Ask"], div[contenteditable="true"]',

      // 参考图上传
      imageUpload: 'input[type="file"][accept*="image"]',
      imageUploadButton: 'button[aria-label*="image"], button[aria-label*="图片"]',

      // 参数选择
      ratioButton: (ratio) => `button[data-ratio="${ratio}"], button:contains("${ratio}")`,
      resolutionButton: (res) => `button[data-resolution="${res}"], button:contains("${res}")`,

      // 生成按钮
      generateButton: 'button[type="submit"], button:contains("Generate"), button:contains("生成")',

      // 视频元素
      videoElement: 'video[src*="generated"], video[src*="assets.grok"]',
      downloadLink: 'a[href*="generated_video"], a[download]'
    };

    this.taskInProgress = false;
  }

  // 填入提示词
  async fillPrompt(prompt) {
    const input = await this.waitForElement(this.selectors.promptInput, 10000);

    // 方式1：直接设置值
    if (input.tagName === 'TEXTAREA') {
      input.value = prompt;
      input.dispatchEvent(new Event('input', { bubbles: true }));
      input.dispatchEvent(new Event('change', { bubbles: true }));
    }
    // 方式2：contenteditable div
    else {
      input.focus();
      document.execCommand('insertText', false, prompt);
    }

    console.log('[GrokOperator] 提示词已填入');
  }

  // 上传参考图
  async uploadImages(images) {
    // 点击上传按钮
    const uploadButton = document.querySelector(this.selectors.imageUploadButton);
    if (uploadButton) uploadButton.click();

    await this.sleep(500);

    // 获取文件输入
    const fileInput = await this.waitForElement(this.selectors.imageUpload, 5000);

    // 创建文件
    const files = images.map((base64, index) =>
      this.base64ToFile(base64, `image_${index}.jpg`)
    );

    // 设置文件
    const dataTransfer = new DataTransfer();
    files.forEach(file => dataTransfer.items.add(file));
    fileInput.files = dataTransfer.files;

    // 触发事件
    fileInput.dispatchEvent(new Event('change', { bubbles: true }));

    console.log('[GrokOperator] 参考图已上传');
  }

  // 选择画面比例
  async selectRatio(ratio) {
    const button = document.querySelector(this.selectors.ratioButton(ratio));
    if (button) {
      button.click();
      console.log(`[GrokOperator] 比例已选择: ${ratio}`);
    } else {
      console.warn(`[GrokOperator] 未找到比例按钮: ${ratio}`);
    }
    await this.sleep(300);
  }

  // 选择分辨率
  async selectResolution(resolution) {
    const button = document.querySelector(this.selectors.resolutionButton(resolution));
    if (button) {
      button.click();
      console.log(`[GrokOperator] 分辨率已选择: ${resolution}`);
    }
    await this.sleep(300);
  }

  // 点击生成按钮
  async clickGenerate() {
    const button = await this.waitForElement(this.selectors.generateButton, 10000);
    button.click();
    console.log('[GrokOperator] 已点击生成按钮');
  }

  // 等待视频生成完成
  async waitForVideo(timeout = 300000) {
    const startTime = Date.now();

    console.log('[GrokOperator] 开始等待视频生成...');

    while (Date.now() - startTime < timeout) {
      // 检查视频元素
      const video = document.querySelector(this.selectors.videoElement);
      if (video?.src) {
        console.log('[GrokOperator] 检测到视频元素:', video.src);
        return video.src;
      }

      // 检查下载链接
      const downloadLink = document.querySelector(this.selectors.downloadLink);
      if (downloadLink?.href) {
        console.log('[GrokOperator] 检测到下载链接:', downloadLink.href);
        return downloadLink.href;
      }

      // 检查是否有错误提示
      const errorElement = document.querySelector('[class*="error"], [class*="failed"]');
      if (errorElement) {
        throw new Error(`Grok 生成失败: ${errorElement.textContent}`);
      }

      await this.sleep(2000);
    }

    throw new Error('视频生成超时');
  }

  // 下载视频
  async downloadVideo(videoUrl) {
    console.log('[GrokOperator] 开始下载视频:', videoUrl);

    const response = await fetch(videoUrl, {
      credentials: 'include'  // 携带 Grok 的认证 Cookie
    });

    if (!response.ok) {
      throw new Error(`视频下载失败: ${response.status}`);
    }

    const blob = await response.blob();
    console.log('[GrokOperator] 视频下载完成, 大小:', blob.size);

    return blob;
  }

  // 执行完整流程
  async generateVideo(task) {
    if (this.taskInProgress) {
      throw new Error('已有任务在执行中');
    }

    this.taskInProgress = true;

    try {
      // 1. 填入提示词
      await this.fillPrompt(task.prompt);
      await this.sleep(500);

      // 2. 上传参考图
      if (task.images?.length) {
        await this.uploadImages(task.images);
        await this.sleep(1000);
      }

      // 3. 选择参数
      if (task.params?.ratio) {
        await this.selectRatio(task.params.ratio);
      }
      if (task.params?.resolution) {
        await this.selectResolution(task.params.resolution);
      }

      // 4. 点击生成
      await this.clickGenerate();

      // 5. 等待完成
      const videoUrl = await this.waitForVideo(task.timeout || 300000);

      // 6. 下载视频
      const videoBlob = await this.downloadVideo(videoUrl);

      // 7. 上传到 COS
      const publicUrl = await COSUploader.upload(videoBlob, task.task_id);

      return { videoUrl: publicUrl };

    } finally {
      this.taskInProgress = false;
    }
  }

  // 工具方法
  waitForElement(selector, timeout = 10000) {
    return new Promise((resolve, reject) => {
      const element = document.querySelector(selector);
      if (element) return resolve(element);

      const observer = new MutationObserver(() => {
        const el = document.querySelector(selector);
        if (el) {
          observer.disconnect();
          resolve(el);
        }
      });

      observer.observe(document.body, { childList: true, subtree: true });

      setTimeout(() => {
        observer.disconnect();
        reject(new Error(`元素未找到: ${selector}`));
      }, timeout);
    });
  }

  base64ToFile(base64, filename) {
    const arr = base64.split(',');
    const mime = arr[0].match(/:(.*?);/)?.[1] || 'image/jpeg';
    const bstr = atob(arr[1]);
    const u8arr = new Uint8Array(bstr.length);
    for (let i = 0; i < bstr.length; i++) {
      u8arr[i] = bstr.charCodeAt(i);
    }
    return new File([u8arr], filename, { type: mime });
  }

  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// COS 上传器
class COSUploader {
  static async upload(blob, taskId) {
    // 1. 从后端获取临时上传凭证
    const credential = await this.getCredential(taskId);

    // 2. 使用 COS SDK 上传
    const cos = new COS({
      getAuthorization: (options, callback) => {
        callback({
          TmpSecretId: credential.secretId,
          TmpSecretKey: credential.secretKey,
          SecurityToken: credential.sessionToken,
          StartTime: credential.startTime,
          ExpiredTime: credential.expiredTime,
        });
      }
    });

    const key = `grok-videos/${taskId}.mp4`;
    const bucket = 'your-bucket-name';
    const region = 'ap-guangzhou';

    return new Promise((resolve, reject) => {
      cos.putObject({
        Bucket: bucket,
        Region: region,
        Key: key,
        Body: blob,
      }, (err, data) => {
        if (err) reject(err);
        else resolve(`https://${bucket}.cos.${region}.myqcloud.com/${key}`);
      });
    });
  }

  static async getCredential(taskId) {
    const response = await fetch('https://your-backend.com/api/cos-credential', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ task_id: taskId })
    });
    return response.json();
  }
}

// 初始化
const operator = new GrokOperator();

// 监听来自 background 的消息
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.action === 'generateVideo') {
    operator.generateVideo(message.task)
      .then(result => sendResponse(result))
      .catch(error => sendResponse({ error: error.message }));
    return true;  // 异步响应
  }
});

// 监听网络请求（备选方案：拦截视频 URL）
const originalFetch = window.fetch;
window.fetch = async (...args) => {
  const response = await originalFetch(...args);

  if (args[0]?.includes?.('generated_video')) {
    console.log('[GrokOperator] 拦截到视频请求:', args[0]);
    // 可以在这里处理视频 URL
  }

  return response;
};
```

### 3.3 后端 API 设计

#### 3.3.1 WebSocket 端点

```
wss://your-backend.com/ws/grok-plugin
```

**消息格式：**

```typescript
// 后端 → 插件：任务
interface TaskMessage {
  type: 'task';
  task_id: string;
  prompt: string;
  images?: string[];      // base64
  params: {
    ratio?: '16:9' | '9:16' | '1:1';
    resolution?: '720p' | '1080p';
    duration?: number;
  };
  timeout?: number;       // 超时时间（毫秒）
}

// 插件 → 后端：结果
interface ResultMessage {
  type: 'result';
  task_id: string;
  status: 'success' | 'failed';
  video_url?: string;
  error?: string;
}

// 心跳
interface HeartbeatMessage {
  type: 'heartbeat' | 'pong';
}
```

#### 3.3.2 REST API

**1. 创建任务**

```
POST /api/grok-video/generate
```

```typescript
// 请求
interface GenerateRequest {
  prompt: string;
  images?: string[];
  ratio?: '16:9' | '9:16' | '1:1';
  resolution?: '720p' | '1080p';
  duration?: number;
}

// 响应
interface GenerateResponse {
  task_id: string;
  status: 'pending';
  estimated_time?: number;
}
```

**2. 查询任务状态**

```
GET /api/grok-video/status/{task_id}
```

```typescript
interface StatusResponse {
  task_id: string;
  status: 'pending' | 'processing' | 'success' | 'failed';
  video_url?: string;
  error?: string;
}
```

**3. 获取 COS 上传凭证**

```
POST /api/cos-credential
```

```typescript
// 请求
interface CredentialRequest {
  task_id: string;
}

// 响应
interface CredentialResponse {
  secretId: string;
  secretKey: string;
  sessionToken: string;
  startTime: number;
  expiredTime: number;
  bucket: string;
  region: string;
}
```

### 3.4 任务队列设计

```
┌─────────────────────────────────────────────────────────────────┐
│                        任务队列                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐     │
│  │ Task 1  │ →  │ Task 2  │ →  │ Task 3  │ →  │ Task 4  │     │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘     │
│       │                                                        │
│       ↓                                                        │
│  ┌─────────────────┐                                          │
│  │ 插件处理器      │                                          │
│  │ (并发数: 1)     │                                          │
│  └─────────────────┘                                          │
│                                                                 │
│  规则：                                                         │
│  1. 一个插件实例一次只处理一个任务                               │
│  2. 任务按先入先出顺序执行                                       │
│  3. 超时任务自动取消并退款                                       │
│  4. 失败任务可配置重试次数                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**后端伪代码：**

```python
# 任务队列
task_queue = asyncio.Queue()
current_task = None
plugin_connected = asyncio.Event()

async def handle_plugin(websocket):
    """处理插件连接"""
    global current_task

    plugin_connected.set()

    try:
        async for message in websocket:
            data = json.loads(message)

            if data['type'] == 'register':
                print('插件已连接')

            elif data['type'] == 'result':
                # 处理结果
                await handle_task_result(data)
                current_task = None

                # 处理下一个任务
                await process_next_task(websocket)

    finally:
        plugin_connected.clear()

async def process_next_task(websocket):
    """处理下一个任务"""
    global current_task

    if current_task:
        return  # 有任务在执行

    try:
        task = task_queue.get_nowait()
        current_task = task

        # 发送任务给插件
        await websocket.send(json.dumps({
            'type': 'task',
            **task
        }))

        # 设置超时
        asyncio.create_task(watch_timeout(task['task_id']))

    except asyncio.QueueEmpty:
        pass

async def create_task(user_id, task_data):
    """创建任务"""
    task_id = str(uuid.uuid4())

    # 预扣积分
    await reserve_points(user_id, cost=10)

    # 加入队列
    task = {
        'task_id': task_id,
        'user_id': user_id,
        **task_data,
        'created_at': time.time()
    }
    await task_queue.put(task)

    # 如果插件空闲，立即处理
    if plugin_connected.is_set() and not current_task:
        # 触发处理
        pass

    return task_id

async def watch_timeout(task_id, timeout=300):
    """超时监控"""
    await asyncio.sleep(timeout)

    if current_task and current_task['task_id'] == task_id:
        # 超时，取消任务
        await refund_points(task_id, reason='timeout')
        current_task = None
```

---

## 四、安全设计

### 4.1 WebSocket 认证

```
┌─────────────────────────────────────────────────────────────────┐
│                      认证流程                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 插件启动时，生成唯一 client_id                               │
│                                                                 │
│  2. 连接 WebSocket 时，携带 token                               │
│     wss://backend/ws/grok-plugin?client_id=xxx&token=yyy       │
│                                                                 │
│  3. 后端验证 token（配置文件中的预共享密钥）                       │
│                                                                 │
│  4. 验证通过后，绑定 client_id 与连接                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**后端验证：**

```python
async def verify_plugin_token(client_id: str, token: str) -> bool:
    """验证插件 token"""
    expected_token = settings.PLUGIN_TOKENS.get(client_id)
    return expected_token and token == expected_token
```

### 4.2 COS 上传安全

```
┌─────────────────────────────────────────────────────────────────┐
│                    COS 临时凭证                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  后端生成 STS 临时凭证：                                         │
│                                                                 │
│  {                                                              │
│    "secretId": "临时ID",                                        │
│    "secretKey": "临时Key",                                      │
│    "sessionToken": "会话令牌",                                   │
│    "expiredTime": 3600,     // 1小时过期                        │
│    "policy": {              // 限制权限                         │
│      "version": "2.0",                                          │
│      "statement": [{                                            │
│        "effect": "allow",                                       │
│        "action": ["putObject"],                                 │
│        "resource": ["grok-videos/{task_id}.mp4"]               │
│      }]                                                         │
│    }                                                            │
│  }                                                              │
│                                                                 │
│  特点：                                                         │
│  - 只能上传指定路径                                              │
│  - 1小时后自动失效                                               │
│  - 无法删除或读取其他文件                                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 任务校验

```python
async def verify_task(task_id: str, user_id: str) -> bool:
    """验证任务归属"""
    task = await get_task(task_id)
    return task and task['user_id'] == user_id
```

---

## 五、错误处理

### 5.1 错误类型

| 错误类型 | 错误码 | 处理方式 |
|----------|--------|----------|
| 插件未连接 | PLUGIN_DISCONNECTED | 返回错误，提示稍后重试 |
| 任务超时 | TASK_TIMEOUT | 自动退款 |
| Grok 页面错误 | GROK_ERROR | 退款，记录日志 |
| 视频下载失败 | DOWNLOAD_FAILED | 重试3次，失败则退款 |
| COS上传失败 | UPLOAD_FAILED | 重试3次，失败则退款 |
| DOM元素未找到 | ELEMENT_NOT_FOUND | 可能页面改版，告警 |

### 5.2 重试策略

```python
class RetryPolicy:
    max_retries = 3
    retry_delay = [1, 3, 5]  # 秒

    async def execute_with_retry(self, func, *args):
        for attempt in range(self.max_retries):
            try:
                return await func(*args)
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                await asyncio.sleep(self.retry_delay[attempt])
```

### 5.3 告警机制

```python
async def send_alert(level: str, message: str):
    """发送告警"""
    # 企业微信/钉钉/邮件
    await notify({
        'level': level,  # error, warning
        'message': message,
        'timestamp': time.time()
    })

# 触发告警的场景
# 1. 插件断连超过5分钟
# 2. 连续3个任务失败
# 3. DOM元素未找到（可能页面改版）
```

---

## 六、监控与运维

### 6.1 监控指标

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| `plugin_status` | 插件连接状态 | 断连超过5分钟 |
| `queue_length` | 队列长度 | 超过10 |
| `task_success_rate` | 任务成功率 | 低于90% |
| `avg_task_duration` | 平均任务耗时 | 超过5分钟 |
| `video_upload_size` | 视频上传大小 | - |

### 6.2 日志规范

```javascript
// 插件日志
console.log('[GrokOperator] 任务开始:', taskId);
console.log('[GrokOperator] 提示词已填入');
console.log('[GrokOperator] 视频下载完成, 大小:', size);
console.error('[GrokOperator] 任务失败:', error);
```

```python
# 后端日志
logger.info(f"任务创建: task_id={task_id}, user_id={user_id}")
logger.info(f"任务完成: task_id={task_id}, duration={duration}s")
logger.error(f"任务失败: task_id={task_id}, error={error}")
```

### 6.3 运维脚本

**检查插件状态：**

```bash
curl https://backend/api/grok-plugin/status
```

**手动重置队列：**

```bash
curl -X POST https://backend/api/admin/grok-plugin/reset-queue \
  -H "Authorization: Bearer ADMIN_TOKEN"
```

---

## 七、风险与对策

### 7.1 风险矩阵

| 风险 | 可能性 | 影响 | 对策 |
|------|--------|------|------|
| Grok 页面改版 | 高 | 高 | 多重选择器 + 快速响应更新 |
| Grok 封号 | 中 | 高 | 控制频率 + 多账号轮换 |
| 验证码弹出 | 中 | 中 | 检测 + 告警 + 人工处理 |
| 浏览器崩溃 | 低 | 高 | 自动重启 + 任务恢复 |
| WebSocket 断连 | 中 | 中 | 自动重连 + 任务队列持久化 |

### 7.2 应急预案

**场景1：插件断连**

```
检测到断连 → 告警 → 暂停接收新任务 → 等待重连或人工介入
```

**场景2：Grok 页面改版**

```
DOM操作失败 → 告警 → 开发者分析新页面 → 更新选择器 → 发布新版本
```

**场景3：账号被封**

```
连续失败 → 检测异常 → 告警 → 切换备用账号（如有）
```

---

## 八、后续优化

### 8.1 短期优化

- [ ] 支持多插件实例（多账号并行）
- [ ] 视频预览图生成
- [ ] 任务进度实时推送

### 8.2 长期优化

- [ ] 自动检测 Grok 页面改版
- [ ] 验证码自动识别（OCR）
- [ ] 多平台支持（Runway、Pika等）

---

## 九、附录

### 9.1 Grok 页面 DOM 选择器（待验证）

```javascript
// 需要实际分析 Grok 页面后确定
const SELECTORS = {
  // 输入框
  promptInput: 'textarea[placeholder*="Ask"]',

  // 图片上传
  imageUpload: 'input[type="file"]',
  imageUploadButton: 'button[aria-label*="upload"]',

  // 参数
  ratio_16_9: 'button[data-ratio="16:9"]',
  ratio_9_16: 'button[data-ratio="9:16"]',
  ratio_1_1: 'button[data-ratio="1:1"]',

  // 生成按钮
  generateButton: 'button[type="submit"]',

  // 视频
  videoElement: 'video[src*="generated"]'
};
```

### 9.2 时间估算

| 阶段 | 工作内容 | 预计时间 |
|------|----------|----------|
| 阶段1 | 分析 Grok 页面 DOM | 0.5 天 |
| 阶段2 | 开发插件基础框架 | 1 天 |
| 阶段3 | 实现 DOM 操作逻辑 | 1 天 |
| 阶段4 | 实现视频下载上传 | 0.5 天 |
| 阶段5 | 后端 WebSocket API | 1 天 |
| 阶段6 | 联调测试 | 1 天 |
| 阶段7 | 部署上线 | 0.5 天 |
| **总计** | | **5.5 天** |

---

## 十、总结

本方案通过 Chrome 浏览器插件实现 Grok 视频生成的自动化，核心优势：

1. **成本低** - 后端几乎零带宽消耗
2. **可控性强** - 完全控制操作流程
3. **可扩展** - 后续可支持更多平台

主要风险：

1. **Grok 页面改版** - 需要及时更新选择器
2. **账号风控** - 需要控制使用频率
3. **单点故障** - 单插件单账号的并发限制

建议：

1. 先开发 MVP 版本验证可行性
2. 建立监控告警机制
3. 预留多账号扩展能力