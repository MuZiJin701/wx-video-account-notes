#!/bin/sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root" >&2
  exit 1
fi

root=/root/projects/wx-video-account-notes
cd "$root"
command -v systemctl >/dev/null
test -x /usr/bin/python3
for file in resolver-linux-amd64 gateway.py update_cookie.py wx-notes-resolver.service wx-notes-gateway.service; do
  test -s "server/$file"
done
test -s client.json
chown root:root "$root" client.json
chmod 0700 "$root"
chmod 0600 client.json
if [ -f cookie ]; then
  chown root:root cookie
  chmod 0600 cookie
fi
install -o root -g root -m 0644 server/gateway.py "$root/gateway.py"
install -o root -g root -m 0700 server/update_cookie.py "$root/update_cookie.py"
install -o root -g root -m 0755 server/resolver-linux-amd64 "$root/resolver.new"
mv -f "$root/resolver.new" "$root/resolver"
install -o root -g root -m 0644 server/wx-notes-resolver.service /etc/systemd/system/wx-notes-resolver.service
install -o root -g root -m 0644 server/wx-notes-gateway.service /etc/systemd/system/wx-notes-gateway.service
systemctl daemon-reload
echo "Installed. Update Cookie, then enable and start both wx-notes services with systemctl."
