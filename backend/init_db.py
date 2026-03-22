"""
初始化数据库和默认数据
运行方式：python init_db.py
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from database import engine, SessionLocal
from models import Base, AIModel, SystemConfig

# 创建表
Base.metadata.create_all(bind=engine)
print("[OK] 数据库表已创建")

db = SessionLocal()

# 检查是否已有数据
if db.query(AIModel).count() > 0:
    print("[WARN] 数据库已有数据，跳过初始化")
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
    config_schema={
        "api_contract": {
            "endpoint_url": "https://ai.t8star.cn/v2/videos/generations",
            "status_url": "https://ai.t8star.cn/v2/videos/generations/{task_id}",
            "status_method": "GET",
            "timeout": 180000
        },
        "request_mapping": {
            "static_params": {"private": True},
            "dynamic_params": {
                "model": "model",
                "prompt": "prompt",
                "duration": "duration",
                "ratio": "aspect_ratio",
                "resolution": "hd",
                "images": "images"
            },
            "value_transformations": {
                "resolution": {
                    "target_field": "hd",
                    "transform": "resolution === '1080P'"
                }
            }
        },
        "response_mapping": {
            "task_id_path": "task_id",
            "status_path": "status",
            "result_url_path": "data.output[0].url"
        },
        "pricing_rules": {
            "mode": "dynamic",
            "duration_pricing": {"5": 2, "10": 2, "15": 5, "25": 25},
            "resolution_pricing": {"720P": 0, "1080P": 2}
        }
    },
    pricing_description="Sora-2 视频生成：\n5-10秒：2积分 | 15秒：5积分 | 25秒：25积分\n高清(1080P)：额外+2积分"
)
db.add(sora2)

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
    config_schema={
        "pricing_rules": {
            "mode": "dynamic",
            "duration_pricing": {"5": 3, "10": 3, "15": 8, "25": 35},
            "resolution_pricing": {"720P": 0, "1080P": 3}
        }
    },
    pricing_description="Sora-2 Pro 视频生成：\n5-10秒：3积分 | 15秒：8积分 | 25秒：35积分\n高清(1080P)：额外+3积分"
)
db.add(sora2pro)

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
    config_schema={
        "pricing_rules": {
            "mode": "dynamic",
            "duration_pricing": {"5": 3, "10": 3, "15": 8},
            "resolution_pricing": {"720P": 0, "1080P": 3}
        }
    },
    pricing_description="Grok Video 3 视频生成：\n5-10秒：3积分 | 15秒：8积分\n高清(1080P)：额外+3积分"
)
db.add(grok3)

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
    config_schema={
        "pricing_rules": {
            "mode": "dynamic",
            "unit_price": 2,
            "resolution_pricing": {"1K": 0, "2K": 1, "4K": 3}
        }
    },
    pricing_description="图片生成：2积分/张\n2K：+1积分 | 4K：+3积分"
)
db.add(nanobanana)

print("[OK] 默认模型已添加")

# ============ 添加系统配置 ============
configs = [
    SystemConfig(key="signup_bonus", value="0", description="注册赠送积分"),
    SystemConfig(key="tencent_function_url", value="https://1307708790-dpjcghai7x.ap-guangzhou.tencentscf.com", description="腾讯云函数URL"),
]
db.add_all(configs)

print("[OK] 系统配置已添加")

# ============ 添加管理员账号 ============
from utils import hash_password
from models import User

# 注意：管理员密码建议在系统上线后立即修改！
# 默认密码 admin123 仅用于首次初始化
# 可以通过管理后台或用户页面的「修改密码」功能更改
admin = User(
    username="admin",
    # 默认密码: admin123 (请在生产环境中修改)
    password_hash=hash_password("admin123"),  # TODO: 生产环境请修改此密码
    points=999999,
    role="admin"
)
db.add(admin)

print("[OK] 管理员账号已添加 (admin / admin123)")
print("[WARN] 请在生产环境中及时修改默认密码！")

db.commit()
db.close()

print("\n[DONE] 数据库初始化完成！")