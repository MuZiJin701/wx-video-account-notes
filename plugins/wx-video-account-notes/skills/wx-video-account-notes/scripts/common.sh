#!/bin/sh
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
skill_root=$(CDPATH= cd -- "$script_dir/.." && pwd)
case "$(uname -s):$(uname -m)" in
  Darwin:x86_64) platform_id=macos-x64; uv_archive=uv-x86_64-apple-darwin.tar.gz; uv_url=https://releases.astral.sh/github/uv/releases/download/0.11.25/$uv_archive; uv_sha256=65ff85b33212f75d34d7c0f0724aba9a742c74f62559f67dc0d6c543dc2fc52f; uv_binary=uv; python_binary=python3.13; venv_python=.venv/bin/python; ffmpeg_binary=ffmpeg; ffprobe_binary=ffprobe ;;
  Linux:x86_64) platform_id=linux-x64; uv_archive=uv-x86_64-unknown-linux-gnu.tar.gz; uv_url=https://releases.astral.sh/github/uv/releases/download/0.11.25/$uv_archive; uv_sha256=1db18b5e76fa645a7f3865773139bdec8e2d46adbdbb35e7410b34fa8015ccd2; uv_binary=uv; python_binary=python3.13; venv_python=.venv/bin/python; ffmpeg_binary=ffmpeg; ffprobe_binary=ffprobe ;;
  *) echo "Unsupported platform. Supported platforms: Windows, macOS, Linux x64." >&2; exit 2 ;;
esac
runtime_root=$skill_root/.runtime/$platform_id
uv_dir=$runtime_root/uv
python_dir=$runtime_root/python
cache_dir=$runtime_root/cache
venv_dir=$runtime_root/.venv
uv_command=$uv_dir/$uv_binary

sha256_matches() {
  file=$1
  expected=$2
  if command -v sha256sum >/dev/null 2>&1; then actual=$(sha256sum "$file" | awk '{print $1}'); else actual=$(shasum -a 256 "$file" | awk '{print $1}'); fi
  [ "$actual" = "$expected" ]
}

ensure_uv() {
  mkdir -p "$uv_dir" "$cache_dir"
  if [ -x "$uv_command" ] && "$uv_command" --version | grep -F '0.11.25' >/dev/null 2>&1; then return; fi
  rm -rf "$uv_dir"
  mkdir -p "$uv_dir"
  archive="$cache_dir/$uv_archive"
  temporary="$archive.tmp"
  echo '[wx-video-account-notes] Downloading private uv 0.11.25.'
  if ! curl -fL --retry 3 "$uv_url" -o "$temporary"; then rm -f "$temporary"; return 1; fi
  if ! sha256_matches "$temporary" "$uv_sha256"; then rm -f "$temporary"; echo 'uv checksum verification failed.' >&2; return 1; fi
  mv "$temporary" "$archive"
  if ! tar -xzf "$archive" -C "$uv_dir"; then rm -rf "$uv_dir"; return 1; fi
  downloaded=$(find "$uv_dir" -type f -name uv -print -quit)
  [ -n "$downloaded" ] || { rm -rf "$uv_dir"; echo 'Downloaded uv archive did not contain uv.' >&2; return 1; }
  cp "$downloaded" "$uv_command"
  chmod +x "$uv_command"
}
