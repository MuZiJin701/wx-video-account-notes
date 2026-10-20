"""Manual fresh-login check; no deployment, Cookie publication, or mail delivery."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from mail_notification import open_mail
from server_config import load_config
from update_cookie import check_cookie
from yuanbao_login import LoginError, UpstreamError, acquire_cookie


def check_login(target: str, config: dict, work_root: Path) -> str:
    work_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    with TemporaryDirectory(prefix="login-check-", dir=work_root) as directory:
        root = Path(directory)
        if target == "yuanbao":
            cookie = acquire_cookie(config["qq"], root / "profile", lambda: print("YUANBAO_PASSWORD_ATTEMPT", flush=True))
            print("YUANBAO_LOGIN_OK", flush=True)
            binary = root / "resolver"
            shutil.copyfile(Path(__file__).with_name("resolver-linux-amd64"), binary)
            binary.chmod(0o700)
            if not check_cookie(cookie, config["verify_link"], binary=binary):
                raise UpstreamError("YUANBAO_PARSE_FAILED")
            return "YUANBAO_PARSE_OK"

        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                str(root / "profile"), channel="chromium", headless=True, locale="zh-CN",
            )
            try:
                open_mail(context, config["qq"])
                return "MAIL_LOGIN_OK"
            finally:
                context.close()


def main() -> int:
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=("yuanbao", "mail"))
    parser.add_argument("--config", required=True, type=Path, help="Private test config.json")
    args = parser.parse_args()
    try:
        config = load_config(args.config)
    except (OSError, ValueError):
        print("CONFIG_INVALID: check the private test config.")
        return 1
    print(args.target.upper() + "_CHECK_STARTED", flush=True)
    try:
        print(check_login(args.target, config, Path(__file__).resolve().parents[1] / ".runtime/server"))
        return 0
    except (LoginError, UpstreamError) as error:
        print(str(error))
    except Exception:
        # Browser exceptions can contain private URLs or page contents.
        print(args.target.upper() + "_CHECK_FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
