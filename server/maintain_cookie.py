"""One maintenance attempt, invoked immediately by deployment and by systemd timer."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from server_config import CONFIG_PATH, ROOT, load_config, write_private_json
from update_cookie import check_cookie, update_cookie
from yuanbao_login import LoginError, UpstreamError, acquire_cookie, login_status


def maintain(config: dict, root: Path = ROOT, *, resume: bool = False) -> str:
    state_dir = root / ".runtime" / "server"
    state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    state_path = state_dir / "maintenance.json"
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    if not isinstance(state, dict):
        raise ValueError("STATE_INVALID")
    if not isinstance(state.get("notified_errors", []), list) or type(state.get("paused", False)) is not bool:
        raise ValueError("STATE_INVALID")
    if resume:
        state["paused"] = False
        write_private_json(state_path, state)

    def before_login() -> None:
        state["paused"] = True
        write_private_json(state_path, state)

    code = "MAINTENANCE_FAILED"
    try:
        cookie_path = root / "cookie"
        cookie = cookie_path.read_text(encoding="utf-8").strip() if cookie_path.exists() else ""
        if check_cookie(cookie, config["verify_link"], binary=root / "resolver"):
            state.pop("notified_errors", None)
            write_private_json(state_path, state)
            return "COOKIE_REUSED"
        status = login_status(cookie)
        if status != "expired":
            raise UpstreamError("COOKIE_OR_UPSTREAM_UNAVAILABLE")
        if state.get("paused"):
            raise UpstreamError("LOGIN_RETRY_PAUSED")
        candidate = acquire_cookie(config["qq"], state_dir / "yuanbao-profile", before_login)
        if not update_cookie(candidate, config["verify_link"], path=cookie_path, binary=root / "resolver"):
            raise UpstreamError("NEW_COOKIE_VALIDATION_FAILED")
        state["paused"] = False
        state.pop("notified_errors", None)
        write_private_json(state_path, state)
        return "COOKIE_UPDATED"
    except LoginError as error:
        before_login()
        code = str(error)
    except UpstreamError as error:
        code = str(error)
    except Exception:
        code = "MAINTENANCE_FAILED"
    if code == "LOGIN_RETRY_PAUSED":
        return code
    # Mark before attempting delivery: an interrupted send must not produce repeated mail.
    if code not in state.get("notified_errors", []):
        state.setdefault("notified_errors", []).append(code)
        write_private_json(state_path, state)
        try:
            from mail_notification import notify_error

            notify_error(config["qq"], state_dir / "mail-profile", code)
            print("ERROR_MAIL_SENT")
        except Exception:
            print("ERROR_MAIL_FAILED: inspect local maintenance status.")
    return code


def main() -> int:
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument("--resume", action="store_true", help="Allow one password login attempt after manual repair")
    args = parser.parse_args()
    try:
        config = load_config(CONFIG_PATH)
        # systemd and manual runs share a nonblocking lock, including browser profiles.
        import fcntl

        state_dir = ROOT / ".runtime" / "server"
        state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        with (state_dir / "maintenance.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                print("MAINTENANCE_ALREADY_RUNNING")
                return 0
            code = maintain(config, resume=args.resume)
    except Exception:
        print("CONFIG_OR_STATE_INVALID: check private config.json and maintenance state.")
        return 1
    print(code)
    return 0 if code in ("COOKIE_REUSED", "COOKIE_UPDATED") else 1


if __name__ == "__main__":
    raise SystemExit(main())
