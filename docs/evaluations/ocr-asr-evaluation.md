# OCR / ASR evaluation

June 2026 evaluation record: stack choices, optimizations, and sample observations. These results do not guarantee transcription quality for other media; see the [later acceptance record](../../plugins/wx-video-account-notes/skills/wx-video-account-notes/tests/test-cases.md#record).

## Evaluated stack

| Component | Provider | Model | Configuration |
| --- | --- | --- | --- |
| OCR | RapidOCR | onnxruntime CPU | 1.5x upscale, 4-character crop early exit |
| ASR | faster-whisper | tiny (150 MB) | CPU-only, adaptive `cpu_threads` and `num_workers` |

## OCR optimizations

| Optimization | Description |
| --- | --- |
| Skip unchanged frames | Compare subtitle-region pixels and reuse the previous result when unchanged. |
| Crop early exit | Stop when any candidate crop reaches at least four Chinese characters. |
| Skip full-frame OCR | Do not run full-frame OCR when a crop already produced a good result. |

## ASR

- Model: `Systran/faster-whisper-tiny`
- Runtime: CTranslate2 with int8 quantization
- Output: segment-based text without punctuation
- Sample result: all three videos in the June evaluation produced non-empty text; this measures availability, not accuracy.

## History

| Date | Change |
| --- | --- |
| 2026-06-12 | Started with faster-whisper tiny plus GPU. |
| 2026-06-12 | Tried SenseVoice GPU and dropped it because of CUDA mismatch. |
| 2026-06-12 | Tried SenseVoice CPU; 2 of 3 videos failed. |
| 2026-06-12 | Returned to faster-whisper CPU; 3 of 3 videos were stable. |
| 2026-06-12 | Added OCR frame skipping, early exit, and full-frame bypass. |
| 2026-06-12 | Added adaptive ASR `cpu_threads` and `num_workers`. |
| 2026-06-13 | Optimized OCR with no disk I/O, shared decode, three crops, 1.5x upscale, and four-character early exit. |
| 2026-06-13 | Changed default ASR concurrency to an adaptive strategy. |
