from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import maintain_cookie as maintenance
from server_config import load_config, prepare_config
from yuanbao_login import LoginError, UpstreamError


CONFIG = {"access_key": "test-key", "verify_link": "https://weixin.qq.com/sph/test"}


class ConfigTests(unittest.TestCase):
    def test_migration_keeps_key_and_cookie_but_removes_password_and_schedule(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "client.json"
            legacy.write_text(json.dumps({"access_key": "old-key"}))
            path = root / "config.json"
            prepare_config(path)
            self.assertEqual(load_config(path)["access_key"], "old-key")
            self.assertEqual(json.loads(legacy.read_text()), {"access_key": "old-key"})
            (root / "cookie").write_text("old-cookie")
            path.write_text(json.dumps({**CONFIG, "qq": {"password": "old-secret"}, "cookie_check_interval_hours": 24}))
            prepare_config(path)
            self.assertEqual(load_config(path), CONFIG)
            self.assertEqual(json.loads(path.read_text()), CONFIG)
            self.assertEqual((root / "cookie").read_text(), "old-cookie")

    def test_config_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            for field, value in (("verify_link", "https://example.com/"), ("access_key", 12), ("access_key", "非ASCII")):
                path.write_text(json.dumps({**CONFIG, field: value}))
                with self.assertRaises(ValueError):
                    load_config(path)


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "cookie").write_text("old-cookie")
        self.check = patch("maintain_cookie.check_cookie", return_value=False).start()
        self.status = patch("maintain_cookie.login_status", return_value="expired").start()
        self.acquire = patch("maintain_cookie.acquire_cookie", return_value="new-cookie").start()
        self.update = patch("maintain_cookie.update_cookie", return_value=True).start()
        self.addCleanup(patch.stopall)

    def test_valid_cookie_never_opens_browser_or_changes_file(self):
        self.check.return_value = True
        self.assertEqual(maintenance.maintain(CONFIG, self.root), "COOKIE_REUSED")
        self.acquire.assert_not_called()
        self.status.assert_not_called()
        self.update.assert_not_called()
        self.assertEqual((self.root / "cookie").read_text(), "old-cookie")

    def test_unknown_or_still_valid_login_does_not_trigger_qr(self):
        for status in ("unknown", "valid"):
            self.status.return_value = status
            self.assertEqual(maintenance.maintain(CONFIG, self.root), "COOKIE_OR_UPSTREAM_UNAVAILABLE")
        self.acquire.assert_not_called()
        self.assertEqual((self.root / "cookie").read_text(), "old-cookie")

    def test_expired_or_missing_cookie_validates_before_replacement(self):
        for present in (True, False):
            if not present:
                (self.root / "cookie").unlink()
            self.assertEqual(maintenance.maintain(CONFIG, self.root), "COOKIE_UPDATED")
        self.update.assert_called_with("new-cookie", CONFIG["verify_link"], path=self.root / "cookie", binary=self.root / "resolver")
        self.acquire.assert_called_with(self.root / ".runtime/server/wechat-qr.png")

    def test_failure_timeout_cancellation_and_network_failure_preserve_old_cookie(self):
        for error in (LoginError("WECHAT_SCAN_TIMEOUT"), LoginError("LOGIN_CANCELLED"),
                      LoginError("LOGIN_ADDITIONAL_VERIFICATION_REQUIRED"), UpstreamError("LOGIN_STATUS_UNKNOWN"),
                      RuntimeError("private-browser-error")):
            self.acquire.side_effect = error
            result = maintenance.maintain(CONFIG, self.root)
            self.assertNotIn("private", result)
            self.assertEqual((self.root / "cookie").read_text(), "old-cookie")
        self.update.assert_not_called()

    def test_failed_replacement_keeps_old_cookie_and_next_manual_run_can_retry(self):
        self.update.return_value = False
        self.assertEqual(maintenance.maintain(CONFIG, self.root), "NEW_COOKIE_VALIDATION_FAILED")
        self.assertEqual((self.root / "cookie").read_text(), "old-cookie")
        self.update.return_value = True
        self.assertEqual(maintenance.maintain(CONFIG, self.root), "COOKIE_UPDATED")
        self.assertFalse((self.root / ".runtime/server/maintenance.json").exists())


if __name__ == "__main__":
    unittest.main()
