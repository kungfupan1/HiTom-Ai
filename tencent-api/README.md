# 腾讯云函数部署指南

## 前提条件

1. 注册腾讯云账号：https://cloud.tencent.com
2. 开通云函数 SCF 服务
3. 开通 API 网关服务

## 部署方式一：控制台上传（推荐新手）

### 1. 安装依赖
```bash
cd tencent-api
npm install
```

### 2. 打包代码
将以下文件打包成 zip：
- functions/ 文件夹
- lib/ 文件夹
- node_modules/ 文件夹（安装依赖后生成）

### 3. 创建函数
1. 登录腾讯云控制台：https://console.cloud.tencent.com/scf
2. 点击「新建」→「从头创建」
3. 填写基本信息：
   - 函数名称：`analyze-images`
   - 运行环境：Node.js 16.13
   - 提交方法：本地上传 zip 包
   - 执行方法：`index.main_handler`
   - 超时时间：120 秒
   - 内存：256 MB
4. 上传 zip 包
5. 高级配置 → 环境变量：
   - `MODELSCOPE_API_KEY` = `ms-904194b2-24f4-40fa-994a-d23694510f21`
6. 点击「完成」

### 4. 创建其他函数
重复上述步骤，创建：
- `generate-video`（超时60秒，环境变量：T8STAR_API_KEY）
- `video-status`（超时30秒，环境变量：T8STAR_API_KEY）
- `generate-image`（超时60秒，环境变量：T8STAR_API_KEY）

### 5. 配置 API 网关
1. 进入 API 网关控制台：https://console.cloud.tencent.com/apigateway
2. 创建服务，名称：`hi-tom-ai`
3. 创建 API：
   - 路径：`/api/ai/analyze-images`，方法：POST，后端：云函数 `analyze-images`
   - 路径：`/api/ai/generate-video`，方法：POST，后端：云函数 `generate-video`
   - 路径：`/api/ai/video-status`，方法：GET，后端：云函数 `video-status`
   - 路径：`/api/ai/generate-image`，方法：POST，后端：云函数 `generate-image`
4. 发布服务到「发布」环境
5. 获取访问地址

## 部署方式二：使用 Serverless Framework CLI

### 1. 安装 Serverless Framework
```bash
npm install -g serverless
```

### 2. 配置凭证
```bash
serverless config credentials --provider tencent --secret_id YOUR_SECRET_ID --secret_key YOUR_SECRET_KEY
```

### 3. 部署
```bash
cd tencent-api
serverless deploy
```

## 更新前端配置

部署完成后，将 API 网关地址配置到：
- 后端数据库的系统配置表
- 或直接修改 user-web/src/api/index.js 中的 VERCEL_URL

## 费用说明

腾讯云函数免费额度：
- 每月 100 万次调用
- 每月 40 万 GB-秒 资源使用量

对于测试和小规模使用完全免费。