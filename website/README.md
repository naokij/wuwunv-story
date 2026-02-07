# 巫巫女睡前故事集 - 网站

基于 Astro 构建的静态网站，展示巫巫女睡前故事集。

## 技术栈

- **框架**: [Astro](https://astro.build/)
- **样式**: 原生 CSS（CSS Variables）
- **部署**: GitHub Pages
- **音频托管**: GitHub Raw

## 本地开发

```bash
# 进入网站目录
cd website

# 安装依赖
npm install

# 生成故事数据
node scripts/generate-stories.js

# 启动开发服务器
npm run dev

# 构建
npm run build
```

## 项目结构

```
website/
├── src/
│   ├── components/     # 可复用组件
│   │   ├── AudioPlayer.astro    # 自定义音频播放器
│   │   ├── Header.astro         # 页面头部导航
│   │   ├── Pagination.astro     # 分页组件
│   │   └── StoryCard.astro      # 故事卡片
│   ├── layouts/        # 布局组件
│   │   └── Layout.astro
│   ├── pages/          # 页面路由
│   │   ├── index.astro          # 首页（故事列表）
│   │   ├── page/[page].astro    # 分页
│   │   └── story/[id].astro     # 故事详情页
│   ├── data/           # 数据文件
│   │   └── stories.json         # 故事数据（自动生成）
│   └── scripts/        # 脚本
│       └── generate-stories.js  # 生成故事数据
├── .github/workflows/   # GitHub Actions
│   └── deploy.yml       # 自动部署配置
└── astro.config.mjs    # Astro 配置
```

## 自动部署

每次推送到 `main` 分支时，GitHub Actions 会自动：
1. 安装依赖
2. 生成故事数据
3. 构建网站
4. 部署到 GitHub Pages

## 设计参考

基于 Google Stitch 生成的原型设计：
- 首页：`website/stitch_prototype/巫巫女睡前故事集_首页/screen.png`
- 详情页：`website/stitch_prototype/巫巫女睡前故事集_详情页/screen.png`

## 版权信息

© 2026 巫巫女睡前故事集 · 江乐

本项目代码采用 MIT 协议开源。
故事内容版权所有，请勿商用。

## 功能特性

- ✅ 响应式设计（桌面/平板/手机）
- ✅ 分页展示（每页 9 个故事）
- ✅ 自定义音频播放器
- ✅ 上一篇/下一篇导航
- ✅ 中文排版优化
- ✅ 零成本托管

## 项目地址

- **网站**: https://naokij.github.io/wuwunv-story/
- **源码**: https://github.com/naokij/wuwunv-story
