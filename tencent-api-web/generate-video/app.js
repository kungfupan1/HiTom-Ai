/**
 * 视频生成 API - 腾讯云 Web 函数
 */
const express = require('express');
const cors = require('cors');
const axios = require('axios');

process.on('uncaughtException', (err) => console.error('=== 致命错误拦截 ===', err));
process.on('unhandledRejection', (reason) => console.error('=== 致命错误拦截 ===', reason));

const app = express();
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

const T8STAR_API_KEY = process.env.T8STAR_API_KEY || '';

app.get('/', (req, res) => res.json({ status: 'ok', service: 'generate-video' }));

app.post('/api/ai/generate-video', async (req, res) => {
  console.log('[POST /api/ai/generate-video] 收到请求...');
  try {
    const { model, prompt, ratio, duration, resolution, images } = req.body;

    if (!model || !prompt) {
      return res.status(400).json({ status: 'error', message: '缺少必要参数：model 或 prompt' });
    }
    if (!T8STAR_API_KEY) {
      return res.status(500).json({ status: 'error', message: '请配置 T8STAR_API_KEY' });
    }

    // 适配不同模型的参数规则
    const payload = { model, prompt };

    // 默认比例
    const aspectRatio = ratio || '16:9';
    if (model === 'grok-video-3') {
      payload.ratio = aspectRatio;
    } else {
      payload.aspect_ratio = aspectRatio; // sora 系列用 aspect_ratio
      payload.private = true;
    }

    // 时长处理
    const dur = duration || 5;
    payload.duration = (model === 'grok-video-3') ? parseInt(dur, 10) : String(dur);

    // 分辨率与首图
    payload.hd = (resolution === '1080P');
    if (images && images.length > 0) {
      payload.images = [images[0]];
    }

    console.log(`[generate-video] 提交任务, 模型: ${model}, 载荷:`, JSON.stringify(payload));

    const response = await axios.post(
      'https://ai.t8star.cn/v2/videos/generations',
      payload,
      {
        headers: { 'Authorization': `Bearer ${T8STAR_API_KEY}`, 'Content-Type': 'application/json' },
        timeout: 55000
      }
    );

    console.log('[generate-video] 任务提交成功！Task ID:', response.data?.data?.task_id || response.data?.task_id);

    // 返回标准格式，保持和原来一样
    res.json({
      status: 'success',
      task_id: response.data.data?.task_id || response.data.task_id,
      detail: response.data
    });

  } catch (err) {
    console.error('[generate-video] 请求报错:', err.message);
    if (err.response) {
      return res.status(err.response.status || 500).json({
        status: 'error',
        message: err.response.data?.error?.message || err.response.data?.message || 'API 请求失败',
        detail: err.response.data
      });
    }
    res.status(500).json({ status: 'error', message: err.message || '服务器错误' });
  }
});

const port = 9000;
const server = app.listen(port, '0.0.0.0', () => console.log(`generate-video running on port ${port}`));
server.on('error', (err) => console.error(err));