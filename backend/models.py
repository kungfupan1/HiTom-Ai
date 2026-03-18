"""
数据库模型定义
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    points = Column(Integer, default=0)
    is_active = Column(Integer, default=1)  # 1=正常, 0=封号
    role = Column(String(20), default="user")  # user/admin
    create_time = Column(DateTime, default=datetime.now)


class PointLog(Base):
    """积分流水表"""
    __tablename__ = "point_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    change_type = Column(String(20), nullable=False)  # RECHARGE/CONSUME/BONUS/REFUND/RESERVE
    amount = Column(Integer, nullable=False)
    balance_after = Column(Integer, default=0)  # 变动后余额
    description = Column(String(255))
    deduction_id = Column(String(50), index=True)  # 关联的扣费ID
    status = Column(String(20), default="confirmed")  # reserved/confirmed/refunded
    create_time = Column(DateTime, default=datetime.now)


class AIModel(Base):
    """AI 模型配置表"""
    __tablename__ = "ai_models"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(String(50), unique=True, nullable=False)  # sora-2, grok-video-3
    display_name = Column(String(100), nullable=False)  # Sora-2 标准版
    model_type = Column(String(20), nullable=False)  # video/image/text
    is_enabled = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    # API 配置
    base_url = Column(String(255), nullable=False)
    endpoint = Column(String(255), nullable=False)  # /v2/videos/generations
    api_provider = Column(String(50))  # t8star, modelScope

    # 计费配置
    billing_mode = Column(String(20), default="per_use")  # per_use/duration
    base_price = Column(Integer, default=0)  # 基础价格（按次计费时使用）

    # 参数映射（JSON格式）
    request_mapping = Column(JSON)  # 前端参数 -> API参数映射
    response_mapping = Column(JSON)  # 响应解析规则
    status_mapping = Column(JSON)  # 状态枚举映射

    # 前端展示配置
    frontend_config = Column(JSON)  # 前端下拉选项等

    # 费用说明
    pricing_description = Column(Text)  # 展示给用户的费用说明

    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 关联计费规则
    pricing_rules = relationship("ModelPricing", back_populates="model", cascade="all, delete-orphan")


class ModelPricing(Base):
    """模型计费规则表"""
    __tablename__ = "model_pricing"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("ai_models.id"), nullable=False)
    pricing_type = Column(String(20), nullable=False)  # duration/resolution/ratio/other
    pricing_key = Column(String(50), nullable=False)  # 5, 10, 720P, 1080P, 9:16 等
    price = Column(Integer, nullable=False)  # 积分
    is_available = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    model = relationship("AIModel", back_populates="pricing_rules")


class SystemConfig(Base):
    """系统配置表"""
    __tablename__ = "system_config"

    key = Column(String(50), primary_key=True)
    value = Column(Text)
    description = Column(String(255))
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class APILog(Base):
    """API 调用日志表"""
    __tablename__ = "api_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    task_type = Column(String(20))  # image/video/text
    model_id = Column(String(50))
    status = Column(String(20))  # SUCCESS/FAILURE/PENDING
    cost_points = Column(Integer, default=0)
    deduction_id = Column(String(50))
    task_id = Column(String(100))  # AI 服务商返回的 task_id
    create_time = Column(DateTime, default=datetime.now)


class PointReserve(Base):
    """积分预扣表"""
    __tablename__ = "point_reserves"

    id = Column(Integer, primary_key=True, index=True)
    deduction_id = Column(String(50), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)
    model_id = Column(String(50))
    status = Column(String(20), default="reserved")  # reserved/confirmed/refunded
    expire_time = Column(DateTime)  # 过期时间（超时自动退还）
    create_time = Column(DateTime, default=datetime.now)