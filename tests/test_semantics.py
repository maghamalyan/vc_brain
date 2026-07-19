import json
import shutil
from datetime import date, datetime
from pathlib import Path

import httpx
import polars as pl
import pytest
from pydantic import ValidationError

from vc_brain.features.build import add_months, context_divergence_2q
from vc_brain.features.taxonomy import capital_families, capital_family
from vc_brain.semantics.annotate import annotate_bundle, build_annotation_payload
from vc_brain.semantics.extract import freeze_cohort_d, text_items_sql
from vc_brain.semantics.schema import SemanticAnnotation

FIXTURES = Path(__file__).parent / "fixtures" / "semantics"


def _text_rows(actor: str, cutoff: date, count: int) -> list[dict[str, object]]:
    return [
        {
            "actor_login": actor,
            "created_at": datetime(2023, 3, 31, 12, index),
            "quarter": date(2023, 1, 1),
            "item_index": index + 1,
            "event_type": "IssuesEvent",
            "repo_name": f"{actor}/repo",
            "title": f"Issue {index}",
            "body": "Fixture body",
            "t_cutoff": cutoff,
        }
        for index in range(count)
    ]


class StubTextClient:
    def query_actor_batches(self, actors, builder, *, batch_size):  # noqa: ANN001
        assert batch_size == 1_500
        sql = builder(actors)
        assert "e.created_at < toDateTime(a.t_cutoff)" in sql
        counts = {"p1": 20, "p2": 19, "n1": 20, "n2": 19}
        rows = [
            row
            for actor in actors
            for row in _text_rows(
                str(actor["actor_login"]),
                actor["t_cutoff"],
                counts[str(actor["actor_login"])],
            )
        ]
        return pl.DataFrame(rows)


def test_text_sql_has_exact_event_fields_cutoff_and_quarter_cap() -> None:
    sql = text_items_sql([{"actor_login": "o'brien", "t_cutoff": date(2024, 1, 1)}])

    assert "e.actor_login = a.actor_login" in sql
    assert "PREWHERE e.actor_login IN ('o\\'brien')" in sql
    assert "IssuesEvent" in sql and "DiscussionEvent" in sql
    assert "base64Encode(e.title) AS title_b64" in sql
    assert "base64Encode(left(e.body, 1500)) AS body_b64" in sql
    assert "PARTITION BY e.actor_login, toStartOfQuarter(e.created_at)" in sql
    assert "WHERE item_index <= 40" in sql
    assert "e.created_at < toDateTime(a.t_cutoff)" in sql
    assert "o\\'brien" in sql


def test_cohort_d_applies_minimum_to_founders_and_matched_controls(
    tmp_path: Path,
) -> None:
    cutoff = date(2024, 1, 1)
    positives = pl.DataFrame(
        {"actor_login": ["p1", "p2"], "t_cutoff": [cutoff, cutoff]}
    )
    matches = pl.DataFrame(
        {
            "actor_login": ["n1", "n2"],
            "t_cutoff": [cutoff, cutoff],
            "matched_positive_login": ["p1", "p1"],
        }
    )

    cohort, items, summary = freeze_cohort_d(
        StubTextClient(),  # type: ignore[arg-type]
        positive_cohort=positives,
        matches=matches,
        positive_text_path=tmp_path / "positive.parquet",
        control_text_path=tmp_path / "control.parquet",
        cohort_path=tmp_path / "cohort.parquet",
        items_path=tmp_path / "items.parquet",
        summary_path=tmp_path / "summary.json",
    )

    assert set(cohort.get_column("actor_login")) == {"p1", "n1"}
    assert items.height == 40
    assert summary["cohort"] == {
        "founders": 1,
        "controls": 1,
        "people": 2,
        "person_quarters": 2,
        "text_items": 40,
    }
    assert summary["annotation_cost_estimate"]["estimated_total_tokens"] == 3_000
    assert json.loads((tmp_path / "summary.json").read_text()) == summary


def test_annotation_schema_requires_citations_and_domain_shift() -> None:
    raw = json.loads(
        (FIXTURES / "fixture-dev__2023-04-01.json").read_text(encoding="utf-8")
    )
    annotation = SemanticAnnotation.model_validate(raw)

    assert annotation.domain_shift.value == 2
    raw["domain_shift"]["citations"] = []
    with pytest.raises(ValidationError, match="scale values require item citations"):
        SemanticAnnotation.model_validate(raw)


def test_mock_annotation_is_offline_content_cached_and_citation_checked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    items = json.loads((FIXTURES / "items.json").read_text(encoding="utf-8"))

    def reject_network(*args, **kwargs):  # noqa: ANN002, ANN003
        raise AssertionError("mock semantic annotation attempted a network request")

    monkeypatch.setattr(httpx.Client, "post", reject_network)
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    fixture_path = FIXTURES / "fixture-dev__2023-04-01.json"
    shutil.copy(fixture_path, fixture_dir / fixture_path.name)
    first = annotate_bundle(
        actor_login="fixture-dev",
        quarter=date(2023, 4, 1),
        current_items=items,
        mock=True,
        fixture_dir=fixture_dir,
        cache_dir=tmp_path / "cache",
    )
    (fixture_dir / fixture_path.name).unlink()
    second = annotate_bundle(
        actor_login="fixture-dev",
        quarter=date(2023, 4, 1),
        current_items=items,
        mock=True,
        fixture_dir=fixture_dir,
        cache_dir=tmp_path / "cache",
    )

    assert first == second
    assert len(list((tmp_path / "cache").glob("*.json"))) == 1


def test_annotation_payload_is_bounded_and_keeps_current_indices() -> None:
    items = json.loads((FIXTURES / "items.json").read_text(encoding="utf-8"))
    payload = build_annotation_payload(
        actor_login="fixture-dev",
        quarter=date(2023, 4, 1),
        current_items=items,
        earlier_bundles=[{"quarter": date(2023, 1, 1), "items": items}],
    )

    assert [row["item_index"] for row in payload["current_quarter_items"]] == [1, 2]
    assert all("item_index" not in row for row in payload["earlier_context_items"])


def test_context_divergence_uses_event_mix_and_requires_two_prior_quarters() -> None:
    start = date(2023, 1, 1)
    events = {
        add_months(start, offset): {"IssuesEvent" if offset < 6 else "PushEvent": 10.0}
        for offset in range(12)
    }

    assert context_divergence_2q(
        month=date(2023, 12, 1),
        event_counts=events,
        own_counts={},
        ownership_counts={},
        event_types=("IssuesEvent", "PushEvent"),
    ) == pytest.approx(1.0)
    assert (
        context_divergence_2q(
            month=date(2023, 6, 1),
            event_counts=events,
            own_counts={},
            ownership_counts={},
            event_types=("IssuesEvent", "PushEvent"),
        )
        is None
    )


def test_capital_mapping_includes_semantic_redeployment_and_empty_financial() -> None:
    mapping = capital_families(
        [
            "tenure_months",
            "context_divergence_2q",
            "activity_push_3m",
            "own_repo_share_3m",
        ]
    )

    assert capital_family("domain_shift") == "cognitive"
    assert mapping["cognitive"] == ["tenure_months", "context_divergence_2q"]
    assert mapping["human"] == ["activity_push_3m"]
    assert mapping["contextual"] == ["own_repo_share_3m"]
    assert mapping["financial"] == []
