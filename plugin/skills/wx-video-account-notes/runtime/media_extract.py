from __future__ import annotations

import math
import subprocess
from pathlib import Path


def _run(command: list[str]) -> None:
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "command failed")


def _read_output(command: list[str]) -> str:
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "command failed")
    return completed.stdout.strip()


def choose_frame_interval(duration_seconds: float) -> int:
    if duration_seconds <= 60:
        return 2
    if duration_seconds <= 180:
        return 3
    return 4


def _choose_target_frame_interval(duration_seconds: float, target_frames: int) -> int:
    if target_frames <= 0:
        raise ValueError("target_frames must be positive")
    return max(1, math.ceil(duration_seconds / target_frames))


def choose_ocr_frame_interval(duration_seconds: float, target_frames: int = 100) -> int:
    return _choose_target_frame_interval(duration_seconds, target_frames)


def choose_visual_frame_interval(duration_seconds: float, target_frames: int = 5) -> int:
    return _choose_target_frame_interval(duration_seconds, target_frames)


def build_frame_filter(seconds_per_frame: int) -> str:
    return f"fps=1/{seconds_per_frame},scale='min(1280,iw)':-2"


def build_ocr_frame_filter(seconds_per_frame: int) -> str:
    return f"fps=1/{seconds_per_frame},crop=iw:ih*0.45:0:ih*0.55,scale='min(960,iw)':-2"


def build_visual_frame_filter(seconds_per_frame: int) -> str:
    return build_frame_filter(seconds_per_frame)


def probe_duration_seconds(ffprobe_path: Path, video_path: Path) -> float:
    output = _read_output([
        str(ffprobe_path),
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ])
    return float(output)


def _clear_existing_frames(frames_dir: Path) -> None:
    for frame_path in frames_dir.glob("*.jpg"):
        frame_path.unlink()


def _extract_filtered_frames(ffmpeg_path: Path, video_path: Path, frames_dir: Path, frame_filter: str) -> list[Path]:
    frames_dir.mkdir(parents=True, exist_ok=True)
    _clear_existing_frames(frames_dir)
    output_pattern = str(frames_dir / "%03d.jpg")
    _run([
        str(ffmpeg_path),
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(video_path),
        "-vf",
        frame_filter,
        output_pattern,
    ])
    return sorted(frames_dir.glob("*.jpg"))


def extract_frames(ffmpeg_path: Path, ffprobe_path: Path, video_path: Path, frames_dir: Path) -> list[Path]:
    seconds_per_frame = choose_frame_interval(probe_duration_seconds(ffprobe_path, video_path))
    return _extract_filtered_frames(ffmpeg_path, video_path, frames_dir, build_frame_filter(seconds_per_frame))


def extract_ocr_frames(ffmpeg_path: Path, ffprobe_path: Path, video_path: Path, frames_dir: Path) -> list[Path]:
    seconds_per_frame = choose_ocr_frame_interval(probe_duration_seconds(ffprobe_path, video_path))
    return _extract_filtered_frames(ffmpeg_path, video_path, frames_dir, build_ocr_frame_filter(seconds_per_frame))


def extract_visual_frames(ffmpeg_path: Path, ffprobe_path: Path, video_path: Path, frames_dir: Path) -> list[Path]:
    seconds_per_frame = choose_visual_frame_interval(probe_duration_seconds(ffprobe_path, video_path))
    return _extract_filtered_frames(ffmpeg_path, video_path, frames_dir, build_visual_frame_filter(seconds_per_frame))


def extract_audio(ffmpeg_path: Path, video_path: Path, audio_dir: Path) -> Path:
    output_path = audio_dir / "speech.wav"
    _run([
        str(ffmpeg_path),
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        str(output_path),
    ])
    return output_path
