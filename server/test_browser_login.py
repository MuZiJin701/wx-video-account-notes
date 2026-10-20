from __future__ import annotations

import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from yuanbao_login import LoginError, login_status, skip_optional_binding, submit_qq_password


class BrowserLoginTests(unittest.TestCase):
    def test_only_explicit_unauthenticated_response_triggers_login(self):
        self.assertEqual(login_status(""), "expired")
        for status, expected in ((401, "expired"), (403, "unknown"), (429, "unknown"), (500, "unknown")):
            error = HTTPError("https://yuanbao.tencent.com/api/getuserinfo", status, "", {}, None)
            with patch("yuanbao_login.urlopen", side_effect=error):
                self.assertEqual(login_status("placeholder"), expected)
        with patch("yuanbao_login.urlopen", side_effect=TimeoutError):
            self.assertEqual(login_status("placeholder"), "unknown")

    def test_optional_binding_only_clicks_the_named_skip_control(self):
        frame = Mock()
        skip = frame.get_by_text.return_value
        skip.count.return_value = 1
        skip.first.is_visible.return_value = True
        page = Mock(frames=[frame])
        self.assertTrue(skip_optional_binding(page))
        skip.first.click.assert_called_once()
        skip.first.is_visible.return_value = False
        self.assertFalse(skip_optional_binding(page))

    def test_credentials_are_not_filled_into_untrusted_frame(self):
        frame = Mock(url="https://xui.ptlogin2.qq.com.attacker.invalid/", **{"name": "ptlogin_iframe"})
        frame.name = "ptlogin_iframe"
        page = Mock(url="https://graph.qq.com/oauth2.0/show", frames=[frame])
        before_login = Mock()
        with self.assertRaises(LoginError):
            submit_qq_password(page, {"account": "12345678", "password": "test-only"}, before_login)
        before_login.assert_not_called()
        frame.get_by_role.assert_not_called()

    def test_waits_for_blank_login_frame_before_filling_credentials(self):
        frame = Mock(url="about:blank")
        frame.name = "ptlogin_iframe"
        page = Mock(url="https://graph.qq.com/oauth2.0/show", frames=[frame])
        page.wait_for_timeout.side_effect = lambda _: setattr(frame, "url", "https://xui.ptlogin2.qq.com/cgi-bin/xlogin")
        frame.evaluate.return_value = {"timeout": False, "verification": False}
        before_login = Mock()
        submit_qq_password(page, {"account": "12345678", "password": "test-only"}, before_login)
        before_login.assert_called_once()
        page.wait_for_timeout.assert_called_once()

    def test_progress_distinguishes_filling_failure_from_returned_click(self):
        frame = Mock(url="https://xui.ptlogin2.qq.com/cgi-bin/xlogin")
        frame.name = "ptlogin_iframe"
        frame.evaluate.return_value = {"timeout": False, "verification": False}
        page = Mock(url="https://graph.qq.com/oauth2.0/show", frames=[frame])
        stages = []
        progress = lambda stage, _: stages.append(stage)
        submit_qq_password(page, {"account": "12345678", "password": "test-only"}, Mock(), progress)
        self.assertEqual(stages, ["QQ_FRAME_READY", "PASSWORD_MODE_READY", "ACCOUNT_FILLED", "QQ_ACCOUNT_CHECK_PASSED",
                                  "PASSWORD_FILLED", "PASSWORD_CLICK_RETURNED"])
        stages.clear()
        frame.get_by_role.return_value.fill.side_effect = RuntimeError("private-browser-error")
        with self.assertRaises(RuntimeError):
            submit_qq_password(page, {"account": "12345678", "password": "test-only"}, Mock(), progress)
        self.assertEqual(stages, ["QQ_FRAME_READY", "PASSWORD_MODE_READY"])

    def test_mandatory_verification_and_check_failure_never_fill_or_submit_password(self):
        for check, code in (({"timeout": False, "verification": True}, "QQ_VERIFICATION_REQUIRED"),
                            ({"timeout": True, "verification": True}, "QQ_ACCOUNT_CHECK_TIMEOUT"),
                            (RuntimeError("private-browser-error"), "QQ_ACCOUNT_CHECK_FAILED")):
            frame = Mock(url="https://xui.ptlogin2.qq.com/cgi-bin/xlogin")
            frame.name = "ptlogin_iframe"
            account, password, login = Mock(), Mock(), Mock()
            frame.get_by_role.side_effect = lambda role, name, **_: password if name == "请输入密码" else login if role == "button" else account
            if isinstance(check, Exception):
                frame.wait_for_function.side_effect = check
            else:
                frame.evaluate.return_value = check
            before = Mock()
            with self.assertRaisesRegex(LoginError, "^" + code + "$"):
                submit_qq_password(Mock(url="https://graph.qq.com/", frames=[frame]),
                                   {"account": "12345678", "password": "private-placeholder"}, before)
            password.fill.assert_not_called()
            login.click.assert_not_called()
            before.assert_not_called()


if __name__ == "__main__":
    unittest.main()
