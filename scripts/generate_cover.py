#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巫巫女故事封面生成工具
使用火山引擎即梦 AI API 为故事生成封面图片
"""

import sys
import os
import argparse
import re
import time
from pathlib import Path

# 添加 scripts 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    VOLCENGINE_ACCESS_KEY,
    VOLCENGINE_SECRET_KEY,
    VOLCENGINE_APP_ID,
    JIMENG_IMAGE_QUALITY,
    JIMENG_REFERENCE_WEIGHT,
    JIMENG_ASPECT_RATIO,
    IMAGE_QUALITY,
    CHARACTERS,
    REFERENCES_DIR,
    STORIES_DIR,
    AUDIO_DIR
)
from volcengine_api import VolcEngineJimeng


def parse_frontmatter(content: str) -> dict:
    """
    解析 Markdown 文件的 frontmatter
    
    Args:
        content: Markdown 文件内容
    
    Returns:
        frontmatter 字典
    """
    frontmatter = {}
    
    if content.startswith('---'):
        # 提取 frontmatter 内容
        match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
        if match:
            fm_text = match.group(1)
            try:
                import yaml
                frontmatter = yaml.safe_load(fm_text) or {}
            except Exception as e:
                print(f"  ⚠ YAML 解析失败，使用简单解析: {e}")
                # 降级到简单解析
                for line in fm_text.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 处理列表类型（如 cover_characters）
                        if key in ['cover_characters', 'cover_character']:
                            # 移除方括号，按逗号分割
                            value = value.strip('[]').replace('\n', '').replace('"', '').replace("'", "")
                            if value:
                                frontmatter[key] = [v.strip() for v in value.split(',')]
                        else:
                            # 移除引号
                            value = value.strip('"').strip("'")
                            frontmatter[key] = value
    
    return frontmatter


def extract_cover_config(story_file: str) -> tuple[str, list[str]]:
    """
    从故事文件中提取封面配置
    
    Args:
        story_file: 故事文件路径
    
    Returns:
        (封面提示词, 角色列表)
    """
    with open(story_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析 frontmatter
    frontmatter = parse_frontmatter(content)
    
    # 获取封面提示词
    prompt = frontmatter.get('cover_prompt', '')
    
    # 获取角色列表
    characters = frontmatter.get('cover_characters', [])
    if not characters:
        characters = frontmatter.get('cover_character', [])
    
    return prompt, characters


def get_reference_image(character: str) -> Path | None:
    """
    获取角色的参考图片路径
    
    Args:
        character: 角色名称
    
    Returns:
        参考图片路径，不存在返回 None
    """
    character_config = CHARACTERS.get(character, {})
    ref_image_path = character_config.get('reference_image')
    
    if ref_image_path:
        ref_path = Path(ref_image_path)
        if ref_path.exists():
            return ref_path
    
    # 尝试使用默认参考图
    default_ref = REFERENCES_DIR / f"{character}_reference.jpg"
    if default_ref.exists():
        return default_ref
    
    return None


def generate_cover(story_file: str, force: bool = False) -> bool:
    """
    为故事生成封面
    
    Args:
        story_file: 故事文件路径
        force: 是否强制重新生成
    
    Returns:
        成功返回 True，失败返回 False
    """
    # 获取故事文件名（不含扩展名）
    story_name = Path(story_file).stem
    
    # 输出封面路径
    cover_output = AUDIO_DIR / f"{story_name}.jpeg"
    
    # 检查封面是否已存在
    if cover_output.exists() and not force:
        print(f"✓ 封面已存在: {cover_output}")
        print(f"  大小: {cover_output.stat().st_size / 1024:.1f} KB")
        print("  使用 --force 参数可强制重新生成")
        return True
    
    # 提取封面配置
    print(f"读取故事: {story_file}")
    prompt, characters = extract_cover_config(story_file)
    
    if not prompt:
        print("✗ 未找到封面提示词 (cover_prompt)")
        print("  请在故事文件的 frontmatter 中添加 cover_prompt 字段")
        return False
    
    print(f"  提示词: {prompt}")
    print(f"  角色: {', '.join(characters) if characters else '无'}")
    print()
    
    # 检查 API 密钥
    if not VOLCENGINE_ACCESS_KEY or not VOLCENGINE_SECRET_KEY:
        print("✗ 未设置火山引擎 API 密钥")
        print("  请在 .env 文件中设置 VOLCENGINE_ACCESS_KEY 和 VOLCENGINE_SECRET_KEY")
        return False
    
    # 获取参考图片
    reference_images = []
    for character in characters:
        ref_path = get_reference_image(character)
        if ref_path:
            reference_images.append(ref_path)
            print(f"  参考图: {ref_path.name}")
    
    if reference_images:
        print(f"  参考图数量: {len(reference_images)}")
        print(f"  参考权重: {JIMENG_REFERENCE_WEIGHT}")
    else:
        print("  ⚠ 未找到参考图，将使用纯文字生成")
    print()
    
    # 创建即梦客户端
    print("开始生成封面...")
    jimeng = VolcEngineJimeng(
        access_key=VOLCENGINE_ACCESS_KEY,
        secret_key=VOLCENGINE_SECRET_KEY,
        app_id=VOLCENGINE_APP_ID
    )
    
    # 在 prompt 中添加宽高比描述
    prompt_with_ratio = f"{prompt}，1:1 正方形构图，square format 1:1 aspect ratio"
    
    # 生成封面
    print("  正在提交任务到即梦 AI...")
    print("  提示: 生成可能需要 30-60 秒，请耐心等待...")
    print(f"  使用宽高比: {JIMENG_ASPECT_RATIO}")
    result = jimeng.generate_image(
        prompt=prompt_with_ratio,
        reference_images=reference_images,
        reference_strength=JIMENG_REFERENCE_WEIGHT,
        aspect_ratio=JIMENG_ASPECT_RATIO,
        quality=IMAGE_QUALITY,
        max_retries=3  # 增加重试次数
    )
    
    if result.get("status") != "success":
        print(f"✗ 封面生成失败: {result.get('message', '未知错误')}")
        return False
    
    # 获取图片数据
    image_data = result.get("image_bytes")
    image_url = result.get("image_url")
    
    if not image_data and image_url:
        # 如果有 URL 但没有数据，尝试下载
        print(f"  从 URL 下载图片: {image_url[:60]}...")
        try:
            import requests
            response = requests.get(image_url, timeout=60)
            if response.status_code == 200:
                image_data = response.content
                print(f"  ✓ 下载成功: {len(image_data)/1024:.1f} KB")
            else:
                print(f"  ✗ 下载失败: HTTP {response.status_code}")
        except Exception as e:
            print(f"  ✗ 下载异常: {e}")
    
    if not image_data:
        print("✗ 未返回图片数据")
        return False
    
    # 保存封面
    print(f"保存路径: {cover_output.absolute()}")
    try:
        with open(cover_output, 'wb') as f:
            f.write(image_data)
        print(f"✓ 封面已保存: {cover_output}")
        print(f"  大小: {len(image_data) / 1024:.1f} KB")
        print(f"  文件存在: {cover_output.exists()}")
    except Exception as e:
        print(f"✗ 保存失败: {e}")
        return False
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="巫巫女故事封面生成工具 - 使用火山引擎即梦 AI 生成故事封面",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'story',
        help='故事文件路径（如：01-巫巫女的心变了.md）'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='强制重新生成，即使封面已存在'
    )
    
    args = parser.parse_args()
    
    # 检查故事文件是否存在
    story_path = STORIES_DIR / args.story
    if not story_path.exists():
        print(f"✗ 故事文件不存在: {story_path}")
        sys.exit(1)
    
    # 确保音频目录存在
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    
    # 生成封面
    print("=" * 60)
    print("巫巫女故事封面生成工具")
    print("=" * 60)
    print()
    
    success = generate_cover(story_path, force=args.force)
    
    print()
    if success:
        print("=" * 60)
        print("✓ 封面生成完成")
        print("=" * 60)
        sys.exit(0)
    else:
        print("=" * 60)
        print("✗ 封面生成失败")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()