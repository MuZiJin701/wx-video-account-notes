from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import maintain_cookie as maintenance
from server_config import load_config, prepare_config
from yuanbao_login import LoginError, UpstreamError


CONFIG = {"access_key": "test-key", "qq": {"account": "12345678", "password": "test-only"},
          "verify_link": "https://weixin.qq.com/sph/test", "cookie_check_interval_hours": 24}


class ConfigTests(unittest.TestCase):
    def test_migration_keeps_old_key_and_original_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "client.json"
            legacy.write_text(json.dumps({"access_key": "old-key"}))
            path = root / "config.json"
            with self.assertRaisesRegex(ValueError, "QQ_ACCOUNT"):
                prepare_config(path)
            self.assertEqual(json.loads(path.read_text())["access_key"], "old-key")
            self.assertEqual(json.loads(legacy.read_text()), {"access_key": "old-key"})

    def test_config_validation_preserves_valid_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(CONFIG))
            prepare_config(path)
            self.assertEqual(load_config(path), CONFIG)
            for field, value in (("cookie_check_interval_hours", True), ("verify_link", "https://example.com/"), ("access_key", 12), ("access_key", "非ASCII")):
                path.write_text(json.dumps({**CONFIG, field: value}))
                with self.assertRaises(ValueError):
                    load_config(path)


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "cookie").write_text("old-cookie")
        self.state_path = self.root / ".runtime/server/maintenance.json"
        self.check = patch("maintain_cookie.check_cookie", return_value=False).start()
        self.status = patch("maintain_cookie.login_status", return_value="expired").start()
        self.acquire = patch("maintain_cookie.acquire_cookie", return_value="new-cookie").start()
        self.update = patch("maintain_cookie.update_cookie", return_value=True).start()
        self.notify = patch("mail_notification.notify_error").start()
        patch("maintain_cookie.print", create=True).start()
        self.addCleanup(patch.stopall)

    def test_valid_cookie_never_opens_browser(self):
        self.check.return_value = True
        self.assertEqual(maintenance.maintain(CONFIG, self.root), "COOKIE_REUSED")
        self.acquire.assert_not_called()
        self.status.assert_not_called()
        self.notify.assert_not_called()

    def test_upstream_failure_preserves_cookie_and_deduplicates_notification(self):
        self.status.return_value = "unknown"
        for _ in range(2):
            self.assertEqual(maintenance.maintain(CONFIG, self.root), "COOKIE_OR_UPSTREAM_UNAVAILABLE")
        self.assertEqual((self.root / "cookie").read_text(), "old-cookie")
        self.acquire.assert_not_called()
        self.notify.assert_called_once()

    def test_expired_cookie_validates_before_replacement(self):
        self.assertEqual(maintenance.maintain(CONFIG, self.root), "COOKIE_UPDATED")
        self.update.assert_called_once_with("new-cookie", CONFIG["verify_link"], path=self.root / "cookie", binary=self.root / "resolver")
        self.assertFalse(json.loads(self.state_path.read_text())["paused"])

    def test_login_failure_suspends_password_attempts_until_resume(self):
        self.acquire.side_effect = LoginError("QQ_LOGIN_FLOW_FAILED")
        self.assertEqual(maintenance.maintain(CONFIG, self.root), "QQ_LOGIN_FLOW_FAILED")
        self.assertEqual(maintenance.maintain(CONFIG, self.root), "LOGIN_RETRY_PAUSED")
        self.assertEqual(self.acquire.call_count, 1)
        self.notify.assert_called_once()
        self.acquire.side_effect = None
        self.assertEqual(maintenance.maintain(CONFIG, self.root, resume=True), "COOKIE_UPDATED")

    def test_failed_replacement_keeps_old_cookie_and_paused_attempt(self):
        def acquire(_qq, _profile, before_login):
            before_login()
            return "new-cookie"
        self.acquire.side_effect = acquire
        self.update.return_value = False
        self.assertEqual(maintenance.maintain(CONFIG, self.root), "NEW_COOKIE_VALIDATION_FAILED")
        self.assertEqual((self.root / "cookie").read_text(), "old-cookie")
        self.assertTrue(json.loads(self.state_path.read_text())["paused"])

    def test_mail_failure_does_not_repeat_send_or_escape(self):
        self.notify.side_effect = RuntimeError("private-placeholder")
        self.status.return_value = "unknown"
        for _ in range(2):
            self.assertEqual(maintenance.maintain(CONFIG, self.root), "COOKIE_OR_UPSTREAM_UNAVAILABLE")
        self.notify.assert_called_once()

    def test_alternating_errors_do_not_repeat_previous_unresolved_alert(self):
        self.status.side_effect = ["unknown", "expired", "unknown"]
        self.acquire.side_effect = UpstreamError("BROWSER_NETWORK_ERROR")
        for _ in range(3):
            maintenance.maintain(CONFIG, self.root)
        self.assertEqual(self.notify.call_count, 2)


if __name__ == "__main__":
    unittest.main()
