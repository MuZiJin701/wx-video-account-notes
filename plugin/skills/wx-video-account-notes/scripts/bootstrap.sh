#!/bin/sh
set -eu
. "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/common.sh"

prune_cache=0
if [ "${1:-}" = "--prune-cache" ]; then prune_cache=1; fi
ensure_uv
mkdir -p "$uv_dir" "$python_dir"
export PYTHONPATH="$skill_root"
export UV_PROJECT_ENVIRONMENT="$venv_dir"
export UV_PYTHON_INSTALL_DIR="$python_dir"
set -- run --locked --project "$skill_root" --python 3.13.14 --link-mode copy "$skill_root/runtime/bootstrap.py" --skill-root "$skill_root" --runtime-root "$runtime_root"
if [ "$prune_cache" -eq 1 ]; then set -- "$@" --prune-cache; fi
"$uv_command" "$@"
echo '[wx-video-account-notes] Bootstrap complete.'
