"""
Hi-Tom-AI Backend API
FastAPI 主应用
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel

from database import get_db, init_db
from models import Base
import crud
import schemas
from utils import hash_password, verify_password, create_access_token, decode_token
from engines.payload_builder import payload_builder
from ai_service import AIService

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


# ============ 启动事件 ============
@app.on_event("startup")
async def startup_event():
    init_db()
    print("[OK] Hi-Tom-AI Backend started")


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
    db: Session = Depends(get_db)
):
    """用户注册"""
    existing = crud.get_user_by_username(db, user_data.username)
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")

    signup_bonus = int(crud.get_config(db, "signup_bonus", "10"))
    user = crud.create_user(db, user_data.username, hash_password(user_data.password), signup_bonus)
    return user


@app.post("/auth/token")
async def login(
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

    token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


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
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员封禁/解封用户"""
    user = crud.toggle_user_status(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
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
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员创建模型"""
    existing = crud.get_model_by_id(db, model_data.model_id)
    if existing:
        raise HTTPException(status_code=400, detail="模型ID已存在")

    model_dict = model_data.model_dump()
    return crud.create_model(db, model_dict)


@app.put("/admin/models/{model_pk}", response_model=schemas.AIModelResponse)
async def admin_update_model(
    model_pk: int,
    model_data: schemas.AIModelUpdate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员更新模型"""
    update_dict = model_data.model_dump(exclude_unset=True)
    model = crud.update_model(db, model_pk, update_dict)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    return model


@app.delete("/admin/models/{model_pk}")
async def admin_delete_model(
    model_pk: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员删除模型"""
    if not crud.delete_model(db, model_pk):
        raise HTTPException(status_code=404, detail="模型不存在")
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
        expire_seconds=600
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
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员更新系统配置"""
    for key, value in data.configs.items():
        crud.set_config(db, key, value)
    return {"status": "success", "message": "配置已更新"}


@app.post("/admin/recharge")
async def admin_recharge(
    username: str,
    amount: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员充值积分"""
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.points += amount
    db.commit()
    return {"status": "success", "new_balance": user.points}


# ============ API Key 管理接口 ============
@app.get("/admin/api-keys", response_model=List[schemas.APIKeyResponse])
async def admin_get_api_keys(
    provider: Optional[str] = None,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员获取 API Key 列表"""
    keys = crud.get_all_api_keys(db, provider)
    # 掩码处理 key_value，只显示前6位和后4位
    result = []
    for key in keys:
        key_dict = {
            "id": key.id,
            "key_name": key.key_name,
            "key_value": mask_api_key(key.key_value),
            "provider": key.provider,
            "is_enabled": key.is_enabled,
            "description": key.description,
            "use_count": key.use_count,
            "last_used_time": key.last_used_time,
            "create_time": key.create_time,
            "update_time": key.update_time
        }
        result.append(key_dict)
    return result


def mask_api_key(key: str) -> str:
    """掩码处理 API Key"""
    if not key or len(key) < 10:
        return "****"
    return f"{key[:6]}...{key[-4:]}"


@app.post("/admin/api-keys", response_model=schemas.APIKeyResponse)
async def admin_create_api_key(
    key_data: schemas.APIKeyCreate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员创建 API Key"""
    existing = crud.get_api_key_by_name(db, key_data.key_name)
    if existing:
        raise HTTPException(status_code=400, detail="Key 名称已存在")

    key = crud.create_api_key(db, key_data.key_name, key_data.key_value, key_data.provider, key_data.description)
    return {
        "id": key.id,
        "key_name": key.key_name,
        "key_value": mask_api_key(key.key_value),
        "provider": key.provider,
        "is_enabled": key.is_enabled,
        "description": key.description,
        "use_count": key.use_count,
        "last_used_time": key.last_used_time,
        "create_time": key.create_time,
        "update_time": key.update_time
    }


@app.put("/admin/api-keys/{key_id}", response_model=schemas.APIKeyResponse)
async def admin_update_api_key(
    key_id: int,
    key_data: schemas.APIKeyUpdate,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员更新 API Key"""
    key = crud.update_api_key(db, key_id, key_data.key_value, key_data.is_enabled, key_data.description)
    if not key:
        raise HTTPException(status_code=404, detail="API Key 不存在")
    return {
        "id": key.id,
        "key_name": key.key_name,
        "key_value": mask_api_key(key.key_value),
        "provider": key.provider,
        "is_enabled": key.is_enabled,
        "description": key.description,
        "use_count": key.use_count,
        "last_used_time": key.last_used_time,
        "create_time": key.create_time,
        "update_time": key.update_time
    }


@app.delete("/admin/api-keys/{key_id}")
async def admin_delete_api_key(
    key_id: int,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)
):
    """管理员删除 API Key"""
    if not crud.delete_api_key(db, key_id):
        raise HTTPException(status_code=404, detail="API Key 不存在")
    return {"status": "success", "message": "API Key 已删除"}


@app.get("/api/keys/{provider}")
async def get_api_key_for_vercel(
    provider: str,
    secret: str = None,
    db: Session = Depends(get_db)
):
    """获取 API Key（供 Vercel Functions 调用，需要 BACKEND_SECRET 认证）"""
    from os import getenv

    # 内部认证
    backend_secret = getenv("BACKEND_SECRET", "hi-tom-ai-internal-secret")
    if secret != backend_secret:
        raise HTTPException(status_code=403, detail="认证失败")

    key = crud.get_random_api_key(db, provider)
    if not key:
        raise HTTPException(status_code=404, detail=f"未找到 {provider} 的 API Key")
    return {"key": key}


# ============ AI 提示词生成接口 ============

class SellingPointsRequest(BaseModel):
    """看图写卖点请求"""
    images: List[str]  # 图片 base64 列表
    product_type: str = "通用产品"
    design_style: str = "简约风格"
    target_lang: str = "中文"
    target_num: int = 1


class PlanImagePromptsRequest(BaseModel):
    """生图提示词规划请求"""
    images: List[str] = []  # 参考图片
    product_type: str = ""
    selling_points: str = ""
    design_style: str = "简约风格"
    target_lang: str = "中文"
    num_screens: int = 1


class VideoScriptRequest(BaseModel):
    """视频分镜生成请求"""
    images: List[str] = []  # 参考图片
    product_type: str = ""
    selling_points: str = ""
    region: str = "东亚"
    target_lang: str = "中文"
    category: str = "通用"
    style: str = "UGC 种草"
    has_subtitle: bool = True


class TranslateRequest(BaseModel):
    """翻译请求"""
    text: str
    target_lang: str = "中文"


@app.post("/api/ai/selling-points")
async def generate_selling_points(
    request: SellingPointsRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    看图写卖点 - 使用管理后台配置的系统提示词

    根据产品图片生成多组卖点文案
    """
    # 获取提示词模板
    prompt_template = crud.get_config(db, "image_selling_points_prompt", "")
    if not prompt_template:
        raise HTTPException(status_code=400, detail="未配置看图写卖点提示词")

    # 调用 AI 服务
    ai = AIService()
    result = ai.generate_selling_points(
        prompt_template=prompt_template,
        images=request.images,
        product_type=request.product_type,
        design_style=request.design_style,
        target_lang=request.target_lang,
        target_num=request.target_num
    )

    if result and "Error" not in result:
        return {"status": "success", "content": result}
    else:
        return {"status": "error", "msg": result or "生成失败"}


@app.post("/api/ai/plan-image-prompts")
async def plan_image_prompts(
    request: PlanImagePromptsRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    生图提示词规划 - 使用管理后台配置的系统提示词

    根据产品信息规划多屏详情页的生图提示词
    """
    # 获取提示词模板
    prompt_template = crud.get_config(db, "image_generation_prompt", "")
    if not prompt_template:
        raise HTTPException(status_code=400, detail="未配置生图提示词规划模板")

    # 调用 AI 服务
    ai = AIService()
    prompts = ai.plan_image_prompts(
        prompt_template=prompt_template,
        images=request.images,
        product_type=request.product_type,
        selling_points=request.selling_points,
        design_style=request.design_style,
        target_lang=request.target_lang,
        num_screens=request.num_screens
    )

    if prompts:
        return {"status": "success", "prompts": prompts}
    else:
        return {"status": "error", "msg": "规划失败"}


@app.post("/api/ai/video-script")
async def generate_video_script(
    request: VideoScriptRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    视频分镜生成 - 使用管理后台配置的系统提示词

    根据产品信息生成视频分镜脚本
    """
    # 获取提示词模板
    prompt_template = crud.get_config(db, "video_script_prompt", "")
    if not prompt_template:
        raise HTTPException(status_code=400, detail="未配置视频分镜提示词模板")

    # 调用 AI 服务
    ai = AIService()
    script = ai.generate_video_script(
        prompt_template=prompt_template,
        images=request.images,
        product_type=request.product_type,
        selling_points=request.selling_points,
        region=request.region,
        target_lang=request.target_lang,
        category=request.category,
        style=request.style,
        has_subtitle=request.has_subtitle
    )

    if script and "Error" not in script:
        return {"status": "success", "script": script}
    else:
        return {"status": "error", "msg": script or "生成失败"}


@app.post("/api/ai/translate")
async def translate_text(
    request: TranslateRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    翻译文本
    """
    # 调用 AI 服务
    ai = AIService()
    result = ai.translate_text(
        text=request.text,
        target_lang=request.target_lang
    )

    if result and "Error" not in result and "失败" not in result:
        return {"status": "success", "content": result}
    else:
        return {"status": "error", "msg": result or "翻译失败"}


# ============ 启动入口 ============
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)