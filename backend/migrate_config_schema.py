"""
数据库迁移脚本：添加 config_schema 字段并导入初始模型配置
"""
import json
import sys
import io
import os
from sqlalchemy import text
from database import engine, get_db
import models
import crud

# 设置标准输出编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def migrate():
    """执行数据库迁移"""
    print("开始数据库迁移...")

    # 1. 检查并添加 config_schema 列
    try:
        with engine.connect() as conn:
            # 检查列是否存在
            result = conn.execute(text("PRAGMA table_info(ai_models)"))
            columns = [row[1] for row in result.fetchall()]

            if 'config_schema' not in columns:
                print("添加 config_schema 列...")
                conn.execute(text("ALTER TABLE ai_models ADD COLUMN config_schema TEXT"))
                conn.commit()
                print("[OK] config_schema 列添加成功")
            else:
                print("[OK] config_schema 列已存在")
    except Exception as e:
        print(f"迁移列时出错: {e}")

    # 2. 创建表（如果不存在）
    models.Base.metadata.create_all(bind=engine)
    print("[OK] 数据库表检查完成")

    # 3. 导入初始模型配置
    db = next(get_db())

    # 读取 JSON 配置文件
    configs = [
        {
            "file": "modelVideoConfigDemo.json",
            "name": "Grok Video 3.0"
        },
        {
            "file": "modelTextConfigDemo.json",
            "name": "Qwen3-VL 看图写文案"
        },
        {
            "file": "modelPictureDemo.json",
            "name": "商品图生成"
        }
    ]

    for config_info in configs:
        try:
            config_path = os.path.join(PROJECT_ROOT, config_info["file"])
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            model_id = config.get("model_info", {}).get("model_id")
            if not model_id:
                print(f"[SKIP] {config_info['file']} 缺少 model_id")
                continue

            # 检查是否已存在
            existing = crud.get_model_by_id(db, model_id)
            if existing:
                print(f"[OK] 模型 {model_id} 已存在，跳过")
                continue

            # 创建模型
            model_data = {
                "model_id": model_id,
                "display_name": config.get("model_info", {}).get("display_name", config_info["name"]),
                "model_type": config.get("model_info", {}).get("model_type", "video"),
                "is_enabled": True,
                "sort_order": 0,
                "base_url": "",
                "endpoint": "",
                "api_provider": config.get("model_info", {}).get("provider", ""),
                "billing_mode": "per_use" if config.get("pricing_rules", {}).get("mode") == "fixed" else "duration",
                "base_price": config.get("pricing_rules", {}).get("fixed_cost", 0),
                "config_schema": config
            }

            # 解析 URL
            endpoint_url = config.get("api_contract", {}).get("endpoint_url", "")
            if endpoint_url:
                try:
                    from urllib.parse import urlparse
                    parsed = urlparse(endpoint_url)
                    model_data["base_url"] = f"{parsed.scheme}://{parsed.netloc}"
                    model_data["endpoint"] = parsed.path
                except:
                    pass

            crud.create_model(db, model_data)
            print(f"[OK] 模型 {model_id} 导入成功")

        except FileNotFoundError:
            print(f"[SKIP] 配置文件 {config_info['file']} 不存在")
        except Exception as e:
            print(f"[ERROR] 导入 {config_info['file']} 失败: {e}")

    # 4. 添加 Sora-2 配置（示例，未调通）
    sora_config = {
        "model_info": {
            "model_id": "sora-2",
            "display_name": "Sora 2.0 (标准版)",
            "model_type": "video",
            "provider": "T8Star",
            "description": "OpenAI 官方 Sora 视频生成大模型"
        },
        "api_contract": {
            "endpoint_url": "https://ai.t8star.cn/v2/videos/generations",
            "status_url": "https://ai.t8star.cn/v2/videos/generations/{task_id}",
            "placeholder": "T8STAR_API_KEY",
            "method": "POST",
            "status_method": "GET",
            "timeout": 180000
        },
        "pricing_rules": {
            "mode": "dynamic",
            "unit_price": 2,
            "multiply_by_field": "duration",
            "duration_pricing": {"4": 2, "8": 2, "12": 5},
            "resolution_pricing": {"720P": 0, "1080P": 2}
        },
        "ui_schema": [
            {"field_name": "aspect_ratio", "label": "画面比例", "ui_type": "select", "options": [{"label": "9:16", "value": "9:16"}, {"label": "16:9", "value": "16:9"}], "default_value": "9:16"},
            {"field_name": "duration", "label": "时长(秒)", "ui_type": "select", "options": [{"label": "4秒", "value": 4}, {"label": "8秒", "value": 8}, {"label": "12秒", "value": 12}], "default_value": 8}
        ],
        "request_mapping": {
            "dynamic_params": {"model": "model", "prompt": "prompt", "duration": "duration", "aspect_ratio": "aspect_ratio"},
            "static_params": {"private": True}
        },
        "response_mapping": {
            "task_id_path": "task_id",
            "status_path": "status",
            "progress_path": "progress",
            "result_url_path": "data.output",
            "error_path": "fail_reason"
        }
    }

    existing_sora = crud.get_model_by_id(db, "sora-2")
    if not existing_sora:
        model_data = {
            "model_id": "sora-2",
            "display_name": "Sora 2.0 (标准版)",
            "model_type": "video",
            "is_enabled": True,
            "sort_order": 0,
            "base_url": "https://ai.t8star.cn",
            "endpoint": "/v2/videos/generations",
            "api_provider": "t8star",
            "billing_mode": "duration",
            "base_price": 0,
            "config_schema": sora_config
        }
        crud.create_model(db, model_data)
        print("[OK] 模型 sora-2 导入成功 (待调通)")

    print("\n[DONE] 数据库迁移完成！")

if __name__ == "__main__":
    migrate()