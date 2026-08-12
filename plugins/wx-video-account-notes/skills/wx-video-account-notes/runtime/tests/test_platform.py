from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime.platform import detect_platform, find_ffmpeg_tools, runtime_root


class PlatformContractTests(unittest.TestCase):
    def test_detects_supported_x64_platforms(self) -> None:
        self.assertEqual(detect_platform("Windows", "AMD64").id, "windows-x64")
        self.assertEqual(detect_platform("Darwin", "x86_64").id, "macos-x64")
        self.assertEqual(detect_platform("Linux", "x86_64").id, "linux-x64")

    def test_rejects_unsupported_platforms(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "Supported architecture: x64"):
            detect_platform("Linux", "aarch64")
        with self.assertRaisesRegex(RuntimeError, "Supported systems: Windows, macOS, Linux"):
            detect_platform("FreeBSD", "x86_64")

    def test_runtime_root_isolated_by_platform(self) -> None:
        skill_root = Path("skill")
        self.assertEqual(runtime_root(skill_root, detect_platform("Windows", "x86_64")), skill_root / ".runtime" / "windows-x64")
        self.assertEqual(runtime_root(skill_root, detect_platform("Linux", "x86_64")), skill_root / ".runtime" / "linux-x64")

    def test_finds_platform_named_ffmpeg_tools(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tools = root / "tools" / "ffmpeg" / "bin"
            tools.mkdir(parents=True)
            (tools / "ffmpeg").write_text("", encoding="utf-8")
            (tools / "ffprobe").write_text("", encoding="utf-8")

            ffmpeg, ffprobe = find_ffmpeg_tools(root, detect_platform("Linux", "x86_64"))

            self.assertEqual(ffmpeg, tools / "ffmpeg")
            self.assertEqual(ffprobe, tools / "ffprobe")


if __name__ == "__main__":
    unittest.main()
