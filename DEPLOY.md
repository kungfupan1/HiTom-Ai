# Hi-Tom-AI 部署指南

## 目录结构

```
hi-tom-ai/
├── backend/
│   ├── Dockerfile          # 后端 Docker 镜像配置
│   ├── .dockerignore       # Docker 忽略文件
│   ├── hi_tom_ai.db        # SQLite 数据库
│   ├── uploads/            # 上传文件目录
│   └── ...其他后端代码
├── user-web/
│   └── dist/               # 用户端构建产物 (需要先执行 npm run build)
├── admin-web/
│   └── dist/               # 管理后台构建产物 (需要先执行 npm run build)
├── docker-compose.yml      # Docker Compose 配置
└── nginx.conf              # Nginx 配置
```

## 部署步骤

### 1. 构建前端 (本地执行)

```bash
# 用户端
cd user-web
npm install
npm run build

# 管理后台
cd ../admin-web
npm install
npm run build
```

### 2. 上传到服务器

```bash
# 将整个项目上传到服务器
scp -r hi-tom-ai/ user@your-server:/home/user/
```

### 3. 服务器上启动

```bash
cd /home/user/hi-tom-ai

# 启动服务
docker-compose up -d --build

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 4. 访问地址

- **用户端**: http://your-server-ip 或 http://your-domain.com
- **管理后台**: http://your-server-ip:8081

## 修改域名

编辑 nginx.conf，将 server_name localhost; 改为你的域名

## 常用命令

```bash
# 重启服务
docker-compose restart

# 重新构建并启动
docker-compose up -d --build

# 查看后端日志
docker logs hitom_backend -f

# 查看 Nginx 日志
docker logs hitom_nginx -f

# 进入后端容器
docker exec -it hitom_backend /bin/bash
```

## 注意事项

1. **数据库备份**: 定期备份 backend/hi_tom_ai.db 文件
2. **上传文件**: backend/uploads/ 目录存放用户上传的文件，请定期清理
3. **端口冲突**: 如果 80 或 8081 端口被占用，修改 docker-compose.yml 中的端口映射
4. **HTTPS**: 建议使用 Nginx + Let's Encrypt 配置 HTTPS
