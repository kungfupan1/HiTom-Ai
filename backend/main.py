"""
Hi-Tom-AI Backend API
FastAPI 主应用
"""
import asyncio
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from database import get_db, init_db, SessionLocal
from models import Base
import crud
import schemas
from utils import hash_password, verify_password, create_access_token, decode_token, create_token_pair, verify_refresh_token
from engines.payload_builder import payload_builder

# 创建应用
app = FastAPI(
    title="Hi-Tom-AI API",
    description="AI 电商内容生成平台后端 API",
    version="1.0.0"
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=False)


# ============ 依赖注入 ============
async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """获取当前用户"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未登录",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = crud.get_user_by_id(db, int(payload.get("sub")))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )

    return user


async def get_current_admin(current_user = Depends(get_current_user)):
    """获取当前管理员"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


# ============ 后台任务 ============
async def cleanup_expired_reserves_task():
    """定时清理过期的积分预扣记录"""
    while True:
        await asyncio.sleep(300)  # 每5分钟执行一次
        try:
            db = SessionLocal()
            count = crud.cleanup_expired_reserves(db)
            db.close()
            if count > 0:
                print(f"[定时任务] 清理了 {count} 条过期预扣记录")
        except Exception as e:
            print(f"[定时任务] 清理过期预扣失败: {e}")


# ============ 启动事件 ============
@app.on_event("startup")
async def startup_event():
    init_db()
    # 启动后台清理任务
    asyncio.create_task(cleanup_expired_reserves_task())
    print("[OK] Hi-Tom-AI Backend started")
    print("[OK] 积分预扣清理任务已启动（每5分钟执行）")


# ============ 健康检查 ============
@app.get("/")
async def root():
    return {"status": "ok", "message": "Hi-Tom-AI API", "version": "1.0.0"}


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.get("/admin/stats")
async def admin_get_stats(
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员获取统计数据"""
    from models import User, AIModel, APILog
    from sqlalchemy import func

    user_count = db.query(func.count(User.id)).scalar()
    model_count = db.query(func.count(AIModel.id)).filter(AIModel.is_enabled == True).scalar()
    video_count = db.query(func.count(APILog.id)).filter(APILog.task_type == 'video').scalar() or 0
    image_count = db.query(func.count(APILog.id)).filter(APILog.task_type == 'image').scalar() or 0

    return {
        "userCount": user_count,
        "modelCount": model_count,
        "videoCount": video_count,
        "imageCount": image_count
    }


# ============ 认证接口 ============
@app.post("/auth/register", response_model=schemas.UserResponse)
async def register(
    user_data: schemas.UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """用户注册"""
    existing = crud.get_user_by_username(db, user_data.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    signup_bonus = int(crud.get_config(db, "signup_bonus", "10"))
    user = crud.create_user(db, user_data.username, hash_password(user_data.password), signup_bonus)

    # 记录操作日志
    crud.log_operation(
        db, user_id=user.id, action="REGISTER",
        detail={"username": user.username, "signup_bonus": signup_bonus},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return user


@app.post("/auth/token")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录"""
    user = crud.get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    if user.is_active == 0:
        raise HTTPException(status_code=403, detail="账号已被封禁")

    # 创建令牌对
    access_token, refresh_token = create_token_pair(user.id)

    # 记录操作日志
    crud.log_operation(
        db, user_id=user.id, action="LOGIN",
        detail={"username": user.username},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 7200  # 2小时，单位秒
    }


class RefreshTokenRequest(BaseModel):
    refresh_token: str


@app.post("/auth/refresh")
async def refresh_token(
    request: RefreshTokenRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """刷新访问令牌"""
    user_id = verify_refresh_token(request.refresh_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="刷新令牌无效或已过期")

    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    if user.is_active == 0:
        raise HTTPException(status_code=403, detail="账号已被封禁")

    # 创建新的令牌对
    access_token, refresh_token = create_token_pair(user.id)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 7200
    }


@app.get("/users/me", response_model=schemas.UserResponse)
async def get_me(current_user = Depends(get_current_user)):
    """获取当前用户信息"""
    return current_user


# ============ 模型管理接口 ============
@app.get("/api/models", response_model=List[schemas.AIModelListItem])
async def get_models(
    model_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取启用的模型列表"""
    models = crud.get_all_models(db, enabled_only=True)
    if model_type:
        models = [m for m in models if m.model_type == model_type]
    return models


@app.get("/api/models/{model_id}", response_model=schemas.AIModelResponse)
async def get_model_detail(
    model_id: str,
    db: Session = Depends(get_db)
):
    """获取模型详情"""
    model = crud.get_model_by_id(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    return model


# ============ 管理员接口 ============
@app.get("/admin/users")
async def admin_get_users(
    keyword: Optional[str] = None,
    page: int = 1,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员获取用户列表"""
    users, total = crud.get_all_users(db, keyword, page)
    return {
        "items": [{"id": u.id, "username": u.username, "points": u.points, "role": u.role, "is_active": u.is_active, "create_time": u.create_time} for u in users],
        "total": total
    }


@app.post("/admin/users/{user_id}/toggle-status")
async def admin_toggle_user_status(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员封禁/解封用户"""
    user = crud.toggle_user_status(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 记录操作日志
    crud.log_operation(
        db, user_id=admin.id, action="USER_TOGGLE_STATUS",
        detail={"target_user_id": user_id, "target_username": user.username, "new_status": user.is_active},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return {"status": "success", "is_active": user.is_active}


@app.get("/admin/models", response_model=List[schemas.AIModelResponse])
async def admin_get_models(
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员获取所有模型"""
    return crud.get_all_models(db)


@app.post("/admin/models", response_model=schemas.AIModelResponse)
async def admin_create_model(
    model_data: schemas.AIModelCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员创建模型"""
    existing = crud.get_model_by_id(db, model_data.model_id)
    if existing:
        raise HTTPException(status_code=400, detail="模型ID已存在")

    model_dict = model_data.model_dump()
    model = crud.create_model(db, model_dict)

    # 记录操作日志
    crud.log_operation(
        db, user_id=admin.id, action="MODEL_CREATE",
        detail={"model_id": model.model_id, "display_name": model.display_name},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return model


@app.put("/admin/models/{model_pk}", response_model=schemas.AIModelResponse)
async def admin_update_model(
    model_pk: int,
    model_data: schemas.AIModelUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员更新模型"""
    update_dict = model_data.model_dump(exclude_unset=True)
    model = crud.update_model(db, model_pk, update_dict)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")

    # 记录操作日志
    crud.log_operation(
        db, user_id=admin.id, action="MODEL_UPDATE",
        detail={"model_pk": model_pk, "model_id": model.model_id, "updated_fields": list(update_dict.keys())},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return model


@app.delete("/admin/models/{model_pk}")
async def admin_delete_model(
    model_pk: int,
    request: Request,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员删除模型"""
    model = crud.get_model_by_pk(db, model_pk)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")

    model_id = model.model_id
    if not crud.delete_model(db, model_pk):
        raise HTTPException(status_code=404, detail="模型不存在")

    # 记录操作日志
    crud.log_operation(
        db, user_id=admin.id, action="MODEL_DELETE",
        detail={"model_pk": model_pk, "model_id": model_id},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return {"status": "success", "message": "模型已删除"}


@app.post("/admin/models/{model_pk}/toggle")
async def admin_toggle_model(
    model_pk: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员启用/禁用模型"""
    model = crud.toggle_model(db, model_pk)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    return {"status": "success", "is_enabled": model.is_enabled}


# ============ 计费接口 ============
@app.post("/api/calculate-cost", response_model=schemas.CalculateCostResponse)
async def calculate_cost(
    request: schemas.CalculateCostRequest,
    db: Session = Depends(get_db)
):
    """计算生成费用"""
    result = crud.calculate_cost(
        db,
        model_id=request.model_id,
        duration=request.duration,
        resolution=request.resolution,
        ratio=request.ratio,
        count=request.count
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@app.post("/api/calculate-cost-dynamic", response_model=schemas.DynamicCalculateCostResponse)
async def calculate_cost_dynamic(
    request: schemas.DynamicCalculateCostRequest,
    db: Session = Depends(get_db)
):
    """
    动态计算生成费用 - 使用 config_schema.pricing_rules

    支持任意表单字段，根据模型配置动态计算费用
    """
    result = crud.calculate_cost_dynamic(
        db,
        model_id=request.model_id,
        form_data=request.form_data
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


class BuildPayloadRequest(BaseModel):
    """构建请求 Payload 请求"""
    model_id: str
    form_data: Dict[str, Any]


class BuildPayloadResponse(BaseModel):
    """构建请求 Payload 响应"""
    model_id: str
    api_contract: Optional[Dict[str, Any]] = None
    payload: Dict[str, Any]
    prompt_used: Optional[str] = None


@app.post("/api/build-payload", response_model=BuildPayloadResponse)
async def build_payload(
    request: BuildPayloadRequest,
    db: Session = Depends(get_db)
):
    """
    构建 API 请求 Payload - 使用 config_schema.request_mapping

    用于测试配置是否正确，返回构建后的请求体
    """
    model = crud.get_model_by_id(db, request.model_id)
    if not model:
        raise HTTPException(status_code=400, detail="模型不存在")

    if not model.config_schema:
        return BuildPayloadResponse(
            model_id=request.model_id,
            payload=request.form_data,
            prompt_used=None
        )

    config_schema = model.config_schema
    request_mapping = config_schema.get("request_mapping", {})
    api_contract = config_schema.get("api_contract", {})
    prompt_config = config_schema.get("prompt_config", {})

    # 获取全局系统提示词
    global_system_prompt = crud.get_config(db, "text_system_prompt", "")

    # 构建 payload
    payload = payload_builder.build(
        request_mapping=request_mapping,
        form_data=request.form_data,
        model_id=model.model_id,
        prompt_config=prompt_config,
        global_system_prompt=global_system_prompt
    )

    # 提取使用的 prompt
    prompt_used = None
    if request_mapping and "prompt_template" in request_mapping:
        import re
        prompt_template = request_mapping["prompt_template"]
        prompt_used = re.sub(
            r'\{(\w+)\}',
            lambda m: str(request.form_data.get(m.group(1), "")),
            prompt_template
        )

    return BuildPayloadResponse(
        model_id=request.model_id,
        api_contract=api_contract,
        payload=payload,
        prompt_used=prompt_used
    )


# ============ 积分接口 ============
@app.post("/api/points/reserve", response_model=schemas.PointReserveResponse)
async def reserve_points(
    request: schemas.PointReserveRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """预扣积分"""
    if current_user.points < request.amount:
        raise HTTPException(status_code=400, detail="积分不足")

    reserve = crud.reserve_points(
        db,
        user_id=current_user.id,
        amount=request.amount,
        model_id=request.model_id
    )

    if not reserve:
        raise HTTPException(status_code=400, detail="预扣失败")

    return schemas.PointReserveResponse(
        deduction_id=reserve.deduction_id,
        amount=reserve.amount,
        balance_before=current_user.points + reserve.amount,
        balance_after=current_user.points,
        expire_seconds=1200
    )


@app.post("/api/points/confirm")
async def confirm_points(
    request: schemas.PointConfirmRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """确认扣费"""
    if not crud.confirm_points(db, request.deduction_id):
        raise HTTPException(status_code=400, detail="确认失败，预扣记录不存在或已处理")
    return {"status": "success", "message": "扣费已确认"}


@app.post("/api/points/refund")
async def refund_points(
    request: schemas.PointRefundRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """退还积分"""
    if not crud.refund_points(db, request.deduction_id, request.reason):
        raise HTTPException(status_code=400, detail="退还失败，预扣记录不存在或已处理")
    return {"status": "success", "message": "积分已退还"}


# ============ 系统配置接口 ============
@app.get("/api/config/pricing-info")
async def get_pricing_info(db: Session = Depends(get_db)):
    """获取费用说明（公开接口）"""
    return crud.get_pricing_info(db)


@app.get("/admin/config")
async def admin_get_config(
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员获取系统配置"""
    configs = crud.get_all_configs(db)
    return {c.key: {"value": c.value, "description": c.description} for c in configs}


@app.put("/admin/config")
async def admin_update_config(
    data: schemas.SystemConfigUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员更新系统配置"""
    for key, value in data.configs.items():
        crud.set_config(db, key, value)

    # 记录操作日志
    crud.log_operation(
        db, user_id=admin.id, action="CONFIG_UPDATE",
        detail={"updated_keys": list(data.configs.keys())},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return {"status": "success", "message": "配置已更新"}


@app.post("/admin/recharge")
async def admin_recharge(
    username: str,
    amount: int,
    request: Request,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员充值积分"""
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    old_balance = user.points
    user.points += amount
    db.commit()

    # 记录操作日志
    crud.log_operation(
        db, user_id=admin.id, action="RECHARGE",
        detail={"target_user_id": user.id, "target_username": username, "amount": amount, "old_balance": old_balance, "new_balance": user.points},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return {"status": "success", "new_balance": user.points}


# ============ 操作日志接口 ============
@app.get("/admin/operation-logs")
async def admin_get_operation_logs(
    user_id: Optional[int] = None,
    action: Optional[str] = None,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员获取操作日志"""
    logs, total = crud.get_operation_logs(db, user_id, action, page, page_size)
    return {
        "items": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "detail": log.detail,
                "ip_address": log.ip_address,
                "create_time": log.create_time.isoformat() if log.create_time else None
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }


# ============ 生成历史记录接口 ============
class CreateHistoryRequest(BaseModel):
    """创建历史记录请求"""
    task_type: str
    model_id: Optional[str] = None
    task_id: Optional[str] = None
    status: str = "success"
    prompt_summary: Optional[str] = None
    params_json: Optional[Dict[str, Any]] = None
    result_url: Optional[str] = None
    cost_points: int = 0


@app.post("/api/history")
async def create_history(
    request: CreateHistoryRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建生成历史记录"""
    history = crud.create_generation_history(
        db,
        user_id=current_user.id,
        task_type=request.task_type,
        model_id=request.model_id,
        task_id=request.task_id,
        status=request.status,
        prompt_summary=request.prompt_summary,
        params_json=request.params_json,
        result_url=request.result_url,
        cost_points=request.cost_points
    )
    return {
        "status": "success",
        "id": history.id,
        "message": "历史记录已保存"
    }


@app.get("/api/history")
async def get_history(
    task_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的生成历史记录"""
    histories, total = crud.get_generation_history(
        db,
        user_id=current_user.id,
        task_type=task_type,
        page=page,
        page_size=page_size
    )

    return {
        "items": [
            {
                "id": h.id,
                "task_type": h.task_type,
                "model_id": h.model_id,
                "prompt_summary": h.prompt_summary,
                "params_json": h.params_json,
                "result_url": h.result_url,
                "cost_points": h.cost_points,
                "create_time": h.create_time.isoformat() if h.create_time else None
            }
            for h in histories
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@app.get("/api/history/{history_id}")
async def get_history_detail(
    history_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取单条历史记录详情"""
    history = crud.get_generation_history_by_id(db, history_id, current_user.id)
    if not history:
        raise HTTPException(status_code=404, detail="记录不存在")

    return {
        "id": history.id,
        "task_type": history.task_type,
        "model_id": history.model_id,
        "task_id": history.task_id,
        "status": history.status,
        "prompt_summary": history.prompt_summary,
        "params_json": history.params_json,
        "result_url": history.result_url,
        "cost_points": history.cost_points,
        "create_time": history.create_time.isoformat() if history.create_time else None
    }


@app.delete("/api/history/{history_id}")
async def delete_history(
    history_id: int,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除历史记录"""
    if not crud.delete_generation_history(db, history_id, current_user.id):
        raise HTTPException(status_code=404, detail="记录不存在")
    return {"status": "success", "message": "记录已删除"}


# ============ 内容配置接口（管理员） ============
@app.get("/admin/content-configs")
async def admin_get_content_configs(
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员获取所有内容配置"""
    configs = crud.get_all_content_configs(db)
    return {c.key: {"config": c.config, "description": c.description} for c in configs}


@app.get("/admin/content-configs/{key}")
async def admin_get_content_config(
    key: str,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员获取单个内容配置"""
    config = crud.get_content_config(db, key)
    return {"key": key, "config": config or {}}


@app.put("/admin/content-configs/{key}")
async def admin_set_content_config(
    key: str,
    data: schemas.ContentConfigUpdate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员设置内容配置"""
    crud.set_content_config(db, key, data.config)
    return {"status": "success", "message": "配置已保存"}


# ============ 内容配置接口（用户端） ============
@app.get("/api/content-config/{key}")
async def get_content_config(
    key: str,
    db: Session = Depends(get_db)
):
    """用户端获取内容配置"""
    config = crud.get_content_config(db, key)
    return {"key": key, "config": config or {}}


# ============ 启动入口 ============
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)