from __future__ import annotations

import io
from contextlib import nullcontext
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import httpx
from PIL import Image
from runtime.download_video import download_file


class DownloadTests(unittest.TestCase):
    def test_image_format_and_redirect_validation(self):
        image = io.BytesIO()
        Image.new("RGB", (2, 2)).save(image, format="PNG")
        response = httpx.Response(200, headers={"content-type": "image/jpeg"}, content=image.getvalue(), request=httpx.Request("GET", "https://qpic.cn/a"))
        with tempfile.TemporaryDirectory() as temp, patch("httpx.stream", return_value=nullcontext(response)):
            result = download_file("https://qpic.cn/a", Path(temp) / "image", kind="image")
            self.assertEqual(result.suffix, ".png")
        redirect = httpx.Response(302, headers={"location": "http://127.0.0.1/secret"}, request=httpx.Request("GET", "https://qpic.cn/a"))
        with tempfile.TemporaryDirectory() as temp, patch("httpx.stream", return_value=nullcontext(redirect)), patch("runtime._retry.time.sleep"):
            with self.assertRaises(RuntimeError):
                download_file("https://qpic.cn/a", Path(temp) / "image", kind="image")
            self.assertFalse(list(Path(temp).iterdir()))

    def test_incomplete_response_leaves_no_file(self):
        response = httpx.Response(200, headers={"content-type": "video/mp4", "content-length": "100"}, content=b"short", request=httpx.Request("GET", "https://qq.com/a"))
        with tempfile.TemporaryDirectory() as temp, patch("httpx.stream", return_value=nullcontext(response)), patch("runtime._retry.time.sleep"):
            with self.assertRaises(RuntimeError):
                download_file("https://qq.com/a?X-snsvideoflag=1", Path(temp) / "video", kind="video")
            self.assertFalse(list(Path(temp).iterdir()))


if __name__ == "__main__":
    unittest.main()
