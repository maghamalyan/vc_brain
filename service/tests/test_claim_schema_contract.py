from __future__ import annotations

from pathlib import Path

import pytest

from vcb_service.claim_schema import Memo

from conftest import DATA_DIR, WORKSPACE_ROOT


MEMO_PATHS = sorted((DATA_DIR / "memos").glob("*.json"))


@pytest.mark.parametrize("memo_path", MEMO_PATHS, ids=lambda path: path.stem)
def test_fixture_memo_matches_copied_claim_contract(memo_path: Path) -> None:
    memo = Memo.model_validate_json(memo_path.read_text(encoding="utf-8"))

    assert memo.founder_logins
    assert memo.claims
    assert all(claim.evidence_refs for claim in memo.claims.values())


def test_service_schema_is_verbatim_copy_with_only_provenance_header() -> None:
    copied = (
        WORKSPACE_ROOT / "service" / "src" / "vcb_service" / "claim_schema.py"
    ).read_text(encoding="utf-8")
    source = (WORKSPACE_ROOT / "src" / "vc_brain" / "memo" / "schema.py").read_text(
        encoding="utf-8"
    )

    assert copied.splitlines()[0].startswith("# Provenance:")
    assert copied.partition("\n")[2].rstrip("\n") == source.rstrip("\n")
