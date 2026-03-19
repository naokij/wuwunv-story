#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巫巫女故事配音工具 - 本地 TTS 版本
使用 Qwen3-TTS Base 模型（mlx-audio）为故事生成语音
支持声音克隆，在 Mac Apple Silicon 上本地运行
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
    STORIES_DIR,
    AUDIO_DIR,
    REFERENCES_DIR
)


# ==================== 本地 TTS 配置 ====================

# 可用模型
AVAILABLE_MODELS = {
    "0.6b": "mlx-community/Qwen3-TTS-12Hz-0.6B-Base-bf16",
    "1.7b": "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16",
}

# 默认模型
DEFAULT_MODEL = "0.6b"

# 参考音频配置（用于声音克隆）
DEFAULT_REF_AUDIO = REFERENCES_DIR / "taozi-ref.wav"
DEFAULT_REF_TEXT = "巫巫女坐在小木屋的台阶上，彩虹披风被月光晒的暖暖的。"

# 备选参考音频位置
ALT_REF_AUDIO_PATHS = [
    Path(__file__).parent.parent / "local_tts_test" / "taozi-ref.wav",
    Path(__file__).parent.parent / "audio" / "references" / "taozi-ref.wav",
]


def find_ref_audio() -> Path:
    """查找参考音频文件"""
    # 优先使用默认位置
    if DEFAULT_REF_AUDIO.exists():
        return DEFAULT_REF_AUDIO
    
    # 检查备选位置
    for path in ALT_REF_AUDIO_PATHS:
        if path.exists():
            return path
    
    raise FileNotFoundError(
        f"参考音频文件不存在。\n"
        f"请将参考音频放置到以下位置之一：\n"
        f"  - {DEFAULT_REF_AUDIO}\n"
        f"  - {ALT_REF_AUDIO_PATHS[0]}\n"
        f"或使用 --ref-audio 参数指定路径"
    )


def extract_story_config(story_file: str) -> tuple[str, str, dict]:
    """
    从 Markdown 文件中提取故事内容和配置
    
    Args:
        story_file: 故事文件路径
    
    Returns:
        (故事标题, 故事内容, frontmatter配置字典)
    """
    with open(story_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析 frontmatter
    frontmatter = {}
    if content.startswith('---'):
        import yaml
        match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL)
        if match:
            try:
                frontmatter = yaml.safe_load(match.group(1))
            except:
                pass
    
    # 提取第一个标题（作为故事标题）
    title = frontmatter.get('title', '')
    if not title:
        title_match = re.search(r'^#\s*(.+)', content, re.MULTILINE)
        title = title_match.group(1).strip() if title_match else "未命名故事"
    
    # 移除 frontmatter
    if content.startswith('---'):
        content = re.sub(r'^---.*?---', '', content, count=1, flags=re.DOTALL)
    
    # 移除标题行
    content = re.sub(r'^#\s*.+\n?', '', content, flags=re.MULTILINE)
    
    # 清理空白
    content = content.strip()
    
    # 把标题加回到内容开头（用于配音）
    if title:
        content = f"{title}。\n\n{content}"
    
    return title, content, frontmatter


def generate_audio_local(
    story_file: str,
    model_size: str = "0.6b",
    ref_audio: str = None,
    ref_text: str = None,
    output_format: str = "wav",
    force: bool = False,
    verbose: bool = True
) -> bool:
    """
    使用本地 TTS 模型为故事生成音频
    
    Args:
        story_file: 故事文件路径
        model_size: 模型大小 ("0.6b" 或 "1.7b")
        ref_audio: 参考音频路径
        ref_text: 参考音频对应的文本
        output_format: 输出格式 ("wav" 或 "mp3")
        force: 是否强制重新生成
        verbose: 是否显示详细输出
    
    Returns:
        成功返回 True，失败返回 False
    """
    # 获取故事文件名（不含扩展名）
    story_name = Path(story_file).stem
    
    # 输出音频路径
    audio_output = AUDIO_DIR / f"{story_name}.{output_format}"
    
    # 检查音频是否已存在
    if audio_output.exists() and not force:
        print(f"✓ 音频已存在: {audio_output}")
        print(f"  大小: {audio_output.stat().st_size / 1024:.1f} KB")
        print("  使用 --force 参数可强制重新生成")
        return True
    
    # 读取故事内容
    if verbose:
        print(f"读取故事: {story_file}")
    title, content, _ = extract_story_config(story_file)
    if verbose:
        print(f"  标题: {title}")
        print(f"  长度: {len(content)} 字符")
    
    # 获取模型路径
    model_path = AVAILABLE_MODELS.get(model_size.lower())
    if not model_path:
        print(f"✗ 无效的模型大小: {model_size}")
        print(f"  可用模型: {', '.join(AVAILABLE_MODELS.keys())}")
        return False
    
    # 确定参考音频
    if ref_audio:
        ref_audio_path = Path(ref_audio)
        if not ref_audio_path.exists():
            print(f"✗ 参考音频不存在: {ref_audio}")
            return False
    else:
        try:
            ref_audio_path = find_ref_audio()
        except FileNotFoundError as e:
            print(f"✗ {e}")
            return False
    
    if not ref_text:
        ref_text = DEFAULT_REF_TEXT
    
    if verbose:
        print()
        print("本地 TTS 配置:")
        print(f"  模型: {model_path}")
        print(f"  参考音频: {ref_audio_path}")
        print(f"  参考文本: {ref_text}")
        print()
    
    # 加载模型
    if verbose:
        print("加载模型...")
    try:
        from mlx_audio.tts.utils import load_model
        from mlx_audio.tts.generate import generate_audio
    except ImportError:
        print("✗ 未安装 mlx-audio")
        print("  请运行: pip install mlx-audio")
        return False
    
    model = load_model(model_path)
    
    # 创建临时输出目录
    temp_dir = AUDIO_DIR / ".temp_local_tts"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    # 生成音频
    if verbose:
        print("生成音频中...")
        print(f"  预计耗时: {len(content) * 0.6:.0f} 秒 (0.6B) 或 {len(content) * 1.0:.0f} 秒 (1.7B)")
    
    start_time = time.time()
    
    try:
        generate_audio(
            model=model,
            text=content,
            lang_code='Chinese',
            ref_audio=str(ref_audio_path),
            ref_text=ref_text,
            output_path=str(temp_dir),
            verbose=verbose
        )
    except Exception as e:
        print(f"✗ 音频生成失败: {e}")
        return False
    
    # 查找生成的文件
    generated_files = list(temp_dir.glob("audio_*.wav"))
    if not generated_files:
        print("✗ 未找到生成的音频文件")
        return False
    
    # 使用最新的文件
    generated_file = max(generated_files, key=lambda f: f.stat().st_mtime)
    
    # 如果需要转换为 MP3
    if output_format == "mp3":
        if verbose:
            print("转换为 MP3...")
        import subprocess
        mp3_output = audio_output
        wav_output = generated_file
        
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", str(wav_output),
                "-codec:a", "libmp3lame", "-qscale:a", "2",
                str(mp3_output)
            ], check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"✗ MP3 转换失败: {e}")
            return False
        except FileNotFoundError:
            print("✗ 未找到 ffmpeg，请先安装: brew install ffmpeg")
            return False
    else:
        # 直接移动 WAV 文件
        import shutil
        shutil.move(str(generated_file), str(audio_output))
    
    # 清理临时文件
    for f in temp_dir.glob("*"):
        if f != generated_file or output_format == "mp3":
            f.unlink()
    if not any(temp_dir.iterdir()):
        temp_dir.rmdir()
    
    elapsed_time = time.time() - start_time
    
    # 获取音频时长
    import soundfile as sf
    audio_data, sr = sf.read(str(audio_output))
    duration = len(audio_data) / sr
    
    if verbose:
        print()
        print(f"✓ 音频已保存: {audio_output}")
        print(f"  时长: {duration:.1f} 秒 ({duration/60:.1f} 分钟)")
        print(f"  大小: {audio_output.stat().st_size / 1024:.1f} KB")
        print(f"  耗时: {elapsed_time:.1f} 秒")
        print(f"  实时倍率: {duration/elapsed_time:.2f}x")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="巫巫女故事配音工具 - 本地 TTS 版本（Qwen3-TTS）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认 0.6B 模型生成音频
  python scripts/generate_audio_local.py "01-巫巫女的心变了.md"
  
  # 使用 1.7B 模型（质量更高，速度更慢）
  python scripts/generate_audio_local.py "01-巫巫女的心变了.md" --model 1.7b
  
  # 强制重新生成
  python scripts/generate_audio_local.py "01-巫巫女的心变了.md" --force
  
  # 指定参考音频
  python scripts/generate_audio_local.py "01-巫巫女的心变了.md" --ref-audio ./my-voice.wav

性能参考:
  - 0.6B 模型: 约 0.32x 实时倍率（10分钟音频约需 31 分钟）
  - 1.7B 模型: 约 0.19x 实时倍率（10分钟音频约需 53 分钟）
        """
    )
    
    parser.add_argument(
        'story',
        help='故事文件路径（如：01-巫巫女的心变了.md）'
    )
    parser.add_argument(
        '--model', '-m',
        choices=['0.6b', '1.7b'],
        default=DEFAULT_MODEL,
        help=f'模型大小，默认: {DEFAULT_MODEL}（更快）'
    )
    parser.add_argument(
        '--ref-audio',
        help='参考音频路径（用于声音克隆）'
    )
    parser.add_argument(
        '--ref-text',
        help='参考音频对应的文本'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['wav', 'mp3'],
        default='wav',
        help='输出格式，默认: wav'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='强制重新生成，即使音频已存在'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='静默模式，减少输出'
    )
    
    args = parser.parse_args()
    
    # 检查故事文件是否存在
    story_path = STORIES_DIR / args.story
    if not story_path.exists():
        # 尝试直接使用输入路径
        story_path = Path(args.story)
        if not story_path.exists():
            print(f"✗ 故事文件不存在: {args.story}")
            sys.exit(1)
    
    # 确保音频目录存在
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    
    # 生成音频
    print("=" * 60)
    print("巫巫女故事配音工具 - 本地 TTS")
    print("=" * 60)
    print()
    
    success = generate_audio_local(
        story_file=str(story_path),
        model_size=args.model,
        ref_audio=args.ref_audio,
        ref_text=args.ref_text,
        output_format=args.format,
        force=args.force,
        verbose=not args.quiet
    )
    
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
