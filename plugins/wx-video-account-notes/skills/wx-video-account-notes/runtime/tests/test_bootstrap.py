from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime.bootstrap import (
    prune_runtime_cache,
    select_assets,
)


class BootstrapTests(unittest.TestCase):
    def test_select_assets_returns_all_required_assets(self) -> None:
        manifest_assets = [
            {
                "name": "ffmpeg",
                "required": True,
                "install_policy": "required",
                "urls": ["https://example.invalid/ffmpeg.zip"],
                "archive_name": "ffmpeg.zip",
                "extract": True,
                "expected_glob": "**/bin/ffmpeg.exe",
            },
            {
                "name": "whisper-tiny",
                "required": True,
                "install_policy": "required",
                "repo_id": "Systran/faster-whisper-tiny",
                "archive_name": "faster-whisper-tiny",
                "expected_glob": "**/config.json",
            },
        ]

        selected = select_assets(manifest_assets)

        self.assertEqual(len(selected), 2)
        self.assertEqual(selected[0]["name"], "ffmpeg")
        self.assertEqual(selected[1]["name"], "whisper-tiny")

    def test_select_assets_skips_non_required_policy(self) -> None:
        manifest_assets = [
            {"name": "ffmpeg", "required": True, "install_policy": "required"},
            {"name": "whisper-tiny", "required": True, "install_policy": "required"},
            {
                "name": "optional-asset",
                "required": False,
                "install_policy": "optional-gpu",
            },
        ]

        selected = select_assets(manifest_assets)

        self.assertEqual([a["name"] for a in selected], ["ffmpeg", "whisper-tiny"])

    def test_prune_runtime_cache_removes_cache_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_root = Path(temp_dir)
            cache_root = runtime_root / "cache"
            cache_root.mkdir(parents=True)
            (cache_root / "asset.bin").write_text("x", encoding="utf-8")

            prune_runtime_cache(runtime_root)

            self.assertFalse(cache_root.exists())

    def test_bootstrap_script_sets_pythonpath_before_running_runtime_bootstrap(self) -> None:
        script_path = Path(__file__).resolve().parents[2] / "scripts" / "bootstrap.ps1"
        script_text = script_path.read_text(encoding="utf-8")

        self.assertIn('$env:PYTHONPATH = $skillRoot', script_text)


if __name__ == "__main__":
    unittest.main()
