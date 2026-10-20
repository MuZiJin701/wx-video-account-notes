from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, Mock, patch

from mail_notification import notify_error, open_mail
from yuanbao_login import LoginError


class MailTests(unittest.TestCase):
    def test_mandatory_verification_is_not_hidden_as_generic_mail_failure(self):
        context = Mock()
        context.pages = [Mock(frames=[Mock(name="ptlogin_iframe")])]
        context.pages[0].frames[0].name = "ptlogin_iframe"
        with patch("mail_notification.visible_text", return_value=None), patch("mail_notification.submit_qq_password", side_effect=LoginError("QQ_VERIFICATION_REQUIRED")):
            with self.assertRaisesRegex(LoginError, "^QQ_VERIFICATION_REQUIRED$"):
                open_mail(context, {})

    def test_alert_is_self_addressed_sanitized_and_sent_once_even_if_toast_is_missing(self):
        class BrowserError(Exception):
            pass

        api = ModuleType("playwright.sync_api")
        api.Error = BrowserError
        api.sync_playwright = MagicMock()
        browser = api.sync_playwright.return_value.__enter__.return_value
        context = browser.chromium.launch_persistent_context.return_value
        page = MagicMock()
        compose, sent = Mock(), Mock()
        fields = {name: Mock() for name in ("收件人", "主题", "输入正文")}
        page.get_by_label.side_effect = lambda name, **kwargs: fields[name]
        page.get_by_text.return_value.first.wait_for.side_effect = [BrowserError(), None]
        qq = {"account": "12345678", "password": "private-placeholder"}
        with tempfile.TemporaryDirectory() as directory, patch.dict(sys.modules, {"playwright": ModuleType("playwright"), "playwright.sync_api": api}), patch("mail_notification.open_mail", return_value=(page, compose)), patch("mail_notification.visible_text", return_value=sent):
            notify_error(qq, Path(directory) / "profile", "QQ_LOGIN_FLOW_FAILED")
        fields["收件人"].fill.assert_called_once_with("12345678@qq.com")
        self.assertNotIn(qq["password"], fields["输入正文"].fill.call_args.args[0])
        self.assertIn("QQ_LOGIN_FLOW_FAILED", fields["主题"].fill.call_args.args[0])
        page.get_by_text.return_value.first.click.assert_called_once()
        sent.click.assert_called_once()
        context.close.assert_called_once()

    def test_raw_errors_cannot_be_sent(self):
        with self.assertRaises(ValueError):
            notify_error({}, Path("unused"), "raw error with private data")


if __name__ == "__main__":
    unittest.main()
