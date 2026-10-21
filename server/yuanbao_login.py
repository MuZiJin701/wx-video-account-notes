"""Operator-assisted WeChat QR login; never log private pages, URLs or Cookie."""

from __future__ import annotations

import base64
from collections import Counter
import math
from pathlib import Path
import re
import select
import shutil
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen


YUANBAO = "https://yuanbao.tencent.com/"
USER_INFO = YUANBAO + "api/getuserinfo"
PARSE_API = YUANBAO + "api/weixin/get_parse_result"
TERMS = "https://rule.tencent.com/rule/202403110001"
PRIVACY = "https://privacy.qq.com/document/preview/eb9be56572ab4886b6ca124e72abf413"


class LoginError(RuntimeError):
    pass


class UpstreamError(RuntimeError):
    pass


def login_status(cookie: str) -> str:
    if not cookie:
        return "expired"
    if len(cookie) > 16_384 or "\n" in cookie or "\r" in cookie:
        return "unknown"
    request = Request(USER_INFO, headers={"Cookie": cookie, "Referer": YUANBAO, "User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request, timeout=20) as response:
            return "valid" if response.status == 200 else "unknown"
    except HTTPError as error:
        error.close()
        return "expired" if error.code == 401 else "unknown"
    except (OSError, URLError, ValueError):
        return "unknown"


def terminal_qr(rows: list[list[bool]]) -> str:
    if not 21 <= len(rows) <= 1000 or any(len(row) != len(rows) for row in rows):
        raise LoginError("QR_IMAGE_INVALID")
    runs = Counter()
    for row in rows:
        start = 0
        for x in range(1, len(row) + 1):
            if x == len(row) or row[x] != row[start]:
                if row[start]:
                    runs[x - start] += 1
                start = x
    unit = math.gcd(*(length for length, count in runs.items() if count >= 3))
    if unit < 1 or len(rows) % unit or not 21 <= len(rows) // unit <= 110:
        raise LoginError("QR_MODULE_SCALE_UNRESOLVED")
    grid = [[row[x] for x in range(unit // 2, len(row), unit)] for row in rows[unit // 2::unit]]
    blank = [False] * (len(grid[0]) + 8)
    grid = [blank[:] for _ in range(4)] + [[False] * 4 + row + [False] * 4 for row in grid] + [blank[:] for _ in range(4)]
    if len(grid) % 2:
        grid.append(blank[:])
    chars = {(False, False): " ", (True, False): "▀", (False, True): "▄", (True, True): "█"}
    # Explicit colors preserve the quiet zone on both light and dark SSH terminals.
    return "\n".join("\033[30;107m" + "".join(chars[a, b] for a, b in zip(grid[y], grid[y + 1])) + "\033[0m"
                     for y in range(0, len(grid), 2))


def confirm_action(prompt: str, timeout: float) -> None:
    print(prompt + " 输入 yes 确认，其他输入取消：", end="", flush=True)
    if timeout <= 0 or not select.select([sys.stdin], [], [], timeout)[0]:
        raise LoginError("LOGIN_CONFIRM_TIMEOUT")
    if sys.stdin.readline().strip().lower() != "yes":
        raise LoginError("LOGIN_CANCELLED")


def show_qr(context, image, path: Path) -> None:
    source = urljoin("https://open.weixin.qq.com/", image.get_attribute("src") or "")
    parsed = urlsplit(source)
    if (parsed.scheme != "https" or parsed.hostname != "open.weixin.qq.com" or parsed.username
            or parsed.password or parsed.port not in (None, 443) or not parsed.path.startswith("/connect/qrcode/")):
        raise LoginError("WECHAT_QR_SOURCE_CHANGED")
    response = context.request.get(source, timeout=10_000)
    mime = response.headers.get("content-type", "").split(";")[0]
    data = response.body()
    if response.status != 200 or mime not in {"image/png", "image/jpeg"} or len(data) > 1_000_000:
        raise LoginError("WECHAT_QR_IMAGE_FAILED")
    decoder = context.new_page()
    try:
        rows = decoder.evaluate("""async uri => {
            const image = new Image(); image.src = uri; await image.decode();
            if (image.naturalWidth > 1000 || image.naturalHeight > 1000) throw Error('size');
            const canvas = document.createElement('canvas');
            canvas.width = image.naturalWidth; canvas.height = image.naturalHeight;
            const ctx = canvas.getContext('2d'); ctx.fillStyle = 'white';
            ctx.fillRect(0, 0, canvas.width, canvas.height); ctx.drawImage(image, 0, 0);
            const pixels = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
            return Array.from({length:canvas.height}, (_,y) =>
                Array.from({length:canvas.width}, (_,x) => {
                    const i = (y*canvas.width+x)*4;
                    return pixels[i]+pixels[i+1]+pixels[i+2] < 384;
                }));
        }""", "data:" + mime + ";base64," + base64.b64encode(data).decode("ascii"))
    finally:
        decoder.close()
    rendered = terminal_qr(rows)
    width = len(rendered.splitlines()[0].removeprefix("\033[30;107m").removesuffix("\033[0m"))
    if shutil.get_terminal_size().columns < width:
        raise LoginError("TERMINAL_TOO_NARROW")
    try:
        rendered.encode(sys.stdout.encoding or "utf-8")
    except UnicodeEncodeError:
        raise LoginError("TERMINAL_UTF8_REQUIRED") from None
    image.screenshot(path=str(path), timeout=5000)
    path.chmod(0o600)
    print("WECHAT_QR_READY: 请用微信扫码并在手机确认；等待最多 3 分钟。", flush=True)
    print(rendered, flush=True)
    print("辅助图片：" + str(path) + "（命令结束后删除）", flush=True)


def wait_for_login(context, page, qr_path: Path, timeout: float = 180) -> str:
    deadline = time.monotonic() + timeout
    displayed = ""
    last_check = 0.0
    confirmed_registration = False
    verification = False

    def response_received(response):
        nonlocal verification
        parsed = urlsplit(response.url)
        if parsed.hostname == "yuanbao.tencent.com" and parsed.path == "/api/joint/login" and response.status >= 400:
            try:
                value = response.json()
                verification = bool(value.get("safeVerifyTypes"))
            except Exception:
                pass

    page.on("response", response_received)
    while time.monotonic() < deadline:
        if page.is_closed():
            raise LoginError("LOGIN_CANCELLED")
        if verification:
            raise LoginError("LOGIN_ADDITIONAL_VERIFICATION_REQUIRED")
        now = time.monotonic()
        if urlsplit(page.url).hostname == "yuanbao.tencent.com" and now - last_check >= 2:
            status = context.request.get(USER_INFO, timeout=5000).status
            last_check = time.monotonic()
            if status == 200:
                cookie = "; ".join(f"{item['name']}={item['value']}" for item in context.cookies([PARSE_API]))
                if not cookie:
                    raise LoginError("LOGIN_COOKIE_MISSING")
                return cookie
            if status != 401:
                raise UpstreamError("LOGIN_STATUS_UNKNOWN")
        for frame in page.frames:
            host = urlsplit(frame.url).hostname or ""
            if any(host == suffix or host.endswith("." + suffix) for suffix in ("captcha.qq.com", "captcha.qcloud.com")):
                if frame.frame_element().is_visible():
                    raise LoginError("LOGIN_ADDITIONAL_VERIFICATION_REQUIRED")
            if host != "open.weixin.qq.com":
                continue
            if frame.locator(".js_wx_after_cancel:visible").count():
                raise LoginError("LOGIN_CANCELLED")
            image = frame.locator("img.qrcode.js_qrcode_img:visible").first
            if image.count() and image.evaluate("el => el.complete && el.naturalWidth > 50"):
                source = image.get_attribute("src")
                if source != displayed:
                    show_qr(context, image, qr_path)
                    displayed = source
            expired = frame.get_by_text(re.compile(r"二维码已(?:过期|失效)|二维码过期"))
            if any(item.is_visible() for item in expired.all()):
                refresh = frame.locator(".js_refresh_qrcode:visible, .js_web_qrcode_reload:visible").first
                if not refresh.count():
                    raise LoginError("WECHAT_QR_EXPIRED")
                refresh.click(timeout=3000)
                displayed = ""
                print("WECHAT_QR_REFRESHED", flush=True)
        registration = page.get_by_role("button", name=re.compile(r"^(同意并注册|注册并登录|同意并登录)$"))
        if registration.count() and registration.first.is_visible():
            if confirmed_registration:
                raise LoginError("LOGIN_PAGE_CHANGED")
            confirm_action("元宝要求确认协议并注册/登录账号，是否继续？", deadline - time.monotonic())
            registration.first.click(timeout=5000)
            confirmed_registration = True
        binding = page.get_by_text(re.compile(r"^跳过[，,、\s]*直接登录$"))
        if binding.count() and binding.first.is_visible():
            binding.first.click(timeout=3000)
        page.wait_for_timeout(250)
    raise LoginError("WECHAT_SCAN_TIMEOUT")


def acquire_cookie(qr_path: Path) -> str:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise LoginError("INTERACTIVE_TERMINAL_REQUIRED")
    print("微信扫码可能创建元宝账号；网页注明扫码即同意以下协议。")
    print("用户服务协议：" + TERMS + "\n隐私协议：" + PRIVACY)
    confirm_action("是否已阅读并同意协议，继续微信扫码登录/注册？", 180)
    from playwright.sync_api import Error, sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chromium", headless=True)
        try:
            context = browser.new_context(locale="zh-CN")
            page = context.new_page()
            page.set_default_timeout(5000)
            page.goto(YUANBAO, wait_until="domcontentloaded", timeout=45_000)
            try:
                page.get_by_text("微信登录", exact=True).wait_for(timeout=5000)
            except Error:
                page.get_by_role("button", name="登录", exact=True).click()
                page.get_by_text("微信", exact=True).click()
            for name, expected in (("用户服务协议", TERMS), ("隐私协议", PRIVACY)):
                if page.get_by_role("link", name=name, exact=True).get_attribute("href") != expected:
                    raise LoginError("LOGIN_TERMS_CHANGED")
            return wait_for_login(context, page, qr_path)
        except Error:
            raise LoginError("WECHAT_LOGIN_FLOW_FAILED") from None
        finally:
            try:
                browser.close()
            finally:
                qr_path.unlink(missing_ok=True)
