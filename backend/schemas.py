"""
Pydantic 数据验证模型
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


# ============ 用户相关 ============
class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int
    points: int
    is_active: int
    role: str
    create_time: datetime

    class Config:
        from_attributes = True


# ============ 模型配置相关 ============
class PricingRuleBase(BaseModel):
    pricing_type: str  # duration/resolution/ratio/other
    pricing_key: str
    price: int
    is_available: bool = True
    sort_order: int = 0


class PricingRuleCreate(PricingRuleBase):
    pass


class PricingRuleResponse(PricingRuleBase):
    id: int
    model_id: int

    class Config:
        from_attributes = True


class AIModelBase(BaseModel):
    model_id: str
    display_name: str
    model_type: str  # video/image/text
    is_enabled: bool = True
    sort_order: int = 0


class AIModelCreate(AIModelBase):
    base_url: str
    endpoint: str
    api_provider: Optional[str] = None
    billing_mode: str = "per_use"  # per_use/duration
    base_price: int = 0
    request_mapping: Optional[Dict[str, Any]] = None
    response_mapping: Optional[Dict[str, Any]] = None
    status_mapping: Optional[Dict[str, Any]] = None
    frontend_config: Optional[Dict[str, Any]] = None
    pricing_description: Optional[str] = None
    pricing_rules: Optional[List[PricingRuleCreate]] = None


class AIModelUpdate(BaseModel):
    display_name: Optional[str] = None
    is_enabled: Optional[bool] = None
    sort_order: Optional[int] = None
    base_url: Optional[str] = None
    endpoint: Optional[str] = None
    billing_mode: Optional[str] = None
    base_price: Optional[int] = None
    request_mapping: Optional[Dict[str, Any]] = None
    response_mapping: Optional[Dict[str, Any]] = None
    status_mapping: Optional[Dict[str, Any]] = None
    frontend_config: Optional[Dict[str, Any]] = None
    pricing_description: Optional[str] = None


class AIModelResponse(AIModelBase):
    id: int
    base_url: str
    endpoint: str
    billing_mode: str
    base_price: int
    request_mapping: Optional[Dict[str, Any]] = None
    response_mapping: Optional[Dict[str, Any]] = None
    status_mapping: Optional[Dict[str, Any]] = None
    frontend_config: Optional[Dict[str, Any]] = None
    pricing_description: Optional[str] = None
    pricing_rules: List[PricingRuleResponse] = []
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True


class AIModelListItem(BaseModel):
    """模型列表项（简化版）"""
    id: int
    model_id: str
    display_name: str
    model_type: str
    is_enabled: bool
    billing_mode: str
    base_price: int
    pricing_description: Optional[str] = None

    class Config:
        from_attributes = True


# ============ 计费计算相关 ============
class CalculateCostRequest(BaseModel):
    model_id: str
    duration: Optional[int] = None  # 视频时长
    resolution: Optional[str] = None  # 分辨率
    ratio: Optional[str] = None  # 比例
    count: Optional[int] = 1  # 数量（图片）


class CostBreakdown(BaseModel):
    base_cost: int
    duration_cost: int = 0
    resolution_cost: int = 0
    ratio_cost: int = 0
    total_cost: int


class CalculateCostResponse(BaseModel):
    model_id: str
    model_name: str
    cost: int
    breakdown: CostBreakdown
    description: str


# ============ 积分相关 ============
class PointReserveRequest(BaseModel):
    amount: int
    model_id: str
    description: Optional[str] = None


class PointReserveResponse(BaseModel):
    deduction_id: str
    amount: int
    balance_before: int
    balance_after: int
    expire_seconds: int


class PointConfirmRequest(BaseModel):
    deduction_id: str


class PointRefundRequest(BaseModel):
    deduction_id: str
    reason: Optional[str] = None


# ============ 系统配置相关 ============
class SystemConfigUpdate(BaseModel):
    configs: Dict[str, str]


class SystemConfigResponse(BaseModel):
    key: str
    value: str
    description: Optional[str] = None

    class Config:
        from_attributes = True


# ============ 通用响应 ============
class MessageResponse(BaseModel):
    status: str
    message: str


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    detail: Optional[str] = None


# ============ API Key 相关 ============
class APIKeyCreate(BaseModel):
    key_name: str
    key_value: str
    provider: str  # t8star, modelscope
    description: Optional[str] = None


class APIKeyUpdate(BaseModel):
    key_value: Optional[str] = None
    is_enabled: Optional[bool] = None
    description: Optional[str] = None


class APIKeyResponse(BaseModel):
    id: int
    key_name: str
    key_value: str  # 返回时会被掩码处理
    provider: str
    is_enabled: bool
    description: Optional[str] = None
    use_count: int = 0
    last_used_time: Optional[datetime] = None
    create_time: datetime
    update_time: datetime

    class Config:
        from_attributes = True