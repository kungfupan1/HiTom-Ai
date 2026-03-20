"""
动态计费引擎
解析 config_schema.pricing_rules 计算费用
"""
from typing import Dict, Any, Optional, List


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

        mode = pricing_rules.get("mode", "static")

        if mode == "static":
            return self._calculate_static(pricing_rules, form_data)
        elif mode in ("dynamic", "fixed"):
            # fixed 和 dynamic 使用相同的计算逻辑
            return self._calculate_dynamic(pricing_rules, form_data)
        elif mode == "tiered":
            return self._calculate_tiered(pricing_rules, form_data)
        else:
            return {"cost": 0, "breakdown": {}, "description": f"未知计费模式: {mode}"}

    def _calculate_static(self, pricing_rules: Dict, form_data: Dict) -> Dict[str, Any]:
        """静态计费 - 固定费用"""
        base_price = pricing_rules.get("base_price", 0)
        count = form_data.get("count", 1)

        total = base_price * count

        return {
            "cost": total,
            "breakdown": {
                "base_price": base_price,
                "count": count,
                "total": total,
                "total_cost": total  # 兼容旧 schema
            },
            "description": f"固定费用 {base_price} 积分/次，共 {count} 次"
        }

    def _calculate_dynamic(self, pricing_rules: Dict, form_data: Dict) -> Dict[str, Any]:
        """
        动态计费 - 根据参数动态计算
        支持：
        - unit_price: 基础单价
        - multiply_by_field: 按字段值乘算（如 duration）
        - duration_pricing: 时长加价（叠加到基础价格上）
        - resolution_pricing: 分辨率加价
        - ratio_pricing: 比例加价
        """
        breakdown = {}
        total = 0
        descriptions = []

        # 基础单价
        unit_price = pricing_rules.get("unit_price", 0)
        multiply_field = pricing_rules.get("multiply_by_field")

        # 基础费用（如果有 unit_price）
        if unit_price > 0:
            total = unit_price
            breakdown["base_cost"] = unit_price
            descriptions.append(f"基础费用: {unit_price} 积分")

        # 时长加价（叠加到基础价格上）
        duration_pricing = pricing_rules.get("duration_pricing", {})
        if duration_pricing and "duration" in form_data:
            duration = int(form_data.get("duration", 0))
            duration_cost = duration_pricing.get(str(duration), 0)
            if duration_cost > 0:
                breakdown["duration_cost"] = duration_cost
                total += duration_cost
                descriptions.append(f"时长 {duration}秒: +{duration_cost} 积分")

        # 分辨率加价
        resolution_pricing = pricing_rules.get("resolution_pricing", {})
        if resolution_pricing and "resolution" in form_data:
            resolution = form_data.get("resolution")
            resolution_cost = resolution_pricing.get(resolution, 0)
            if resolution_cost > 0:
                breakdown["resolution_cost"] = resolution_cost
                total += resolution_cost
                descriptions.append(f"分辨率 {resolution}: +{resolution_cost} 积分")

        # 比例加价
        ratio_pricing = pricing_rules.get("ratio_pricing", {})
        if ratio_pricing and "aspect_ratio" in form_data:
            ratio = form_data.get("aspect_ratio")
            ratio_cost = ratio_pricing.get(ratio, 0)
            if ratio_cost > 0:
                breakdown["ratio_cost"] = ratio_cost
                total += ratio_cost
                descriptions.append(f"比例 {ratio}: +{ratio_cost} 积分")

        # 按字段乘算（如果没有时长阶梯价且没有基础单价）
        if multiply_field and multiply_field in form_data and not duration_pricing and unit_price == 0:
            multiply_value = int(form_data.get(multiply_field, 1))
            total = pricing_rules.get("base_price", 10) * multiply_value
            breakdown["multiply_cost"] = total
            descriptions.insert(0, f"{multiply_field}={multiply_value}")

        breakdown["total"] = total
        breakdown["total_cost"] = total  # 兼容旧 schema

        return {
            "cost": total,
            "breakdown": breakdown,
            "description": " | ".join(descriptions) if descriptions else "免费"
        }

    def _calculate_tiered(self, pricing_rules: Dict, form_data: Dict) -> Dict[str, Any]:
        """
        阶梯计费 - 按数量区间计费
        示例：
        {
            "tiers": [
                {"min": 1, "max": 10, "price": 5},
                {"min": 11, "max": 50, "price": 4},
                {"min": 51, "max": null, "price": 3}
            ],
            "field": "count"
        }
        """
        tiers = pricing_rules.get("tiers", [])
        field = pricing_rules.get("field", "count")
        value = int(form_data.get(field, 1))

        total = 0
        breakdown = {"tiers": []}

        for tier in tiers:
            min_val = tier.get("min", 0)
            max_val = tier.get("max")
            price = tier.get("price", 0)

            if value >= min_val:
                if max_val is None or value <= max_val:
                    tier_total = price * value
                    total += tier_total
                    breakdown["tiers"].append({
                        "range": f"{min_val}-{max_val or '∞'}",
                        "price": price,
                        "count": value,
                        "subtotal": tier_total
                    })
                    break

        breakdown["total"] = total
        breakdown["total_cost"] = total  # 兼容旧 schema

        return {
            "cost": total,
            "breakdown": breakdown,
            "description": f"{field}={value}, 总计 {total} 积分"
        }

    def get_pricing_preview(self, pricing_rules: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取计费预览信息（用于前端展示）
        """
        if not pricing_rules:
            return {"available": False, "message": "未配置计费规则"}

        mode = pricing_rules.get("mode", "static")
        preview = {"mode": mode, "available": True}

        if mode == "static":
            preview["base_price"] = pricing_rules.get("base_price", 0)
            preview["description"] = f"固定费用 {preview['base_price']} 积分/次"

        elif mode == "dynamic":
            preview["unit_price"] = pricing_rules.get("unit_price", 0)
            preview["multiply_by_field"] = pricing_rules.get("multiply_by_field")
            preview["duration_options"] = pricing_rules.get("duration_pricing", {})
            preview["resolution_options"] = pricing_rules.get("resolution_pricing", {})
            preview["ratio_options"] = pricing_rules.get("ratio_pricing", {})

            # 生成描述
            parts = []
            if preview["duration_options"]:
                parts.append(f"按时长计费: {list(preview['duration_options'].keys())}秒")
            if preview["resolution_options"]:
                parts.append(f"分辨率加价: {list(preview['resolution_options'].keys())}")
            preview["description"] = " | ".join(parts) if parts else "动态计费"

        elif mode == "tiered":
            preview["tiers"] = pricing_rules.get("tiers", [])
            preview["field"] = pricing_rules.get("field", "count")
            preview["description"] = f"阶梯计费，按 {preview['field']}"

        return preview


# 单例实例
pricing_engine = PricingEngine()