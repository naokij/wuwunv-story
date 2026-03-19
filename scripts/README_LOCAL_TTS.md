# 本地 TTS 使用说明

使用 Qwen3-TTS 模型在本地生成故事音频，完全免费，无需 API 密钥。

## 功能特点

- **声音克隆**：使用参考音频克隆音色
- **情感自动适配**：模型根据文本内容自动调整情感表达
- **两种模型选择**：0.6B（更快）和 1.7B（质量更高）
- **多格式输出**：支持 WAV 和 MP3 格式

## 环境要求

- macOS with Apple Silicon（M1/M2/M3/M4）
- Python 3.12+
- 内存：至少 10GB（0.6B 模型）或 13GB（1.7B 模型）
- 磁盘空间：约 6.5GB（模型缓存）

## 安装

```bash
# 安装依赖
pip install mlx-audio

# 如果需要 MP3 输出，确保已安装 ffmpeg
brew install ffmpeg
```

## 模型下载

首次运行时会自动从 HuggingFace 下载模型：

| 模型 | 大小 | 缓存位置 |
|------|------|----------|
| 0.6B-Base | 2.3 GB | `~/.cache/huggingface/hub/` |
| 1.7B-Base | 4.2 GB | `~/.cache/huggingface/hub/` |

无需手动下载，脚本会自动处理。

## 使用方法

### 基本用法

```bash
# 激活虚拟环境
source venv/bin/activate

# 使用默认 0.6B 模型生成音频
python scripts/generate_audio_local.py "01-巫巫女的心变了.md"

# 使用 1.7B 模型（质量更高，速度更慢）
python scripts/generate_audio_local.py "01-巫巫女的心变了.md" --model 1.7b
```

### 输出格式

```bash
# 输出 WAV 格式（默认）
python scripts/generate_audio_local.py "故事文件.md"

# 输出 MP3 格式
python scripts/generate_audio_local.py "故事文件.md" --format mp3
```

### 强制重新生成

```bash
# 跳过已存在的文件检查
python scripts/generate_audio_local.py "故事文件.md" --force
```

### 自定义参考音频

```bash
# 使用自定义参考音频
python scripts/generate_audio_local.py "故事文件.md" \
  --ref-audio ./my-voice.wav \
  --ref-text "这是参考音频对应的文字内容。"
```

## 性能参考

| 模型 | 实时倍率 | 10分钟音频耗时 | 内存占用 |
|------|----------|----------------|----------|
| 0.6B | ~0.32x | 约 31 分钟 | ~8 GB |
| 1.7B | ~0.19x | 约 53 分钟 | ~12 GB |

**实时倍率说明**：0.32x 表示生成 1 秒音频需要约 3 秒。

## 参考音频

默认使用 `audio/references/taozi-ref.wav` 作为参考音频，这是「温柔桃子」音色的采样。

**参考音频要求**：
- 格式：WAV（推荐）、MP3
- 时长：5-15 秒
- 内容：清晰、无背景噪音、单一说话人
- 文本：需要提供对应的文字稿

## 与 MiniMax API 对比

| 对比项 | 本地 TTS | MiniMax API |
|--------|----------|-------------|
| 费用 | 免费 | 按字符计费 |
| 速度 | 约 0.32x | 约 0.1x（更快） |
| 音质 | 良好 | 优秀 |
| 情感控制 | 自动 | 自动 + 可选标签 |
| 需要联网 | 仅首次下载模型 | 每次都需要 |
| 隐私 | 完全本地 | 数据上传云端 |

## 完整工作流程

使用本地 TTS 生成故事音频的完整流程：

```bash
# 1. 安装依赖（首次）
pip install mlx-audio

# 2. 生成音频（首次会自动下载模型）
python scripts/generate_audio_local.py "故事文件.md" --format mp3

# 3. 生成封面（仍需火山引擎 API）
python scripts/generate_cover.py "故事文件.md"

# 4. 嵌入元数据
python scripts/add_metadata_to_existing.py "audio/故事文件.mp3"

# 5. 生成缩略图
python scripts/generate_thumbnails.py

# 6. 更新 README.md 故事目录
```

## 清理模型缓存

如果不再使用，可以删除模型缓存释放磁盘空间：

```bash
# 删除所有 Qwen3-TTS 模型缓存
rm -rf ~/.cache/huggingface/hub/models--mlx-community--Qwen3-TTS*
```

## 常见问题

### Q: 模型下载速度慢怎么办？

模型从 HuggingFace 下载，国内网络可能较慢。可以：
1. 使用代理
2. 手动下载模型文件到缓存目录

### Q: 生成速度能提升吗？

可以尝试：
1. 使用 0.6B 模型（更快）
2. 关闭其他占用内存的应用
3. 确保 Mac 有足够的散热空间

### Q: 生成的声音和参考音频不像？

参考音频质量很关键：
- 确保参考音频清晰、无噪音
- 参考音频时长建议 5-15 秒
- 参考文本必须与音频内容一致

### Q: 为什么不用官方 qwen-tts 包？

官方包不支持 Apple Silicon 的 GPU 加速。mlx-audio 是专门为 Apple Silicon 优化的版本。
