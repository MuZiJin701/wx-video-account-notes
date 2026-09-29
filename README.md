# wx-video-account-notes

把一个微信视频号分享链接转换成可交给 agent 的结构化笔记材料，再生成 Markdown 笔记。

[English README](README.en.md) · [![Tests](https://github.com/MuZiJin701/wx-video-account-notes/actions/workflows/tests.yml/badge.svg)](https://github.com/MuZiJin701/wx-video-account-notes/actions/workflows/tests.yml)

## 两种使用方式

| 方式 | 适合谁 | 需要做什么 |
| --- | --- | --- |
| **直接使用维护者解析服务（默认）** | 所有用户 | 安装 Skill，提交分享链接；无需部署服务器或配置凭证。 |
| **自行部署解析服务（可选）** | 希望自行管理解析服务的用户 | 在自己的 Linux x64 服务器部署解析服务和元宝登录态，再为 Skill 配置自己的接口地址与凭证。 |

两种方式都只在服务器解析视频号分享链接；媒体下载、OCR、ASR 和笔记生成在用户本机完成。下方[快速开始](#快速开始)列出两条路径。

## 核心优势

- **一条链接开始**：自动处理视频动态和图文动态。
- **材料完整**：保留原始响应、元数据、OCR、ASR、视觉帧和处理状态，方便 agent 继续整理。
- **结果可检查**：失败会明确记录，不把缺失内容伪装成成功。
- **跨平台且 CPU 优先**：支持 Windows x64、macOS Intel x64 和 Linux x64，不要求 GPU、CUDA 或系统 FFmpeg。
- **环境隔离**：项目私有 Python、uv、FFmpeg 和模型按平台缓存，初始化后可重复使用。

## 当前解析状态

默认服务已于 2026 年 9 月 29 日通过真实链接的解析、下载、OCR、ASR 和 Markdown 笔记验收。它使用公网 HTTP，分享链接、解析响应和公开 Skill 内的共用凭证均明文传输；该凭证不具备保密性，服务全局每分钟限流 30 次请求。元宝登录态由维护者在服务器更新，服务当前由维护者手动启动。详情见[解析服务说明](docs/resolver-deployment.md)。

## 快速开始

### 安装 Skill

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

### 直接使用维护者解析服务（默认）

安装后无需配置服务器或凭证。把下面的请求和真实链接交给 agent：

```text
处理这个视频号分享链接并生成笔记：
https://weixin.qq.com/sph/your_share_id_here
```

需要指定目录时，直接补充路径：

```text
把这个视频号链接整理到 D:\notes\wx：
https://weixin.qq.com/sph/your_share_id_here
```

### 自行部署解析服务（可选）

1. 按[自部署说明](docs/resolver-deployment.md)在自己的 Linux x64 服务器构建并启动解析服务，使用自己的元宝 Cookie 和访问凭证。
2. 在启动 agent 的环境中同时设置 `WX_VIDEO_ACCOUNT_RESOLVE_API`（自己的完整解析接口地址）和 `WX_VIDEO_ACCOUNT_RESOLVE_KEY`（自己的访问凭证）。两者缺一不可；取消这两项配置即可恢复默认服务。
3. 像上面一样把分享链接交给 agent。自部署服务失败时不会自动改用维护者服务。

自部署服务若使用公网 HTTP，也会明文传输分享链接、访问凭证和解析响应；需要保密传输时请为自己的服务配置 HTTPS 入口。

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
| 外部服务 | 维护者的公网 HTTP 解析接口或自部署解析服务、GitHub Releases、Hugging Face |

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
- [视频号获取原理](docs/research/wx-channels-architecture.md)
- [解析服务部署与维护](docs/resolver-deployment.md)
- [测试与评估](plugins/wx-video-account-notes/skills/wx-video-account-notes/tests/test-cases.md)
- [变更日志](CHANGELOG.md)

## 贡献与许可证

请先阅读 [AGENTS.md](AGENTS.md)，再通过 GitHub Issues 提交需求或问题。本项目使用 MIT 许可证，详见 [LICENSE](LICENSE)。
