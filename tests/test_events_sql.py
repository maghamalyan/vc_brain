from datetime import date

from vc_brain.ingest.sql import (
    monthly_agg_sql,
    negative_candidates_sql,
    owned_repo_agg_sql,
    repo_creations_sql,
)


ACTORS = [
    {"actor_login": "alice", "t_cutoff": date(2024, 1, 5)},
    {"actor_login": "o'brien", "t_cutoff": date(2023, 6, 1)},
]


def test_actor_queries_batch_logins_and_enforce_strict_48_month_window() -> None:
    for sql in (monthly_agg_sql(ACTORS), repo_creations_sql(ACTORS)):
        assert "actor_login IN ('alice', 'o\\'brien')" in sql
        assert "addMonths(toDateTime(a.t_cutoff), -48)" in sql
        assert "e.created_at < toDateTime(a.t_cutoff)" in sql


def test_owned_repo_query_has_verified_traction_received_contract() -> None:
    sql = owned_repo_agg_sql(ACTORS)

    assert "arrayElement(splitByChar('/', e.repo_name), 1) IN" in sql
    assert "e.actor_login != arrayElement" in sql
    assert "'WatchEvent', 'ForkEvent'" in sql
    assert "e.event_type = 'IssuesEvent' AND e.action = 'opened'" in sql
    assert "e.created_at < toDateTime(a.t_cutoff)" in sql


def test_candidate_query_uses_hash_sample_bot_filter_and_all_label_exclusion() -> None:
    sql = negative_candidates_sql(
        [date(2024, 1, 5)],
        hash_seed=2,
        excluded_logins=["founder", "low-confidence-founder"],
    )

    assert "cityHash64(e.actor_login) % 400 = 2" in sql
    assert "total_events >= 20" in sql
    assert "(?i)(bot|\\[bot\\]|-ci|automation)" in sql
    assert "e.actor_login NOT IN ('founder', 'low-confidence-founder')" in sql
    assert "cityHash64(e.actor_login) AS actor_hash" in sql
