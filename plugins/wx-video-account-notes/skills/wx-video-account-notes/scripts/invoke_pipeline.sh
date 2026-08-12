#!/bin/sh
set -eu
. "$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)/common.sh"

share_url=''
output_dir=''
while [ "$#" -gt 0 ]; do
  case "$1" in
    --share-url) share_url=${2:-}; shift 2 ;;
    --output-dir) output_dir=${2:-}; shift 2 ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done
[ -n "$share_url" ] || { echo '--share-url is required.' >&2; exit 2; }
[ -x "$uv_command" ] && [ -x "$venv_dir/bin/python" ] || { echo 'Private runtime is not initialized. Run scripts/bootstrap.sh first.' >&2; exit 1; }
export PYTHONPATH="$skill_root"
export UV_PROJECT_ENVIRONMENT="$venv_dir"
set -- run --locked --project "$skill_root" python -m runtime.pipeline --skill-root "$skill_root" --share-url "$share_url"
if [ -n "$output_dir" ]; then set -- "$@" --output-dir "$output_dir"; fi
"$uv_command" "$@"
