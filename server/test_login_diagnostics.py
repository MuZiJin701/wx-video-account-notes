from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import Mock

from login_diagnostics import report_login, site


class LoginDiagnosticsTests(unittest.TestCase):
    def test_captcha_frame_origins_are_classified_without_trusting_lookalikes(self):
        for host in ("captcha.gtimg.com", "turing.captcha.qcloud.com", "t.captcha.qq.com"):
            self.assertEqual(site("https://" + host + "/?private-token"), "CAPTCHA")
        self.assertEqual(site("https://captcha.gtimg.com.attacker.invalid/"), "OTHER")

    def test_only_site_classes_and_fixed_signals_escape_private_pages(self):
        frame = Mock(url="https://t.captcha.qq.com/?private-token")
        frame.name = "captcha"
        item = Mock()
        item.is_visible.return_value = True
        frame.get_by_text.side_effect = lambda regex: Mock(all=lambda: [item] if regex.search("安全验证") else [])
        frame.get_by_role.return_value.all.return_value = []
        frame.locator.return_value.all.return_value = []
        page = Mock(url="https://graph.qq.com/?private-account", frames=[frame])
        with io.StringIO() as output, redirect_stdout(output):
            report_login("FAILED", page)
            result = output.getvalue()
        self.assertIn('"site": "QQ_AUTH"', result)
        self.assertIn('"CAPTCHA"', result)
        self.assertIn('"VERIFICATION"', result)
        self.assertNotIn("private", result)
        self.assertNotIn("https", result)
        self.assertEqual(site("https://xui.ptlogin2.qq.com.attacker.invalid/"), "OTHER")

    def test_network_and_detached_frame_errors_never_emit_raw_details(self):
        frame = Mock(url="https://unknown.invalid/private-cookie")
        frame.name = "ptlogin_iframe"
        frame.evaluate.return_value = {"needVc": True, "checkRet": "private-browser-error"}
        frame.get_by_text.side_effect = RuntimeError("private-browser-error")
        frame.locator.return_value.all.return_value = []
        page = Mock(url="https://mail.qq.com/?private-token", frames=[frame])
        callbacks = {}
        page.on.side_effect = lambda name, callback: callbacks.update({name: callback})
        with io.StringIO() as output, redirect_stdout(output):
            report_login("BROWSER_READY", page)
            callbacks["requestfailed"](Mock(url="https://xui.ptlogin2.qq.com/?private-token", failure="private-error"))
            callbacks["requestfailed"](Mock(url="https://xui.ptlogin2.qq.com/?private-token", failure="net::ERR_CONNECTION_RESET"))
            callbacks["requestfailed"](Mock(url="https://localhost.ptlogin2.qq.com:4301/private", failure="net::ERR_CONNECTION_REFUSED"))
            callbacks["response"](Mock(url="https://graph.qq.com/?private-token", status=403))
            callbacks["response"](Mock(url="https://unknown.invalid/?private-token", status=500))
            callbacks["response"](Mock(url="https://ssl.ptlogin2.qq.com/ssl/login?private-token", status=200,
                                        text=lambda: "ptuiCB('4','0','private-url','0','private-account')"))
            report_login("FAILED", page)
            result = output.getvalue()
        self.assertIn("LOGIN_NETWORK_FAILED QQ_LOGIN", result)
        self.assertIn("net::ERR_CONNECTION_RESET", result)
        self.assertNotIn("ERR_CONNECTION_REFUSED", result)
        self.assertIn("LOGIN_QQ_RESULT LOGIN 4", result)
        self.assertIn("LOGIN_HTTP QQ_AUTH 403", result)
        self.assertIn("FRAME_UNAVAILABLE", result)
        self.assertIn('"needVc": true', result)
        self.assertNotIn("private", result)
        self.assertNotIn("500", result)


if __name__ == "__main__":
    unittest.main()
