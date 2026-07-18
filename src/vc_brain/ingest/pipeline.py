"""Stage orchestration for event extraction and deterministic case-control sampling."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import polars as pl

from vc_brain.ingest.clickhouse import ClickHouseClient
from vc_brain.ingest.cohort import (
    actor_records,
    confident_cohort,
    labeled_logins,
    load_founder_snapshot,
    subtract_months,
)
from vc_brain.ingest.contracts import (
    ACTIVITY_BAND_HIGH,
    ACTIVITY_BAND_LOW,
    BASELINES_PATH,
    BASELINE_SCHEMA,
    DATA_CARD_PATH,
    DEFAULT_HASH_SEEDS,
    EVENTS_DIR,
    FIRST_SEEN_YEAR_TOLERANCE,
    HASH_MODULUS,
    LEAKAGE_DROPS_PATH,
    MATCH_OFFSET,
    MONTHLY_AGG_DIR,
    MONTHLY_SCHEMA,
    NEGATIVE_CANDIDATES_PATH,
    NEGATIVE_MATCHES_PATH,
    NEGATIVES_PER_POSITIVE,
    OWNED_REPO_AGG_DIR,
    OWNED_REPO_SCHEMA,
    REPO_CREATIONS_DIR,
    REPO_CREATION_SCHEMA,
)
from vc_brain.ingest.leakage import (
    assert_no_founders_in_negatives,
    assert_temporal_leakage_free,
    company_repo_leakage_drops,
)
from vc_brain.ingest.sql import (
    actor_stats_sql,
    baselines_sql,
    monthly_agg_sql,
    negative_candidates_sql,
    owned_repo_agg_sql,
    repo_creations_sql,
    repo_names_audit_sql,
)
from vc_brain.ingest.storage import atomic_write_parquet, atomic_write_text

LOGGER = logging.getLogger(__name__)


def _conform(frame: pl.DataFrame, schema: dict[str, pl.DataType]) -> pl.DataFrame:
    result = frame
    for column, dtype in schema.items():
        if column not in result.columns:
            result = result.with_columns(pl.lit(None, dtype=dtype).alias(column))
    return result.select(
        pl.col(column).cast(dtype, strict=False).alias(column)
        for column, dtype in schema.items()
    )


def extract_baselines(
    client: ClickHouseClient,
    *,
    output_path: Path = BASELINES_PATH,
) -> pl.DataFrame:
    frame = _conform(client.query(baselines_sql()), BASELINE_SCHEMA).sort(
        "month", "event_type"
    )
    if frame.is_empty() or frame.get_column("event_count").min() < 1:
        raise ValueError("ClickHouse returned an empty or invalid global baseline")
    atomic_write_parquet(frame, output_path)
    LOGGER.info("Baseline complete rows=%d path=%s", frame.height, output_path)
    return frame


def _query_actor_rows(
    client: ClickHouseClient,
    cohort: pl.DataFrame,
    builder: Any,
) -> pl.DataFrame:
    return client.query_actor_batches(actor_records(cohort), builder)


def audit_company_repo_leakage(
    client: ClickHouseClient,
    cohort: pl.DataFrame,
    *,
    output_path: Path = LEAKAGE_DROPS_PATH,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    repo_names = _query_actor_rows(client, cohort, repo_names_audit_sql)
    drops = company_repo_leakage_drops(repo_names, cohort)
    atomic_write_parquet(drops, output_path)
    if drops.is_empty():
        return cohort, drops
    dropped_logins = drops.get_column("actor_login")
    kept = cohort.filter(~pl.col("actor_login").is_in(dropped_logins.implode()))
    LOGGER.warning(
        "Dropped company-domain leakage actors=%d kept=%d",
        drops.height,
        kept.height,
    )
    return kept, drops


def extract_monthly_agg(
    client: ClickHouseClient,
    cohort: pl.DataFrame,
    *,
    cohort_name: str,
    output_path: Path,
) -> pl.DataFrame:
    raw = _query_actor_rows(client, cohort, monthly_agg_sql)
    raw = raw.with_columns(
        pl.lit(cohort_name).alias("cohort"),
        pl.lit(False).alias("no_gh_activity"),
    )
    frame = _conform(raw, MONTHLY_SCHEMA)
    observed = set(frame.get_column("actor_login").drop_nulls().to_list())
    missing = [
        row
        for row in actor_records(cohort)
        if row["actor_login"] not in observed
    ]
    if missing:
        sentinels = pl.DataFrame(
            [
                {
                    "actor_login": row["actor_login"],
                    "month": subtract_months(row["t_cutoff"], 1).replace(day=1),
                    "event_type": "__NO_ACTIVITY__",
                    "is_weekend": False,
                    "event_count": 0,
                    "t_cutoff": row["t_cutoff"],
                    "cohort": cohort_name,
                    "no_gh_activity": True,
                }
                for row in missing
            ],
            schema=MONTHLY_SCHEMA,
            strict=False,
        )
        frame = pl.concat([frame, sentinels])
    frame = frame.sort("actor_login", "month", "event_type", "is_weekend")
    assert_temporal_leakage_free(frame)
    atomic_write_parquet(frame, output_path)
    LOGGER.info(
        "Monthly aggregate complete cohort=%s actors=%d rows=%d no_activity=%d",
        cohort_name,
        cohort.height,
        frame.height,
        len(missing),
    )
    return frame


def extract_owned_repo_agg(
    client: ClickHouseClient,
    cohort: pl.DataFrame,
    *,
    cohort_name: str,
    output_path: Path,
) -> pl.DataFrame:
    raw = _query_actor_rows(client, cohort, owned_repo_agg_sql).with_columns(
        pl.lit(cohort_name).alias("cohort")
    )
    frame = _conform(raw, OWNED_REPO_SCHEMA).sort(
        "owner_login", "month", "event_type"
    )
    assert_temporal_leakage_free(frame)
    atomic_write_parquet(frame, output_path)
    return frame


def extract_repo_creations(
    client: ClickHouseClient,
    cohort: pl.DataFrame,
    *,
    cohort_name: str,
    output_path: Path,
) -> pl.DataFrame:
    raw = _query_actor_rows(client, cohort, repo_creations_sql).with_columns(
        pl.lit(cohort_name).alias("cohort")
    )
    frame = _conform(raw, REPO_CREATION_SCHEMA).sort(
        "actor_login", "created_at", "repo_name"
    )
    assert_temporal_leakage_free(frame, time_column="created_at")
    atomic_write_parquet(frame, output_path)
    return frame


def actor_stats(client: ClickHouseClient, cohort: pl.DataFrame) -> pl.DataFrame:
    raw = _query_actor_rows(client, cohort, actor_stats_sql)
    schema = {
        "actor_login": pl.String,
        "t_cutoff": pl.Date,
        "total_events": pl.Int64,
        "first_seen_year": pl.Int32,
    }
    frame = _conform(raw, schema)
    missing = cohort.join(frame, on=["actor_login", "t_cutoff"], how="anti").select(
        "actor_login", "t_cutoff"
    )
    if not missing.is_empty():
        frame = pl.concat(
            [
                frame,
                missing.with_columns(
                    pl.lit(0, dtype=pl.Int64).alias("total_events"),
                    pl.lit(None, dtype=pl.Int32).alias("first_seen_year"),
                ),
            ]
        )
    return frame.sort("actor_login")


def build_candidate_pool(
    client: ClickHouseClient,
    positives: pl.DataFrame,
    founder_logins: set[str],
    *,
    hash_seeds: tuple[int, ...] = DEFAULT_HASH_SEEDS,
    output_path: Path = NEGATIVE_CANDIDATES_PATH,
) -> pl.DataFrame:
    cutoffs = positives.get_column("t_cutoff").drop_nulls().unique().to_list()
    frames = [
        client.query(
            negative_candidates_sql(
                cutoffs,
                hash_seed=seed,
                excluded_logins=sorted(founder_logins),
            )
        )
        for seed in hash_seeds
    ]
    schema = {
        "actor_login": pl.String,
        "t_cutoff": pl.Date,
        "total_events": pl.Int64,
        "first_seen_year": pl.Int32,
        "actor_hash": pl.UInt64,
        "hash_seed": pl.UInt16,
    }
    frame = _conform(
        pl.concat(frames, how="diagonal_relaxed") if frames else pl.DataFrame(),
        schema,
    ).unique(subset=["actor_login", "t_cutoff"], keep="first")
    assert_no_founders_in_negatives(frame, founder_logins)
    atomic_write_parquet(frame, output_path)
    return frame


def match_negatives(
    positives: pl.DataFrame,
    candidates: pl.DataFrame,
    founder_logins: set[str],
    *,
    k: int = NEGATIVES_PER_POSITIVE,
    offset: int = MATCH_OFFSET,
) -> pl.DataFrame:
    """Deterministically match without replacement using ClickHouse actor hashes."""
    if k < 1:
        raise ValueError("k must be positive")
    columns = {
        "actor_login": pl.String,
        "t_cutoff": pl.Date,
        "matched_positive_login": pl.String,
        "positive_total_events": pl.Int64,
        "total_events": pl.Int64,
        "first_seen_year": pl.Int32,
        "actor_hash": pl.UInt64,
        "match_rank": pl.UInt8,
    }
    normalized_founders = {login.lower() for login in founder_logins}
    candidates = candidates.filter(
        ~pl.col("actor_login").str.to_lowercase().is_in(list(normalized_founders))
    )
    used: set[str] = set()
    matches: list[dict[str, object]] = []
    ordered_positives = positives.sort("actor_login", "t_cutoff")
    for positive in ordered_positives.to_dicts():
        total = int(positive.get("total_events") or 0)
        year = positive.get("first_seen_year")
        if total <= 0 or year is None:
            continue
        eligible = candidates.filter(
            (pl.col("t_cutoff") == positive["t_cutoff"])
            & (pl.col("total_events") >= total * ACTIVITY_BAND_LOW)
            & (pl.col("total_events") <= total * ACTIVITY_BAND_HIGH)
            & (
                (pl.col("first_seen_year") - int(year)).abs()
                <= FIRST_SEEN_YEAR_TOLERANCE
            )
            & ~pl.col("actor_login").is_in(list(used))
        ).sort("actor_hash", "actor_login")
        rows = eligible.to_dicts()
        if rows:
            rotation = offset % len(rows)
            rows = rows[rotation:] + rows[:rotation]
        for rank, candidate in enumerate(rows[:k], start=1):
            login = str(candidate["actor_login"])
            used.add(login)
            matches.append(
                {
                    "actor_login": login,
                    "t_cutoff": positive["t_cutoff"],
                    "matched_positive_login": positive["actor_login"],
                    "positive_total_events": total,
                    "total_events": candidate["total_events"],
                    "first_seen_year": candidate["first_seen_year"],
                    "actor_hash": candidate["actor_hash"],
                    "match_rank": rank,
                }
            )
    frame = pl.DataFrame(matches, schema=columns, strict=False)
    assert_no_founders_in_negatives(frame, founder_logins)
    return frame


def render_data_card(events_dir: Path = EVENTS_DIR) -> str:
    def rows(path: Path) -> int:
        return pl.scan_parquet(path).select(pl.len()).collect().item() if path.exists() else 0

    positive_path = events_dir / "monthly_agg" / "positives.parquet"
    negative_path = events_dir / "monthly_agg" / "negatives.parquet"
    matched_path = events_dir / "negatives" / "matched.parquet"
    candidates_path = events_dir / "negatives" / "candidates.parquet"
    drops_path = events_dir / "leakage" / "company_domain_drops.parquet"
    matched = rows(matched_path)
    positive_rows = rows(positive_path)
    negative_rows = rows(negative_path)
    positive_actors = 0
    negative_actors = 0
    no_activity = 0
    if positive_path.exists():
        frame = pl.read_parquet(positive_path)
        positive_actors = frame.get_column("actor_login").n_unique()
        no_activity = frame.filter(pl.col("no_gh_activity")).height
    if negative_path.exists():
        negative_actors = pl.read_parquet(negative_path).get_column("actor_login").n_unique()
    ratio = matched / positive_actors if positive_actors else 0.0
    dropped_actors = rows(drops_path)
    eligible_positive_actors = positive_actors + dropped_actors
    coverage = positive_actors / eligible_positive_actors if eligible_positive_actors else 0.0
    return f"""# Event Extraction Data Card

Generated: `{datetime.now(UTC).isoformat()}`

## Coverage

- Positive aggregate actors: **{positive_actors:,}**
- Positive aggregate rows: **{positive_rows:,}**
- Positive actor coverage after leakage drops: **{coverage:.1%}**
- Positive actors with no GitHub activity in-window: **{no_activity:,}**
- Negative aggregate actors: **{negative_actors:,}**
- Negative aggregate rows: **{negative_rows:,}**
- Positive owned-repo aggregate rows: **{rows(events_dir / 'owned_repo_agg' / 'positives.parquet'):,}**
- Negative owned-repo aggregate rows: **{rows(events_dir / 'owned_repo_agg' / 'negatives.parquet'):,}**
- Positive repository-creation rows: **{rows(events_dir / 'repo_creations' / 'positives.parquet'):,}**
- Negative repository-creation rows: **{rows(events_dir / 'repo_creations' / 'negatives.parquet'):,}**
- Candidate actor-cutoff rows: **{rows(candidates_path):,}**
- Final matched negatives: **{matched:,}**
- Realized negatives per extracted positive: **{ratio:.3f}** (target: {NEGATIVES_PER_POSITIVE})
- Company-domain leakage drops: **{dropped_actors:,}**
- Global baseline rows: **{rows(events_dir / 'baselines' / 'monthly_totals.parquet'):,}**

## Sampling contract

Candidates are sampled where `cityHash64(actor_login) % {HASH_MODULUS}` is one of
`{list(DEFAULT_HASH_SEEDS)}`. Each positive receives up to {NEGATIVES_PER_POSITIVE}
negatives, without replacement, from the same pseudo-cutoff. Eligible activity is
within [{ACTIVITY_BAND_LOW:.1f}x, {ACTIVITY_BAND_HIGH:.1f}x] of the positive's own
48-month event total and first-seen year is within ±{FIRST_SEEN_YEAR_TOLERANCE}.
Candidates are ordered by ClickHouse `cityHash64`, then rotated by the fixed offset
{MATCH_OFFSET}. The exact realized ratio above must be used for probability correction.

## Leakage controls

- SQL enforces `created_at >= t_cutoff - 48 months` and `created_at < t_cutoff`.
- Every loaded aggregate is asserted to have `month < t_cutoff`.
- Every non-null founder login, regardless of confidence, is excluded from negatives
  in SQL and asserted absent after matching.
- Actors whose company website domain appears in a repo name in their pre-cutoff
  feature window are dropped and recorded under `leakage/`.

## Known gaps and limitations

- Bot exclusion is regex-only (`bot`, `[bot]`, `-ci`, `automation`); GitHub user type
  is unavailable in the playground schema.
- The ClickHouse playground is shared, best-effort infrastructure. Results are cached
  by exact SQL hash; retries are bounded, and cached snapshots may differ by run date.
- GitHub events start in 2011-02, so early actors can have left-truncated histories.
- Deleted/private activity, renamed actors and repos, and events absent from GH Archive
  are not recoverable here.
- A `__NO_ACTIVITY__` zero-count sentinel preserves confident actors with no events;
  it is not a GitHub event type and must not be treated as activity.
"""


def write_data_card(events_dir: Path = EVENTS_DIR) -> None:
    atomic_write_text(render_data_card(events_dir), events_dir / DATA_CARD_PATH.name)


def run_baselines(client: ClickHouseClient) -> pl.DataFrame:
    frame = extract_baselines(client)
    write_data_card()
    return frame


def _load_positive_cohort(actor_limit: int | None = None) -> tuple[pl.DataFrame, pl.DataFrame]:
    founders = load_founder_snapshot()
    cohort = confident_cohort(founders)
    if actor_limit is not None:
        if actor_limit < 1:
            raise ValueError("actor_limit must be positive")
        cohort = cohort.head(actor_limit)
    if cohort.is_empty():
        raise ValueError("No confident founder GitHub actors are available")
    return founders, cohort


def run_positives(
    client: ClickHouseClient,
    *,
    actor_limit: int | None = None,
) -> pl.DataFrame:
    _, cohort = _load_positive_cohort(actor_limit)
    smoke = actor_limit is not None
    suffix = f"smoke_{actor_limit}" if smoke else "positives"
    leakage_path = (
        EVENTS_DIR / "leakage" / f"{suffix}_company_domain_drops.parquet"
        if smoke
        else LEAKAGE_DROPS_PATH
    )
    cohort, _ = audit_company_repo_leakage(
        client, cohort, output_path=leakage_path
    )
    frame = extract_monthly_agg(
        client,
        cohort,
        cohort_name="positives",
        output_path=MONTHLY_AGG_DIR / f"{suffix}.parquet",
    )
    if not smoke:
        write_data_card()
    return frame


def run_negatives(client: ClickHouseClient) -> pl.DataFrame:
    founders, cohort = _load_positive_cohort()
    cohort, _ = audit_company_repo_leakage(client, cohort)
    stats = actor_stats(client, cohort)
    all_founder_logins = labeled_logins(founders)
    candidates = build_candidate_pool(client, stats, all_founder_logins)
    matches = match_negatives(stats, candidates, all_founder_logins)
    atomic_write_parquet(matches, NEGATIVE_MATCHES_PATH)
    negative_cohort = matches.select("actor_login", "t_cutoff").unique()
    frame = extract_monthly_agg(
        client,
        negative_cohort,
        cohort_name="negatives",
        output_path=MONTHLY_AGG_DIR / "negatives.parquet",
    )
    assert_no_founders_in_negatives(frame, all_founder_logins)
    write_data_card()
    return frame


def run_repos(client: ClickHouseClient) -> dict[str, pl.DataFrame]:
    _, positive_cohort = _load_positive_cohort()
    positive_cohort, _ = audit_company_repo_leakage(client, positive_cohort)
    cohorts = {"positives": positive_cohort}
    if NEGATIVE_MATCHES_PATH.exists():
        cohorts["negatives"] = (
            pl.read_parquet(NEGATIVE_MATCHES_PATH)
            .select("actor_login", "t_cutoff")
            .unique()
        )
    outputs: dict[str, pl.DataFrame] = {}
    for name, cohort in cohorts.items():
        outputs[f"{name}_creations"] = extract_repo_creations(
            client,
            cohort,
            cohort_name=name,
            output_path=REPO_CREATIONS_DIR / f"{name}.parquet",
        )
        outputs[f"{name}_owned"] = extract_owned_repo_agg(
            client,
            cohort,
            cohort_name=name,
            output_path=OWNED_REPO_AGG_DIR / f"{name}.parquet",
        )
    write_data_card()
    return outputs
