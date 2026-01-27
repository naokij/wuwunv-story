# 音频处理工具使用说明

这个工具可以帮助你处理从 iPhone 录屏中提取的音频文件。

## 功能

1. **提取音频**: 从录屏文件（.mov, .mp4 等）中提取音频
2. **去除空白**: 自动检测并去除音频前后的静音部分
3. **嵌入封面**: 自动查找同名图片文件或使用指定的封面图片
4. **嵌入元数据**: 自动查找同名故事文件，将标题、简介和全文嵌入到 MP3 元数据中

## 安装依赖

### 1. 安装 ffmpeg

macOS:
```bash
brew install ffmpeg
```

### 2. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 基本用法（自动查找封面和故事）

```bash
python scripts/process_audio.py <录屏文件>
```

例如：
```bash
python scripts/process_audio.py screen_recording.mov
```

工具会自动：
- 在 `audio/` 目录下查找同名的封面图片（如 `01-巫巫女的心变了.jpeg`）
- 在项目根目录查找同名的故事文件（如 `01-巫巫女的心变了.md`）
- 生成处理后的 MP3 文件（如 `screen_recording_processed.mp3`）

### 指定输出文件

```bash
python scripts/process_audio.py screen_recording.mov output.mp3
```

### 指定封面图片

```bash
python scripts/process_audio.py screen_recording.mov output.mp3 cover.jpg
```

### 指定故事文件

```bash
python scripts/process_audio.py screen_recording.mov output.mp3 cover.jpg story.md
```

### 为已存在的 MP3 文件添加元数据

如果你已经有一个 MP3 文件，想要添加或更新元数据，可以使用：

```bash
python scripts/add_metadata_to_existing.py <MP3文件> [封面图片] [故事文件]
```

例如：
```bash
python scripts/add_metadata_to_existing.py audio/01-巫巫女的心变了.mp3
```

工具会自动查找同名的封面和故事文件。

### 批量处理 audio 目录中的所有 MP3 文件

如果你想一次性为 audio 目录中所有缺少元数据的 MP3 文件添加元数据：

```bash
python scripts/batch_add_metadata.py
```

**模拟运行**（查看会处理哪些文件，不实际修改）：
```bash
python scripts/batch_add_metadata.py --dry-run
```

**指定目录**：
```bash
python scripts/batch_add_metadata.py --dir <目录路径>
```

批量处理脚本会：
- 自动扫描指定目录中的所有 MP3 文件
- 检查每个文件是否已有完整的元数据（标题、封面、简介、全文）
- 只处理缺少元数据的文件
- 自动跳过已有完整元数据的文件
- 显示处理统计信息

## 文件命名规则

工具会自动匹配文件，按照项目的目录结构查找：

1. **封面图片**: 查找与音频文件同名的图片（去除括号内容）
   - 查找顺序：`audio/` 目录 → 当前目录 → 项目根目录
   - 例如：`audio/01-巫巫女的心变了（豆包朗读版）.mp3` 会查找 `audio/01-巫巫女的心变了.jpeg`
   - 支持的格式：`.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`

2. **故事文件**: 查找与音频文件同名的 Markdown 文件
   - 查找顺序：项目根目录 → 当前目录
   - 例如：`audio/01-巫巫女的心变了（豆包朗读版）.mp3` 会查找 `01-巫巫女的心变了.md`（在项目根目录）

## 元数据说明

处理后的 MP3 文件会包含以下元数据：

- **标题**: 故事标题（从 .md 文件第一行读取）
- **艺术家**: "巫巫女睡前故事"
- **专辑**: "巫巫女睡前故事集"
- **类型**: "儿童故事"
- **封面**: 嵌入的图片
- **简介**: 故事的前几段（作为注释）
- **全文**: 完整的故事内容（作为歌词/文本字段）

## 注意事项

1. 确保 `ffmpeg` 已正确安装并可在命令行中使用
2. 录屏文件可以是 `.mov`, `.mp4` 等常见视频格式
3. 静音检测阈值设置为 -30dB，持续 0.5 秒以上会被识别为静音
4. 如果找不到封面或故事文件，工具会跳过相应步骤，但不会报错

## 验证元数据和封面

处理完成后，可以使用验证脚本检查 MP3 文件：

```bash
python scripts/verify_audio.py <MP3文件>
```

例如：
```bash
python scripts/verify_audio.py audio/01-巫巫女的心变了.mp3
```

验证脚本会显示：
- ✓ 基本信息（时长、比特率等）
- ✓ 元数据（标题、艺术家、专辑、类型）
- ✓ 封面信息（MIME 类型、大小，并会提取封面保存为文件）
- ✓ 简介和全文信息

**验证封面的小技巧**：
1. 运行验证脚本后，会自动提取封面保存为 `文件名_cover.jpg`
2. 可以用图片查看器打开提取的封面文件确认
3. 在支持 ID3 标签的播放器（如 iTunes、VLC、foobar2000）中打开 MP3，应该能看到封面

## 示例工作流

假设你有一个录屏文件 `10-巫巫女的春日野餐（录屏）.mov`：

1. 将录屏文件放在项目目录或 `audio/` 目录
2. 运行：
   ```bash
   python scripts/process_audio.py "10-巫巫女的春日野餐（录屏）.mov"
   ```
3. 工具会：
   - 提取音频
   - 去除前后空白
   - 查找 `audio/10-巫巫女的春日野餐.jpeg` 作为封面
   - 查找 `10-巫巫女的春日野餐.md` 读取故事内容
   - 生成 `10-巫巫女的春日野餐（录屏）_processed.mp3`
4. 验证结果：
   ```bash
   python scripts/verify_audio.py "10-巫巫女的春日野餐（录屏）_processed.mp3"
   ```
