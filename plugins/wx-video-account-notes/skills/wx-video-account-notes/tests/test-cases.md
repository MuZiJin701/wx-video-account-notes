# Manual smoke test checklist | 手动 smoke test 清单

本文件是发布前的人工 smoke test 清单，不是 `unittest` 自动测试入口。自动测试使用锁定的 uv 环境运行，且不访问外部下载服务。

## 前置条件

- 在 Windows x64、macOS Intel x64 或 Linux x64 上执行。
- 当前系统可访问视频号解析接口、GitHub Releases 和 Hugging Face。
- 使用全新 skill 目录，或先备份并删除对应平台的 `.runtime/<os>-<arch>/`。

## Cases

1. 视频动态默认输出目录：使用 `https://weixin.qq.com/sph/AybwTXRwkt`，确认输出包含 `<slug>.mp4`、`note_materials.json`、`raw.json`、`ocr.txt`、`asr.txt`、`ocr_frames/`、`frames/` 和 `audio/`；确认 `note_materials.json` 包含 `visual_frames`。
2. 图文动态默认输出目录：使用 `https://weixin.qq.com/sph/AeGgo9k3KL`，确认图片写入 `frames/`，跳过视频、音频和 ASR，生成空 `asr.txt`，并标记 `图文动态无音频`。
3. 指定输出目录：确认所有笔记材料写入用户指定目录，并可供 agent 生成同目录最终 `<slug>.md`。
4. 首次 bootstrap：确认创建当前平台的 `.runtime/<os>-<arch>/`，下载并校验私有 uv、Python、FFmpeg 和模型，然后完成锁定依赖同步。
5. 重复 bootstrap：确认已完成且校验通过的资产会复用，不重复下载；不同平台目录互不复用。
6. 失败恢复：模拟资产下载、校验或解压失败，确认命令返回非零状态、错误包含资产名称、`.tmp` 文件被清理，已完成资产保留，且不报告初始化成功。
7. 不支持平台：在不支持的 OS 或架构上执行，确认命令直接失败，并显示检测到的 OS/架构及支持范围。

## Record

记录执行日期、平台、架构、Python 版本、bootstrap 结果、pipeline 结果和失败日志摘要；不要提交下载的运行时资产、用户媒体或敏感日志。
