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

from process_audio import find_cover_image, find_story_file, read_story_content
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TCON, COMM, USLT


def add_metadata_fixed(audio_path: str, cover_path: str = None,
                       story_title: str = None, story_content: str = None):
    """为 MP3 文件添加元数据和封面（修复版：正确删除旧封面）"""
    print("\n正在添加元数据和封面...")
    
    try:
        audio_file = MP3(audio_path, ID3=ID3)
    except:
        audio_file = MP3(audio_path)
        audio_file.add_tags()
    
    # 添加标题
    if story_title:
        audio_file['TIT2'] = TIT2(encoding=3, text=story_title)
        print(f"  ✓ 添加标题: {story_title}")
    
    # 添加艺术家
    audio_file['TPE1'] = TPE1(encoding=3, text='巫巫女睡前故事')
    print("  ✓ 添加艺术家: 巫巫女睡前故事")
    
    # 添加专辑
    audio_file['TALB'] = TALB(encoding=3, text='巫巫女睡前故事集')
    print("  ✓ 添加专辑: 巫巫女睡前故事集")
    
    # 添加类型
    audio_file['TCON'] = TCON(encoding=3, text='儿童故事')
    print("  ✓ 添加类型: 儿童故事")
    
    # 添加封面（修复：正确删除所有旧封面）
    if cover_path and os.path.exists(cover_path):
        try:
            with open(cover_path, 'rb') as f:
                cover_data = f.read()
            
            # 确定 MIME 类型
            ext = Path(cover_path).suffix.lower()
            mime_types = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.bmp': 'image/bmp'
            }
            mime_type = mime_types.get(ext, 'image/jpeg')
            
            # 修复：删除所有 APIC 标签（包括 APIC:Cover, APIC: 等）
            keys_to_delete = [key for key in audio_file.keys() if key.startswith('APIC')]
            for key in keys_to_delete:
                del audio_file[key]
                print(f"  ✓ 删除旧封面标签: {key}")
            
            # 添加新封面
            audio_file['APIC'] = APIC(
                encoding=3,
                mime=mime_type,
                type=3,  # 封面图片
                desc='Cover',
                data=cover_data
            )
            print(f"  ✓ 添加封面: {cover_path} ({len(cover_data)/1024:.2f} KB)")
        except Exception as e:
            print(f"  ✗ 添加封面失败: {e}")
    elif cover_path:
        print(f"  ✗ 封面文件不存在: {cover_path}")
    else:
        print("  ⚠ 未提供封面路径")
    
    # 添加简介
    if story_content:
        intro = story_content[:500] + "..." if len(story_content) > 500 else story_content
        
        # 删除旧的注释
        keys_to_delete = [key for key in audio_file.keys() if key.startswith('COMM')]
        for key in keys_to_delete:
            del audio_file[key]
        
        audio_file['COMM'] = COMM(
            encoding=3,
            lang='chi',
            desc='简介',
            text=intro
        )
        print(f"  ✓ 添加简介 ({len(intro)} 字符)")
    
    # 添加全文歌词
    if story_content:
        # 删除旧的歌词
        keys_to_delete = [key for key in audio_file.keys() if key.startswith('USLT')]
        for key in keys_to_delete:
            del audio_file[key]
        
        audio_file['USLT'] = USLT(
            encoding=3,
            lang='chi',
            desc='全文',
            text=story_content
        )
        print(f"  ✓ 添加全文 ({len(story_content)} 字符)")
    
    # 保存
    audio_file.save()
    print("✓ 元数据添加完成\n")


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
    
    # 添加元数据（使用修复版函数）
    add_metadata_fixed(audio_path, cover_path, story_title, story_content)
    
    print(f"✓ 完成！可以运行以下命令验证:")
    print(f"  python scripts/verify_audio.py \"{audio_path}\"")


if __name__ == '__main__':
    main()
