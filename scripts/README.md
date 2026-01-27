# 音频处理脚本

本目录包含音频处理相关的 Python 脚本。

## 脚本列表

- **process_audio.py**: 从录屏文件中提取音频，去除空白，嵌入封面和元数据
- **verify_audio.py**: 验证 MP3 文件的元数据和封面
- **add_metadata_to_existing.py**: 为已存在的 MP3 文件添加元数据

## 使用方法

所有脚本都需要从项目根目录运行，使用 `scripts/` 前缀：

```bash
# 处理录屏文件
python scripts/process_audio.py <录屏文件>

# 验证 MP3 文件
python scripts/verify_audio.py <MP3文件>

# 为已存在的 MP3 添加元数据
python scripts/add_metadata_to_existing.py <MP3文件>
```

详细使用说明请参考项目根目录的 `README_音频处理.md`。
