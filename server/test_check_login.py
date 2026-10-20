from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import check_login as probe
from yuanbao_login import LoginError, UpstreamError


CONFIG = {"qq": {"account": "12345678", "password": "private-placeholder"},
          "verify_link": "https://weixin.qq.com/sph/test"}


class LoginCheckTests(unittest.TestCase):
    def test_yuanbao_checks_cookie_without_publishing_and_cleans_temporary_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def acquire(qq, profile, before):
                profile.mkdir()
                (profile / "private-session").write_text("private-cookie")
                before()
                return "private-cookie"

            for valid in (True, False):
                with patch.object(probe, "acquire_cookie", side_effect=acquire), patch.object(probe, "check_cookie", return_value=valid) as check, io.StringIO() as output, redirect_stdout(output):
                    if valid:
                        self.assertEqual(probe.check_login("yuanbao", CONFIG, root), "YUANBAO_PARSE_OK")
                    else:
                        with self.assertRaisesRegex(UpstreamError, "YUANBAO_PARSE_FAILED"):
                            probe.check_login("yuanbao", CONFIG, root)
                    self.assertNotIn("private-cookie", output.getvalue())
                    check.assert_called_once()
                    self.assertEqual(check.call_args.args, ("private-cookie", CONFIG["verify_link"]))
                self.assertEqual(list(root.iterdir()), [])

    def test_mail_only_opens_mail_and_closes_browser_even_on_failure(self):
        api = ModuleType("playwright.sync_api")
        api.sync_playwright = MagicMock()
        browser = api.sync_playwright.return_value.__enter__.return_value
        context = browser.chromium.launch_persistent_context.return_value
        for error in (None, LoginError("MAIL_LOGIN_FAILED")):
            context.reset_mock()
            page, compose = MagicMock(), MagicMock()
            with tempfile.TemporaryDirectory() as directory, patch.dict(sys.modules, {"playwright": ModuleType("playwright"), "playwright.sync_api": api}), patch.object(probe, "open_mail", side_effect=error, return_value=(page, compose)) as open_mail, patch("mail_notification.notify_error") as notify:
                root = Path(directory)
                if error:
                    with self.assertRaises(LoginError):
                        probe.check_login("mail", CONFIG, root)
                else:
                    self.assertEqual(probe.check_login("mail", CONFIG, root), "MAIL_LOGIN_OK")
                open_mail.assert_called_once_with(context, CONFIG["qq"])
                context.close.assert_called_once()
                compose.click.assert_not_called()
                self.assertEqual(page.mock_calls, [])
                notify.assert_not_called()
                self.assertEqual(list(root.iterdir()), [])

    def test_cli_does_not_log_browser_exception_or_run_on_invalid_config(self):
        with patch.object(sys, "argv", ["check_login.py", "mail", "--config", "unused"]), patch.object(probe, "load_config", return_value=CONFIG), patch.object(probe, "check_login", side_effect=RuntimeError("private-cookie")), io.StringIO() as output, redirect_stdout(output):
            self.assertEqual(probe.main(), 1)
            self.assertIn("MAIL_CHECK_FAILED", output.getvalue())
            self.assertNotIn("private-cookie", output.getvalue())
        with patch.object(sys, "argv", ["check_login.py", "yuanbao", "--config", "unused"]), patch.object(probe, "load_config", side_effect=ValueError("private-password")), patch.object(probe, "check_login") as check, io.StringIO() as output, redirect_stdout(output):
            self.assertEqual(probe.main(), 1)
            check.assert_not_called()
            self.assertNotIn("private-password", output.getvalue())


if __name__ == "__main__":
    unittest.main()
