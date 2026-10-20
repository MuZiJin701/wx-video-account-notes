#!/bin/sh
set -eu
test "$(uname -s):$(uname -m)" = Linux:x86_64

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root" >&2
  exit 1
fi

root=/root/projects/wx-video-account-notes
cd "$root"
command -v systemctl >/dev/null
test -x /usr/bin/python3
for file in resolver-linux-amd64 gateway.py update_cookie.py server_config.py yuanbao_login.py maintain_cookie.py mail_notification.py pyproject.toml uv.lock wx-notes-resolver.service wx-notes-gateway.service wx-notes-cookie.service wx-notes-cookie.timer; do
  test -s "server/$file"
done
chown root:root "$root"
chmod 0700 "$root"
umask 077
interval=$(/usr/bin/python3 server/server_config.py "$root/config.json")
chown root:root config.json
chmod 0600 config.json
if [ -f client.json ]; then
  chown root:root client.json
  chmod 0600 client.json
fi
if [ -f cookie ]; then
  chown root:root cookie
  chmod 0600 cookie
fi
uv_command=$(sh plugins/wx-video-account-notes/skills/wx-video-account-notes/scripts/ensure_uv.sh)
export UV_PROJECT_ENVIRONMENT="$root/.runtime/server/.venv"
export UV_PYTHON_INSTALL_DIR="$root/.runtime/server/python"
export PLAYWRIGHT_BROWSERS_PATH="$root/.runtime/server/browsers"
"$uv_command" sync --locked --project server --python 3.13.14
"$UV_PROJECT_ENVIRONMENT/bin/python" -m playwright install --with-deps --no-shell chromium
install -o root -g root -m 0644 server/gateway.py "$root/gateway.py"
install -o root -g root -m 0700 server/update_cookie.py "$root/update_cookie.py"
for file in server_config.py yuanbao_login.py maintain_cookie.py mail_notification.py; do
  install -o root -g root -m 0600 "server/$file" "$root/$file"
done
install -o root -g root -m 0755 server/resolver-linux-amd64 "$root/resolver.new"
mv -f "$root/resolver.new" "$root/resolver"
install -o root -g root -m 0644 server/wx-notes-resolver.service /etc/systemd/system/wx-notes-resolver.service
install -o root -g root -m 0644 server/wx-notes-gateway.service /etc/systemd/system/wx-notes-gateway.service
install -o root -g root -m 0644 server/wx-notes-cookie.service /etc/systemd/system/wx-notes-cookie.service
sed "s/^OnUnitActiveSec=.*/OnUnitActiveSec=${interval}h/" server/wx-notes-cookie.timer > "$root/.runtime/server/cookie.timer"
install -o root -g root -m 0644 "$root/.runtime/server/cookie.timer" /etc/systemd/system/wx-notes-cookie.timer
systemctl daemon-reload
systemctl enable wx-notes-cookie.timer
systemctl restart wx-notes-cookie.timer
systemctl start wx-notes-cookie.service
echo "Installed and Cookie checked. Enable and start wx-notes-resolver and wx-notes-gateway."
