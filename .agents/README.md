# 巫巫女睡前故事集 - Agent 团队配置

本目录包含「巫巫女睡前故事集」项目的 AI Agent 配置文件，用于分工协作完成故事创作、审核、制作和发布。

## Agent 团队架构

```
ProjectCoordinator (项目协调师)
    ├── StoryCreator (故事创作师)
    ├── StoryReviewer (故事审核师)
    ├── 【人类】 (最终审核)
    ├── AudioProducer (音频制作师)
    ├── VisualDesigner (视觉设计师)
    ├── MetadataManager (元数据管理师)
    ├── WebMaintainer (网站维护师)
    └── DocumentationMaintainer (文档维护师)
```

## Agent 职责速览

| Agent | 主要职责 | 输出物 |
|-------|---------|--------|
| **StoryCreator** | 创作温馨治愈的故事 | Markdown 故事文件 |
| **StoryReviewer** | AI审核故事和封面质量 | 详细审核报告（含评分） |
| **【人类】** | 最终审核定稿 | 定稿确认 |
| **AudioProducer** | 生成 MP3 音频 | 音频文件 |
| **VisualDesigner** | 生成封面和缩略图 | 图片文件 |
| **MetadataManager** | 嵌入元数据 | 完整 MP3 |
| **WebMaintainer** | 更新网站并部署 | 网站更新 |
| **DocumentationMaintainer** | 更新各项目文档 | 文档更新 |
| **ProjectCoordinator** | 统筹全流程 | 项目报告 |

## 使用方式

### 方式一：手动切换 Agent
在对话开始时，让 AI 阅读对应的 Agent 配置文件：

```
请阅读 /Users/jiangle/project/wuwunv/.agents/01-story-creator.md，然后帮我创作一个新故事。
```

### 方式二：使用 ProjectCoordinator
直接让协调师来统筹任务：

```
请阅读 /Users/jiangle/project/wuwunv/.agents/07-project-coordinator.md，我需要创作一个新故事，主题是...
```

### 方式三：配置到 IDE
在 Cursor、Windsurf 等 IDE 中，可以：
1. 将 `.agents` 目录配置为 Agent 上下文
2. 通过 `@` 符号快速切换 Agent 角色
3. 或使用自定义命令触发特定 Agent

## 工作流程

### 标准新故事流程（含人工审核和文档维护）
```
1. ProjectCoordinator 分析需求
2. StoryCreator 创作故事初稿
3. StoryReviewer AI审核（详细报告+评分）
4. 【人类】最终审核定稿 ← 关键节点！
5. AudioProducer + VisualDesigner 并行制作
6. StoryReviewer 审核封面
7. MetadataManager 嵌入元数据
8. WebMaintainer 部署网站
9. DocumentationMaintainer 更新文档
10. ProjectCoordinator 报告完成
```

### 人工审核环节说明
**为什么需要人工审核？**
- AI审核可能有遗漏
- 需要人类判断是否符合孩子当前兴趣
- 确保价值观符合家庭期望

**人工审核检查项**：
- [ ] 整体阅读体验流畅自然
- [ ] 符合女儿当前年龄和兴趣
- [ ] 没有不适合家庭价值观的内容
- [ ] 确认可以进入制作阶段

### 文档维护环节说明
**文档维护师在媒体文件完成后执行**：
- 更新 `设定文档.md`（新光芒/角色/道具）
- 更新 `README.md`（故事目录表格）
- 更新 `AGENTS.md`（清单和更新日志）
- 确保各文档之间信息一致

### 已有故事制作流程
```
1. AudioProducer 生成音频
2. VisualDesigner 生成封面
3. StoryReviewer 审核封面
4. MetadataManager 嵌入元数据
5. WebMaintainer 更新网站
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `01-story-creator.md` | 故事创作师配置 |
| `02-story-reviewer.md` | 故事审核师配置（含详细审核模板） |
| `03-audio-producer.md` | 音频制作师配置 |
| `04-visual-designer.md` | 视觉设计师配置 |
| `05-metadata-manager.md` | 元数据管理师配置 |
| `06-web-maintainer.md` | 网站维护师配置 |
| `07-project-coordinator.md` | 项目协调师配置（含人工审核流程） |
| `08-documentation-maintainer.md` | 文档维护师配置 |

## 审核报告标准

StoryReviewer 必须提供以下内容的审核报告：
1. **质量评分表**（各维度10分制）
2. **优点清单**（至少3条具体优点）
3. **问题清单**（按高/中/低优先级分级）
4. **具体修改建议**（原文+建议+理由）
5. **总体评价**（整体判断）
6. **下一步行动**（明确后续步骤）

## 协作原则

1. **单一职责**：每个 Agent 专注于自己的专业领域
2. **顺序执行**：审核必须在创作之后，元数据必须在音视频之后
3. **并行优化**：音频和封面可以并行制作；网站部署和文档更新可并行
4. **质量把关**：AI审核+人工审核双重把关，确保故事质量
5. **详细报告**：审核必须提供详细报告（评分+优点+问题+建议）
6. **人工定稿**：媒体制作前必须经过人类最终审核确认
7. **文档同步**：媒体文件完成后必须同步更新相关文档
8. **用户确认**：关键节点征求用户意见

## 快速命令参考

```bash
# 一键生成故事（音频+封面）
python scripts/generate_story.py "XX-故事标题.md"

# 嵌入元数据
python scripts/add_metadata_to_existing.py "audio/XX-故事标题.mp3"

# 批量处理
python scripts/batch_add_metadata.py

# 生成缩略图
python scripts/generate_thumbnails.py

# 更新网站数据
cd website && node scripts/generate-stories.js

# 验证音频
python scripts/verify_audio.py "audio/XX-故事标题.mp3"
```

## 更新日志

- 2026-03-06: 初始创建 7 个 Agent 配置文件
- 2026-03-06: 优化更新
  - 增加 DocumentationMaintainer（文档维护师）
  - 增加人工最终审核环节
  - 优化 StoryReviewer 审核标准（移除二级标题要求）
  - 增加详细审核报告模板（含评分系统）
  - 完善工作流程，明确各阶段检查项
