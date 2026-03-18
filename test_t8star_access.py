"""
T8Star API 访问测试脚本
用于检测 API 是否有地区限制

使用方法：
1. 确保 ANTHROPIC_API_KEY 环境变量已设置（或其他 API Key）
2. 直接运行：python test_t8star_access.py
3. 开代理后再运行一次，对比结果
"""

import requests
import json
import time

# T8Star API 配置
T8_BASE_URL = "https://ai.t8star.cn"
T8_VIDEO_URL = f"{T8_BASE_URL}/v2/videos/generations"

# 请在这里填入你的 T8Star API Key
# 或者通过环境变量设置: export T8STAR_API_KEY=your_key
API_KEY = "sk-S0SFzFBigiwFqP2NGAVvOtJWkb7VO8VYJTp4WfcBSCvUMsA1"  # 替换成你的 Key


def test_basic_connection():
    """测试基本连接"""
    print("\n" + "="*50)
    print("测试 1: 基本连接测试")
    print("="*50)

    try:
        resp = requests.get(T8_BASE_URL, timeout=10)
        print(f"✅ 可以访问 {T8_BASE_URL}")
        print(f"   状态码: {resp.status_code}")
        return True
    except requests.exceptions.Timeout:
        print(f"❌ 连接超时")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ 连接失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False


def test_api_without_key():
    """测试 API 端点（不带 Key）"""
    print("\n" + "="*50)
    print("测试 2: API 端点测试（无 Key）")
    print("="*50)

    try:
        resp = requests.post(
            T8_VIDEO_URL,
            json={"model": "sora-2", "prompt": "test"},
            timeout=15
        )
        print(f"✅ API 端点可达")
        print(f"   状态码: {resp.status_code}")
        print(f"   响应: {resp.text[:200]}")
        return resp.status_code in [200, 401, 403, 422]  # 这些都说明能连通
    except requests.exceptions.Timeout:
        print(f"❌ API 请求超时")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ API 连接失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False


def test_api_with_key():
    """测试 API 端点（带 Key）"""
    print("\n" + "="*50)
    print("测试 3: API 端点测试（带 Key）")
    print("="*50)

    if API_KEY == "YOUR_T8STAR_API_KEY_HERE":
        print("⚠️  请先在脚本中填入你的 T8Star API Key")
        return None

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "sora-2",
        "prompt": "a cat walking on the street",
        "aspect_ratio": "1:1",
        "duration": 5
    }

    try:
        resp = requests.post(
            T8_VIDEO_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        print(f"✅ API 请求成功")
        print(f"   状态码: {resp.status_code}")

        result = resp.json()
        if "task_id" in result:
            print(f"   ✅ 获得 task_id: {result['task_id']}")
            return result['task_id']
        else:
            print(f"   响应: {json.dumps(result, ensure_ascii=False)[:300]}")
        return True

    except requests.exceptions.Timeout:
        print(f"❌ API 请求超时（可能被地区限制）")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ API 连接失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        return False


def check_ip_location():
    """检查当前 IP 归属地"""
    print("\n" + "="*50)
    print("测试 4: 当前 IP 归属地")
    print("="*50)

    try:
        # 使用多个 IP 查询服务
        ip_services = [
            ("https://ipapi.co/json/", "ipapi.co"),
            ("https://ipwho.is/", "ipwho.is"),
            ("http://ip-api.com/json/", "ip-api.com"),
        ]

        for url, name in ip_services:
            try:
                resp = requests.get(url, timeout=10)
                data = resp.json()
                country = data.get("country", data.get("country_name", "未知"))
                city = data.get("city", "未知")
                ip = data.get("ip", "未知")
                print(f"   {name}: {ip} - {country} {city}")
                break
            except:
                continue

    except Exception as e:
        print(f"   无法获取 IP 信息: {e}")


def main():
    print("\n" + "#"*60)
    print("#  T8Star API 访问测试")
    print("#  用于检测是否有地区限制")
    print("#"*60)

    print("\n📌 测试说明：")
    print("   1. 先在直连（不开代理）情况下运行一次")
    print("   2. 开启代理后再运行一次")
    print("   3. 对比两次结果，判断是否有地区限制")

    # 获取当前 IP
    check_ip_location()

    # 运行测试
    test_basic_connection()
    test_api_without_key()

    # 提示填入 API Key
    if API_KEY == "YOUR_T8STAR_API_KEY_HERE":
        print("\n" + "⚠️ "*20)
        print("请先在脚本顶部填入你的 T8Star API Key，然后重新运行")
        print("⚠️ "*20)
    else:
        test_api_with_key()

    print("\n" + "="*50)
    print("测试完成！")
    print("="*50)
    print("\n📋 结果分析：")
    print("   - 如果直连成功、代理失败 → T8Star 限制海外 IP")
    print("   - 如果直连失败、代理成功 → T8Star 限制国内 IP（不太可能）")
    print("   - 如果都成功 → 无地区限制，可以用 Vercel")
    print("   - 如果都失败 → 网络问题或 API Key 问题")


if __name__ == "__main__":
    main()