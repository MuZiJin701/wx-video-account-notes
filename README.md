# wx-video-account-notes

从微信视频号分享链接下载视频或图文图片，提取 OCR/ASR 笔记材料，并由 agent 生成 Markdown 笔记。

[English README](README.en.md) · [![Tests](https://github.com/MuZiJin701/wx-video-account-notes/actions/workflows/tests.yml/badge.svg)](https://github.com/MuZiJin701/wx-video-account-notes/actions/workflows/tests.yml)

> **Playwright 登录方案探索已暂停（2026-10-20）**：`codex/explore-qq-yuanbao-login` 保留 QQ 账号密码登录元宝和 QQ 邮箱的实验代码、诊断与研究记录，未通过完整云端登录验收，未合入 `main`。2026-10-21 补充的[纯 HTTP 账号预检查](docs/research/yuanbao-qq-login.md#纯-http-账号预检查2026-10-21)中，两个入口在本机免验证码、阿里云仍要求验证码，未提交密码或验证完整登录。恢复浏览器探索需用户明确要求；当前发布功能与部署方式以 [`main`](https://github.com/MuZiJin701/wx-video-account-notes/tree/main) 为准。

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

### 2. 发送分享链接

默认使用项目维护者的解析服务，无需配置服务器或凭证。把真实链接交给 agent：

```text
下载这个视频号分享链接的内容并生成笔记：
https://weixin.qq.com/sph/your_share_id_here
```

想指定输出目录，可在请求中写明，例如“把这个链接整理到 D:\notes\wx”。

### 想使用自己的服务器？

当前请使用 [`main` 的自部署指南](https://github.com/MuZiJin701/wx-video-account-notes/blob/main/docs/resolver-deployment.md)，手动维护元宝 Cookie。本分支中的账号密码登录、每日维护和 QQ 邮箱告警均为已暂停的实验功能；[本分支指南](docs/resolver-deployment.md)保留历史检查和部署草案，暂停期间不执行。

暂停时已知：阿里云直连下两项登录均要求图片点选验证码，有头/无头模式都触发；元宝单题已有 agent 识图、程序点击通过的样本，但邮箱验证码和完整云端登录均未通过，通用识图未集成。网络出口是证据最强的影响因素，腾讯具体命中规则仍未知。CI 和 `BROWSER_SMOKE_OK` 不代表真实登录成功。详见[暂停状态与研究记录](docs/research/yuanbao-qq-login.md#探索暂停与分支隔离2026-10-20)。

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
- 默认服务的元宝登录态由维护者更新；`main` 的自部署由用户手动维护 Cookie，可配置 HTTPS 入口。本分支的自动维护和邮箱告警尚未验收，探索已暂停。
- 目前不支持 ARM64、GPU 推理或离线首次初始化。项目私有 Python 版本为 3.13.14，ASR 使用 CPU 上的 faster-whisper tiny。

## 本地开发

```sh
cd plugins/wx-video-account-notes/skills/wx-video-account-notes
uv sync --locked
uv run --locked python -m unittest discover -s runtime/tests
```

服务端单测从仓库根目录运行 `python3 -m unittest discover -s server`（仅用标准库）；真实初始化和端到端处理见[手动验收清单](plugins/wx-video-account-notes/skills/wx-video-account-notes/tests/test-cases.md)。

GitHub Actions 同时执行三平台单测及无凭据的 Linux Chromium 启动、JavaScript 与资料持久化检查，支持手动触发，不向 CI 上传个人凭据。[历史验收步骤](docs/resolver-deployment.md#0-先验收开发分支)保留独立登录入口；暂停期间不执行真实登录、发信或实验部署。离线回归和无凭据 CI 不代表云端登录验收通过。

## 更多文档

- [自部署与故障排查](docs/resolver-deployment.md)
- [QQ 密码登录、Cookie 维护与邮件通知验证](docs/research/yuanbao-qq-login.md)
- [Skill 执行说明](plugins/wx-video-account-notes/skills/wx-video-account-notes/SKILL.md)
- [仓库目录](目录说明.md) · [领域术语](GLOSSARY.md) · [架构决策](docs/adr/)
- [解析原理](docs/research/wx-channels-architecture.md) · [测试与评估](plugins/wx-video-account-notes/skills/wx-video-account-notes/tests/test-cases.md) · [变更日志](CHANGELOG.md)

贡献前请阅读 [AGENTS.md](AGENTS.md)；需求与问题请提交 GitHub Issues。项目采用 [MIT 许可证](LICENSE)。
