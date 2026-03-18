"""
初始化数据库和默认数据
运行方式：python init_db.py
"""
from database import engine, SessionLocal
from models import Base, AIModel, ModelPricing, SystemConfig

# 创建表
Base.metadata.create_all(bind=engine)
print("✅ 数据库表已创建")

db = SessionLocal()

# 检查是否已有数据
if db.query(AIModel).count() > 0:
    print("⚠️ 数据库已有数据，跳过初始化")
    db.close()
    exit(0)

# ============ 添加默认模型 ============

# Sora-2 模型
sora2 = AIModel(
    model_id="sora-2",
    display_name="Sora-2 标准版",
    model_type="video",
    is_enabled=True,
    sort_order=1,
    base_url="https://ai.t8star.cn",
    endpoint="/v2/videos/generations",
    api_provider="t8star",
    billing_mode="duration",
    base_price=0,
    request_mapping={
        "model": "{model}",
        "prompt": "{prompt}",
        "aspect_ratio": "{ratio}",
        "duration": "{duration}",
        "hd": "{hd}",
        "private": True,
        "images": "{images}"
    },
    response_mapping={
        "task_id": "$.task_id",
        "status": "$.status",
        "video_url": "$.data.output"
    },
    status_mapping={
        "success": "SUCCESS",
        "failure": "FAILURE",
        "processing": "processing"
    },
    frontend_config={
        "durations": [5, 10, 15, 25],
        "ratios": ["9:16", "16:9", "1:1"],
        "resolutions": [{"value": "720P", "label": "标清"}, {"value": "1080P", "label": "高清"}]
    },
    pricing_description="Sora-2 视频生成：\n5-10秒：2积分 | 15秒：5积分 | 25秒：25积分\n高清(1080P)：额外+2积分"
)
db.add(sora2)
db.commit()
db.refresh(sora2)

# Sora-2 计费规则
sora2_pricing = [
    ModelPricing(model_id=sora2.id, pricing_type="duration", pricing_key="5", price=2, sort_order=1),
    ModelPricing(model_id=sora2.id, pricing_type="duration", pricing_key="10", price=2, sort_order=2),
    ModelPricing(model_id=sora2.id, pricing_type="duration", pricing_key="15", price=5, sort_order=3),
    ModelPricing(model_id=sora2.id, pricing_type="duration", pricing_key="25", price=25, sort_order=4),
    ModelPricing(model_id=sora2.id, pricing_type="resolution", pricing_key="720P", price=0, sort_order=1),
    ModelPricing(model_id=sora2.id, pricing_type="resolution", pricing_key="1080P", price=2, sort_order=2),
]
db.add_all(sora2_pricing)

# Sora-2 Pro 模型
sora2pro = AIModel(
    model_id="sora-2-pro",
    display_name="Sora-2 Pro 专业版",
    model_type="video",
    is_enabled=True,
    sort_order=2,
    base_url="https://ai.t8star.cn",
    endpoint="/v2/videos/generations",
    api_provider="t8star",
    billing_mode="duration",
    base_price=0,
    request_mapping={
        "model": "{model}",
        "prompt": "{prompt}",
        "aspect_ratio": "{ratio}",
        "duration": "{duration}",
        "hd": "{hd}",
        "private": True,
        "images": "{images}"
    },
    response_mapping={
        "task_id": "$.task_id",
        "status": "$.status",
        "video_url": "$.data.output"
    },
    status_mapping={
        "success": "SUCCESS",
        "failure": "FAILURE",
        "processing": "processing"
    },
    frontend_config={
        "durations": [5, 10, 15, 25],
        "ratios": ["9:16", "16:9", "1:1"],
        "resolutions": [{"value": "720P", "label": "标清"}, {"value": "1080P", "label": "高清"}]
    },
    pricing_description="Sora-2 Pro 视频生成：\n5-10秒：3积分 | 15秒：8积分 | 25秒：35积分\n高清(1080P)：额外+3积分"
)
db.add(sora2pro)
db.commit()
db.refresh(sora2pro)

sora2pro_pricing = [
    ModelPricing(model_id=sora2pro.id, pricing_type="duration", pricing_key="5", price=3, sort_order=1),
    ModelPricing(model_id=sora2pro.id, pricing_type="duration", pricing_key="10", price=3, sort_order=2),
    ModelPricing(model_id=sora2pro.id, pricing_type="duration", pricing_key="15", price=8, sort_order=3),
    ModelPricing(model_id=sora2pro.id, pricing_type="duration", pricing_key="25", price=35, sort_order=4),
    ModelPricing(model_id=sora2pro.id, pricing_type="resolution", pricing_key="720P", price=0, sort_order=1),
    ModelPricing(model_id=sora2pro.id, pricing_type="resolution", pricing_key="1080P", price=3, sort_order=2),
]
db.add_all(sora2pro_pricing)

# Grok Video 3 模型
grok3 = AIModel(
    model_id="grok-video-3",
    display_name="Grok Video 3",
    model_type="video",
    is_enabled=True,
    sort_order=3,
    base_url="https://ai.t8star.cn",
    endpoint="/v2/videos/generations",
    api_provider="t8star",
    billing_mode="duration",
    base_price=0,
    request_mapping={
        "model": "{model}",
        "prompt": "{prompt}",
        "ratio": "{ratio}",
        "resolution": "{resolution}",
        "duration": "{duration}",
        "images": "{images}"
    },
    response_mapping={
        "task_id": "$.task_id",
        "status": "$.status",
        "video_url": "$.data.output"
    },
    status_mapping={
        "success": "SUCCESS",
        "failure": "FAILURE",
        "processing": "IN_PROGRESS",
        "pending": "NOT_START"
    },
    frontend_config={
        "durations": [5, 10, 15],
        "ratios": ["2:3", "3:2", "1:1"],
        "resolutions": [{"value": "720P", "label": "标清"}, {"value": "1080P", "label": "高清"}]
    },
    pricing_description="Grok Video 3 视频生成：\n5-10秒：3积分 | 15秒：8积分\n高清(1080P)：额外+3积分"
)
db.add(grok3)
db.commit()
db.refresh(grok3)

grok3_pricing = [
    ModelPricing(model_id=grok3.id, pricing_type="duration", pricing_key="5", price=3, sort_order=1),
    ModelPricing(model_id=grok3.id, pricing_type="duration", pricing_key="10", price=3, sort_order=2),
    ModelPricing(model_id=grok3.id, pricing_type="duration", pricing_key="15", price=8, sort_order=3),
    ModelPricing(model_id=grok3.id, pricing_type="resolution", pricing_key="720P", price=0, sort_order=1),
    ModelPricing(model_id=grok3.id, pricing_type="resolution", pricing_key="1080P", price=3, sort_order=2),
]
db.add_all(grok3_pricing)

# Nano Banana 2 图片模型
nanobanana = AIModel(
    model_id="nano-banana-2",
    display_name="Nano Banana 2",
    model_type="image",
    is_enabled=True,
    sort_order=10,
    base_url="https://ai.t8star.cn",
    endpoint="/v1/images/generations",
    api_provider="t8star",
    billing_mode="per_use",
    base_price=2,
    request_mapping={
        "model": "{model}",
        "prompt": "{prompt}",
        "size": "{size}",
        "response_format": "url",
        "image": "{images}"
    },
    response_mapping={
        "image_urls": "$.data[*].url"
    },
    frontend_config={
        "resolutions": [{"value": "1K", "label": "1K"}, {"value": "2K", "label": "2K"}, {"value": "4K", "label": "4K"}],
        "ratios": ["1:1", "3:4", "4:3", "9:16", "16:9"]
    },
    pricing_description="图片生成：2积分/张\n2K：+1积分 | 4K：+3积分"
)
db.add(nanobanana)
db.commit()
db.refresh(nanobanana)

nanobanana_pricing = [
    ModelPricing(model_id=nanobanana.id, pricing_type="resolution", pricing_key="1K", price=0, sort_order=1),
    ModelPricing(model_id=nanobanana.id, pricing_type="resolution", pricing_key="2K", price=1, sort_order=2),
    ModelPricing(model_id=nanobanana.id, pricing_type="resolution", pricing_key="4K", price=3, sort_order=3),
]
db.add_all(nanobanana_pricing)

print("✅ 默认模型已添加")

# ============ 添加系统配置 ============
configs = [
    SystemConfig(key="signup_bonus", value="10", description="注册赠送积分"),
    SystemConfig(key="image_base_price", value="2", description="图片生成基础费用"),
    SystemConfig(key="pricing_description", value="费用说明：\n• 图片生成：2积分/张\n• 视频生成：按时长计费\n• 高清模式：额外加价", description="费用说明展示文字"),
]
db.add_all(configs)

print("✅ 系统配置已添加")

# ============ 添加管理员账号 ============
from utils import hash_password
from models import User

admin = User(
    username="admin",
    password_hash=hash_password("admin123"),
    points=999999,
    role="admin"
)
db.add(admin)

print("✅ 管理员账号已添加 (admin / admin123)")

db.commit()
db.close()

print("\n🎉 数据库初始化完成！")