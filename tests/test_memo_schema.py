import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from vc_brain.memo.schema import Memo


FIXTURES = Path("data/fixtures")


@pytest.mark.parametrize("path", sorted((FIXTURES / "memos").glob("*.json")))
def test_memo_schema_round_trips_fixture(path: Path) -> None:
    memo = Memo.model_validate_json(path.read_text(encoding="utf-8"))

    restored = Memo.model_validate_json(memo.model_dump_json())

    assert restored == memo
    assert set(restored.sections.model_fields_set) == {
        "company_snapshot",
        "investment_hypotheses",
        "swot",
        "problem_product",
        "traction_kpis",
    }


def test_memo_schema_rejects_unknown_section_claim() -> None:
    payload = json.loads(
        (FIXTURES / "memos" / "ada-lovelace-fixture.json").read_text()
    )
    payload["sections"]["company_snapshot"]["claim_ids"].append("invented-claim")

    with pytest.raises(ValidationError, match="unknown claim_ids"):
        Memo.model_validate(payload)

