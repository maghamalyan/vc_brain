from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path

import pytest

from vcb_service.cli import run
from vcb_service.indexer import (
    DOC_TYPES,
    CountVerificationError,
    VerificationError,
    build_index,
    inspect_index,
)
from vcb_service.snapshot import SnapshotManifestError, load_and_verify_snapshot

from conftest import DATA_DIR, THESIS_PATH


def test_index_builds_one_complete_sqlite_artifact(index_path: Path) -> None:
    result = inspect_index(index_path)

    assert set(result.doc_counts) == set(DOC_TYPES)
    assert all(count > 0 for count in result.doc_counts.values())
    assert result.unresolved == []
    assert [path.name for path in index_path.parent.iterdir()] == ["vcb.sqlite"]

    connection = sqlite3.connect(index_path)
    try:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table', 'view')"
            )
        }
        assert {"docs", "candidates", "trajectories", "events", "memos", "claims"} <= tables
        candidate_columns = {
            row[1] for row in connection.execute("PRAGMA table_info(candidates)")
        }
        assert {"recognition_json", "score_components_json"} <= candidate_columns
        assert connection.execute("SELECT count(*) FROM candidates").fetchone()[0] == 12
        assert connection.execute("SELECT count(*) FROM events").fetchone()[0] == 480
        assert connection.execute("SELECT count(*) FROM claims").fetchone()[0] == 8
    finally:
        connection.close()


def test_build_is_idempotent(tmp_path: Path) -> None:
    output = tmp_path / "nested" / "vcb.sqlite"

    first = build_index(DATA_DIR, THESIS_PATH, output, verify=True)
    second = build_index(DATA_DIR, THESIS_PATH, output, verify=True)

    assert first.doc_counts == second.doc_counts
    assert inspect_index(output).unresolved == []
    assert [path.name for path in output.parent.iterdir()] == ["vcb.sqlite"]


def test_build_uses_fixed_timestamp(tmp_path: Path) -> None:
    output = tmp_path / "vcb.sqlite"
    built_at = "2026-07-19T11:25:04.318866+00:00"

    result = build_index(
        DATA_DIR, THESIS_PATH, output, verify=True, built_at=built_at
    )

    assert result.built_at == built_at
    assert inspect_index(output).built_at == built_at


def test_count_failure_does_not_replace_existing_index(tmp_path: Path) -> None:
    output = tmp_path / "vcb.sqlite"
    build_index(DATA_DIR, THESIS_PATH, output, verify=True)
    original = output.read_bytes()

    with pytest.raises(CountVerificationError) as captured:
        build_index(
            DATA_DIR,
            THESIS_PATH,
            output,
            verify=True,
            expected_counts={"candidates": 999},
        )

    assert captured.value.mismatches == {"candidates": (999, 12)}
    assert output.read_bytes() == original


def test_snapshot_manifest_rejects_hash_mismatch(tmp_path: Path) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "input.json").write_text("{}", encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "built_at": "2026-07-19T11:25:04+00:00",
                "expected_counts": {"candidates": 1},
                "files": {"input.json": "0" * 64},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(SnapshotManifestError, match="SHA-256 mismatch"):
        load_and_verify_snapshot(manifest, data_dir)


def test_verify_fails_for_dangling_claim_evidence(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    broken_data = tmp_path / "fixtures"
    shutil.copytree(DATA_DIR, broken_data)
    memo_path = broken_data / "memos" / "ada-lovelace-fixture.json"
    memo = json.loads(memo_path.read_text(encoding="utf-8"))
    memo["claims"]["ada-product"]["evidence_refs"] = ["missing-evidence-id"]
    memo_path.write_text(json.dumps(memo), encoding="utf-8")

    with pytest.raises(VerificationError) as captured:
        build_index(broken_data, THESIS_PATH, tmp_path / "broken.sqlite", verify=True)

    assert captured.value.unresolved == [("ada-product", "missing-evidence-id")]

    exit_code = run(
        [
            "build",
            "--data-dir",
            str(broken_data),
            "--thesis",
            str(THESIS_PATH),
            "--out",
            str(tmp_path / "broken-cli.sqlite"),
            "--verify",
        ]
    )
    captured_output = capsys.readouterr()
    assert exit_code == 1
    assert "missing-evidence-id" in captured_output.err


def test_cli_verify_prints_counts(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    output = tmp_path / "cli.sqlite"

    exit_code = run(
        [
            "build",
            "--data-dir",
            str(DATA_DIR),
            "--thesis",
            str(THESIS_PATH),
            "--out",
            str(output),
            "--verify",
        ]
    )

    stdout = capsys.readouterr().out
    assert exit_code == 0
    assert "founder: 12" in stdout
    assert "recognized-after-detection: 9" in stdout
    assert "not-yet-recognized: 2" in stdout
    assert "miss: 1" in stdout
    assert "verification: ok" in stdout


def test_verify_fails_when_score_components_do_not_sum(tmp_path: Path) -> None:
    broken_data = tmp_path / "fixtures"
    shutil.copytree(DATA_DIR, broken_data)
    (broken_data / "candidates.parquet").unlink()
    candidates_path = broken_data / "candidates.json"
    candidates = json.loads(candidates_path.read_text(encoding="utf-8"))
    candidates[0]["score_components"][0]["contribution"] += 0.01
    candidates_path.write_text(json.dumps(candidates), encoding="utf-8")

    with pytest.raises(VerificationError) as captured:
        build_index(broken_data, THESIS_PATH, tmp_path / "broken-score.sqlite", verify=True)

    assert captured.value.unresolved == []
    assert captured.value.component_sum_errors[0][0] == "ada-lovelace-fixture"
