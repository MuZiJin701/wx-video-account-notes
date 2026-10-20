"""Best-effort, self-addressed QQ Mail alerts through the web UI."""

from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from pathlib import Path

from yuanbao_login import LoginError, skip_optional_binding, submit_qq_password


def visible_text(page, text):
    for frame in page.frames:
        locator = frame.get_by_text(text, exact=True)
        for item in locator.all():
            if item.is_visible():
                return item
    return None


def open_mail(context, qq: dict, progress=lambda stage, page: None):
    page = context.pages[0] if context.pages else context.new_page()
    progress("BROWSER_READY", page)
    try:
        page.goto("https://mail.qq.com/", wait_until="domcontentloaded", timeout=45_000)
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            compose = visible_text(page, "写信")
            if compose:
                return page, compose
            if any(f.name == "ptlogin_iframe" for f in page.frames):
                break
            page.wait_for_timeout(250)
        submit_qq_password(page, qq, lambda: None, progress)
        deadline = time.monotonic() + 90
        while time.monotonic() < deadline:
            compose = visible_text(page, "写信")
            if compose:
                return page, compose
            if skip_optional_binding(page):
                progress("OPTIONAL_BINDING_SKIPPED", page)
            page.wait_for_timeout(1_000)
    except LoginError:
        progress("FAILED", page)
        raise
    except Exception:
        progress("FAILED", page)
        raise LoginError("MAIL_LOGIN_FAILED") from None
    progress("FAILED", page)
    raise LoginError("MAIL_LOGIN_FAILED")


def notify_error(qq: dict, profile: Path, code: str) -> None:
    if not re.fullmatch(r"[A-Z][A-Z0-9_]{0,80}", code):
        raise ValueError("UNSAFE_ERROR_CODE")
    from playwright.sync_api import Error, sync_playwright
    profile.mkdir(parents=True, exist_ok=True, mode=0o700)
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            str(profile), channel="chromium", headless=True, locale="zh-CN",
        )
        try:
            page, compose = open_mail(context, qq)
            compose.click()
            page.get_by_label("收件人", exact=True).fill(qq["account"] + "@qq.com")
            page.get_by_label("收件人", exact=True).press("Enter")
            timestamp = datetime.now(timezone.utc).isoformat(timespec="microseconds")
            subject = "wx-notes 部署验证" if code == "DEPLOYMENT_TEST" else "wx-notes 自部署告警：" + code
            subject += " [" + timestamp + "]"
            page.get_by_label("主题", exact=True).fill(subject)
            body = "时间（UTC）：" + timestamp + "\n错误码：" + code
            body += "\n这是一封经授权的部署验证测试邮件。" if code == "DEPLOYMENT_TEST" else "\n请查看服务器维护日志并手动恢复。"
            page.get_by_label("输入正文", exact=True).fill(body)
            page.get_by_text("发送", exact=True).first.click()
            try:
                page.get_by_text("发送成功", exact=False).first.wait_for(timeout=5_000)
            except Error:
                sent = visible_text(page, "已发送")
                if sent is None:
                    raise LoginError("MAIL_SEND_UNCONFIRMED") from None
                sent.click()
                page.get_by_text(subject, exact=True).first.wait_for(timeout=20_000)
        finally:
            context.close()
