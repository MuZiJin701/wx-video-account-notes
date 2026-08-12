#!/bin/sh
set -eu
. "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/common.sh"
[ -x "$venv_dir/bin/python" ] || { echo 'Private runtime is not initialized. Run scripts/bootstrap.sh first.' >&2; exit 1; }
export PYTHONPATH="$skill_root"
"$venv_dir/bin/python" "$skill_root/runtime/verify.py" --skill-root "$skill_root"
