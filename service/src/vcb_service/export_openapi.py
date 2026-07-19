"""Export the FastAPI contract snapshot consumed by the frontend task."""

from __future__ import annotations

import json
from pathlib import Path

from vcb_service.app import create_app


def default_output_path() -> Path:
    workspace = Path(__file__).resolve().parents[3]
    return workspace / "frontend" / "src" / "lib" / "api" / "openapi.json"


def export_openapi(output: Path | None = None) -> Path:
    destination = (output or default_output_path()).resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(create_app().openapi(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return destination


def main() -> None:
    print(export_openapi())
