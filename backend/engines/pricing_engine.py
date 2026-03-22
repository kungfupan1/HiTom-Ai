"""
动态计费引擎
简化版：支持两种模式
- fixed: 固定价格模式，使用 fixed_price
- dynamic: 动态加价模式，使用 base_price + add_price
"""
from typing import Dict, Any


class PricingEngine:
    """动态计费引擎 - 根据 pricing_rules 配置计算费用"""

    def calculate(self, pricing_rules: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算费用

        Args:
            pricing_rules: 从 config_schema.pricing_rules 获取
            form_data: 用户提交的表单数据

        Returns:
            {
                "cost": int,  # 总费用
                "breakdown": dict,  # 费用明细
                "description": str  # 费用说明
            }
        """
        if not pricing_rules:
            return {"cost": 0, "breakdown": {}, "description": "未配置计费规则"}

        mode = pricing_rules.get("mode", "fixed")

        if mode == "fixed":
            return self._calculate_fixed(pricing_rules, form_data)
        elif mode == "dynamic":
            return self._calculate_dynamic(pricing_rules, form_data)
        else:
            # 兼容旧模式名，统一按 fixed 处理
            return self._calculate_fixed(pricing_rules, form_data)

    def _calculate_fixed(self, pricing_rules: Dict, form_data: Dict) -> Dict[str, Any]:
        """
        固定价格模式 - 使用 fixed_price

        示例配置:
        {
            "mode": "fixed",
            "fixed_price": 5
        }

        计算: fixed_price × count
        """
        # 读取固定价格
        fixed_price = pricing_rules.get("fixed_price", 0)

        # 数量字段：支持 count, num_images
        count = form_data.get("count") or form_data.get("num_images", 1)

        total = fixed_price * count

        return {
            "cost": total,
            "breakdown": {
                "fixed_price": fixed_price,
                "count": count,
                "total": total
            },
            "description": f"固定价格 {fixed_price} 积分/次，共 {count} 次，总计 {total} 积分"
        }

    def _calculate_dynamic(self, pricing_rules: Dict, form_data: Dict) -> Dict[str, Any]:
        """
        动态加价模式 - 使用 base_price + add_price

        示例配置:
        {
            "mode": "dynamic",
            "base_price": 5,
            "add_price": {
                "duration": {"5": 0, "10": 2, "15": 5},
                "resolution": {"480P": 0, "720P": 2, "1080P": 5},
                "aspect_ratio": {"16:9": 0, "9:16": 1}
            }
        }

        计算: (base_price + add_price.duration + add_price.resolution + add_price.aspect_ratio) × count
        """
        breakdown = {}
        descriptions = []

        # 1. 基础价格
        base_price = pricing_rules.get("base_price", 0)
        unit_cost = base_price  # 单次费用
        if base_price > 0:
            breakdown["base_price"] = base_price
            descriptions.append(f"基础费用: {base_price} 积分")

        # 2. 叠加费用
        add_price = pricing_rules.get("add_price", {})

        # 2.1 时长加价
        if "duration" in add_price and "duration" in form_data:
            duration = str(form_data.get("duration", ""))
            duration_add = add_price["duration"].get(duration, 0)
            if duration_add > 0:
                unit_cost += duration_add
                breakdown["duration_add"] = duration_add
                descriptions.append(f"时长 {duration}秒: +{duration_add} 积分")

        # 2.2 分辨率加价
        if "resolution" in add_price and "resolution" in form_data:
            resolution = form_data.get("resolution", "")
            resolution_add = add_price["resolution"].get(resolution, 0)
            if resolution_add > 0:
                unit_cost += resolution_add
                breakdown["resolution_add"] = resolution_add
                descriptions.append(f"分辨率 {resolution}: +{resolution_add} 积分")

        # 2.3 比例加价
        if "aspect_ratio" in add_price and "aspect_ratio" in form_data:
            aspect_ratio = form_data.get("aspect_ratio", "")
            ratio_add = add_price["aspect_ratio"].get(aspect_ratio, 0)
            if ratio_add > 0:
                unit_cost += ratio_add
                breakdown["ratio_add"] = ratio_add
                descriptions.append(f"比例 {aspect_ratio}: +{ratio_add} 积分")

        # 3. 数量乘算
        count = form_data.get("count", 1)
        total = unit_cost * count

        breakdown["unit_cost"] = unit_cost
        breakdown["count"] = count
        breakdown["total"] = total

        if count > 1:
            return {
                "cost": total,
                "breakdown": breakdown,
                "description": f"单价 {unit_cost} 积分 × {count} 次 = {total} 积分"
            }
        else:
            return {
                "cost": total,
                "breakdown": breakdown,
                "description": " | ".join(descriptions) if descriptions else f"基础费用: {base_price} 积分"
            }

    def get_pricing_preview(self, pricing_rules: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取计费预览信息（用于前端展示）
        """
        if not pricing_rules:
            return {"available": False, "message": "未配置计费规则"}

        mode = pricing_rules.get("mode", "fixed")
        preview = {"mode": mode, "available": True}

        if mode == "fixed":
            preview["fixed_price"] = pricing_rules.get("fixed_price", 0)
            preview["description"] = f"固定价格 {preview['fixed_price']} 积分/次"

        elif mode == "dynamic":
            preview["base_price"] = pricing_rules.get("base_price", 0)
            preview["add_price"] = pricing_rules.get("add_price", {})
            preview["description"] = f"基础费用 {preview['base_price']} 积分起"

        return preview


# 单例实例
pricing_engine = PricingEngine()