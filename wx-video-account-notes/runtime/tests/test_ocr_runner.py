from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from runtime.ocr_runner import (
    _calculate_binarize_threshold,
    _filter_ocr_lines,
    _fuse_frame_results,
    _is_good_crop_result,
    _prepare_subtitle_crop,
    _prepare_crop_candidates,
    _score_ocr_result,
)


class OcrRunnerTests(unittest.TestCase):
    def test_prepare_crop_candidates_returns_multiple_regions(self) -> None:
        candidates = _prepare_crop_candidates()

        self.assertGreaterEqual(len(candidates), 3)

    def test_prepare_crop_candidates_cover_lower_and_mid_lower_regions(self) -> None:
        candidates = _prepare_crop_candidates()

        self.assertIn((0.03, 0.5, 0.97, 1.0), candidates)
        self.assertIn((0.12, 0.66, 0.88, 0.94), candidates)

    def test_calculate_binarize_threshold_adapts_to_image_brightness(self) -> None:
        dark_threshold = _calculate_binarize_threshold([40, 42, 44, 46])
        bright_threshold = _calculate_binarize_threshold([200, 202, 204, 206])

        self.assertGreater(bright_threshold, dark_threshold)
        self.assertGreaterEqual(dark_threshold, 80)
        self.assertLessEqual(bright_threshold, 210)

    def test_fuse_frame_results_merges_adjacent_duplicates(self) -> None:
        fused = _fuse_frame_results([
            ["第一句", "第二句"],
            ["第一句", "第二句"],
            ["第二句", "第三句"],
            ["第四句"],
        ])

        self.assertEqual(fused, ["第一句", "第二句", "第三句", "第四句"])

    def test_filter_ocr_lines_drops_short_repeated_watermark_like_text(self) -> None:
        filtered = _filter_ocr_lines([
            "小明小明",
            "......",
            "???",
            "这是正常字幕内容",
        ])

        self.assertEqual(filtered, ["这是正常字幕内容"])

    def test_score_ocr_result_prefers_subtitle_like_lines_over_short_corner_text(self) -> None:
        subtitle_score = _score_ocr_result(["这是完整字幕内容"])
        watermark_score = _score_ocr_result(["关注", "小店"])

        self.assertGreater(subtitle_score, watermark_score)

    def test_filter_ocr_lines_preserves_legitimate_short_subtitle_lines(self) -> None:
        filtered = _filter_ocr_lines([
            "走吧",
            "嗯",
            "小明小明",
            "......",
        ])

        self.assertEqual(filtered, ["走吧", "嗯"])

    def test_filter_ocr_lines_preserves_doubled_chinese_subtitle_words(self) -> None:
        filtered = _filter_ocr_lines([
            "谢谢",
            "看看",
            "小明小明",
            "......",
        ])

        self.assertEqual(filtered, ["谢谢", "看看"])

    def test_filter_ocr_lines_preserves_short_punctuated_subtitle_lines(self) -> None:
        filtered = _filter_ocr_lines([
            "嗯？",
            "啊！",
            "好吧…",
            "......",
            "???",
        ])

        self.assertEqual(filtered, ["嗯？", "啊！", "好吧…"])

    def test_prepare_subtitle_crop_scales_by_one_point_five(self) -> None:
        from PIL import Image

        image = Image.new("RGB", (200, 100), color="white")
        original_resize = Image.Image.resize
        resize_sizes: list[tuple[int, int]] = []

        def recording_resize(instance, size, *args, **kwargs):
            resize_sizes.append(size)
            return original_resize(instance, size, *args, **kwargs)

        with patch.object(Image.Image, "resize", autospec=True, side_effect=recording_resize):
            _prepare_subtitle_crop(image, (0.1, 0.5, 0.9, 1.0))

        self.assertEqual(resize_sizes, [(240, 75)])

    def test_is_good_crop_result_accepts_four_chinese_chars(self) -> None:
        self.assertTrue(_is_good_crop_result(["已经到了"] ))
        self.assertFalse(_is_good_crop_result(["到了"] ))


if __name__ == "__main__":
    unittest.main()
