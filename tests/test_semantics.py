import json
import shutil
from collections import deque
from datetime import date, datetime
from pathlib import Path

import httpx
import polars as pl
import pytest
from pydantic import ValidationError

from vc_brain.features.build import add_months, context_divergence_2q
from vc_brain.features.taxonomy import capital_families, capital_family
from vc_brain.semantics.annotate import (
    FAILURE_WINDOW_SIZE,
    _failure_rate_exceeded,
    annotate_bundle,
    annotate_bundle_result,
    build_annotation_payload,
)
from vc_brain.semantics.extract import freeze_cohort_d, text_items_sql
from vc_brain.semantics.features import (
    annotation_feature_maps,
    semantic_features_for_month,
)
from vc_brain.semantics.schema import SemanticAnnotation
from vc_brain.semantics.validation import write_validation_sample

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


def test_live_adapter_sets_reasoning_budget_retries_validation_and_tracks_usage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    items = json.loads((FIXTURES / "items.json").read_text(encoding="utf-8"))
    valid = json.loads(
        (FIXTURES / "fixture-dev__2023-04-01.json").read_text(encoding="utf-8")
    )
    invalid = json.loads(json.dumps(valid))
    invalid["domain_shift"]["citations"] = [99]
    bodies = []
    for raw, prompt_tokens, completion_tokens in (
        (invalid, 100, 80),
        (valid, 140, 90),
    ):
        bodies.append(
            {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {
                            "content": json.dumps(raw),
                            "reasoning": "internal reasoning",
                        },
                    }
                ],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "completion_tokens_details": {"reasoning_tokens": 50},
                },
            }
        )

    class FakeResponse:
        def __init__(self, body):  # noqa: ANN001
            self.body = body

        def raise_for_status(self) -> None:
            return None

        def json(self):  # noqa: ANN201
            return self.body

    class FakeClient:
        def __init__(self) -> None:
            self.requests = []

        def post(self, url, *, headers, json):  # noqa: ANN001, ANN201
            self.requests.append(json)
            return FakeResponse(bodies.pop(0))

    client = FakeClient()
    monkeypatch.setenv("OPENROUTER_KEY", "fixture-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "z-ai/glm-5.2")
    monkeypatch.setattr("vc_brain.semantics.annotate.time.sleep", lambda _delay: None)
    outcome = annotate_bundle_result(
        actor_login="fixture-dev",
        quarter=date(2023, 4, 1),
        current_items=items,
        cache_dir=tmp_path / "cache",
        client=client,  # type: ignore[arg-type]
    )

    assert outcome.attempts == 2
    assert outcome.usage.input_tokens == 240
    assert outcome.usage.output_tokens == 170
    assert outcome.usage.reasoning_tokens == 100
    assert outcome.reasoning_present
    assert client.requests[0]["max_tokens"] == 2_000
    assert client.requests[0]["reasoning"] == {"effort": "low"}
    assert "failed validation" in client.requests[1]["messages"][-1]["content"]


def test_annotation_features_fill_months_within_quarter_and_delta_adjacent_quarters(
) -> None:
    annotations = pl.DataFrame(
        [
            {
                "actor_login": "person",
                "quarter": date(2023, 1, 1),
                "annotation_status": "ok",
                "building_what_category": "developer_tool",
                "audience_orientation": "developers",
                "productization_markers": 1,
                "commercial_language": 0,
                "collaboration_posture": "solo",
                "stated_founding_intent": "none",
                "seriousness": 1,
                "domain_shift": 0,
            },
            {
                "actor_login": "person",
                "quarter": date(2023, 4, 1),
                "annotation_status": "ok",
                "building_what_category": "application",
                "audience_orientation": "customers",
                "productization_markers": 3,
                "commercial_language": 2,
                "collaboration_posture": "team_forming",
                "stated_founding_intent": "implicit",
                "seriousness": 3,
                "domain_shift": 2,
            },
        ]
    )

    maps = annotation_feature_maps(annotations)
    may = semantic_features_for_month(maps, login="person", month=date(2023, 5, 1))
    june = semantic_features_for_month(maps, login="person", month=date(2023, 6, 1))

    assert may == june
    assert may["productization_markers"] == 3.0
    assert may["productization_markers_delta"] == 2.0
    assert may["building_what_application"] == 1.0
    assert may["building_what_application_delta"] == 1.0
    assert may["stated_founding_intent_delta"] == 1.0


def test_failure_window_aborts_only_after_more_than_five_percent() -> None:
    at_threshold = deque(
        [True] * 25 + [False] * (FAILURE_WINDOW_SIZE - 25),
        maxlen=FAILURE_WINDOW_SIZE,
    )
    over_threshold = deque(
        [True] * 26 + [False] * (FAILURE_WINDOW_SIZE - 26),
        maxlen=FAILURE_WINDOW_SIZE,
    )

    assert not _failure_rate_exceeded(at_threshold)
    assert _failure_rate_exceeded(over_threshold)


def test_validation_sample_is_40_bundles_and_withholds_outcome_labels(
    tmp_path: Path,
) -> None:
    quarters = [date(year, month, 1) for year in range(2020, 2025) for month in (1, 4)]
    annotations = []
    items = []
    for person_type in ("positive", "control"):
        for index in range(30):
            login = f"blind-{person_type[0]}-{index:02d}"
            quarter = quarters[index % len(quarters)]
            annotations.append(
                {
                    "actor_login": login,
                    "quarter": quarter,
                    "person_type": person_type,
                    "annotation_status": "ok",
                    "annotation_json": '{"measurement": "fixture"}',
                }
            )
            items.append(
                {
                    "actor_login": login,
                    "quarter": quarter,
                    "item_index": 1,
                    "created_at": datetime(quarter.year, quarter.month, 2),
                    "event_type": "IssuesEvent",
                    "repo_name": "person/repo",
                    "title": "Fixture title",
                    "body": "Fixture body",
                }
            )
    annotations_path = tmp_path / "annotations.parquet"
    items_path = tmp_path / "items.parquet"
    output_path = tmp_path / "sample.md"
    pl.DataFrame(annotations).write_parquet(annotations_path)
    pl.DataFrame(items).write_parquet(items_path)

    write_validation_sample(
        items_path=items_path,
        annotations_path=annotations_path,
        output_path=output_path,
    )
    rendered = output_path.read_text(encoding="utf-8")

    assert rendered.count("\n## Bundle ") == 40
    assert "person_type" not in rendered
    assert "matched_positive_login" not in rendered
    assert "blind-p-" in rendered and "blind-c-" in rendered


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
