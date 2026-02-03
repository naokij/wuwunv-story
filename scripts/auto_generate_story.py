#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巫巫女故事自动化生成工具
使用 MiniMax TTS API 和即梦 AI API 自动生成音频和封面
"""

import sys
import os
import yaml
import re
import subprocess
from pathlib import Path

# 添加 scripts 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    VOLCENGINE_ACCESS_KEY,
    VOLCENGINE_SECRET_KEY,
    MINIMAX_API_KEY,
    MINIMAX_MODEL,
    USE_MINIMAX_TTS,
    MINIMAX_SPEED,
    MINIMAX_VOL,
    MINIMAX_PITCH,
    CHARACTERS,
    REFERENCES_DIR,
    AUDIO_DIR,
    STORIES_DIR,
    IMAGE_SIZE,
    IMAGE_QUALITY,
    REFERENCE_WEIGHT,
    DEFAULT_STYLE_KEYWORDS,
    METADATA_ARTIST,
    METADATA_ALBUM,
    METADATA_GENRE,
    validate_config
)
from volcengine_api import VolcEngineJimeng

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, APIC, COMM, USLT
except ImportError:
    print("错误: 需要安装 mutagen 库")
    print("请运行: pip install mutagen")
    sys.exit(1)


def read_story_content(story_path: str) -> tuple[str, str, dict]:
    """
    读取故事内容，返回标题、正文和 frontmatter

    Args:
        story_path: 故事文件路径

    Returns:
        (标题, 正文, frontmatter)
    """
    try:
        with open(story_path, 'r', encoding='utf-8') as f:
            content = f.read()

        frontmatter = {}
        story_body = content

        # 检查是否有 YAML frontmatter
        if content.startswith('---'):
            # 找到 frontmatter 结束位置
            end_marker = content.find('\n---', 4)
            if end_marker != -1:
                frontmatter_text = content[4:end_marker]
                try:
                    frontmatter = yaml.safe_load(frontmatter_text) or {}
                except yaml.YAMLError as e:
                    print(f"警告: 解析 frontmatter 失败: {e}")
                story_body = content[end_marker + 4:].lstrip()

        lines = story_body.split('\n')
        raw_title = lines[0].strip() if lines else "未知故事"

        # 清理标题（去除 Markdown 标记）
        clean_title = re.sub(r'^#+\s*', '', raw_title)
        clean_title = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_title)
        clean_title = clean_title.strip()

        # 如果 frontmatter 中有标题，优先使用
        if frontmatter.get('title'):
            clean_title = frontmatter['title']

        return clean_title, story_body, frontmatter
    except Exception as e:
        print(f"读取故事文件失败: {e}")
        return "未知故事", "", {}

def extract_main_character(story_content: str) -> str:
    """
    从故事内容中提取主要角色

    Args:
        story_content: 故事正文

    Returns:
        主要角色名称
    """
    # 简单的关键词匹配
    if "巫巫女" in story_content:
        return "巫巫女"
    elif "莉莉" in story_content:
        return "莉莉"
    elif "欣欣" in story_content:
        return "欣欣"
    else:
        return "巫巫女"  # 默认


def split_text_for_tts(text: str, max_bytes: int = 1024) -> list:
    """
    将文本分割为适合 TTS 的片段
    
    Args:
        text: 原始文本
        max_bytes: 每段的最大字节数
        
    Returns:
        文本片段列表
    """
    # 按句子分割（中文句号、问号、感叹号）
    sentences = re.split(r'([。！？\n])', text)
    
    # 重新组合句子和标点
    segments = []
    current_segment = ""
    
    for i in range(0, len(sentences) - 1, 2):
        if i + 1 < len(sentences):
            sentence = sentences[i] + sentences[i + 1]
        else:
            sentence = sentences[i]
        
        # 检查是否可以添加到当前段
        if len((current_segment + sentence).encode('utf-8')) <= max_bytes:
            current_segment += sentence
        else:
            # 当前段已满，保存并开始新段
            if current_segment:
                segments.append(current_segment)
            current_segment = sentence
    
    # 添加最后一段
    if current_segment:
        segments.append(current_segment)
    
    # 如果分割后还有超长的单句，强制分割
    final_segments = []
    for seg in segments:
        if len(seg.encode('utf-8')) > max_bytes:
            # 按字符强制分割
            char_list = list(seg)
            temp = ""
            for char in char_list:
                if len((temp + char).encode('utf-8')) <= max_bytes:
                    temp += char
                else:
                    if temp:
                        final_segments.append(temp)
                    temp = char
            if temp:
                final_segments.append(temp)
        else:
            final_segments.append(seg)
    
    return final_segments


def merge_audio_segments(audio_segments: list, output_path: str) -> bytes:
    """
    合并多个音频段
    
    Args:
        audio_segments: 音频数据列表
        output_path: 输出文件路径
        
    Returns:
        合并后的音频数据
    """
    if len(audio_segments) == 1:
        return audio_segments[0]
    
    # 使用 ffmpeg 合并音频
    import tempfile
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_files = []
        
        # 保存所有音频段到临时文件
        for i, segment in enumerate(audio_segments):
            temp_file = os.path.join(temp_dir, f"segment_{i}.mp3")
            with open(temp_file, 'wb') as f:
                f.write(segment)
            temp_files.append(temp_file)
        
        # 创建合并列表文件
        list_file = os.path.join(temp_dir, "concat_list.txt")
        with open(list_file, 'w', encoding='utf-8') as f:
            for temp_file in temp_files:
                f.write(f"file '{temp_file}'\n")
        
        # 使用 ffmpeg 合并
        output_path = str(output_path)
        result = subprocess.run([
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', list_file,
            '-c', 'copy',
            '-y',
            output_path
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"合并音频失败: {result.stderr}")
            # 如果合并失败，返回第一个段
            return audio_segments[0]
        
        # 读取合并后的文件
        with open(output_path, 'rb') as f:
            return f.read()


def generate_cover_prompt(story_title: str, story_content: str, main_character: str, frontmatter: dict = None) -> str:
    """
    生成封面图片的提示词

    Args:
        story_title: 故事标题
        story_content: 故事正文
        main_character: 主要角色
        frontmatter: frontmatter 数据（可选）

    Returns:
        图片提示词
    """
    # 如果 frontmatter 中有自定义 prompt，直接使用
    if frontmatter and frontmatter.get('cover_prompt'):
        custom_prompt = frontmatter['cover_prompt']
        # 获取角色基础提示词并添加
        char_config = CHARACTERS.get(main_character, CHARACTERS["巫巫女"])
        return f"{char_config['base_prompt']}，{custom_prompt}，{DEFAULT_STYLE_KEYWORDS}"

    # 否则使用默认逻辑生成 prompt
    # 获取角色基础提示词
    char_config = CHARACTERS.get(main_character, CHARACTERS["巫巫女"])
    base_prompt = char_config["base_prompt"]
def add_metadata_to_audio(audio_path: str, story_title: str, story_content: str, cover_path: str):
    """
    为 MP3 文件添加元数据和封面

    Args:
        audio_path: 音频文件路径
        story_title: 故事标题
        story_content: 故事正文
        cover_path: 封面图片路径
    """
    print("正在添加元数据和封面...")

    try:
        audio_file = MP3(audio_path, ID3=ID3)
    except:
        audio_file = MP3(audio_path)
        audio_file.add_tags()

    # 添加标题
    audio_file['TIT2'] = TIT2(encoding=3, text=story_title)
    print(f"  ✓ 添加标题: {story_title}")

    # 添加艺术家
    audio_file['TPE1'] = TPE1(encoding=3, text=METADATA_ARTIST)
    print(f"  ✓ 添加艺术家: {METADATA_ARTIST}")

    # 添加专辑
    audio_file['TALB'] = TALB(encoding=3, text=METADATA_ALBUM)
    print(f"  ✓ 添加专辑: {METADATA_ALBUM}")

    # 添加类型
    audio_file['TCON'] = TCON(encoding=3, text=METADATA_GENRE)
    print(f"  ✓ 添加类型: {METADATA_GENRE}")

    # 添加封面
    if os.path.exists(cover_path):
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

            # 删除旧的封面
            if 'APIC:' in audio_file:
                del audio_file['APIC:']

            audio_file['APIC'] = APIC(
                encoding=3,
                mime=mime_type,
                type=3,
                desc='Cover',
                data=cover_data
            )
            print(f"  ✓ 添加封面: {cover_path} ({len(cover_data)/1024:.2f} KB)")
        except Exception as e:
            print(f"  ✗ 添加封面失败: {e}")
    else:
        print(f"  ⚠ 封面文件不存在: {cover_path}")

    # 添加简介
    intro = story_content[:500] + "..." if len(story_content) > 500 else story_content

    if 'COMM::chi' in audio_file:
        del audio_file['COMM::chi']

    audio_file['COMM'] = COMM(
        encoding=3,
        lang='chi',
        desc='简介',
        text=intro
    )
    print(f"  ✓ 添加简介 ({len(intro)} 字符)")

    # 添加全文
    if 'USLT::chi' in audio_file:
        del audio_file['USLT::chi']

    audio_file['USLT'] = USLT(
        encoding=3,
        lang='chi',
        desc='全文',
        text=story_content
    )
    print(f"  ✓ 添加全文 ({len(story_content)} 字符)")

    try:
        audio_file.save()
        print("✓ 元数据添加完成\n")
    except Exception as e:
        print(f"✗ 保存元数据失败: {e}")


def generate_cover_only(story_path: str):
    """
    只生成封面（音频文件必须已存在）

    Args:
        story_path: 故事文件路径
    """
    story_path = Path(story_path).resolve()

    if not story_path.exists():
        print(f"错误: 故事文件不存在: {story_path}")
        return False

    print("=" * 60)
    print(f"只生成封面: {story_path.name}")
    print("=" * 60)

    # 读取故事内容
    story_title, story_content, frontmatter = read_story_content(str(story_path))
    print(f"✓ 读取故事: {story_title}")
    print()

    # 生成输出文件名
    base_name = story_path.stem
    audio_output = AUDIO_DIR / f"{base_name}.mp3"
    cover_output = AUDIO_DIR / f"{base_name}.jpeg"

    # 检查音频文件是否存在
    if not audio_output.exists():
        print(f"✗ 错误: 音频文件不存在: {audio_output}")
        print("提示: 请先运行不带 --cover-only 参数的命令生成音频")
        return False

    print(f"✓ 音频文件已存在: {audio_output}")
    print()

    # 检查封面文件是否已存在
    cover_already_exists = cover_output.exists()
    if cover_already_exists:
        print(f"✓ 封面文件已存在: {cover_output}")
        print(f"  将使用现有封面，跳过 API 请求")
        print()

    # 提取主要角色
    main_character = extract_main_character(story_content)
    print(f"✓ 主要角色: {main_character}")
    print()

    # ========== 生成封面 ==========
    if not cover_already_exists:
        print("生成封面")
        print("-" * 60)

        # 获取角色参考图
        character_config = CHARACTERS.get(main_character, {})
        reference_image = character_config.get("reference_image", "")
        
        if not reference_image or not os.path.exists(reference_image):
            print(f"✗ 角色参考图不存在: {reference_image}")
            print("提示: 请确保角色参考图存在于 audio/references/ 目录")
            return False

        # 检查火山引擎 API 密钥（用于封面生成）
        use_key_secret = bool(VOLCENGINE_ACCESS_KEY and VOLCENGINE_SECRET_KEY)

        if not use_key_secret:
            print("✗ 未设置火山引擎 API 密钥（封面生成需要）")
            print()
            print("请在 .env 文件中设置 VOLCENGINE_ACCESS_KEY 和 VOLCENGINE_SECRET_KEY")
            return False

        print(f"✓ 使用火山引擎 Access Key + Secret Key")
        print()

        # 获取参考图列表（支持多角色）
        reference_images = []

        # 从 frontmatter 中读取角色列表
        if frontmatter and frontmatter.get("cover_characters"):
            cover_characters = frontmatter["cover_characters"]
            if isinstance(cover_characters, str):
                cover_characters = [cover_characters]

            for char_name in cover_characters:
                char_config = CHARACTERS.get(char_name)
                if char_config and char_config.get("reference_image"):
                    ref_path = char_config["reference_image"]
                    if os.path.exists(ref_path):
                        reference_images.append(ref_path)
                        print(f"✓ 添加角色参考图: {char_name} -> {ref_path}")
                    else:
                        print(f"⚠ 角色参考图不存在: {char_name} -> {ref_path}")
        else:
            # 使用单个主要角色
            if reference_image and os.path.exists(reference_image):
                reference_images.append(reference_image)

        if not reference_images:
            print("✗ 没有可用的参考图")
            return False

        # 使用图生图
        jimeng = VolcEngineJimeng(
            access_key=VOLCENGINE_ACCESS_KEY,
            secret_key=VOLCENGINE_SECRET_KEY
        )
        prompt = generate_cover_prompt(story_title, story_content, main_character, frontmatter)

        print(f"提示词: {prompt}")
        print(f"参考图: {reference_image}")
        print(f"参考权重: {JIMENG_REFERENCE_WEIGHT}")
        print()

        result = jimeng.generate_image(
            prompt=prompt,
            reference_image=reference_image,
            reference_strength=JIMENG_REFERENCE_WEIGHT,
            aspect_ratio=JIMENG_ASPECT_RATIO,
            quality=JIMENG_IMAGE_QUALITY
        )

        if result.get("status") != "success":
            print(f"✗ 封面生成失败: {result.get('message')}")
            return False

        image_url = result.get("image_url")
        image_base64 = result.get("image_base64")
        
        if not image_url and not image_base64:
            print("✗ 封面生成失败: 未返回图片 URL 或 base64 数据")
            return False

        # 下载封面
        success = jimeng.download_image(image_url, str(cover_output), image_base64)

        if not success:
            print("✗ 封面下载失败")
            return False

        print(f"✓ 封面已保存: {cover_output}")
        print()

    # 添加封面到音频文件
    print("添加封面到音频文件")
    print("-" * 60)
    
    try:
        audio_file = ID3(audio_output)
        
        with open(cover_output, 'rb') as f:
            cover_data = f.read()

        ext = Path(cover_output).suffix.lower()
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp'
        }
        mime_type = mime_types.get(ext, 'image/jpeg')

        # 删除所有现有的 APIC 标签（封面）
        keys_to_delete = [key for key in audio_file.keys() if key.startswith('APIC')]
        for key in keys_to_delete:
            del audio_file[key]
            print(f"  删除旧封面标签: {key}")

        audio_file['APIC'] = APIC(
            encoding=3,
            mime=mime_type,
            type=3,
            desc='Cover',
            data=cover_data
        )
        
        audio_file.save()
        print(f"✓ 封面已添加到音频文件")
        print()
    except Exception as e:
        print(f"✗ 添加封面到音频文件失败: {e}")
        return False

    return True


def generate_story(story_path: str, generate_cover: bool = True):
    """
    生成故事的音频和封面

    Args:
        story_path: 故事文件路径
        generate_cover: 是否生成封面
    """
    story_path = Path(story_path).resolve()

    if not story_path.exists():
        print(f"错误: 故事文件不存在: {story_path}")
        return False

    print("=" * 60)
    print(f"开始生成故事: {story_path.name}")
    print("=" * 60)

    # 读取故事内容
    story_title, story_content, frontmatter = read_story_content(str(story_path))
    print(f"✓ 读取故事: {story_title}")
    print(f"✓ 故事长度: {len(story_content)} 字符")
    print()

    # 提取主要角色
    main_character = extract_main_character(story_content)
    print(f"✓ 主要角色: {main_character}")
    print()

    # 生成输出文件名
    base_name = story_path.stem
    audio_output = AUDIO_DIR / f"{base_name}.mp3"
    cover_output = AUDIO_DIR / f"{base_name}.jpeg"

    # 检查音频文件是否已存在
    audio_already_exists = audio_output.exists()
    cover_already_exists = cover_output.exists()

    if audio_already_exists and cover_already_exists and generate_cover:
        print(f"✓ 音频和封面都已存在，跳过生成")
        print(f"  音频: {audio_output}")
        print(f"  封面: {cover_output}")
        return True

    if audio_already_exists and not generate_cover:
        print(f"✓ 音频已存在，跳过音频生成")
        print(f"  音频: {audio_output}")
        print()
        
        # 检查火山引擎 API 密钥（用于封面生成）
        use_key_secret = bool(VOLCENGINE_ACCESS_KEY and VOLCENGINE_SECRET_KEY)
        
        if not use_key_secret:
            print("✗ 未设置火山引擎 API 密钥（封面生成需要）")
            print()
            print("请选择以下方式之一：")
            print("  方式 A：在 .env 文件中设置 VOLCENGINE_ACCESS_KEY 和 VOLCENGINE_SECRET_KEY")
        print("  方式 B：在 .env 文件中设置 VOLCENGINE_APP_ID 和 VOLCENGINE_ACCESS_TOKEN")
                    return False
        
                print(f"✓ 使用火山引擎 Access Key + Secret Key")
        
            # ========== 生成音频 ==========    if not audio_already_exists:
        print("步骤 1/3: 生成音频")
        print("-" * 60)
    else:
        print("步骤 1/3: 跳过音频生成（已存在）")
        print("-" * 60)

    # 使用 MiniMax TTS
    if USE_MINIMAX_TTS:
        print("✓ 使用 MiniMax TTS (speech-2.8-hd)")
        
        # 导入 MiniMax TTS
        from minimax_api import MiniMaxTTS
        
        # 获取角色配置
        character_config = CHARACTERS.get(main_character, {})
        voice_id = character_config.get("minimax_voice_id", "")
        emotion = character_config.get("minimax_emotion", "gentle")
        
        if not voice_id:
            print("⚠ 警告: 角色未配置 minimax_voice_id，将使用默认音色")
            # 使用 MiniMax 系统音色
            voice_id = "female-tianmeijiaojia"  # 可根据需要更改
        
        print(f"  音色ID: {voice_id}")
        print(f"  情感: {emotion}")
        print()
        
        tts = MiniMaxTTS(api_key=MINIMAX_API_KEY)
        
        # 直接生成（MiniMax 支持最长 10000 字符）
        print(f"文本长度: {len(story_content)} 字符")
        audio_data = tts.synthesize_speech(
            text=story_content,
            voice_id=voice_id,
            model=MINIMAX_MODEL,
            speed=MINIMAX_SPEED,
            vol=MINIMAX_VOL,
            pitch=MINIMAX_PITCH,
            emotion=emotion
        )
    else:
        print("错误: 未配置 MiniMax API Key")
        return None

    if not audio_data:
        print("✗ 音频生成失败")
        return False

    # 保存音频
    with open(audio_output, "wb") as f:
        f.write(audio_data)

    print(f"✓ 音频已保存: {audio_output}")
    print()

    # ========== 生成封面 ==========
    if not generate_cover:
        print("步骤 2/3: 跳过封面生成 (--no-cover)")
        print("-" * 60)
        cover_output = None
    else:
        print("步骤 2/3: 生成封面")
        print("-" * 60)

    # 获取角色参考图（支持多角色）
    reference_images = []

    # 从 frontmatter 中读取角色列表
    if frontmatter and frontmatter.get('cover_characters'):
        cover_characters = frontmatter['cover_characters']
        if isinstance(cover_characters, str):
            cover_characters = [cover_characters]

        for char_name in cover_characters:
            char_config = CHARACTERS.get(char_name)
            if char_config and char_config.get('reference_image'):
                ref_path = char_config['reference_image']
                if os.path.exists(ref_path):
                    reference_images.append(ref_path)
                    print(f"✓ 添加角色参考图: {char_name} -> {ref_path}")
                else:
                    print(f"⚠ 角色参考图不存在: {char_name} -> {ref_path}")
    else:
        # 使用单个主要角色
        character_config = CHARACTERS.get(main_character, {})
        reference_image = character_config.get("reference_image", "")
        if reference_image and os.path.exists(reference_image):
            reference_images.append(reference_image)

    if not reference_images:
        print("✗ 没有可用的参考图")
        return False

    # 生成封面提示词
    prompt = generate_cover_prompt(story_title, story_content, main_character, frontmatter)

    print(f"提示词: {prompt}")
    print(f"参考图: {reference_images}")
    print(f"参考权重: {JIMENG_REFERENCE_WEIGHT}")
    print()

    # 调用即梦 AI 生成封面
    jimeng = VolcEngineJimeng(
        access_key=VOLCENGINE_ACCESS_KEY,
        secret_key=VOLCENGINE_SECRET_KEY
    )

    image_url = jimeng.generate_image_with_reference(
        prompt=prompt,
        reference_image_paths=reference_images,
        reference_weight=JIMENG_REFERENCE_WEIGHT,
        quality=JIMENG_IMAGE_QUALITY
    )

    if not image_url:
        print("✗ 封面生成失败")
        return False

    # 下载封面
    success = jimeng.download_image(image_url, str(cover_output))

    if not success:
        print("✗ 封面下载失败")
        return False

    print(f"✓ 封面已保存: {cover_output}")
    print()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
巫巫女故事自动化生成工具 - 主函数
使用豆包 TTS API 和即梦 AI API 自动生成音频和封面
"""

import sys
from pathlib import Path

# 添加 scripts 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    AUDIO_DIR,
    STORIES_DIR
)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="巫巫女故事自动化生成工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 生成单个故事
  python scripts/auto_generate_story.py 23-新故事.md

  # 只生成封面（音频必须已存在）
  python scripts/auto_generate_story.py 23-新故事.md --cover-only

  # 批量生成所有故事
  python scripts/auto_generate_story.py --all

  # 批量生成未处理的故事
  python scripts/auto_generate_story.py --batch

  # 指定输出目录
  python scripts/auto_generate_story.py 23-新故事.md --output-dir /path/to/output
        """
    )

    parser.add_argument(
        "story",
        nargs="?",
        help="故事文件路径"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="生成所有故事（包括已存在的）"
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="批量生成所有未处理的故事"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(AUDIO_DIR),
        help="输出目录（默认: audio/）"
    )
    parser.add_argument(
        "--no-cover",
        action="store_true",
        help="跳过封面生成，只生成音频"
    )
    parser.add_argument(
        "--cover-only",
        action="store_true",
        help="只生成封面，跳过音频生成（音频文件必须已存在）"
    )

    args = parser.parse_args()

    if args.all:
        # 批量模式：生成所有故事
        print("批量生成模式 - 处理所有故事")
        print()

        # 查找所有故事文件
        story_files = sorted(STORIES_DIR.glob("*.md"))

        if not story_files:
            print("✓ 未找到故事文件")
            return

        print(f"找到 {len(story_files)} 个故事文件:")
        for story_file in story_files:
            print(f"  - {story_file.name}")
        print()

        # 逐个生成
        for i, story_file in enumerate(story_files, 1):
            print(f"\n[{i}/{len(story_files)}] 处理: {story_file.name}")
            print("-" * 60)

            if args.cover_only:
                # 只生成封面
                generate_cover_only(story_file)
            else:
                # 生成完整故事
                success = generate_story(story_file, generate_cover=not args.no_cover)

                if not success:
                    print(f"✗ 生成失败: {story_file.name}")
                    continue

    elif args.batch:
        # 批量模式：只生成未处理的故事
        print("批量生成模式 - 处理未处理的故事")
        print()

        # 查找所有故事文件
        story_files = sorted(STORIES_DIR.glob("*.md"))

        # 过滤掉已生成的
        unprocessed = []
        for story_file in story_files:
            audio_file = AUDIO_DIR / f"{story_file.stem}.mp3"
            if not audio_file.exists():
                unprocessed.append(story_file)

        if not unprocessed:
            print("✓ 所有故事都已生成")
            return

        print(f"找到 {len(unprocessed)} 个未处理的故事:")
        for story_file in unprocessed:
            print(f"  - {story_file.name}")
        print()

        # 逐个生成
        for i, story_file in enumerate(unprocessed, 1):
            print(f"\n[{i}/{len(unprocessed)}] 处理: {story_file.name}")
            print("-" * 60)

            success = generate_story(story_file, generate_cover=not args.no_cover)

            if not success:
                print(f"✗ 生成失败: {story_file.name}")
                continue

    elif args.story:
        # 单个故事模式
        if args.cover_only:
            # 只生成封面
            if args.no_cover:
                print("✗ 错误：--cover-only 和 --no-cover 不能同时使用")
                return
            generate_cover_only(args.story)
        else:
            generate_story(args.story, generate_cover=not args.no_cover)
    else:
        # 显示帮助
        parser.print_help()
        print()
        print("提示:")
        print("  1. 先在豆包 App 中生成角色参考图，保存到 audio/references/")
        print("  2. 设置 API 密钥:")
        print("     export VOLCENGINE_ACCESS_KEY=\"你的AccessKey\"")
        print("     export VOLCENGINE_SECRET_KEY=\"你的SecretKey\"")
        print("  3. 或者在 .env 文件中配置:")
        print("     VOLCENGINE_ACCESS_KEY=你的AccessKey")
        print("     VOLCENGINE_SECRET_KEY=你的SecretKey")


if __name__ == "__main__":
    main()
