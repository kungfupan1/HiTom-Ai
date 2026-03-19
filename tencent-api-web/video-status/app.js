/**
 * 视频状态查询 API - 腾讯云 Web 函数 (GET请求)
 */
const express = require('express');
const cors = require('cors');
const axios = require('axios');

process.on('uncaughtException', (err) => console.error('=== 致命错误拦截 ===', err));
process.on('unhandledRejection', (reason) => console.error('=== 致命错误拦截 ===', reason));

const app = express();
app.use(cors());

const T8STAR_API_KEY = process.env.T8STAR_API_KEY || '';

app.get('/', (req, res) => res.json({ status: 'ok', service: 'video-status' }));

// 注意这是 GET 请求，参数从 req.query 获取
app.get('/api/ai/video-status', async (req, res) => {
  console.log(`[GET /api/ai/video-status] 收到查询请求: task_id=${req.query.task_id}`);
  try {
    const { task_id, model } = req.query;

    if (!task_id) {
      return res.status(400).json({ status: 'error', message: '缺少 task_id 参数' });
    }
    if (!T8STAR_API_KEY) {
      return res.status(500).json({ status: 'error', message: '请配置 T8STAR_API_KEY' });
    }

    const response = await axios.get(
      `https://ai.t8star.cn/v2/videos/generations/${task_id}`,
      {
        headers: { 'Authorization': `Bearer ${T8STAR_API_KEY}` },
        timeout: 25000
      }
    );

    const result = response.data;
    const apiStatus = result.status || result.data?.status;
    const videoUrl = result.data?.output || result.video_url || result.data?.video_url;
    const progress = result.progress || result.data?.progress || '0%';

    // 状态映射逻辑归一化
    let normalizedStatus = 'pending';
    const s = String(apiStatus).toLowerCase();
    if (s === 'success' || s === 'completed' || s === 'succeeded') normalizedStatus = 'success';
    else if (s === 'failed' || s === 'error') normalizedStatus = 'failed';
    else if (s === 'processing' || s === 'running' || s === 'generating') normalizedStatus = 'processing';

    console.log(`[video-status] 查询成功, Status: ${normalizedStatus}, Progress: ${progress}`);

    res.json({
      status: normalizedStatus,
      task_id: task_id,
      video_url: videoUrl || null,
      progress: progress,
      raw_status: apiStatus
    });

  } catch (err) {
    console.error('[video-status] 请求报错:', err.message);
    if (err.response) {
      return res.status(err.response.status || 500).json({
        status: 'error',
        message: err.response.data?.error?.message || err.response.data?.message || '查询失败',
        detail: err.response.data
      });
    }
    res.status(500).json({ status: 'error', message: err.message || '服务器错误' });
  }
});

const port = 9000;
const server = app.listen(port, '0.0.0.0', () => console.log(`video-status running on port ${port}`));
server.on('error', (err) => console.error(err));