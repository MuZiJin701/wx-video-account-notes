from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from runtime import pipeline


class PipelineTests(unittest.TestCase):
    def test_slugify_limits_length_and_windows_reserved_names(self):
        self.assertLessEqual(len(pipeline.slugify("很长的标题" * 30)), 80)
        self.assertEqual(pipeline.slugify("CON"), "_CON")

    def test_images_partial_failure_and_repeated_download_preserve_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            resolved = {"title": "图文", "author": "作者", "media_type": "image", "video_url": "", "image_urls": ["one", "two"], "cover_url": "cover", "bgm_urls": [], "raw_text": "{}"}
            def download(url, destination, *, kind):
                if url == "two":
                    raise ValueError("failed")
                result = destination.with_suffix(".png")
                result.write_bytes(b"image")
                return result
            args = ["--skill-root", temp, "--share-url", "https://weixin.qq.com/sph/example", "--output-dir", temp]
            with patch("runtime.pipeline.resolve_share_link", return_value=resolved), patch("runtime.pipeline.download_file", side_effect=download), patch("runtime.pipeline.run_ocr", return_value="图片文字"):
                self.assertEqual(pipeline.main(args), 1)
                (root / "图文" / "keep.txt").write_text("keep", encoding="utf-8")
                self.assertEqual(pipeline.main(args), 1)
            first, second = root / "图文", root / "图文_2"
            self.assertEqual((first / "keep.txt").read_text(encoding="utf-8"), "keep")
            self.assertTrue((second / "images" / "001.png").exists())
            self.assertTrue((second / "cover.png").exists())
            material = json.loads((second / "note_materials.json").read_text(encoding="utf-8"))
            self.assertIn("图片 002", material["status"]["download"])
            self.assertEqual(material["status"]["asr"], "图文动态无音频")
            self.assertIn("图片 002", (second / "index.html").read_text(encoding="utf-8"))

    def test_video_failure_keeps_other_media_and_records_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            resolved = {"title": "<video>", "author": "作者", "media_type": "video", "video_url": "bad", "image_urls": [], "cover_url": "cover", "bgm_urls": [], "raw_text": "{}"}
            def download(url, destination, *, kind):
                if url == "bad":
                    raise ValueError("failed")
                path = destination.with_suffix(".jpg")
                path.write_bytes(b"image")
                return path
            with patch("runtime.pipeline.resolve_share_link", return_value=resolved), patch("runtime.pipeline.download_file", side_effect=download), patch("runtime.pipeline.extract_audio") as audio:
                result = pipeline.main(["--skill-root", temp, "--share-url", "link", "--output-dir", temp])
            out = Path(temp) / "video"
            self.assertEqual(result, 1)
            audio.assert_not_called()
            self.assertTrue((out / "cover.jpg").exists())
            material = json.loads((out / "note_materials.json").read_text(encoding="utf-8"))
            self.assertIn("视频", material["status"]["download"])
            self.assertIn("视频下载失败", material["status"]["asr"])
            self.assertIn("&lt;video&gt;", (out / "index.html").read_text(encoding="utf-8"))

    def test_video_falls_back_to_next_available_version(self):
        with tempfile.TemporaryDirectory() as temp:
            resolved = {"title": "备用", "media_type": "video", "video_url": "first", "video_urls": ["first", "second"], "image_urls": [], "raw_text": "{}"}
            def download(url, destination, *, kind):
                if url == "first":
                    raise ValueError("bad")
                path = destination.with_suffix(".mp4")
                path.write_bytes(b"media")
                return path
            with (patch("runtime.pipeline.resolve_share_link", return_value=resolved), patch("runtime.pipeline.download_file", side_effect=download),
                  patch("runtime.pipeline.find_ffmpeg_tools", return_value=(Path("ffmpeg"), Path("ffprobe"))),
                  patch("runtime.pipeline.subprocess.run", return_value=SimpleNamespace(returncode=0, stdout="h264")),
                  patch("runtime.pipeline.extract_ocr_frames", return_value=[]), patch("runtime.pipeline.extract_visual_frames", return_value=[]),
                  patch("runtime.pipeline.extract_audio", return_value=Path("audio.wav")), patch("runtime.pipeline.resolve_asr_model_dir", return_value=Path("model")),
                  patch("runtime.pipeline.run_asr", return_value="转写内容")):
                self.assertEqual(pipeline.main(["--skill-root", temp, "--share-url", "link", "--output-dir", temp]), 0)
            self.assertTrue((Path(temp) / "备用" / "备用.mp4").exists())

    def test_video_and_attached_images_are_used(self):
        with tempfile.TemporaryDirectory() as temp:
            resolved = {"title": "动态", "media_type": "video", "video_url": "video", "image_urls": ["image"], "cover_url": "", "bgm_urls": [], "raw_text": "{}"}
            def download(url, destination, *, kind):
                path = destination.with_suffix(".mp4" if kind == "video" else ".png")
                path.write_bytes(b"media")
                return path
            with (patch("runtime.pipeline.resolve_share_link", return_value=resolved), patch("runtime.pipeline.download_file", side_effect=download),
                  patch("runtime.pipeline.find_ffmpeg_tools", return_value=(Path("ffmpeg"), Path("ffprobe"))),
                  patch("runtime.pipeline.subprocess.run", return_value=SimpleNamespace(returncode=0, stdout="h264")),
                  patch("runtime.pipeline.extract_ocr_frames", return_value=[]), patch("runtime.pipeline.extract_visual_frames", return_value=[]),
                  patch("runtime.pipeline.extract_audio", return_value=Path("audio.wav")), patch("runtime.pipeline.run_ocr", return_value="图片文字"),
                  patch("runtime.pipeline.resolve_asr_model_dir", return_value=Path("model")), patch("runtime.pipeline.run_asr", return_value="转写内容")):
                self.assertEqual(pipeline.main(["--skill-root", temp, "--share-url", "link", "--output-dir", temp]), 0)
            material = json.loads((Path(temp) / "动态" / "note_materials.json").read_text(encoding="utf-8"))
            self.assertEqual(material["ocr_lines"], ["图片文字"])
            self.assertEqual(material["status"]["download"], "成功")


if __name__ == "__main__":
    unittest.main()
