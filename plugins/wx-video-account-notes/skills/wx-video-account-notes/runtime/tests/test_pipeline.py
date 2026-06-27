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
                patch("runtime.pipeline.extract_ocr_frames", return_value=[output_dir / "ocr_frames" / "001.jpg"]) as extract_ocr_frames,
                patch("runtime.pipeline.extract_visual_frames", return_value=[output_dir / "frames" / "001.jpg"]) as extract_visual_frames,
                patch("runtime.pipeline.extract_audio", return_value=output_dir / "audio" / "speech.wav"),
                patch("runtime.pipeline.run_ocr", return_value="") as run_ocr,
                patch("runtime.pipeline.run_asr", return_value="转写文案"),
                patch("runtime.pipeline.build_note_materials", return_value=materials) as build_note_materials,
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
            extract_ocr_frames.assert_called_once()
            extract_visual_frames.assert_called_once()
            run_ocr.assert_called_once_with([output_dir / "ocr_frames" / "001.jpg"], frames_are_subtitle_crops=True)
            self.assertEqual(
                build_note_materials.call_args.kwargs["frame_paths"],
                [output_dir / "frames" / "001.jpg"],
            )

    def test_pipeline_handles_image_feed_without_video_or_asr(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            skill_root = root / "skill"
            output_dir = root / "output"

            materials = {
                "share_url": "https://weixin.qq.com/sph/image",
                "slug": "图文动态",
                "metadata": {"title": "图文动态", "author": "作者", "raw_title": "图文动态"},
                "ocr_lines": ["图片文字"],
                "asr_lines": [],
                "overview_lines": ["梗概"],
                "status": {"ocr": "成功", "asr": "图文动态无音频"},
                "visual_frames": [str(output_dir / "frames" / "001.jpg")],
            }

            with (
                patch("runtime.pipeline.resolve_share_link", return_value={
                    "title": "图文动态",
                    "author": "作者",
                    "media_type": "image",
                    "image_urls": ["https://example.invalid/one.jpg"],
                    "video_url": "",
                    "raw_text": '{"ok":true}',
                }),
                patch("runtime.pipeline.download_video") as download_video,
                patch("runtime.pipeline.download_images", return_value=[output_dir / "frames" / "001.jpg"]) as download_images,
                patch("runtime.pipeline.extract_ocr_frames") as extract_ocr_frames,
                patch("runtime.pipeline.extract_visual_frames") as extract_visual_frames,
                patch("runtime.pipeline.extract_audio") as extract_audio,
                patch("runtime.pipeline.run_ocr", return_value="图片文字") as run_ocr,
                patch("runtime.pipeline.run_asr") as run_asr,
                patch("runtime.pipeline.build_note_materials", return_value=materials) as build_note_materials,
            ):
                exit_code = pipeline.main([
                    "--skill-root",
                    str(skill_root),
                    "--share-url",
                    "https://weixin.qq.com/sph/image",
                    "--output-dir",
                    str(output_dir),
                ])

            self.assertEqual(exit_code, 0)
            self.assertTrue((output_dir / "note_materials.json").exists())
            download_video.assert_not_called()
            download_images.assert_called_once()
            extract_ocr_frames.assert_not_called()
            extract_visual_frames.assert_not_called()
            extract_audio.assert_not_called()
            run_ocr.assert_called_once_with([output_dir / "frames" / "001.jpg"], frames_are_subtitle_crops=False)
            run_asr.assert_not_called()
            self.assertEqual(build_note_materials.call_args.kwargs["asr_error"], "图文动态无音频")


if __name__ == "__main__":
    unittest.main()
