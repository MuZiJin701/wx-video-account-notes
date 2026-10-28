# wx-video-account-notes

从微信视频号分享链接下载视频、图文图片及可用的封面和背景音乐，生成离线归档，提取 OCR/ASR 笔记材料，并由 agent 整理 Markdown 笔记。

[English README](README.en.md) · [![Tests](https://github.com/MuZiJin701/wx-video-account-notes/actions/workflows/tests.yml/badge.svg)](https://github.com/MuZiJin701/wx-video-account-notes/actions/workflows/tests.yml)

> **自部署登录方式**：维护者主动运行命令，由 Playwright 启动临时无头 Chromium，通过微信扫码取得元宝 Cookie；也可继续手动粘贴 Cookie。两种方式均先完成解析校验再替换，失败保留原文件。操作见[自部署指南](docs/resolver-deployment.md)。

## 使用效果

![在 Codex 中发送视频号分享链接并生成 Markdown 笔记](docs/images/使用过程.png)

![本地保存的视频、Markdown 笔记、参考帧与 OCR/ASR 笔记材料](docs/images/产物.png)

示例中 OCR 成功，ASR 未识别出文字；笔记会标记失败和不确定性。

## 开始使用

支持 Windows x64、macOS Intel x64 和 Linux x64。首次处理会从 GitHub Releases、Hugging Face 等来源下载项目私有的 Python、依赖、FFmpeg 和模型；需要联网和足够的磁盘空间，之后可复用。

优先复用系统中可用的 uv（最低 0.11.25）；缺失或不兼容时，沿用固定版本和校验的项目私有 uv。

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

### 更新 Skill

通过上面的 `skills add ... -g` 安装后，运行以下命令只更新这个全局 Skill：

```sh
skills update wx-video-account-notes -g
```

通过 Codex 插件市场安装后，Codex 启动时会在后台尝试刷新已配置的 Git 市场，并在发现更新时刷新插件缓存。也可以手动刷新本项目的市场并检查插件：

```sh
codex plugin marketplace upgrade wx-video-account-notes-dev
codex plugin list --marketplace wx-video-account-notes-dev
```

自动刷新依赖网络和市场配置，失败时可手动刷新；请在新会话中检查插件是否已更新。当前会话不保证立即加载新内容。

更新前请备份已安装 Skill 中自行修改的配置。通过 `cc-switch` 安装时，请使用该工具的更新方式。

默认解析服务已更新，旧版 Skill 请按上述方式更新。配置位于实际安装的 Skill 的 `runtime/resolver_config.json`，包含服务地址 `api_url` 和访问凭证 `access_key`；默认服务使用项目当前默认的访问凭证。自部署配置及环境变量说明见[自部署指南](docs/resolver-deployment.md#4-连接客户端)。

### 2. 发送分享链接

默认使用项目维护者的解析服务，无需配置服务器或凭证。把真实链接交给 agent：

```text
下载这个视频号分享链接的内容并生成笔记：
https://weixin.qq.com/sph/your_share_id_here
```

想指定输出目录，可在请求中写明，例如“把这个链接整理到 D:\notes\wx”。

### 想使用自己的服务器？

按[自部署指南](docs/resolver-deployment.md)在 Linux x64 + systemd 服务器安装。在交互式 SSH 终端运行维护命令：有效 Cookie 直接复用，缺失或明确失效才展示微信二维码；命令结束后关闭浏览器。扫码无法完成时，可使用原有的无回显手动 Cookie 更新入口。

微信扫码、完整解析和 Cookie 更新后复用已在隔离服务器验收；普通 SSH 字符二维码实扫、真实过期刷新、新账号注册和生产 systemd 生命周期仍需单独验证。扫码可能触发额外验证，没有定时登录或邮件告警。详见[验收记录与限制](docs/research/yuanbao-manual-qr-login.md#微信手动维护改造与真实验收2026-10-21)。

## 生成的文件

```text
<output-dir>/<slug>[_N]/
  <slug>.<格式>       # 视频动态，优先 H.264
  images/             # 按顺序保存的原始图片
  cover.<格式>        # 可用时
  background_music.<格式> # 可用时
  index.html          # 离线归档和失败信息
  note_materials.json # 笔记材料及下载、OCR、ASR 状态
  raw.json            # 原始解析响应，可能包含临时访问参数
  ocr.txt, asr.txt
  ocr_frames/, frames/, audio/
  <slug>.md           # 最终笔记
```

每次处理在输出目录下创建独立子目录，避免覆盖已有内容；指定输出目录时也一样。图文原图用于 OCR 和识图，视频参考帧保存在 `frames/`。单项下载失败时保留成功内容、记录失败并返回非零状态；归档仍可查看。媒体内容取决于解析服务提供的信息，不保证私密、不可访问或加密内容可下载。

## 运行方式与限制

- 服务器只解析分享链接；下载媒体、OCR、ASR 和写笔记在本机完成，不需要 GPU 或系统 FFmpeg。
- 默认服务使用公网 HTTP，分享链接和解析结果明文传输；公开 Skill 内的共用访问凭证不是秘密。服务对所有用户合计每分钟最多处理 30 次请求。
- 默认服务的元宝登录态由维护者更新；自部署使用手动 Cookie 维护：有效时复用，失效后由维护者在 SSH 终端通过微信扫码或手动粘贴更新，可配置 HTTPS 入口；没有定时登录或邮箱通知。
- 目前不支持 ARM64、GPU 推理或离线首次初始化。项目私有 Python 版本为 3.13.14，ASR 使用 CPU 上的 faster-whisper tiny。

## 本地开发

```sh
cd plugins/wx-video-account-notes/skills/wx-video-account-notes
uv sync --locked
uv run --locked python -m unittest discover -s runtime/tests
```

服务端单测从仓库根目录运行 `python3 -m unittest discover -s server`（仅用标准库）；真实初始化和端到端处理见[手动验收清单](plugins/wx-video-account-notes/skills/wx-video-account-notes/tests/test-cases.md)。

GitHub Actions 同时执行三平台单测及无凭据的 Linux Chromium 启动、JavaScript 与资料持久化检查，支持手动触发，不向 CI 上传个人凭据。[独立验收步骤](plugins/wx-video-account-notes/skills/wx-video-account-notes/tests/test-cases.md#standalone-wechat-login-check)提供微信扫码和完整解析检查；离线回归和无凭据 CI 不代表云端登录验收通过。

## 更多文档

- [自部署与故障排查](docs/resolver-deployment.md)
- [微信扫码与手动 Cookie 维护验证](docs/research/yuanbao-manual-qr-login.md) · [历史 QQ 密码与邮件实验](docs/research/yuanbao-qq-login.md)
- [Skill 执行说明](plugins/wx-video-account-notes/skills/wx-video-account-notes/SKILL.md)
- [仓库目录](目录说明.md) · [领域术语](GLOSSARY.md) · [架构决策](docs/adr/)
- [解析原理](docs/research/wx-channels-architecture.md) · [测试与评估](plugins/wx-video-account-notes/skills/wx-video-account-notes/tests/test-cases.md) · [变更日志](CHANGELOG.md)

贡献前请阅读 [AGENTS.md](AGENTS.md)；需求与问题请提交 GitHub Issues。项目采用 [MIT 许可证](LICENSE)。
