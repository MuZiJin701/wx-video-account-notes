from __future__ import annotations

import os
import json
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


@unittest.skipUnless(sys.platform == "linux", "Linux installer")
class InstallTests(unittest.TestCase):
    def test_install_preserves_cookie_key_and_removes_automatic_maintenance(self) -> None:
        source = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "server").mkdir()
            (root / "units").mkdir()
            (root / "bin").mkdir()
            files = ("gateway.py", "update_cookie.py", "server_config.py", "yuanbao_login.py", "maintain_cookie.py", "pyproject.toml", "uv.lock", "wx-notes-resolver.service", "wx-notes-gateway.service")
            for name in files:
                shutil.copyfile(source / name, root / "server" / name)
            (root / "server/resolver-linux-amd64").write_text("new resolver")
            (root / "resolver").write_text("old resolver")
            for name in ("client.json", "cookie"):
                (root / name).write_text("private-placeholder")
            config = {"access_key": "kept-key", "qq": {"account": "12345678", "password": "test-only"}, "cookie_check_interval_hours": 6}
            (root / "config.json").write_text(json.dumps(config))
            for name in ("wx-notes-cookie.timer", "wx-notes-cookie.service"):
                (root / "units" / name).write_text("legacy maintenance")
            (root / "mail_notification.py").write_text("legacy mail")
            scripts = root / "plugins/wx-video-account-notes/skills/wx-video-account-notes/scripts"
            scripts.mkdir(parents=True)
            (scripts / "ensure_uv.sh").write_text('printf "%s\\n" "' + str(root / "bin/uv") + '"\n')
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
                "systemctl": 'if [ "$1" = cat ]; then test -f "$INSTALL_UNITS/$2"; else printf "%s\\n" "$*" >> "$INSTALL_CALLS"; fi',
                "uv": 'mkdir -p "$UV_PROJECT_ENVIRONMENT/bin"\nprintf "#!/bin/sh\\nexit 0\\n" > "$UV_PROJECT_ENVIRONMENT/bin/python"\nchmod +x "$UV_PROJECT_ENVIRONMENT/bin/python"',
            }
            for name, body in commands.items():
                command = root / "bin" / name
                command.write_text("#!/bin/sh\n" + body + "\n")
                command.chmod(0o755)
            env = {**os.environ, "PATH": f"{root / 'bin'}:/usr/bin:/bin", "INSTALL_CALLS": str(root / "calls"), "INSTALL_UNITS": str(root / "units")}
            for _ in range(2):
                result = subprocess.run(["sh", str(installer)], env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            expected_calls = ["disable --now wx-notes-cookie.timer", "stop wx-notes-cookie.service", "daemon-reload", "daemon-reload"]
            self.assertEqual((root / "calls").read_text().splitlines(), expected_calls)
            self.assertEqual(json.loads((root / "config.json").read_text())["access_key"], "kept-key")
            self.assertNotIn("qq", json.loads((root / "config.json").read_text()))
            self.assertNotIn("cookie_check_interval_hours", json.loads((root / "config.json").read_text()))
            self.assertFalse((root / "mail_notification.py").exists())
            self.assertEqual(stat.S_IMODE((root / "config.json").stat().st_mode), 0o600)
            self.assertEqual((root / "resolver").read_text(), "new resolver")
            self.assertFalse((root / "resolver.new").exists())
            self.assertEqual(stat.S_IMODE(root.stat().st_mode), 0o700)
            for name in ("client.json", "cookie"):
                self.assertEqual((root / name).read_text(), "private-placeholder")
                self.assertEqual(stat.S_IMODE((root / name).stat().st_mode), 0o600)
            for name in ("wx-notes-resolver.service", "wx-notes-gateway.service"):
                self.assertEqual((root / "units" / name).read_bytes(), (source / name).read_bytes())
            self.assertFalse((root / "units/wx-notes-cookie.timer").exists())
            self.assertFalse((root / "units/wx-notes-cookie.service").exists())
            (root / "server/wx-notes-gateway.service").unlink()
            result = subprocess.run(["sh", str(installer)], env=env, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual((root / "calls").read_text().splitlines(), expected_calls)
            self.assertEqual((root / "cookie").read_text(), "private-placeholder")


if __name__ == "__main__":
    unittest.main()
