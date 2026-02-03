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


# ==================== MiniMax TTS 配置 ====================

# MiniMax API 配置
# 获取地址: https://www.minimaxi.com/user-center/basic-information/interface-key
# - Group ID: 用户中心 → 账户信息 → 基本信息
# - API Key: 用户中心 → 接口密钥 → 创建新的 API Key
MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "")

# MiniMax TTS 模型
# 可选值：speech-2.8-hd, speech-2.8-turbo, speech-2.6-hd, speech-2.6-turbo, speech-02-hd, speech-02-turbo, speech-01-hd, speech-01-turbo
MINIMAX_MODEL = "speech-2.8-hd"

# 是否使用 MiniMax TTS（优先使用 MiniMax）
USE_MINIMAX_TTS = bool(MINIMAX_API_KEY)

# MiniMax 默认参数
MINIMAX_SPEED = 1.0  # 语速
MINIMAX_VOL = 1.0  # 音量
MINIMAX_PITCH = 0  # 音调 (-1 到 1)
MINIMAX_FORMAT = "mp3"  # 音频格式
MINIMAX_OUTPUT_TYPE = "hex"  # 输出格式：hex 或 url

# 统一音色配置（所有角色使用同一个音色）
MINIMAX_VOICE_ID = os.environ.get("MINIMAX_VOICE_ID", "")
MINIMAX_EMOTION = os.environ.get("MINIMAX_EMOTION", "gentle")  # 默认情感：gentle（温柔）、happy（欢快）、sad（悲伤）等


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
        "style": "温馨治愈风格，柔和的光线，童话插画风格",
        # MiniMax 配置（从环境变量读取，所有角色使用同一个音色）
        "minimax_voice_id": os.environ.get("MINIMAX_VOICE_ID", ""),
        "minimax_emotion": os.environ.get("MINIMAX_EMOTION", "gentle")  # 默认情感：gentle（温柔）、happy（欢快）、sad（悲伤）等
    },
    "莉莉": {
        "reference_image": str(REFERENCES_DIR / "莉莉_reference.jpg"),
        "base_prompt": "莉莉，6岁小女孩，扎着小辫子，穿着粉色连衣裙，可爱活泼",
        "style": "温馨治愈风格，柔和的光线，童话插画风格",
        # MiniMax 配置（使用统一的音色）
        "minimax_voice_id": os.environ.get("MINIMAX_VOICE_ID", ""),
        "minimax_emotion": os.environ.get("MINIMAX_EMOTION", "gentle")
    },
    "欣欣": {
        "reference_image": str(REFERENCES_DIR / "欣欣_reference.jpg"),
        "base_prompt": "欣欣，6岁小女孩，梳着丸子头，穿黄色羽绒服，戴毛线帽，手里拿着画本和画笔",
        "style": "温馨治愈风格，柔和的光线，童话插画风格",
        # MiniMax 配置（使用统一的音色）
        "minimax_voice_id": os.environ.get("MINIMAX_VOICE_ID", ""),
        "minimax_emotion": os.environ.get("MINIMAX_EMOTION", "gentle")
    }
}

# ==================== 即梦 AI 配置 ====================

# 图像尺寸: 1024*1020, 1080*1920 等
IMAGE_SIZE = "1024*1020"

# 图像质量: standard, high
IMAGE_QUALITY = "high"

# 参考图权重（0.0 - 1.0，越高越严格保持角色特征）
REFERENCE_WEIGHT = 0.8

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

    # 检查 MiniMax API 密钥
    if not MINIMAX_API_KEY:
        errors.append("未设置 MINIMAX_API_KEY")

    # 检查火山引擎 API 密钥（用于封面生成）
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
    print(f"  MiniMax API Key: {'已设置' if MINIMAX_API_KEY else '未设置'}")
    print(f"  MiniMax Voice ID: {MINIMAX_VOICE_ID if MINIMAX_VOICE_ID else '未设置'}")
    print(f"  MiniMax Emotion: {MINIMAX_EMOTION}")
    print(f"  火山引擎 Access Key: {'已设置' if VOLCENGINE_ACCESS_KEY else '未设置'}")
    print(f"  火山引擎 Secret Key: {'已设置' if VOLCENGINE_SECRET_KEY else '未设置'}")
    print()
    print("TTS 配置:")
    print(f"  模型: {MINIMAX_MODEL}")
    print(f"  语速: {MINIMAX_SPEED}")
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