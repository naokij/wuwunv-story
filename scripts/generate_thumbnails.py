#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为音频封面批量生成缩略图

用法：
    python scripts/generate_thumbnails.py

说明：
- 扫描项目根目录下的 audio/ 目录
- 查找其中的 .jpg / .jpeg 封面文件
- 在 audio/thumbnails/ 下生成最长边不超过 400 像素的缩略图
- 缩略图命名为：原文件名去扩展名后加 `_thumb`，再加原扩展名
  例如：`01-巫巫女的心变了.jpeg` -> `01-巫巫女的心变了_thumb.jpeg`
"""

import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("错误：需要安装 Pillow 库才能生成缩略图。")
    print("请运行：pip install pillow")
    sys.exit(1)


def generate_thumbnails(
    audio_dir: Path,
    thumb_dir: Path,
    max_size: int = 400,
) -> None:
    """在 audio_dir 中为所有封面图片生成缩略图到 thumb_dir"""
    if not audio_dir.exists():
        print(f"错误：目录不存在：{audio_dir}")
        return

    thumb_dir.mkdir(parents=True, exist_ok=True)

    exts = {".jpg", ".jpeg", ".png"}
    images = [p for p in audio_dir.iterdir() if p.suffix.lower() in exts]

    if not images:
        print(f"在 {audio_dir} 下没有找到封面图片。")
        return

    print(f"在 {audio_dir} 下找到 {len(images)} 张封面，将生成缩略图到 {thumb_dir}。")

    for img_path in images:
        try:
            rel_name = img_path.stem + "_thumb" + img_path.suffix
            out_path = thumb_dir / rel_name

            with Image.open(img_path) as im:
                im.thumbnail((max_size, max_size))
                im.save(out_path, optimize=True, quality=85)

            print(f"✓ 生成缩略图：{out_path}")
        except Exception as e:
            print(f"✗ 生成缩略图失败：{img_path} -> {e}")


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    audio_dir = project_root / "audio"
    thumb_dir = audio_dir / "thumbnails"

    generate_thumbnails(audio_dir, thumb_dir)


if __name__ == "__main__":
    main()

