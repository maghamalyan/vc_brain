"""Verification for committed, immutable deployment snapshots."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from vcb_service.indexer import IndexBuildError


class SnapshotManifestError(IndexBuildError):
    """Raised when a deployment snapshot manifest or input file is invalid."""


@dataclass(frozen=True)
class SnapshotManifest:
    built_at: str
    expected_counts: dict[str, int]
    files: dict[str, str]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _object(value: Any, *, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SnapshotManifestError(f"snapshot manifest {name} must be an object")
    return value


def load_and_verify_snapshot(
    manifest_path: Path, data_dir: Path
) -> SnapshotManifest:
    """Load a manifest and verify every declared file before index construction."""

    manifest_path = manifest_path.resolve()
    data_dir = data_dir.resolve()
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SnapshotManifestError(
            f"cannot read snapshot manifest: {manifest_path}"
        ) from error
    payload = _object(payload, name="root")
    if payload.get("schema_version") != 1:
        raise SnapshotManifestError("snapshot manifest schema_version must be 1")

    built_at = payload.get("built_at")
    if not isinstance(built_at, str):
        raise SnapshotManifestError("snapshot manifest built_at must be a string")
    try:
        parsed_built_at = datetime.fromisoformat(built_at)
    except ValueError as error:
        raise SnapshotManifestError(
            "snapshot manifest built_at must be an ISO-8601 datetime"
        ) from error
    if parsed_built_at.tzinfo is None:
        raise SnapshotManifestError("snapshot manifest built_at must include a timezone")

    raw_counts = _object(payload.get("expected_counts"), name="expected_counts")
    expected_counts: dict[str, int] = {}
    for name, value in raw_counts.items():
        if not isinstance(name, str) or not isinstance(value, int) or isinstance(value, bool):
            raise SnapshotManifestError(
                "snapshot manifest expected_counts values must be integers"
            )
        if value < 0:
            raise SnapshotManifestError(
                "snapshot manifest expected_counts values must be non-negative"
            )
        expected_counts[name] = value

    raw_files = _object(payload.get("files"), name="files")
    if not raw_files:
        raise SnapshotManifestError("snapshot manifest files must not be empty")
    files: dict[str, str] = {}
    for relative_name, expected_hash in raw_files.items():
        if not isinstance(relative_name, str) or not isinstance(expected_hash, str):
            raise SnapshotManifestError(
                "snapshot manifest files must map paths to SHA-256 strings"
            )
        if len(expected_hash) != 64 or any(
            character not in "0123456789abcdef" for character in expected_hash
        ):
            raise SnapshotManifestError(
                f"snapshot manifest has invalid SHA-256 for {relative_name}"
            )
        candidate = (data_dir / relative_name).resolve()
        if not candidate.is_relative_to(data_dir):
            raise SnapshotManifestError(
                f"snapshot manifest path escapes data directory: {relative_name}"
            )
        if not candidate.is_file():
            raise SnapshotManifestError(f"snapshot file not found: {relative_name}")
        actual_hash = _sha256(candidate)
        if actual_hash != expected_hash:
            raise SnapshotManifestError(
                f"snapshot SHA-256 mismatch for {relative_name}: "
                f"expected {expected_hash}, got {actual_hash}"
            )
        files[relative_name] = expected_hash

    return SnapshotManifest(
        built_at=parsed_built_at.isoformat(),
        expected_counts=expected_counts,
        files=files,
    )
