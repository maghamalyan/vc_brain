#!/usr/bin/env bash
set -euo pipefail

image=${VCB_RAILWAY_IMAGE:-vc-brain-railway:smoke}
host_port=${VCB_RAILWAY_SMOKE_PORT:-18080}
container="vc-brain-railway-smoke-$$"
temporary_dir=$(mktemp -d)

cleanup() {
  docker rm -f "$container" >/dev/null 2>&1 || true
  rm -rf "$temporary_dir"
}
trap cleanup EXIT

docker build -f Dockerfile.railway -t "$image" .
docker run -d --name "$container" -e PORT=8080 -p "127.0.0.1:${host_port}:8080" "$image" >/dev/null

ready=0
for _attempt in $(seq 1 30); do
  if curl --fail --silent --show-error \
    "http://127.0.0.1:${host_port}/api/v1/health" \
    >"$temporary_dir/health.json"; then
    ready=1
    break
  fi
  sleep 1
done
if (( ready == 0 )); then
  docker logs "$container" >&2
  exit 1
fi

python3 - "$temporary_dir/health.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)
assert payload["status"] == "ok", payload
assert payload["counts"] == {"candidates": 100, "events": 4090, "claims": 50}, payload
PY

docker logs "$container" >"$temporary_dir/container.log" 2>&1
if ! grep --quiet \
  'event=service_ready index_built_at=2026-07-19T11:25:04.318866+00:00 candidates=100 events=4090 claims=50' \
  "$temporary_dir/container.log"; then
  echo "readiness event missing from container logs" >&2
  cat "$temporary_dir/container.log" >&2
  exit 1
fi

curl --fail --silent --show-error "http://127.0.0.1:${host_port}/" >"$temporary_dir/index.html"
grep --quiet "VC Brain" "$temporary_dir/index.html"
curl --fail --silent --show-error \
  "http://127.0.0.1:${host_port}/candidate/28andrew" \
  >"$temporary_dir/history.html"
grep --quiet "VC Brain" "$temporary_dir/history.html"

if docker exec "$container" grep -R -E \
  'Start deep dive|Live diligence workspace|Deep dive on .*Start founder analysis' \
  /app/frontend/dist >/dev/null; then
  echo "production frontend still contains live deep-dive controls" >&2
  exit 1
fi

status=$(curl --silent --show-error \
  --output "$temporary_dir/deepdive.json" \
  --write-out '%{http_code}' \
  --request POST \
  --header 'Content-Type: application/json' \
  --data '{"entity_type":"founder","entity_id":"28andrew"}' \
  "http://127.0.0.1:${host_port}/api/v1/deepdive")
test "$status" = "503"
python3 - "$temporary_dir/deepdive.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)
assert payload["detail"]["code"] == "LIVE_DEEPDIVE_DISABLED", payload
PY

if docker exec "$container" sh -c 'test -w /app/data/vcb.sqlite'; then
  echo "deployment index is unexpectedly writable" >&2
  exit 1
fi
docker exec "$container" sh -c \
  'test ! -e /app/deploy && test ! -e /app/app_data && test ! -e /app/.env'

echo "Railway image smoke test: ok"
