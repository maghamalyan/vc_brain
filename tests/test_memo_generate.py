import json
from pathlib import Path

import httpx
import pytest

from vc_brain.memo.generate import generate_memo


FIXTURES = Path("data/fixtures")


def test_mock_generation_is_offline_and_preserves_evidence_discipline(
    tmp_path: Path, monkeypatch
) -> None:
    candidates = json.loads((FIXTURES / "candidates.json").read_text())
    candidate = next(
        item for item in candidates if item["gh_login"] == "ada-lovelace-fixture"
    )
    evidence = [
        item
        for item in json.loads((FIXTURES / "events.json").read_text())
        if item["gh_login"] == candidate["gh_login"]
    ]

    def reject_network(*args, **kwargs):
        raise AssertionError("mock generation attempted a network request")

    monkeypatch.setattr(httpx.Client, "post", reject_network)
    memo = generate_memo(
        candidate,
        evidence,
        mock=True,
        cache_dir=tmp_path / "cache",
        fixture_memos_dir=FIXTURES / "memos",
    )

    supplied_refs = {
        value
        for row in evidence
        for value in (row["evidence_id"], row["url"])
    }
    assert all(claim.evidence_refs for claim in memo.claims.values())
    assert all(
        ref in supplied_refs
        for claim in memo.claims.values()
        for ref in claim.evidence_refs
    )
    assert memo.gaps == [
        "Revenue and customer retention: not disclosed.",
        "Cap table: not disclosed.",
    ]
    assert set(memo.sections.model_dump()) == {
        "company_snapshot",
        "investment_hypotheses",
        "swot",
        "problem_product",
        "traction_kpis",
    }
    assert len(list((tmp_path / "cache").glob("*.json"))) == 1


def test_mock_generation_rejects_a_fixture_citation_not_in_input(
    tmp_path: Path,
) -> None:
    candidate = {"gh_login": "ada-lovelace-fixture"}
    fixture = json.loads(
        (FIXTURES / "memos" / "ada-lovelace-fixture.json").read_text()
    )
    fixture["claims"]["ada-product"]["evidence_refs"] = ["invented-source"]
    fixture_dir = tmp_path / "memos"
    fixture_dir.mkdir()
    (fixture_dir / "ada-lovelace-fixture.json").write_text(json.dumps(fixture))

    with pytest.raises(ValueError, match="evidence that was not supplied"):
        generate_memo(
            candidate,
            [],
            mock=True,
            cache_dir=tmp_path / "cache",
            fixture_memos_dir=fixture_dir,
        )
