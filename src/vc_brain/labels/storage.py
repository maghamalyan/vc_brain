"""Atomic local storage for label tables, caches, and resume metadata."""

import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import polars as pl


class InvalidCheckpointError(RuntimeError):
    """A checkpoint cannot be parsed or has the wrong top-level shape."""


def checkpoint_path(output_path: Path) -> Path:
    return output_path.with_suffix(".checkpoint.json")


def read_checkpoint(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise InvalidCheckpointError(f"Checkpoint contains invalid JSON: {path}") from error
    if not isinstance(value, dict):
        raise InvalidCheckpointError(f"Checkpoint must contain an object: {path}")
    return value


def atomic_write_json(value: Mapping[str, Any], path: Path) -> None:
    atomic_write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", path)


def atomic_write_text(value: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def atomic_write_parquet(frame: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    os.close(descriptor)
    try:
        frame.write_parquet(temporary)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def frame_from_rows(
    rows: list[dict[str, Any]], schema: Mapping[str, pl.DataType]
) -> pl.DataFrame:
    if not rows:
        return pl.DataFrame(schema=schema)
    return pl.DataFrame(rows, schema=schema, strict=False).select(list(schema))
