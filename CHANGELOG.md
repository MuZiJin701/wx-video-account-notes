# Changelog

## Unreleased

- Added cross-platform runtime support for Windows x64, Intel macOS x64, and Linux x64.
- Unified runtime initialization, asset verification, and media processing under Python.
- Added platform-isolated runtimes, SHA256 verification, runtime checks, and three-platform CI.
- Split the README into concise Chinese and English entry points.
- Updated documentation to use one primary language per file and corrected the global `skills` CLI command.

## 0.2.3

- Removed Claude Code distribution metadata and kept the Codex plugin entry point.
- Made repository-level global `skills` installation the primary installation path while retaining Codex marketplace and `cc-switch` options.
- Improved OCR performance by bypassing temporary disk I/O, caching JPEG decoding, reducing crop candidates from five to three, and reducing the ANA06rMHMf benchmark from 204s to 142s.
- Reduced OCR preprocessing upscale from 2x to 1.5x, reducing ANA06rMHMf from 142s to 133s.
- Relaxed OCR crop early exit from five to four Chinese characters, reducing ANA06rMHMf from 132s to 111s and case2 from 17.4s to 16.3s without materially changing CPU usage.
- Made ASR concurrency adaptive: `cpu_threads=cpu_count//2`, with one worker on low-core machines and two workers on machines with at least four cores.
- Removed ineffective `OMP_NUM_THREADS`/`OMP_WAIT_POLICY` code and the permanently empty `low_signal_exact` filter branch.
- Removed the unused `resolved["raw"]` payload reference.
- Improved the missing-FFmpeg error to point users to bootstrap.
- Added unit coverage for `visual_frames`.
- Removed the duplicate `.runtime/python/` installation (about 75 MB).
- Added `.gitignore` and real test links in `evals.json`.

## 0.2.2

- Added up to five evenly sampled `visual_frames` to `note_materials.json` for videos without speech.
- Removed dead GPU parameters, the empty noise filter, and unused function parameters.
- Removed leftover `.runtime/models/sensevoice/` assets.
- Updated README, repository map, test cases, skill instructions, and note template.

## 0.2.1

- Switched ASR from SenseVoice to faster-whisper tiny for more reliable cross-video behavior.
- Removed `NEXT_STEP.md` generation because the instructions duplicated `SKILL.md`.
- Added `cpu_threads` and `num_workers` to improve CPU utilization.
- Synchronized all documentation with the new workflow.

## 0.2.0

- Tried and dropped SenseVoice CPU because only one of three videos succeeded.
- Kept faster-whisper and removed all GPU-related code, including CUDA detection, DLL injection, and NVIDIA runtime assets.
- Removed `-IncludeOptionalGpu`, `-PruneOptionalGpu`, `-AsrDevice`, and `-AsrProvider` options.
- Optimized OCR with frame skipping, crop early exit, and full-frame bypass.
- Added automatic CPU thread detection for ASR.
- Made bootstrap remove its cache after completion.
- Simplified `bootstrap.py`, `pipeline.py`, and `invoke_pipeline.ps1`.
- Reduced skill runtime size from about 1.3 GB to about 700 MB, excluding FFmpeg.
- Rewrote all tests (35 cases).

## 0.1.1

- Shortened the skill documentation and made `SKILL.md` the primary execution guide.
- Reduced overlap among README, repository map, and note template.
- Shortened generated next-step instructions.
- Updated test cases for the materials-plus-agent-note workflow.
- Documented runtime slimming, optional GPU assets, and rebuildable caches.

## 0.1.0

- Added a portable, Windows-first skill scaffold.
- Added a project-local `.runtime` environment using uv and venv.
- Added WeChat Channels link resolution, download, OCR, ASR, and Markdown note processing.
