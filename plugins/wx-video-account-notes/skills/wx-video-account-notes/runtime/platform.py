from __future__ import annotations

import platform as host_platform
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PlatformInfo:
    id: str
    uv_archive: str
    uv_url: str
    uv_sha256: str
    uv_binary: str
    python_binary: str
    venv_python: str
    ffmpeg_binary: str
    ffprobe_binary: str


def detect_platform(system: str | None = None, machine: str | None = None) -> PlatformInfo:
    system_name = (system or host_platform.system()).lower()
    machine_name = (machine or host_platform.machine()).lower().replace("amd64", "x86_64")
    if machine_name not in {"x86_64", "x64"}:
        raise RuntimeError(
            f"Unsupported architecture: {machine_name}. Supported architecture: x64."
        )

    uv_version = "0.11.25"
    if system_name == "windows":
        archive = "uv-x86_64-pc-windows-msvc.zip"
        return PlatformInfo(
            "windows-x64",
            archive,
            f"https://releases.astral.sh/github/uv/releases/download/{uv_version}/{archive}",
            "15bfd1423b7eaa7aae949922d4712ebaac2bb44a81af64ab59bbe007090cb0d0",
            "uv.exe",
            "python.exe",
            "Scripts/python.exe",
            "ffmpeg.exe",
            "ffprobe.exe",
        )
    if system_name in {"darwin", "macos"}:
        archive = "uv-x86_64-apple-darwin.tar.gz"
        return PlatformInfo(
            "macos-x64",
            archive,
            f"https://releases.astral.sh/github/uv/releases/download/{uv_version}/{archive}",
            "65ff85b33212f75d34d7c0f0724aba9a742c74f62559f67dc0d6c543dc2fc52f",
            "uv",
            "python3.13",
            "bin/python",
            "ffmpeg",
            "ffprobe",
        )
    if system_name == "linux":
        archive = "uv-x86_64-unknown-linux-gnu.tar.gz"
        return PlatformInfo(
            "linux-x64",
            archive,
            f"https://releases.astral.sh/github/uv/releases/download/{uv_version}/{archive}",
            "1db18b5e76fa645a7f3865773139bdec8e2d46adbdbb35e7410b34fa8015ccd2",
            "uv",
            "python3.13",
            "bin/python",
            "ffmpeg",
            "ffprobe",
        )
    raise RuntimeError(
        f"Unsupported operating system: {system_name}. Supported systems: Windows, macOS, Linux."
    )


def runtime_root(skill_root: Path, info: PlatformInfo | None = None) -> Path:
    return skill_root / ".runtime" / (info or detect_platform()).id


def find_runtime_binary(root: Path, name: str) -> Path | None:
    if not root.exists():
        return None
    matches = sorted(path for path in root.rglob(name) if path.is_file())
    return matches[0] if matches else None


def find_ffmpeg_tools(runtime_root_path: Path, info: PlatformInfo | None = None) -> tuple[Path, Path]:
    current = info or detect_platform()
    tools_root = runtime_root_path / "tools" / "ffmpeg"
    ffmpeg = find_runtime_binary(tools_root, current.ffmpeg_binary)
    ffprobe = find_runtime_binary(tools_root, current.ffprobe_binary)
    if not ffmpeg or not ffprobe:
        raise RuntimeError(
            f"ffmpeg/ffprobe not found in {tools_root}. Run the platform bootstrap command first."
        )
    return ffmpeg, ffprobe
