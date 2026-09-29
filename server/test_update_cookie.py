from __future__ import annotations

import io
import os
import runpy
import stat
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from update_cookie import update_cookie


class UpdateCookieTests(unittest.TestCase):
    def test_success_replaces_cookie_without_echo(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cookie"
            path.write_text("old-placeholder", encoding="utf-8")
            output = io.StringIO()
            with (
                patch("update_cookie.subprocess.run", return_value=SimpleNamespace(returncode=0)) as run,
                redirect_stdout(output),
            ):
                self.assertTrue(update_cookie("new-placeholder", "https://weixin.qq.com/sph/test", path=path))
            self.assertEqual(path.read_text(encoding="utf-8"), "new-placeholder")
            if os.name == "posix":
                self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(run.call_args.kwargs["input"], "new-placeholder")
            self.assertEqual(output.getvalue(), "")
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_failed_check_preserves_previous_cookie(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cookie"
            path.write_text("old-placeholder", encoding="utf-8")
            with patch("update_cookie.subprocess.run", return_value=SimpleNamespace(returncode=1)):
                self.assertFalse(update_cookie("bad-placeholder", "https://weixin.qq.com/sph/test", path=path))
            self.assertEqual(path.read_text(encoding="utf-8"), "old-placeholder")
            self.assertEqual(list(Path(directory).iterdir()), [path])

    def test_interactive_failure_exits_nonzero_without_echo(self) -> None:
        output = io.StringIO()
        with (
            patch("builtins.input", side_effect=AssertionError("unexpected link prompt")),
            patch("getpass.getpass", return_value="private-placeholder"),
            patch("subprocess.run", return_value=SimpleNamespace(returncode=1)) as run,
            patch.dict("os.environ", {"WX_NOTES_VERIFY_LINK": "https://weixin.qq.com/sph/test"}),
            redirect_stdout(output),
        ):
            with self.assertRaises(SystemExit) as stopped:
                runpy.run_path(str(Path(__file__).with_name("update_cookie.py")), run_name="__main__")
        self.assertEqual(stopped.exception.code, 1)
        self.assertEqual(run.call_args.args[0][-1], "https://weixin.qq.com/sph/test")
        self.assertNotIn("private-placeholder", output.getvalue())


if __name__ == "__main__":
    unittest.main()
