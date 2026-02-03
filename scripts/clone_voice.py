#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MiniMax 音色克隆工具
支持快速复刻和音色设计
"""

import os
import sys
import requests
import base64
from pathlib import Path

# 添加 scripts 目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from config import MINIMAX_API_KEY


class MiniMaxVoiceCloning:
    """MiniMax 音色克隆 API 客户端"""

    def __init__(self, api_key: str = ""):
        """
        初始化音色克隆客户端

        Args:
            api_key: MiniMax API Key
        """
        self.api_key = api_key
        # 修复端点地址 - 使用 api.minimaxi.com 而不是 api.minimax.chat
        self.base_url = "https://api.minimaxi.com/v1"
        
        # 请求头
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    def upload_audio_file(self, audio_file_path: str) -> str:
        """
        上传音频文件

        Args:
            audio_file_path: 音频文件路径

        Returns:
            file_id
        """
        try:
            # 构建请求
            url = f"{self.base_url}/files/upload"
            
            # 使用 multipart/form-data 格式上传
            with open(audio_file_path, "rb") as f:
                files = {
                    "file": (Path(audio_file_path).name, f, "audio/mpeg")
                }
                data = {
                    "purpose": "voice_clone"  # 音色克隆专用
                }
                
                # 临时移除 Content-Type，让 requests 自动设置
                headers = {
                    "Authorization": f"Bearer {self.api_key}"
                }
                
                response = requests.post(url, headers=headers, files=files, data=data)
                result = response.json()
            
            if result.get("base_resp", {}).get("status_code") == 0:
                return result.get("file_id")
            else:
                print(f"上传失败: {result.get('base_resp', {}).get('status_msg', '未知错误')}")
                return None
                
        except Exception as e:
            print(f"上传音频文件失败: {e}")
            return None

    def clone_voice(
        self,
        target_audio_file: str,
        voice_id: str,
        sample_audio_file: str = None,
        clone_prompt: str = ""
    ) -> bool:
        """
        快速复刻音色

        Args:
            target_audio_file: 待克隆的目标音频文件路径（10-30秒）
            voice_id: 自定义的音色 ID
            sample_audio_file: 示例音频文件路径（可选，用于增强克隆效果）
            clone_prompt: 克隆提示词（可选）

        Returns:
            成功返回 True，失败返回 False
        """
        try:
            # 上传目标音频
            print(f"上传目标音频: {target_audio_file}")
            target_file_id = self.upload_audio_file(target_audio_file)
            if not target_file_id:
                return False
            print(f"✓ 目标音频上传成功，file_id: {target_file_id}")
            
            # 上传示例音频（如果提供）
            sample_file_id = None
            if sample_audio_file:
                print(f"上传示例音频: {sample_audio_file}")
                sample_file_id = self.upload_audio_file(sample_audio_file)
                if sample_file_id:
                    print(f"✓ 示例音频上传成功，file_id: {sample_file_id}")
            
            # 构建克隆请求
            url = f"{self.base_url}/voice/clone/create"
            payload = {
                "voice_id": voice_id,
                "target_file_id": target_file_id,
                "model": "speech-2.8-hd"
            }
            
            # 添加示例音频（如果提供）
            if sample_file_id:
                payload["sample_file_id"] = sample_file_id
                if clone_prompt:
                    payload["clone_prompt"] = {
                        "prompt_audio": sample_file_id,
                        "prompt_text": clone_prompt
                    }
            
            # 调用克隆接口
            print(f"开始克隆音色，voice_id: {voice_id}")
            response = requests.post(url, headers=self.headers, json=payload)
            result = response.json()
            
            if result.get("base_resp", {}).get("status_code") == 0:
                print(f"✓ 音色克隆成功！")
                print(f"  voice_id: {voice_id}")
                print(f"  model: speech-2.8-hd")
                print(f"  有效期: 7天内至少使用一次，否则将被删除")
                return True
            else:
                print(f"✗ 克隆失败: {result.get('base_resp', {}).get('status_msg', '未知错误')}")
                return False
                
        except Exception as e:
            print(f"克隆音色失败: {e}")
            return False

    def design_voice(
        self,
        prompt: str,
        voice_id: str,
        model: str = "speech-02-hd"
    ) -> dict:
        """
        音色设计（基于文字描述生成音色）

        Args:
            prompt: 音色描述（如："温柔的女巫声音，语调轻柔，适合讲故事"）
            voice_id: 自定义的音色 ID
            model: 模型版本（推荐 speech-02-hd）

        Returns:
            返回包含 voice_id 和试听音频的结果
        """
        try:
            url = f"{self.base_url}/voice/design/create"
            payload = {
                "voice_id": voice_id,
                "prompt": prompt,
                "model": model
            }
            
            print(f"开始设计音色...")
            print(f"  描述: {prompt}")
            print(f"  voice_id: {voice_id}")
            print(f"  model: {model}")
            
            response = requests.post(url, headers=self.headers, json=payload)
            result = response.json()
            
            if result.get("base_resp", {}).get("status_code") == 0:
                print(f"✓ 音色设计成功！")
                return result
            else:
                print(f"✗ 设计失败: {result.get('base_resp', {}).get('status_msg', '未知错误')}")
                return None
                
        except Exception as e:
            print(f"音色设计失败: {e}")
            return None

    def get_available_voices(self) -> list:
        """
        查询可用音色列表

        Returns:
            音色列表
        """
        try:
            url = f"{self.base_url}/voice/list"
            
            response = requests.get(url, headers=self.headers)
            result = response.json()
            
            if result.get("base_resp", {}).get("status_code") == 0:
                voices = result.get("voices", [])
                print(f"✓ 找到 {len(voices)} 个可用音色")
                return voices
            else:
                print(f"✗ 查询失败: {result.get('base_resp', {}).get('status_msg', '未知错误')}")
                return []
                
        except Exception as e:
            print(f"查询音色列表失败: {e}")
            return []


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="MiniMax 音色克隆工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 快速复刻音色
  python scripts/clone_voice.py clone --audio audio/巫巫女_sample.mp3 --voice-id wuwunv_001
  
  # 音色设计
  python scripts/clone_voice.py design --prompt "温柔的女巫声音" --voice-id wuwunv_002
  
  # 查询可用音色
  python scripts/clone_voice.py list
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # 快速复刻命令
    clone_parser = subparsers.add_parser("clone", help="快速复刻音色")
    clone_parser.add_argument("--audio", required=True, help="目标音频文件路径（10-30秒）")
    clone_parser.add_argument("--voice-id", required=True, help="自定义音色 ID")
    clone_parser.add_argument("--sample", help="示例音频文件路径（可选）")
    clone_parser.add_argument("--prompt", help="克隆提示词（可选）")
    
    # 音色设计命令
    design_parser = subparsers.add_parser("design", help="音色设计")
    design_parser.add_argument("--prompt", required=True, help="音色描述")
    design_parser.add_argument("--voice-id", required=True, help="自定义音色 ID")
    design_parser.add_argument("--model", default="speech-02-hd", help="模型版本（默认: speech-02-hd）")
    
    # 查询音色列表命令
    subparsers.add_parser("list", help="查询可用音色列表")
    
    args = parser.parse_args()
    
    # 检查 API Key
    if not MINIMAX_API_KEY:
        print("错误: 未设置 MINIMAX_API_KEY 环境变量")
        print("请在 .env 文件中配置: MINIMAX_API_KEY=your_api_key_here")
        sys.exit(1)
    
    # 创建客户端
    cloning = MiniMaxVoiceCloning(api_key=MINIMAX_API_KEY)
    
    # 执行命令
    if args.command == "clone":
        success = cloning.clone_voice(
            target_audio_file=args.audio,
            voice_id=args.voice_id,
            sample_audio_file=args.sample,
            clone_prompt=args.prompt or ""
        )
        
        if success:
            print(f"\n✓ 音色克隆完成！")
            print(f"现在可以在 scripts/config.py 中配置:")
            print(f'  "巫巫女": {{')
            print(f'    "minimax_voice_id": "{args.voice_id}",')
            print(f'    "minimax_emotion": "gentle"')
            print(f'  }}')
        else:
            sys.exit(1)
            
    elif args.command == "design":
        result = cloning.design_voice(
            prompt=args.prompt,
            voice_id=args.voice_id,
            model=args.model
        )
        
        if result:
            print(f"\n✓ 音色设计完成！")
            print(f"现在可以在 scripts/config.py 中配置:")
            print(f'  "巫巫女": {{')
            print(f'    "minimax_voice_id": "{args.voice_id}",')
            print(f'    "minimax_emotion": "gentle"')
            print(f'  }}')
        else:
            sys.exit(1)
            
    elif args.command == "list":
        voices = cloning.get_available_voices()
        
        if voices:
            print("\n可用音色列表:")
            print("-" * 60)
            for voice in voices[:20]:  # 只显示前20个
                voice_id = voice.get("voice_id", "N/A")
                voice_name = voice.get("voice_name", "N/A")
                print(f"  - {voice_id}: {voice_name}")
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
