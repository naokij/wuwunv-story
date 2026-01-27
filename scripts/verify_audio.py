#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证 MP3 文件的元数据和封面
"""

import sys
import os
from pathlib import Path

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, APIC
    from mutagen import File
except ImportError:
    print("错误: 需要安装 mutagen 库")
    print("请运行: pip install mutagen")
    sys.exit(1)


def verify_audio(audio_path: str):
    """验证音频文件的元数据和封面"""
    if not os.path.exists(audio_path):
        print(f"错误: 文件不存在: {audio_path}")
        return False
    
    print(f"正在验证: {audio_path}\n")
    print("=" * 60)
    
    try:
        audio_file = MP3(audio_path, ID3=ID3)
    except Exception as e:
        print(f"✗ 无法读取文件: {e}")
        return False
    
    # 基本信息
    print("\n【基本信息】")
    print(f"  时长: {audio_file.info.length:.2f} 秒")
    print(f"  比特率: {audio_file.info.bitrate} bps")
    print(f"  采样率: {audio_file.info.sample_rate} Hz")
    
    # 元数据
    print("\n【元数据】")
    
    # 标题
    if 'TIT2' in audio_file:
        title = str(audio_file['TIT2'][0])
        print(f"  ✓ 标题: {title}")
    else:
        print("  ✗ 标题: 未设置")
    
    # 艺术家
    if 'TPE1' in audio_file:
        artist = str(audio_file['TPE1'][0])
        print(f"  ✓ 艺术家: {artist}")
    else:
        print("  ✗ 艺术家: 未设置")
    
    # 专辑
    if 'TALB' in audio_file:
        album = str(audio_file['TALB'][0])
        print(f"  ✓ 专辑: {album}")
    else:
        print("  ✗ 专辑: 未设置")
    
    # 类型
    if 'TCON' in audio_file:
        genre = str(audio_file['TCON'][0])
        print(f"  ✓ 类型: {genre}")
    else:
        print("  ✗ 类型: 未设置")
    
    # 封面
    print("\n【封面图片】")
    apic_found = False
    for key in audio_file.keys():
        if key.startswith('APIC'):
            apic = audio_file[key]
            mime = apic.mime
            desc = apic.desc
            apic_data = apic.data
            print(f"  ✓ 封面已嵌入")
            print(f"    - 标签键: {key}")
            print(f"    - MIME 类型: {mime}")
            print(f"    - 描述: {desc}")
            print(f"    - 大小: {len(apic_data)} 字节 ({len(apic_data)/1024:.2f} KB)")
            
            # 保存封面到文件以便查看
            cover_ext = {
                'image/jpeg': '.jpg',
                'image/png': '.png',
                'image/gif': '.gif',
                'image/bmp': '.bmp'
            }.get(mime, '.jpg')
            
            cover_path = Path(audio_path).parent / f"{Path(audio_path).stem}_cover{cover_ext}"
            try:
                with open(cover_path, 'wb') as f:
                    f.write(apic_data)
                print(f"    - 已保存到: {cover_path}")
            except Exception as e:
                print(f"    - 保存封面失败: {e}")
            apic_found = True
            break
    
    if not apic_found:
        print("  ✗ 封面: 未嵌入")
        print(f"    可用标签: {list(audio_file.keys())}")
    
    # 简介
    print("\n【简介】")
    comm_found = False
    for key in audio_file.keys():
        if key.startswith('COMM'):
            comm = audio_file[key]
            intro = str(comm[0])
            print(f"  ✓ 简介已嵌入")
            print(f"    - 标签键: {key}")
            print(f"    - 长度: {len(intro)} 字符")
            print(f"    - 预览: {intro[:100]}...")
            comm_found = True
            break
    
    if not comm_found:
        print("  ✗ 简介: 未嵌入")
    
    # 全文
    print("\n【全文】")
    uslt_found = False
    for key in audio_file.keys():
        if key.startswith('USLT'):
            uslt = audio_file[key]
            # USLT 对象有 text 属性
            if hasattr(uslt, 'text'):
                content = str(uslt.text)
            else:
                # 如果是列表，取第一个
                content = str(uslt) if not isinstance(uslt, list) else str(uslt[0])
            print(f"  ✓ 全文已嵌入")
            print(f"    - 标签键: {key}")
            print(f"    - 长度: {len(content)} 字符")
            print(f"    - 预览: {content[:100]}...")
            uslt_found = True
            break
    
    if not uslt_found:
        print("  ✗ 全文: 未嵌入")
    
    print("\n" + "=" * 60)
    
    # 总结
    print("\n【验证总结】")
    has_cover = any(k.startswith('APIC') for k in audio_file.keys())
    has_title = 'TIT2' in audio_file
    has_intro = any(k.startswith('COMM') for k in audio_file.keys())
    has_content = any(k.startswith('USLT') for k in audio_file.keys())
    
    all_good = has_cover and has_title and has_intro and has_content
    
    if all_good:
        print("  ✓ 所有元数据都已正确嵌入！")
    else:
        print("  ⚠ 部分元数据缺失:")
        if not has_cover:
            print("    - 封面")
        if not has_title:
            print("    - 标题")
        if not has_intro:
            print("    - 简介")
        if not has_content:
            print("    - 全文")
    
    return all_good


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python scripts/verify_audio.py <MP3文件>")
        print("\n示例:")
        print("  python scripts/verify_audio.py audio/01-巫巫女的心变了.mp3")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    success = verify_audio(audio_path)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
