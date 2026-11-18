from __future__ import annotations

import unittest

from runtime.media_extract import (
    build_frame_filter,
    build_ocr_frame_filter,
    build_visual_frame_filter,
    choose_frame_interval,
    choose_ocr_frame_interval,
    choose_visual_frame_interval,
)


class MediaExtractTests(unittest.TestCase):
    def test_build_frame_filter_uses_adaptive_interval_without_frame_limit(self) -> None:
        frame_filter = build_frame_filter(seconds_per_frame=3)

        self.assertEqual(frame_filter, "fps=1/3,scale='min(1280,iw)':-2")

    def test_choose_frame_interval_adapts_to_video_duration(self) -> None:
        self.assertEqual(choose_frame_interval(45), 2)
        self.assertEqual(choose_frame_interval(120), 3)
        self.assertEqual(choose_frame_interval(320), 4)

    def test_choose_ocr_frame_interval_targets_candidate_limit(self) -> None:
        self.assertEqual(choose_ocr_frame_interval(45, target_frames=100), 1)
        self.assertEqual(choose_ocr_frame_interval(320, target_frames=100), 4)
        self.assertEqual(choose_ocr_frame_interval(1200, target_frames=100), 12)

    def test_build_ocr_frame_filter_crops_bottom_subtitle_region(self) -> None:
        frame_filter = build_ocr_frame_filter(seconds_per_frame=4)

        self.assertIn("fps=1/4", frame_filter)
        self.assertIn("crop=iw:ih*0.45:0:ih*0.55", frame_filter)
        self.assertIn("scale='min(960,iw)':-2", frame_filter)

    def test_visual_frame_filter_keeps_full_frame_and_small_count(self) -> None:
        self.assertEqual(choose_visual_frame_interval(45, target_frames=5), 9)
        frame_filter = build_visual_frame_filter(seconds_per_frame=9)

        self.assertEqual(frame_filter, "fps=1/9,scale='min(1280,iw)':-2")


if __name__ == "__main__":
    unittest.main()
