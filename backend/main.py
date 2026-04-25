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
from models import Base, PointReserve
import crud
import schemas
from utils import hash_password, verify_password, create_access_token, decode_token, create_token_pair, verify_refresh_token
from engines.payload_builder import payload_builder
import httpx

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

    signup_bonus = int(crud.get_config(db, "signup_bonus", "0"))
    user = crud.create_user(db, user_data.username, hash_password(user_data.password), signup_bonus)

    # 记录操作日志
    crud.log_operation(
        db, user_id=user.id, action="REGISTER",
        detail={"username": user.username, "signup_bonus": signup_bonus},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
    return user


# 登录失败限制配置
MAX_LOGIN_FAIL_COUNT = 7  # 最大连续失败次数
LOCK_DURATION_MINUTES = 30  # 锁定时长（分钟）


@app.post("/auth/token")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """用户登录（带失败次数限制）"""
    user = crud.get_user_by_username(db, form_data.username)

    # 用户不存在
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 检查是否被锁定
    if user.locked_until and user.locked_until > datetime.now():
        remaining = (user.locked_until - datetime.now()).seconds // 60
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"账号已被锁定，请 {remaining} 分钟后重试"
        )

    # 验证密码
    if not verify_password(form_data.password, user.password_hash):
        # 密码错误，增加失败次数
        user.login_fail_count = (user.login_fail_count or 0) + 1

        # 达到上限则锁定
        if user.login_fail_count >= MAX_LOGIN_FAIL_COUNT:
            user.locked_until = datetime.now() + timedelta(minutes=LOCK_DURATION_MINUTES)
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"连续登录失败 {MAX_LOGIN_FAIL_COUNT} 次，账号已锁定 {LOCK_DURATION_MINUTES} 分钟"
            )

        db.commit()
        remaining_attempts = MAX_LOGIN_FAIL_COUNT - user.login_fail_count
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"用户名或密码错误，剩余尝试次数: {remaining_attempts}"
        )

    # 检查账号状态
    if user.is_active == 0:
        raise HTTPException(status_code=403, detail="账号已被封禁")

    # 登录成功，重置失败计数
    user.login_fail_count = 0
    user.locked_until = None
    db.commit()

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


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str
    new_password: str


@app.post("/auth/change-password")
async def change_password(
    request: Request,
    data: ChangePasswordRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    # 验证旧密码
    if not verify_password(data.old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="旧密码错误")

    # 新密码不能与旧密码相同
    if verify_password(data.new_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="新密码不能与旧密码相同")

    # 新密码长度检查
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="新密码长度不能少于6位")

    # 更新密码
    current_user.password_hash = hash_password(data.new_password)
    # 重置登录失败计数
    current_user.login_fail_count = 0
    current_user.locked_until = None
    db.commit()

    # 记录操作日志
    crud.log_operation(
        db, user_id=current_user.id, action="CHANGE_PASSWORD",
        detail={"username": current_user.username},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    return {"status": "success", "message": "密码修改成功"}


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


@app.get("/api/content-configs-enabled")
async def get_content_configs_enabled(db: Session = Depends(get_db)):
    """用户端获取所有内容配置的启用状态"""
    all_configs = crud.get_all_content_configs(db)
    # 默认全部启用
    default_enabled = {
        'shrimp_openclaw': True,
        'shrimp_skills': True,
        'shrimp_ai_staff': True,
        'service_shop': True,
        'service_course': True,
        'service_logistics': True,
        'service_software': True,
        'service_network': True,
        'service_other': True
    }
    # 用数据库配置覆盖默认值
    for c in all_configs:
        if c.key in default_enabled and c.config:
            default_enabled[c.key] = c.config.get('enabled', True)
    return {"configs": default_enabled}


# ============ 任务提交接口（配置驱动）============

# HTTP 客户端（复用）
_http_client = None

def get_http_client():
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=120.0)
    return _http_client


async def call_external_api(
    api_contract: Dict[str, Any],
    payload: Dict[str, Any],
    method: str = "POST"
) -> Dict[str, Any]:
    """
    根据 api_contract 配置调用外部 API

    api_contract 结构:
    {
        "endpoint_url": "https://...",
        "status_url": "https://...",
        "method": "POST",
        "auth_type": "cloud_function" | "api_key_header" | "bearer_token",
        "placeholder": "T8STAR_API_KEY",  // cloud_function 时用
        "api_key": "sk-xxx",              // 直接调用时用
        "api_key_header": "X-API-Key"     // 默认 X-API-Key
    }
    """
    client = get_http_client()
    endpoint_url = api_contract.get("endpoint_url", "")
    auth_type = api_contract.get("auth_type", "cloud_function")

    # 构建请求头
    headers = {"Content-Type": "application/json"}

    if auth_type == "api_key_header":
        # 后端直接调用：使用 Header 认证
        header_name = api_contract.get("api_key_header", "X-API-Key")
        api_key = api_contract.get("api_key", "")
        if api_key:
            headers[header_name] = api_key
    elif auth_type == "bearer_token":
        # 后端直接调用：使用 Bearer Token 认证
        api_key = api_contract.get("api_key", "")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
    # cloud_function 模式：后端不处理，前端自己走云函数

    try:
        if method.upper() == "GET":
            response = await client.get(endpoint_url, headers=headers)
        else:
            response = await client.post(endpoint_url, headers=headers, json=payload)

        return response.json()
    except httpx.HTTPError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def query_task_status(
    api_contract: Dict[str, Any],
    task_id: str
) -> Dict[str, Any]:
    """查询任务状态"""
    client = get_http_client()
    status_url = api_contract.get("status_url", "")
    auth_type = api_contract.get("auth_type", "cloud_function")

    # 替换 {task_id} 占位符
    status_url = status_url.replace("{task_id}", task_id)

    # 构建请求头
    headers = {"Content-Type": "application/json"}

    if auth_type == "api_key_header":
        header_name = api_contract.get("api_key_header", "X-API-Key")
        api_key = api_contract.get("api_key", "")
        if api_key:
            headers[header_name] = api_key
    elif auth_type == "bearer_token":
        api_key = api_contract.get("api_key", "")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

    try:
        response = await client.get(status_url, headers=headers)
        return response.json()
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/api/tasks/submit", response_model=schemas.TaskSubmitResponse)
async def submit_task(
    request: schemas.TaskSubmitRequest,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    提交任务 - 配置驱动模式

    根据 config_schema.api_contract.auth_type 判断调用方式：
    - "cloud_function": 返回云函数配置，让前端走原有路径
    - "api_key_header" / "bearer_token": 后端直接调用外部 API
    """
    # 1. 查询模型配置
    model = crud.get_model_by_id(db, request.model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")

    # 2. 获取 api_contract 配置
    config_schema = model.config_schema or {}
    api_contract = config_schema.get("api_contract", {})
    auth_type = api_contract.get("auth_type", "cloud_function")

    # 3. 判断调用方式
    if auth_type == "cloud_function":
        # 云函数模式，返回配置让前端走原有路径
        tencent_function_url = crud.get_config(db, "tencent_function_url", "")
        return schemas.TaskSubmitResponse(
            success=True,
            use_cloud_function=True,
            tencent_function_url=tencent_function_url,
            model_info={
                "model_id": model.model_id,
                "display_name": model.display_name,
                "config_schema": model.config_schema
            }
        )

    # 4. 后端直接调用模式
    pricing_rules = config_schema.get("pricing_rules", {})

    # 计算积分
    form_data = request.params or {}
    if request.prompt:
        form_data["prompt"] = request.prompt

    cost_result = crud.calculate_cost_dynamic(db, request.model_id, form_data)
    cost_points = cost_result.get("cost", 0)

    if cost_points <= 0:
        cost_points = pricing_rules.get("fixed_cost", model.base_price)

    # 验证积分
    if current_user.points < cost_points:
        raise HTTPException(
            status_code=402,
            detail="积分不足",
            headers={"X-Error-Code": "INSUFFICIENT_POINTS"}
        )

    # 预扣积分
    reserve = crud.reserve_points(
        db,
        user_id=current_user.id,
        amount=cost_points,
        model_id=request.model_id
    )

    if not reserve:
        raise HTTPException(status_code=400, detail="预扣积分失败")

    deduction_id = reserve.deduction_id

    # 5. 构建请求 payload（使用 request_mapping）
    request_mapping = config_schema.get("request_mapping", {})
    external_model_id = config_schema.get("external_model_id", request.model_id)

    if request_mapping:
        # 使用 request_mapping 构建 payload
        payload = {}
        dynamic_params = request_mapping.get("dynamic_params", {})
        static_params = request_mapping.get("static_params", {})

        payload.update(static_params)

        for target_field, source_field in dynamic_params.items():
            if source_field == "model_id":
                payload[target_field] = external_model_id
            elif source_field == "prompt":
                payload[target_field] = request.prompt
            elif source_field == "params.duration":
                if "params" not in payload:
                    payload["params"] = {}
                payload["params"]["duration"] = request.params.get("duration") if request.params else None
            elif source_field == "params.aspect_ratio":
                if "params" not in payload:
                    payload["params"] = {}
                payload["params"]["aspect_ratio"] = request.params.get("aspect_ratio") if request.params else None
            elif source_field == "params.resolution":
                if "params" not in payload:
                    payload["params"] = {}
                payload["params"]["resolution"] = request.params.get("resolution") if request.params else None
            elif source_field == "external_id":
                payload[target_field] = deduction_id
            elif source_field and request.params:
                payload[target_field] = request.params.get(source_field)

        # 确保 params 不为空
        if "params" in payload and not payload["params"]:
            del payload["params"]
    else:
        # 默认 payload 格式
        payload = {
            "model_id": external_model_id,
            "prompt": request.prompt or "",
            "params": request.params or {}
        }
        if request.images:
            payload["images"] = request.images

    try:
        # 6. 调用外部 API
        result = await call_external_api(api_contract, payload)

        if not result.get("success"):
            crud.refund_points(db, deduction_id, f"API调用失败: {result.get('error', '未知错误')}")
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "调用外部 API 失败")
            )

        task_id = result.get("task_id")

        # 7. 创建任务记录
        prompt_summary = request.prompt[:500] if request.prompt else None
        crud.create_task_record(
            db,
            task_id=task_id,
            user_id=current_user.id,
            model_id=request.model_id,
            deduction_id=deduction_id,
            task_type=model.model_type,
            cost_points=cost_points,
            prompt_summary=prompt_summary,
            params_json=request.params,
            status="pending"
        )

        return schemas.TaskSubmitResponse(
            success=True,
            use_cloud_function=False,
            task_id=task_id,
            deduction_id=deduction_id,
            estimated_time=result.get("estimated_time", 300),
            cost_points=cost_points
        )

    except HTTPException:
        raise
    except Exception as e:
        crud.refund_points(db, deduction_id, f"异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"调用失败: {str(e)}")


@app.get("/api/tasks/{task_id}/status", response_model=schemas.TaskStatusResponse)
async def get_task_status(
    task_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    查询任务状态

    - 验证任务归属
    - 调用外部 API 查询
    - 失败/超时时自动退款
    """
    # 验证归属
    task = crud.get_task_record_by_user(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=403, detail="无权查询此任务")

    # 如果任务已终态，直接返回本地状态
    if task.status in ["success", "failed", "timeout", "refunded"]:
        return schemas.TaskStatusResponse(
            success=True,
            task={
                "task_id": task.task_id,
                "status": task.status,
                "result_url": task.result_url
            },
            refunded=(task.status == "refunded")
        )

    # 获取模型的 api_contract
    model = crud.get_model_by_id(db, task.model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")

    config_schema = model.config_schema or {}
    api_contract = config_schema.get("api_contract", {})

    # 调用外部 API 查询状态
    result = await query_task_status(api_contract, task_id)

    if not result.get("success"):
        return schemas.TaskStatusResponse(
            success=False,
            error=result.get("error", "查询失败")
        )

    # 解析响应（使用 response_mapping）
    response_mapping = config_schema.get("response_mapping", {})
    task_data = result.get("task", result)

    # 从 response_mapping 提取状态
    if response_mapping:
        status_path = response_mapping.get("status_path", "")
        result_url_path = response_mapping.get("result_url_path", "")

        # 简单的路径提取
        if status_path and "task.status" in status_path:
            status = task_data.get("status", result.get("status", "pending"))
        else:
            status = task_data.get("status", "pending")

        if result_url_path and "task.result_url" in result_url_path:
            result_url = task_data.get("result_url")
        else:
            result_url = task_data.get("result_url")
    else:
        status = task_data.get("status", "pending")
        result_url = task_data.get("result_url")

    # 更新本地记录状态
    crud.update_task_status(db, task_id, status, result_url)

    # 失败/超时时自动退款
    if status in ["failed", "timeout"]:
        if task.deduction_id:
            crud.refund_points(db, task.deduction_id, f"任务{status}")
        return schemas.TaskStatusResponse(
            success=True,
            task={"task_id": task_id, "status": status, "result_url": result_url},
            refunded=True,
            message="积分已退还"
        )

    return schemas.TaskStatusResponse(
        success=True,
        task={"task_id": task_id, "status": status, "result_url": result_url},
        refunded=False
    )


@app.post("/api/tasks/{task_id}/confirm", response_model=schemas.TaskConfirmResponse)
async def confirm_task(
    task_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    确认扣费
    """
    task = crud.get_task_record_by_user(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=403, detail="无权操作此任务")

    if task.status == "success":
        # 已经确认过了
        return schemas.TaskConfirmResponse(success=True, message="扣费已确认")

    # 获取模型配置查询最新状态
    model = crud.get_model_by_id(db, task.model_id)
    if model:
        config_schema = model.config_schema or {}
        api_contract = config_schema.get("api_contract", {})
        result = await query_task_status(api_contract, task_id)

        response_mapping = config_schema.get("response_mapping", {})
        task_data = result.get("task", result)

        if response_mapping and "task.status" in response_mapping.get("status_path", ""):
            status = task_data.get("status", "pending")
        else:
            status = task_data.get("status", "pending")

        result_url = task_data.get("result_url")

        if status != "success":
            raise HTTPException(status_code=400, detail="任务未成功完成，无法确认扣费")

        # 更新记录
        crud.update_task_status(db, task_id, "success", result_url)

    # 确认扣费
    if task.deduction_id:
        crud.confirm_points(db, task.deduction_id)

    return schemas.TaskConfirmResponse(success=True, message="扣费已确认")


@app.post("/api/tasks/{task_id}/refund", response_model=schemas.TaskRefundResponse)
async def refund_task(
    task_id: str,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    退还积分
    """
    task = crud.get_task_record_by_user(db, task_id, current_user.id)
    if not task:
        raise HTTPException(status_code=403, detail="无权操作此任务")

    if task.status == "refunded":
        return schemas.TaskRefundResponse(
            success=True,
            refunded_amount=0,
            message="积分已退还过"
        )

    # 退还积分
    refunded_amount = 0
    if task.deduction_id:
        reserve = db.query(PointReserve).filter(
            PointReserve.deduction_id == task.deduction_id,
            PointReserve.status == "reserved"
        ).first()

        if reserve:
            refunded_amount = reserve.amount
            crud.refund_points(db, task.deduction_id, "任务失败/超时退款")

    # 更新记录
    crud.update_task_status(db, task_id, "refunded")

    return schemas.TaskRefundResponse(
        success=True,
        refunded_amount=refunded_amount,
        message="积分已退还"
    )


# ============ 启动入口 ============
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)