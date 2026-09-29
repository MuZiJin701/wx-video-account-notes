"""Public, single-route HTTP gateway for the loopback Go resolver."""

from __future__ import annotations

import hmac
import json
import os
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import urlopen


CONFIG = os.environ.get("WX_NOTES_RESOLVER_CONFIG", "/root/projects/wx-video-account-notes/client.json")
with open(CONFIG, encoding="utf-8") as source:
    ACCESS_KEY = json.load(source)["access_key"]
if not ACCESS_KEY:
    raise SystemExit("access key is empty")

# ponytail: one shared 30/min budget; use per-client limits if invited-user traffic grows.
recent: deque[float] = deque()
rate_lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        pass  # Request lines contain share links and must not enter logs.

    def send_json(self, status: int, code: str, data: object = None) -> None:
        body = json.dumps({"code": code, "msg": code, "data": data}, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parts = urlsplit(self.path)
        if parts.path != "/api/channels/parse_sph":
            self.send_json(404, "NOT_FOUND")
            return
        auth = self.headers.get("Authorization", "")
        if not hmac.compare_digest(auth, f"Bearer {ACCESS_KEY}"):
            self.send_json(401, "UNAUTHORIZED")
            return
        links = parse_qs(parts.query).get("url", [])
        if len(links) != 1 or not links[0].startswith("https://weixin.qq.com/sph/"):
            self.send_json(400, "INVALID_LINK")
            return
        now = time.monotonic()
        with rate_lock:
            while recent and recent[0] <= now - 60:
                recent.popleft()
            limited = len(recent) >= 30
            if not limited:
                recent.append(now)
        if limited:
            self.send_json(429, "RATE_LIMITED")
            return
        target = "http://127.0.0.1:17879/internal/parse?" + urlencode({"url": links[0]})
        try:
            with urlopen(target, timeout=65) as response:
                payload = json.load(response)
                self.send_json(200, payload.get("code", "BAD_RESPONSE"), payload.get("data"))
        except HTTPError as exc:
            with exc:
                try:
                    payload = json.load(exc)
                    code = payload.get("code", "UPSTREAM_ERROR")
                except (ValueError, AttributeError):
                    code = "UPSTREAM_ERROR"
            self.send_json(exc.code, code)
        except (URLError, TimeoutError, ValueError, AttributeError):
            self.send_json(502, "RESOLVER_UNAVAILABLE")


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 80), Handler).serve_forever()
