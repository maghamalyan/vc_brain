"""Extract raw pre-cutoff text-bearing events for the pilot cohort.

Standalone requester (not ClickHouseClient) because free-text bodies need
FORMAT Parquet end-to-end; the shared client is TSV-only and its parser would
mangle embedded quotes. Retry/quota/bisect behavior mirrors ingest.clickhouse.
"""

from __future__ import annotations

import hashlib
import io
import logging
import time
from collections.abc import Sequence
from typing import Any

import httpx
import polars as pl

from vc_brain.ingest.contracts import DATA_ROOT, WINDOW_MONTHS
from vc_brain.ingest.sql import quote
from vc_brain.ingest.storage import atomic_write_parquet

LOGGER = logging.getLogger(__name__)
PLAYGROUND_URL = "https://play.clickhouse.com/"
PILOT_DIR = DATA_ROOT / "pilot"
PILOT_COHORT_PATH = PILOT_DIR / "pilot_cohort.parquet"
TEXT_EVENTS_PATH = PILOT_DIR / "text_events.parquet"
FULL_COHORT_PATH = PILOT_DIR / "full_cohort.parquet"
FULL_TEXT_EVENTS_PATH = PILOT_DIR / "full_text_events.parquet"
PANEL_PATH = DATA_ROOT / "features_panel_main.parquet"
TRAJECTORIES_PATH = DATA_ROOT / "scores" / "trajectories.parquet"
CACHE_DIR = DATA_ROOT / "cache" / "pilot"
# Each batch query full-scans actor_login regardless of batch size, so fewer
# batches = less quota; 408-bisect recovers if a batch's result is too slow.
BATCH_SIZE = 250
MAX_ATTEMPTS = 10

# Text-bearing (or structurally informative) event types only. PushEvent is
# excluded: GH Archive's flattened schema carries no commit messages, and push
# counts already exist in the features panel. WatchEvent is pure volume.
TEXT_EVENT_TYPES = (
    "CreateEvent",
    "ForkEvent",
    "IssuesEvent",
    "PullRequestEvent",
    "IssueCommentEvent",
    "PullRequestReviewCommentEvent",
    "ReleaseEvent",
    "MemberEvent",
    "PublicEvent",
)


class QueryTimeout(RuntimeError):
    """Playground 408: query exceeded its execution budget."""


def text_events_sql(actors: Sequence[dict[str, Any]]) -> str:
    values = ", ".join(
        f"({quote(str(row['gh_login']))}, {quote(row['t_cutoff'].isoformat())})"
        for row in actors
    )
    cohort = f"values('actor_login String, t_cutoff Date', {values})"
    logins = ", ".join(quote(str(row["gh_login"])) for row in actors)
    types = ", ".join(quote(t) for t in TEXT_EVENT_TYPES)
    return f"""
WITH cohort AS (SELECT * FROM {cohort})
SELECT
    e.actor_login AS actor_login,
    e.created_at AS created_at,
    toString(e.event_type) AS event_type,
    toString(e.action) AS action,
    e.repo_name AS repo_name,
    toValidUTF8(e.ref) AS ref,
    toString(e.ref_type) AS ref_type,
    e.number AS number,
    toValidUTF8(substring(e.title, 1, 300)) AS title,
    toValidUTF8(substring(e.body, 1, 1000)) AS body,
    toValidUTF8(arrayStringConcat(e.labels, '|')) AS labels,
    toString(e.author_association) AS author_association,
    e.creator_user_login AS creator_user_login,
    e.member_login AS member_login,
    e.merged AS merged,
    e.additions AS additions,
    e.deletions AS deletions,
    e.changed_files AS changed_files,
    toValidUTF8(e.release_name) AS release_name,
    a.t_cutoff AS t_cutoff
FROM github_events AS e
INNER JOIN cohort AS a ON e.actor_login = a.actor_login
WHERE e.actor_login IN ({logins})
  AND e.event_type IN ({types})
  AND e.created_at >= addMonths(toDateTime(a.t_cutoff), -{WINDOW_MONTHS})
  AND e.created_at < toDateTime(a.t_cutoff)
FORMAT Parquet
""".strip()


def _request_parquet(client: httpx.Client, sql: str) -> pl.DataFrame:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = client.post(
                PLAYGROUND_URL,
                params={"user": "play"},
                content=sql.encode("utf-8"),
                headers={"Content-Type": "text/plain; charset=utf-8"},
            )
        except httpx.TransportError as error:
            LOGGER.warning("transport error attempt=%d: %s", attempt, error)
            time.sleep(min(2**attempt, 30))
            continue
        if response.status_code == 408:
            raise QueryTimeout("playground 408")
        body_head = response.content[:300].decode("utf-8", "replace")
        if response.status_code == 429 or response.status_code >= 500:
            if "QUOTA_EXCEEDED" in body_head:
                LOGGER.warning("quota exhausted; sleeping 600s (attempt %d)", attempt)
                time.sleep(600)
            else:
                time.sleep(min(2**attempt, 30))
            continue
        response.raise_for_status()
        return pl.read_parquet(io.BytesIO(response.content))
    raise RuntimeError(f"gave up after {MAX_ATTEMPTS} attempts")


def fetch_batch(
    client: httpx.Client, actors: Sequence[dict[str, Any]]
) -> pl.DataFrame:
    """Fetch one actor batch with SQL-hash caching, bisecting on 408."""
    sql = text_events_sql(actors)
    cache_path = CACHE_DIR / (
        hashlib.sha256(sql.encode("utf-8")).hexdigest() + ".parquet"
    )
    if cache_path.exists():
        return pl.read_parquet(cache_path)
    try:
        frame = _request_parquet(client, sql)
    except QueryTimeout:
        if len(actors) == 1:
            raise
        LOGGER.warning("bisecting batch after 408 actors=%d", len(actors))
        middle = len(actors) // 2
        return pl.concat(
            [
                fetch_batch(client, actors[:middle]),
                fetch_batch(client, actors[middle:]),
            ],
            how="diagonal_relaxed",
        )
    atomic_write_parquet(frame, cache_path)
    LOGGER.info("batch cached actors=%d rows=%d", len(actors), frame.height)
    return frame


def _fetch_cohort_events(
    client: httpx.Client, cohort: pl.DataFrame, label: str
) -> list[pl.DataFrame]:
    """Fetch a cohort's events serially in gh_login-sorted BATCH_SIZE batches."""
    actors = cohort.sort("gh_login").select("gh_login", "t_cutoff").to_dicts()
    frames: list[pl.DataFrame] = []
    for start in range(0, len(actors), BATCH_SIZE):
        batch = actors[start : start + BATCH_SIZE]
        frames.append(fetch_batch(client, batch))
        LOGGER.info(
            "%s progress %d/%d actors, %d rows so far",
            label,
            min(start + BATCH_SIZE, len(actors)),
            len(actors),
            sum(f.height for f in frames),
        )
        time.sleep(0.5)
    return frames


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    cohort = pl.read_parquet(PILOT_COHORT_PATH)
    with httpx.Client(timeout=httpx.Timeout(180.0)) as client:
        frames = _fetch_cohort_events(client, cohort, "pilot")
    events = pl.concat([f for f in frames if f.height], how="diagonal_relaxed")
    atomic_write_parquet(events, TEXT_EVENTS_PATH)
    print(f"wrote {events.height:,} rows for {events['actor_login'].n_unique()} actors")
    print(events.group_by("event_type").len().sort("len", descending=True))


def build_full_cohort() -> pl.DataFrame:
    """All scored actors: panel identity/cutoff columns + trajectory peak.

    Pilot stratum/quartile are carried over where the pilot overlaps so the
    original strata remain reconstructible from the full cohort.
    """
    actors = (
        pl.read_parquet(PANEL_PATH)
        .select("gh_login", "person_type", "t_cutoff", "match_group_id")
        .unique()
    )
    peaks = (
        pl.read_parquet(TRAJECTORIES_PATH)
        .group_by("gh_login")
        .agg(pl.col("score").max().alias("peak"))
    )
    pilot = pl.read_parquet(PILOT_COHORT_PATH).select(
        "gh_login", "stratum", "quartile"
    )
    cohort = (
        actors.join(peaks, on="gh_login", how="inner")
        .join(pilot, on="gh_login", how="left")
        .sort("gh_login")
    )
    atomic_write_parquet(cohort, FULL_COHORT_PATH)
    return cohort


def main_full() -> None:
    """Extract text events for the full scored cohort.

    The pilot cohort is fetched with its original batching first (pure cache
    hits); only actors outside the pilot cost fresh playground quota.
    """
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    cohort = build_full_cohort()
    pilot = pl.read_parquet(PILOT_COHORT_PATH)
    remaining = cohort.filter(
        ~pl.col("gh_login").is_in(pilot["gh_login"].implode())
    )
    LOGGER.info(
        "full cohort %d actors: %d pilot (cached), %d new",
        cohort.height,
        pilot.height,
        remaining.height,
    )
    with httpx.Client(timeout=httpx.Timeout(180.0)) as client:
        frames = _fetch_cohort_events(client, pilot, "pilot")
        frames += _fetch_cohort_events(client, remaining, "new")
    events = pl.concat([f for f in frames if f.height], how="diagonal_relaxed")
    atomic_write_parquet(events, FULL_TEXT_EVENTS_PATH)
    print(f"wrote {events.height:,} rows for {events['actor_login'].n_unique()} actors")
    print(events.group_by("event_type").len().sort("len", descending=True))


if __name__ == "__main__":
    import sys

    main_full() if "--full" in sys.argv else main()
