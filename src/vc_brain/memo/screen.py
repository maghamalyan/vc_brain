"""Deterministic, independently scored opportunity screening axes."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from typing import Any

from vc_brain.memo.schema import Axis, Memo, ThreeAxis


STATUS_WEIGHT = {
    "verified": 1.0,
    "single_source": 0.68,
    "unverified": 0.32,
    "not_disclosed": 0.0,
}


def screen_candidate(
    candidate: Mapping[str, Any],
    evidence_rows: Sequence[Mapping[str, Any]],
    memo: Memo,
    trajectory_rows: Sequence[Mapping[str, Any]],
) -> ThreeAxis:
    """Return stable per-axis scores; the three values remain independent."""
    detector_score = _bounded(float(candidate.get("current_score", 0.0)), 0.0, 1.0)
    evidence_density = min(len(evidence_rows) / 40.0, 1.0)
    founder_value = 1.0 + 9.0 * (0.78 * detector_score + 0.22 * evidence_density)

    market_ids = _existing_ids(
        memo,
        [
            *[item.claim_ids for item in memo.sections.swot.opportunities],
            *[item.claim_ids for item in memo.sections.swot.risks],
        ],
    )
    idea_ids = _existing_ids(
        memo,
        [
            *memo.sections.problem_product.claim_ids,
            *memo.sections.traction_kpis.claim_ids,
            *[item.claim_ids for item in memo.sections.investment_hypotheses],
        ],
    )
    founder_ids = _existing_ids(
        memo,
        [
            *[item.claim_ids for item in memo.sections.swot.strengths],
            *memo.sections.traction_kpis.claim_ids,
        ],
    )

    market_value = _claim_axis_value(memo, market_ids)
    idea_value = _claim_axis_value(memo, idea_ids)
    trajectory_trend = _trajectory_trend(trajectory_rows)

    return ThreeAxis(
        founder=Axis(
            score=round(founder_value, 1),
            trend=trajectory_trend,
            claim_ids=founder_ids,
        ),
        market=Axis(
            score=round(market_value, 1),
            trend=_claim_trend(memo, market_ids),
            claim_ids=market_ids,
        ),
        idea_vs_market=Axis(
            score=round(idea_value, 1),
            trend=trajectory_trend,
            claim_ids=idea_ids,
        ),
    )


def _existing_ids(memo: Memo, groups: Sequence[Any]) -> list[str]:
    flattened: list[str] = []
    for value in groups:
        if isinstance(value, list):
            flattened.extend(str(item) for item in value)
        else:
            flattened.append(str(value))
    return list(dict.fromkeys(item for item in flattened if item in memo.claims))


def _claim_axis_value(memo: Memo, claim_ids: Sequence[str]) -> float:
    if not claim_ids:
        return 1.0
    weighted_total = 0.0
    for claim_id in claim_ids:
        claim = memo.claims[claim_id]
        trust = STATUS_WEIGHT[claim.verification_status]
        contradiction_penalty = min(len(claim.contradictions) * 0.16, 0.48)
        weighted_total += claim.confidence * trust * (1.0 - contradiction_penalty)
    normalized = weighted_total / len(claim_ids)
    return 1.0 + 9.0 * normalized


def _claim_trend(memo: Memo, claim_ids: Sequence[str]) -> str:
    if not claim_ids:
        return "stable"
    contradictions = sum(len(memo.claims[item].contradictions) for item in claim_ids)
    verified = sum(
        memo.claims[item].verification_status == "verified" for item in claim_ids
    )
    if contradictions:
        return "declining"
    if verified * 2 >= len(claim_ids):
        return "improving"
    return "stable"


def _trajectory_trend(rows: Sequence[Mapping[str, Any]]) -> str:
    points = sorted(rows, key=lambda row: _date_key(row.get("month")))
    if len(points) < 2:
        return "stable"
    count = len(points)
    x_center = (count - 1) / 2.0
    y_values = [float(point["score"]) for point in points]
    y_center = sum(y_values) / count
    numerator = sum(
        (index - x_center) * (value - y_center)
        for index, value in enumerate(y_values)
    )
    denominator = sum((index - x_center) ** 2 for index in range(count))
    slope = numerator / denominator if denominator else 0.0
    if slope > 0.003:
        return "improving"
    if slope < -0.003:
        return "declining"
    return "stable"


def _date_key(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value or "")


def _bounded(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))
