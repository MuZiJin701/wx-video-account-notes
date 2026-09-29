from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import patch

import httpx

from runtime.resolve_link import _CONFIG, parse_worker_payload, resolve_share_link


class ResolveLinkTests(unittest.TestCase):
    def test_shared_resolver_returns_video_fields(self) -> None:
        feed = {"data": {"authorInfo": {"nickname": "作者"}, "feedInfo": {
            "description": "标题", "videoUrl": "https://example.invalid/video.mp4"}}}
        response = SimpleNamespace(status_code=200, json=lambda: {"code": "OK", "data": feed})
        with patch("httpx.get", return_value=response) as get:
            parsed = resolve_share_link("https://weixin.qq.com/sph/example")
        self.assertEqual(parsed["title"], "标题")
        self.assertEqual(parsed["author"], "作者")
        self.assertEqual(parsed["video_url"], "https://example.invalid/video.mp4")
        self.assertEqual(get.call_args.kwargs["params"]["url"], "https://weixin.qq.com/sph/example")
        self.assertEqual(get.call_args.kwargs["headers"]["Authorization"], f"Bearer {_CONFIG['access_key']}")

    def test_shared_resolver_returns_image_fields(self) -> None:
        feed = {"data": {"feedInfo": {"picInfo": [{"url": "https://example.invalid/one.jpg"}]}}}
        response = SimpleNamespace(status_code=200, json=lambda: {"code": "OK", "data": feed})
        with patch("httpx.get", return_value=response):
            parsed = resolve_share_link("https://weixin.qq.com/sph/example")
        self.assertEqual(parsed["media_type"], "image")
        self.assertEqual(parsed["image_urls"], ["https://example.invalid/one.jpg"])

    def test_shared_resolver_reports_actionable_errors(self) -> None:
        for status, code, message in (
            (401, "UNAUTHORIZED", "凭证不匹配"),
            (503, "LOGIN_REQUIRED", "缺少元宝登录态"),
            (503, "LOGIN_EXPIRED_OR_UPSTREAM_CHANGED", "可能失效"),
            (502, "FEED_UNAVAILABLE_OR_UPSTREAM_CHANGED", "媒体动态不可用"),
            (429, "RATE_LIMITED", "过于频繁"),
        ):
            with self.subTest(code=code):
                response = SimpleNamespace(status_code=status, json=lambda: {"code": code})
                with patch("httpx.get", return_value=response):
                    with self.assertRaisesRegex(RuntimeError, message):
                        resolve_share_link("https://weixin.qq.com/sph/example")

    def test_shared_resolver_reports_connection_failure(self) -> None:
        with patch("httpx.get", side_effect=httpx.ConnectError("offline")):
            with self.assertRaisesRegex(RuntimeError, "解析服务不可达"):
                resolve_share_link("https://weixin.qq.com/sph/example")

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
