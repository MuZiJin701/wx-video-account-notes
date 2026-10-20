from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(sys.platform == "linux", "Linux installer")
class InstallTests(unittest.TestCase):
    def test_install_preserves_secrets_and_only_reloads_systemd(self) -> None:
        source = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "server").mkdir()
            (root / "units").mkdir()
            (root / "bin").mkdir()
            for name in ("gateway.py", "update_cookie.py", "wx-notes-resolver.service", "wx-notes-gateway.service"):
                shutil.copyfile(source / name, root / "server" / name)
            (root / "server/resolver-linux-amd64").write_text("new resolver")
            (root / "resolver").write_text("old resolver")
            for name in ("client.json", "cookie"):
                (root / name).write_text("private-placeholder")
            # Isolate fixed deployment paths and privileged commands from the real host.
            script = (source / "install.sh").read_text().replace(
                "/root/projects/wx-video-account-notes", str(root)
            ).replace("/etc/systemd/system", str(root / "units"))
            installer = root / "install.sh"
            installer.write_text(script)
            commands = {
                "id": "echo 0",
                "chown": ":",
                "install": 'shift 4; exec /usr/bin/install "$@"',
                "systemctl": 'printf "%s\\n" "$*" >> "$INSTALL_CALLS"',
            }
            for name, body in commands.items():
                command = root / "bin" / name
                command.write_text("#!/bin/sh\n" + body + "\n")
                command.chmod(0o755)
            env = {**os.environ, "PATH": f"{root / 'bin'}:/usr/bin:/bin", "INSTALL_CALLS": str(root / "calls")}
            for _ in range(2):
                result = subprocess.run(["sh", str(installer)], env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual((root / "calls").read_text().splitlines(), ["daemon-reload"] * 2)
            self.assertEqual((root / "resolver").read_text(), "new resolver")
            self.assertFalse((root / "resolver.new").exists())
            self.assertEqual(stat.S_IMODE(root.stat().st_mode), 0o700)
            for name in ("client.json", "cookie"):
                self.assertEqual((root / name).read_text(), "private-placeholder")
                self.assertEqual(stat.S_IMODE((root / name).stat().st_mode), 0o600)
            for name in ("wx-notes-resolver.service", "wx-notes-gateway.service"):
                self.assertEqual((root / "units" / name).read_bytes(), (source / name).read_bytes())
            (root / "server/wx-notes-gateway.service").unlink()
            result = subprocess.run(["sh", str(installer)], env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((root / "calls").read_text().splitlines(), ["daemon-reload"] * 2)
            self.assertEqual((root / "cookie").read_text(), "private-placeholder")


if __name__ == "__main__":
    unittest.main()
