#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巫巫女故事自动化生成工具 - 配置文件
使用豆包 TTS API 和即梦 AI API 自动生成音频和封面
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件（如果存在）
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

# ==================== 项目路径配置 ====================

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

# 音频输出目录
AUDIO_DIR = PROJECT_ROOT / "audio"

# 角色参考图目录
REFERENCES_DIR = AUDIO_DIR / "references"

# 故事文件目录
STORIES_DIR = PROJECT_ROOT


# ==================== 火山引擎 API 配置 ====================

# 方式 A：使用 Access Key + Secret Key
VOLCENGINE_ACCESS_KEY = os.environ.get("VOLCENGINE_ACCESS_KEY", "")
VOLCENGINE_SECRET_KEY = os.environ.get("VOLCENGINE_SECRET_KEY", "")

# 方式 B：使用 APP ID + Access Token（推荐）
VOLCENGINE_APP_ID = os.environ.get("VOLCENGINE_APP_ID", "")
VOLCENGINE_ACCESS_TOKEN = os.environ.get("VOLCENGINE_ACCESS_TOKEN", "")

# 自动选择认证方式（优先使用方式 B）
USE_APPID_TOKEN_AUTH = bool(VOLCENGINE_APP_ID and VOLCENGINE_ACCESS_TOKEN)


# ==================== 豆包 TTS 配置 ====================

# TTS API 端点
TTS_API_URL = "https://openspeech.bytedance.com/api/v1/tts"

# 音色类型（需要通过 get_tts_voices.py 获取完整的音色列表）
# 常见音色：
# - S_ieReLKSR1: 温柔桃子（复刻）
# - zh_female_tianmeitaozi_mars_bigtts: 甜美桃子
# - zh_female_vv_mars_bigtts: Vivi
# - ICL_zh_female_wenrounvshen_239eff5e8ffa_tob: 温柔女神
TTS_VOICE_TYPE = os.environ.get("TTS_VOICE_TYPE", "S_ieReLKSR1")

# TTS 编码格式
TTS_ENCODING = "mp3"

# TTS 语速（0.5 - 2.0，默认 1.0）
TTS_SPEED_RATIO = 1.0

# TTS 音量（0.0 - 1.0，默认 1.0）
TTS_VOLUME_RATIO = 1.0

# TTS 模型版本（seed-tts-1.0 或 seed-tts-2.0）
TTS_MODEL_TYPE = "seed-tts-2.0"


# ==================== 即梦 AI 配置 ====================

# 即梦 AI API 端点（使用火山引擎 OpenAPI）
JIMENG_API_URL = "https://open.volcengineapi.com"
JIMENG_SERVICE = "cv"
JIMENG_REGION = "cn-north-1"

# 即梦 AI 模型 key（图片生成 4.0）
JIMENG_REQ_KEY = "jimeng_t2i_v40"

# 图像宽高比: 16:9, 4:3, 1:1, 3:4, 9:16
JIMENG_ASPECT_RATIO = "16:9"

# 图像质量: standard, high
JIMENG_IMAGE_QUALITY = os.environ.get("IMAGE_QUALITY", "high")

# 参考图权重（0.0 - 1.0，越高越严格保持角色特征）
JIMENG_REFERENCE_WEIGHT = float(os.environ.get("REFERENCE_WEIGHT", "0.8"))


# ==================== 角色配置 ====================

# 角色参考图配置
CHARACTERS = {
    "巫巫女": {
        "reference_image": str(REFERENCES_DIR / "巫巫女_reference.jpg"),
        "base_prompt": "巫巫女，乱蓬蓬的紫头发，尖尖的鼻子，穿着彩虹披风，温柔的女巫",
        "style": "温馨治愈风格，柔和的光线，童话插画风格"
    },
    "莉莉": {
        "reference_image": str(REFERENCES_DIR / "莉莉_reference.jpg"),
        "base_prompt": "莉莉，6岁小女孩，扎着小辫子，穿着粉色连衣裙，可爱活泼",
        "style": "温馨治愈风格，柔和的光线，童话插画风格"
    },
    "欣欣": {
        "reference_image": str(REFERENCES_DIR / "欣欣_reference.jpg"),
        "base_prompt": "欣欣，6岁小女孩，梳着丸子头，穿黄色羽绒服，戴毛线帽，手里拿着画本和画笔",
        "style": "温馨治愈风格，柔和的光线，童话插画风格"
    }
}

# 默认风格关键词（所有图片都会添加）
DEFAULT_STYLE_KEYWORDS = "温馨治愈风格，柔和的光线，童话插画风格，色彩明亮温暖"


# ==================== 元数据配置 ====================

# MP3 元数据
METADATA_ARTIST = "巫巫女睡前故事"
METADATA_ALBUM = "巫巫女睡前故事集"
METADATA_GENRE = "儿童故事"


# ==================== 验证配置 ====================

def validate_config():
    """验证配置是否正确"""
    errors = []

    # 检查 API 密钥
    if not VOLCENGINE_ACCESS_KEY:
        errors.append("未设置 VOLCENGINE_ACCESS_KEY")
    if not VOLCENGINE_SECRET_KEY:
        errors.append("未设置 VOLCENGINE_SECRET_KEY")

    # 检查目录
    if not AUDIO_DIR.exists():
        errors.append(f"音频目录不存在: {AUDIO_DIR}")
    if not REFERENCES_DIR.exists():
        errors.append(f"角色参考图目录不存在: {REFERENCES_DIR}")

    # 检查角色参考图
    for char_name, char_config in CHARACTERS.items():
        ref_image = char_config["reference_image"]
        if not Path(ref_image).exists():
            errors.append(f"角色参考图不存在: {ref_image}")

    return errors


def print_config():
    """打印当前配置"""
    print("=" * 60)
    print("巫巫女故事自动化生成工具 - 配置信息")
    print("=" * 60)
    print(f"项目根目录: {PROJECT_ROOT}")
    print(f"音频目录: {AUDIO_DIR}")
    print(f"参考图目录: {REFERENCES_DIR}")
    print()
    print("API 配置:")
    print(f"  Access Key: {'已设置' if VOLCENGINE_ACCESS_KEY else '未设置'}")
    print(f"  Secret Key: {'已设置' if VOLCENGINE_SECRET_KEY else '未设置'}")
    print(f"  App ID: {VOLCENGINE_APP_ID if VOLCENGINE_APP_ID else '未设置'}")
    print(f"  Access Token: {'已设置' if VOLCENGINE_ACCESS_TOKEN else '未设置'}")
    print()
    print("TTS 配置:")
    print(f"  音色: {TTS_VOICE_TYPE}")
    print(f"  模型: {TTS_MODEL_TYPE}")
    print(f"  语速: {TTS_SPEED_RATIO}")
    print()
    print("即梦 AI 配置:")
    print(f"  模型: {JIMENG_REQ_KEY}")
    print(f"  宽高比: {JIMENG_ASPECT_RATIO}")
    print(f"  图像质量: {JIMENG_IMAGE_QUALITY}")
    print(f"  参考图权重: {JIMENG_REFERENCE_WEIGHT}")
    print()
    print("角色配置:")
    for char_name in CHARACTERS.keys():
        print(f"  - {char_name}")
    print("=" * 60)


if __name__ == "__main__":
    print_config()
    errors = validate_config()
    if errors:
        print("\n配置错误:")
        for error in errors:
            print(f"  ✗ {error}")
    else:
        print("\n✓ 配置验证通过")