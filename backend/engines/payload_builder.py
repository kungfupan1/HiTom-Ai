"""
报文拼凑引擎
解析 config_schema.request_mapping 构建 API 请求
"""
from typing import Dict, Any, Optional, List
import re


class PayloadBuilder:
    """报文拼凑引擎 - 根据 request_mapping 配置构建 API 请求"""

    def build(
        self,
        request_mapping: Dict[str, Any],
        form_data: Dict[str, Any],
        model_id: str = None,
        prompt_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        构建请求 payload

        Args:
            request_mapping: 从 config_schema.request_mapping 获取
            form_data: 用户提交的表单数据
            model_id: 模型 ID（用于动态参数）
            prompt_config: 提示词配置（可选）

        Returns:
            构建好的请求 payload
        """
        if not request_mapping:
            return form_data  # 如果没有映射，直接返回原始数据

        payload = {}

        # 1. 添加静态参数
        static_params = request_mapping.get("static_params", {})
        payload.update(static_params)

        # 2. 映射动态参数
        dynamic_params = request_mapping.get("dynamic_params", {})
        for source_field, target_field in dynamic_params.items():
            if source_field in form_data:
                value = form_data[source_field]

                # 特殊字段处理
                if source_field == "model" and model_id:
                    value = model_id
                elif source_field == "model" and value:
                    pass  # 使用表单中的值

                # 设置到目标字段
                self._set_nested_value(payload, target_field, value)

        # 3. 构建 prompt（如果有模板）
        prompt_template = request_mapping.get("prompt_template")
        if prompt_template:
            prompt = self._render_template(prompt_template, form_data)
            # prompt 字段映射
            prompt_field = dynamic_params.get("prompt", "prompt")
            self._set_nested_value(payload, prompt_field, prompt)

        # 4. 系统提示词（如果有）
        if prompt_config and "system_prompt" in prompt_config:
            system_prompt = prompt_config["system_prompt"]
            # 系统提示词通常放在 messages 数组的第一个元素
            if "messages" not in payload:
                payload["messages"] = []
            # 插入系统提示词到开头
            payload["messages"].insert(0, {
                "role": "system",
                "content": system_prompt
            })

        # 5. 值转换
        value_transformations = request_mapping.get("value_transformations", {})
        for source_field, transform_config in value_transformations.items():
            if source_field in form_data:
                source_value = form_data[source_field]
                target_field = transform_config.get("target_field")
                transform_expr = transform_config.get("transform")

                if target_field and transform_expr:
                    transformed_value = self._transform_value(source_value, transform_expr)
                    self._set_nested_value(payload, target_field, transformed_value)

        # 6. 处理图片上传字段
        if "images" in form_data:
            images = form_data["images"]
            if images and isinstance(images, list):
                # 根据不同的 API 格式处理图片
                image_field = dynamic_params.get("images", "images")
                self._set_nested_value(payload, image_field, images)

        return payload

    def _set_nested_value(self, obj: Dict, path: str, value: Any):
        """设置嵌套对象的值，支持点号路径如 'data.url'"""
        keys = path.split(".")
        current = obj

        for i, key in enumerate(keys[:-1]):
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def _render_template(self, template: str, form_data: Dict) -> str:
        """渲染模板字符串，替换 {field} 为实际值"""
        def replace(match):
            field_name = match.group(1)
            value = form_data.get(field_name, "")
            return str(value) if value is not None else ""

        return re.sub(r'\{(\w+)\}', replace, template)

    def _transform_value(self, source_value: Any, transform_expr: str) -> Any:
        """
        执行值转换

        支持的表达式：
        - "resolution === '1080P'" -> 返回布尔值
        - "parseInt(value)" -> 返回整数
        - "value.toUpperCase()" -> 返回大写字符串
        """
        # JavaScript 风格的转换表达式（简化实现）
        try:
            # 布尔表达式
            if "===" in transform_expr:
                # 解析如 "resolution === '1080P'"
                parts = transform_expr.split("===")
                if len(parts) == 2:
                    expected = parts[1].strip().strip("'\"")
                    return str(source_value) == expected

            # parseInt
            if transform_expr == "parseInt(value)":
                return int(source_value)

            # toUpperCase
            if transform_expr == "value.toUpperCase()":
                return str(source_value).upper()

            # toLowerCase
            if transform_expr == "value.toLowerCase()":
                return str(source_value).lower()

            # 默认返回原值
            return source_value

        except Exception:
            return source_value

    def build_status_query(
        self,
        api_contract: Dict[str, Any],
        task_id: str
    ) -> Dict[str, Any]:
        """
        构建状态查询请求

        Args:
            api_contract: API 配置
            task_id: 任务 ID

        Returns:
            {"url": "...", "method": "...", "params": {}}
        """
        status_url = api_contract.get("status_url", "")
        # 替换 {task_id} 占位符
        url = status_url.replace("{task_id}", task_id)

        return {
            "url": url,
            "method": api_contract.get("status_method", "GET"),
            "params": {}
        }

    def extract_response(
        self,
        response_mapping: Dict[str, Any],
        api_response: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        从 API 响应中提取关键信息

        Args:
            response_mapping: 从 config_schema.response_mapping 获取
            api_response: API 返回的原始响应

        Returns:
            {
                "task_id": "...",
                "status": "processing|success|failed",
                "progress": 0-100,
                "result_url": "...",
                "error": "..."
            }
        """
        if not response_mapping:
            return api_response

        result = {}

        # 提取 task_id
        task_id_path = response_mapping.get("task_id_path")
        if task_id_path:
            result["task_id"] = self._get_json_value(api_response, task_id_path)

        # 提取状态
        status_path = response_mapping.get("status_path")
        if status_path:
            raw_status = self._get_json_value(api_response, status_path)
            result["status"] = self._normalize_status(raw_status, response_mapping.get("status_mapping", {}))

        # 提取进度
        progress_path = response_mapping.get("progress_path")
        if progress_path:
            result["progress"] = self._get_json_value(api_response, progress_path) or 0

        # 提取结果 URL
        result_url_path = response_mapping.get("result_url_path")
        if result_url_path:
            result["result_url"] = self._get_json_value(api_response, result_url_path)

        # 提取错误信息
        error_path = response_mapping.get("error_path")
        if error_path:
            result["error"] = self._get_json_value(api_response, error_path)

        return result

    def _get_json_value(self, obj: Dict, path: str) -> Any:
        """
        根据 JSON Path 获取值
        支持：data.output, data[0].url, items[*].url
        """
        if not path:
            return None

        keys = path.split(".")
        value = obj

        for key in keys:
            if value is None:
                return None

            # 处理数组索引 data[0]
            array_match = re.match(r'^(\w+)\[(\d+)\]$', key)
            if array_match:
                array_key = array_match.group(1)
                index = int(array_match.group(2))
                if isinstance(value, dict) and array_key in value:
                    value = value[array_key]
                    if isinstance(value, list) and len(value) > index:
                        value = value[index]
                    else:
                        return None
                else:
                    return None
            # 处理通配符 [*]
            elif key == "*":
                if isinstance(value, list):
                    # 返回第一个元素的值（简化处理）
                    value = value[0] if value else None
            # 普通字段
            elif isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value

    def _normalize_status(self, raw_status: str, status_mapping: Dict) -> str:
        """
        标准化状态值

        Args:
            raw_status: API 返回的原始状态
            status_mapping: 状态映射配置

        Returns:
            "processing" | "success" | "failed"
        """
        if not raw_status:
            return "processing"

        raw_status = str(raw_status).lower()

        # 检查各状态映射
        for status, values in status_mapping.items():
            if raw_status in [v.lower() for v in values]:
                return status

        # 默认映射
        if raw_status in ["success", "completed", "succeeded", "done", "finished"]:
            return "success"
        elif raw_status in ["failed", "error", "failure", "rejected", "canceled"]:
            return "failed"
        else:
            return "processing"


# 单例实例
payload_builder = PayloadBuilder()