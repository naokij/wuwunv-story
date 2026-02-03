#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巫巫女故事配音工具
使用 MiniMax TTS API 为故事生成语音
"""

import sys
import os
import argparse
import re
from pathlib import Path

# 添加 scripts 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    MINIMAX_API_KEY,
    MINIMAX_MODEL,
    MINIMAX_VOICE_ID,
    MINIMAX_EMOTION,
    CHARACTERS,
    STORIES_DIR,
    AUDIO_DIR
)
from minimax_api import MiniMaxTTS


def extract_story_content(story_file: str) -> tuple[str, str]:
    """
    从 Markdown 文件中提取故事内容
    
    Args:
        story_file: 故事文件路径
    
    Returns:
        (故事标题, 故事内容)
    """
    with open(story_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 提取第一个标题（作为故事标题）
    title_match = re.search(r'^#\s*(.+)', content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "未命名故事"
    
    # 移除 frontmatter（如果有）
    if content.startswith('---'):
        content = re.sub(r'^---.*?---', '', content, count=1, flags=re.DOTALL)
    
    # 移除标题行
    content = re.sub(r'^#\s*.+\n?', '', content, flags=re.MULTILINE)
    
    # 清理空白
    content = content.strip()
    
    return title, content


def detect_main_character(content: str) -> str:
    """
    检测故事的主要角色
    
    Args:
        content: 故事内容
    
    Returns:
        主要角色名称
    """
    # 在 CHARACTERS 中查找出现频率最高的角色
    character_counts = {}
    
    for char_name in CHARACTERS.keys():
        # 查找角色名称的出现次数
        count = content.count(char_name)
        if count > 0:
            character_counts[char_name] = count
    
    if character_counts:
        # 返回出现次数最多的角色
        return max(character_counts, key=character_counts.get)
    else:
        return "巫巫女"  # 默认角色


def generate_audio(story_file: str, force: bool = False) -> bool:
    """
    为故事生成音频
    
    Args:
        story_file: 故事文件路径
        force: 是否强制重新生成
    
    Returns:
        成功返回 True，失败返回 False
    """
    # 获取故事文件名（不含扩展名）
    story_name = Path(story_file).stem
    
    # 输出音频路径
    audio_output = AUDIO_DIR / f"{story_name}.mp3"
    
    # 检查音频是否已存在
    if audio_output.exists() and not force:
        print(f"✓ 音频已存在: {audio_output}")
        print(f"  大小: {audio_output.stat().st_size / 1024:.1f} KB")
        print("  使用 --force 参数可强制重新生成")
        return True
    
    # 读取故事内容
    print(f"读取故事: {story_file}")
    title, content = extract_story_content(story_file)
    print(f"  标题: {title}")
    print(f"  长度: {len(content)} 字符")
    
    # 检测主要角色
    main_character = detect_main_character(content)
    print(f"  主要角色: {main_character}")
    print()
    
    # 检查 API 密钥
    if not MINIMAX_API_KEY:
        print("✗ 未设置 MINIMAX_API_KEY")
        print("  请在 .env 文件中设置 MINIMAX_API_KEY")
        return False
    
    # 获取角色配置
    character_config = CHARACTERS.get(main_character, {})
    voice_id = character_config.get("minimax_voice_id", MINIMAX_VOICE_ID)
    emotion = character_config.get("minimax_emotion", MINIMAX_EMOTION)
    
    if not voice_id:
        print("⚠ 警告: 角色未配置 minimax_voice_id")
        print("  将使用默认音色: female-tianmeijiaojia")
        voice_id = "female-tianmeijiaojia"
    
    print(f"语音合成配置:")
    print(f"  模型: {MINIMAX_MODEL}")
    print(f"  音色ID: {voice_id}")
    print(f"  情感: {emotion}")
    print()
    
    # 创建 TTS 客户端
    print("开始生成音频...")
    tts = MiniMaxTTS(api_key=MINIMAX_API_KEY)
    
    # 合成语音
    audio_data = tts.synthesize_speech(
        text=content,
        voice_id=voice_id,
        model=MINIMAX_MODEL,
        emotion=emotion
    )
    
    if not audio_data:
        print("✗ 音频生成失败")
        return False
    
    # 保存音频
    print(f"保存路径: {audio_output.absolute()}")
    try:
        with open(audio_output, 'wb') as f:
            f.write(audio_data)
        print(f"✓ 音频已保存: {audio_output}")
        print(f"  大小: {len(audio_data) / 1024:.1f} KB")
        print(f"  文件存在: {audio_output.exists()}")
    except Exception as e:
        print(f"✗ 保存失败: {e}")
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="巫巫女故事配音工具 - 使用 MiniMax TTS 生成故事语音",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'story',
        help='故事文件路径（如：01-巫巫女的心变了.md）'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='强制重新生成，即使音频已存在'
    )
    
    args = parser.parse_args()
    
    # 检查故事文件是否存在
    story_path = STORIES_DIR / args.story
    if not story_path.exists():
        print(f"✗ 故事文件不存在: {story_path}")
        sys.exit(1)
    
    # 确保音频目录存在
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    
    # 生成音频
    print("=" * 60)
    print("巫巫女故事配音工具")
    print("=" * 60)
    print()
    
    success = generate_audio(story_path, force=args.force)
    
    print()
    if success:
        print("=" * 60)
        print("✓ 配音完成")
        print("=" * 60)
        sys.exit(0)
    else:
        print("=" * 60)
        print("✗ 配音失败")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()