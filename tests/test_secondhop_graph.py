"""Unit tests for the second-hop co-activity extraction script."""

import importlib.util
import sys
from datetime import date
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SPEC = importlib.util.spec_from_file_location(
    "secondhop", PROJECT_ROOT / "scripts" / "graph" / "secondhop.py"
)
assert _SPEC is not None and _SPEC.loader is not None
secondhop = importlib.util.module_from_spec(_SPEC)
sys.modules["secondhop"] = secondhop
_SPEC.loader.exec_module(secondhop)


def test_count_sql_is_repo_batched_and_bot_filtered() -> None:
    sql = secondhop.repo_actor_count_sql(["a/b", "c/d'x"])
    assert "repo_name IN ('a/b', 'c/d\\'x')" in sql
    assert "uniqExact(actor_login)" in sql
    assert "(?i)(bot|\\[bot\\]|-ci|automation)" in sql
    assert "actor_login IN" not in sql


def test_monthly_sql_shape() -> None:
    sql = secondhop.secondhop_monthly_sql(["a/b"])
    assert "toStartOfMonth(created_at) AS month" in sql
    assert "toString(event_type) AS event_type" in sql
    assert "created_at < toDateTime('2026-07-01 00:00:00')" in sql
    assert "GROUP BY repo_name, actor_login, month, event_type" in sql


def test_capped_sql_limits_per_repo_month() -> None:
    sql = secondhop.secondhop_capped_sql(["big/repo"])
    assert f"LIMIT {secondhop.TOP_ACTORS_PER_REPO_MONTH} BY repo_name, month" in sql
    assert "'__ALL__' AS event_type" in sql


def test_split_repo_lists_keeps_owned_and_small() -> None:
    universe = pl.DataFrame(
        {
            "repo_name": ["own/small", "own/big", "other/small", "other/big"],
            "owned_by_cohort": [True, True, False, False],
        }
    )
    counts = pl.DataFrame(
        {
            "repo_name": ["own/small", "own/big", "other/big"],
            "distinct_actors": [3, 5_000, 5_000],
        }
    )
    regular, capped, report = secondhop.split_repo_lists(universe, counts)
    # other/small is absent from counts -> treated as small and kept.
    assert sorted(regular) == ["other/small", "own/small"]
    assert capped == ["own/big"]
    assert report.height == 4


def test_cohort_login_map_is_case_insensitive_and_unique() -> None:
    cohort = pl.DataFrame(
        {
            "actor_login": ["Alice", "alice", "Bob"],
            "person_type": ["positive", "positive", "control"],
            "t_cutoff": [date(2023, 6, 1)] * 3,
        }
    )
    mapped = secondhop.cohort_login_map(cohort)
    assert mapped.height == 2
    assert set(mapped["login_lower"]) == {"alice", "bob"}


def test_degree_distribution_keys() -> None:
    neighbors = pl.DataFrame(
        {"cohort_login": ["a", "a", "b"], "neighbor_login": ["x", "y", "x"]}
    )
    dist = secondhop.degree_distribution(neighbors)
    assert dist["max"] == 2.0
    assert dist["min"] == 1.0
    assert set(dist) >= {"p50", "p90", "mean"}
