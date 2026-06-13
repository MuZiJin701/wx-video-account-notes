from __future__ import annotations

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


def build_frame_filter(seconds_per_frame: int) -> str:
    return f"fps=1/{seconds_per_frame},scale='min(1280,iw)':-2"


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


def extract_frames(ffmpeg_path: Path, ffprobe_path: Path, video_path: Path, frames_dir: Path) -> list[Path]:
    seconds_per_frame = choose_frame_interval(probe_duration_seconds(ffprobe_path, video_path))
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
        build_frame_filter(seconds_per_frame),
        output_pattern,
    ])
    return sorted(frames_dir.glob("*.jpg"))


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
