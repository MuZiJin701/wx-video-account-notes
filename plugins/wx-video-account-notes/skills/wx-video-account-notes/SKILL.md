---
name: wx-video-account-notes
description: 处理微信视频号分享链接，提取 OCR/ASR 笔记材料并生成 Markdown 笔记。 Process WeChat Channels share links into OCR/ASR note materials and Markdown notes.
---

# 微信视频号下载与笔记整理

处理一个视频号分享链接，生成可供 agent 继续整理的结构化笔记材料。

## 触发条件

仅在用户提供 `https://weixin.qq.com/sph/...` 视频号分享链接，并要求继续处理时使用。

## 输入

- 必需：一个视频号分享链接
- 可选：输出目录
- 可选：期望标题或文件名

## 固定流程

1. Windows 运行 `pwsh -File "scripts/bootstrap.ps1"`；macOS/Linux 运行 `sh scripts/bootstrap.sh`。
2. Windows 运行 `pwsh -File "scripts/invoke_pipeline.ps1" -ShareUrl "https://weixin.qq.com/sph/..."`；macOS/Linux 运行 `sh scripts/invoke_pipeline.sh --share-url "https://weixin.qq.com/sph/..."`。
3. pipeline 负责下载视频或图文动态图片、抽帧、OCR、ASR，生成 `note_materials.json`。
4. 当前 agent / model 基于 `note_materials.json` 写最终 `<slug>.md`。
5. 如果用户明确说不要笔记，跳过最终 `<slug>.md`。

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

默认情况下，当前 agent / model 还应写出同目录的 `<slug>.md`。如果用户明确说不要笔记，跳过该文件。

## 成稿规则

- 以 `note_materials.json` 为主。
- 必要时对照 `raw.json`、`ocr.txt`、`asr.txt`。
- 参考 `resources/model-note-template.md`。
- 不要编造提取结果中不存在的信息。
- 如果 `note_materials.json` 包含 `visual_frames` 字段，且当前模型有识图能力，必须读取 `visual_frames` 对应图片辅助理解视频内容。
- 对图文动态，`visual_frames` 是原始图片素材；如果当前模型有识图能力，必须读取这些图片补充 OCR 无法表达的版式、界面、图表或视觉上下文。

## 失败处理

- 如果自举失败，停止并明确说明失败的资产或命令。
- 如果解析失败，按凭证不匹配、登录态问题、服务不可达或媒体动态不可用的错误提示处理；需要所选服务的维护者操作时明确告知。
- 如果 OCR 或 ASR 失败，在材料和最终 Markdown 中明确标记失败。
- 不要把失败结果伪装成成功。

## 实施要求

- 优先使用 skill 目录下当前平台的 `.runtime/<os>-<arch>/` 环境，不依赖系统 PATH。
- 低层下载、抽帧、抽音频、OCR、ASR 由脚本和 Python 完成。
- 视频动态中，`ocr_frames/` 存放 ffmpeg 直接裁出的字幕区域小图；`frames/` 只保留少量完整参考帧，供 `visual_frames` 使用。
- 图文动态中，`frames/` 存放下载到的原始图片，供 OCR 和 `visual_frames` 使用；该类动态跳过 ASR。
- 当前 agent / model 只负责基于材料整理最终 `<slug>.md`。
- 默认使用维护者的公网 HTTP 解析服务；仅在用户配置 `WX_VIDEO_ACCOUNT_RESOLVE_API` 和 `WX_VIDEO_ACCOUNT_RESOLVE_KEY` 后改用自部署服务，失败时不自动回退。两种方式的元宝 Cookie 均由所选服务的维护者在服务器保存，不得写入笔记材料或仓库。
- 默认服务经公网 HTTP 明文传输分享链接和解析响应；其共用访问凭证随 Skill 分发，不具备保密性。自部署服务若也使用 HTTP，具有相同的明文传输风险。
