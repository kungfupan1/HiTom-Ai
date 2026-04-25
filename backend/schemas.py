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
    base_url: str = ""
    endpoint: str = ""
    api_provider: Optional[str] = None
    billing_mode: str = "per_use"  # per_use/duration
    base_price: int = 0
    request_mapping: Optional[Dict[str, Any]] = None
    response_mapping: Optional[Dict[str, Any]] = None
    status_mapping: Optional[Dict[str, Any]] = None
    frontend_config: Optional[Dict[str, Any]] = None
    pricing_description: Optional[str] = None
    pricing_rules: Optional[List[PricingRuleCreate]] = None
    config_schema: Optional[Dict[str, Any]] = None  # 大一统 JSON 配置


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
    config_schema: Optional[Dict[str, Any]] = None  # 大一统 JSON 配置


class AIModelResponse(AIModelBase):
    id: int
    base_url: str
    endpoint: str
    billing_mode: str
    base_price: int
    api_provider: Optional[str] = None
    request_mapping: Optional[Dict[str, Any]] = None
    response_mapping: Optional[Dict[str, Any]] = None
    status_mapping: Optional[Dict[str, Any]] = None
    frontend_config: Optional[Dict[str, Any]] = None
    pricing_description: Optional[str] = None
    config_schema: Optional[Dict[str, Any]] = None  # 大一统 JSON 配置
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
    api_provider: Optional[str] = None
    pricing_description: Optional[str] = None
    config_schema: Optional[Dict[str, Any]] = None  # 大一统 JSON 配置

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
    base_cost: int = 0
    duration_cost: int = 0
    resolution_cost: int = 0
    ratio_cost: int = 0
    total_cost: Optional[int] = None
    total: Optional[int] = None  # 新增，兼容 pricing_engine


class CalculateCostResponse(BaseModel):
    model_id: str
    model_name: str
    cost: int
    breakdown: CostBreakdown
    description: str


# ============ 动态计费计算相关 ============
class DynamicCalculateCostRequest(BaseModel):
    """动态计费请求 - 支持任意表单字段"""
    model_id: str
    form_data: Dict[str, Any]  # 用户提交的表单数据


class DynamicCostBreakdown(BaseModel):
    """动态费用明细"""
    total: int
    duration_cost: Optional[int] = None
    resolution_cost: Optional[int] = None
    ratio_cost: Optional[int] = None
    base_cost: Optional[int] = None
    multiply_cost: Optional[int] = None


class DynamicCalculateCostResponse(BaseModel):
    """动态计费响应"""
    model_id: str
    model_name: Optional[str] = None
    cost: int
    breakdown: DynamicCostBreakdown
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


class ContentConfigUpdate(BaseModel):
    config: Dict[str, Any]


class ContentConfigResponse(BaseModel):
    key: str
    config: Dict[str, Any]
    description: Optional[str] = None
    update_time: datetime

    class Config:
        from_attributes = True


# ============ 任务提交相关（双轨制新增）============
class TaskSubmitRequest(BaseModel):
    """任务提交请求"""
    model_id: str
    prompt: Optional[str] = None
    images: Optional[List[str]] = None
    params: Optional[Dict[str, Any]] = None


class TaskSubmitResponse(BaseModel):
    """任务提交响应"""
    success: bool
    use_cloud_function: bool = True  # True=走云函数，False=后端直接调用
    task_id: Optional[str] = None
    deduction_id: Optional[str] = None
    estimated_time: Optional[int] = None
    cost_points: Optional[int] = None
    tencent_function_url: Optional[str] = None  # 云函数模式时返回
    model_info: Optional[Dict[str, Any]] = None  # 云函数模式时返回模型配置
    error: Optional[str] = None
    error_code: Optional[str] = None


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    success: bool
    task: Optional[Dict[str, Any]] = None
    refunded: Optional[bool] = None  # 是否已自动退款
    message: Optional[str] = None
    error: Optional[str] = None


class TaskConfirmResponse(BaseModel):
    """任务确认响应"""
    success: bool
    message: Optional[str] = None


class TaskRefundResponse(BaseModel):
    """任务退款响应"""
    success: bool
    refunded_amount: Optional[int] = None
    message: Optional[str] = None