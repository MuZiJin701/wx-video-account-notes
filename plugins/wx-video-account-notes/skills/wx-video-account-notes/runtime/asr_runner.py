from __future__ import annotations

import os
from pathlib import Path


def resolve_asr_model_dir(runtime_root: Path, provider: str) -> Path:
    if provider.lower() == "faster-whisper":
        return next((runtime_root / "models" / "whisper").glob("**/config.json")).parent
    raise ValueError(f"Unsupported ASR provider: {provider}")


def resolve_asr_runtime(cpu_count: int | None = None) -> tuple[int, int]:
    detected_cpu_count = max(1, cpu_count or os.cpu_count() or 1)
    cpu_threads = max(2, detected_cpu_count // 2)
    num_workers = 2 if detected_cpu_count >= 4 else 1
    return cpu_threads, num_workers


def run_asr(audio_path: Path, model_dir: Path, provider: str = "faster-whisper") -> str:
    if provider.lower() != "faster-whisper":
        raise ValueError(f"Unsupported ASR provider: {provider}")

    from faster_whisper import WhisperModel

    cpu_threads, num_workers = resolve_asr_runtime()

    model = WhisperModel(
        str(model_dir),
        device="cpu",
        compute_type="int8",
        cpu_threads=cpu_threads,
        num_workers=num_workers,
    )
    segments, _ = model.transcribe(str(audio_path), language="zh")
    return "\n".join(seg.text.strip() for seg in segments if seg.text.strip())
