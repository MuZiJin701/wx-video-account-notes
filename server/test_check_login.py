from __future__ import annotations

import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

import check_login as probe
from yuanbao_login import UpstreamError


CONFIG = {"access_key": "test-key", "verify_link": "https://weixin.qq.com/sph/test"}


class LoginCheckTests(unittest.TestCase):
    def test_checks_cookie_without_publishing_and_cleans_temporary_state(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)

            def acquire(qr_path):
                qr_path.write_text("qr-image")
                return "private-cookie"

            for valid in (True, False):
                with patch.object(probe, "acquire_cookie", side_effect=acquire), patch.object(probe, "check_cookie", return_value=valid) as check, io.StringIO() as output, redirect_stdout(output):
                    if valid:
                        self.assertEqual(probe.check_login(CONFIG, root), "YUANBAO_PARSE_OK")
                    else:
                        with self.assertRaisesRegex(UpstreamError, "YUANBAO_PARSE_FAILED"):
                            probe.check_login(CONFIG, root)
                    self.assertNotIn("private-cookie", output.getvalue())
                    self.assertEqual(check.call_args.args, ("private-cookie", CONFIG["verify_link"]))
                self.assertEqual(list(root.iterdir()), [])

    def test_cli_redacts_exception_and_rejects_invalid_config(self):
        with patch.object(sys, "argv", ["check_login.py", "--config", "unused"]), patch.object(probe, "load_config", return_value=CONFIG), patch.object(probe, "check_login", side_effect=RuntimeError("private-cookie")), io.StringIO() as output, redirect_stdout(output):
            self.assertEqual(probe.main(), 1)
            self.assertIn("WECHAT_CHECK_FAILED", output.getvalue())
            self.assertNotIn("private-cookie", output.getvalue())
        with patch.object(sys, "argv", ["check_login.py", "--config", "unused"]), patch.object(probe, "load_config", side_effect=ValueError("private-secret")), patch.object(probe, "check_login") as check, io.StringIO() as output, redirect_stdout(output):
            self.assertEqual(probe.main(), 1)
            check.assert_not_called()
            self.assertNotIn("private-secret", output.getvalue())


if __name__ == "__main__":
    unittest.main()
