"""ClickHouse SQL builders with actor-specific leakage-safe windows."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Any

from vc_brain.ingest.contracts import HASH_MODULUS, WINDOW_MONTHS


def quote(value: str) -> str:
    return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"


def _actor_values(actors: Sequence[dict[str, Any]]) -> str:
    if not actors:
        raise ValueError("At least one actor is required")
    values = ", ".join(
        f"({quote(str(row['actor_login']))}, {quote(row['t_cutoff'].isoformat())})"
        for row in actors
    )
    return f"values('actor_login String, t_cutoff Date', {values})"


def _actor_login_list(actors: Sequence[dict[str, Any]]) -> str:
    return ", ".join(quote(str(row["actor_login"])) for row in actors)


def _cutoff_values(cutoffs: Sequence[date]) -> str:
    if not cutoffs:
        raise ValueError("At least one cutoff is required")
    unique = sorted(set(cutoffs))
    values = ", ".join(f"({quote(value.isoformat())})" for value in unique)
    return f"values('t_cutoff Date', {values})"


def baselines_sql() -> str:
    return """
SELECT
    toStartOfMonth(created_at) AS month,
    toString(event_type) AS event_type,
    toInt64(count()) AS event_count
FROM github_events
GROUP BY month, event_type
ORDER BY month, event_type
""".strip()


def monthly_agg_sql(actors: Sequence[dict[str, Any]]) -> str:
    return f"""
WITH cohort AS (SELECT * FROM {_actor_values(actors)})
SELECT
    e.actor_login AS actor_login,
    toStartOfMonth(e.created_at) AS month,
    toString(e.event_type) AS event_type,
    toDayOfWeek(e.created_at) IN (6, 7) AS is_weekend,
    toInt64(count()) AS event_count,
    a.t_cutoff AS t_cutoff
FROM github_events AS e
INNER JOIN cohort AS a ON e.actor_login = a.actor_login
WHERE e.actor_login IN ({_actor_login_list(actors)})
  AND e.created_at >= addMonths(toDateTime(a.t_cutoff), -{WINDOW_MONTHS})
  AND e.created_at < toDateTime(a.t_cutoff)
GROUP BY actor_login, month, event_type, is_weekend, t_cutoff
ORDER BY actor_login, month, event_type, is_weekend
""".strip()


def owned_repo_agg_sql(actors: Sequence[dict[str, Any]]) -> str:
    owner = "arrayElement(splitByChar('/', e.repo_name), 1)"
    return f"""
WITH cohort AS (SELECT * FROM {_actor_values(actors)})
SELECT
    {owner} AS owner_login,
    toStartOfMonth(e.created_at) AS month,
    toString(e.event_type) AS event_type,
    toInt64(count()) AS event_count,
    a.t_cutoff AS t_cutoff
FROM github_events AS e
INNER JOIN cohort AS a ON {owner} = a.actor_login
WHERE {owner} IN ({_actor_login_list(actors)})
  AND e.actor_login != {owner}
  AND e.created_at >= addMonths(toDateTime(a.t_cutoff), -{WINDOW_MONTHS})
  AND e.created_at < toDateTime(a.t_cutoff)
  AND (
      e.event_type IN ('WatchEvent', 'ForkEvent')
      OR (e.event_type = 'IssuesEvent' AND e.action = 'opened')
  )
GROUP BY owner_login, month, event_type, t_cutoff
ORDER BY owner_login, month, event_type
""".strip()


def repo_creations_sql(actors: Sequence[dict[str, Any]]) -> str:
    return f"""
WITH cohort AS (SELECT * FROM {_actor_values(actors)})
SELECT
    e.actor_login AS actor_login,
    e.created_at AS created_at,
    e.repo_name AS repo_name,
    a.t_cutoff AS t_cutoff
FROM github_events AS e
INNER JOIN cohort AS a ON e.actor_login = a.actor_login
WHERE e.actor_login IN ({_actor_login_list(actors)})
  AND e.event_type = 'CreateEvent'
  AND e.ref_type = 'repository'
  AND e.created_at >= addMonths(toDateTime(a.t_cutoff), -{WINDOW_MONTHS})
  AND e.created_at < toDateTime(a.t_cutoff)
ORDER BY actor_login, created_at, repo_name
""".strip()


def repo_names_audit_sql(actors: Sequence[dict[str, Any]]) -> str:
    return f"""
WITH cohort AS (SELECT * FROM {_actor_values(actors)})
SELECT DISTINCT
    e.actor_login AS actor_login,
    e.repo_name AS repo_name,
    a.t_cutoff AS t_cutoff
FROM github_events AS e
INNER JOIN cohort AS a ON e.actor_login = a.actor_login
WHERE e.actor_login IN ({_actor_login_list(actors)})
  AND e.repo_name != ''
  AND e.created_at >= addMonths(toDateTime(a.t_cutoff), -{WINDOW_MONTHS})
  AND e.created_at < toDateTime(a.t_cutoff)
ORDER BY actor_login, repo_name
""".strip()


def actor_stats_sql(actors: Sequence[dict[str, Any]]) -> str:
    return f"""
WITH cohort AS (SELECT * FROM {_actor_values(actors)})
SELECT
    e.actor_login AS actor_login,
    a.t_cutoff AS t_cutoff,
    toInt64(countIf(
        e.created_at >= addMonths(toDateTime(a.t_cutoff), -{WINDOW_MONTHS})
        AND e.created_at < toDateTime(a.t_cutoff)
    )) AS total_events,
    toInt32(toYear(min(e.created_at))) AS first_seen_year
FROM github_events AS e
INNER JOIN cohort AS a ON e.actor_login = a.actor_login
WHERE e.actor_login IN ({_actor_login_list(actors)})
  AND e.created_at < toDateTime(a.t_cutoff)
GROUP BY actor_login, t_cutoff
ORDER BY actor_login
""".strip()


def negative_candidates_sql(
    cutoffs: Sequence[date],
    *,
    hash_seed: int,
    excluded_logins: Sequence[str],
) -> str:
    if not 0 <= hash_seed < HASH_MODULUS:
        raise ValueError(f"hash_seed must be in [0, {HASH_MODULUS})")
    exclusions = ""
    if excluded_logins:
        exclusions = (
            "\n  AND e.actor_login NOT IN ("
            + ", ".join(quote(login) for login in sorted(set(excluded_logins)))
            + ")"
        )
    return f"""
WITH cutoffs AS (SELECT * FROM {_cutoff_values(cutoffs)})
SELECT
    e.actor_login AS actor_login,
    c.t_cutoff AS t_cutoff,
    toInt64(countIf(
        e.created_at >= addMonths(toDateTime(c.t_cutoff), -{WINDOW_MONTHS})
        AND e.created_at < toDateTime(c.t_cutoff)
    )) AS total_events,
    toInt32(toYear(min(e.created_at))) AS first_seen_year,
    cityHash64(e.actor_login) AS actor_hash,
    toUInt16({hash_seed}) AS hash_seed
FROM github_events AS e
CROSS JOIN cutoffs AS c
WHERE cityHash64(e.actor_login) % {HASH_MODULUS} = {hash_seed}
  AND e.actor_login != ''
  AND e.created_at < toDateTime(c.t_cutoff)
  AND NOT match(e.actor_login, '(?i)(bot|\\[bot\\]|-ci|automation)'){exclusions}
GROUP BY actor_login, t_cutoff
HAVING total_events >= 20
ORDER BY actor_hash, actor_login, t_cutoff
""".strip()
