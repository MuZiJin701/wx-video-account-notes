# OCR / ASR Evaluation

## Current Stack

| 组件 | Provider | 模型 | 配置 |
|---|---|---|---|
| OCR | RapidOCR | onnxruntime CPU | 1.5x upscale, 4-char crop early exit |
| ASR | faster-whisper | tiny (150MB) | CPU-only, adaptive `cpu_threads` + `num_workers` |

## OCR Optimizations

| 优化 | 说明 |
|---|---|
| 跳过无变化帧 | 像素比对字幕区域，不变则复用 |
| 裁切区提前退出 | 任一候选区 ≥4 中文字符即停止 |
| 跳过全帧 OCR | 裁切区有好结果时不再跑整帧 |

## ASR

- 模型：`Systran/faster-whisper-tiny`
- 底层运行时：CTranslate2 (int8 量化)
- 输出：按 segment 分段，无标点
- 特点：所有测试视频均可靠产出文本，从不空白

## History

| Date | Change |
|---|---|
| 2026-06-12 | 初始：faster-whisper tiny + GPU |
| 2026-06-12 | 试验：SenseVoice GPU → 放弃（CUDA 不匹配） |
| 2026-06-12 | 切到 SenseVoice CPU → 2/3 视频失败 |
| 2026-06-12 | 回退 faster-whisper CPU → 3/3 稳定 |
| 2026-06-12 | OCR 优化：跳帧+提前退出+跳过全帧 |
| 2026-06-12 | ASR 优化：cpu_threads + num_workers |
| 2026-06-13 | OCR 优化：去磁盘 I/O、单次解码复用、3 个 crop、1.5x 放大、4 字提前退出 |
| 2026-06-13 | ASR 默认并发改为自适应策略 |
