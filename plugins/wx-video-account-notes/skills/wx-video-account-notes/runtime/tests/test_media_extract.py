from __future__ import annotations

import unittest

from runtime.media_extract import build_frame_filter, choose_frame_interval


class MediaExtractTests(unittest.TestCase):
    def test_build_frame_filter_uses_adaptive_interval_without_frame_limit(self) -> None:
        frame_filter = build_frame_filter(seconds_per_frame=3)

        self.assertEqual(frame_filter, "fps=1/3,scale='min(1280,iw)':-2")

    def test_choose_frame_interval_adapts_to_video_duration(self) -> None:
        self.assertEqual(choose_frame_interval(45), 2)
        self.assertEqual(choose_frame_interval(120), 3)
        self.assertEqual(choose_frame_interval(320), 4)


if __name__ == "__main__":
    unittest.main()
