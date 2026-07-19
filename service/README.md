# VC Brain service

Build the single-file read model and run the API from this directory:

```bash
uv run vcb-index build --data-dir ../data/fixtures --thesis ../config/thesis.json --out ../data/index/vcb.sqlite --verify
VCB_INDEX=../data/index/vcb.sqlite uv run uvicorn vcb_service.app:app
```

The server opens `VCB_INDEX` read-only. Its default is `data/index/vcb.sqlite`
relative to the process working directory. The API is under `/api/v1`, including
OpenAPI at `/api/v1/openapi.json`.

Export the checked-in frontend OpenAPI snapshot with:

```bash
uv run vcb-openapi
```
