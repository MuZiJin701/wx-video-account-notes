# wx-video-account-notes

一个微信视频号处理 skill。给它一个视频号分享链接，它会自动下载视频、提取 OCR / ASR、整理结构化材料，并默认继续生成 Markdown 笔记。

## 功能特性

- 处理 `https://weixin.qq.com/sph/...` 视频号分享链接
- 自动下载视频并抽取画面与音频内容
- OCR 提取画面文字
- ASR 提取口播文案
- 生成结构化材料，便于 agent 后续整理
- 默认继续输出同目录 Markdown 笔记
- 首次运行自动准备 `.runtime` 目录，后续可重复复用

## 优势

- 项目内 `.runtime` 目录保存 Python、依赖、ffmpeg 和模型，不污染系统环境
- 默认 CPU-only，不要求本机有 GPU、CUDA 或手工配置的 Python 环境
- 运行资产集中在 skill 目录下，便于复制、分发和清理
- 首次初始化后可复用，后续处理更快

## 系统要求

- Windows
- 使用 `skills` 或 `npx skills` 安装时，需要先安装 Node.js 和 npm
- 使用 Codex 插件市场安装时，需要先安装 Codex CLI
- 能访问 GitHub Releases、Hugging Face 和默认的视频号解析接口
- 首次运行允许下载 Python、依赖、工具和模型文件

## 安装指南

这个仓库只维护一份 skill 内容：

- skill 目录：`plugins/wx-video-account-notes/skills/wx-video-account-notes/`
- Codex 插件目录：`plugins/wx-video-account-notes/`
- Codex marketplace 清单：`.agents/plugins/marketplace.json`

推荐用 `skills` 全局安装。Codex 也可以走插件市场；已有 `cc-switch` 工作流的用户可以直接输入仓库地址。

### 推荐：skills 全局安装

优先使用 Vercel Labs 的 `skills` CLI 全局安装。这样安装后，支持该 skill 目录的 agent 都可以复用同一份 skill。

```powershell
npm install -g skills
skills add https://github.com/MuZiJin701/wx-video-account-notes.git -g
```

如果只想安装到 Codex，可以指定 agent：

```powershell
skills add https://github.com/MuZiJin701/wx-video-account-notes.git -g -a codex
```

如果不想全局安装 `skills` CLI，也可以用 `npx`：

```powershell
npx skills add https://github.com/MuZiJin701/wx-video-account-notes.git -g
```

常用管理命令：

```powershell
skills list
skills update wx-video-account-notes
skills remove wx-video-account-notes
```

`skills` CLI 的 Codex 全局安装目标是 `~/.codex/skills/`；安装完成后重启 Codex 以加载新 skill。

### 可选：Codex 插件市场

当前 GitHub 仓库也是一个 Codex marketplace 仓库，Codex 插件目录位于 `plugins/wx-video-account-notes/`。

```powershell
codex plugin marketplace add https://github.com/MuZiJin701/wx-video-account-notes.git
codex plugin add wx-video-account-notes@wx-video-account-notes-dev
```

### 可选：cc-switch

如果你通过 `cc-switch` 管理 skill，直接输入仓库地址即可：

```text
https://github.com/MuZiJin701/wx-video-account-notes.git
```

正常使用时，用户不需要手动运行脚本或处理环境细节。首次执行会自动准备 `.runtime` 目录，所以第一次通常更慢。

### 安装验证

安装完成后，开一个新会话，直接让 agent 处理一个视频号分享链接即可验证 skill 是否被加载。

如果使用 Codex 插件市场安装，命令成功时会返回 `pluginId`、`version` 和 `installedPath`。也可以重复执行：

```powershell
codex plugin add wx-video-account-notes@wx-video-account-notes-dev --json
```

只要返回插件元数据且没有报错，说明安装链路是通的。随后建议开一个新线程，让 Codex 直接处理一个视频号分享链接，确认 skill 能被实际调用。

## 快速开始

在 agent 中直接输入视频号链接，并说明你要做什么，例如：

```text
帮我处理这个视频号分享链接并生成笔记：https://weixin.qq.com/sph/...
```

或者：

```text
把这个视频号链接下载下来，整理成材料输出到 D:\notes\wx：https://weixin.qq.com/sph/...
```

正常情况下，agent 会自动完成：

- 首次初始化 `.runtime` 目录
- 下载视频
- 抽帧和抽音频
- OCR / ASR 提取
- 生成结构化材料
- 整理最终 Markdown 笔记

## 输出结果

处理完成后，输出目录通常会包含：

```text
<output-dir>/
  <slug>.mp4
  note_materials.json
  raw.json
  ocr.txt
  asr.txt
  frames/
  audio/
  <slug>.md
```

其中：

- `raw.json`：解析接口原始结果
- `ocr.txt`：OCR 原始文本
- `asr.txt`：ASR 原始文本
- `note_materials.json`：供模型整理的结构化材料
- `<slug>.md`：最终笔记成品

如果用户明确说不要笔记，可以跳过最终 Markdown 文件。

## 常见问题

### 为什么第一次运行更慢？

第一次运行会自动下载 Python、依赖、ffmpeg 和模型文件，并放在 skill 目录下的 `.runtime` 中，所以初始化时间会明显长于后续运行。

### 为什么仓库里没有 `.runtime/`？

`.runtime/` 是本地自动生成目录，不应提交到 GitHub。

### 为什么 OCR / ASR 比较慢？

当前默认是 CPU-only 方案，重点是稳定、可迁移和轻量分发，不依赖 GPU。

### 默认的视频号解析接口来自哪里？

默认解析接口使用的是：

- `https://sph.litao.workers.dev/api/fetch_video_profile`

这个默认解析能力参考自开源项目：

- `https://github.com/ltaoo/wx_channels_download`

## 文档

- `CHANGELOG.md`：变更历史
- `目录说明.md`：目录结构说明
- `ocr-asr-evaluation.md`：OCR / ASR 方案和实测记录
- `plugins/wx-video-account-notes/skills/wx-video-account-notes/SKILL.md`：skill 主说明

## 贡献指南

欢迎提交 issue 或 PR。

建议在提交前：

- 阅读 `README.md` 和 `CHANGELOG.md`
- 保持实现和文档同步更新
- 尽量让改动保持聚焦

## 致谢

- 默认视频号解析能力参考了 `ltaoo/wx_channels_download`
- 项目地址：`https://github.com/ltaoo/wx_channels_download`

## 许可证

本项目使用 `MIT` 许可证，详见 `LICENSE` 文件。

## 支持

- Bug 反馈：建议通过 GitHub Issues
- 使用说明：优先阅读本 README 和仓库中的补充文档
