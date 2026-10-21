"""Manual fresh WeChat login and parse check; never publishes Cookie."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

from server_config import load_config
from update_cookie import check_cookie
from yuanbao_login import LoginError, UpstreamError, acquire_cookie


def check_login(config: dict, work_root: Path) -> str:
    work_root.mkdir(parents=True, exist_ok=True, mode=0o700)
    with TemporaryDirectory(prefix="login-check-", dir=work_root) as directory:
        root = Path(directory)
        cookie = acquire_cookie(root / "wechat-qr.png")
        print("YUANBAO_LOGIN_OK", flush=True)
        binary = root / "resolver"
        shutil.copyfile(Path(__file__).with_name("resolver-linux-amd64"), binary)
        binary.chmod(0o700)
        if not check_cookie(cookie, config["verify_link"], binary=binary):
            raise UpstreamError("YUANBAO_PARSE_FAILED")
        return "YUANBAO_PARSE_OK"


def main() -> int:
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path, help="Private test config.json")
    args = parser.parse_args()
    try:
        config = load_config(args.config)
    except (OSError, ValueError):
        print("CONFIG_INVALID: check the private test config.")
        return 1
    runtime = Path(__file__).resolve().parents[1] / ".runtime/server"
    os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", str(runtime / "browsers"))
    print("WECHAT_CHECK_STARTED", flush=True)
    try:
        print(check_login(config, runtime))
        return 0
    except KeyboardInterrupt:
        print("LOGIN_CANCELLED")
        return 130
    except (LoginError, UpstreamError) as error:
        print(str(error))
    except Exception:
        print("WECHAT_CHECK_FAILED")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
