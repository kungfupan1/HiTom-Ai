# Hi-Tom-AI

AI 电商内容生成平台 - 配置化重构版本

## 功能特性

- 🎬 **视频生成**：支持 Sora-2、Grok Video 3 等模型
- 🖼️ **图片生成**：支持多种分辨率和比例
- 💰 **积分系统**：预扣机制防止重复扣费
- ⚙️ **配置化**：模型、计费规则后台可配
- 🔐 **权限分离**：用户端/管理端分离

## 项目结构

```
hi-tom-ai/
├── backend/                    # FastAPI 后端
│   ├── main.py                 # 主应用
│   ├── models.py               # 数据库模型
│   ├── crud.py                 # 业务逻辑
│   ├── schemas.py              # 数据校验
│   └── init_db.py              # 初始化脚本
├── vercel-api/                 # Vercel Functions（AI 代理）
│   ├── api/ai/                 # AI 接口
│   └── lib/provider-mapper.js  # 参数映射引擎
├── user-web/                   # 用户端前端（Vue 3）
├── admin-web/                  # 管理端前端（Vue 3）
├── CLAUDE.md                   # 开发指南
├── DEPLOY.md                   # 部署文档
└── feature_list.json           # 功能清单
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

## 快速开始

### 1. 后端

```bash
cd backend
pip install -r requirements.txt
python init_db.py              # 初始化数据库
uvicorn main:app --reload      # 启动服务
```

### 2. 前端

```bash
# 用户端
cd user-web && npm install && npm run dev

# 管理端
cd admin-web && npm install && npm run dev
```

### 3. Vercel Functions

```bash
cd vercel-api
npm install
vercel                          # 部署到 Vercel
```

## 默认账号

- 管理员：`admin` / `admin123`
- 注册赠送：10 积分

## 环境变量

```env
# Vercel 环境变量
T8STAR_API_KEY=sk-xxx
MODELSCOPE_API_KEY=sk-xxx
BACKEND_URL=https://your-server.com
```

## 文档

- [开发指南](./CLAUDE.md)
- [部署文档](./DEPLOY.md)

## 开发状态

✅ 全部 20 项功能已完成，参见 `feature_list.json`