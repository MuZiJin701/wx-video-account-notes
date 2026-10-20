#!/bin/sh
set -eu
. "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/common.sh"
ensure_uv
printf '%s\n' "$uv_command"
