# Hi-Tom-AI

AI 电商内容生成平台 - 配置化重构版本

## 项目结构

```
hi-tom-ai/
├── backend/                    # FastAPI 后端（精简版）
│   ├── main.py
│   ├── models.py
│   ├── crud.py
│   └── ...
├── vercel-api/                 # Vercel Functions（AI 代理）
│   ├── api/
│   │   ├── ai/
│   │   │   ├── generate-image.js
│   │   │   ├── generate-video.js
│   │   │   └── video-status.js
│   │   └── ...
│   ├── lib/
│   │   └── provider-mapper.js  # 参数映射引擎
│   ├── vercel.json
│   └── package.json
├── user-web/                   # 用户端前端（Vue 3）
├── admin-web/                  # 管理端前端（Vue 3）
├── feature_list.json           # 功能列表
├── claude-progress.txt         # 进度追踪
└── README.md
```

## 架构说明

```
用户浏览器
    │
    ├── AI 请求 ──────────────→ Vercel Functions ──→ AI 服务商
    │   (生图/生视频)              (存 API Key)        (T8Star等)
    │
    └── 业务请求 ──────────────→ 你的服务器
        (登录/积分/日志)            (FastAPI + SQLite)
```

## 开发进度

参见 `feature_list.json` 和 `claude-progress.txt`

## 快速开始

```bash
# 安装依赖
cd backend && pip install -r requirements.txt
cd vercel-api && npm install

# 本地开发
cd backend && uvicorn main:app --reload
cd vercel-api && vercel dev

# 部署
vercel --prod
```

## 环境变量

```env
# Vercel 环境变量
T8STAR_API_KEY=sk-xxx
MODELSCOPE_API_KEY=sk-xxx
BACKEND_URL=https://your-server.com
```