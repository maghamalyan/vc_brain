.PHONY: build shell test test-service test-all lint frontend-check railway-build railway-smoke deploy-audit

build:
	docker build -t vc-brain .

shell:
	docker run -it --rm -v $(PWD):/app --env-file .env vc-brain bash

test:
	uv run pytest -q tests

test-service:
	cd service && UV_CACHE_DIR=../.uv-cache uv run --python 3.13 pytest -q

test-all: test test-service frontend-check

lint:
	uv run ruff check src tests

frontend-check:
	cd frontend && npm ci && npm run check && npm run build

railway-build:
	docker build -f Dockerfile.railway -t vc-brain-railway .

railway-smoke:
	bash scripts/smoke_railway_image.sh

deploy-audit:
	bash scripts/check_deploy_artifacts.sh
