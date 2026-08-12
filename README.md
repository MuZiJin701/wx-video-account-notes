# wx-video-account-notes

把一个微信视频号分享链接转换成可交给 agent 的结构化笔记材料，再生成 Markdown 笔记。

[English README](README.en.md) · [![Tests](https://github.com/MuZiJin701/wx-video-account-notes/actions/workflows/tests.yml/badge.svg)](https://github.com/MuZiJin701/wx-video-account-notes/actions/workflows/tests.yml)

## 核心优势

- **一条链接开始**：自动处理视频动态和图文动态。
- **材料完整**：保留原始响应、元数据、OCR、ASR、视觉帧和处理状态，方便 agent 继续整理。
- **结果可检查**：失败会明确记录，不把缺失内容伪装成成功。
- **跨平台且 CPU 优先**：支持 Windows x64、macOS Intel x64 和 Linux x64，不要求 GPU、CUDA 或系统 FFmpeg。
- **环境隔离**：项目私有 Python、uv、FFmpeg 和模型按平台缓存，初始化后可重复使用。

## 快速开始

### 安装

```sh
npm install -g skills
skills add https://github.com/MuZiJin701/wx-video-account-notes.git -g -y
```

首次运行会下载当前平台的私有运行时、锁定依赖、FFmpeg 和模型，请预留网络访问权限与磁盘空间。

### Codex 插件（可选）

也可以通过 Codex 插件市场安装：

```sh
codex plugin marketplace add https://github.com/MuZiJin701/wx-video-account-notes.git
codex plugin add wx-video-account-notes@wx-video-account-notes-dev
```

如果使用 `cc-switch`，直接输入仓库地址即可。

### 处理链接

把下面的请求和真实链接交给 agent：

```text
处理这个视频号分享链接并生成笔记：
https://weixin.qq.com/sph/your_share_id_here
```

需要指定目录时，直接补充路径：

```text
把这个视频号链接整理到 D:\notes\wx：
https://weixin.qq.com/sph/your_share_id_here
```

## 输出

```text
<output-dir>/
  <slug>.mp4          # 仅视频动态
  note_materials.json # 交给 agent 的结构化材料
  raw.json            # 原始解析响应
  ocr.txt             # OCR 文本
  asr.txt             # ASR 文本；图文动态为空
  ocr_frames/         # 视频 OCR 使用的字幕裁切图
  frames/             # 视觉帧或原始图片
  audio/              # 视频动态的音频
  <slug>.md           # agent 生成的最终笔记
```

图文动态跳过视频、音频和 ASR；原始图片进入 `frames/`，并可作为 `visual_frames` 供有识图能力的模型读取。

## 支持范围

| 项目 | 范围 |
| --- | --- |
| 操作系统 | Windows x64、macOS Intel x64、Linux x64 |
| Python | 3.13.14，项目私有环境 |
| 推理 | CPU-only，faster-whisper tiny |
| 输入 | `https://weixin.qq.com/sph/...` 分享链接 |
| 外部服务 | 视频号解析接口、GitHub Releases、Hugging Face |

ARM64、GPU 推理和离线首次初始化暂不支持。

## 本地开发

```sh
cd plugins/wx-video-account-notes/skills/wx-video-account-notes
uv sync --locked
uv run --locked python -m unittest discover -s runtime/tests
```

真实初始化和端到端处理属于手动 smoke test：

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

## 文档

- [Skill 使用说明](plugins/wx-video-account-notes/skills/wx-video-account-notes/SKILL.md)
- [目录地图](目录说明.md)
- [领域术语](CONTEXT.md)
- [架构决策](docs/adr/)
- [测试与评估](plugins/wx-video-account-notes/skills/wx-video-account-notes/tests/test-cases.md)
- [变更日志](CHANGELOG.md)

## 贡献与许可证

请先阅读 [AGENTS.md](AGENTS.md)，再通过 GitHub Issues 提交需求或问题。本项目使用 MIT 许可证，详见 [LICENSE](LICENSE)。
