from __future__ import annotations

import io
import json
import os
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

os.environ["WX_NOTES_RESOLVER_CONFIG"] = str(
    Path(__file__).resolve().parents[1]
    / "plugins/wx-video-account-notes/skills/wx-video-account-notes/runtime/resolver_config.json"
)
import gateway  # noqa: E402


class GatewayTests(unittest.TestCase):
    def test_only_authorized_parse_route_reaches_loopback(self) -> None:
        server = gateway.ThreadingHTTPServer(("127.0.0.1", 0), gateway.Handler)
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"

        def status(path: str, key: str = "") -> int:
            request = Request(base + path, headers={"Authorization": key})
            try:
                with urlopen(request) as response:
                    return response.status
            except HTTPError as exc:
                try:
                    return exc.code
                finally:
                    exc.close()

        try:
            valid = f"Bearer {gateway.ACCESS_KEY}"
            self.assertEqual(status("/other", valid), 404)
            self.assertEqual(status("/api/channels/parse_sph?url=https%3A%2F%2Fweixin.qq.com%2Fsph%2Ftest"), 401)
            self.assertEqual(status("/api/channels/parse_sph?url=bad", valid), 400)
            with patch("gateway.urlopen", return_value=io.BytesIO(json.dumps({"code": "OK", "data": {}}).encode())):
                self.assertEqual(status("/api/channels/parse_sph?url=https%3A%2F%2Fweixin.qq.com%2Fsph%2Ftest", valid), 200)
            gateway.recent.clear()
            gateway.recent.extend([time.monotonic()] * 30)
            self.assertEqual(status("/api/channels/parse_sph?url=https%3A%2F%2Fweixin.qq.com%2Fsph%2Ftest", valid), 429)
        finally:
            gateway.recent.clear()
            server.shutdown()
            thread.join()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
