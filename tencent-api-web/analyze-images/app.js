/**
 * 看图生成文案 API - 腾讯云 Web 函数 (终极防崩溃版)
 */
const express = require('express');
const cors = require('cors');
const axios = require('axios');

// 1. 全局拦截致命异常，防止 Node 进程静默崩溃导致 502
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

const MODELSCOPE_API_KEY = process.env.MODELSCOPE_API_KEY || '';

// 健康检查接口 - 用于测试服务器是否存活
app.get('/', (req, res) => {
  console.log('[GET /] 收到健康检查请求，服务器存活！');
  res.json({ status: 'ok', message: 'Web function is perfectly alive!' });
});

// 主接口
app.post('/api/ai/analyze-images', async (req, res) => {
  console.log('[POST /api/ai/analyze-images] 收到请求，准备处理...');
  try {
    const { images, product_type, design_style, target_lang, target_num } = req.body;

    if (!images || images.length === 0) {
      console.log('拦截：缺少图片数据');
      return res.status(400).json({ status: 'error', message: '缺少图片数据' });
    }

    if (!MODELSCOPE_API_KEY) {
      console.log('拦截：未配置 MODELSCOPE_API_KEY');
      return res.status(500).json({ status: 'error', message: '请在云函数环境变量中配置 MODELSCOPE_API_KEY' });
    }

    const targetLangStr = target_lang || 'Chinese';
    const targetNumInt = target_num || 1;
    const productType = product_type || '通用产品';
    const designStyle = design_style || '现代简约';

    const formatParts = [];
    for (let i = 1; i <= targetNumInt; i++) {
      formatParts.push(`Set ${i}:\nMain Title: ...\nSubtitle: ...`);
    }

    const promptText = `
[Role] Senior E-commerce Copywriter specialized in **${targetLangStr}**.
[Input Info]
- Product Category: ${productType}
- Desired Style: ${designStyle}
- **TARGET LANGUAGE: ${targetLangStr}**
[Task]
Analyze these product images. Write catchy 'Main Title' and 'Subtitle'.
[Requirement]
Generate exactly **${targetNumInt} distinct sets**.
[Format]:
${formatParts.join('\n\n')}
`;

    const contentList = [{ type: 'text', text: promptText }];
    const validImages = images.filter(img => img).slice(0, 3);
    for (const imgBase64 of validImages) {
      let imgUrl = imgBase64;
      if (!imgBase64.startsWith('data:image')) {
        imgUrl = `data:image/jpeg;base64,${imgBase64}`;
      }
      contentList.push({ type: 'image_url', image_url: { url: imgUrl } });
    }

    const payload = {
      model: 'Qwen/Qwen3-VL-30B-A3B-Instruct',
      messages: [{ role: 'user', content: contentList }],
      max_tokens: 1500,
      temperature: 0.7
    };

    console.log('[analyze-images] 参数组装完毕，开始调用 ModelScope API...');

    const response = await axios.post(
      'https://api-inference.modelscope.cn/v1/chat/completions',
      payload,
      {
        headers: {
          'Authorization': `Bearer ${MODELSCOPE_API_KEY}`,
          'Content-Type': 'application/json'
        },
        timeout: 110000
      }
    );

    console.log('[analyze-images] API 调用成功！');
    let content = response.data.choices[0].message.content.trim();
    content = content.replace(/\*\*/g, '').replace(/##/g, '');

    res.json({ status: 'success', content });

  } catch (err) {
    console.error('[analyze-images] 请求处理过程中发生报错:', err.message);
    if (err.response) {
      console.error('ModelScope API 返回了详细报错:', JSON.stringify(err.response.data));
      return res.status(err.response.status || 500).json({
        status: 'error',
        message: err.response.data?.error?.message || 'API 请求失败',
        detail: err.response.data
      });
    }
    res.status(500).json({ status: 'error', message: err.message || '服务器错误' });
  }
});

const port = 9000;
const server = app.listen(port, '0.0.0.0', () => {
  console.log(`Web function is successfully listening on port ${port} at 0.0.0.0`);
});

// 2. 监听并打印底层的服务器运行错误（如端口被占用）
server.on('error', (err) => {
  console.error('=== 底层 Server 启动失败 ===', err);
});

// 3. 【极度关键】代码结束！绝对不要写 module.exports = app