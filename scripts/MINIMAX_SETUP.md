# MiniMax TTS 配置指南

本项目已集成 MiniMax 的 Speech 2.8 HD 模型，提供更高质量的语音合成和情感控制功能。

## 功能特点

- ✅ 更高的音色相似度和自然度
- ✅ 支持情感控制（gentle, happy, sad 等）
- ✅ 支持最长 10,000 字符的单次合成
- ✅ 支持音色克隆和音色设计
- ✅ 支持多种语气词标签（笑声、叹气等）

## 配置步骤

### 1. 获取 API 密钥

1. 访问 [MiniMax 开放平台](https://www.minimaxi.com/)
2. 登录或注册账号
3. 进入"用户中心" → "接口密钥"
4. 创建新的 API Key，获取 `MINIMAX_API_KEY`

**API Key 类型**：
- **Pay-as-you-go**：按量付费，支持所有模型（文本、语音、图像、视频等）
- **Coding Plan**：套餐类型，仅支持文本模型，更便宜但不支持语音

**注意**：本项目需要使用 Pay-as-you-go 类型的 API Key，因为需要使用语音合成功能。

### 2. 配置环境变量

在项目根目录的 `.env` 文件中添加：

```bash
MINIMAX_API_KEY=your_api_key_here
```

### 3. 获取或创建音色

#### 方式 A：使用系统音色（快速开始）

MiniMax 提供了 300+ 系统音色，可以直接使用。常用音色包括：

- `female-tianmeijiaojia` - 甜美娇娇
- `male-qn-qingse` - 青涩男声
- `female-shaonv` - 少女音色

#### 方式 B：音色快速复刻（推荐）

1. 访问 [MiniMax Audio](https://www.minimaxi.com/audio)
2. 点击"Voices" → "Create Your Voice Clone"
3. 上传 10-30 秒的音频文件
4. 输入自定义的 `voice_id`（如：`wuwunv_001`）
5. 完成克隆，获取 `voice_id`

#### 方式 C：音色设计（高级）

1. 访问 [音色设计](https://www.minimaxi.com/audio)
2. 输入声音描述（如："温柔的女巫声音，语调轻柔，适合讲故事"）
3. 生成音色，获取 `voice_id`

### 4. 配置角色音色

在 `.env` 文件中配置统一的音色（所有角色使用同一个音色）：

```bash
# MiniMax 统一音色配置
MINIMAX_VOICE_ID=wuwunv_001  # 你的音色 ID
MINIMAX_EMOTION=gentle  # 情感: gentle（温柔）, happy（欢快）, sad（悲伤）等
```

**本项目已配置的音色**：

| 环境变量 | 音色 ID | 说明 | 音源 |
|---------|---------|------|------|
| `MINIMAX_VOICE_ID` | `wuwunv_gentle_taozi` | 温柔的女巫声音，适合讲故事 | audio/豆包温柔桃子升级版.mp3 |

该音色已于 2026-02-03 使用 MiniMax Speech 2.8 HD 模型克隆完成。

**查看可用音色**：

使用克隆工具查询所有可用音色：

```bash
python scripts/clone_voice.py list
```

或访问 [MiniMax 音色管理](https://www.minimaxi.com/audio) 查看和管理你的音色。

### 5. 情感控制

MiniMax 支持的情感类型：

- `gentle` - 温柔
- `happy` - 欢快
- `sad` - 悲伤
- `angry` - 愤怒
- `excited` - 兴奋
- `calm` - 平静

### 6. 语气词标签

在文本中可以插入语气词标签（仅 speech-2.8-hd 和 speech-2.8-turbo 支持）：

- `(laughs)` - 笑声
- `(sighs)` - 叹气
- `(coughs)` - 咳嗽
- `(clear-throat)` - 清嗓子
- `(breath)` - 正常换气
- `(emm)` - 嗯

示例：
```markdown
巫巫女笑着说：(laughs) 欢迎来到我的小屋！
```

## 使用方法

配置完成后，直接运行脚本即可：

```bash
python scripts/auto_generate_story.py "23-森林小动物的音乐狂欢日.md"
```

脚本会自动检测并使用 MiniMax TTS（如果配置了 API 密钥）。

## 音色克隆工具

本项目提供了音色克隆工具 `scripts/clone_voice.py`，可以通过命令行快速克隆音色。

### 查看可用音色

```bash
python scripts/clone_voice.py list-voices
```

### 快速克隆音色

```bash
python scripts/clone_voice.py clone --audio "path/to/audio.mp3" --voice-id "custom_voice_id"
```

参数说明：
- `--audio`: 音频文件路径（10-30 秒，mp3/m4a/wav 格式）
- `--voice-id`: 自定义音色 ID（8-256 字符，首字母必须为英文字母）

### 音色设计

```bash
python scripts/clone_voice.py design --prompt "温柔的年轻女声，适合讲故事" --preview-text "你好，我是巫巫女。"
```

### 测试音色

```bash
python scripts/clone_voice.py test --voice-id "wuwunv_001" --text "你好，这是一个测试。"
```

## 技术说明

本项目使用 WebSocket API 而非 HTTP API，原因如下：

1. **HTTP API 问题**：MiniMax 的 HTTP TTS API 存在参数验证问题，返回 "invalid params, empty field" 错误
2. **WebSocket API 优势**：
   - 更稳定的连接
   - 支持流式输出
   - 更好的错误处理
   - 官方推荐方式

## 优势对比

| 特性 | MiniMax Speech 2.8 HD | 豆包 TTS 2.0 |
|------|----------------------|--------------|
| 音色相似度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 情感控制 | ✅ 支持 | ❌ 不支持 |
| 单次文本长度 | 10,000 字符 | 1,024 字节 |
| 音色克隆 | ✅ 10秒快速克隆 | ✅ 需要训练 |
| 语气词标签 | ✅ 支持 | ❌ 不支持 |

## 注意事项

1. **API 密钥安全**：不要将 `.env` 文件提交到 Git
2. **音色有效期**：快速复刻的音色在 7 天内至少使用一次，否则会被删除
3. **费用**：音色克隆费用在首次使用时收取
4. **认证要求**：使用音色克隆功能需要完成实名认证或企业认证

## 故障排除

### 问题：API 限流错误（HTTP 429）

**解决方案**：
- 本项目已内置请求限速控制（默认 0.5 秒间隔）
- 如果批量生成多个故事，建议间隔 1-2 秒
- 升级账户等级可以获得更高的 QPS 限制

### 问题：脚本仍然使用豆包 TTS

**解决方案**：确认 `.env` 文件中正确配置了 `MINIMAX_API_KEY`，并且使用的是 Pay-as-you-go 类型（不支持 Coding Plan，因为它不包含语音功能）

### 问题：音色 ID 无效

**解决方案**：
1. 检查 `voice_id` 是否正确
2. 确认音色是否已创建成功
3. 访问 [MiniMax 音色管理](https://www.minimaxi.com/audio) 查看可用音色列表

### 问题：情感控制不生效

**解决方案**：
1. 确认使用的是 speech-2.8-hd 或 speech-2.8-turbo 模型
2. 检查 `emotion` 参数是否正确
3. 某些音色可能不支持所有情感类型

## 相关链接

- [MiniMax 官网](https://www.minimaxi.com/)
- [同步语音合成 API 文档](https://platform.minimaxi.com/docs/api-reference/speech-t2a-http)
- [音色快速复刻文档](https://platform.minimaxi.com/docs/api-reference/voice-cloning-create)
- [音色设计文档](https://platform.minimaxi.com/docs/api-reference/voice-design-design)
- [API 请求限制](https://platform.minimaxi.com/user-center/basic-information/request-limits)

## API 限速说明

MiniMax API 有请求频率限制，具体限制取决于账户等级：

**同步语音合成 API 限速**：
- **默认限制**：每分钟 10 次请求（6 秒间隔）
- 不同账户等级可能有不同的限制

**本项目已内置请求限速控制**：
- 默认请求间隔：6 秒（符合每分钟 10 次的限制）
- 避免触发 429 错误（请求过多）
- 批量生成时会自动等待

**建议**：
- 批量生成故事时，每个故事生成大约需要 10-30 秒（取决于文本长度）
- 如果需要更高并发，请升级 MiniMax 账户或使用异步长文本语音生成 API
