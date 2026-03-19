"""
CRUD 操作
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
import uuid
import json

from models import User, AIModel, ModelPricing, SystemConfig, PointLog, PointReserve, APILog, APIKey


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
def reserve_points(db: Session, user_id: int, amount: int, model_id: str, expire_seconds: int = 600) -> Optional[PointReserve]:
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
    """计算费用"""
    model = get_model_by_id(db, model_id)
    if not model:
        return {"error": "模型不存在"}

    base_cost = model.base_price
    duration_cost = 0
    resolution_cost = 0
    ratio_cost = 0

    # 获取计费规则
    pricing_rules = get_pricing_rules(db, model.id)
    pricing_map = {}
    for rule in pricing_rules:
        key = f"{rule.pricing_type}_{rule.pricing_key}"
        pricing_map[key] = rule.price

    # 计算时长费用
    if duration and model.billing_mode == "duration":
        duration_cost = pricing_map.get(f"duration_{duration}", 0)
        base_cost = 0  # 按时长计费时，基础费用为0

    # 计算分辨率加价
    if resolution:
        resolution_cost = pricing_map.get(f"resolution_{resolution}", 0)

    # 计算比例加价
    if ratio:
        ratio_cost = pricing_map.get(f"ratio_{ratio}", 0)

    total_cost = (base_cost + duration_cost + resolution_cost + ratio_cost) * count

    return {
        "model_id": model_id,
        "model_name": model.display_name,
        "cost": total_cost,
        "breakdown": {
            "base_cost": base_cost * count,
            "duration_cost": duration_cost * count,
            "resolution_cost": resolution_cost * count,
            "ratio_cost": ratio_cost * count,
            "total_cost": total_cost
        },
        "description": model.pricing_description or ""
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
        "tencent_function_url": config_map.get("tencent_function_url", "")
    }


# ============ API Key 相关 ============
def get_all_api_keys(db: Session, provider: str = None) -> List[APIKey]:
    """获取所有 API Key"""
    query = db.query(APIKey)
    if provider:
        query = query.filter(APIKey.provider == provider)
    return query.order_by(APIKey.provider, APIKey.id).all()


def get_api_key_by_id(db: Session, key_id: int) -> Optional[APIKey]:
    """根据 ID 获取 API Key"""
    return db.query(APIKey).filter(APIKey.id == key_id).first()


def create_api_key(db: Session, key_name: str, key_value: str, provider: str, description: str = None) -> APIKey:
    """创建 API Key"""
    api_key = APIKey(
        key_name=key_name,
        key_value=key_value,
        provider=provider,
        description=description
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key


def update_api_key(db: Session, key_id: int, key_value: str = None, is_enabled: bool = None, description: str = None) -> Optional[APIKey]:
    """更新 API Key"""
    api_key = get_api_key_by_id(db, key_id)
    if not api_key:
        return None

    if key_value is not None:
        api_key.key_value = key_value
    if is_enabled is not None:
        api_key.is_enabled = is_enabled
    if description is not None:
        api_key.description = description

    db.commit()
    db.refresh(api_key)
    return api_key


def delete_api_key(db: Session, key_id: int) -> bool:
    """删除 API Key"""
    api_key = get_api_key_by_id(db, key_id)
    if not api_key:
        return False

    db.delete(api_key)
    db.commit()
    return True


def get_random_api_key(db: Session, provider: str) -> Optional[str]:
    """随机获取一个可用的 API Key（负载均衡/薅羊毛策略）"""
    import random
    keys = db.query(APIKey).filter(
        APIKey.provider == provider,
        APIKey.is_enabled == True
    ).all()

    if not keys:
        return None

    # 随机选择一个
    selected = random.choice(keys)

    # 更新使用统计
    selected.use_count += 1
    selected.last_used_time = datetime.now()
    db.commit()

    return selected.key_value


def get_api_key_by_name(db: Session, key_name: str) -> Optional[APIKey]:
    """根据名称获取 API Key"""
    return db.query(APIKey).filter(APIKey.key_name == key_name).first()