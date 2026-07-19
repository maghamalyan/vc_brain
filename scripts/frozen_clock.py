"""A5 — Frozen-clock top-of-funnel precision simulation at vintage 2023-06-01.

Scores a deterministic 8,000-actor sample of the hash-sampled candidate pool
plus every scoreable future YC founder, using only data before the vintage, and
reports precision@K / lift against the implied base rate.

Reuses feature internals from ``vc_brain.features.build`` without modifying it.
The ownership / collaboration / owned-repo traction blocks are NOT extracted for
the pool, so those feature blocks are neutral-filled identically for every
scored actor (pool and founders) by feeding the feature builder empty maps.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from vc_brain.features.build import (  # noqa: E402
    _activity_maps,
    _feature_row,
    _repo_maps,
)
from vc_brain.ingest import sql  # noqa: E402
from vc_brain.ingest.clickhouse import ClickHouseClient  # noqa: E402
from vc_brain.ingest.contracts import (  # noqa: E402
    BASELINES_PATH,
    CONFIDENT_GITHUB_THRESHOLD,
    FOUNDERS_PATH,
    MONTHLY_AGG_DIR,
    NEGATIVE_CANDIDATES_PATH,
    REPO_CREATIONS_DIR,
)
from vc_brain.models.train import load_training_bundle, predict_probabilities  # noqa: E402

VINTAGE = date(2023, 6, 1)
FEATURE_MONTH = date(2023, 5, 1)
DEFAULT_POOL_SIZE = 8_000
SAMPLE_SEED = 7
MIN_TOTAL_EVENTS = 20
NO_ACTIVITY_SENTINEL = "__NO_ACTIVITY__"
EVAL_JSON_PATH = PROJECT_ROOT / "data" / "eval" / "frozen_clock_2023.json"
EVAL_MD_PATH = PROJECT_ROOT / "data" / "eval" / "frozen_clock_2023.md"

# Feature names produced from the deliberately empty ownership/collab/traction
# maps; every scored actor receives identical neutral values in these columns.
ZERO_FILLED_FEATURES = (
    "traction_stars_3m",
    "traction_stars_12m",
    "traction_stars_ratio_3m_prior12m",
    "traction_stars_delta_3m_prior12m",
    "traction_forks_3m",
    "traction_forks_12m",
    "traction_forks_ratio_3m_prior12m",
    "traction_forks_delta_3m_prior12m",
    "traction_issues_by_others_3m",
    "traction_issues_by_others_12m",
    "traction_issues_by_others_ratio_3m_prior12m",
    "traction_issues_by_others_delta_3m_prior12m",
    "own_repo_share_3m",
    "own_repo_share_delta_3m_prior12m",
    "distinct_collaborators_3m",
    "distinct_collaborators_delta_3m_prior12m",
    "new_collaborator_burst_zscore",
)


@dataclass
class FounderSelection:
    monthly: pl.DataFrame
    creations: pl.DataFrame
    scored_logins: list[str]
    near_window_logins: set[str]
    counts: dict[str, int]


def confident_founder_logins(labels: pl.DataFrame) -> set[str]:
    """Lowercased confident GitHub logins across all label rows."""
    eligible = labels.filter(
        pl.col("gh_login").is_not_null()
        & (pl.col("gh_login").str.strip_chars() != "")
        & (pl.col("gh_confidence") >= CONFIDENT_GITHUB_THRESHOLD)
    )
    return set(eligible.get_column("gh_login").str.to_lowercase().unique().to_list())


def sample_pool(
    candidates: pl.DataFrame,
    excluded_logins: set[str],
    *,
    pool_size: int,
    seed: int = SAMPLE_SEED,
) -> pl.DataFrame:
    """Deterministically sample eligible pool actors at the vintage cutoff."""
    eligible = (
        candidates.filter(
            (pl.col("t_cutoff") == VINTAGE)
            & (pl.col("total_events") >= MIN_TOTAL_EVENTS)
        )
        .with_columns(pl.col("actor_login").str.to_lowercase().alias("login_lower"))
        .filter(~pl.col("login_lower").is_in(sorted(excluded_logins)))
        .sort("actor_login")
        .unique(subset=["login_lower"], keep="first", maintain_order=True)
    )
    if eligible.height < pool_size:
        raise ValueError(
            f"Eligible pool has {eligible.height} actors, fewer than {pool_size}"
        )
    return eligible.sample(n=pool_size, seed=seed).sort("actor_login")


def extract_pool_frames(
    pool: pl.DataFrame, client: ClickHouseClient
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Fetch monthly aggregates and repo creations for pool actors (cached)."""
    actors = [
        {"actor_login": login, "t_cutoff": VINTAGE}
        for login in pool.get_column("actor_login").to_list()
    ]
    monthly = client.query_actor_batches(actors, sql.monthly_agg_sql)
    creations = client.query_actor_batches(actors, sql.repo_creations_sql)
    return monthly, creations


def select_future_founders(
    labels: pl.DataFrame,
    positives_monthly: pl.DataFrame,
    positives_creations: pl.DataFrame,
) -> FounderSelection:
    """Pick scoreable future founders from cached aggregates; count every drop."""
    confident = labels.filter(
        pl.col("gh_login").is_not_null()
        & (pl.col("gh_login").str.strip_chars() != "")
        & (pl.col("gh_confidence") >= CONFIDENT_GITHUB_THRESHOLD)
        & pl.col("batch_start_date").is_not_null()
    ).with_columns(pl.col("gh_login").str.to_lowercase())
    per_login = confident.group_by("gh_login").agg(
        pl.col("batch_start_date").min().alias("min_batch_start")
    )
    future = per_login.filter(pl.col("min_batch_start") > VINTAGE)
    future_logins = set(future.get_column("gh_login").to_list())

    monthly = positives_monthly.with_columns(
        pl.col("actor_login").str.to_lowercase()
    ).filter(pl.col("actor_login").is_in(sorted(future_logins)))
    cached_logins = set(monthly.get_column("actor_login").unique().to_list())

    activity = monthly.filter(
        (pl.col("event_type") != NO_ACTIVITY_SENTINEL) & (pl.col("event_count") > 0)
    )
    per_actor = activity.group_by("actor_login").agg(
        pl.col("month").min().alias("first_month"),
        pl.col("t_cutoff").first().alias("t_cutoff"),
    )
    scoreable = per_actor.filter(pl.col("first_month") < VINTAGE)
    scored_logins = sorted(scoreable.get_column("actor_login").to_list())
    near_window_logins = set(
        scoreable.filter(pl.col("t_cutoff") < VINTAGE)
        .get_column("actor_login")
        .to_list()
    )
    truncated = len(near_window_logins)

    counts = {
        "future_founder_logins": len(future_logins),
        "without_cached_aggregates": len(future_logins - cached_logins),
        "cached_without_any_pre_cutoff_activity": len(cached_logins)
        - len(scored_logins),
        "scored": len(scored_logins),
        "scored_with_truncated_window_t_cutoff_before_vintage": truncated,
    }

    founder_monthly = activity.filter(
        pl.col("actor_login").is_in(scored_logins) & (pl.col("month") < VINTAGE)
    )
    founder_creations = positives_creations.with_columns(
        pl.col("actor_login").str.to_lowercase()
    ).filter(
        pl.col("actor_login").is_in(scored_logins)
        & (pl.col("created_at").cast(pl.Date) < VINTAGE)
    )
    return FounderSelection(
        founder_monthly, founder_creations, scored_logins, near_window_logins, counts
    )


def build_feature_frame(
    monthly: pl.DataFrame,
    creations: pl.DataFrame,
    baselines: pl.DataFrame,
    logins: list[str],
    *,
    month: date = FEATURE_MONTH,
) -> pl.DataFrame:
    """One feature row per login at ``month`` using build.py internals.

    Traction, ownership, and collaboration maps are intentionally empty so
    those blocks come out neutral-filled identically for every login.
    """
    normalized, weekend, total = _activity_maps(monthly, baselines)
    repos = _repo_maps(creations)
    rows = []
    for login in sorted(set(logins)):
        features = _feature_row(
            login,
            month,
            normalized=normalized,
            weekend=weekend,
            total=total,
            traction={},
            repos=repos,
            own_repo={},
            ownership_total={},
            collaborators={},
            composition={},
            composition_event_types=(),
        )
        rows.append({"gh_login": login, **features})
    return pl.DataFrame(rows, infer_schema_length=None)


def assert_no_leakage(monthly: pl.DataFrame, creations: pl.DataFrame) -> None:
    if monthly.filter(pl.col("month") >= VINTAGE).height:
        raise AssertionError("Monthly aggregate rows at or after the vintage cutoff")
    if creations.filter(pl.col("created_at").cast(pl.Date) >= VINTAGE).height:
        raise AssertionError("Repo creations at or after the vintage cutoff")


def rank_and_score(
    features: pl.DataFrame,
    founder_logins: set[str],
) -> pl.DataFrame:
    bundle = load_training_bundle()
    missing = [name for name in bundle.feature_names if name not in features.columns]
    if missing:
        raise ValueError(f"Feature frame is missing model features: {missing}")
    scores = predict_probabilities(
        bundle.selected_model, features, bundle.feature_names
    )
    return (
        features.select("gh_login")
        .with_columns(
            pl.Series("score", scores),
            pl.col("gh_login").is_in(sorted(founder_logins)).alias("is_future_founder"),
        )
        .sort(["score", "gh_login"], descending=[True, False])
        .with_row_index("rank", offset=1)
    )


def precision_at(ranked: pl.DataFrame, k: int) -> float:
    return ranked.head(k).get_column("is_future_founder").sum() / k


def compute_metrics(
    ranked: pl.DataFrame, near_window_logins: set[str]
) -> dict[str, float | int]:
    total = ranked.height
    n_founders = int(ranked.get_column("is_future_founder").sum())
    base_rate = n_founders / total
    founders = ranked.filter(pl.col("is_future_founder")).with_columns(
        pl.col("gh_login").is_in(sorted(near_window_logins)).alias("near_window")
    )
    founder_ranks = founders.get_column("rank")
    near = founders.filter(pl.col("near_window")).get_column("rank")
    far = founders.filter(~pl.col("near_window")).get_column("rank")
    metrics: dict[str, float | int] = {
        "total_scored": total,
        "n_future_founders": n_founders,
        "implied_base_rate": base_rate,
        "median_founder_rank_percentile": float((founder_ranks / total).median()),
        "n_founders_near_hazard_window": near.len(),
        "median_rank_percentile_founders_near_hazard_window": float(
            (near / total).median()
        ),
        "median_rank_percentile_founders_far_from_hazard_window": float(
            (far / total).median()
        ),
    }
    for k in (100, 500):
        precision = precision_at(ranked, k)
        metrics[f"precision_at_{k}"] = precision
        metrics[f"hits_at_{k}"] = int(round(precision * k))
        metrics[f"lift_at_{k}"] = precision / base_rate if base_rate else float("nan")
    return metrics


def write_reports(
    metrics: dict[str, float | int],
    founder_counts: dict[str, int],
    config: dict[str, object],
) -> None:
    caveats = [
        "Outcome labels are YC founders only: any pool actor who founded a "
        "non-YC company, or a YC founder we could not confidently resolve to a "
        "GitHub login, counts as a negative. Every precision number is a floor.",
        "Population framing: the scored set is a deterministic 8,000-actor "
        "subsample (seed 7) of the 102,750-actor hash-sampled candidate pool "
        "(cityHash64 seeds 0-2 of modulus 400, i.e. roughly 3/400 of active "
        "GitHub) PLUS all scoreable future founders. Concentrating every known "
        "future founder into the subsample inflates the base rate versus the "
        "full pool (about 12.3x), so precision@K is specific to this synthetic "
        "population; lift versus the implied base rate is the transferable "
        "number.",
        "Ownership, collaboration, and owned-repo traction aggregates were not "
        "extracted for the pool; those feature blocks are neutral-filled "
        "identically for ALL scored actors (founders included, discarding "
        "their cached values) so the comparison is fair. Neutral fill means "
        "the exact values build.py produces from zero activity: 0 for sums, "
        "shares, deltas, and z-scores, 1.0 for smoothed ratios.",
        f"{founder_counts['scored_with_truncated_window_t_cutoff_before_vintage']} "
        "scored founders have their own t_cutoff before the vintage, so their "
        "feature window ends early (features are up to 11 months stale at "
        "scoring time). No founder window was extended past their t_cutoff.",
        "Founders whose own t_cutoff is after the vintage were truncated to "
        "months strictly before 2023-06-01; because their cached extraction "
        "window is 48 months ending at their own later t_cutoff, they can "
        "carry slightly shorter usable histories than pool actors.",
        "Pool actors resolved to founders with gh_confidence below 0.5 were "
        "not excluded; if any is a real founder it counts as a negative.",
    ]
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "experiment": "A5 frozen-clock top-of-funnel precision",
        "config": config,
        "founder_selection_counts": founder_counts,
        "metrics": metrics,
        "caveats": caveats,
    }
    EVAL_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVAL_JSON_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    lines = [
        "# A5 — Frozen-clock top-of-funnel precision (vintage 2023-06-01)",
        "",
        "Every scored actor is frozen at 2023-06-01: features come only from "
        "events strictly before that date, at feature month 2023-05-01, scored "
        "with the trained LightGBM hazard model. Outcome: did the actor later "
        "become a confidently-resolved YC founder (batch start after the "
        "vintage)?",
        "",
        "## Headline numbers",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Total scored | {metrics['total_scored']:,} |",
        f"| Future founders in population | {metrics['n_future_founders']} |",
        f"| Implied base rate | {metrics['implied_base_rate']:.4f} |",
        f"| Precision@100 | {metrics['precision_at_100']:.3f} "
        f"({metrics['hits_at_100']}/100) |",
        f"| Precision@500 | {metrics['precision_at_500']:.3f} "
        f"({metrics['hits_at_500']}/500) |",
        f"| Lift@100 | {metrics['lift_at_100']:.2f}x |",
        f"| Lift@500 | {metrics['lift_at_500']:.2f}x |",
        f"| Median founder rank percentile | "
        f"{metrics['median_founder_rank_percentile']:.3f} |",
        "",
        "## Proximity to the hazard window matters",
        "",
        "The model is trained to fire 12-15 months before batch start. At a "
        "frozen calendar clock, most future founders (2025-2027 batches) are "
        "years away from that window, and they score near chance. Founders "
        "whose batch started within 12 months of the vintage (their own "
        "t_cutoff falls before it) are exactly the ones the detector is built "
        "to catch, and they rank far better:",
        "",
        "| Founder group | n | Median rank percentile |",
        "| --- | --- | --- |",
        f"| Batch within 12 months after the vintage (near hazard window) | "
        f"{metrics['n_founders_near_hazard_window']} | "
        f"{metrics['median_rank_percentile_founders_near_hazard_window']:.3f} |",
        f"| Later batches (far from hazard window) | "
        f"{metrics['n_future_founders'] - metrics['n_founders_near_hazard_window']}"
        f" | "
        f"{metrics['median_rank_percentile_founders_far_from_hazard_window']:.3f}"
        f" |",
        "",
        "## Founder selection accounting (no silent drops)",
        "",
        "| Count | Value |",
        "| --- | --- |",
    ]
    lines.extend(
        f"| {name.replace('_', ' ')} | {value} |"
        for name, value in founder_counts.items()
    )
    lines.extend(["", "## Caveats", ""])
    lines.extend(f"- {caveat}" for caveat in caveats)
    lines.append("")
    EVAL_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pool-size", type=int, default=DEFAULT_POOL_SIZE)
    args = parser.parse_args()

    labels = pl.read_parquet(FOUNDERS_PATH)
    candidates = pl.read_parquet(NEGATIVE_CANDIDATES_PATH)
    baselines = pl.read_parquet(BASELINES_PATH)
    positives_monthly = pl.read_parquet(MONTHLY_AGG_DIR / "positives.parquet")
    positives_creations = pl.read_parquet(REPO_CREATIONS_DIR / "positives.parquet")

    excluded = confident_founder_logins(labels)
    pool = sample_pool(candidates, excluded, pool_size=args.pool_size)
    print(f"Pool sampled: {pool.height} actors", flush=True)

    founders = select_future_founders(labels, positives_monthly, positives_creations)
    print(f"Founder selection: {founders.counts}", flush=True)

    with ClickHouseClient() as client:
        pool_monthly, pool_creations = extract_pool_frames(pool, client)
    print(
        f"Pool extraction: monthly={pool_monthly.height} rows, "
        f"creations={pool_creations.height} rows",
        flush=True,
    )

    monthly_columns = [
        "actor_login",
        "month",
        "event_type",
        "is_weekend",
        "event_count",
    ]
    creation_columns = ["actor_login", "created_at"]
    monthly = pl.concat(
        [
            pool_monthly.select(monthly_columns).with_columns(
                pl.col("is_weekend").cast(pl.Boolean)
            ),
            founders.monthly.select(monthly_columns),
        ],
        how="vertical_relaxed",
    )
    creations = pl.concat(
        [
            pool_creations.select(creation_columns).with_columns(
                pl.col("created_at").cast(pl.Datetime("us"))
            ),
            founders.creations.select(creation_columns),
        ],
        how="vertical_relaxed",
    )
    assert_no_leakage(monthly, creations)

    pool_logins = pool.get_column("login_lower").to_list()
    overlap = set(pool_logins) & set(founders.scored_logins)
    if overlap:
        raise AssertionError(f"Pool and founder logins overlap: {sorted(overlap)[:5]}")
    features = build_feature_frame(
        monthly, creations, baselines, [*pool_logins, *founders.scored_logins]
    )
    ranked = rank_and_score(features, set(founders.scored_logins))
    metrics = compute_metrics(ranked, founders.near_window_logins)
    config = {
        "vintage_cutoff": VINTAGE.isoformat(),
        "feature_month": FEATURE_MONTH.isoformat(),
        "pool_size": args.pool_size,
        "sample_seed": SAMPLE_SEED,
        "min_total_events": MIN_TOTAL_EVENTS,
        "candidate_pool_unique_logins_at_vintage": 102_750,
        "hash_sample": "cityHash64(actor_login) % 400 in {0,1,2}",
        "model": "data/models selected LightGBM (see params.json)",
        "zero_filled_feature_blocks": list(ZERO_FILLED_FEATURES),
    }
    write_reports(metrics, founders.counts, config)
    print(json.dumps(metrics, indent=2), flush=True)
    print(f"Wrote {EVAL_JSON_PATH} and {EVAL_MD_PATH}", flush=True)


if __name__ == "__main__":
    main()
