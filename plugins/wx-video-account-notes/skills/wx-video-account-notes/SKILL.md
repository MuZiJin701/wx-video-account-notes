---
name: wx-video-account-notes
description: 根据微信视频号分享链接下载视频或图文图片，提取 OCR/ASR 笔记材料并生成 Markdown 笔记。 Download WeChat Channels videos or image posts from share links, extract OCR/ASR note materials, and write Markdown notes.
---

# 微信视频号下载与笔记整理

仅在用户提供 `https://weixin.qq.com/sph/...` 视频号分享链接并要求处理时使用；可指定输出目录、标题或文件名。

## 固定流程

1. Windows 运行 `pwsh -File "scripts/bootstrap.ps1"`；macOS/Linux 运行 `sh scripts/bootstrap.sh`。
2. Windows 运行 `pwsh -File "scripts/invoke_pipeline.ps1" -ShareUrl "https://weixin.qq.com/sph/..."`；macOS/Linux 运行 `sh scripts/invoke_pipeline.sh --share-url "https://weixin.qq.com/sph/..."`。
3. 检查 pipeline 生成的 `note_materials.json` 及处理状态；下载、抽帧、OCR、ASR 由脚本和 Python 完成。
4. 根据下述成稿规则写同目录 `<slug>.md`；用户明确不要笔记时跳过。

## 输出约定

```text
<output-dir>/
  <slug>.mp4        # 仅视频动态
  note_materials.json
  raw.json
  ocr.txt
  asr.txt
  ocr_frames/
  frames/
  audio/
```

视频动态包含视频、音频和字幕裁切图；图文动态把原始图片写入 `frames/`，跳过 ASR，`asr.txt` 为空。

## 成稿规则

- 以 `note_materials.json` 为主，必要时核对 `raw.json`、`ocr.txt`、`asr.txt`；按 [成稿模板](resources/model-note-template.md) 整理，只写材料支持的内容。
- 如果当前模型有识图能力，且材料包含 `visual_frames`，必须读取 `visual_frames` 对应图片（视频参考帧或图文原图），补充 OCR/ASR 无法表达的视觉上下文。

## 失败处理

- 如果自举失败，停止并明确说明失败的资产或命令。
- 如果解析失败，按凭证不匹配、登录态问题、服务不可达或媒体动态不可用的错误提示处理；需要所选服务的维护者操作时明确告知。
- OCR/ASR 失败在材料和最终 Markdown 中明确标记，不得伪装成功。

## 实施要求

- 优先使用 skill 目录下当前平台的 `.runtime/<os>-<arch>/` 环境，不依赖系统 PATH。
- 默认使用维护者的公网 HTTP 解析服务；仅在用户配置 `WX_VIDEO_ACCOUNT_RESOLVE_API` 和 `WX_VIDEO_ACCOUNT_RESOLVE_KEY` 后改用自部署服务，失败时不自动回退。两种方式的元宝 Cookie 均由所选服务的维护者在服务器保存，不得写入笔记材料或仓库。
- 默认服务经公网 HTTP 明文传输分享链接和解析响应；其共用访问凭证随 Skill 分发，不具备保密性。自部署服务若也使用 HTTP，具有相同的明文传输风险。
