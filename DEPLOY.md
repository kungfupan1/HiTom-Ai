# 部署指南

## 1. 后端部署

### 1.1 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 1.2 初始化数据库

```bash
python init_db.py
```

这会创建 SQLite 数据库并添加默认模型和管理员账号。

### 1.3 启动服务

**开发环境：**
```bash
uvicorn main:app --reload --port 8000
```

**生产环境：**
```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

### 1.4 默认账号

- 管理员：`admin` / `admin123`
- 注册赠送积分：10

---

## 2. Vercel Functions 部署

### 2.1 安装 Vercel CLI

```bash
npm install -g vercel
```

### 2.2 配置环境变量

在 Vercel Dashboard 或通过 CLI 设置：

```bash
vercel env add T8STAR_API_KEY
# 输入你的 API Key: sk-xxx

vercel env add MODELSCOPE_API_KEY
# 输入你的 API Key: sk-xxx

vercel env add BACKEND_URL
# 输入后端地址: https://your-backend.com
```

### 2.3 部署

```bash
cd vercel-api
npm install
vercel --prod
```

部署后会得到一个 URL，如 `https://hi-tom-ai.vercel.app`

---

## 3. 前端部署

### 3.1 用户端 (user-web)

```bash
cd user-web
npm install
npm run build
```

构建产物在 `dist/` 目录，部署到任意静态服务器。

### 3.2 管理端 (admin-web)

```bash
cd admin-web
npm install
npm run build
```

---

## 4. 环境变量汇总

### Vercel Functions

| 变量名 | 说明 | 示例 |
|--------|------|------|
| T8STAR_API_KEY | T8Star API 密钥 | sk-xxx |
| MODELSCOPE_API_KEY | ModelScope API 密钥 | sk-xxx |
| BACKEND_URL | 后端服务地址 | https://api.example.com |

### 后端系统配置 (通过管理后台设置)

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| signup_bonus | 注册赠送积分 | 10 |
| image_base_price | 图片生成基础价格 | 2 |
| vercel_url | Vercel Functions 地址 | - |
| pricing_description | 费用说明文案 | - |

---

## 5. API 端点

### 后端 API (FastAPI)

| 端点 | 方法 | 说明 |
|------|------|------|
| `/auth/register` | POST | 用户注册 |
| `/auth/token` | POST | 用户登录 |
| `/users/me` | GET | 获取当前用户 |
| `/api/models` | GET | 获取模型列表 |
| `/api/models/{id}` | GET | 获取模型详情 |
| `/api/calculate-cost` | POST | 计算费用 |
| `/api/points/reserve` | POST | 预扣积分 |
| `/api/points/confirm` | POST | 确认扣费 |
| `/api/points/refund` | POST | 退还积分 |
| `/admin/models` | GET/POST/PUT/DELETE | 模型管理 |
| `/admin/config` | GET/PUT | 系统配置 |

### Vercel Functions

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/ai/generate-image` | POST | 图片生成代理 |
| `/api/ai/generate-video` | POST | 视频生成代理 |
| `/api/ai/video-status` | GET | 视频状态查询 |

---

## 6. 常见问题

### Q: 如何添加新的 AI 模型？

1. 登录管理后台
2. 进入「模型管理」→「添加模型」
3. 填写模型 ID、API 配置、参数映射
4. 在「计费配置」中设置价格规则

### Q: 如何修改积分规则？

1. 登录管理后台
2. 进入「系统配置」
3. 修改注册赠送、基础价格等配置

### Q: 如何查看 API 调用日志？

API 调用日志存储在 `api_logs` 表中，可通过数据库工具查询。

---

## 7. 架构图

```
┌─────────────┐     AI请求      ┌─────────────────┐     API调用     ┌─────────────┐
│  用户浏览器  │ ──────────────→ │ Vercel Functions │ ──────────────→ │  AI 服务商   │
│  (user-web) │                 │  (存 API Key)    │                 │  (T8Star)   │
└─────────────┘                 └─────────────────┘                 └─────────────┘
       │
       │ 业务请求
       ↓
┌─────────────┐                 ┌─────────────────┐
│   FastAPI   │ ◄───────────────│     SQLite      │
│   Backend   │                 │    Database     │
└─────────────┘                 └─────────────────┘
```

---

## 8. 安全建议

1. **修改默认管理员密码**
2. **限制 CORS 来源**（生产环境不要用 `*`）
3. **定期备份数据库**
4. **API Key 定期轮换**
5. **使用 HTTPS**