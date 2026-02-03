#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巫巫女故事完整生成工具
自动为故事生成音频和封面
"""

import sys
import os
import argparse
from pathlib import Path

# 添加 scripts 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 导入子模块
from generate_audio import generate_audio
from generate_cover import generate_cover


def generate_story(story_file: str, force: bool = False, skip_audio: bool = False, skip_cover: bool = False) -> bool:
    """
    完整生成故事（音频 + 封面）
    
    Args:
        story_file: 故事文件路径
        force: 是否强制重新生成
        skip_audio: 跳过音频生成
        skip_cover: 跳过封面生成
    
    Returns:
        成功返回 True，失败返回 False
    """
    story_name = Path(story_file).stem
    
    print(f"故事: {story_name}")
    print(f"文件: {story_file}")
    print()
    
    # 生成音频
    if not skip_audio:
        print("=" * 60)
        print("步骤 1/2: 生成音频")
        print("=" * 60)
        audio_success = generate_audio(story_file, force=force)
        
        if not audio_success:
            print("✗ 音频生成失败，终止")
            return False
        print()
    else:
        print("⏭ 跳过音频生成")
        print()
    
    # 生成封面
    if not skip_cover:
        print("=" * 60)
        print("步骤 2/2: 生成封面")
        print("=" * 60)
        cover_success = generate_cover(story_file, force=force)
        
        if not cover_success:
            print("⚠ 封面生成失败，但音频已生成")
            return True  # 音频成功即返回 True
        print()
    else:
        print("⏭ 跳过封面生成")
        print()
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="巫巫女故事完整生成工具 - 自动生成音频和封面",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'story',
        help='故事文件路径（如：01-巫巫女的心变了.md）'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='强制重新生成，即使文件已存在'
    )
    parser.add_argument(
        '--skip-audio',
        action='store_true',
        help='跳过音频生成'
    )
    parser.add_argument(
        '--skip-cover',
        action='store_true',
        help='跳过封面生成'
    )
    
    args = parser.parse_args()
    
    # 检查故事文件是否存在
    from config import STORIES_DIR
    story_path = STORIES_DIR / args.story
    if not story_path.exists():
        print(f"✗ 故事文件不存在: {story_path}")
        sys.exit(1)
    
    # 生成故事
    print("=" * 60)
    print("巫巫女故事完整生成工具")
    print("=" * 60)
    print()
    
    success = generate_story(
        story_path,
        force=args.force,
        skip_audio=args.skip_audio,
        skip_cover=args.skip_cover
    )
    
    print()
    print("=" * 60)
    if success:
        print("✓ 故事生成完成")
    else:
        print("✗ 故事生成失败")
    print("=" * 60)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()