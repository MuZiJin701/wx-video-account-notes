from __future__ import annotations

import argparse
from pathlib import Path

from runtime.platform import detect_platform, find_runtime_binary, runtime_root


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-root", required=True)
    args = parser.parse_args()

    skill_root = Path(args.skill_root).resolve()
    info = detect_platform()
    root = runtime_root(skill_root, info)
    uv = find_runtime_binary(root / "uv", info.uv_binary)
    python = root / ".venv" / info.venv_python
    ffmpeg = find_runtime_binary(root / "tools" / "ffmpeg", info.ffmpeg_binary)
    ffprobe = find_runtime_binary(root / "tools" / "ffmpeg", info.ffprobe_binary)
    model = next((path for path in (root / "models" / "whisper").rglob("model.bin") if path.is_file()), None)
    print(f"[wx-video-account-notes] platform: {info.id}")
    print(f"[wx-video-account-notes] runtime: {root}")
    print(f"[wx-video-account-notes] private-uv: {bool(uv)}")
    print(f"[wx-video-account-notes] venv-python: {python.is_file()}")
    print(f"[wx-video-account-notes] ffmpeg: {bool(ffmpeg and ffprobe)}")
    print(f"[wx-video-account-notes] whisper-model: {bool(model)}")
    return 0 if uv and python.is_file() and ffmpeg and ffprobe and model else 1


if __name__ == "__main__":
    raise SystemExit(main())
