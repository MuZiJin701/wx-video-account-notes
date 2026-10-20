"""Private configuration shared by deployment and Cookie maintenance."""

from __future__ import annotations

import json
import os
import re
import secrets
import tempfile
from pathlib import Path

from update_cookie import DEFAULT_LINK


ROOT = Path("/root/projects/wx-video-account-notes")
CONFIG_PATH = ROOT / "config.json"


def write_private_json(path: Path, value: dict) -> None:
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as output:
            temporary = output.name
            os.chmod(temporary, 0o600)
            json.dump(value, output, ensure_ascii=False, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)


def load_config(path: Path = CONFIG_PATH) -> dict:
    config = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(config, dict):
        raise ValueError("CONFIG_INVALID")
    qq = config.get("qq")
    if not isinstance(qq, dict) or not isinstance(qq.get("account"), str) or not re.fullmatch(r"[1-9][0-9]{4,14}", qq["account"]):
        raise ValueError("QQ_ACCOUNT_INVALID")
    if not isinstance(qq.get("password"), str) or not qq["password"] or len(qq["password"]) > 1024:
        raise ValueError("QQ_PASSWORD_MISSING")
    key = config.get("access_key")
    if not isinstance(key, str) or not key or not key.isascii() or any(c in key for c in "\r\n"):
        raise ValueError("ACCESS_KEY_INVALID")
    interval = config.get("cookie_check_interval_hours", 24)
    if type(interval) is not int or not 1 <= interval <= 8760:
        raise ValueError("COOKIE_INTERVAL_INVALID")
    link = config.get("verify_link", DEFAULT_LINK)
    if not isinstance(link, str) or not re.fullmatch(r"https://weixin\.qq\.com/sph/[A-Za-z0-9_-]+/?", link):
        raise ValueError("VERIFY_LINK_INVALID")
    return {**config, "cookie_check_interval_hours": interval, "verify_link": link}


def prepare_config(path: Path) -> None:
    if path.exists():
        config = json.loads(path.read_text(encoding="utf-8-sig"))
    else:
        legacy = path.with_name("client.json")
        config = json.loads(legacy.read_text(encoding="utf-8-sig")) if legacy.exists() else {}
    if not isinstance(config, dict):
        raise ValueError("CONFIG_INVALID")
    config.setdefault("qq", {"account": "", "password": ""})
    config.setdefault("cookie_check_interval_hours", 24)
    config.setdefault("verify_link", DEFAULT_LINK)
    if not config.get("access_key"):
        config["access_key"] = secrets.token_urlsafe(32)
    write_private_json(path, config)
    load_config(path)


if __name__ == "__main__":
    import sys

    try:
        prepare_config(Path(sys.argv[1]))
        print(load_config(Path(sys.argv[1]))["cookie_check_interval_hours"])
    except (OSError, ValueError, IndexError):
        print("CONFIG_INVALID: edit config.json (QQ account/password and verification link).", file=sys.stderr)
        raise SystemExit(1)
