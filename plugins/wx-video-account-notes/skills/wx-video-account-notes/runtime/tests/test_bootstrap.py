from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime.bootstrap import (
    download_file,
    prune_runtime_cache,
    select_platform_asset,
    select_assets,
)


class BootstrapTests(unittest.TestCase):
    def test_download_file_replaces_destination_only_after_checksum_passes(self) -> None:
        class Response:
            headers = {"content-length": "3"}

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def raise_for_status(self) -> None:
                return None

            def iter_bytes(self):
                yield b"abc"

        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "asset.bin"
            expected = hashlib.sha256(b"abc").hexdigest()
            with patch("httpx.stream", return_value=Response()):
                download_file(["https://example.invalid/asset.bin"], destination, sha256=expected)

            self.assertEqual(destination.read_bytes(), b"abc")
            self.assertFalse((destination.with_suffix(".bin.tmp")).exists())

    def test_download_file_removes_temporary_file_after_checksum_failure(self) -> None:
        class Response:
            headers = {}

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def raise_for_status(self) -> None:
                return None

            def iter_bytes(self):
                yield b"abc"

        with tempfile.TemporaryDirectory() as temp_dir:
            destination = Path(temp_dir) / "asset.bin"
            with patch("httpx.stream", return_value=Response()), patch("runtime._retry.time.sleep"):
                with self.assertRaisesRegex(RuntimeError, "SHA256 verification failed"):
                    download_file(["https://example.invalid/asset.bin"], destination, sha256="0" * 64)

            self.assertFalse(destination.exists())
            self.assertFalse((destination.with_suffix(".bin.tmp")).exists())

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

    def test_select_platform_asset_returns_supported_variant(self) -> None:
        asset = {
            "name": "ffmpeg",
            "platforms": {
                "windows-x64": {"archive_name": "windows.zip"},
                "linux-x64": {"archive_name": "linux.tar.xz"},
            },
        }

        selected = select_platform_asset(asset, "linux-x64")

        self.assertEqual(selected["archive_name"], "linux.tar.xz")
        self.assertEqual(selected["name"], "ffmpeg")

    def test_select_platform_asset_rejects_unsupported_variant(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "does not support macos-x64"):
            select_platform_asset(
                {"name": "ffmpeg", "platforms": {"windows-x64": {}}},
                "macos-x64",
            )

    def test_whisper_manifest_requires_model_weights_for_each_platform(self) -> None:
        manifest_path = Path(__file__).resolve().parents[1] / "assets_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        whisper_asset = next(asset for asset in manifest["assets"] if asset["name"] == "whisper-tiny")

        for platform_asset in whisper_asset["platforms"].values():
            self.assertEqual(platform_asset["expected_glob"], "**/model.bin")
            self.assertRegex(platform_asset["file_sha256"], r"^[0-9a-f]{64}$")

    def test_manifest_archives_have_sha256_pins(self) -> None:
        manifest_path = Path(__file__).resolve().parents[1] / "assets_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        ffmpeg_asset = next(asset for asset in manifest["assets"] if asset["name"] == "ffmpeg")

        for platform_asset in ffmpeg_asset["platforms"].values():
            for archive in platform_asset["archives"]:
                self.assertRegex(archive["sha256"], r"^[0-9a-f]{64}$")

    def test_script_contracts_are_thin_forwarders(self) -> None:
        scripts_root = Path(__file__).resolve().parents[2] / "scripts"
        for script_name in ("bootstrap.ps1", "bootstrap.sh", "invoke_pipeline.ps1", "invoke_pipeline.sh"):
            script_text = (scripts_root / script_name).read_text(encoding="utf-8")
            self.assertIn("runtime", script_text)
            self.assertNotIn("ffmpeg-master-latest", script_text)

    def test_skill_tells_vision_models_to_read_visual_frames(self) -> None:
        skill_root = Path(__file__).resolve().parents[2]
        skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("如果当前模型有识图能力", skill_text)
        self.assertIn("读取 `visual_frames`", skill_text)
        self.assertIn("图文动态", skill_text)


if __name__ == "__main__":
    unittest.main()
