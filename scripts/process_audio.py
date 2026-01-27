#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频处理工具
从录屏文件中提取音频，去除空白，嵌入封面和元数据
修复：解决Markdown标题标记去除问题
"""

import os
import sys
import subprocess
import json
import re
from pathlib import Path
from typing import Optional, Tuple

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TCON, APIC, COMM, USLT
    from mutagen import File
except ImportError:
    print("错误: 需要安装 mutagen 库")
    print("请运行: pip install mutagen")
    sys.exit(1)


def check_ffmpeg():
    """检查 ffmpeg 是否安装"""
    try:
        subprocess.run(['ffmpeg', '-version'], 
                      capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("错误: 需要安装 ffmpeg")
        print("macOS 安装: brew install ffmpeg")
        return False


def extract_audio(video_path: str, output_path: str) -> bool:
    """从视频文件中提取音频"""
    print(f"正在从录屏文件提取音频: {video_path}")
    cmd = [
        'ffmpeg', '-i', video_path,
        '-vn',  # 不包含视频
        '-acodec', 'libmp3lame',  # 使用 MP3 编码
        '-ab', '192k',  # 音频比特率
        '-ar', '44100',  # 采样率
        '-y',  # 覆盖输出文件
        output_path
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✓ 音频提取完成: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 音频提取失败: {e.stderr.decode()}")
        return False


def detect_silence(audio_path: str, 
                   min_start_padding: float = 0.5,
                   min_end_padding: float = 0.5) -> Tuple[float, float]:
    """检测音频前后的静音部分
    
    Args:
        audio_path: 音频文件路径
        min_start_padding: 开头最小保留时长（秒），默认0.5秒
        min_end_padding: 结尾最小保留时长（秒），默认0.5秒
    
    Returns:
        (start_trim, end_trim): 需要去除的开头和结尾时长
    """
    print("正在检测静音部分...")
    cmd = [
        'ffmpeg', '-i', audio_path,
        '-af', 'silencedetect=noise=-30dB:duration=0.5',
        '-f', 'null', '-'
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stderr
        
        # 解析静音检测结果
        silence_starts = []
        silence_ends = []
        
        for line in output.split('\n'):
            if 'silence_start' in line:
                match = re.search(r'silence_start: ([\d.]+)', line)
                if match:
                    silence_starts.append(float(match.group(1)))
            elif 'silence_end' in line:
                match = re.search(r'silence_end: ([\d.]+)', line)
                if match:
                    silence_ends.append(float(match.group(1)))
        
        # 获取音频总时长
        duration_match = re.search(r'Duration: (\d{2}):(\d{2}):(\d{2})\.(\d{2})', output)
        if duration_match:
            hours, minutes, seconds, centiseconds = map(int, duration_match.groups())
            total_duration = hours * 3600 + minutes * 60 + seconds + centiseconds / 100
        else:
            total_duration = 0.0
        
        # 计算需要去除的前后空白
        start_trim = 0.0
        end_trim = 0.0
        
        if total_duration == 0:
            return 0.0, 0.0
        
        # 改进的开头静音处理逻辑
        # 检查开头是否有静音，但只在开头静音持续时间较长时才考虑裁剪
        if silence_starts and silence_starts[0] < 1.0:  # 开头有静音
            if silence_ends and len(silence_ends) > 0:
                # 检查第一个静音段是否足够长（比如大于0.5秒）才考虑裁剪
                first_silence_end = silence_ends[0]
                if first_silence_end > 0.5:  # 只有当开头静音超过0.5秒才裁剪
                    # 保留0.1秒的缓冲，但不能超过开头最小保留时间
                    start_trim = min(max(first_silence_end - 0.1, min_start_padding), first_silence_end)
                else:
                    # 开头静音很短，不裁剪
                    start_trim = min_start_padding
            else:
                # 没有对应的静音结束时间，不裁剪
                start_trim = min_start_padding
        else:
            # 开头没有静音，保留最小开头空白
            start_trim = min_start_padding
        
        # 处理结尾空白
        if silence_starts:
            # 寻找最后可能的结尾静音
            for i in range(len(silence_starts)-1, -1, -1):
                silence_start_time = silence_starts[i]
                # 检查这个静音段是否接近音频结尾
                if total_duration - silence_start_time <= 2.0:  # 静音开始时间距离结尾小于2秒
                    if i < len(silence_ends):
                        # 计算这个静音段的持续时间
                        silence_duration = silence_ends[i] - silence_start_time
                        if silence_duration > 0.5:  # 静音持续时间超过0.5秒才裁剪
                            # 裁剪从静音开始时间到结尾的部分
                            end_trim = min(max(total_duration - silence_start_time - 0.1, min_end_padding), 
                                          total_duration - silence_start_time)
                        break
        
        # 确保不会裁剪过度（剩余的有效音频时长不能为负）
        remaining_duration = total_duration - start_trim - end_trim
        if remaining_duration < 0:
            # 如果音频太短，重新分配保留时长
            if total_duration >= min_start_padding + min_end_padding:
                # 音频足够长，分别保留最小空白
                start_trim = min_start_padding
                end_trim = min_end_padding
            else:
                # 音频太短，不进行裁剪，保留原样
                start_trim = 0.0
                end_trim = 0.0
        
        print(f"  检测到开头空白: {start_trim:.2f}秒 (将保留至少 {min_start_padding:.2f}秒)")
        print(f"  检测到结尾空白: {end_trim:.2f}秒 (将保留至少 {min_end_padding:.2f}秒)")
        
        return start_trim, end_trim
        
    except subprocess.CalledProcessError as e:
        print(f"✗ 静音检测失败: {e}")
        return 0.0, 0.0


def trim_audio(input_path: str, output_path: str, 
               start_trim: float, end_trim: float) -> bool:
    """去除音频前后的空白"""
    if start_trim == 0.0 and end_trim == 0.0:
        print("没有检测到需要去除的空白")
        # 直接复制文件
        import shutil
        shutil.copy2(input_path, output_path)
        return True
    
    print(f"正在去除空白 (开头: {start_trim:.2f}秒, 结尾: {end_trim:.2f}秒)...")
    
    # 获取音频时长
    cmd_duration = [
        'ffprobe', '-v', 'error', '-show_entries',
        'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
        input_path
    ]
    try:
        result = subprocess.run(cmd_duration, capture_output=True, text=True, check=True)
        total_duration = float(result.stdout.strip())
        end_time = total_duration - end_trim
        
        # 使用正确的编码参数，确保后续可以应用滤镜
        cmd = [
            'ffmpeg', '-i', input_path,
            '-ss', str(start_trim),
            '-t', str(end_time - start_trim),
            '-acodec', 'libmp3lame',  # 使用MP3编码而不是copy
            '-ab', '192k',  # 保持比特率
            '-ar', '44100',  # 保持采样率
            '-y',
            output_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✓ 空白去除完成: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 空白去除失败: {e.stderr.decode()}")
        return False


def apply_fade_in_effect(input_path: str, output_path: str, fade_duration: float = 0.2) -> bool:
    """应用淡入效果到音频开头，减少突兀感
    
    Args:
        input_path: 输入音频文件路径
        output_path: 输出音频文件路径
        fade_duration: 淡入时长（秒），默认0.2秒
    """
    print(f"正在应用淡入效果 (时长: {fade_duration:.2f}秒)...")
    
    cmd = [
        'ffmpeg', '-i', input_path,
        '-af', f'afade=t=in:ss=0:d={fade_duration}',  # 应用淡入效果
        '-c:a', 'libmp3lame',  # 使用MP3编码
        '-ab', '192k',  # 保持比特率
        '-ar', '44100',  # 保持采样率
        '-y',
        output_path
    ]
    
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"✓ 淡入效果应用完成: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ 淡入效果应用失败: {e.stderr.decode()}")
        return False


def get_original_base_name(original_path: str) -> str:
    """获取原始文件的基本名称（去掉临时后缀）"""
    original_name = Path(original_path).stem
    # 去掉常见的临时后缀
    suffixes_to_remove = ['_temp', '_trimmed', '_with_fade', '_processed']
    for suffix in suffixes_to_remove:
        if original_name.endswith(suffix):
            original_name = original_name[:-len(suffix)]
    return original_name


def find_cover_image(original_path: str) -> Optional[str]:
    """查找封面图片（同名或指定）
    查找顺序：audio目录 > 当前目录 > 项目根目录
    """
    # 获取原始文件名（不含临时后缀）
    original_base_name = get_original_base_name(original_path)
    audio_dir = Path(original_path).parent
    
    # 清理名称：去除括号内容和常见后缀
    clean_name = re.sub(r'[（(].*?[）)]', '', original_base_name).strip()
    # 去除 _processed, _temp, _trimmed 等后缀
    clean_name = re.sub(r'_(processed|temp|trimmed|录屏).*$', '', clean_name).strip()
    
    # 可能的图片扩展名
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    
    # 查找目录列表：优先 audio 目录，然后当前目录，最后项目根目录
    search_dirs = [
        audio_dir.parent / 'audio',  # audio目录（优先）
        audio_dir,  # 当前目录
        audio_dir.parent,  # 项目根目录
    ]
    
    # 只保留存在的目录
    search_dirs = [d for d in search_dirs if d.exists()]
    
    # 查找同名图片
    for search_dir in search_dirs:
        for ext in image_extensions:
            # 尝试清理后的名称
            image_path = search_dir / f"{clean_name}{ext}"
            if image_path.exists():
                print(f"  找到封面: {image_path}")
                return str(image_path)
            
            # 尝试完整匹配（去除后缀前）
            temp_name = re.sub(r'_(processed|temp|trimmed).*$', '', original_base_name).strip()
            image_path = search_dir / f"{temp_name}{ext}"
            if image_path.exists():
                print(f"  找到封面: {image_path}")
                return str(image_path)
    
    print(f"  未找到封面图片 (查找名称: {clean_name})")
    return None


def find_story_file(original_path: str) -> Optional[str]:
    """查找对应的故事文件
    查找顺序：项目根目录 > 当前目录
    """
    # 获取原始文件名（不含临时后缀）
    original_base_name = get_original_base_name(original_path)
    audio_dir = Path(original_path).parent
    
    # 清理名称：去除括号内容和常见后缀
    clean_name = re.sub(r'[（(].*?[）)]', '', original_base_name).strip()
    # 去除 _processed, _temp, _trimmed 等后缀
    clean_name = re.sub(r'_(processed|temp|trimmed|录屏).*$', '', clean_name).strip()
    
    # 查找目录列表：优先项目根目录，然后当前目录
    search_dirs = [
        audio_dir.parent,  # 项目根目录（优先）
        audio_dir,  # 当前目录
    ]
    
    # 只保留存在的目录
    search_dirs = [d for d in search_dirs if d.exists()]
    
    # 查找 .md 文件
    for search_dir in search_dirs:
        story_path = search_dir / f"{clean_name}.md"
        if story_path.exists():
            print(f"  找到故事文件: {story_path}")
            return str(story_path)
    
    print(f"  未找到故事文件 (查找名称: {clean_name}.md)")
    return None


def clean_markdown_title(title: str) -> str:
    """清理Markdown标题，去除标记符号"""
    # 去除开头的 # 符号和空格
    cleaned = re.sub(r'^#+\s*', '', title)
    # 去除其他可能的Markdown格式
    cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)  # 去除粗体标记
    cleaned = re.sub(r'\*(.*?)\*', r'\1', cleaned)      # 去除斜体标记
    cleaned = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', cleaned)  # 去除链接标记
    cleaned = re.sub(r'`(.*?)`', r'\1', cleaned)        # 去除代码标记
    cleaned = cleaned.strip()
    return cleaned


def read_story_content(story_path: str) -> Tuple[str, str]:
    """读取故事内容，返回标题和正文"""
    try:
        with open(story_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        raw_title = lines[0].strip() if lines else "未知故事"
        # 清理标题
        clean_title = clean_markdown_title(raw_title)
        
        # 提取简介（前几段）
        intro_lines = []
        for line in lines[1:]:
            line = line.strip()
            if line and not line.startswith('#'):
                intro_lines.append(line)
                if len(intro_lines) >= 3:  # 取前3段作为简介
                    break
        
        intro = '\n'.join(intro_lines) if intro_lines else content[:500]
        
        return clean_title, content
    except Exception as e:
        print(f"读取故事文件失败: {e}")
        return "未知故事", ""


def add_metadata(audio_path: str, cover_path: Optional[str] = None,
                 story_title: Optional[str] = None,
                 story_content: Optional[str] = None):
    """为 MP3 文件添加元数据和封面"""
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
    else:
        print("  ⚠ 未提供标题")
    
    # 添加艺术家
    audio_file['TPE1'] = TPE1(encoding=3, text='巫巫女睡前故事')
    print("  ✓ 添加艺术家: 巫巫女睡前故事")
    
    # 添加专辑
    audio_file['TALB'] = TALB(encoding=3, text='巫巫女睡前故事集')
    print("  ✓ 添加专辑: 巫巫女睡前故事集")
    
    # 添加类型
    audio_file['TCON'] = TCON(encoding=3, text='儿童故事')
    print("  ✓ 添加类型: 儿童故事")
    
    # 添加封面
    if cover_path:
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
                
                # 删除旧的封面（如果存在）
                if 'APIC:' in audio_file:
                    del audio_file['APIC:']
                
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
                import traceback
                traceback.print_exc()
        else:
            print(f"  ✗ 封面文件不存在: {cover_path}")
    else:
        print("  ⚠ 未提供封面路径")
    
    # 添加简介（作为注释）
    if story_content:
        # 简介（前500字符）
        intro = story_content[:500] + "..." if len(story_content) > 500 else story_content
        
        # 删除旧的注释（如果存在）
        if 'COMM::chi' in audio_file:
            del audio_file['COMM::chi']
        
        audio_file['COMM'] = COMM(
            encoding=3,
            lang='chi',
            desc='简介',
            text=intro
        )
        print(f"  ✓ 添加简介 ({len(intro)} 字符)")
        
        # 全文（作为歌词/文本）
        # 删除旧的歌词（如果存在）
        if 'USLT::chi' in audio_file:
            del audio_file['USLT::chi']
        
        audio_file['USLT'] = USLT(
            encoding=3,
            lang='chi',
            desc='全文',
            text=story_content
        )
        print(f"  ✓ 添加全文 ({len(story_content)} 字符)")
    else:
        print("  ⚠ 未提供故事内容")
    
    try:
        audio_file.save()
        print("✓ 元数据添加完成\n")
    except Exception as e:
        print(f"✗ 保存元数据失败: {e}")
        import traceback
        traceback.print_exc()


def process_video(video_path: str, output_path: Optional[str] = None,
                  cover_path: Optional[str] = None,
                  story_path: Optional[str] = None,
                  min_start_padding: float = 0.5,
                  min_end_padding: float = 0.5,
                  fade_in_duration: float = 0.2):
    """处理录屏文件的完整流程
    
    Args:
        video_path: 录屏文件路径
        output_path: 输出音频文件路径（可选）
        cover_path: 封面图片路径（可选）
        story_path: 故事文件路径（可选）
        min_start_padding: 开头最小保留时长（秒），默认0.5秒
        min_end_padding: 结尾最小保留时长（秒），默认0.5秒
        fade_in_duration: 淡入时长（秒），默认0.2秒
    """
    if not check_ffmpeg():
        return False
    
    video_path = Path(video_path).resolve()
    if not video_path.exists():
        print(f"错误: 文件不存在: {video_path}")
        return False
    
    # 确定输出路径
    if output_path is None:
        output_path = video_path.parent / f"{video_path.stem}_processed.mp3"
    else:
        output_path = Path(output_path).resolve()
    
    # 临时文件
    temp_audio = video_path.parent / f"{video_path.stem}_temp.mp3"
    temp_trimmed = video_path.parent / f"{video_path.stem}_trimmed.mp3"
    temp_with_fade = video_path.parent / f"{video_path.stem}_with_fade.mp3"
    
    try:
        # 1. 提取音频
        if not extract_audio(str(video_path), str(temp_audio)):
            return False
        
        # 2. 检测静音
        start_trim, end_trim = detect_silence(str(temp_audio), 
                                             min_start_padding=min_start_padding,
                                             min_end_padding=min_end_padding)
        
        # 3. 去除空白
        if not trim_audio(str(temp_audio), str(temp_trimmed), start_trim, end_trim):
            return False
        
        # 4. 应用淡入效果
        if not apply_fade_in_effect(str(temp_trimmed), str(temp_with_fade), fade_in_duration):
            print("警告: 淡入效果应用失败，跳过此步骤")
            # 如果淡入失败，直接使用修剪后的音频
            temp_with_fade = temp_trimmed
        else:
            # 如果成功应用了淡入效果，删除修剪后的临时文件
            if temp_trimmed.exists() and temp_trimmed != temp_with_fade:
                temp_trimmed.unlink()
        
        # 5. 查找封面和故事文件 - 使用原始文件路径
        print("\n查找封面图片...")
        if cover_path is None:
            cover_path = find_cover_image(str(video_path))  # 使用原始视频文件路径
        else:
            print(f"  使用指定的封面: {cover_path}")
        
        # 6. 查找故事文件 - 使用原始文件路径
        print("\n查找故事文件...")
        if story_path is None:
            story_path = find_story_file(str(video_path))  # 使用原始视频文件路径
        else:
            print(f"  使用指定的故事文件: {story_path}")
        
        story_title = None
        story_content = None
        if story_path and os.path.exists(story_path):
            print(f"  读取故事内容...")
            story_title, story_content = read_story_content(story_path)
            print(f"  ✓ 标题: {story_title}")  # 这里会显示清理后的标题
            print(f"  ✓ 内容长度: {len(story_content)} 字符")
        else:
            print("  ⚠ 未找到故事文件")
        
        # 7. 添加元数据
        add_metadata(str(temp_with_fade), cover_path, story_title, story_content)
        
        # 8. 移动到最终输出位置
        import shutil
        shutil.move(str(temp_with_fade), str(output_path))
        print(f"\n✓ 处理完成: {output_path}")
        
        # 清理临时文件
        if temp_audio.exists():
            temp_audio.unlink()
        
        return True
        
    except Exception as e:
        print(f"✗ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理临时文件
        for temp_file in [temp_audio, temp_trimmed, temp_with_fade]:
            if temp_file.exists() and temp_file != output_path:
                try:
                    temp_file.unlink()
                except:
                    pass


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python scripts/process_audio.py <录屏文件> [输出文件] [封面图片] [故事文件]")
        print("\n示例:")
        print("  python scripts/process_audio.py screen_recording.mov")
        print("  python scripts/process_audio.py screen_recording.mov output.mp3 cover.jpg story.md")
        sys.exit(1)
    
    video_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    cover_path = sys.argv[3] if len(sys.argv) > 3 else None
    story_path = sys.argv[4] if len(sys.argv) > 4 else None
    
    success = process_video(video_path, output_path, cover_path, story_path)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
