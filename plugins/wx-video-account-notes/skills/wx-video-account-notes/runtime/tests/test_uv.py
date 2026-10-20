from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from runtime.platform import detect_platform, find_uv


class UvTests(unittest.TestCase):
    def test_system_version_selection_and_private_fallback(self):
        info = detect_platform("Linux", "x86_64")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            private = root / "uv/uv"
            private.parent.mkdir()
            private.touch()
            for version, status, expected in (("uv 0.13.3", 0, "/system/uv"), ("uv 0.11.25", 0, "/system/uv"),
                                               ("uv 0.1.0", 0, str(private)), ("uv 0.13.3", 1, str(private)),
                                               ("uv 0.13.3-beta", 0, str(private)), ("garbage", 0, str(private))):
                def run(args, **kwargs):
                    return SimpleNamespace(stdout=version if args[0] == "/system/uv" else "uv 0.11.25", returncode=status if args[0] == "/system/uv" else 0)
                with patch("runtime.platform.shutil.which", return_value="/system/uv"), patch("runtime.platform.subprocess.run", side_effect=run):
                    self.assertEqual(find_uv(root, info), Path(expected))

    @unittest.skipUnless(os.name == "posix", "POSIX launcher")
    def test_shell_prefers_system_and_reuses_private_for_missing_old_or_broken_system(self):
        scripts = Path(__file__).resolve().parents[2] / "scripts"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            (root / "bin").mkdir()
            shutil.copyfile(scripts / "common.sh", root / "scripts/common.sh")
            runner = root / "scripts/check.sh"
            runner.write_text('. "$(dirname "$0")/common.sh"\nensure_uv\nprintf "%s\\n" "$uv_command"\n')
            platform = "macos-x64" if os.uname().sysname == "Darwin" else "linux-x64"
            private = root / ".runtime" / platform / "uv/uv"
            private.parent.mkdir(parents=True)
            private.write_text('#!/bin/sh\necho "uv 0.11.25"\n')
            private.chmod(0o755)
            system = root / "bin/uv"
            for version, status in (("0.13.3", 0), ("0.1.0", 0), ("0.13.3", 1), (None, 0)):
                if version:
                    system.write_text(f'#!/bin/sh\necho "uv {version}"\nexit {status}\n')
                    system.chmod(0o755)
                else:
                    system.unlink()
                result = subprocess.run(["/bin/sh", str(runner)], env={**os.environ, "PATH": f"{root / 'bin'}:/usr/bin:/bin"}, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), str(system if version == "0.13.3" and status == 0 else private))

    @unittest.skipUnless(os.name == "nt", "Windows launcher")
    def test_powershell_prefers_system_and_falls_back_without_overwriting_it(self):
        common = Path(__file__).resolve().parents[2] / "scripts/common.ps1"
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            system = root / "uv.cmd"
            private = root / "private/uv/uv.exe"
            private.parent.mkdir(parents=True)
            private.touch()
            for version, expected in (("0.13.3", system), ("0.1.0", private)):
                system.write_text(f'@echo off\necho uv {version}\n')
                script = (f". '{common}'; function Get-RuntimeRoot {{ '{root / 'private'}' }}; "
                          "function Get-CommandVersionText([string]$FilePath) { if ($FilePath.EndsWith('uv.exe')) { 'uv 0.11.25' } else { & $FilePath --version } }; "
                          "Ensure-Uv")
                result = subprocess.run([powershell, "-NoProfile", "-Command", script], env={**os.environ, "PATH": str(root) + os.pathsep + os.environ["SystemRoot"] + "\\System32"}, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), str(expected))
                self.assertIn(version, system.read_text())


if __name__ == "__main__":
    unittest.main()
