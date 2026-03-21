"""
迁移计费规则：从 ModelPricing 表迁移到 config_schema.pricing_rules

运行方式：cd backend && python migrate_pricing_to_config.py
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from database import SessionLocal
from models import AIModel, ModelPricing

def migrate_pricing_to_config():
    db = SessionLocal()

    try:
        # 获取所有模型
        models = db.query(AIModel).all()

        for model in models:
            # 获取该模型的所有计费规则
            pricing_rules = db.query(ModelPricing).filter(
                ModelPricing.model_id == model.id
            ).all()

            if not pricing_rules:
                print(f"[SKIP] 模型 {model.model_id} 没有计费规则")
                continue

            # 构建 pricing_rules 结构
            duration_pricing = {}
            resolution_pricing = {}
            ratio_pricing = {}

            for rule in pricing_rules:
                if rule.pricing_type == "duration":
                    duration_pricing[rule.pricing_key] = rule.price
                elif rule.pricing_type == "resolution":
                    resolution_pricing[rule.pricing_key] = rule.price
                elif rule.pricing_type == "ratio":
                    ratio_pricing[rule.pricing_key] = rule.price

            # 构建 config_schema.pricing_rules
            new_pricing_rules = {
                "mode": "dynamic",
                "unit_price": model.base_price if model.billing_mode == "per_use" else 0,
                "duration_pricing": duration_pricing if duration_pricing else None,
                "resolution_pricing": resolution_pricing if resolution_pricing else None,
                "ratio_pricing": ratio_pricing if ratio_pricing else None,
            }

            # 移除空值
            new_pricing_rules = {k: v for k, v in new_pricing_rules.items() if v is not None or k in ["mode", "unit_price"]}

            # 更新或创建 config_schema
            if model.config_schema is None:
                model.config_schema = {}

            model.config_schema["pricing_rules"] = new_pricing_rules

            print(f"[OK] 迁移模型 {model.model_id}: {new_pricing_rules}")

        db.commit()
        print("\n[DONE] 计费规则迁移完成！")

    except Exception as e:
        db.rollback()
        print(f"[ERROR] 迁移失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_pricing_to_config()