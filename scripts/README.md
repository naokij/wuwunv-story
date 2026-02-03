# 脚本目录说明

## 主要脚本

### generate_story.py
整合脚本，一键生成音频和封面。

**使用示例**：
```bash
# 生成完整故事（音频 + 封面）
python scripts/generate_story.py "23-森林小动物的音乐狂欢日.md"

# 只生成音频
python scripts/generate_story.py "23-森林小动物的音乐狂欢日.md" --skip-cover

# 只生成封面
python scripts/generate_story.py "23-森林小动物的音乐狂欢日.md" --skip-audio

# 强制重新生成
python scripts/generate_story.py "23-森林小动物的音乐狂欢日.md" --force
```

### generate_audio.py
独立的音频生成脚本，使用 MiniMax TTS API。

**使用示例**：
```bash
# 生成音频
python scripts/generate_audio.py "23-森林小动物的音乐狂欢日.md"

# 强制重新生成
python scripts/generate_audio.py "23-森林小动物的音乐狂欢日.md" --force
```

### generate_cover.py
独立的封面生成脚本，使用火山引擎即梦 AI。

**使用示例**：
```bash
# 生成封面
python scripts/generate_cover.py "23-森林小动物的音乐狂欢日.md"

# 强制重新生成
python scripts/generate_cover.py "23-森林小动物的音乐狂欢日.md" --force
```

### minimax_api.py
MiniMax TTS API 封装，使用 WebSocket 协议。

**特性**：
- 支持 MiniMax Speech 2.8 HD 模型
- 支持复刻音色
- 内置速率限制（10 次/分钟）
- 异步操作支持

### volcengine_api.py
火山引擎即梦 AI API 封装，用于封面图片生成。

**特性**：
- 支持多角色参考图
- 支持自定义图片尺寸和质量
- 异步任务提交 + 轮询

### config.py
项目配置文件，包含：
- MiniMax API 密钥和音色配置
- 火山引擎 API 密钥配置
- 封面生成参数（宽高比、质量）
- 角色配置（基础提示词、参考图路径）

### clone_voice.py
MiniMax 音色克隆工具。

**使用示例**：
```bash
python scripts/clone_voice.py audio/豆包温柔桃子升级版.mp3
```

## 工具脚本（备用）

### process_audio.py
音频处理工具，从录屏视频中提取音频、去除静音、添加淡入效果。

### add_metadata_to_existing.py
为现有音频文件添加元数据（标题、内容、封面）。

### batch_add_metadata.py
批量添加元数据到多个音频文件。

### generate_thumbnails.py
为封面图片生成缩略图。

### verify_audio.py
验证音频文件的完整性。

## 配置文件

### .env
环境变量配置（包含 API 密钥等敏感信息）

**示例**：
```env
# MiniMax TTS 配置
MINIMAX_API_KEY=your_minimax_api_key
MINIMAX_VOICE_ID=wuwunv_gentle_taozi
MINIMAX_EMOTION=gentle

# 火山引擎即梦 AI 配置
VOLCENGINE_ACCESS_KEY=your_access_key
VOLCENGINE_SECRET_KEY=your_secret_key
VOLCENGINE_APP_ID=your_app_id
```

## 文档

### MINIMAX_SETUP.md
MiniMax 配置和使用文档。

### auto_generate_story_README.md
自动生成工具说明文档（已废弃，保留作为参考）。

## 输出目录

### audio/
- `{故事名称}.mp3` - 生成的音频文件
- `{故事名称}.jpeg` - 生成的封面图片
- `{故事名称}_thumb.jpeg` - 封面缩略图

### audio/references/
角色参考图目录，包含：
- 巫巫女_reference.jpg
- 莉莉_reference.jpg
- 欣欣_reference.jpg

## 依赖安装

```bash
pip install -r requirements.txt
```

## 注意事项

1. 所有脚本需要在项目根目录下运行
2. 确保已配置 .env 文件中的 API 密钥
3. 角色参考图需要提前准备并放在 `audio/references/` 目录
4. 故事文件支持 YAML frontmatter 来自定义封面生成
5. MiniMax TTS API 速率限制为 10 次/分钟，脚本已自动处理
6. 火山引擎封面生成需要 5-10 分钟，请耐心等待