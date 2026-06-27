from __future__ import annotations

import unittest

from runtime.resolve_link import parse_worker_payload


class ResolveLinkTests(unittest.TestCase):
    def test_prefers_author_info_and_description(self) -> None:
        payload = {
            "data": {
                "authorInfo": {"nickname": "GitHubStore"},
                "feedInfo": {
                    "description": "颠覆 3D 建模常识的新技术 R3",
                    "videoUrl": "https://example.invalid/video.mp4",
                },
            }
        }

        parsed = parse_worker_payload(payload)

        self.assertEqual(parsed["author"], "GitHubStore")
        self.assertEqual(parsed["title"], "颠覆 3D 建模常识的新技术 R3")
        self.assertEqual(parsed["video_url"], "https://example.invalid/video.mp4")
        self.assertEqual(parsed["media_type"], "video")

    def test_parse_worker_payload_supports_image_feed_without_video_url(self) -> None:
        payload = {
            "data": {
                "authorInfo": {"nickname": "NatureSkills"},
                "feedInfo": {
                    "description": "开源项目动态",
                    "mediaType": 2,
                    "picInfo": [
                        {"url": "https://example.invalid/one.jpg"},
                        {"url": "https://example.invalid/two.jpg"},
                    ],
                },
            }
        }

        parsed = parse_worker_payload(payload)

        self.assertEqual(parsed["media_type"], "image")
        self.assertEqual(parsed["image_urls"], ["https://example.invalid/one.jpg", "https://example.invalid/two.jpg"])
        self.assertEqual(parsed["video_url"], "")


if __name__ == "__main__":
    unittest.main()
