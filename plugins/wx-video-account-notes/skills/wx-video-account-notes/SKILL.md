---
name: wx-video-account-notes
description: 根据微信视频号分享链接下载视频或图文图片，提取 OCR/ASR 笔记材料并生成 Markdown 笔记。 Download WeChat Channels videos or image posts from share links, extract OCR/ASR note materials, and write Markdown notes.
---

# 微信视频号下载与笔记整理

仅在用户提供 `https://weixin.qq.com/sph/...` 视频号分享链接并要求处理时使用；可指定输出目录、标题或文件名。

## 固定流程

1. Windows 运行 `pwsh -File "scripts/bootstrap.ps1"`；macOS/Linux 运行 `sh scripts/bootstrap.sh`。
2. Windows 运行 `pwsh -File "scripts/invoke_pipeline.ps1" -ShareUrl "https://weixin.qq.com/sph/..."`；macOS/Linux 运行 `sh scripts/invoke_pipeline.sh --share-url "https://weixin.qq.com/sph/..."`。
3. 从 pipeline 输出的 `output:` 路径检查 `note_materials.json` 和 `index.html`；即使命令因部分下载失败返回非零，也检查已生成的归档及处理状态。
4. 根据下述成稿规则写同目录 `<slug>.md`；用户明确不要笔记时跳过。

## 输出约定

```text
<output-dir>/<slug>[_N]/
  <slug>.<格式>      # 视频动态
  images/            # 原始图片
  cover.<格式>       # 可用时
  background_music.<格式> # 可用时
  index.html         # 离线归档及失败状态
  note_materials.json
  raw.json
  ocr.txt
  asr.txt
  ocr_frames/
  frames/            # 视频参考帧
  audio/
```

每次创建独立目录；指定输出目录时也在其下创建子目录。图文动态的原图供 OCR 和识图使用；图文无语音转写。原始响应可能含临时媒体访问参数，分享前应检查。

## 成稿规则

- 以 `note_materials.json` 为主，必要时核对 `raw.json`、`ocr.txt`、`asr.txt`；按 [成稿模板](resources/model-note-template.md) 整理，只写材料支持的内容。
- 如果当前模型有识图能力，且材料包含 `visual_frames`，必须读取 `visual_frames` 对应图片（视频参考帧或图文原图），补充 OCR/ASR 无法表达的视觉上下文。

## 失败处理

- 如果自举失败，停止并明确说明失败的资产或命令。
- 如果解析失败，按凭证不匹配、登录态问题、服务不可达或媒体动态不可用的错误提示处理；需要所选服务的维护者操作时明确告知。
- 下载、OCR 或 ASR 失败在材料和最终 Markdown 中明确标记；保留已成功的媒体并说明不完整。

## 实施要求

- 优先使用 skill 目录下当前平台的 `.runtime/<os>-<arch>/` 环境，不依赖系统 PATH。
- 从 `runtime/resolver_config.json` 读取服务地址和访问凭证；随包配置指向维护者的公网 HTTP 服务，自部署时修改 `api_url` 和 `access_key`。已有的 `WX_VIDEO_ACCOUNT_RESOLVE_API` 和 `WX_VIDEO_ACCOUNT_RESOLVE_KEY` 必须成对设置，会优先覆盖文件配置。解析失败不自动回退。元宝 Cookie 只由所选服务的维护者保存在服务器，不得写入笔记材料或仓库；私有配置不得提交或公开。
- 默认服务经公网 HTTP 明文传输分享链接和解析响应；其共用访问凭证随 Skill 分发，不具备保密性。自部署服务若也使用 HTTP，具有相同的明文传输风险。
