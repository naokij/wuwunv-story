#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
火山引擎 API 调用模块
包括豆包 TTS 和即梦 AI 的 API 封装
"""

import hmac
import hashlib
import base64
import json
import time
import requests
import os
from typing import Optional, Dict, Any
from pathlib import Path
from collections import OrderedDict

try:
    from volcengine.visual.VisualService import VisualService
    VOLCENGINE_SDK_AVAILABLE = True
except ImportError:
    VOLCENGINE_SDK_AVAILABLE = False
    print("警告: 火山引擎 SDK 未安装，某些功能可能不可用")


class VolcEngineTTS:
    """豆包 TTS API 客户端"""

    def __init__(self, access_key: str = "", secret_key: str = "", app_id: str = "", access_token: str = ""):
        """
        初始化 TTS 客户端

        Args:
            access_key: 火山引擎 Access Key（方式 A）
            secret_key: 火山引擎 Secret Key（方式 A）
            app_id: 应用 ID（方式 B 必需）
            access_token: Access Token（方式 B 必需）
        """
        # 方式 A：Access Key + Secret Key
        self.access_key = access_key
        self.secret_key = secret_key

        # 方式 B：APP ID + Access Token
        self.app_id = app_id
        self.access_token = access_token

        # 判断是否使用方式 B（APP ID + Access Token）
        self.use_appid_token = bool(app_id and access_token)

        # 判断是否是复刻音色（音色 ID 以 S_ 开头）
        self.is_cloned_voice = False
        if access_token and (app_id and access_token):
            pass

        self.api_url = "https://openspeech.bytedance.com/api/v1/tts"

    def _generate_signature(self, request_body: str) -> str:
        """生成 API 签名（方式 A）"""
        hmac_obj = hmac.new(
            self.secret_key.encode('utf-8'),
            request_body.encode('utf-8'),
            hashlib.sha256
        )
        return base64.b64encode(hmac_obj.digest()).decode('utf-8')

    def synthesize_speech(
        self,
        text: str,
        voice_type: str,
        encoding: str = "mp3",
        speed_ratio: float = 1.0,
        volume_ratio: float = 1.0,
        model_type: str = "seed-tts-2.0",
        resource_id: str = None,
        cluster: Optional[str] = None
    ) -> Optional[bytes]:
        """
        合成语音

        Args:
            text: 要合成的文本
            voice_type: 音色类型
            encoding: 编码格式（mp3, wav 等）
            speed_ratio: 语速（0.5 - 2.0）
            volume_ratio: 音量（0.0 - 1.0）
            model_type: 模型版本
            resource_id: 资源 ID（用于复刻音色）

        Returns:
            音频数据（bytes），失败返回 None
        """
        # 根据 auth 方式构建请求
        if cluster:
            actual_cluster = cluster
        else:
            actual_cluster = "volcano_icl" if voice_type.startswith("S_") else "volcano_tts"

        if self.use_appid_token:
            # 方式 B：APP ID + Access Token
            request_body = {
                "app": {
                    "appid": self.app_id,
                    "token": self.access_token,
                    "cluster": actual_cluster
                },
                "user": {
                    "uid": "user_001"
                },
                "audio": {
                    "voice_type": voice_type,
                    "encoding": encoding,
                    "speed_ratio": speed_ratio,
                    "volume_ratio": volume_ratio,
                    "pitch_ratio": 1.0
                },
                "request": {
                    "reqid": f"req_{int(time.time() * 1000)}",
                    "text": text,
                    "text_type": "plain",
                    "operation": "query"
                }
            }

            if model_type == "seed-tts-2.0":
                request_body["audio"]["model_type"] = model_type

            if resource_id:
                request_body["audio"]["resource_id"] = resource_id

            body_str = json.dumps(request_body)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer;{self.access_token}"
            }
        else:
            # 方式 A：Access Key + Secret Key
            request_body = {
                "app": {
                    "appid": self.app_id or "default_appid",
                    "token": self.access_token or "default_token",
                    "cluster": actual_cluster
                },
                "user": {
                    "uid": "user_001"
                },
                "audio": {
                    "voice_type": voice_type,
                    "encoding": encoding,
                    "speed_ratio": speed_ratio,
                    "volume_ratio": volume_ratio,
                    "pitch_ratio": 1.0
                },
                "request": {
                    "reqid": f"req_{int(time.time() * 1000)}",
                    "text": text,
                    "text_type": "plain",
                    "operation": "query"
                }
            }

            if model_type == "seed-tts-2.0":
                request_body["audio"]["model_type"] = model_type

            if resource_id:
                request_body["audio"]["resource_id"] = resource_id

            body_str = json.dumps(request_body)
            signature = self._generate_signature(body_str)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_key}:{signature}"
            }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                data=body_str,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()

                is_success = (
                    result.get("code") == 0 or 
                    result.get("code") == 3000 or
                    result.get("message") == "Success"
                )

                if is_success:
                    audio_data = base64.b64decode(result.get("data", ""))
                    return audio_data
                else:
                    print(f"TTS API 错误: code={result.get('code')}, message={result.get('message')}")
                    return None
            else:
                print(f"TTS HTTP 错误: {response.status_code}")
                return None

        except Exception as e:
            print(f"TTS 请求失败: {e}")
            return None


class VolcEngineJimeng:
    """即梦 AI API 客户端"""

    def __init__(self, access_key: str = "", secret_key: str = "", app_id: str = ""):
        """
        初始化即梦 AI 客户端

        Args:
            access_key: 火山引擎 Access Key
            secret_key: 火山引擎 Secret Key
            app_id: 应用 ID（可选）
        """
        self.access_key = access_key
        self.secret_key = secret_key
        self.app_id = app_id

        # 尝试使用官方 SDK
        if VOLCENGINE_SDK_AVAILABLE:
            try:
                self.visual_service = VisualService()
                self.visual_service.set_ak(access_key)
                self.visual_service.set_sk(secret_key)
                self.use_sdk = True
            except Exception as e:
                print(f"警告: 初始化 SDK 失败: {e}")
                self.visual_service = None
                self.use_sdk = False
        else:
            self.visual_service = None
            self.use_sdk = False
            print("警告: 火山引擎 Visual SDK 未安装，某些功能可能不可用")

        # 即梦 AI 4.0 模型
        self.req_key = "jimeng_t2i_v40"

    def generate_image_with_reference(
        self,
        prompt: str,
        reference_image_paths: list[str] | str,
        reference_weight: float = 0.8,
        size: str = "1024*1020",
        quality: str = "high"
    ) -> Optional[str]:
        """
        使用参考图生成图像（图生图）

        Args:
            prompt: 图像描述提示词
            reference_image_paths: 参考图片路径列表或单个路径
            reference_weight: 参考图权重（0.0 - 1.0）
            size: 图像尺寸（1024*1020, 1080*1920 等）
            quality: 图像质量（standard, high）

        Returns:
            生成的图像 URL，失败返回 None
        """
        # 支持单张或多张参考图
        if isinstance(reference_image_paths, str):
            reference_image_paths = [reference_image_paths]
        
        # 即梦 AI 最多支持 10 张参考图
        if len(reference_image_paths) > 10:
            print(f"警告: 参考图数量超过限制（10张），将只使用前 10 张")
            reference_image_paths = reference_image_paths[:10]
        
        print(f"使用 {len(reference_image_paths)} 张参考图生成图像")
        result = self.generate_image(
            prompt=prompt,
            reference_images=reference_image_paths,
            reference_strength=reference_weight,
            quality=quality
        )
        
        if result.get("status") == "success":
            return result.get("image_url")
        else:
            print(f"生成失败: {result.get('message')}")
            return None

    def generate_image(self, prompt: str, **kwargs) -> dict:
        """
        生成图片（使用异步任务提交 + 轮询）

        Args:
            prompt: 提示词
            **kwargs: 其他参数
                - aspect_ratio: 宽高比，默认 "16:9"
                - image_count: 生成数量，默认 1
                - quality: 图片质量，默认 "high"
                - reference_images: 参考图片 URL 列表（可选，用于图生图）
                - reference_strength: 参考图强度，默认 0.5

        Returns:
            {
                "status": "success" | "error",
                "image_url": str,
                "image_base64": str,
                "task_id": str,
                "message": str
            }
        """
        try:
            # 1. 提交任务
            submit_result = self._submit_task(prompt, **kwargs)
            
            if submit_result.get("status") != "success":
                return submit_result

            task_id = submit_result.get("task_id")
            print(f"图片生成任务已提交，任务ID: {task_id}")

            # 2. 轮询任务状态
            print("开始轮询任务状态，最多尝试 30 次，每次间隔 10 秒...")
            for i in range(30):
                time.sleep(10)
                
                poll_result = self._poll_task_result(task_id)
                status = poll_result.get("status", "")
                
                print(f"第 {i+1} 次查询: 任务状态 = {status}")
                
                if status == "done":
                    # 任务完成，获取图片
                    image_base64 = poll_result.get("image_base64")
                    image_url = poll_result.get("image_url")
                    
                    if image_base64:
                        return {
                            "status": "success",
                            "image_base64": image_base64,
                            "task_id": task_id,
                            "message": "图片生成成功"
                        }
                    elif image_url:
                        return {
                            "status": "success",
                            "image_url": image_url,
                            "task_id": task_id,
                            "message": "图片生成成功"
                        }
                    else:
                        return {
                            "status": "error",
                            "message": "任务完成但未返回图片数据"
                        }
                elif status == "failed":
                    return {
                        "status": "error",
                        "message": poll_result.get("message", "任务失败")
                    }
                # 其他状态（如 pending, processing）继续轮询

            # 超时
            return {
                "status": "error",
                "message": "任务超时，请稍后手动查询任务状态"
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"生成图片失败: {str(e)}"
            }

    def _submit_task(self, prompt: str, **kwargs) -> dict:
        """提交文生图任务"""
        # 构建请求参数
        payload = {
            "req_key": self.req_key,
            "prompt": prompt,
            "aspect_ratio": kwargs.get("aspect_ratio", "16:9"),
            "image_count": kwargs.get("image_count", 1),
            "quality": kwargs.get("quality", "high"),
            "aigc_meta": {
                "content_producer": "wuwunv_story",
                "producer_id": "wuwunv",
                "content_propagator": "wuwunv_story",
                "propagate_id": "story_001"
            }
        }

        # 如果有参考图片，添加图生图参数
        if "reference_images" in kwargs:
            # 多张参考图
            reference_images = kwargs["reference_images"]
            binary_data_list = []
            for ref_path in reference_images:
                try:
                    with open(ref_path, "rb") as f:
                        img_data = base64.b64encode(f.read()).decode('utf-8')
                        binary_data_list.append(img_data)
                except Exception as e:
                    print(f"读取参考图失败 {ref_path}: {e}")
            
            if binary_data_list:
                payload["binary_data_base64"] = binary_data_list
                payload["reference_strength"] = kwargs.get("reference_strength", 0.5)
        elif "reference_image" in kwargs:
            # 单张参考图（向后兼容）
            payload["binary_data_base64"] = []
            try:
                with open(kwargs["reference_image"], "rb") as f:
                    img_data = base64.b64encode(f.read()).decode('utf-8')
                    payload["binary_data_base64"].append(img_data)
                payload["reference_strength"] = kwargs.get("reference_strength", 0.5)
            except Exception as e:
                print(f"读取参考图失败: {e}")

        # 使用 SDK 提交任务
        if self.use_sdk:
            try:
                resp = self.visual_service.cv_sync2async_submit_task(payload)
                print(f"API 响应: {resp}")

                # 即梦 AI 4.0 使用 code=10000 表示成功
                if resp.get("code") == 0 or resp.get("code") == 3000 or resp.get("code") == 10000:
                    return {
                        "status": "success",
                        "task_id": resp.get("data", {}).get("task_id"),
                        "request_id": resp.get("request_id")
                    }
                else:
                    return {
                        "status": "error",
                        "message": resp.get("message", f"任务提交失败，code={resp.get('code')}"),
                        "result": resp
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"SDK 调用失败: {str(e)}",
                    "result": None
                }
        else:
            # SDK 不可用
            return {
                "status": "error",
                "message": "火山引擎 SDK 未安装，无法调用即梦 AI API"
            }

    def _poll_task_result(self, task_id: str) -> dict:
        """轮询任务结果"""
        if not self.use_sdk:
            return {
                "status": "error",
                "message": "火山引擎 SDK 未安装"
            }

        try:
            payload = {
                "req_key": self.req_key,
                "task_id": task_id
            }

            resp = self.visual_service.cv_sync2async_get_result(payload)
            
            # 检查返回
            if resp.get("code") == 0 or resp.get("code") == 3000 or resp.get("code") == 10000:
                data = resp.get("data", {})
                
                # 检查任务状态
                status = data.get("status", "unknown")
                
                # 如果任务完成，返回图片数据
                if status == "done":
                    binary_data = data.get("binary_data_base64", [])
                    if binary_data:
                        return {
                            "status": "done",
                            "image_base64": binary_data[0] if binary_data else None
                        }
                    else:
                        return {
                            "status": "done",
                            "image_url": data.get("image_url")
                        }
                else:
                    return {
                        "status": status,
                        "message": data.get("message", f"任务状态: {status}")
                    }
            else:
                return {
                    "status": "error",
                    "message": resp.get("message", "查询失败")
                }

        except Exception as e:
            return {
                "status": "error",
                "message": f"查询任务失败: {str(e)}"
            }

    def download_image(self, image_url: str, output_path: str, image_base64: str = None) -> bool:
        """
        下载生成的图像

        Args:
            image_url: 图像 URL
            output_path: 保存路径
            image_base64: base64 编码的图片数据（可选）

        Returns:
            成功返回 True，失败返回 False
        """
        try:
            # 如果提供了 base64 数据，直接保存
            if image_base64:
                with open(output_path, 'wb') as f:
                    f.write(base64.b64decode(image_base64))
                return True
            
            # 否则从 URL 下载
            response = requests.get(image_url, timeout=30)
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True
            else:
                print(f"下载图像失败: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"下载图像异常: {e}")
            return False


if __name__ == "__main__":
    # 测试代码
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from config import (
        VOLCENGINE_ACCESS_KEY,
        VOLCENGINE_SECRET_KEY,
        VOLCENGINE_APP_ID,
        VOLCENGINE_ACCESS_TOKEN
    )

    # 测试即梦 AI
    jimeng = VolcEngineJimeng(VOLCENGINE_ACCESS_KEY, VOLCENGINE_SECRET_KEY)
    print(f"SDK 可用: {jimeng.use_sdk}")
