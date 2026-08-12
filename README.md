# wx-video-account-notes

将微信视频号分享链接转换为可供 agent 整理的笔记材料和 Markdown 笔记。
Convert WeChat Channels share links into structured note materials and Markdown notes for agents.

[![Tests](https://github.com/MuZiJin701/wx-video-account-notes/actions/workflows/tests.yml/badge.svg)](https://github.com/MuZiJin701/wx-video-account-notes/actions/workflows/tests.yml)

## 核心能力 | What it does

- **一条链接开始**：处理视频动态和图文动态，自动识别媒体类型
- **提取可复用材料**：生成 OCR、ASR、视觉帧、元数据和处理状态
- **继续生成成稿**：agent 基于 `note_materials.json` 输出同目录 Markdown 笔记
- **One link in**: process video and image posts with automatic media-type detection
- **Structured output**: produce OCR, ASR, visual frames, metadata, and processing status
- **Agent-ready notes**: use `note_materials.json` to create a Markdown note beside the media

## 为什么适合长期使用 | Why this project

- **跨平台**：支持 Windows x64、macOS Intel x64 和 Linux x64
- **环境隔离**：项目私有 uv、Python 3.13.14、FFmpeg 和模型，不污染系统环境
- **CPU 优先**：默认不依赖 GPU、CUDA 或系统 FFmpeg
- **结果可检查**：原始响应、OCR、ASR、帧和状态分别保存，失败不会伪装成成功
- **可重复运行**：运行时按 `.runtime/<os>-<arch>/` 隔离，初始化后复用
- **Cross-platform**: supports Windows x64, Intel macOS x64, and Linux x64
- **Self-contained runtime**: uses private uv, Python 3.13.14, FFmpeg, and models
- **CPU-first**: no GPU, CUDA, or system FFmpeg setup is required
- **Inspectable results**: raw data, OCR, ASR, frames, and status stay as separate artifacts
- **Repeatable runs**: each platform reuses its isolated `.runtime/<os>-<arch>/`

## 快速开始 | Quick start

### 1. 安装 skill | Install the skill

推荐使用 `skills` CLI：
Use the `skills` CLI for a global installation:

```sh
npm install -g skills
skills add https://github.com/MuZiJin701/wx-video-account-notes.git -g -a codex
```

也可以使用 Codex 插件市场：
You can also install the Codex plugin:

```sh
codex plugin marketplace add https://github.com/MuZiJin701/wx-video-account-notes.git
codex plugin add wx-video-account-notes@wx-video-account-notes-dev
```

### 2. 直接处理链接 | Process a link

在 agent 中输入：
Send this prompt to your agent:

```text
处理这个视频号分享链接并生成笔记：
https://weixin.qq.com/sph/your_share_id_here
```

首次运行会下载私有运行时、锁定依赖、FFmpeg 和模型。请预留网络访问权限和磁盘空间。
The first run downloads the private runtime, locked dependencies, FFmpeg, and the model.

### 3. 指定输出目录 | Choose an output directory

```text
把这个视频号链接整理到 D:\notes\wx：
https://weixin.qq.com/sph/your_share_id_here
```

## 输出结构 | Output

处理完成后，输出目录通常包含：
The output directory usually contains:

```text
<output-dir>/
  <slug>.mp4          # video posts only
  note_materials.json # structured handoff for the agent
  raw.json            # raw resolver response
  ocr.txt             # OCR text
  asr.txt             # ASR text, empty for image posts
  ocr_frames/         # subtitle crops for video OCR
  frames/             # visual frames or downloaded images
  audio/              # extracted audio for video posts
  <slug>.md           # final note written by the agent
```

图文动态跳过视频、音频和 ASR；原始图片会进入 `frames/`，并可作为 `visual_frames` 供有识图能力的模型读取。
Image posts skip video, audio, and ASR. Their source images go to `frames/` and can be exposed as `visual_frames`.

## 支持范围 | Support

| 项目 | 范围 |
| --- | --- |
| 操作系统 | Windows x64、macOS Intel x64、Linux x64 |
| Python | 3.13.14，项目私有环境 |
| 推理 | CPU-only，faster-whisper tiny |
| 输入 | `https://weixin.qq.com/sph/...` 分享链接 |
| 外部服务 | 视频号解析接口、GitHub Releases、Hugging Face |

ARM64、GPU 推理和离线首次初始化不在当前支持范围内。
ARM64, GPU inference, and offline first-time bootstrap are outside the current support scope.

## 本地开发 | Development

运行时位于 `plugins/wx-video-account-notes/skills/wx-video-account-notes/`：
The runtime project lives at `plugins/wx-video-account-notes/skills/wx-video-account-notes/`:

```sh
cd plugins/wx-video-account-notes/skills/wx-video-account-notes
uv sync --locked
uv run --locked python -m unittest discover -s runtime/tests
```

真实初始化和端到端处理属于手动 smoke test：
Use the manual smoke workflow for real bootstrap and end-to-end processing:

```powershell
pwsh -File scripts\bootstrap.ps1
pwsh -File scripts\verify_runtime.ps1
pwsh -File scripts\invoke_pipeline.ps1 -ShareUrl "https://weixin.qq.com/sph/your_share_id_here"
```

```sh
sh scripts/bootstrap.sh
sh scripts/verify_runtime.sh
sh scripts/invoke_pipeline.sh --share-url "https://weixin.qq.com/sph/your_share_id_here"
```

## 文档导航 | Documentation

- [Skill 使用说明](plugins/wx-video-account-notes/skills/wx-video-account-notes/SKILL.md)
- [目录地图](目录说明.md)
- [领域术语](CONTEXT.md)
- [跨平台运行时决策](docs/adr/0001-cross-platform-runtime.md)
- [测试策略](docs/adr/0002-test-strategy.md)
- [OCR / ASR 评估](docs/evaluations/ocr-asr-evaluation.md)
- [变更日志](CHANGELOG.md)

## 贡献与许可证 | Contributing and license

请先阅读 `AGENTS.md`，再通过 GitHub Issues 提交需求或问题。保持实现、测试和文档同步。
Read `AGENTS.md` before contributing. Use GitHub Issues for requests and bug reports, and keep code, tests, and docs aligned.

本项目使用 MIT 许可证，详见 [LICENSE](LICENSE)。
This project is released under the MIT License. See [LICENSE](LICENSE).
