---
name: wx-video-account-notes
description: 处理微信视频号分享链接，例如 https://weixin.qq.com/sph/... 。当用户提供视频号分享链接，并要求解析链接、下载视频或图文动态图片、提取 OCR 或 ASR、整理结构化材料、或输出与媒体同目录的 Markdown 笔记时，务必使用这个 skill。
---

# 微信视频号下载与笔记整理

## 触发条件

仅在用户提供 `https://weixin.qq.com/sph/...` 视频号分享链接，并要求继续处理时使用。

## 输入

- 必需：一个视频号分享链接
- 可选：输出目录
- 可选：期望标题或文件名

## 固定流程

1. 先运行：`pwsh -File "scripts/bootstrap.ps1"`
2. 再运行：`pwsh -File "scripts/invoke_pipeline.ps1" -ShareUrl "https://weixin.qq.com/sph/..."`
3. pipeline 负责下载视频或图文动态图片、抽帧、OCR、ASR，生成 `note_materials.json`
4. 当前 agent / model 基于 `note_materials.json` 写最终 `<slug>.md`
5. 如果用户明确说不要笔记，跳过最终 `<slug>.md`

## 固定输出

输出目录中应包含：

```text
<output-dir>/
  <slug>.mp4        # 视频动态才有
  note_materials.json
  raw.json
  ocr.txt
  asr.txt
  ocr_frames/
  frames/
  audio/
```

默认情况下，当前 agent / model 还应写出：

```text
<output-dir>/
  <slug>.md
```

如果用户明确说不要笔记，跳过该文件。

## 成稿规则

- 以 `note_materials.json` 为主
- 必要时对照 `raw.json`、`ocr.txt`、`asr.txt`
- 参考 `resources/model-note-template.md`
- 不要编造提取结果中不存在的信息
- 如果 `note_materials.json` 包含 `visual_frames` 字段，说明 pipeline 提供了少量视觉参考帧；如果当前模型有识图能力，必须读取 `visual_frames` 对应图片辅助理解视频内容，再综合图片信息写笔记
- 对图文动态，`visual_frames` 是原始图片素材；如果当前模型有识图能力，必须读取这些图片补充 OCR 无法表达的版式、界面、图表或视觉上下文

## 失败处理

- 如果自举失败，停止并明确说明失败的资产或命令
- 如果 OCR 或 ASR 失败，在材料和最终 Markdown 中明确标记失败
- 不要把失败结果伪装成成功

## 实施要求

- 优先使用 skill 目录下的 `.runtime` 环境，不依赖系统 PATH
- 低层下载、抽帧、抽音频、OCR、ASR 由脚本和 Python 完成
- 视频动态中，`ocr_frames/` 存放 ffmpeg 直接裁出的字幕区域小图，供 OCR 使用；`frames/` 只保留少量完整参考帧，供 `visual_frames` 使用
- 图文动态中，`frames/` 存放下载到的原始图片，供 OCR 和 `visual_frames` 使用；该类动态跳过 ASR
- 当前 agent / model 只负责基于材料整理最终 `<slug>.md`
