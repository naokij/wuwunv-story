#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
获取豆包 TTS 音色列表工具
帮助找到"甜美桃子"等音色的正确 ID
"""

import sys
import requests
from pathlib import Path

# 添加 scripts 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    VOLCENGINE_ACCESS_KEY,
    VOLCENGINE_SECRET_KEY,
    VOLCENGINE_APP_ID,
    VOLCENGINE_ACCESS_TOKEN,
    USE_APPID_TOKEN_AUTH,
    TTS_MODEL_TYPE
)


# 豆包 TTS 常用音色列表（基于官方文档）
# 完整列表请访问：https://www.volcengine.com/docs/6561/1257544

COMMON_VOICES = {
    # 用户复刻音色
    "S_ieReLKSR1": "温柔桃子（复刻）⭐",

    # 女声音色
    "zh_female_tianmeitaozi_mars_bigtts": "甜美桃子",
    "zh_female_vv_mars_bigtts": "Vivi",
    "ICL_zh_female_wenrounvshen_239eff5e8ffa_tob": "温柔女神",
    "zh_female_wanrou_mars_bigtts": "温柔女声",
    "zh_female_qingxin_mars_bigtts": "清新女声",
    "zh_female_tianmei_mars_bigtts": "甜美女声",
    "zh_female_yujie_mars_bigtts": "御姐",
    "zh_female_shaonv_mars_bigtts": "少女",
    "zh_female_chengshu_mars_bigtts": "成熟女声",

    # 男声音色
    "zh_male_wenshun_mars_bigtts": "温顺男声",
    "zh_male_qingnian_mars_bigtts": "青年男声",
    "zh_male_chengshu_mars_bigtts": "成熟男声",
    "zh_male_wenzhong_mars_bigtts": "稳重男声",
    "zh_male_boy_mars_bigtts": "男孩",

    # 其他特殊音色
    "BV405_24k_streaming": "甜美小源",
    "BV001_24k_streaming": "通用女声",
    "BV002_24k_streaming": "通用男声",
}


def fetch_voice_list_from_api():
    """
    从 API 获取音色列表（真实调用）

    Returns:
        音色列表数据，失败返回 None
    """
    print("正在从 API 获取音色列表...")
    print()

    # 检查认证方式
    use_appid_token = USE_APPID_TOKEN_AUTH
    use_key_secret = bool(VOLCENGINE_ACCESS_KEY and VOLCENGINE_SECRET_KEY)

    if not use_appid_token and not use_key_secret:
        print("✗ 未设置任何认证信息")
        print()
        print("请先在 .env 文件中配置：")
        print("  方式 A：VOLCENGINE_ACCESS_KEY 和 VOLCENGINE_SECRET_KEY")
        print("  方式 B：VOLCENGINE_APP_ID 和 VOLCENGINE_ACCESS_TOKEN")
        return None

    # ListSpeakers 接口 URL
    url = "https://openspeech.bytedance.com/api/v1/tts"

    # 构建请求体（用于获取音色列表的特殊请求）
    request_body = {
        "app": {
            "appid": VOLCENGINE_APP_ID if use_appid_token else "",
            "token": VOLCENGINE_ACCESS_TOKEN if use_appid_token else "access_token",
            "cluster": "volcano_tts"
        },
        "user": {
            "uid": "user_001"
        },
        "audio": {
            "voice_type": "zh_female_tianmeitaozi_mars_bigtts",  # 使用一个默认音色
            "encoding": "mp3",
            "speed_ratio": 1.0,
            "volume_ratio": 1.0,
            "pitch_ratio": 1.0
        },
        "request": {
            "reqid": f"list_speakers_{int(__import__('time').time() * 1000)}",
            "text": "测试",  # 最小文本
            "text_type": "plain",
            "operation": "query"
        }
    }

    # 添加模型类型
    if TTS_MODEL_TYPE == "seed-tts-2.0":
        request_body["audio"]["model_type"] = TTS_MODEL_TYPE

    import json
    import hmac
    import hashlib
    import base64

    body_str = json.dumps(request_body)

    headers = {
        "Content-Type": "application/json"
    }

    if use_appid_token:
        # 方式 B：APP ID + Access Token
        headers["Authorization"] = f"Bearer;{VOLCENGINE_ACCESS_TOKEN}"
        print(f"使用方式 B：APP ID + Access Token")
    else:
        # 方式 A：Access Key + Secret Key
        signature = hmac.new(
            VOLCENGINE_SECRET_KEY.encode('utf-8'),
            body_str.encode('utf-8'),
            hashlib.sha256
        )
        signature_b64 = base64.b64encode(signature.digest()).decode('utf-8')
        headers["Authorization"] = f"Bearer {VOLCENGINE_ACCESS_KEY}:{signature_b64}"
        print(f"使用方式 A：Access Key + Secret Key")

    print()

    try:
        response = requests.post(url, headers=headers, data=body_str, timeout=30)

        print(f"HTTP 状态码: {response.status_code}")

        if response.status_code == 200:
            result = response.json()

            print(f"响应代码: {result.get('code')}")
            print(f"响应消息: {result.get('message')}")

            # 检查返回的数据
            if "data" in result and result["data"]:
                print(f"返回数据长度: {len(result['data'])} 字节")
                print()
                print("✓ API 调用成功")
                print()
                print("注意：当前接口返回的是语音合成结果，不包含音色列表。")
                print()
                print("获取完整音色列表的方法：")
                print("  1. 访问火山引擎控制台：https://console.volcengine.com/speech/service")
                print("  2. 在控制台查看所有可用音色")
                print("  3. 或访问官方文档：https://www.volcengine.com/docs/6561/1257544")
                print()
                return result
            elif result.get("code") == 0 or result.get("message") == "Success":
                print()
                print("✓ API 调用成功")
                print()
                print("注意：当前接口返回的是语音合成结果，不包含音色列表。")
                print()
                print("获取完整音色列表的方法：")
                print("  1. 访问火山引擎控制台：https://console.volcengine.com/speech/service")
                print("  2. 在控制台查看所有可用音色")
                print("  3. 或访问官方文档：https://www.volcengine.com/docs/6561/1257544")
                print()
                return result
            else:
                print()
                print(f"✗ API 返回异常")
                print(f"完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return None
        else:
            print(f"✗ HTTP 错误: {response.status_code}")
            print(f"响应内容: {response.text[:500]}")
            return None

    except Exception as e:
        print(f"✗ 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def print_voice_list(voices: dict = None):
    """打印音色列表"""
    print("=" * 80)
    print("豆包 TTS 音色列表")
    print("=" * 80)
    print(f"模型版本: {TTS_MODEL_TYPE}")
    print(f"完整文档: https://www.volcengine.com/docs/6561/1257544")
    print()
    print("常用音色:")
    print("-" * 80)

    voice_list = voices or COMMON_VOICES

    for voice_id, voice_name in voice_list.items():
        # 标记推荐音色
        marker = " ⭐推荐" if "tianmeitaozi" in voice_id else ""
        print(f"  {voice_id:50s}  →  {voice_name}{marker}")

    print("-" * 80)
    print()
    print("使用方法:")
    print("  1. 在 config.py 中设置 TTS_VOICE_TYPE")
    print("  2. 或通过环境变量设置:")
    print(f"     export TTS_VOICE_TYPE=\"zh_female_tianmeitaozi_mars_bigtts\"")
    print()
    print("=" * 80)


def search_voice(keyword: str):
    """搜索音色"""
    print(f"搜索包含 '{keyword}' 的音色...")
    print()

    found = []
    for voice_id, voice_name in COMMON_VOICES.items():
        if keyword.lower() in voice_id.lower() or keyword in voice_name:
            found.append((voice_id, voice_name))

    if found:
        print("找到以下音色:")
        print("-" * 80)
        for voice_id, voice_name in found:
            print(f"  {voice_id:50s}  →  {voice_name}")
        print("-" * 80)
    else:
        print(f"未找到包含 '{keyword}' 的音色")
        print()
        print("提示:")
        print("  - 访问官方文档查看完整列表: https://www.volcengine.com/docs/6561/1257544")
        print("  - 或尝试其他关键词（如：桃子、温柔、女声、男声）")


def test_voice(voice_id: str, test_text: str = "你好，这是巫巫女睡前故事。"):
    """测试音色（需要 API 密钥）"""
    # 检查认证方式
    use_appid_token = USE_APPID_TOKEN_AUTH
    use_key_secret = bool(VOLCENGINE_ACCESS_KEY and VOLCENGINE_SECRET_KEY)

    if not use_appid_token and not use_key_secret:
        print("✗ 未设置任何认证信息，无法测试音色")
        print()
        print("请先在 .env 文件中配置：")
        print("  方式 A：VOLCENGINE_ACCESS_KEY 和 VOLCENGINE_SECRET_KEY")
        print("  方式 B：VOLCENGINE_APP_ID 和 VOLCENGINE_ACCESS_TOKEN")
        return

    print(f"测试音色: {voice_id}")
    print(f"测试文本: {test_text}")
    print()

    if use_appid_token:
        print(f"使用方式 B：APP ID + Access Token")
    else:
        print(f"使用方式 A：Access Key + Secret Token")
    print()

    # 判断是否是复刻音色（音色 ID 以 S_ 开头）
    cluster = "volcano_tts"  # 默认 cluster
    
    if voice_id.startswith("S_"):
        print("检测到复刻音色")
        print(f"  - 使用 volcano_icl cluster")
        print(f"  - voice_type 直接使用: {voice_id}")
        cluster = "volcano_icl"
        voice_type_for_request = voice_id
    else:
        voice_type_for_request = voice_id

    print()

    from volcengine_api import VolcEngineTTS

    tts = VolcEngineTTS(
        access_key=VOLCENGINE_ACCESS_KEY,
        secret_key=VOLCENGINE_SECRET_KEY,
        app_id=VOLCENGINE_APP_ID,
        access_token=VOLCENGINE_ACCESS_TOKEN
    )

    audio_data = tts.synthesize_speech(
        text=test_text,
        voice_type=voice_type_for_request,
        model_type=TTS_MODEL_TYPE,
        cluster=cluster
    )

    if audio_data:
        # 保存测试音频
        output_path = Path(__file__).parent / "test_voice.mp3"
        with open(output_path, "wb") as f:
            f.write(audio_data)

        print(f"✓ 音色测试成功")
        print(f"✓ 测试音频已保存: {output_path}")
        print()
        print("你可以播放这个文件来确认音色是否符合预期")
    else:
        print("✗ 音色测试失败")
        print()
        print("可能的原因:")
        print("  - 音色 ID 不正确或不属于当前账号")
        print("  - API 密钥无效")
        print("  - 网络连接问题")
        print("  - 复刻音色可能需要特殊参数")
        print()
        print("建议:")
        print("  1. 在火山引擎控制台确认音色 ID: " + voice_id)
        print("  2. 检查音色状态是否为'可用'")
        print("  3. 确认账号有权限使用该复刻音色")
        print("  4. 尝试使用官方音色测试:")
        print("     python scripts/get_tts_voices.py --test zh_female_tianmeitaozi_mars_bigtts")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="豆包 TTS 音色列表工具")
    parser.add_argument(
        "--list",
        action="store_true",
        help="显示预定义的音色列表"
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="调用 API 测试连接（不返回音色列表，仅测试认证）"
    )
    parser.add_argument(
        "--search",
        type=str,
        metavar="KEYWORD",
        help="搜索包含关键词的音色"
    )
    parser.add_argument(
        "--test",
        type=str,
        metavar="VOICE_ID",
        help="测试指定音色（需要 API 密钥）"
    )

    args = parser.parse_args()

    if args.api:
        # 调用 API 测试
        fetch_voice_list_from_api()
    elif args.search:
        search_voice(args.search)
    elif args.test:
        test_voice(args.test)
    else:
        # 默认显示预定义的音色列表
        print_voice_list()
        print()
        print("💡 提示:")
        print("  --list         显示预定义的音色列表")
        print("  --api          调用 API 测试连接")
        print("  --search 关键词  搜索音色")
        print("  --test 音色ID    测试指定音色")
        print()
        print("示例:")
        print("  python scripts/get_tts_voices.py --list")
        print("  python scripts/get_tts_voices.py --api")
        print("  python scripts/get_tts_voices.py --search 桃子")
        print("  python scripts/get_tts_voices.py --test zh_female_tianmeitaozi_mars_bigtts")


if __name__ == "__main__":
    main()
