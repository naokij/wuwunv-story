#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量为 audio 目录中的 MP3 文件添加元数据
"""

import sys
import os
from pathlib import Path

# 添加 scripts 目录到路径，以便导入其他模块
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from process_audio import find_cover_image, find_story_file, read_story_content, add_metadata
from mutagen.mp3 import MP3
from mutagen.id3 import ID3


def has_complete_metadata(audio_path: str) -> bool:
    """检查 MP3 文件是否有完整的元数据"""
    try:
        audio_file = MP3(audio_path, ID3=ID3)
        
        # 检查是否有标题
        has_title = 'TIT2' in audio_file
        
        # 检查是否有封面
        has_cover = any(k.startswith('APIC') for k in audio_file.keys())
        
        # 检查是否有简介
        has_intro = any(k.startswith('COMM') for k in audio_file.keys())
        
        # 检查是否有全文
        has_content = any(k.startswith('USLT') for k in audio_file.keys())
        
        return has_title and has_cover and has_intro and has_content
    except:
        return False


def process_audio_file(audio_path: str, dry_run: bool = False) -> bool:
    """处理单个音频文件"""
    audio_path = Path(audio_path).resolve()
    
    print(f"\n{'='*60}")
    print(f"处理: {audio_path.name}")
    print(f"{'='*60}")
    
    # 检查是否已有完整元数据
    if has_complete_metadata(str(audio_path)):
        print("  ✓ 已有完整元数据，跳过")
        return True
    
    if dry_run:
        print("  [模拟运行] 将添加元数据")
        return True
    
    # 查找封面
    print("\n查找封面图片...")
    cover_path = find_cover_image(str(audio_path))
    
    # 查找故事文件
    print("\n查找故事文件...")
    story_path = find_story_file(str(audio_path))
    
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
    if cover_path or story_title:
        add_metadata(str(audio_path), cover_path, story_title, story_content)
        return True
    else:
        print("  ⚠ 未找到封面和故事文件，跳过")
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='批量为 audio 目录中的 MP3 文件添加元数据')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行，不实际修改文件')
    parser.add_argument('--dir', default='audio', help='要处理的目录（默认: audio）')
    args = parser.parse_args()
    
    audio_dir = Path(args.dir).resolve()
    if not audio_dir.exists():
        print(f"错误: 目录不存在: {audio_dir}")
        sys.exit(1)
    
    # 查找所有 MP3 文件
    mp3_files = list(audio_dir.glob('*.mp3')) + list(audio_dir.glob('*.MP3'))
    mp3_files.sort()
    
    if not mp3_files:
        print(f"在 {audio_dir} 中未找到 MP3 文件")
        sys.exit(0)
    
    print(f"找到 {len(mp3_files)} 个 MP3 文件")
    if args.dry_run:
        print("【模拟运行模式】")
    
    # 统计
    processed = 0
    skipped = 0
    failed = 0
    
    # 处理每个文件
    for mp3_file in mp3_files:
        try:
            # 先检查是否已有完整元数据
            if has_complete_metadata(str(mp3_file)):
                skipped += 1
                continue
            
            # 处理文件
            if process_audio_file(str(mp3_file), args.dry_run):
                processed += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  ✗ 处理失败: {e}")
            failed += 1
            import traceback
            traceback.print_exc()
    
    # 输出统计
    print(f"\n{'='*60}")
    print("处理完成！")
    print(f"{'='*60}")
    print(f"总计: {len(mp3_files)} 个文件")
    print(f"已处理: {processed} 个")
    print(f"已跳过: {skipped} 个（已有完整元数据或未找到对应文件）")
    if failed > 0:
        print(f"失败: {failed} 个")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
