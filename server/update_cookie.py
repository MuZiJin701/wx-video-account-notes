"""Interactive, no-echo Yuanbao Cookie update on the resolver host."""

from __future__ import annotations

import getpass
import os
import subprocess
import tempfile
from pathlib import Path


COOKIE_PATH = Path("/root/projects/wx-video-account-notes/cookie")
RESOLVER = Path("/root/projects/wx-video-account-notes/resolver")
DEFAULT_LINK = "https://weixin.qq.com/sph/AHhuzPE3Pi"


def update_cookie(cookie: str, link: str, *, path: Path = COOKIE_PATH, binary: Path = RESOLVER) -> bool:
    if not cookie or len(cookie) > 16_384 or "\n" in cookie or "\r" in cookie:
        return False
    try:
        check = subprocess.run(
            [str(binary), "--check-cookie", link],
            input=cookie,
            text=True,
            capture_output=True,
            timeout=80,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if check.returncode != 0:
        return False
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as output:
            temporary = output.name
            output.write(cookie)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        return True
    except OSError:
        return False
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


if __name__ == "__main__":
    link = os.environ.get("WX_NOTES_VERIFY_LINK") or DEFAULT_LINK
    candidate = getpass.getpass("粘贴元宝 Cookie（不回显）: ").strip()
    if update_cookie(candidate, link):
        print("Cookie 已更新；解析验证通过。")
    else:
        print("验证或更新失败，原有 Cookie 未改变。可设置 WX_NOTES_VERIFY_LINK 后重试。")
        raise SystemExit(1)
