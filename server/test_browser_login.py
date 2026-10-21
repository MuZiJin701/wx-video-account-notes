from __future__ import annotations

import io
from pathlib import Path
import re
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch
from urllib.error import HTTPError

import yuanbao_login as login


class BrowserLoginTests(unittest.TestCase):
    def test_only_explicit_expiry_triggers_login(self):
        self.assertEqual(login.login_status(""), "expired")
        for status, expected in ((401, "expired"), (403, "unknown"), (429, "unknown"), (500, "unknown")):
            error = HTTPError(login.USER_INFO, status, "", {}, None)
            with patch.object(login, "urlopen", side_effect=error):
                self.assertEqual(login.login_status("placeholder"), expected)
        with patch.object(login, "urlopen", side_effect=TimeoutError):
            self.assertEqual(login.login_status("placeholder"), "unknown")
        with patch.object(login, "urlopen") as request:
            self.assertEqual(login.login_status("bad\nheader"), "unknown")
            request.assert_not_called()

    def test_terminal_qr_preserves_modules_quiet_zone_and_colors(self):
        grid = [[((x * 3 + y * 5) % 7) < 3 for x in range(21)] for y in range(21)]
        pixels = [[cell for cell in row for _ in range(10)] for row in grid for _ in range(10)]
        rendered = login.terminal_qr(pixels)
        reverse = {" ": (False, False), "▀": (True, False), "▄": (False, True), "█": (True, True)}
        decoded = []
        for line in rendered.splitlines():
            self.assertTrue(line.startswith("\033[30;107m") and line.endswith("\033[0m"))
            pairs = [reverse[char] for char in re.sub(r"\x1b\[[0-9;]*m", "", line)]
            decoded.extend([[pair[0] for pair in pairs], [pair[1] for pair in pairs]])
        self.assertEqual([row[4:-4] for row in decoded[4:25]], grid)
        self.assertTrue(all(not cell for row in decoded[:4] for cell in row))
        for invalid in ([], [[True] * 20] * 21, [[False] * 21] * 21):
            with self.assertRaises(login.LoginError):
                login.terminal_qr(invalid)

    def page(self):
        page = Mock(url=login.YUANBAO, frames=[])
        page.is_closed.return_value = False
        page.get_by_role.return_value.count.return_value = 0
        page.get_by_text.return_value.count.return_value = 0
        clock = SimpleNamespace(now=100.0)
        page.wait_for_timeout.side_effect = lambda ms: setattr(clock, "now", clock.now + ms / 1000)
        return page, clock

    def test_waits_for_real_userinfo_success_and_scopes_cookie_to_parse_url(self):
        page, clock = self.page()
        context = Mock()
        context.request.get.side_effect = [Mock(status=401), Mock(status=200)]
        context.cookies.return_value = [{"name": "hy_token", "value": "private-value"}]
        with patch.object(login.time, "monotonic", side_effect=lambda: clock.now):
            self.assertEqual(login.wait_for_login(context, page, Path("unused"), 3), "hy_token=private-value")
        context.cookies.assert_called_once_with([login.PARSE_API])

    def test_refresh_does_not_extend_scan_deadline(self):
        page, clock = self.page()
        context = Mock()
        context.request.get.return_value.status = 401
        frame = Mock(url="https://open.weixin.qq.com/connect/qrconnect")
        page.frames = [frame]
        missing, image, refresh, expired = Mock(), Mock(), Mock(), Mock()
        missing.count.return_value = 0
        image.first = image
        image.count.return_value = 1
        image.evaluate.return_value = True
        image.get_attribute.return_value = "old-private-source"
        refresh.first = refresh
        refresh.count.return_value = 1
        frame.locator.side_effect = lambda selector: image if selector.startswith("img.") else refresh if "js_refresh_qrcode" in selector else missing
        expired.is_visible.return_value = True
        frame.get_by_text.return_value.all.side_effect = [[expired], [], [], []]
        refresh.click.side_effect = lambda **_: setattr(image.get_attribute, "return_value", "new-private-source")
        with patch.object(login.time, "monotonic", side_effect=lambda: clock.now), patch.object(login, "show_qr") as show, patch("builtins.print"):
            with self.assertRaisesRegex(login.LoginError, "^WECHAT_SCAN_TIMEOUT$"):
                login.wait_for_login(context, page, Path("unused"), 1)
        self.assertEqual(show.call_count, 2)
        refresh.click.assert_called_once()
        self.assertLessEqual(clock.now, 101.25)
        context.cookies.assert_not_called()

    def test_safe_verification_stops_without_answer_or_cookie(self):
        page, clock = self.page()
        context = Mock()
        context.request.get.return_value.status = 401
        callbacks = {}
        page.on.side_effect = lambda name, callback: callbacks.__setitem__(name, callback)
        response = Mock(url=login.YUANBAO + "api/joint/login", status=400)
        response.json.return_value = {"safeVerifyTypes": ["waterProof"], "safeVerifyCode": "private"}

        def wait(ms):
            clock.now += ms / 1000
            callbacks["response"](response)

        page.wait_for_timeout.side_effect = wait
        with patch.object(login.time, "monotonic", side_effect=lambda: clock.now):
            with self.assertRaisesRegex(login.LoginError, "LOGIN_ADDITIONAL_VERIFICATION_REQUIRED"):
                login.wait_for_login(context, page, Path("unused"), 3)
        context.cookies.assert_not_called()
        context.request.post.assert_not_called()

    def test_qr_source_cannot_request_external_or_plain_http_url(self):
        for source in ("https://open.weixin.qq.com.attacker.invalid/connect/qrcode/x",
                       "http://open.weixin.qq.com/connect/qrcode/x", "https://u:p@open.weixin.qq.com/connect/qrcode/x"):
            context, image = Mock(), Mock()
            image.get_attribute.return_value = source
            with self.assertRaisesRegex(login.LoginError, "WECHAT_QR_SOURCE_CHANGED"):
                login.show_qr(context, image, Path("unused"))
            context.request.get.assert_not_called()

    def test_registration_needs_terminal_confirmation_before_click(self):
        for accepted in (True, False):
            page, clock = self.page()
            context = Mock()
            context.request.get.side_effect = [Mock(status=401), Mock(status=200)]
            context.cookies.return_value = [{"name": "token", "value": "candidate"}]
            registration = page.get_by_role.return_value
            registration.count.return_value = 1
            registration.first.is_visible.return_value = True
            registration.first.click.side_effect = lambda **_: setattr(registration.count, "return_value", 0)
            with patch.object(login.time, "monotonic", side_effect=lambda: clock.now), patch.object(login, "confirm_action", side_effect=None if accepted else login.LoginError("LOGIN_CANCELLED")) as confirm:
                if accepted:
                    self.assertEqual(login.wait_for_login(context, page, Path("unused"), 3), "token=candidate")
                    registration.first.click.assert_called_once()
                else:
                    with self.assertRaisesRegex(login.LoginError, "LOGIN_CANCELLED"):
                        login.wait_for_login(context, page, Path("unused"), 3)
                    registration.first.click.assert_not_called()
                    context.cookies.assert_not_called()
                confirm.assert_called_once()

    def test_browser_and_qr_are_cleaned_on_success_failure_and_interrupt(self):
        api = ModuleType("playwright.sync_api")

        class BrowserError(Exception):
            pass

        api.Error = BrowserError
        api.sync_playwright = MagicMock()
        browser = api.sync_playwright.return_value.__enter__.return_value.chromium.launch.return_value
        page = browser.new_context.return_value.new_page.return_value
        page.get_by_role.side_effect = lambda role, name, **_: Mock(**{"get_attribute.return_value": login.TERMS if name == "用户服务协议" else login.PRIVACY})
        for error in (None, login.LoginError("WECHAT_SCAN_TIMEOUT"), KeyboardInterrupt()):
            browser.reset_mock()
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "qr.png"
                path.write_text("temporary qr")
                with patch.dict(sys.modules, {"playwright": ModuleType("playwright"), "playwright.sync_api": api}), patch.object(login.sys.stdin, "isatty", return_value=True), patch.object(login.sys.stdout, "isatty", return_value=True), patch.object(login, "confirm_action"), patch.object(login, "wait_for_login", return_value="candidate", side_effect=error), patch("builtins.print"):
                    if error is None:
                        self.assertEqual(login.acquire_cookie(path), "candidate")
                    else:
                        with self.assertRaises(type(error)):
                            login.acquire_cookie(path)
                browser.close.assert_called_once()
                self.assertFalse(path.exists())

    def test_confirmation_requires_explicit_yes_and_honors_timeout(self):
        for ready, answer, expected in ((True, "yes\n", None), (True, "no\n", "LOGIN_CANCELLED"),
                                        (False, "", "LOGIN_CONFIRM_TIMEOUT")):
            with patch.object(login.select, "select", return_value=([1] if ready else [], [], [])), patch.object(login.sys, "stdin", io.StringIO(answer)), patch("builtins.print"):
                if expected:
                    with self.assertRaisesRegex(login.LoginError, expected):
                        login.confirm_action("confirm", 1)
                else:
                    login.confirm_action("confirm", 1)


if __name__ == "__main__":
    unittest.main()
