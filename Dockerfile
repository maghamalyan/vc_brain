FROM python:3.13-slim

RUN pip install --no-cache-dir uv==0.11.21

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src/ src/

RUN uv sync --frozen

