from __future__ import annotations

from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit


def download_file(url: str, destination: Path, *, kind: str) -> Path:
    """Download to a temporary file, verify the response and keep its real extension."""
    import httpx
    from runtime._retry import retry_call

    def download() -> Path:
        current = url
        for _ in range(6):
            parts = urlsplit(current)
            if kind == "audio" and parts.scheme == "http" and parts.hostname == "wx.music.tc.qq.com" and parts.port in (None, 80):
                parts = parts._replace(scheme="https", netloc="wx.music.tc.qq.com")
                current = urlunsplit(parts)
            host = parts.hostname or ""
            if (parts.scheme != "https" or parts.username or parts.password or parts.port not in (None, 443)
                    or not any(host == domain or host.endswith("." + domain) for domain in ("qq.com", "qpic.cn", "qlogo.cn", "gtimg.com"))):
                raise ValueError("媒体地址不是受支持的腾讯 HTTPS 地址")
            if kind == "video":
                query = urlencode([(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key != "X-snsvideoflag"])
                current = urlunsplit(parts._replace(query=query))
            with httpx.stream("GET", current, follow_redirects=False, timeout=120.0, headers={"Accept-Encoding": "identity"}) as response:
                if response.is_redirect:
                    current = urljoin(current, response.headers["location"])
                    continue
                response.raise_for_status()
                mime = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                extensions = {
                    "video": {"video/mp4": ".mp4", "video/webm": ".webm"},
                    "audio": {"audio/mp4": ".m4a", "audio/x-m4a": ".m4a", "audio/mpeg": ".mp3", "audio/aac": ".aac", "audio/ogg": ".ogg", "audio/wav": ".wav", "audio/x-wav": ".wav", "audio/flac": ".flac"},
                    "image": {"image/jpeg": ".jpg", "image/jpg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif", "image/avif": ".avif"},
                }[kind]
                temporary = destination.with_name(destination.name + ".part")
                try:
                    with temporary.open("xb") as output:
                        size = 0
                        for chunk in response.iter_bytes():
                            size += output.write(chunk)
                    expected = response.headers.get("content-length")
                    if not size or (expected and not response.headers.get("content-encoding") and size != int(expected)):
                        raise ValueError("媒体文件不完整")
                    if kind == "image":
                        from PIL import Image
                        with Image.open(temporary) as image:
                            image.verify()
                            extension = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp", "GIF": ".gif", "AVIF": ".avif"}.get(image.format)
                    else:
                        with temporary.open("rb") as source:
                            head = source.read(12)
                        if kind == "video":
                            extension = ".mp4" if head[4:8] == b"ftyp" else ".webm" if head.startswith(b"\x1aE\xdf\xa3") else None
                        else:
                            extension = (".m4a" if head[4:8] == b"ftyp" else
                                         ".ogg" if head.startswith(b"OggS") else
                                         ".wav" if head.startswith(b"RIFF") and head[8:12] == b"WAVE" else
                                         ".flac" if head.startswith(b"fLaC") else
                                         extensions.get(mime) if head.startswith(b"ID3") or (len(head) > 1 and head[0] == 0xff and head[1] & 0xe0 == 0xe0) else None)
                    if not extension:
                        raise ValueError("媒体格式不受支持或无法识别")
                    target = destination.with_name(destination.name + extension)
                    temporary.replace(target)
                    return target
                finally:
                    temporary.unlink(missing_ok=True)
        raise ValueError("媒体重定向次数过多")

    return retry_call(download, description=f"download {destination.name}")
