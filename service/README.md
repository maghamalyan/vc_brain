# VC Brain service

Build the single-file read model and run the API from this directory:

```bash
uv run vcb-index build --data-dir ../data/fixtures --thesis ../config/thesis.json --out ../data/index/vcb.sqlite --verify
VCB_INDEX=../data/index/vcb.sqlite uv run uvicorn vcb_service.app:app
```

The server opens `VCB_INDEX` read-only. Its default is `data/index/vcb.sqlite`
relative to the process working directory. The API is under `/api/v1`, including
OpenAPI at `/api/v1/openapi.json`.

Live deep-dives are enabled by default for local development. Set
`VCB_DEEPDIVE_ENABLED=0` for deterministic deployments; the creation endpoint
then returns `503` with `LIVE_DEEPDIVE_DISABLED` before constructing a data
provider or making an external request. The Railway image bakes this setting
into both the backend and frontend build.

For a frozen snapshot, verify hashes and counts and reuse its fixed timestamp:

```bash
uv run vcb-index build \
  --data-dir ../deploy/demo-data \
  --manifest ../deploy/demo-data/manifest.json \
  --thesis ../config/thesis.json \
  --out ../data/index/vcb.sqlite \
  --verify
```

Export the checked-in frontend OpenAPI snapshot with:

```bash
uv run vcb-openapi
```
