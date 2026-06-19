# 更新日志

## 0.2.3

- 删除 Claude Code 插件分发元数据，保留 Codex 插件入口
- README 和目录说明改为推荐使用 Vercel Labs `skills` CLI 安装、更新和移除 skill
- OCR 性能优化：绕过临时文件磁盘 I/O + JPEG 解码缓存 + 裁切候选 5→3 个，ANA06rMHMf 基准 204s→142s（-30%）
- OCR 预处理放大倍数从 2x 调整到 1.5x，ANA06rMHMf 进一步从 142s→133s（再降约 6%）
- OCR 裁切提前退出阈值从 5 个中文字符放宽到 4 个，ANA06rMHMf 从 132s→111s、case2 从 17.4s→16.3s，CPU 占用基本不变
- ASR 默认并发策略改为按 CPU 数量自适应分配：`cpu_threads=cpu_count//2`、`num_workers` 在低核机器用 1，高于等于 4 核机器用 2，避免默认占满整机
- 清理 `OMP_NUM_THREADS`/`OMP_WAIT_POLICY` 死代码（实测对 onnxruntime 无效果）
- 清理 `low_signal_exact` 永远为空的噪声过滤分支
- 删除 `resolved["raw"]` 未使用的完整 payload 引用
- 改进 ffmpeg 未找到时的错误提示（明确提示运行 bootstrap）
- 添加 `visual_frames` 单测覆盖
- 删除重复的 `.runtime/python/` 旧版安装（~75MB）
- 新增 `.gitignore`，evals.json 使用真实测试链接，CHANGELOG 全中文化

## 0.2.2

- 无语音视频支持视觉帧：`note_materials.json` 自动嵌入最多 5 个均匀采样帧供 agent 看图理解
- 清理死代码：移除 GPU 参数、空噪声过滤器、无用函数参数
- 删除残留的 `.runtime/models/sensevoice/` 运行时数据
- 更新文档：README、目录说明、test-cases、SKILL、model-note-template

## 0.2.1

- ASR 从 SenseVoice 切换为 faster-whisper tiny（跨视频更稳定可靠）
- 删除 NEXT_STEP.md 生成（与 SKILL.md 指令重复）
- 添加 faster-whisper `cpu_threads` 和 `num_workers` 参数提升 CPU 利用率
- 同步更新所有文档

## 0.2.0

- SenseVoice CPU（sherpa-onnx）尝试并放弃：3 个视频仅 1 个成功，不稳定
- 保留 faster-whisper 并删除全部 GPU 相关代码：CUDA 检测、DLL 注入、NVIDIA 运行时资产
- 删除 `-IncludeOptionalGpu` / `-PruneOptionalGpu` bootstrap 参数
- 删除 `-AsrDevice` / `-AsrProvider` pipeline 参数
- OCR 优化：跳帧（像素比对）、裁切候选提前退出、跳过全帧 OCR
- ASR `num_threads` 自动检测 CPU 核心数
- Bootstrap 完成后自动删除缓存
- 简化 bootstrap.py、pipeline.py、invoke_pipeline.ps1
- Skill 运行时体积：~1.3GB → ~700MB（不含 ffmpeg）
- 全部测试重写（35 项）

## 0.1.1

- 精简 skill 文档，SKILL.md 成为最小执行真源
- 减少 README.md、目录说明.md、model-note-template.md 之间的重叠
- 缩短生成的 NEXT_STEP.md 指令
- 更新测试用例文档以匹配"材料 + agent 整理笔记"工作流
- 添加运行时瘦身控制和可选 GPU 资产、可重建缓存的文档

## 0.1.0

- Windows 优先的可移植 skill 脚手架
- 基于 uv 和 venv 的私有运行时自举
- 微信视频号解析、下载、OCR、ASR、Markdown 笔记流水线
