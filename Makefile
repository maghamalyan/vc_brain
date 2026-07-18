.PHONY: build shell test lint

build:
	docker build -t vc-brain .

shell:
	docker run -it --rm -v $(PWD):/app --env-file .env vc-brain bash

test:
	uv run pytest -q

lint:
	uv run ruff check src tests

