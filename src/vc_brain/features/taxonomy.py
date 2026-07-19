"""Presentation-only mapping from feature names to the four capital families."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

CapitalFamily = Literal["cognitive", "human", "contextual", "financial"]
CAPITAL_FAMILIES: tuple[CapitalFamily, ...] = (
    "cognitive",
    "human",
    "contextual",
    "financial",
)


def capital_family(feature_name: str) -> CapitalFamily:
    """Classify observed signals without changing model weights."""
    if feature_name in {
        "context_divergence_2q",
        "domain_shift",
        "domain_shift_delta",
    }:
        return "cognitive"
    if feature_name.startswith(
        (
            "traction_",
            "own_repo_",
            "distinct_collaborators_",
            "new_collaborator_",
            "collaboration_posture",
        )
    ):
        return "contextual"
    if feature_name == "tenure_months" or feature_name.startswith(
        "activity_watch_given_"
    ):
        return "cognitive"
    return "human"


def capital_families(feature_names: Iterable[str]) -> dict[str, list[str]]:
    """Return a complete mapping, explicitly retaining empty financial capital."""
    result = {family: [] for family in CAPITAL_FAMILIES}
    for feature_name in feature_names:
        result[capital_family(feature_name)].append(feature_name)
    return result
