#!/bin/sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo "Run as root" >&2
  exit 1
fi

root=/root/projects/wx-video-account-notes
cd "$root"
test -s resolver-linux-amd64
test -s client.json
chown root:root "$root" gateway.py update_cookie.py client.json
chmod 0700 "$root"
chmod 0644 gateway.py
chmod 0700 update_cookie.py
chmod 0600 client.json
install -o root -g root -m 0755 resolver-linux-amd64 "$root/resolver.new"
mv -f "$root/resolver.new" "$root/resolver"
