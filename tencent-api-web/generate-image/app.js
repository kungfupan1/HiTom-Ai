/**
 * 图片生成 API - 腾讯云 Web 函数
 */
const express = require('express');
const cors = require('cors');
const axios = require('axios');

process.on('uncaughtException', (err) => {
  console.error('=== 致命错误拦截: Uncaught Exception ===', err);
});
process.on('unhandledRejection', (reason, promise) => {
  console.error('=== 致命错误拦截: Unhandled Rejection ===', reason);
});

const app = express();
app.use(cors());
app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

const T8STAR_API_KEY = process.env.T8STAR_API_KEY || '';

app.get('/', (req, res) => {
  res.json({ status: 'ok', service: 'generate-image' });
});

app.post('/api/ai/generate-image', async (req, res) => {
  console.log('[POST /api/ai/generate-image] 收到请求...');
  try {
    const { model, prompt, size, images } = req.body;

    if (!model || !prompt) {
      return res.status(400).json({ status: 'error', message: '缺少必要参数：model 或 prompt' });
    }
    if (!T8STAR_API_KEY) {
      return res.status(500).json({ status: 'error', message: '请在云函数环境变量中配置 T8STAR_API_KEY' });
    }

    const payload = {
      model: model,
      prompt: prompt,
      response_format: 'url'
    };
    if (size) payload.size = size;
    if (images && images.length > 0) payload.image = images;

    console.log(`[generate-image] 调用模型: ${model}, 准备发送请求...`);

    const response = await axios.post(
      'https://ai.t8star.cn/v1/images/generations',
      payload,
      {
        headers: {
          'Authorization': `Bearer ${T8STAR_API_KEY}`,
          'Content-Type': 'application/json'
        },
        timeout: 55000 // 留出一点余量给云函数
      }
    );

    console.log('[generate-image] API 调用成功！');
    const resultImages = response.data.data?.map(item => item.url) || [];

    res.json({ status: 'success', images: resultImages });

  } catch (err) {
    console.error('[generate-image] 请求处理报错:', err.message);
    if (err.response) {
      console.error('T8Star API 详细报错:', JSON.stringify(err.response.data));
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
const server = app.listen(port, '0.0.0.0', () => {
  console.log(`generate-image is listening on port ${port} at 0.0.0.0`);
});
server.on('error', (err) => console.error('=== Server 启动失败 ===', err));