# wx-video-account-notes

把一个微信视频号分享链接交给 agent，生成可检查的笔记材料和 Markdown 笔记。支持视频动态与图文动态。

[English README](README.en.md) · [![Tests](https://github.com/MuZiJin701/wx-video-account-notes/actions/workflows/tests.yml/badge.svg)](https://github.com/MuZiJin701/wx-video-account-notes/actions/workflows/tests.yml)

## 开始使用

支持 Windows x64、macOS Intel x64 和 Linux x64。首次处理会从 GitHub Releases、Hugging Face 等来源下载项目私有的 Python、依赖、FFmpeg 和模型；需要联网和足够的磁盘空间，之后可复用。

### 1. 安装 Skill

```sh
npm install -g skills
skills add https://github.com/MuZiJin701/wx-video-account-notes.git -g -y
```

Codex 用户也可通过插件市场安装：

```sh
codex plugin marketplace add https://github.com/MuZiJin701/wx-video-account-notes.git
codex plugin add wx-video-account-notes@wx-video-account-notes-dev
```

使用 `cc-switch` 时，直接输入仓库地址。

### 2. 发送分享链接

默认使用项目维护者的解析服务，无需配置服务器或凭证。把真实链接交给 agent：

```text
处理这个视频号分享链接并生成笔记：
https://weixin.qq.com/sph/your_share_id_here
```

想指定输出目录，可在请求中写明，例如“把这个链接整理到 D:\notes\wx”。

### 想使用自己的服务器？

按[自部署指南](docs/resolver-deployment.md)在 Linux 服务器克隆本仓库并启动解析服务，再为 agent 配置自己的接口地址和访问凭证。自部署服务失败时不会自动改用默认服务。

## 生成的文件

```text
<output-dir>/
  <slug>.mp4          # 仅视频动态
  note_materials.json # 结构化材料和处理状态
  raw.json            # 原始解析响应
  ocr.txt             # 识别出的画面文字
  asr.txt             # 语音转文字；图文动态为空
  ocr_frames/         # 视频字幕裁切图
  frames/             # 视频参考帧或原始图片
  audio/              # 视频音频
  <slug>.md           # 最终笔记
```

图文动态不生成视频和音频；有识图能力的 agent 还会读取 `frames/` 中的图片辅助写笔记。处理失败会记录在材料中，不会伪装成成功。

## 运行方式与限制

- 服务器只解析分享链接；下载媒体、OCR、ASR 和写笔记在本机完成，不需要 GPU 或系统 FFmpeg。
- 默认服务使用公网 HTTP，分享链接和解析结果明文传输；公开 Skill 内的共用访问凭证不是秘密。服务对所有用户合计每分钟最多处理 30 次请求。
- 默认服务的登录态由维护者更新，服务进程目前需要手动启动。自部署也可使用 HTTPS 入口，详见[部署指南](docs/resolver-deployment.md)。
- 目前不支持 ARM64、GPU 推理或离线首次初始化。项目私有 Python 版本为 3.13.14，ASR 使用 CPU 上的 faster-whisper tiny。

## 本地开发

```sh
cd plugins/wx-video-account-notes/skills/wx-video-account-notes
uv sync --locked
uv run --locked python -m unittest discover -s runtime/tests
```

真实初始化和端到端处理需手动检查：

```powershell
pwsh -File scripts\bootstrap.ps1
pwsh -File scripts\verify_runtime.ps1
pwsh -File scripts\invoke_pipeline.ps1 -ShareUrl "https://weixin.qq.com/sph/your_share_id_here"
```

macOS/Linux 对应命令为 `sh scripts/bootstrap.sh`、`sh scripts/verify_runtime.sh` 和 `sh scripts/invoke_pipeline.sh --share-url "https://weixin.qq.com/sph/your_share_id_here"`。

## 更多文档

- [自部署与故障排查](docs/resolver-deployment.md)
- [Skill 执行说明](plugins/wx-video-account-notes/skills/wx-video-account-notes/SKILL.md)
- [仓库目录](目录说明.md) · [领域术语](CONTEXT.md) · [架构决策](docs/adr/)
- [解析原理](docs/research/wx-channels-architecture.md) · [测试与评估](plugins/wx-video-account-notes/skills/wx-video-account-notes/tests/test-cases.md) · [变更日志](CHANGELOG.md)

贡献前请阅读 [AGENTS.md](AGENTS.md)；需求与问题请提交 GitHub Issues。项目采用 [MIT 许可证](LICENSE)。
