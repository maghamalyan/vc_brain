"""Map validated quarterly annotations into numeric panel features."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date, datetime

import polars as pl

from vc_brain.semantics.schema import BuildingCategory

BUILDING_CATEGORIES = tuple(category.value for category in BuildingCategory)
AUDIENCE_VALUES = ("self", "developers", "end_users", "customers")
COLLABORATION_VALUES = ("solo", "contributing", "leading", "team_forming")
INTENT_LEVELS = {"none": 0.0, "implicit": 1.0, "explicit": 2.0}
SCALE_FIELDS = (
    "productization_markers",
    "commercial_language",
    "seriousness",
    "domain_shift",
)


def annotation_level_feature_names() -> tuple[str, ...]:
    return (
        *(f"building_what_{value}" for value in BUILDING_CATEGORIES),
        *(f"audience_orientation_{value}" for value in AUDIENCE_VALUES),
        *SCALE_FIELDS,
        *(f"collaboration_posture_{value}" for value in COLLABORATION_VALUES),
        "stated_founding_intent",
    )


def annotation_feature_names() -> tuple[str, ...]:
    levels = annotation_level_feature_names()
    return (*levels, *(f"{name}_delta" for name in levels))


def _quarter_value(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raise TypeError(f"Expected date-like quarter, got {type(value).__name__}")


def _previous_quarter(value: date) -> date:
    if value.month == 1:
        return date(value.year - 1, 10, 1)
    return date(value.year, value.month - 3, 1)


def _one_hot(
    prefix: str, value: object, categories: tuple[str, ...]
) -> dict[str, float]:
    selected = str(value) if value is not None else None
    return {f"{prefix}_{category}": float(selected == category) for category in categories}


def annotation_feature_maps(
    annotations: pl.DataFrame,
) -> dict[tuple[str, date], dict[str, float | None]]:
    """Return exact-quarter levels and adjacent-quarter deltas by actor."""
    if annotations.is_empty():
        return {}
    required = {
        "actor_login",
        "quarter",
        "annotation_status",
        "building_what_category",
        "audience_orientation",
        "productization_markers",
        "commercial_language",
        "collaboration_posture",
        "stated_founding_intent",
        "seriousness",
        "domain_shift",
    }
    missing = required - set(annotations.columns)
    if missing:
        raise ValueError(f"annotations are missing required columns: {sorted(missing)}")
    successful = annotations.filter(pl.col("annotation_status") == "ok")
    duplicates = successful.group_by("actor_login", "quarter").len().filter(
        pl.col("len") != 1
    )
    if not duplicates.is_empty():
        raise ValueError("annotations contain duplicate successful person-quarters")

    levels: dict[tuple[str, date], dict[str, float | None]] = {}
    for row in successful.to_dicts():
        login = str(row["actor_login"]).lower()
        quarter = _quarter_value(row["quarter"])
        intent = str(row["stated_founding_intent"])
        if intent not in INTENT_LEVELS:
            raise ValueError(f"Unknown stated_founding_intent value: {intent!r}")
        values: dict[str, float | None] = {
            **_one_hot(
                "building_what", row["building_what_category"], BUILDING_CATEGORIES
            ),
            **_one_hot(
                "audience_orientation", row["audience_orientation"], AUDIENCE_VALUES
            ),
            **_one_hot(
                "collaboration_posture",
                row["collaboration_posture"],
                COLLABORATION_VALUES,
            ),
            "stated_founding_intent": INTENT_LEVELS[intent],
        }
        for field in SCALE_FIELDS:
            raw = row[field]
            values[field] = float(raw) if raw is not None else None
        levels[(login, quarter)] = values

    result: dict[tuple[str, date], dict[str, float | None]] = {}
    for (login, quarter), values in levels.items():
        previous = levels.get((login, _previous_quarter(quarter)))
        deltas = {
            f"{name}_delta": (
                float(value) - float(previous[name])
                if value is not None
                and previous is not None
                and previous[name] is not None
                else None
            )
            for name, value in values.items()
        }
        result[(login, quarter)] = {**values, **deltas}
    return result


def month_quarter(month: date) -> date:
    """Return the calendar-quarter start used for within-quarter forward fill."""
    return date(month.year, ((month.month - 1) // 3) * 3 + 1, 1)


def semantic_features_for_month(
    maps: Mapping[tuple[str, date], Mapping[str, float | None]],
    *,
    login: str,
    month: date,
) -> dict[str, float | None]:
    values = maps.get((login.lower(), month_quarter(month)), {})
    return {name: values.get(name) for name in annotation_feature_names()}
