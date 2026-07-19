"""Second-hop actor extraction and actor-actor co-activity edges (Pillar 2).

Builds, for the 1,920 Cohort-D people:

1. The distinct-repo universe they touched (local extracts only).
2. A small-rooms filter: repos owned by a cohort member are always kept;
   other repos are kept only if their full-history distinct non-bot actor
   count is <= ``SMALL_ROOM_MAX_ACTORS`` (one cheap repo-batched count query
   family against the ClickHouse playground).
3. Second-hop monthly activity: (repo, actor, month, event_type, count) for
   every non-bot actor on the filtered repos, full history < 2026-07-01.
   Owned repos that exceed the small-rooms bound are extracted through a
   capped query (top ``TOP_ACTORS_PER_REPO_MONTH`` actors per repo-month,
   event_type collapsed to ``__ALL__``) so no single repo can blow the row
   guard.
4. Actor-actor co-activity edges restricted to one Cohort-D side, capped at
   the ``TOP_ACTORS_PER_REPO_MONTH`` most active actors per repo-month.
5. A per-(cohort_login, neighbor_login) summary with post-hoc founder flags.

All ClickHouse access goes through the shared cached, quota-aware client;
queries are repo-IN-batched (index-pruned), never actor scans. Every stage is
resumable: batch outputs are written once and skipped on rerun.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from collections.abc import Sequence
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from vc_brain.ingest.clickhouse import ClickHouseClient  # noqa: E402
from vc_brain.ingest.contracts import CONFIDENT_GITHUB_THRESHOLD  # noqa: E402
from vc_brain.ingest.sql import quote  # noqa: E402
from vc_brain.ingest.storage import atomic_write_parquet  # noqa: E402

LOGGER = logging.getLogger("secondhop")

DATA_ROOT = PROJECT_ROOT / "data"
GRAPH_DIR = DATA_ROOT / "graph"
SECONDHOP_DIR = GRAPH_DIR / "secondhop_monthly"
COHORT_D_PATH = DATA_ROOT / "semantics" / "cohort_d.parquet"
ITEMS_PATH = DATA_ROOT / "semantics" / "text" / "items.parquet"
REPO_CREATION_PATHS = (
    DATA_ROOT / "events" / "repo_creations" / "positives.parquet",
    DATA_ROOT / "events" / "repo_creations" / "negatives.parquet",
)
FOUNDERS_PATH = DATA_ROOT / "labels" / "founders.parquet"

REPO_UNIVERSE_PATH = GRAPH_DIR / "repo_universe.parquet"
REPO_ACTOR_COUNTS_PATH = GRAPH_DIR / "repo_actor_counts.parquet"
EDGES_PATH = GRAPH_DIR / "coactivity_edges.parquet"
NEIGHBORS_PATH = GRAPH_DIR / "neighbors.parquet"
SUMMARY_PATH = GRAPH_DIR / "coactivity_summary.json"
README_PATH = GRAPH_DIR / "README.md"

EXTRACTION_END = "2026-07-01 00:00:00"
SMALL_ROOM_MAX_ACTORS = 500
TOP_ACTORS_PER_REPO_MONTH = 50
COUNT_BATCH_SIZE = 5_000
EXTRACT_BATCH_SIZE = 2_000
CAPPED_BATCH_SIZE = 200
CAPPED_EVENT_TYPE = "__ALL__"

# Mirrors the project-wide exclusion in vc_brain.ingest.sql (regex-only bot
# filter); the raw string renders as `\[bot\]` inside the SQL literal exactly
# like the existing builders.
BOT_MATCH_SQL = r"(?i)(bot|\[bot\]|-ci|automation)"
BOT_RE = re.compile(r"(?i)(bot|\[bot\]|-ci|automation)")
# Obvious CI / platform service accounts the regex does not catch.
CI_ACCOUNTS = frozenset(
    {
        "web-flow",
        "github-actions",
        "github-classroom",
        "circleci",
        "azure-pipelines",
        "codecov",
        "codecov-io",
        "coveralls",
        "greenkeeper",
        "gitter-badger",
        "invalid-email-address",
        "netlify",
        "vercel",
        "renovate",
        "snyk",
        "stale",
    }
)


def _bot_filter(column: str = "actor_login") -> str:
    return f"NOT match({column}, '{BOT_MATCH_SQL}')"


def repo_actor_count_sql(repos: Sequence[str]) -> str:
    repo_list = ", ".join(quote(repo) for repo in repos)
    return f"""
SELECT
    repo_name,
    toInt64(uniqExact(actor_login)) AS distinct_actors
FROM github_events
WHERE repo_name IN ({repo_list})
  AND created_at < toDateTime('{EXTRACTION_END}')
  AND actor_login != ''
  AND {_bot_filter()}
GROUP BY repo_name
ORDER BY repo_name
""".strip()


def secondhop_monthly_sql(repos: Sequence[str]) -> str:
    repo_list = ", ".join(quote(repo) for repo in repos)
    return f"""
SELECT
    repo_name,
    actor_login,
    toStartOfMonth(created_at) AS month,
    toString(event_type) AS event_type,
    toInt64(count()) AS event_count
FROM github_events
WHERE repo_name IN ({repo_list})
  AND created_at < toDateTime('{EXTRACTION_END}')
  AND actor_login != ''
  AND {_bot_filter()}
GROUP BY repo_name, actor_login, month, event_type
ORDER BY repo_name, month, actor_login, event_type
""".strip()


def secondhop_capped_sql(repos: Sequence[str]) -> str:
    """Top-N actors per repo-month for owned repos too big for full extraction.

    Event-type breakdown is collapsed (``__ALL__``) so ``LIMIT BY`` bounds
    rows at N per repo-month regardless of repo size.
    """
    repo_list = ", ".join(quote(repo) for repo in repos)
    return f"""
SELECT
    repo_name,
    actor_login,
    month,
    '{CAPPED_EVENT_TYPE}' AS event_type,
    event_count
FROM (
    SELECT
        repo_name,
        actor_login,
        toStartOfMonth(created_at) AS month,
        toInt64(count()) AS event_count
    FROM github_events
    WHERE repo_name IN ({repo_list})
      AND created_at < toDateTime('{EXTRACTION_END}')
      AND actor_login != ''
      AND {_bot_filter()}
    GROUP BY repo_name, actor_login, month
    ORDER BY repo_name, month, event_count DESC, actor_login
    LIMIT {TOP_ACTORS_PER_REPO_MONTH} BY repo_name, month
)
ORDER BY repo_name, month, event_count DESC, actor_login
""".strip()


class CountingClient(ClickHouseClient):
    """ClickHouseClient that counts live HTTP requests and cache misses."""

    def __init__(self, **kwargs: object) -> None:
        super().__init__(**kwargs)  # type: ignore[arg-type]
        self.http_requests = 0
        self.cache_misses = 0

    def _request(self, sql: str) -> bytes:
        self.http_requests += 1
        return super()._request(sql)

    def query(self, sql: str) -> pl.DataFrame:
        if not self.cache_path(sql).exists():
            self.cache_misses += 1
        return super().query(sql)


def load_cohort() -> pl.DataFrame:
    return pl.read_parquet(COHORT_D_PATH)


def cohort_login_map(cohort: pl.DataFrame) -> pl.DataFrame:
    """lower(login) -> canonical cohort spelling, type, and t_cutoff."""
    return cohort.select(
        pl.col("actor_login").str.to_lowercase().alias("login_lower"),
        pl.col("actor_login").alias("cohort_login"),
        "person_type",
        "t_cutoff",
    ).unique(subset="login_lower", keep="first")


def build_repo_universe(cohort: pl.DataFrame) -> pl.DataFrame:
    """Distinct repos touched by Cohort-D, with owned-by-member flag."""
    lowered = set(cohort["actor_login"].str.to_lowercase())
    items = (
        pl.scan_parquet(ITEMS_PATH)
        .filter(pl.col("actor_login").str.to_lowercase().is_in(lowered))
        .select("repo_name")
        .unique()
        .collect()
    )
    creations = pl.concat(
        [
            pl.read_parquet(path).select("actor_login", "repo_name")
            for path in REPO_CREATION_PATHS
        ]
    ).filter(pl.col("actor_login").str.to_lowercase().is_in(lowered))
    universe = pl.concat([items, creations.select("repo_name")]).unique()
    universe = universe.filter(
        pl.col("repo_name").is_not_null()
        & pl.col("repo_name").str.contains("/", literal=True)
    )
    return universe.with_columns(
        pl.col("repo_name")
        .str.split("/")
        .list.get(0)
        .str.to_lowercase()
        .is_in(lowered)
        .alias("owned_by_cohort")
    ).sort("repo_name")


def stage_repo_universe() -> pl.DataFrame:
    if REPO_UNIVERSE_PATH.exists():
        return pl.read_parquet(REPO_UNIVERSE_PATH)
    universe = build_repo_universe(load_cohort())
    atomic_write_parquet(universe, REPO_UNIVERSE_PATH)
    return universe


def stage_actor_counts(
    client: CountingClient, universe: pl.DataFrame
) -> pl.DataFrame:
    if REPO_ACTOR_COUNTS_PATH.exists():
        return pl.read_parquet(REPO_ACTOR_COUNTS_PATH)
    repos = universe["repo_name"].to_list()
    counts = client.query_actor_batches(
        repos, repo_actor_count_sql, batch_size=COUNT_BATCH_SIZE
    )
    atomic_write_parquet(counts, REPO_ACTOR_COUNTS_PATH)
    return counts


def split_repo_lists(
    universe: pl.DataFrame, counts: pl.DataFrame
) -> tuple[list[str], list[str], pl.DataFrame]:
    """(regular repos, capped owned repos, filter report).

    Repos absent from the count result (renamed/no surviving events) are
    treated as small: extraction on them is nearly free.
    """
    joined = universe.join(counts, on="repo_name", how="left").with_columns(
        pl.col("distinct_actors").fill_null(0)
    )
    small = pl.col("distinct_actors") <= SMALL_ROOM_MAX_ACTORS
    kept = joined.filter(pl.col("owned_by_cohort") | small)
    regular = kept.filter(small)["repo_name"].to_list()
    capped = kept.filter(~small)["repo_name"].to_list()
    return regular, capped, joined


def stage_extraction(
    client: CountingClient, regular: list[str], capped: list[str]
) -> None:
    SECONDHOP_DIR.mkdir(parents=True, exist_ok=True)
    batches: list[tuple[str, list[str], object]] = []
    for start in range(0, len(regular), EXTRACT_BATCH_SIZE):
        index = start // EXTRACT_BATCH_SIZE
        batches.append(
            (
                f"batch_{index:04d}",
                regular[start : start + EXTRACT_BATCH_SIZE],
                secondhop_monthly_sql,
            )
        )
    for start in range(0, len(capped), CAPPED_BATCH_SIZE):
        index = start // CAPPED_BATCH_SIZE
        batches.append(
            (
                f"capped_{index:04d}",
                capped[start : start + CAPPED_BATCH_SIZE],
                secondhop_capped_sql,
            )
        )
    for name, repo_batch, builder in batches:
        path = SECONDHOP_DIR / f"{name}.parquet"
        if path.exists():
            continue
        frame = client.query_actor_batch(repo_batch, builder)  # type: ignore[arg-type]
        if frame.is_empty():
            frame = pl.DataFrame(
                schema={
                    "repo_name": pl.String,
                    "actor_login": pl.String,
                    "month": pl.Date,
                    "event_type": pl.String,
                    "event_count": pl.Int64,
                }
            )
        atomic_write_parquet(frame, path)
        LOGGER.info("extracted %s repos=%d rows=%d", name, len(repo_batch), frame.height)


def _clean_activity() -> pl.LazyFrame:
    """(repo, month, actor) activity with bot/CI accounts removed."""
    return (
        pl.scan_parquet(str(SECONDHOP_DIR / "*.parquet"))
        .filter(
            ~pl.col("actor_login").str.to_lowercase().is_in(CI_ACCOUNTS)
            & ~pl.col("actor_login").str.contains(BOT_RE.pattern)
        )
        .group_by("repo_name", "month", "actor_login")
        .agg(pl.col("event_count").sum().alias("events"))
    )


def stage_edges(cohort: pl.DataFrame) -> pl.DataFrame:
    if EDGES_PATH.exists():
        return pl.read_parquet(EDGES_PATH)
    activity = _clean_activity()
    ranked = (
        activity.sort(
            ["repo_name", "month", "events", "actor_login"],
            descending=[False, False, True, False],
        )
        .with_columns(
            pl.int_range(pl.len())
            .over(["repo_name", "month"])
            .alias("rank")
        )
        .filter(pl.col("rank") < TOP_ACTORS_PER_REPO_MONTH)
        .select(
            "repo_name",
            "month",
            pl.col("actor_login").alias("neighbor_login"),
            pl.col("events").alias("neighbor_events"),
        )
    )
    members = cohort_login_map(cohort).lazy()
    cohort_side = (
        activity.with_columns(
            pl.col("actor_login").str.to_lowercase().alias("login_lower")
        )
        .join(members, on="login_lower", how="inner")
        .select(
            "repo_name",
            "month",
            "cohort_login",
            pl.col("events").alias("cohort_events"),
            "login_lower",
        )
    )
    edges = (
        cohort_side.join(ranked, on=["repo_name", "month"], how="inner")
        .filter(
            pl.col("neighbor_login").str.to_lowercase() != pl.col("login_lower")
        )
        .select(
            "cohort_login",
            "neighbor_login",
            "repo_name",
            "month",
            "cohort_events",
            "neighbor_events",
        )
        .sort(["cohort_login", "repo_name", "month", "neighbor_login"])
        .collect()
    )
    atomic_write_parquet(edges, EDGES_PATH)
    return edges


def confident_founders() -> pl.DataFrame:
    founders = pl.read_parquet(FOUNDERS_PATH)
    return (
        founders.filter(
            pl.col("gh_login").is_not_null()
            & (pl.col("gh_confidence") >= CONFIDENT_GITHUB_THRESHOLD)
        )
        .group_by(pl.col("gh_login").str.to_lowercase().alias("login_lower"))
        .agg(pl.col("batch_start_date").min().alias("founder_batch_start_date"))
    )


def stage_neighbors(edges: pl.DataFrame, cohort: pl.DataFrame) -> pl.DataFrame:
    cohort_lower = set(cohort["actor_login"].str.to_lowercase())
    neighbors = (
        edges.group_by("cohort_login", "neighbor_login")
        .agg(
            pl.col("month").min().alias("first_coactive_month"),
            pl.col("month").max().alias("last_coactive_month"),
            pl.col("month").n_unique().alias("months_coactive"),
            pl.col("repo_name").n_unique().alias("repos_coactive"),
            pl.col("cohort_events").sum().alias("total_cohort_events"),
            pl.col("neighbor_events").sum().alias("total_neighbor_events"),
        )
        .with_columns(
            pl.col("neighbor_login").str.to_lowercase().alias("login_lower")
        )
        .join(confident_founders(), on="login_lower", how="left")
        .with_columns(
            pl.col("founder_batch_start_date").is_not_null().alias(
                "neighbor_is_confident_founder"
            ),
            pl.col("login_lower").is_in(cohort_lower).alias("neighbor_in_cohort_d"),
        )
        .drop("login_lower")
        .sort(["cohort_login", "neighbor_login"])
    )
    atomic_write_parquet(neighbors, NEIGHBORS_PATH)
    return neighbors


def degree_distribution(neighbors: pl.DataFrame) -> dict[str, float]:
    degrees = (
        neighbors.group_by("cohort_login")
        .agg(pl.len().alias("degree"))["degree"]
        .cast(pl.Float64)
    )
    return {
        "min": degrees.min(),
        "p25": degrees.quantile(0.25),
        "p50": degrees.quantile(0.5),
        "p75": degrees.quantile(0.75),
        "p90": degrees.quantile(0.9),
        "p99": degrees.quantile(0.99),
        "max": degrees.max(),
        "mean": degrees.mean(),
    }


def write_readme() -> None:
    README_PATH.write_text(
        """# data/graph — second-hop co-activity extracts

- `repo_universe.parquet` — distinct repos touched by Cohort-D (local extracts),
  with `owned_by_cohort` flag (owner prefix == a cohort login, case-insensitive).
- `repo_actor_counts.parquet` — full-history distinct non-bot actor count per
  repo (small-rooms filter input).
- `secondhop_monthly/` — (repo, actor, month, event_type, event_count) for all
  non-bot actors on filtered repos, history < 2026-07-01. `capped_*` batches
  cover cohort-owned repos with > 500 distinct actors: top-50 actors per
  repo-month, `event_type = '__ALL__'`.
- `coactivity_edges.parquet` — (cohort_login, neighbor_login, repo_name, month,
  cohort_events, neighbor_events); neighbor side capped at the 50 most-active
  actors per repo-month.
- `neighbors.parquet` — per (cohort_login, neighbor_login) summary with
  founder flags.

**LEAKAGE WARNING: `neighbor_is_confident_founder` and
`founder_batch_start_date` are POST-HOC knowledge.** Backtest-legal features
must use founder-status-as-of-t only: a neighbor may be counted as a founder at
prediction time t only if `founder_batch_start_date <= t` (recognized-founder
form), never via the unconditioned flag. Edge months also run past each
person's `t_cutoff`; feature builders must window edges to `month < t_cutoff`.
""",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        choices=["all", "universe", "counts", "extract", "edges", "neighbors"],
        default="all",
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(name)s %(message)s"
    )
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    cohort = load_cohort()
    universe = stage_repo_universe()
    owned = int(universe["owned_by_cohort"].sum())
    LOGGER.info(
        "repo universe: %d repos (%d owned by cohort, %d other)",
        universe.height,
        owned,
        universe.height - owned,
    )
    if args.stage == "universe":
        return 0
    with CountingClient() as client:
        counts = stage_actor_counts(client, universe)
        regular, capped, report = split_repo_lists(universe, counts)
        dropped = report.height - len(regular) - len(capped)
        LOGGER.info(
            "small-rooms filter: %d kept full (%d owned+small), %d owned capped, "
            "%d dropped (>%d actors, not owned)",
            len(regular),
            int(
                report.filter(
                    pl.col("owned_by_cohort")
                    & (pl.col("distinct_actors") <= SMALL_ROOM_MAX_ACTORS)
                ).height
            ),
            len(capped),
            dropped,
            SMALL_ROOM_MAX_ACTORS,
        )
        if args.stage == "counts":
            return 0
        stage_extraction(client, regular, capped)
        LOGGER.info(
            "clickhouse usage: %d cache misses, %d http requests",
            client.cache_misses,
            client.http_requests,
        )
    if args.stage == "extract":
        return 0
    edges = stage_edges(cohort)
    LOGGER.info("edges: %d rows", edges.height)
    if args.stage == "edges":
        return 0
    neighbors = stage_neighbors(edges, cohort)
    summary = {
        "repo_universe": universe.height,
        "repos_owned_by_cohort": owned,
        "repos_extracted_full": len(regular),
        "repos_extracted_capped": len(capped),
        "repos_dropped_small_rooms": report.height - len(regular) - len(capped),
        "edge_rows": edges.height,
        "distinct_neighbor_logins": int(edges["neighbor_login"].n_unique()),
        "neighbor_pairs": neighbors.height,
        "founder_neighbor_pairs": int(
            neighbors["neighbor_is_confident_founder"].sum()
        ),
        "degree_distribution": degree_distribution(neighbors),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2, default=str))
    write_readme()
    LOGGER.info("summary: %s", json.dumps(summary, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
