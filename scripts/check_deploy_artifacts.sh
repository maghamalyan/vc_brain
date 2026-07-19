#!/usr/bin/env bash
set -euo pipefail

failed=0
while IFS= read -r path; do
  case "$path" in
    .env|.env.*|app_data/*|data/*|*/.venv/*|*/node_modules/*|*/__pycache__/*)
      echo "forbidden tracked deployment input: $path" >&2
      failed=1
      ;;
  esac
done < <(git ls-files)

while IFS= read -r path; do
  echo "deployment snapshot file exceeds 2 MiB: $path" >&2
  failed=1
done < <(find deploy/demo-data -type f -size +2M -print)

snapshot_kib=$(du -sk deploy/demo-data | awk '{print $1}')
if (( snapshot_kib > 1024 )); then
  echo "deployment snapshot exceeds 1 MiB: ${snapshot_kib} KiB" >&2
  failed=1
fi

if (( failed != 0 )); then
  exit 1
fi

echo "deployment artifact audit: ok (${snapshot_kib} KiB snapshot)"
