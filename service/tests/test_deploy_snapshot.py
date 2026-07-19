from pathlib import Path

from vcb_service.indexer import build_index
from vcb_service.snapshot import load_and_verify_snapshot


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "deploy" / "demo-data"
MANIFEST = DATA_DIR / "manifest.json"
THESIS = ROOT / "config" / "thesis.json"


def test_committed_deployment_snapshot_builds_expected_index(tmp_path: Path) -> None:
    snapshot = load_and_verify_snapshot(MANIFEST, DATA_DIR)

    result = build_index(
        DATA_DIR,
        THESIS,
        tmp_path / "vcb.sqlite",
        verify=True,
        built_at=snapshot.built_at,
        expected_counts=snapshot.expected_counts,
    )

    assert result.built_at == "2026-07-19T11:25:04.318866+00:00"
    assert result.entity_counts == {
        "candidates": 100,
        "trajectories": 3700,
        "events": 4090,
        "memos": 6,
        "claims": 50,
    }
    assert result.unresolved == []
    assert result.component_sum_errors == []
