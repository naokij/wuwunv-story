#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
火山引擎 API 调用模块
即梦 AI 的 API 封装，用于封面生成
"""

import json
import time
import base64
import requests
from typing import Optional, Dict, Any
from pathlib import Path

try:
    from volcengine.visual.VisualService import VisualService
    VOLCENGINE_SDK_AVAILABLE = True
except ImportError:
    VOLCENGINE_SDK_AVAILABLE = False
    print("警告: 火山引擎 SDK 未安装，封面生成功能可能不可用")


class VolcEngineJimeng:
    """即梦 AI API 客户端（用于封面生成）"""

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
            print("警告: 火山引擎 Visual SDK 未安装，封面生成功能可能不可用")

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
                    image_bytes = poll_result.get("image_bytes")
                    image_url = poll_result.get("image_url")
                    
                    # 优先使用 image_bytes
                    if image_bytes:
                        return {
                            "status": "success",
                            "image_bytes": image_bytes,
                            "task_id": task_id,
                            "message": "图片生成成功"
                        }
                    
                    # 其次使用 image_url
                    if image_url:
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
            
            # 打印完整响应用于调试
            print(f"查询响应: {resp}")
            
            # 检查返回
            if resp.get("code") == 0 or resp.get("code") == 3000 or resp.get("code") == 10000:
                data = resp.get("data", {})
                
                # 检查任务状态
                status = data.get("status", "unknown")
                
                # 如果任务完成，返回图片数据
                if status == "done":
                    binary_data = data.get("binary_data_base64", [])
                    if binary_data and len(binary_data) > 0:
                        # binary_data_base64 是一个列表，取第一个元素
                        img_data = binary_data[0]
                        if isinstance(img_data, str):
                            # 如果是 base64 字符串，尝试解码
                            try:
                                import base64
                                image_bytes = base64.b64decode(img_data)
                                return {
                                    "status": "done",
                                    "image_bytes": image_bytes
                                }
                            except:
                                return {
                                    "status": "error",
                                    "message": "Base64 解码失败"
                                }
                        elif isinstance(img_data, bytes):
                            return {
                                "status": "done",
                                "image_bytes": img_data
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
        VOLCENGINE_SECRET_KEY
    )

    # 测试即梦 AI
    jimeng = VolcEngineJimeng(VOLCENGINE_ACCESS_KEY, VOLCENGINE_SECRET_KEY)
    print(f"SDK 可用: {jimeng.use_sdk}")
