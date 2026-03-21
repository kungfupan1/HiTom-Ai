"""
CRUD 操作
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
import uuid
import json

from models import User, AIModel, ModelPricing, SystemConfig, PointLog, PointReserve, APILog
from models import ContentConfig, OperationLog
from engines.pricing_engine import pricing_engine


# ============ 用户相关 ============
def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_all_users(db: Session, keyword: str = None, page: int = 1, page_size: int = 20) -> tuple:
    """获取用户列表"""
    query = db.query(User)
    if keyword:
        query = query.filter(User.username.contains(keyword))
    total = query.count()
    users = query.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return users, total


def toggle_user_status(db: Session, user_id: int) -> Optional[User]:
    """切换用户状态（封禁/解封）"""
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    user.is_active = 0 if user.is_active == 1 else 1
    db.commit()
    db.refresh(user)
    return user


def create_user(db: Session, username: str, password_hash: str, signup_bonus: int = 10) -> User:
    user = User(
        username=username,
        password_hash=password_hash,
        points=signup_bonus
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 记录赠送积分
    if signup_bonus > 0:
        log = PointLog(
            user_id=user.id,
            change_type="BONUS",
            amount=signup_bonus,
            balance_after=user.points,
            description="注册赠送"
        )
        db.add(log)
        db.commit()

    return user


def get_user_points(db: Session, user_id: int) -> int:
    user = get_user_by_id(db, user_id)
    return user.points if user else 0


# ============ 积分预扣相关 ============
def reserve_points(db: Session, user_id: int, amount: int, model_id: str, expire_seconds: int = 1200) -> Optional[PointReserve]:
    """预扣积分，返回预扣记录"""
    user = get_user_by_id(db, user_id)
    if not user or user.points < amount:
        return None

    # 生成唯一 deduction_id
    deduction_id = f"ded_{uuid.uuid4().hex[:16]}"

    # 扣减积分
    balance_before = user.points
    user.points -= amount

    # 创建预扣记录
    reserve = PointReserve(
        deduction_id=deduction_id,
        user_id=user_id,
        amount=amount,
        model_id=model_id,
        status="reserved",
        expire_time=datetime.now() + timedelta(seconds=expire_seconds)
    )

    # 创建积分日志
    log = PointLog(
        user_id=user_id,
        change_type="RESERVE",
        amount=-amount,
        balance_after=user.points,
        description=f"预扣积分 - {model_id}",
        deduction_id=deduction_id,
        status="reserved"
    )

    db.add(reserve)
    db.add(log)
    db.commit()

    return reserve


def confirm_points(db: Session, deduction_id: str) -> bool:
    """确认扣费"""
    reserve = db.query(PointReserve).filter(
        PointReserve.deduction_id == deduction_id,
        PointReserve.status == "reserved"
    ).first()

    if not reserve:
        return False

    # 更新预扣状态
    reserve.status = "confirmed"

    # 更新日志状态
    db.query(PointLog).filter(
        PointLog.deduction_id == deduction_id
    ).update({"status": "confirmed", "change_type": "CONSUME"})

    db.commit()
    return True


def refund_points(db: Session, deduction_id: str, reason: str = None) -> bool:
    """退还积分"""
    reserve = db.query(PointReserve).filter(
        PointReserve.deduction_id == deduction_id,
        PointReserve.status == "reserved"
    ).first()

    if not reserve:
        return False

    user = get_user_by_id(db, reserve.user_id)
    if not user:
        return False

    # 退还积分
    user.points += reserve.amount
    reserve.status = "refunded"

    # 创建退还日志
    log = PointLog(
        user_id=user.id,
        change_type="REFUND",
        amount=reserve.amount,
        balance_after=user.points,
        description=reason or "积分退还",
        deduction_id=deduction_id,
        status="refunded"
    )

    db.add(log)
    db.commit()
    return True


def cleanup_expired_reserves(db: Session) -> int:
    """清理过期的预扣记录，自动退还"""
    expired = db.query(PointReserve).filter(
        PointReserve.status == "reserved",
        PointReserve.expire_time < datetime.now()
    ).all()

    count = 0
    for reserve in expired:
        if refund_points(db, reserve.deduction_id, "预扣超时自动退还"):
            count += 1

    return count


# ============ 模型配置相关 ============
def get_all_models(db: Session, enabled_only: bool = False) -> List[AIModel]:
    query = db.query(AIModel)
    if enabled_only:
        query = query.filter(AIModel.is_enabled == True)
    return query.order_by(AIModel.sort_order, AIModel.id).all()


def get_model_by_id(db: Session, model_id: str) -> Optional[AIModel]:
    return db.query(AIModel).filter(AIModel.model_id == model_id).first()


def get_model_by_pk(db: Session, pk: int) -> Optional[AIModel]:
    return db.query(AIModel).filter(AIModel.id == pk).first()


def create_model(db: Session, model_data: dict) -> AIModel:
    pricing_rules = model_data.pop("pricing_rules", [])

    model = AIModel(**model_data)
    db.add(model)
    db.commit()
    db.refresh(model)

    # 添加计费规则
    for rule_data in pricing_rules:
        rule = ModelPricing(model_id=model.id, **rule_data)
        db.add(rule)

    db.commit()
    db.refresh(model)
    return model


def update_model(db: Session, model_id: int, update_data: dict) -> Optional[AIModel]:
    model = db.query(AIModel).filter(AIModel.id == model_id).first()
    if not model:
        return None

    for key, value in update_data.items():
        if hasattr(model, key) and value is not None:
            setattr(model, key, value)

    db.commit()
    db.refresh(model)
    return model


def delete_model(db: Session, model_id: int) -> bool:
    model = db.query(AIModel).filter(AIModel.id == model_id).first()
    if not model:
        return False

    db.delete(model)
    db.commit()
    return True


def toggle_model(db: Session, model_id: int) -> Optional[AIModel]:
    model = db.query(AIModel).filter(AIModel.id == model_id).first()
    if not model:
        return None

    model.is_enabled = not model.is_enabled
    db.commit()
    db.refresh(model)
    return model


# ============ 计费规则相关 ============
def get_pricing_rules(db: Session, model_id: int) -> List[ModelPricing]:
    return db.query(ModelPricing).filter(
        ModelPricing.model_id == model_id
    ).order_by(ModelPricing.pricing_type, ModelPricing.sort_order).all()


def calculate_cost(db: Session, model_id: str, duration: int = None, resolution: str = None, ratio: str = None, count: int = 1) -> Dict[str, Any]:
    """计算费用 - 使用 config_schema.pricing_rules"""
    model = get_model_by_id(db, model_id)
    if not model:
        return {"error": "模型不存在"}

    # 使用 config_schema 中的 pricing_rules
    if model.config_schema and "pricing_rules" in model.config_schema:
        pricing_rules = model.config_schema["pricing_rules"]
        form_data = {
            "duration": duration,
            "resolution": resolution,
            "aspect_ratio": ratio,
            "count": count
        }
        result = pricing_engine.calculate(pricing_rules, form_data)
        result["model_id"] = model_id
        result["model_name"] = model.display_name
        return result

    # 如果没有配置 pricing_rules，使用基础价格
    total_cost = model.base_price * count
    return {
        "model_id": model_id,
        "model_name": model.display_name,
        "cost": total_cost,
        "breakdown": {
            "base_cost": total_cost,
            "total_cost": total_cost
        },
        "description": model.pricing_description or "未配置计费规则，使用基础价格"
    }


def calculate_cost_dynamic(db: Session, model_id: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    动态计费 - 使用 config_schema.pricing_rules 计算

    Args:
        db: 数据库会话
        model_id: 模型 ID
        form_data: 用户提交的表单数据

    Returns:
        计费结果
    """
    model = get_model_by_id(db, model_id)
    if not model:
        return {"error": "模型不存在", "cost": 0}

    # 使用 config_schema 中的 pricing_rules
    if model.config_schema and "pricing_rules" in model.config_schema:
        pricing_rules = model.config_schema["pricing_rules"]
        result = pricing_engine.calculate(pricing_rules, form_data)
        result["model_id"] = model_id
        result["model_name"] = model.display_name
        return result

    # 如果没有配置 pricing_rules，使用基础价格
    count = form_data.get("count", 1)
    total_cost = model.base_price * count
    return {
        "model_id": model_id,
        "model_name": model.display_name,
        "cost": total_cost,
        "breakdown": {"base_cost": total_cost, "total_cost": total_cost},
        "description": "未配置计费规则，使用基础价格"
    }


# ============ 系统配置相关 ============
def get_config(db: Session, key: str, default: str = None) -> Optional[str]:
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    return config.value if config else default


def set_config(db: Session, key: str, value: str, description: str = None) -> SystemConfig:
    config = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if config:
        config.value = value
        if description:
            config.description = description
    else:
        config = SystemConfig(key=key, value=value, description=description)
        db.add(config)
    db.commit()
    return config


def get_all_configs(db: Session) -> List[SystemConfig]:
    return db.query(SystemConfig).all()


def get_pricing_info(db: Session) -> Dict[str, Any]:
    """获取费用说明信息"""
    configs = get_all_configs(db)
    config_map = {c.key: c.value for c in configs}

    return {
        "signup_bonus": int(config_map.get("signup_bonus", "10")),
        "image_base_price": int(config_map.get("image_base_price", "2")),
        "pricing_description": config_map.get("pricing_description", ""),
        "tencent_function_url": config_map.get("tencent_function_url", ""),
        # 三个系统提示词配置
        "image_selling_points_prompt": config_map.get("image_selling_points_prompt", ""),
        "image_generation_prompt": config_map.get("image_generation_prompt", ""),
        "video_script_prompt": config_map.get("video_script_prompt", "")
    }


# ============ 内容配置相关 ============
def get_content_config(db: Session, key: str) -> Optional[Dict[str, Any]]:
    """获取小类配置"""
    config = db.query(ContentConfig).filter(ContentConfig.key == key).first()
    if config:
        return config.config
    return None


def set_content_config(db: Session, key: str, config: Dict[str, Any], description: str = None) -> ContentConfig:
    """设置小类配置"""
    existing = db.query(ContentConfig).filter(ContentConfig.key == key).first()
    if existing:
        existing.config = config
        if description:
            existing.description = description
    else:
        existing = ContentConfig(key=key, config=config, description=description)
        db.add(existing)
    db.commit()
    db.refresh(existing)
    return existing


def get_all_content_configs(db: Session) -> List[ContentConfig]:
    """获取所有内容配置"""
    return db.query(ContentConfig).all()


# ============ 操作日志相关 ============
def log_operation(
    db: Session,
    user_id: int,
    action: str,
    detail: Dict[str, Any] = None,
    ip_address: str = None,
    user_agent: str = None
) -> OperationLog:
    """
    记录操作日志

    Args:
        user_id: 用户ID
        action: 操作类型 (LOGIN, LOGOUT, POINTS_CHANGE, MODEL_CREATE, CONFIG_UPDATE, RECHARGE, etc.)
        detail: 操作详情
        ip_address: IP地址
        user_agent: 用户代理

    Returns:
        操作日志记录
    """
    log = OperationLog(
        user_id=user_id,
        action=action,
        detail=detail or {},
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def get_operation_logs(
    db: Session,
    user_id: int = None,
    action: str = None,
    page: int = 1,
    page_size: int = 50
) -> tuple:
    """
    获取操作日志列表

    Args:
        user_id: 用户ID（可选，不传则查全部）
        action: 操作类型（可选，不传则查全部）
        page: 页码
        page_size: 每页数量

    Returns:
        (logs, total)
    """
    query = db.query(OperationLog)

    if user_id:
        query = query.filter(OperationLog.user_id == user_id)
    if action:
        query = query.filter(OperationLog.action == action)

    total = query.count()
    logs = query.order_by(OperationLog.create_time.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return logs, total