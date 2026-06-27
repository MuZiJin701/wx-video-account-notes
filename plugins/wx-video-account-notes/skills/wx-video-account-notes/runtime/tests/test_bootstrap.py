from __future__ import annotations

import tempfile
import unittest
import json
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

    def test_whisper_manifest_requires_model_weights(self) -> None:
        manifest_path = Path(__file__).resolve().parents[1] / "assets_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        whisper_asset = next(asset for asset in manifest["assets"] if asset["name"] == "whisper-tiny")

        self.assertEqual(whisper_asset["expected_glob"], "**/model.bin")

    def test_bootstrap_script_sets_pythonpath_before_running_runtime_bootstrap(self) -> None:
        script_path = Path(__file__).resolve().parents[2] / "scripts" / "bootstrap.ps1"
        script_text = script_path.read_text(encoding="utf-8")

        self.assertIn('$env:PYTHONPATH = $skillRoot', script_text)

    def test_runtime_scripts_use_only_private_uv_and_locked_python_project(self) -> None:
        scripts_root = Path(__file__).resolve().parents[2] / "scripts"
        skill_root = scripts_root.parent
        common_text = (scripts_root / "common.ps1").read_text(encoding="utf-8")
        bootstrap_text = (scripts_root / "bootstrap.ps1").read_text(encoding="utf-8")
        invoke_text = (scripts_root / "invoke_pipeline.ps1").read_text(encoding="utf-8")

        self.assertIn("return '0.11.25'", common_text)
        self.assertIn("return '3.13.14'", common_text)
        self.assertNotIn("Get-Command uv", common_text)
        self.assertIn("releases/download/$targetUvVersion", bootstrap_text)
        self.assertIn("'python', 'install', $targetPythonVersion", bootstrap_text)
        self.assertIn("'sync', '--locked'", bootstrap_text)
        self.assertNotIn("'pip', 'install'", bootstrap_text)
        self.assertIn("'run', '--locked'", invoke_text)
        self.assertTrue((skill_root / ".python-version").exists())
        self.assertTrue((skill_root / "pyproject.toml").exists())
        self.assertTrue((skill_root / "uv.lock").exists())

    def test_skill_tells_vision_models_to_read_visual_frames(self) -> None:
        skill_root = Path(__file__).resolve().parents[2]
        skill_text = (skill_root / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("如果当前模型有识图能力", skill_text)
        self.assertIn("读取 `visual_frames`", skill_text)
        self.assertIn("图文动态", skill_text)


if __name__ == "__main__":
    unittest.main()
