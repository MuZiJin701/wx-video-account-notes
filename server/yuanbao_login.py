"""Headless QQ authentication. Never log browser errors or capture private pages."""

from __future__ import annotations

import re
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


YUANBAO = "https://yuanbao.tencent.com/"
USER_INFO = YUANBAO + "api/getuserinfo"
PARSE_API = YUANBAO + "api/weixin/get_parse_result"


class LoginError(RuntimeError):
    pass


class UpstreamError(RuntimeError):
    pass


def login_status(cookie: str) -> str:
    if not cookie:
        return "expired"
    request = Request(USER_INFO, headers={"Cookie": cookie, "Referer": YUANBAO, "User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request, timeout=20) as response:
            return "valid" if response.status == 200 else "unknown"
    except HTTPError as error:
        error.close()
        return "expired" if error.code == 401 else "unknown"
    except (OSError, URLError, ValueError):
        return "unknown"


def submit_qq_password(page, qq: dict, before_login) -> None:
    deadline = time.monotonic() + 30
    frame = None
    while time.monotonic() < deadline:
        frame = next((f for f in page.frames if f.name == "ptlogin_iframe"), None)
        if frame and frame.url != "about:blank":
            break
        page.wait_for_timeout(250)
    if (frame is None or urlsplit(frame.url).scheme != "https"
            or not (urlsplit(frame.url).hostname or "").endswith(".ptlogin2.qq.com")
            or urlsplit(page.url).hostname not in {"graph.qq.com", "mail.qq.com", "wx.mail.qq.com"}):
        raise LoginError("QQ_LOGIN_PAGE_CHANGED")
    frame.get_by_role("link", name="密码登录", exact=True).click(timeout=15_000)
    before_login()
    frame.get_by_role("textbox", name="支持QQ号/邮箱/手机号登录", exact=True).fill(qq["account"])
    frame.get_by_role("textbox", name="请输入密码", exact=True).fill(qq["password"])
    frame.get_by_role("button", name="登录", exact=True).click()


def skip_optional_binding(page) -> bool:
    for frame in page.frames:
        skip = frame.get_by_text(re.compile(r"^跳过[，,、\s]*直接登录$"))
        if skip.count() and skip.first.is_visible():
            skip.first.click(timeout=5_000)
            return True
    return False


def acquire_cookie(qq: dict, profile: Path, before_login) -> str:
    from playwright.sync_api import Error, sync_playwright

    profile.mkdir(parents=True, exist_ok=True, mode=0o700)
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            str(profile), channel="chromium", headless=True, locale="zh-CN",
        )
        try:
            page = context.pages[0] if context.pages else context.new_page()
            try:
                page.goto(YUANBAO, wait_until="domcontentloaded", timeout=45_000)
                status = context.request.get(USER_INFO, timeout=20_000).status
            except Error:
                raise UpstreamError("BROWSER_NETWORK_ERROR") from None
            if status not in (200, 401):
                raise UpstreamError("LOGIN_STATUS_UNKNOWN")
            if status == 401:
                try:
                    qq_choice = page.get_by_text("QQ", exact=True)
                    try:
                        qq_choice.wait_for(state="visible", timeout=5_000)
                    except Error:
                        page.get_by_role("button", name="登录", exact=True).click()
                    qq_choice.click(timeout=15_000)
                    deadline = time.monotonic() + 30
                    while time.monotonic() < deadline:
                        if urlsplit(page.url).hostname == "yuanbao.tencent.com" and context.request.get(USER_INFO, timeout=10_000).status == 200:
                            break
                        if any(f.name == "ptlogin_iframe" for f in page.frames):
                            submit_qq_password(page, qq, before_login)
                            break
                        page.wait_for_timeout(250)
                    else:
                        raise LoginError("QQ_LOGIN_PAGE_CHANGED")
                    deadline = time.monotonic() + 90
                    skips = 0
                    while time.monotonic() < deadline:
                        if skips < 3 and skip_optional_binding(page):
                            skips += 1
                        if urlsplit(page.url).hostname == "yuanbao.tencent.com":
                            if context.request.get(USER_INFO, timeout=10_000).status == 200:
                                break
                        page.wait_for_timeout(1_000)
                    else:
                        raise LoginError("QQ_LOGIN_FAILED_OR_VERIFICATION_REQUIRED")
                except Error:
                    raise LoginError("QQ_LOGIN_FLOW_FAILED") from None
            return "; ".join(f"{c['name']}={c['value']}" for c in context.cookies([PARSE_API]))
        finally:
            context.close()
