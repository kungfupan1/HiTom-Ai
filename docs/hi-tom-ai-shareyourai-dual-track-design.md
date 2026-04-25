# Hi-Tom-AI 双轨制 AI 服务对接设计文档

> 版本：v1.0
> 日期：2026-03-31
> 模式：双轨制（云函数代理 + 后端直接调用）

---

## 一、设计概述

### 1.1 背景

Hi-Tom-AI 当前使用云函数代理模式调用 T8Star/ModelScope API。本次新增 ShareYourAi 服务对接，采用后端直接调用模式，形成双轨制架构。

### 1.2 双轨制设计原则

| 服务商 | 调用方式 | 原因 |
|-------|---------|------|
| T8Star | 云函数代理（保留） | 已稳定运行，不改动 |
| ModelScope | 云函数代理（保留） | 已稳定运行，不改动 |
| ShareYourAi | 后端直接调用（新增） | 需要用户验证+积分扣费，后端统一处理更合理 |

### 1.3 架构对比

**原有架构（云函数代理）**：
```
前端 → 腾讯云函数 → AI服务商
         ↑
      占位符替换为真实Key
      无用户验证
```

**新增架构（后端直接调用）**：
```
前端 → 后端（验证+扣费+调用）→ ShareYourAi → 结果存云存储
         ↑
      用户Token验证 ✓
      积分预扣 ✓
      API Key 在后端 ✓
```

### 1.4 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Hi-Tom-AI 前端                                     │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      VideoTool.vue / ImageTool.vue                   │    │
│  │                                                                      │    │
│  │   用户选择模型 → 查询模型配置 → 判断 use_cloud_function               │    │
│  │                                                                      │    │
│  │   ┌─────────────────┐              ┌─────────────────┐              │    │
│  │   │ use_cloud_function│            │use_cloud_function│              │    │
│  │   │     = true       │              │     = false     │              │    │
│  │   └─────────────────┘              └─────────────────┘              │    │
│  │          │                                   │                      │    │
│  │          ▼                                   ▼                      │    │
│  │   ┌─────────────────┐              ┌─────────────────┐              │    │
│  │   │  云函数代理路径   │              │  后端直接路径    │              │    │
│  │   │  (原有逻辑不变)  │              │  (新增逻辑)     │              │    │
│  │   └─────────────────┘              └─────────────────┘              │    │
│  │                                                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
         │                                        │
         │                                        │
         ▼                                        ▼
┌─────────────────────┐              ┌─────────────────────────────────────┐
│   腾讯云函数         │              │           Hi-Tom-AI 后端             │
│                     │              │                                      │
│  - 占位符替换       │              │  ┌─────────────────────────────┐    │
│  - 转发请求         │              │  │    /api/tasks/submit        │    │
│  - 无用户验证       │              │  │    提交任务 + 预扣积分        │    │
│                     │              │  └─────────────────────────────┘    │
└─────────────────────┘              │  ┌─────────────────────────────┐    │
         │                           │  │    /api/tasks/{id}/status   │    │
         │                           │  │    查询状态（轻量轮询）       │    │
         ▼                           │  └─────────────────────────────┘    │
┌─────────────────────┐              │  ┌─────────────────────────────┐    │
│   T8Star/ModelScope │              │  │    /api/tasks/{id}/confirm  │    │
│                     │              │  │    确认扣费                  │    │
└─────────────────────┘              │  └─────────────────────────────┘    │
                                     │  ┌─────────────────────────────┐    │
                                     │  │    /api/tasks/{id}/refund   │    │
                                     │  │    退还积分                  │    │
                                     │  └─────────────────────────────┘    │
                                     │                                      │
                                     │  ShareYourAi API Key 存储在后端      │
                                     │  用户Token验证 ✓                     │
                                     │  积分预扣/确认/退款 ✓                │
                                     │                                      │
                                     └─────────────────────────────────────┘
                                                    │
                                                    │ X-API-Key: sk_xxxx
                                                    │
                                                    ▼
                                     ┌─────────────────────────────────────┐
                                     │           ShareYourAi API            │
                                     │                                      │
                                     │  Base URL: shareyouai.winepipeline   │
                                     │  - POST /tasks/submit                │
                                     │  - GET  /tasks/{id}                  │
                                     │  - POST /tasks/{id}/cancel           │
                                     │                                      │
                                     └─────────────────────────────────────┘
                                                    │
                                                    ▼
                                     ┌─────────────────────────────────────┐
                                     │           腾讯云 COS                 │
                                     │                                      │
                                     │  - 视频结果存储                       │
                                     │  - 返回公开URL给前端                  │
                                     │                                      │
                                     └─────────────────────────────────────┘
```

---

## 二、模型配置开关设计

### 2.1 数据库字段新增

在 `ai_models` 表新增字段：

```python
# backend/models.py
class AIModel(Base):
    # ... 现有字段 ...

    # 新增字段：是否使用云函数转发
    use_cloud_function = Column(Boolean, default=True)  # 默认True，兼容现有模型

    # 新增字段：直接调用的 API Provider 类型
    direct_api_provider = Column(String(50))  # shareyourai / t8star_direct / modelscope_direct

    # 新增字段：API Key（直接调用模式时使用）
    direct_api_key = Column(String(255))  # 存储在数据库，或从环境变量读取
```

### 2.2 模型配置示例

**云函数代理模式（T8Star）**：
```json
{
  "model_id": "sora-2",
  "display_name": "Sora-2",
  "use_cloud_function": true,
  "api_provider": "t8star",
  "config_schema": {
    "pricing_rules": { "mode": "dynamic", "base_price": 5, ... },
    ...
  }
}
```

**后端直接调用模式（ShareYourAi）**：
```json
{
  "model_id": "grok-video-3",
  "display_name": "Grok Video 3",
  "use_cloud_function": false,
  "direct_api_provider": "shareyourai",
  "direct_api_key": null,  // 从环境变量读取，不存数据库
  "config_schema": {
    "pricing_rules": { "mode": "fixed", "fixed_price": 30 },
    "shareyourai_model_id": "grok_video",
    ...
  }
}
```

### 2.3 管理后台配置界面

在 `ModelManage.vue` 新增开关：

```vue
<el-form-item label="调用方式">
  <el-switch
    v-model="form.use_cloud_function"
    active-text="云函数代理"
    inactive-text="后端直接调用"
  />
</el-form-item>

<el-form-item label="直接调用服务商" v-if="!form.use_cloud_function">
  <el-select v-model="form.direct_api_provider">
    <el-option label="ShareYourAi" value="shareyourai" />
    <el-option label="T8Star Direct" value="t8star_direct" />
  </el-select>
</el-form-item>

<el-form-item label="ShareYourAi 模型ID" v-if="form.direct_api_provider === 'shareyourai'">
  <el-input v-model="form.config_schema.shareyourai_model_id" placeholder="grok_video" />
</el-form-item>
```

---

## 三、ShareYourAi API 接口契约

### 3.1 基础信息

| 项目 | 值 |
|-----|-----|
| **Base URL** | `https://shareyouai.winepipeline.com/api/v1` |
| **认证方式** | Header: `X-API-Key: {api_key}` |
| **内容格式** | `Content-Type: application/json` |

### 3.2 核心接口

#### 提交任务：POST /tasks/submit

**请求**：
```json
{
  "model_id": "grok_video",
  "prompt": "一只可爱的猫咪在阳光下跳舞",
  "images": ["data:image/png;base64,iVBORw0KGgo..."],
  "params": {
    "duration": 6,
    "aspect_ratio": "16:9",
    "resolution": "1080p"
  },
  "external_id": "HITOM_12345"
}
```

**成功响应**：
```json
{
  "success": true,
  "task_id": "T123456789012",
  "estimated_time": 300,
  "cost": 0.30
}
```

#### 查询状态：GET /tasks/{task_id}

**响应**：
```json
{
  "success": true,
  "task": {
    "task_id": "T123456789012",
    "status": "success",
    "result_url": "https://shareyouai-xxx.cos.ap-guangzhou.myqcloud.com/videos/xxx.mp4",
    "duration": 6,
    "file_size": 12582912
  }
}
```

**状态映射**：
| ShareYourAi status | Hi-Tom-AI 处理 |
|--------------------|----------------|
| pending | 继续轮询 |
| processing | 继续轮询 |
| success | 停止轮询，返回URL |
| failed | 停止轮询，退还积分 |
| timeout | 停止轮询，退还积分 |
| cancelled | 停止轮询，已退款 |

### 3.3 可用模型

| ShareYourAi model_id | 名称 | 收费 | Hi-Tom-AI 积分建议 |
|----------------------|------|------|-------------------|
| `grok_video` | Grok 视频生成 | ¥0.30 | 30积分 |
| `sora2_video` | Sora2 视频生成 | ¥0.10 | 10积分 |

---

## 四、后端 API 设计（新增）

### 4.1 接口列表

| 接口 | 方法 | 说明 | 用途 |
|-----|------|------|------|
| `/api/tasks/submit` | POST | 提交任务 | 预扣积分 + 调用 ShareYourAi |
| `/api/tasks/{task_id}/status` | GET | 查询状态 | 轻量轮询，不阻塞 |
| `/api/tasks/{task_id}/confirm` | POST | 确认扣费 | 任务成功后确认 |
| `/api/tasks/{task_id}/refund` | POST | 退还积分 | 任务失败/取消时退款 |

### 4.2 提交任务接口

**POST /api/tasks/submit**

**请求头**：
```
Authorization: Bearer {user_token}
```

**请求体**：
```json
{
  "model_id": "grok-video-3",
  "prompt": "一只可爱的猫咪在阳光下跳舞",
  "images": ["data:image/png;base64,..."],
  "params": {
    "duration": 6,
    "aspect_ratio": "9:16",
    "resolution": "1080p"
  }
}
```

**处理流程**：
```
1. 验证用户Token → 401 if 无效
2. 查询模型配置 → 判断 use_cloud_function
3. 计算积分费用 → 402 if 积分不足
4. 预扣积分 → reserve_points()
5. 调用 ShareYourAi API → 提交任务
6. 创建任务记录 → 存入 generation_history
7. 返回 task_id + deduction_id → 前端开始轮询
```

**成功响应**：
```json
{
  "success": true,
  "task_id": "T123456789012",
  "deduction_id": "DEDUCT_xxx",
  "estimated_time": 300,
  "cost_points": 30
}
```

**失败响应**：
```json
{
  "success": false,
  "error": "积分不足",
  "error_code": "INSUFFICIENT_POINTS"
}
```

### 4.3 查询状态接口

**GET /api/tasks/{task_id}/status**

**请求头**：
```
Authorization: Bearer {user_token}
```

**处理流程**：
```
1. 验证用户Token
2. 验证任务归属（防止查询他人任务）
3. 调用 ShareYourAi 查询接口
4. 返回状态（不阻塞，轻量）
```

**响应**：
```json
{
  "success": true,
  "task": {
    "task_id": "T123456789012",
    "status": "processing",
    "progress": 50
  }
}
```

**任务成功时**：
```json
{
  "success": true,
  "task": {
    "task_id": "T123456789012",
    "status": "success",
    "result_url": "https://xxx.cos.ap-guangzhou.myqcloud.com/videos/xxx.mp4"
  },
  "auto_confirmed": false  // 前端需调用 confirm 接口
}
```

### 4.4 确认扣费接口

**POST /api/tasks/{task_id}/confirm**

**处理流程**：
```
1. 验证用户Token
2. 验证任务归属
3. 验证任务状态 = success
4. 确认积分扣费 → confirm_points(deduction_id)
5. 更新任务记录状态
```

**响应**：
```json
{
  "success": true,
  "message": "扣费已确认"
}
```

### 4.5 退还积分接口

**POST /api/tasks/{task_id}/refund**

**处理流程**：
```
1. 验证用户Token
2. 验证任务归属
3. 验证任务状态 = failed/timeout
4. 退还积分 → refund_points(deduction_id)
5. 更新任务记录状态
```

---

## 五、异步任务 + 轮询分离架构

### 5.1 设计理念

```
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│   提交阶段（同步，快速响应）                                           │
│   ─────────────────────                                              │
│   前端 POST /tasks/submit                                            │
│        │                                                             │
│        ▼                                                             │
│   后端：验证 → 预扣积分 → 调用ShareYourAi → 返回task_id               │
│        │                                                             │
│        │  响应时间：约 2-3 秒                                         │
│        │                                                             │
│        ▼                                                             │
│   前端收到 task_id，开始轮询                                          │
│                                                                      │
│   ───────────────────────────────────────────────────────────────────│
│                                                                      │
│   轮询阶段（异步，不阻塞）                                             │
│   ─────────────────────                                              │
│   前端 GET /tasks/{id}/status（每30秒）                               │
│        │                                                             │
│        ▼                                                             │
│   后端：验证Token → 调用ShareYourAi查询 → 返回状态                    │
│        │                                                             │
│        │  响应时间：约 0.5 秒（轻量）                                  │
│        │                                                             │
│        ▼                                                             │
│   前端根据状态决定：继续轮询 / 完成 / 失败                             │
│                                                                      │
│   ───────────────────────────────────────────────────────────────────│
│                                                                      │
│   完成阶段（前端主动确认）                                             │
│   ─────────────────────                                              │
│   前端 POST /tasks/{id}/confirm                                      │
│        │                                                             │
│        ▼                                                             │
│   后端：确认扣费 → 更新记录                                           │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 5.2 前端轮询配置

```javascript
const POLLING_CONFIG = {
  interval: 30000,       // 30秒轮询间隔
  maxAttempts: 20,       // 最大20次 = 10分钟
  timeout: 600000,       // 总超时10分钟

  // 状态处理
  onSuccess: (task) => {
    // 调用 confirm 接口确认扣费
    confirmTask(task.task_id)
    // 显示结果URL
    showVideo(task.result_url)
  },
  onFailed: (task) => {
    // 调用 refund 接牌退还积分
    refundTask(task.task_id)
    // 提示用户重试
    showError('生成失败，积分已退还')
  },
  onTimeout: () => {
    // 超时处理
    refundTask(task_id)
    showError('生成超时，积分已退还')
  }
}
```

### 5.3 后端轮询请求处理（轻量）

```python
# backend/main.py

@router.get("/api/tasks/{task_id}/status")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    查询任务状态 - 轻量接口，不阻塞
    """
    # 1. 验证任务归属
    task = get_task_by_id(task_id)
    if task.user_id != current_user.id:
        raise HTTPException(403, "无权查询此任务")

    # 2. 调用 ShareYourAi 查询（异步，不阻塞）
    status_data = await shareyourai_client.get_task_status(task_id)

    # 3. 直接返回，不做额外处理
    return {
        "success": True,
        "task": status_data["task"]
    }
```

---

## 六、代码实现设计

### 6.1 后端目录结构

```
backend/
├── main.py                    # 新增 task 相关路由
├── crud.py                    # 新增 task CRUD 函数
├── models.py                  # 新增字段 + Task 表
├── clients/
│   ├── __init__.py
│   ├── shareyourai_client.py  # ShareYourAi API 封装
│   └── base_client.py         # API 客户端基类
└── engines/
    ├── pricing_engine.py      # 现有
    └── payload_builder.py     # 现有
```

### 6.2 ShareYourAi 客户端封装

```python
# backend/clients/shareyourai_client.py

import httpx
from typing import Dict, Any, Optional

class ShareYourAiClient:
    """ShareYourAi API 客户端"""

    BASE_URL = "https://shareyouai.winepipeline.com/api/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=60.0)

    async def submit_task(
        self,
        model_id: str,
        prompt: str,
        images: Optional[list] = None,
        params: Optional[dict] = None,
        external_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """提交任务"""
        payload = {
            "model_id": model_id,
            "prompt": prompt,
            "params": params or {}
        }
        if images:
            payload["images"] = images
        if external_id:
            payload["external_id"] = external_id

        response = await self.client.post(
            f"{self.BASE_URL}/tasks/submit",
            headers={"X-API-Key": self.api_key},
            json=payload
        )
        return response.json()

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """查询任务状态"""
        response = await self.client.get(
            f"{self.BASE_URL}/tasks/{task_id}",
            headers={"X-API-Key": self.api_key}
        )
        return response.json()

    async def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """取消任务"""
        response = await self.client.post(
            f"{self.BASE_URL}/tasks/{task_id}/cancel",
            headers={"X-API-Key": self.api_key}
        )
        return response.json()

    async def get_account_info(self) -> Dict[str, Any]:
        """查询账户余额"""
        response = await self.client.get(
            f"{self.BASE_URL}/account/info",
            headers={"X-API-Key": self.api_key}
        )
        return response.json()

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


# 全局实例（API Key 从环境变量读取）
import os
SHAREYOURAI_API_KEY = os.getenv("SHAREYOURAI_API_KEY", "")
shareyourai_client = ShareYourAiClient(SHAREYOURAI_API_KEY)
```

### 6.3 后端路由实现

```python
# backend/main.py（新增部分）

from clients.shareyourai_client import shareyourai_client

@router.post("/api/tasks/submit")
async def submit_task(
    request: TaskSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    提交任务 - 后端直接调用模式
    """
    # 1. 查询模型配置
    model = get_model_by_id(db, request.model_id)
    if not model:
        raise HTTPException(404, "模型不存在")

    # 2. 判断调用方式
    if model.use_cloud_function:
        # 云函数模式，返回特殊标记让前端走原有路径
        return {
            "success": True,
            "use_cloud_function": True,
            "model": model,
            "tencent_function_url": get_system_config("tencent_function_url")
        }

    # 3. 后端直接调用模式
    # 计算积分
    cost_points = pricing_engine.calculate(
        model.config_schema.get("pricing_rules", {}),
        request.dict()
    )["cost"]

    # 验证积分
    if current_user.points < cost_points:
        raise HTTPException(402, "积分不足")

    # 预扣积分
    deduction_id = reserve_points(
        db, current_user.id, cost_points,
        request.model_id, "视频生成"
    )

    # 调用 ShareYourAi
    shareyourai_model_id = model.config_schema.get("shareyourai_model_id", request.model_id)

    try:
        result = await shareyourai_client.submit_task(
            model_id=shareyourai_model_id,
            prompt=request.prompt,
            images=request.images,
            params=request.params,
            external_id=deduction_id
        )

        if not result.get("success"):
            # 调用失败，退还积分
            refund_points(db, deduction_id, "ShareYourAi调用失败")
            raise HTTPException(500, result.get("error", "调用失败"))

        # 创建任务记录
        create_task_record(db, {
            "task_id": result["task_id"],
            "user_id": current_user.id,
            "model_id": request.model_id,
            "deduction_id": deduction_id,
            "status": "pending",
            "cost_points": cost_points
        })

        return {
            "success": True,
            "use_cloud_function": False,
            "task_id": result["task_id"],
            "deduction_id": deduction_id,
            "estimated_time": result.get("estimated_time", 300),
            "cost_points": cost_points
        }

    except Exception as e:
        refund_points(db, deduction_id, f"异常: {str(e)}")
        raise HTTPException(500, f"调用失败: {str(e)}")


@router.get("/api/tasks/{task_id}/status")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """查询任务状态"""
    # 验证归属
    task = get_task_record(db, task_id)
    if not task or task.user_id != current_user.id:
        raise HTTPException(403, "无权查询此任务")

    # 调用 ShareYourAi 查询
    result = await shareyourai_client.get_task_status(task_id)

    if not result.get("success"):
        return {"success": False, "error": result.get("error")}

    task_data = result["task"]
    status = task_data["status"]

    # 更新本地记录状态
    update_task_status(db, task_id, status)

    # 失败/超时时自动退款
    if status in ["failed", "timeout"]:
        refund_points(db, task.deduction_id, f"任务{status}")
        return {
            "success": True,
            "task": task_data,
            "refunded": True,
            "message": "积分已退还"
        }

    return {
        "success": True,
        "task": task_data,
        "refunded": False
    }


@router.post("/api/tasks/{task_id}/confirm")
async def confirm_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """确认扣费"""
    task = get_task_record(db, task_id)
    if not task or task.user_id != current_user.id:
        raise HTTPException(403, "无权操作此任务")

    # 验证状态
    result = await shareyourai_client.get_task_status(task_id)
    if result["task"]["status"] != "success":
        raise HTTPException(400, "任务未成功完成")

    # 确认扣费
    confirm_points(db, task.deduction_id)

    # 更新记录
    update_task_status(db, task_id, "success", result["task"].get("result_url"))

    return {"success": True, "message": "扣费已确认"}
```

### 6.4 前端调用逻辑

```javascript
// user-web/src/api/index.js（新增部分）

// 提交任务（统一入口）
export const submitTask = async (data) => {
  const response = await request.post('/api/tasks/submit', data)

  if (response.use_cloud_function) {
    // 云函数模式：走原有逻辑
    return submitViaCloudFunction(response, data)
  } else {
    // 后端直接模式：返回task_id，开始轮询
    return {
      mode: 'direct',
      task_id: response.task_id,
      deduction_id: response.deduction_id,
      estimated_time: response.estimated_time
    }
  }
}

// 查询任务状态（后端直接模式）
export const getTaskStatus = (taskId) => {
  return request.get(`/api/tasks/${taskId}/status`)
}

// 确认扣费
export const confirmTask = (taskId) => {
  return request.post(`/api/tasks/${taskId}/confirm`)
}

// 退还积分
export const refundTask = (taskId) => {
  return request.post(`/api/tasks/${taskId}/refund`)
}
```

### 6.5 前端 VideoTool.vue 改动

```vue
<script setup>
import { submitTask, getTaskStatus, confirmTask, refundTask } from '@/api'

const pollTask = async (taskId, deductionId) => {
  const config = {
    interval: 30000,
    maxAttempts: 20
  }

  for (let i = 0; i < config.maxAttempts; i++) {
    await sleep(config.interval)

    const result = await getTaskStatus(taskId)

    if (result.task.status === 'success') {
      // 确认扣费
      await confirmTask(taskId)
      // 显示结果
      videoUrl.value = result.task.result_url
      return
    }

    if (result.task.status === 'failed' || result.task.status === 'timeout') {
      // 已自动退款
      showError('生成失败，积分已退还')
      return
    }

    // 继续轮询
    progress.value = result.task.progress || 0
  }

  // 超时
  await refundTask(taskId)
  showError('生成超时，积分已退还')
}
</script>
```

---

## 七、环境配置

### 7.1 后端环境变量

```env
# ShareYourAi 配置
SHAREYOURAI_API_KEY=sk_xxxxxxxxxxxxxxxx

# 腾讯云 COS 配置（可选，用于存储结果）
COS_SECRET_ID=xxx
COS_SECRET_KEY=xxx
COS_BUCKET=xxx
COS_REGION=ap-guangzhou
```

### 7.2 系统配置（管理后台）

在 `SystemConfig` 表新增配置项：

| key | value | 说明 |
|-----|-------|------|
| `shareyourai_api_key` | sk_xxx | 可选，从数据库读取 |
| `shareyourai_balance_alert` | 100 | 余额低于此值时告警 |

---

## 八、错误处理策略

### 8.1 错误码定义

| 错误码 | HTTP状态 | 说明 | 处理 |
|-------|---------|------|------|
| `INVALID_TOKEN` | 401 | Token无效 | 前端跳转登录 |
| `INSUFFICIENT_POINTS` | 402 | 积分不足 | 前端提示充值 |
| `MODEL_NOT_FOUND` | 404 | 模型不存在 | 前端刷新模型列表 |
| `TASK_NOT_FOUND` | 404 | 任务不存在 | 前端停止轮询 |
| `SHAREYOURAI_ERROR` | 500 | ShareYourAi调用失败 | 退还积分 |
| `NO_AVAILABLE_NODES` | 200 | 无可用节点 | 稍后重试 |

### 8.2 异常处理流程

```
提交阶段异常：
├── 积分不足 → 直接返回 402，不调用 API
├── ShareYourAi 调用失败 → 退还积分 → 返回 500
└── 网络超时 → 退还积分 → 返回 500

轮询阶段异常：
├── 任务 failed → 自动退还积分
├── 任务 timeout → 自动退还积分
└── 轮询超时（10分钟）→ 调用 refund 接口

确认阶段异常：
├── 任务未成功 → 返回 400
└── 认证失败 → 返回 403
```

---

## 九、测试验证清单

### 9.1 功能测试

- [ ] 云函数模式正常工作（原有逻辑不变）
- [ ] 后端直接模式提交任务成功
- [ ] 后端直接模式轮询状态正常
- [ ] 任务成功后确认扣费
- [ ] 任务失败后自动退款
- [ ] 模型配置开关切换正常
- [ ] 无可用节点时正确报错
- [ ] ShareYourAi 余额查询正常

### 9.2 安全测试

- [ ] 无Token用户无法提交任务
- [ ] 用户无法查询他人任务状态
- [ ] 用户无法确认他人任务扣费
- [ ] API Key 不暴露给前端

### 9.3 异常测试

- [ ] ShareYourAi 账户余额不足时正确报错
- [ ] 任务超时后自动退款
- [ ] 任务失败后自动退款
- [ ] 网络异常时积分正确退还

---

## 十、部署步骤

### 10.1 后端部署

```bash
# 1. 安装依赖（httpx 用于异步 HTTP）
cd backend
pip install httpx

# 2. 配置环境变量
export SHAREYOURAI_API_KEY=sk_xxx

# 3. 数据库迁移（新增字段）
python migrate_add_use_cloud_function.py

# 4. 重启服务
uvicorn main:app --reload --port 8000
```

### 10.2 ShareYourAi 平台准备

1. 登录管理后台：`https://shareyouai.winepipeline.com`
2. 创建平台客户：`Hi-Tom-AI`
3. 获取 API Key：`sk_xxx`
4. 充值测试余额：建议 ¥50

### 10.3 模型配置

在 Hi-Tom-AI 管理后台新增模型：

| 字段 | 值 |
|-----|-----|
| model_id | grok-video-3 |
| display_name | Grok Video 3 |
| use_cloud_function | false |
| direct_api_provider | shareyourai |
| shareyourai_model_id | grok_video |
| fixed_price | 30 |

---

## 附录：完整请求流程示例

### A.1 提交 Grok 视频任务

**前端请求**：
```javascript
POST /api/tasks/submit
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...

{
  "model_id": "grok-video-3",
  "prompt": "一只橘猫在阳光下伸懒腰",
  "params": {
    "duration": 6,
    "aspect_ratio": "9:16",
    "resolution": "1080p"
  }
}
```

**后端响应**：
```json
{
  "success": true,
  "use_cloud_function": false,
  "task_id": "T996145748986",
  "deduction_id": "DEDUCT_abc123",
  "estimated_time": 300,
  "cost_points": 30
}
```

### A.2 轮询状态（每30秒）

**前端请求**：
```javascript
GET /api/tasks/T996145748986/status
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**后端响应（processing）**：
```json
{
  "success": true,
  "task": {
    "task_id": "T996145748986",
    "status": "processing",
    "progress": 50
  },
  "refunded": false
}
```

### A.3 任务完成

**后端响应（success）**：
```json
{
  "success": true,
  "task": {
    "task_id": "T996145748986",
    "status": "success",
    "result_url": "https://shareyouai-xxx.cos.ap-guangzhou.myqcloud.com/videos/xxx.mp4"
  },
  "refunded": false
}
```

### A.4 前端确认扣费

**前端请求**：
```javascript
POST /api/tasks/T996145748986/confirm
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

**后端响应**：
```json
{
  "success": true,
  "message": "扣费已确认"
}
```