#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为已存在的 MP3 文件添加元数据
"""

import sys
import os
from pathlib import Path

# 添加 scripts 目录到路径，以便导入其他模块
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from process_audio import find_cover_image, find_story_file, read_story_content, add_metadata


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python scripts/add_metadata_to_existing.py <MP3文件> [封面图片] [故事文件]")
        print("\n示例:")
        print("  python scripts/add_metadata_to_existing.py audio/01-巫巫女的心变了.mp3")
        print("  python scripts/add_metadata_to_existing.py audio/01-巫巫女的心变了.mp3 cover.jpg story.md")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    cover_path = sys.argv[2] if len(sys.argv) > 2 else None
    story_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    if not os.path.exists(audio_path):
        print(f"错误: 文件不存在: {audio_path}")
        sys.exit(1)
    
    print(f"处理文件: {audio_path}\n")
    
    # 查找封面
    print("查找封面图片...")
    if cover_path is None:
        cover_path = find_cover_image(audio_path)
    else:
        print(f"  使用指定的封面: {cover_path}")
    
    # 查找故事文件
    print("\n查找故事文件...")
    if story_path is None:
        story_path = find_story_file(audio_path)
    else:
        print(f"  使用指定的故事文件: {story_path}")
    
    story_title = None
    story_content = None
    if story_path and os.path.exists(story_path):
        print(f"  读取故事内容...")
        story_title, story_content = read_story_content(story_path)
        print(f"  ✓ 标题: {story_title}")
        print(f"  ✓ 内容长度: {len(story_content)} 字符")
    else:
        print("  ⚠ 未找到故事文件")
    
    # 添加元数据
    add_metadata(audio_path, cover_path, story_title, story_content)
    
    print(f"\n✓ 完成！可以运行以下命令验证:")
    print(f"  python scripts/verify_audio.py \"{audio_path}\"")


if __name__ == '__main__':
    main()
