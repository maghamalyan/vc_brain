"""Pod D — text depth: do commit messages add signal? (plus survivorship).

Commit messages are absent from GH Archive's flattened schema; the only source
is the live GitHub API, which has survivorship bias (deleted/private repos 404).
This module measures both the signal and the bias on a stratified 200-actor
subsample of the 335 annotated top-region pilot actors.

Leakage rules honored:
- Commit fetches use `until=<t_cutoff>` and additionally drop any commit whose
  *author* date exceeds t_cutoff. Author dates are rewritable (rebase/amend);
  we trust but record both author and committer dates in the output parquet.
- The augmented digest = the exact event-time digest from annotate.build_digest
  plus pre-cutoff commit message first-lines. No labels, scores, or post-cutoff
  data reach the annotator.
- The live-API repo *status* (alive/404) is survivorship measurement, i.e.
  current-day data; it is reported as such and never fed to the annotator.

Network: gh CLI (authenticated), sequential, ~2 req/s, per-repo JSON cache in
data/cache/gh_commits/. LLM calls cached in data/cache/pilot_annotations_commits/.
Deterministic: seed 42, temperature 0, sorted iteration.
"""

from __future__ import annotations

import hashlib
import json
import logging
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import polars as pl

from vc_brain.ingest.contracts import DATA_ROOT
from vc_brain.pilot import annotate
from vc_brain.pilot.annotate import build_digest
from vc_brain.pilot.content_features import auc
from vc_brain.pilot.extract import PILOT_COHORT_PATH, PILOT_DIR, TEXT_EVENTS_PATH

LOGGER = logging.getLogger(__name__)

SEED = 42
SAMPLE_SIZE = 200
MAX_REPOS_PER_ACTOR = 6
MAX_COMMITS_IN_DIGEST = 60
COMMIT_MSG_TRUNC = 150

COMMITS_CACHE_DIR = DATA_ROOT / "cache" / "gh_commits"
COMMIT_ANN_CACHE_DIR = DATA_ROOT / "cache" / "pilot_annotations_commits"
SAMPLE_PATH = PILOT_DIR / "commit_depth_sample.parquet"
REPO_STATUS_PATH = PILOT_DIR / "commit_repo_status.parquet"
COMMITS_PATH = PILOT_DIR / "commit_messages.parquet"
COMMIT_ANNOTATIONS_PATH = PILOT_DIR / "annotations_commits.parquet"

GESTATION_BANDS = [(0, 15), (15, 50), (50, 80), (80, 101)]


def gestation_band(col: pl.Expr) -> pl.Expr:
    expr = pl.lit(None, dtype=pl.String)
    for lo, hi in reversed(GESTATION_BANDS):
        label = f"[{lo},{hi})" if hi <= 100 else f"[{lo},100]"
        expr = pl.when((col >= lo) & (col < hi)).then(pl.lit(label)).otherwise(expr)
    return expr


def sample_actors() -> pl.DataFrame:
    """Stratified 200: all annotated actors with gestation>=50, then random
    fill from the rest (seed 42) balancing founders/controls to ~100/100."""
    if SAMPLE_PATH.exists():
        return pl.read_parquet(SAMPLE_PATH)
    cohort = pl.read_parquet(PILOT_COHORT_PATH).filter(
        pl.col("stratum") == "top_region"
    )
    ann = pl.read_parquet(annotate.ANNOTATIONS_PATH).with_columns(
        pl.col("gestation_likelihood").cast(pl.Float64)
    )
    joined = cohort.join(
        ann.select("gh_login", "gestation_likelihood", "builder_type"),
        on="gh_login",
        how="inner",
    ).sort("gh_login")
    high = joined.filter(pl.col("gestation_likelihood") >= 50)
    rest = joined.filter(pl.col("gestation_likelihood") < 50)
    per_class_target = SAMPLE_SIZE // 2
    fills = []
    for person_type in ("positive", "control"):
        have = high.filter(pl.col("person_type") == person_type).height
        pool = rest.filter(pl.col("person_type") == person_type).sort("gh_login")
        need = min(per_class_target - have, pool.height)
        fills.append(pool.sample(n=need, seed=SEED))
    sample = pl.concat([high, *fills]).sort("gh_login")
    sample = sample.with_columns(
        gestation_band(pl.col("gestation_likelihood")).alias("gestation_band")
    )
    SAMPLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    sample.write_parquet(SAMPLE_PATH)
    return sample


def select_repos(sample: pl.DataFrame) -> pl.DataFrame:
    """Own repos created pre-cutoff, up to 6 per actor, most event-active
    first (activity = the actor's text-event count on that repo)."""
    events = pl.read_parquet(TEXT_EVENTS_PATH).filter(
        pl.col("actor_login").is_in(sample["gh_login"].implode())
    )
    own = (
        pl.col("repo_name").str.split("/").list.get(0).str.to_lowercase()
        == pl.col("actor_login").str.to_lowercase()
    )
    created = (
        events.filter(
            (pl.col("event_type") == "CreateEvent")
            & (pl.col("ref_type") == "repository")
            & own
        )
        .group_by("actor_login", "repo_name")
        .agg(pl.col("created_at").min().alias("repo_created_at"))
    )
    activity = events.group_by("actor_login", "repo_name").agg(
        pl.len().alias("n_repo_events")
    )
    ranked = (
        created.join(activity, on=["actor_login", "repo_name"], how="left")
        .with_columns(pl.col("n_repo_events").fill_null(0))
        .sort(
            ["actor_login", "n_repo_events", "repo_name"],
            descending=[False, True, False],
        )
        .with_columns(pl.col("repo_name").cum_count().over("actor_login").alias("_rank"))
        .filter(pl.col("_rank") <= MAX_REPOS_PER_ACTOR)
        .drop("_rank")
    )
    return ranked.join(
        sample.select("gh_login", "t_cutoff"),
        left_on="actor_login",
        right_on="gh_login",
        how="left",
    ).sort(["actor_login", "repo_name"])


def fetch_repo_commits(repo: str, until_iso: str) -> dict:
    """One page (100) of commits before t_cutoff via gh api, disk-cached.

    status: alive | deleted_404 | empty_409 | blocked_451 | error_<code|net>.
    404 conflates deleted and made-private (renames redirect and still 200).
    """
    key = hashlib.sha256(f"{repo}|{until_iso}".encode()).hexdigest()
    cache_path = COMMITS_CACHE_DIR / f"{key}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text())
    result = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{repo}/commits?until={until_iso}&per_page=100",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode == 0:
        record = {"repo": repo, "status": "alive", "commits": json.loads(result.stdout)}
    else:
        stderr = result.stderr
        if "HTTP 404" in stderr:
            status = "deleted_404"
        elif "HTTP 409" in stderr:
            status = "empty_409"  # repo exists but git history is empty
        elif "HTTP 451" in stderr:
            status = "blocked_451"
        else:
            status = "error"
        record = {"repo": repo, "status": status, "commits": [], "stderr": stderr[:300]}
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(record))
    time.sleep(0.5)  # ~2 req/s sustained
    return record


def fetch_all_commits(repos: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Returns (repo_status, commit_messages) frames; both leakage-annotated."""
    status_rows: list[dict] = []
    commit_rows: list[dict] = []
    rows = repos.sort(["actor_login", "repo_name"]).to_dicts()
    for i, row in enumerate(rows, 1):
        until_iso = f"{row['t_cutoff'].isoformat()}T00:00:00Z"
        cutoff_str = until_iso.replace("Z", "+00:00")
        record = fetch_repo_commits(row["repo_name"], until_iso)
        kept = 0
        for c in record["commits"]:
            commit = c.get("commit", {})
            author_date = (commit.get("author") or {}).get("date") or ""
            committer_date = (commit.get("committer") or {}).get("date") or ""
            # `until` filters on committer date; author dates are rewritable —
            # drop post-cutoff author dates, but record both dates verbatim.
            if author_date.replace("Z", "+00:00") > cutoff_str:
                continue
            kept += 1
            message = (commit.get("message") or "").split("\n")[0][:COMMIT_MSG_TRUNC]
            commit_rows.append(
                {
                    "actor_login": row["actor_login"],
                    "repo_name": row["repo_name"],
                    "sha": c.get("sha"),
                    "author_date": author_date,
                    "committer_date": committer_date,
                    "author_login": (c.get("author") or {}).get("login"),
                    "message": message,
                }
            )
        status_rows.append(
            {
                "actor_login": row["actor_login"],
                "repo_name": row["repo_name"],
                "n_repo_events": row["n_repo_events"],
                "repo_created_at": row["repo_created_at"],
                "status": record["status"],
                "n_commits_pre_cutoff": kept,
                "n_commits_raw": len(record["commits"]),
            }
        )
        if i % 50 == 0:
            LOGGER.info("commits fetched %d/%d repos", i, len(rows))
    return pl.DataFrame(status_rows), pl.DataFrame(commit_rows)


def build_augmented_digest(events: pl.DataFrame, commits: pl.DataFrame) -> str:
    """Event digest + up to 60 pre-cutoff commit message first-lines."""
    base = build_digest(events)
    if not commits.height:
        return base
    lines = ["COMMIT MESSAGES (own repos):"]
    recent = commits.sort("author_date").tail(MAX_COMMITS_IN_DIGEST)
    for r in recent.iter_rows(named=True):
        month = (r["author_date"] or "")[:7]
        lines.append(f"  {month} [{r['repo_name']}] {r['message']}")
    return (base + "\n" + "\n".join(lines))[:20000]


def annotate_augmented(sample: pl.DataFrame, commits: pl.DataFrame) -> pl.DataFrame:
    """Re-annotate the sample with commit-augmented digests (same prompt/model).

    Actors with zero fetched commit messages have byte-identical digests, so
    their event-only annotation is reused verbatim (marked augmented=False).
    """
    import os

    from dotenv import load_dotenv

    load_dotenv(
        "/Users/mishaaghamalyan/Development/personal/competitions/vc_brain/.env"
    )
    api_key = os.getenv("OPENROUTER_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_KEY missing")
    COMMIT_ANN_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    events = pl.read_parquet(TEXT_EVENTS_PATH).filter(
        pl.col("actor_login").is_in(sample["gh_login"].implode())
    )
    event_ann = pl.read_parquet(annotate.ANNOTATIONS_PATH)

    digests: dict[str, str] = {}
    reused: list[dict] = []
    for login in sorted(sample["gh_login"]):
        actor_events = events.filter(pl.col("actor_login") == login)
        actor_commits = commits.filter(pl.col("actor_login") == login)
        if not actor_commits.height:
            row = event_ann.filter(pl.col("gh_login") == login).to_dicts()
            if row:
                reused.append({**row[0], "augmented": False})
            continue
        digests[login] = build_augmented_digest(actor_events, actor_commits)

    LOGGER.info(
        "annotating %d augmented digests (%d reused event-only)",
        len(digests),
        len(reused),
    )
    records: list[dict] = []
    with httpx.Client() as client:
        with ThreadPoolExecutor(max_workers=annotate.MAX_WORKERS) as pool:
            futures = {
                pool.submit(
                    annotate.annotate_one,
                    client,
                    api_key,
                    login,
                    digest,
                    COMMIT_ANN_CACHE_DIR,
                ): login
                for login, digest in sorted(digests.items())
            }
            for i, future in enumerate(futures, 1):
                record = future.result()
                if record:
                    records.append({**record, "augmented": True})
                if i % 25 == 0:
                    LOGGER.info("progress %d/%d", i, len(futures))
    frame = pl.DataFrame(records + reused, infer_schema_length=None)
    frame.write_parquet(COMMIT_ANNOTATIONS_PATH)
    return frame


def survivorship_report(sample: pl.DataFrame, status: pl.DataFrame) -> None:
    joined = status.join(
        sample.select("gh_login", "person_type", "gestation_band"),
        left_on="actor_login",
        right_on="gh_login",
        how="left",
    )
    dead = pl.col("status") == "deleted_404"
    print("\n=== SURVIVORSHIP: pre-cutoff-created repos now 404 (live API, current-day) ===")
    print(
        joined.group_by("status")
        .len()
        .sort("len", descending=True)
    )
    print("\nby person_type:")
    print(
        joined.group_by("person_type").agg(
            pl.len().alias("repos"),
            dead.sum().alias("dead_404"),
            dead.mean().round(3).alias("dead_share"),
        ).sort("person_type")
    )
    print("\nby gestation band:")
    print(
        joined.group_by("gestation_band").agg(
            pl.len().alias("repos"),
            dead.sum().alias("dead_404"),
            dead.mean().round(3).alias("dead_share"),
        ).sort("gestation_band")
    )
    print("\nby person_type x gestation band:")
    print(
        joined.group_by("person_type", "gestation_band").agg(
            pl.len().alias("repos"),
            dead.mean().round(3).alias("dead_share"),
        ).sort("person_type", "gestation_band")
    )
    actor_level = joined.group_by("actor_login", "person_type").agg(
        pl.len().alias("repos"), dead.any().alias("any_dead")
    )
    print("\nactors with >=1 dead repo, by person_type:")
    print(
        actor_level.group_by("person_type").agg(
            pl.len().alias("actors"), pl.col("any_dead").mean().round(3)
        ).sort("person_type")
    )


def signal_report(sample: pl.DataFrame, commit_ann: pl.DataFrame) -> None:
    event_ann = pl.read_parquet(annotate.ANNOTATIONS_PATH).select(
        "gh_login",
        pl.col("gestation_likelihood").cast(pl.Float64).alias("gestation_event"),
        pl.col("builder_type").alias("builder_type_event"),
    )
    aug = commit_ann.select(
        "gh_login",
        pl.col("gestation_likelihood").cast(pl.Float64).alias("gestation_commit"),
        pl.col("builder_type").alias("builder_type_commit"),
        "augmented",
        pl.col("building_what").alias("building_what_commit"),
    )
    frame = (
        sample.select("gh_login", "person_type", "peak")
        .join(event_ann, on="gh_login", how="inner")
        .join(aug, on="gh_login", how="inner")
    )
    print(f"\n=== SIGNAL: same {frame.height} actors, event-only vs commit-augmented ===")
    for col in ("gestation_event", "gestation_commit", "peak"):
        print(f"AUC {col:18s} {auc(frame, col):.3f}")
    aug_only = frame.filter(pl.col("augmented"))
    print(f"\naugmented-only subset (n={aug_only.height}):")
    for col in ("gestation_event", "gestation_commit"):
        print(f"AUC {col:18s} {auc(aug_only, col):.3f}")

    print("\ngestation medians by class:")
    print(
        frame.group_by("person_type").agg(
            pl.col("gestation_event").median(),
            pl.col("gestation_commit").median(),
            pl.len(),
        ).sort("person_type")
    )
    print("\nbuilder_type shifts (event -> commit-augmented), augmented subset:")
    shifts = (
        aug_only.filter(
            pl.col("builder_type_event") != pl.col("builder_type_commit")
        )
        .group_by("builder_type_event", "builder_type_commit", "person_type")
        .len()
        .sort("len", descending=True)
    )
    print(shifts)
    print(
        f"changed builder_type: {aug_only.filter(pl.col('builder_type_event') != pl.col('builder_type_commit')).height}"
        f"/{aug_only.height}"
    )
    moved = aug_only.with_columns(
        (pl.col("gestation_commit") - pl.col("gestation_event")).alias("delta")
    ).sort("delta")
    print("\nlargest gestation moves (down then up):")
    cols = [
        "gh_login",
        "person_type",
        "builder_type_event",
        "builder_type_commit",
        "gestation_event",
        "gestation_commit",
        "delta",
    ]
    with pl.Config(tbl_rows=20, fmt_str_lengths=40):
        print(moved.select(cols).head(10))
        print(moved.select(cols).tail(10))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    sample = sample_actors()
    print(
        "sample:",
        sample.group_by("person_type", "gestation_band").len().sort(
            "person_type", "gestation_band"
        ),
    )
    repos = select_repos(sample)
    print(f"repos selected: {repos.height} for {repos['actor_login'].n_unique()} actors")
    status, commits = fetch_all_commits(repos)
    status.write_parquet(REPO_STATUS_PATH)
    commits.write_parquet(COMMITS_PATH)
    print(f"commits kept (author_date <= cutoff): {commits.height}")

    survivorship_report(sample, status)

    if COMMIT_ANNOTATIONS_PATH.exists():
        commit_ann = pl.read_parquet(COMMIT_ANNOTATIONS_PATH)
    else:
        commit_ann = annotate_augmented(sample, commits)
    signal_report(sample, commit_ann)


if __name__ == "__main__":
    main()
