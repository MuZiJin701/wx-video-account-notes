from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runtime import pipeline


class PipelineTests(unittest.TestCase):
    def test_pipeline_writes_note_materials_for_agent_handoff(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_root = root / "skill"
            output_dir = root / "output"
            ffmpeg_dir = skill_root / ".runtime" / "tools" / "ffmpeg" / "bin"
            model_dir = skill_root / ".runtime" / "models" / "whisper" / "tiny"
            ffmpeg_dir.mkdir(parents=True)
            model_dir.mkdir(parents=True)
            (ffmpeg_dir / "ffmpeg.exe").write_text("", encoding="utf-8")
            (ffmpeg_dir / "ffprobe.exe").write_text("", encoding="utf-8")
            (model_dir / "config.json").write_text("{}", encoding="utf-8")

            materials = {
                "share_url": "https://weixin.qq.com/sph/example",
                "slug": "标题",
                "metadata": {"title": "标题", "author": "作者", "raw_title": "标题"},
                "ocr_lines": ["字幕线索"],
                "asr_lines": ["转写文案"],
                "overview_lines": ["梗概"],
                "status": {"ocr": "成功", "asr": "成功"},
            }

            with (
                patch("runtime.pipeline.resolve_share_link", return_value={
                    "title": "标题",
                    "author": "作者",
                    "video_url": "https://example.invalid/demo.mp4",
                    "raw_text": '{"ok":true}',
                }),
                patch("runtime.pipeline.download_video"),
                patch("runtime.pipeline.extract_frames", return_value=[]),
                patch("runtime.pipeline.extract_audio", return_value=output_dir / "audio" / "speech.wav"),
                patch("runtime.pipeline.run_ocr", return_value=""),
                patch("runtime.pipeline.run_asr", return_value="转写文案"),
                patch("runtime.pipeline.build_note_materials", return_value=materials),
            ):
                exit_code = pipeline.main([
                    "--skill-root",
                    str(skill_root),
                    "--share-url",
                    "https://weixin.qq.com/sph/example",
                    "--output-dir",
                    str(output_dir),
                ])

            self.assertEqual(exit_code, 0)
            self.assertTrue((output_dir / "note_materials.json").exists())


if __name__ == "__main__":
    unittest.main()
