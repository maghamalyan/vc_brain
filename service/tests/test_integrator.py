from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from vcb_service.integrator import (
    IntegrationBuildError,
    build_recognition_lookup,
    build_score_components,
    component_sum_errors,
    normalize_score_percentile,
    unresolved_memo_refs,
)


def test_percentile_normalization_scales_fraction_without_double_scaling() -> None:
    assert normalize_score_percentile(0.974) == pytest.approx(97.4)
    assert normalize_score_percentile(1.0) == 100.0
    assert normalize_score_percentile(97.4) == 97.4

    with pytest.raises(IntegrationBuildError, match="0..1 or already normalized"):
        normalize_score_percentile(9_740)
    with pytest.raises(IntegrationBuildError, match="0..1 or already normalized"):
        normalize_score_percentile(-0.01)


def test_recognition_join_uses_highest_confidence_real_batch() -> None:
    founders = pl.DataFrame(
        {
            "gh_login": ["founder", "founder", "unmatched"],
            "gh_confidence": [0.6, 1.0, 0.8],
            "batch_start_date": [
                date(2025, 1, 5),
                date(2024, 6, 1),
                date(2023, 9, 1),
            ],
            "batch": ["Winter 2025", "Summer 2024", "Fall 2023"],
        }
    )

    recognition = build_recognition_lookup(founders)

    assert recognition["founder"] == {
        "month": "2024-06",
        "kind": "yc_batch",
        "label": "YC Summer 2024",
    }


def test_score_components_are_additive_and_absent_attributions_stay_empty() -> None:
    candidates = pl.DataFrame(
        {
            "gh_login": ["with-signals", "without-signals"],
            "current_score": [0.4, 0.3],
            "first_detection_month": [date(2024, 1, 1), date(2024, 2, 1)],
        }
    )
    attributions = pl.DataFrame(
        {
            "login": ["with-signals"] * 5,
            "crossing_month": [date(2024, 1, 1)] * 5,
            "feature": ["alpha", "beta", "gamma", "delta", "epsilon"],
            "delta_contrib": [0.5, -0.3, 0.1, 0.05, 0.05],
        }
    )

    components = build_score_components(candidates, attributions)

    assert components["without-signals"] == []
    assert len(components["with-signals"]) == 5
    assert components["with-signals"][-1]["key"] == "other_observed_signals"
    assert sum(item["contribution"] for item in components["with-signals"]) == pytest.approx(
        0.4
    )
    rows = [
        {
            "gh_login": login,
            "current_score": score,
            "score_components": components[login],
        }
        for login, score in (("with-signals", 0.4), ("without-signals", 0.3))
    ]
    assert component_sum_errors(rows) == []


def test_memo_refs_resolve_only_against_inline_evidence_or_public_urls() -> None:
    memos = {
        "founder": {
            "claims": {
                "resolved": {
                    "evidence_refs": ["yc:company", "https://example.com/public"]
                },
                "dangling": {"evidence_refs": ["repo:missing"]},
            }
        }
    }
    events = [{"evidence_id": "yc:company"}]

    assert unresolved_memo_refs(memos, events) == [
        ("founder:dangling", "repo:missing")
    ]
