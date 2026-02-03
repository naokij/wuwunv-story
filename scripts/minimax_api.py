#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MiniMax TTS API 客户端
支持 speech-2.8-hd 等模型的语音合成
使用 WebSocket API 实现
支持语气词标签
"""

import asyncio
import websockets
import ssl
import json
import time
from typing import Optional, Dict, Any


class MiniMaxTTS:
    """MiniMax 文本转语音 API 客户端"""

    # 类变量，用于控制请求速率
    _last_request_time = 0
    _min_request_interval = 6.0  # 最小请求间隔（秒），根据 MiniMax 限速：每分钟 10 次

    def __init__(self, api_key: str = ""):
        """
        初始化 MiniMax TTS 客户端

        Args:
            api_key: MiniMax API Key（pay-as-you-go 或 coding plan key）
        """
        self.api_key = api_key
        self.ws_url = "wss://api.minimaxi.com/ws/v1/t2a_v2"
        
        # 默认参数
        self.default_model = "speech-2.8-hd"  # 最新 HD 模型
        self.default_vol = 1.0  # 音量
        self.default_pitch = 0  # 音调
        self.default_speed = 1.0  # 语速

    def _rate_limit_wait(self):
        """请求限速控制"""
        current_time = time.time()
        time_since_last_request = current_time - MiniMaxTTS._last_request_time
        
        if time_since_last_request < MiniMaxTTS._min_request_interval:
            sleep_time = MiniMaxTTS._min_request_interval - time_since_last_request
            print(f"等待 {sleep_time:.2f} 秒以避免触发 API 限流...")
            time.sleep(sleep_time)
        
        MiniMaxTTS._last_request_time = time.time()

    def synthesize_speech(
        self,
        text: str,
        voice_id: str,
        model: str = None,
        speed: float = None,
        vol: float = None,
        pitch: int = None,
        emotion: str = None
    ) -> Optional[bytes]:
        """
        合成语音（使用 WebSocket API）

        Args:
            text: 要合成的文本（可包含语气词标签）
            voice_id: 音色 ID（系统音色或克隆音色）
            model: 模型版本（默认：speech-2.8-hd）
            speed: 语速（默认：1.0）
            vol: 音量（默认：1.0）
            pitch: 音调（默认：0）
            emotion: 情感控制（已废弃，MiniMax 会根据内容自动设置）

        Returns:
            音频数据（bytes），失败返回 None
        
        支持的语气词标签（仅 speech-2.8-hd 和 speech-2.8-turbo 支持）：
            (laughs) - 笑声
            (chuckle) - 轻笑
            (coughs) - 咳嗽
            (clear-throat) - 清嗓子
            (groans) - 呻吟
            (breath) - 正常换气
            (pant) - 喘气
            (inhale) - 吸气
            (exhale) - 呼气
            (gasps) - 倒吸气
            (sniffs) - 吸鼻子
            (sighs) - 叹气
            (snorts) - 喷鼻息
            (burps) - 打嗝
            (lip-smacking) - 咂嘴
            (humming) - 哼唱
            (hissing) - 嘶嘶声
            (emm) - 嗯
            (sneezes) - 喷嚏
        """
        # 使用默认值
        model = model or self.default_model
        speed = speed if speed is not None else self.default_speed
        vol = vol if vol is not None else self.default_vol
        pitch = pitch if pitch is not None else self.default_pitch

        # emotion 参数已废弃，MiniMax 会根据内容自动设置
        if emotion:
            print(f"提示: emotion 参数已废弃，MiniMax 会根据内容自动设置感情，将被忽略")
        
        # 检查文本中是否包含语气词标签
        if model not in ["speech-2.8-hd", "speech-2.8-turbo"]:
            import re
            tone_pattern = r'\((laughs|chuckle|coughs|clear-throat|groans|breath|pant|inhale|exhale|gasps|sniffs|sighs|snorts|burps|lip-smacking|humming|hissing|emm|sneezes)\)'
            if re.search(tone_pattern, text, re.IGNORECASE):
                print(f"警告: 检测到文本中包含语气词标签，但当前模型 {model} 不支持，标签将被忽略")
        
        # 运行异步 WebSocket 调用
        self._rate_limit_wait()
        return asyncio.run(self._synthesize_via_websocket(
            text=text,
            voice_id=voice_id,
            model=model,
            speed=speed,
            vol=vol,
            pitch=pitch
        ))

    async def _synthesize_via_websocket(
        self,
        text: str,
        voice_id: str,
        model: str,
        speed: float,
        vol: float,
        pitch: int,
        emotion: str = None
    ) -> Optional[bytes]:
        """通过 WebSocket 合成语音"""
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            async with websockets.connect(
                self.ws_url,
                additional_headers=headers,
                ssl=ssl_context
            ) as ws:
                # 等待连接成功
                connected_msg = json.loads(await ws.recv())
                if connected_msg.get("event") != "connected_success":
                    print(f"连接失败: {connected_msg}")
                    return None
                
                # 构建开始任务请求
                start_msg = {
                    "event": "task_start",
                    "model": model,
                    "voice_setting": {
                        "voice_id": voice_id,
                        "speed": int(speed),
                        "vol": int(vol),
                        "pitch": int(pitch)
                    }
                }
                
                await ws.send(json.dumps(start_msg))
                
                # 等待任务开始
                start_response = json.loads(await ws.recv())
                if start_response.get("event") != "task_started":
                    print(f"任务启动失败: {start_response}")
                    return None
                
                # 发送文本（文本中可包含语气词标签）
                await ws.send(json.dumps({
                    "event": "task_continue",
                    "text": text
                }))
                
                # 收集音频数据
                audio_data = b""
                while True:
                    response = json.loads(await ws.recv())
                    
                    if "data" in response and "audio" in response["data"]:
                        audio_hex = response["data"]["audio"]
                        if audio_hex:
                            audio_data += bytes.fromhex(audio_hex)
                    
                    if response.get("is_final"):
                        break
                    
                    if response.get("event") == "task_failed":
                        error_msg = response.get("base_resp", {}).get("status_msg", "未知错误")
                        print(f"任务失败: {error_msg}")
                        return None
                
                # 结束任务
                await ws.send(json.dumps({"event": "task_finish"}))
                
                return audio_data if audio_data else None
                
        except Exception as e:
            print(f"WebSocket 请求失败: {e}")
            return None


if __name__ == "__main__":
    # 测试代码
    import sys
    import os
    from pathlib import Path
    
    # 从环境变量读取配置
    from dotenv import load_dotenv
    env_file = Path('.env')
    load_dotenv(env_file)
    
    api_key = os.environ.get("MINIMAX_API_KEY", "")
    
    if not api_key:
        print("错误: 未设置 MINIMAX_API_KEY 环境变量")
        sys.exit(1)
    
    # 创建客户端
    tts = MiniMaxTTS(api_key=api_key)
    
    # 测试合成（带语气词标签）
    text = "你好，这是一个测试。"
    voice_id = "wuwunv_gentle_taozi"  # 使用克隆的音色
    
    # 语气词标签示例
    tone_tags = [
        "你好/(ni3)(hao3)",  # 指定拼音
        "测试/ceshi4"  # 英文或拼音
    ]
    
    audio_data = tts.synthesize_speech(
        text=text,
        voice_id=voice_id,
        model="speech-2.8-hd",
        tone_tags=tone_tags
    )
    
    if audio_data:
        output_file = "test_minimax_output.mp3"
        with open(output_file, "wb") as f:
            f.write(audio_data)
        print(f"✓ 音频已保存到: {output_file}")
    else:
        print("✗ 音频生成失败")