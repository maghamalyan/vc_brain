"""Unit tests for the A5 frozen-clock feature-row construction."""

import importlib.util
import json
import math
import sys
from datetime import date, datetime
from pathlib import Path

import polars as pl
import pytest

from vc_brain.features.build import NO_REPO_SENTINEL_MONTHS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "frozen_clock", PROJECT_ROOT / "scripts" / "frozen_clock.py"
)
assert _SPEC is not None and _SPEC.loader is not None
frozen_clock = importlib.util.module_from_spec(_SPEC)
sys.modules["frozen_clock"] = frozen_clock
_SPEC.loader.exec_module(frozen_clock)

FEATURE_MONTH = date(2023, 5, 1)


def _baselines() -> pl.DataFrame:
    months = [date(2023, month, 1) for month in (3, 4, 5)]
    return pl.DataFrame(
        {
            "month": [month for month in months for _ in range(2)],
            "event_type": ["PushEvent", "CreateEvent"] * len(months),
            "event_count": [2_000_000, 1_000_000] * len(months),
        }
    )


def _monthly() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "actor_login": ["alice", "alice", "bob"],
            "month": [date(2023, 5, 1), date(2023, 5, 1), date(2023, 4, 1)],
            "event_type": ["PushEvent", "PushEvent", "CreateEvent"],
            "is_weekend": [False, True, False],
            "event_count": [6, 4, 3],
        }
    )


def _creations() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "actor_login": ["alice"],
            "created_at": [datetime(2023, 4, 10, 12, 0, 0)],
        }
    )


def test_feature_row_matches_hand_built_example() -> None:
    frame = frozen_clock.build_feature_frame(
        _monthly(), _creations(), _baselines(), ["alice", "bob"], month=FEATURE_MONTH
    )
    alice = frame.filter(pl.col("gh_login") == "alice").row(0, named=True)

    # 10 raw May pushes against a 2M global May baseline -> 5.0 per million.
    assert alice["activity_push_1m"] == pytest.approx(5.0)
    assert alice["activity_push_3m"] == pytest.approx(5.0)
    assert alice["activity_push_12m"] == pytest.approx(5.0)
    # Recent 3-month mean 5/3 vs empty prior 12 months.
    assert alice["activity_push_ratio_3m_prior12m"] == pytest.approx(
        (5.0 / 3.0 + 1.0) / 1.0
    )
    assert alice["activity_push_delta_3m_prior12m"] == pytest.approx(5.0 / 3.0)
    # 4 of 10 mapped events fell on a weekend.
    assert alice["weekend_share_3m"] == pytest.approx(0.4)
    assert alice["tenure_months"] == pytest.approx(1.0)
    assert alice["no_gh_activity"] == 0.0
    # One repository created in April 2023.
    assert alice["new_repos_3m"] == pytest.approx(1.0)
    assert alice["cumulative_repos"] == pytest.approx(1.0)
    assert alice["months_since_last_new_repo"] == pytest.approx(1.0)

    bob = frame.filter(pl.col("gh_login") == "bob").row(0, named=True)
    # 3 raw April creates against a 1M global April baseline -> 3.0 per million.
    assert bob["activity_create_3m"] == pytest.approx(3.0)
    assert bob["activity_create_1m"] == pytest.approx(0.0)
    assert bob["months_since_last_new_repo"] == pytest.approx(NO_REPO_SENTINEL_MONTHS)
    assert bob["tenure_months"] == pytest.approx(2.0)


def test_zero_filled_blocks_identical_for_founder_and_pool() -> None:
    frame = frozen_clock.build_feature_frame(
        _monthly(), _creations(), _baselines(), ["alice", "bob"], month=FEATURE_MONTH
    )
    neutral_ratio_columns = {
        name
        for name in frozen_clock.ZERO_FILLED_FEATURES
        if name.endswith("_ratio_3m_prior12m")
    }
    rows = frame.sort("gh_login").select(frozen_clock.ZERO_FILLED_FEATURES).to_dicts()
    assert rows[0] == rows[1], "Founder and pool rows must share identical fills"
    for name, value in rows[0].items():
        expected = 1.0 if name in neutral_ratio_columns else 0.0
        assert value == pytest.approx(expected), name
        assert math.isfinite(value)


def test_produced_columns_cover_trained_feature_list() -> None:
    feature_list_path = PROJECT_ROOT / "data" / "models" / "feature_list.json"
    if not feature_list_path.exists():
        pytest.skip("Trained model artifacts are not available")
    expected = json.loads(feature_list_path.read_text(encoding="utf-8"))
    frame = frozen_clock.build_feature_frame(
        _monthly(), _creations(), _baselines(), ["alice"], month=FEATURE_MONTH
    )
    missing = [name for name in expected if name not in frame.columns]
    assert not missing
