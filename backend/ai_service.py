"""
AI 服务层 - 处理提示词生成和 API 调用
参考旧项目 MyWebTool/ai_service.py 实现
"""
import requests
import re
import base64
from typing import Dict, Any, List, Optional


class AIService:
    """AI 提示词生成服务"""

    # 语言映射字典
    LANG_MAP = {
        "中文": "Chinese", "简体中文": "Simplified Chinese", "繁体中文": "Traditional Chinese",
        "英语": "English", "英文": "English",
        "日语": "Japanese", "日文": "Japanese",
        "韩语": "Korean", "韩文": "Korean",
        "法语": "French", "德语": "German", "俄语": "Russian",
        "西班牙语": "Spanish", "葡萄牙语": "Portuguese", "意大利语": "Italian",
        "荷兰语": "Dutch", "波兰语": "Polish", "瑞典语": "Swedish",
        "越南语": "Vietnamese", "泰语": "Thai", "印尼语": "Indonesian",
        "马来语": "Malay", "菲律宾语": "Filipino", "印地语": "Hindi",
        "阿拉伯语": "Arabic", "土耳其语": "Turkish",
        # 带括号的语言格式
        "日语 (Japanese)": "Japanese",
        "英语 (English)": "English",
        "中文 (Chinese)": "Chinese",
        "韩语 (Korean)": "Korean",
        "法语 (French)": "French",
        "德语 (German)": "German",
        "俄语 (Russian)": "Russian",
        "西班牙语 (Spanish)": "Spanish",
        "阿拉伯语 (Arabic)": "Arabic",
        "葡萄牙语 (Portuguese)": "Portuguese",
        "越南语 (Vietnamese)": "Vietnamese",
        "泰语 (Thai)": "Thai",
        "印尼语 (Indonesian)": "Indonesian",
        "意大利语 (Italian)": "Italian",
        "马来语 (Malay)": "Malay"
    }

    def __init__(self, modelscope_api_key: str):
        self.modelscope_api_key = modelscope_api_key
        self.api_url = "https://api-inference.modelscope.cn/v1/chat/completions"
        self.model = "Qwen/Qwen3-VL-30B-A3B-Instruct"

    def _get_lang_eng(self, target_lang: str) -> str:
        """将中文语言名转换为英文"""
        return self.LANG_MAP.get(target_lang, target_lang)

    def _encode_image_to_base64(self, image_data: str) -> Optional[str]:
        """编码图片为 base64 格式"""
        if not image_data:
            return None
        # 如果已经是 base64 格式
        if image_data.startswith("data:image"):
            return image_data
        # 如果是纯 base64 字符串
        if len(image_data) > 1000:
            return f"data:image/jpeg;base64,{image_data}"
        return None

    def _call_modelscope_api(self, prompt: str, images: List[str] = None, max_tokens: int = 1500) -> str:
        """调用 ModelScope API"""
        headers = {
            'Authorization': f'Bearer {self.modelscope_api_key}',
            'Content-Type': 'application/json'
        }

        # 构建消息内容
        content_list = [{"type": "text", "text": prompt}]

        # 添加图片
        if images:
            for img in images:
                b64 = self._encode_image_to_base64(img)
                if b64:
                    content_list.append({
                        "type": "image_url",
                        "image_url": {"url": b64}
                    })

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": content_list}],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }

        try:
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=120, verify=False)
            if resp.status_code == 200:
                content = resp.json()['choices'][0]['message']['content'].strip()
                return content.replace("**", "").replace("##", "")
            return f"API Error: {resp.status_code} - {resp.text}"
        except Exception as e:
            return f"Network Error: {str(e)}"

    # ==================== 1. 看图写卖点 ====================

    def generate_selling_points(
        self,
        prompt_template: str,
        images: List[str],
        product_type: str,
        design_style: str,
        target_lang: str,
        target_num: int
    ) -> str:
        """
        看图写卖点 - 根据提示词模板生成卖点文案

        Args:
            prompt_template: 从数据库读取的提示词模板
            images: 图片 base64 列表
            product_type: 产品类型
            design_style: 设计风格
            target_lang: 目标语言
            target_num: 生成数量

        Returns:
            生成的卖点文案
        """
        lang_eng = self._get_lang_eng(target_lang)

        # 生成格式示例
        format_parts = []
        for i in range(1, target_num + 1):
            format_parts.append(f"Set {i}:\nMain Title: ...\nSubtitle: ...")
        format_example = "\n\n".join(format_parts)

        # 替换变量
        prompt = prompt_template
        prompt = prompt.replace("{lang_eng}", lang_eng)
        prompt = prompt.replace("{product_type}", product_type or "通用产品")
        prompt = prompt.replace("{design_style}", design_style or "简约风格")
        prompt = prompt.replace("{target_num}", str(target_num))
        prompt = prompt.replace("{format_example}", format_example)

        return self._call_modelscope_api(prompt, images, max_tokens=2000)

    # ==================== 2. 生图提示词规划 ====================

    def plan_image_prompts(
        self,
        prompt_template: str,
        images: List[str],
        product_type: str,
        selling_points: str,
        design_style: str,
        target_lang: str,
        num_screens: int
    ) -> List[str]:
        """
        生图提示词规划 - 根据提示词模板规划多屏详情页的生图提示词

        Args:
            prompt_template: 从数据库读取的提示词模板
            images: 参考图片 base64 列表
            product_type: 产品类型
            selling_points: 核心卖点
            design_style: 设计风格
            target_lang: 目标语言
            num_screens: 屏幕数量

        Returns:
            生图提示词列表
        """
        lang_eng = self._get_lang_eng(target_lang)

        # 替换变量
        prompt = prompt_template
        prompt = prompt.replace("{num_screens}", str(num_screens))
        prompt = prompt.replace("{lang_eng}", lang_eng)
        prompt = prompt.replace("{product_type}", product_type or "")
        prompt = prompt.replace("{selling_points}", selling_points or "")
        prompt = prompt.replace("{design_style}", design_style or "简约风格")

        result = self._call_modelscope_api(prompt, images, max_tokens=4000)

        # 解析结果为列表
        return self._parse_prompts(result, num_screens, product_type, design_style)

    def _parse_prompts(self, content: str, target_num: int, product_type: str, design_style: str) -> List[str]:
        """解析 AI 返回的提示词为列表"""
        try:
            # 尝试 JSON 解析
            import json
            clean_content = content.replace('```json', '').replace('```', '').strip()
            try:
                prompts = json.loads(clean_content)
                if isinstance(prompts, list):
                    return [str(p) for p in prompts[:target_num]]
            except:
                pass

            # 正则解析 - 按"第X屏"分割
            parts = re.split(r'["\']?第\d+屏["\']?[：:]', content)
            prompts = [p.strip().strip(',"') for p in parts if len(p.strip()) > 20]

            # 补齐数量
            fallback = f"{product_type}, {design_style}, e-commerce product photography"
            while len(prompts) < target_num:
                prompts.append(prompts[0] if prompts else fallback)

            return prompts[:target_num]
        except Exception as e:
            print(f"Parse Error: {e}")
            return [f"{product_type}, {design_style}"] * target_num

    # ==================== 3. 视频分镜提示词 ====================

    def generate_video_script(
        self,
        prompt_template: str,
        images: List[str],
        product_type: str,
        selling_points: str,
        region: str,
        target_lang: str,
        category: str,
        style: str,
        has_subtitle: bool = True
    ) -> str:
        """
        视频分镜生成 - 根据提示词模板生成视频分镜脚本

        Args:
            prompt_template: 从数据库读取的提示词模板
            images: 参考图片
            product_type: 产品名称
            selling_points: 核心卖点
            region: 投放地区
            target_lang: 目标语言
            category: 产品类目
            style: 视频风格
            has_subtitle: 是否需要字幕

        Returns:
            视频分镜脚本
        """
        lang_eng = self._get_lang_eng(target_lang)

        # 根据地区生成场景描述
        region_prompt = self._get_region_prompt(region)

        # 根据字幕设置生成指令
        text_instruction, overlay_action, output_req = self._get_subtitle_instructions(
            has_subtitle, lang_eng
        )

        # 替换变量
        script = prompt_template
        script = script.replace("{target_lang}", lang_eng)
        script = script.replace("{region_sel}", region or "东亚")
        script = script.replace("{style_sel}", style or "UGC 种草")
        script = script.replace("{category}", category or "通用")
        script = script.replace("{region_prompt}", region_prompt)
        script = script.replace("{text_instruction}", text_instruction)
        script = script.replace("{overlay_action}", overlay_action)
        script = script.replace("{output_req}", output_req)

        # 构建用户请求
        user_req = f"""
Input:
Product: {product_type}
Selling Points: {selling_points}

Instruction:
Write a video script in English description but {lang_eng} dialogue/text.
{output_req}
"""

        # 合并为完整提示词
        full_prompt = f"{script}\n\n{user_req}"

        return self._call_modelscope_api(full_prompt, images[:1] if images else None, max_tokens=1500)

    def _get_region_prompt(self, region: str) -> str:
        """根据地区生成场景描述"""
        if "非洲" in region:
            return "Environment: Vibrant African urban setting. Character: Local African influencer."
        elif "东南亚" in region:
            return "Environment: Southeast Asian home setting. Character: Southeast Asian influencer."
        elif "欧美" in region:
            return "Environment: Modern Western apartment. Character: Caucasian influencer."
        elif "中东" in region:
            return "Environment: Luxurious modern home. Character: Middle Eastern influencer."
        else:
            return "Environment: Clean Japanese/Korean apartment. Character: Asian influencer."

    def _get_subtitle_instructions(self, has_subtitle: bool, target_lang: str) -> tuple:
        """根据字幕设置生成指令"""
        if has_subtitle:
            text_instruction = f"Target Language: {target_lang}. Text must be Huge, Bold."
            overlay_action = f"- (Scene 3: Detail) Close-up. Overlay huge bold text in {target_lang}: '...'"
            output_req = f"- Ensure Text Overlays are in target language."
        else:
            text_instruction = "NO TEXT OVERLAYS. Pure visual."
            overlay_action = "- (Scene 3: Detail) Close-up emphasizing texture. (NO TEXT)."
            output_req = "- ABSOLUTELY NO TEXT OVERLAYS."
        return text_instruction, overlay_action, output_req

    # ==================== 4. 翻译功能 ====================

    def translate_text(self, text: str, target_lang: str, prompt_key: str) -> str:
        """翻译文本"""
        lang_eng = self._get_lang_eng(target_lang)

        prompt = f"""
Role: Professional Translator.
Task: Translate the following content into **{lang_eng}**.
Rule: Output ONLY the translated text. No explanations.

[Content]:
{text}
"""

        headers = {
            'Authorization': f'Bearer {prompt_key}',
            'Content-Type': 'application/json'
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            resp = requests.post(self.api_url, headers=headers, json=payload, timeout=60, verify=False)
            if resp.status_code == 200:
                return resp.json()['choices'][0]['message']['content'].strip()
            return "翻译失败"
        except:
            return "网络错误"