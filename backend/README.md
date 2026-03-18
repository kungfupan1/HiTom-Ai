# Hi-Tom-AI Backend

FastAPI 后端服务 - 精简版

## 功能
- 用户认证与授权
- 积分管理（预扣、确认、退还）
- AI 模型配置管理
- 计费规则配置
- API 日志记录

## 运行

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## API 文档

启动后访问: http://localhost:8000/docs