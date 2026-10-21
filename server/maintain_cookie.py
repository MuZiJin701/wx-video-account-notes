"""One operator-initiated Cookie check, with WeChat QR login only after expiry."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from server_config import CONFIG_PATH, ROOT, load_config
from update_cookie import check_cookie, update_cookie
from yuanbao_login import LoginError, UpstreamError, acquire_cookie, login_status


def maintain(config: dict, root: Path = ROOT) -> str:
    try:
        cookie_path = root / "cookie"
        cookie = cookie_path.read_text(encoding="utf-8").strip() if cookie_path.exists() else ""
        if check_cookie(cookie, config["verify_link"], binary=root / "resolver"):
            return "COOKIE_REUSED"
        if login_status(cookie) != "expired":
            return "COOKIE_OR_UPSTREAM_UNAVAILABLE"
        state_dir = root / ".runtime" / "server"
        state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        candidate = acquire_cookie(state_dir / "wechat-qr.png")
        if not update_cookie(candidate, config["verify_link"], path=cookie_path, binary=root / "resolver"):
            return "NEW_COOKIE_VALIDATION_FAILED"
        return "COOKIE_UPDATED"
    except (LoginError, UpstreamError) as error:
        return str(error)
    except Exception:
        return "MAINTENANCE_FAILED"


def main() -> int:
    os.umask(0o077)
    argparse.ArgumentParser(description=__doc__).parse_args()
    try:
        config = load_config(CONFIG_PATH)
        import fcntl

        state_dir = ROOT / ".runtime" / "server"
        state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(state_dir / "browsers"))
        with (state_dir / "maintenance.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                print("MAINTENANCE_ALREADY_RUNNING")
                return 1
            code = maintain(config)
    except KeyboardInterrupt:
        print("LOGIN_CANCELLED: 原有 Cookie 未改变。")
        return 130
    except Exception:
        print("CONFIG_OR_RUNTIME_INVALID: 检查私有 config.json 和运行目录。")
        return 1
    print(code)
    return 0 if code in ("COOKIE_REUSED", "COOKIE_UPDATED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
