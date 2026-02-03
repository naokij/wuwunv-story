# 自动生成故事脚本说明

## 功能概述

`auto_generate_story.py` 是一个自动化脚本，用于从 Markdown 故事文件生成：
- **音频**：使用火山引擎 TTS 生成故事朗读音频
- **封面**：使用即梦 AI 生成故事封面图片
- **元数据**：将故事标题、内容和封面嵌入到 MP3 文件中

## 前置要求

### 1. API 密钥配置

在 `.env` 文件中配置火山引擎 API 密钥：

**方式 A：Access Key + Secret Key**
```env
VOLCENGINE_ACCESS_KEY=your_access_key
VOLCENGINE_SECRET_KEY=your_secret_key
```

**方式 B：APP ID + Access Token**
```env
VOLCENGINE_APP_ID=your_app_id
VOLCENGINE_ACCESS_TOKEN=your_access_token
```

### 2. 角色参考图

在 `audio/references/` 目录中准备角色参考图：

- `巫巫女_reference.jpg` - 巫巫女的角色形象
- `莉莉_reference.jpg` - 莉莉的角色形象
- `欣欣_reference.jpg` - 欣欣的角色形象

参考图需要在豆包 App 中生成，确保角色形象一致。

### 3. 依赖安装

```bash
pip install -r requirements.txt
```

## 故事文件格式

故事文件使用 Markdown 格式，支持 YAML frontmatter：

```markdown
---
title: 故事标题
cover_prompt: "自定义的封面提示词，描述画面场景和风格"
cover_characters:
  - 巫巫女
  - 莉莉
voice_instruction: "用欢快活泼的语气说"
---

# 故事正文

这里写故事内容...
```

### Frontmatter 字段说明

- `title`：故事标题（可选，覆盖正文中的标题）
- `cover_prompt`：自定义封面提示词（可选，替换自动生成的 prompt）
- `cover_characters`：封面中包含的角色列表（可选，用于多角色参考图）
- `voice_instruction`：语音指令（可选，控制语气和情感）

### 语音指令控制

**注意**：火山引擎的语音指令功能（如 `[#用欢快活泼的语气说]`）目前**仅支持在豆包 App 和实时音视频（RTC）场景下使用**，**不支持在 TTS API 中使用**。

如果尝试在 TTS API 中使用语音指令格式，会导致指令文本被读出来（如"用欢快活泼的语气说"）。

#### 当前可用的语气控制方法：

1. **选择合适的音色**：不同的音色有不同的默认语气和风格
   - 温柔桃子（S_ieReLKSR1）：温柔治愈，适合睡前故事
   - 甜美桃子（zh_female_tianmeitaozi_mars_bigtts）：甜美可爱
   - 温柔女神（ICL_zh_female_wenrounvshen_239eff5e8ffa_tob）：温柔优雅

2. **调整语速和音调**：通过 `speed_ratio` 和 `pitch_ratio` 参数微调
   - 语速：0.5 - 2.0（默认 1.0）
   - 音调：0.5 - 2.0（默认 1.0）

3. **使用 SSML（需特定音色支持）**：
   - SSML 的 `<emotion>` 标签可以指定情感
   - 但仅支持部分中文普通话音色
   - seed-tts-2.0 模型可能不支持 SSML

如果您需要更精细的语气控制，建议：
- 咨询火山引擎客服，了解支持情感控制的音色列表
- 考虑使用异步长文本 API 的"情感预测版"，该版本支持 `style` 参数
- 或使用豆包 App 的语音指令功能进行配音

## 使用方法

### 生成完整故事（音频 + 封面）

```bash
python scripts/auto_generate_story.py "23-森林小动物的音乐狂欢日.md"
```

### 只生成封面（音频必须已存在）

```bash
python scripts/auto_generate_story.py "23-森林小动物的音乐狂欢日.md" --cover-only
```

### 只生成音频（不生成封面）

```bash
python scripts/auto_generate_story.py "23-森林小动物的音乐狂欢日.md" --no-cover
```

### 批量生成所有故事

```bash
python scripts/auto_generate_story.py --all
```

### 批量生成所有封面

```bash
python scripts/auto_generate_story.py --all --cover-only
```

## 工作流程

### 完整生成流程

1. **读取故事文件**：解析 Markdown 文件和 frontmatter
2. **生成音频**：
   - 提取故事文本
   - 如果文本超过 1024 字节，自动分段
   - 调用火山引擎 TTS 生成音频
   - 合并音频片段
3. **生成封面**：
   - 提取主要角色
   - 从 frontmatter 读取自定义 prompt 和角色列表
   - 加载角色参考图（支持多角色）
   - 调用即梦 AI 生成封面
4. **添加元数据**：
   - 将故事标题写入 MP3 标题
   - 将故事内容写入歌词（USLT 标签）
   - 将封面图片嵌入 MP3（APIC 标签）

### 只生成封面流程

1. **检查封面文件**：如果封面文件已存在，跳过 API 请求
2. **生成封面**：如果封面不存在，调用即梦 AI 生成
3. **嵌入封面**：删除 MP3 中所有现有封面标签，添加新封面

## 配置选项

在 `scripts/config.py` 中可以配置：

### TTS 配置
- `TTS_VOICE_TYPE`：TTS 音色（支持标准音色和复刻音色）
- `TTS_MODEL_TYPE`：TTS 模型类型
- `USE_APPID_TOKEN_AUTH`：是否使用 APP ID + Access Token 认证

### 封面生成配置
- `JIMENG_ASPECT_RATIO`：封面宽高比（默认 "1024*1020"）
- `JIMENG_IMAGE_QUALITY`：图片质量（默认 "high"）
- `JIMENG_REFERENCE_WEIGHT`：参考图权重（默认 0.8）

### 角色配置
- `CHARACTERS`：角色配置字典，包含每个角色的基础提示词和参考图路径

## 输出文件

生成的文件位于 `audio/` 目录：

- `{故事名称}.mp3` - 音频文件（包含封面和元数据）
- `{故事名称}.jpeg` - 封面图片文件

## 注意事项

1. **API 限制**：TTS API 单次请求最多支持 1024 字节，脚本会自动处理超长文本
2. **封面缓存**：使用 `--cover-only` 时，如果封面文件已存在，会跳过 API 请求，避免重复计费
3. **封面替换**：脚本会删除 MP3 中所有现有的封面标签，确保正确替换
4. **多角色支持**：即梦 AI 最多支持 10 张参考图，可以在 frontmatter 中指定多个角色

## 故障排查

### 音频生成失败
- 检查 API 密钥是否正确
- 检查网络连接
- 查看错误信息

### 封面生成失败
- 检查即梦 AI 服务是否开通
- 检查参考图文件是否存在
- 检查 API 密钥权限

### 封面未嵌入 MP3
- 确认音频文件存在
- 确认封面文件已生成
- 查看错误日志

## 常见问题

**Q: 为什么封面文件已存在还会调用 API？**

A: 使用 `--cover-only` 参数时，脚本会检查封面文件是否存在。如果存在，会跳过 API 请求，直接使用现有封面。

**Q: 如何修改封面风格？**

A: 在故事文件的 frontmatter 中添加 `cover_prompt` 字段，自定义封面提示词。

**Q: 如何在封面中包含多个角色？**

A: 在故事文件的 frontmatter 中添加 `cover_characters` 字段，列出角色名称。

**Q: 音频分段生成后会有停顿吗？**

A: 脚本使用直接拼接的方式合并音频片段，可能会在分段处有轻微停顿。如果需要无缝拼接，可以使用交叉淡入淡出处理。