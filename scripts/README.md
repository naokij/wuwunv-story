# 脚本目录说明

## 主要脚本

### auto_generate_story.py
自动化故事生成工具，从 Markdown 文件生成音频、封面和元数据。

**文档**：[auto_generate_story_README.md](auto_generate_story_README.md)

**使用示例**：
```bash
# 生成完整故事
python scripts/auto_generate_story.py "23-森林小动物的音乐狂欢日.md"

# 只生成封面
python scripts/auto_generate_story.py "23-森林小动物的音乐狂欢日.md" --cover-only

# 批量生成所有故事
python scripts/auto_generate_story.py --all
```

### volcengine_api.py
火山引擎 API 封装，包括：
- TTS（文本转语音）
- 即梦 AI（图片生成）

### config.py
项目配置文件，包含：
- API 密钥配置
- TTS 音色和模型设置
- 封面生成参数
- 角色配置

### get_tts_voices.py
TTS 音色查询工具，帮助查找和选择合适的音色。

**使用示例**：
```bash
python scripts/get_tts_voices.py
```

## 工具脚本

### process_audio.py
音频处理工具，包括音频分割、合并、转换等功能。

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
VOLCENGINE_ACCESS_KEY=your_access_key
VOLCENGINE_SECRET_KEY=your_secret_key
```

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