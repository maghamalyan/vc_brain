"""Pillar-1 mini experiment: LLM semantic annotation of pre-cutoff activity.

For each top-region actor, build a compact digest of their pre-cutoff text
events and ask the model to characterize the work (coursework vs product
building etc.). The model never sees labels, scores, or anything post-cutoff.

Known caveat (reported, not hidden): the model's world knowledge could
recognize specific people/repos and their later outcomes; digests are
event-time text only, but login/repo names are visible. Treat results as an
upper bound pending a name-blinded replication.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import polars as pl
from dotenv import load_dotenv

from vc_brain.semantics.person_extract import (
    FULL_COHORT_PATH,
    FULL_TEXT_EVENTS_PATH,
    PILOT_COHORT_PATH,
    PILOT_DIR,
    TEXT_EVENTS_PATH,
)

LOGGER = logging.getLogger(__name__)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4.5")
CACHE_DIR = Path("data/cache/pilot_annotations")
ANNOTATIONS_PATH = PILOT_DIR / "annotations.parquet"
FULL_ANNOTATIONS_PATH = PILOT_DIR / "full_annotations.parquet"
MAX_WORKERS = 8

SYSTEM_PROMPT = """You are analyzing a GitHub user's public activity digest to
characterize what kind of work they were doing during this period. The digest
contains only events from a fixed historical window; you know nothing else
about the person. Do not speculate about who they are today.

Return ONLY a JSON object:
{
  "building_what": "<one sentence: the dominant activity in this window>",
  "builder_type": "coursework_learning | portfolio_jobseek | hobby_tinkering |
                   oss_contribution | employment_work | research |
                   own_product_building",
  "audience_orientation": "self | other_developers | end_users_customers",
  "productization": 0-3,  // 0=none, 3=clear docs/versioning/onboarding/deploy investment
  "team_formation": true/false,  // adding collaborators / sustained co-work on own new repos
  "gestation_likelihood": 0-100  // does this look like someone building toward
                                 // their OWN product/venture (not a job, not a
                                 // course, not contributions to others' projects)?
}

Judge from the substance of repo names, issue/PR titles, and comment text.
Coursework, tutorials, bootcamps, interview prep => low gestation_likelihood
even if activity is intense. Contributions to established external projects
=> oss_contribution unless they also build their own thing. A person creating
their own coherent multi-repo product, writing user-facing or commercial
language, versioning releases, adding collaborators => high."""


def build_digest(events: pl.DataFrame) -> str:
    """Compact, chronological digest of one actor's pre-cutoff text events."""
    lines: list[str] = []
    created = events.filter(
        (pl.col("event_type") == "CreateEvent") & (pl.col("ref_type") == "repository")
    ).sort("created_at")
    if created.height:
        lines.append("REPOS CREATED:")
        for r in created.head(60).iter_rows(named=True):
            lines.append(f"  {r['created_at']:%Y-%m} {r['repo_name']}")
    forks = events.filter(pl.col("event_type") == "ForkEvent").sort("created_at")
    if forks.height:
        lines.append("FORKED:")
        for r in forks.head(25).iter_rows(named=True):
            lines.append(f"  {r['created_at']:%Y-%m} {r['repo_name']}")
    releases = events.filter(pl.col("event_type") == "ReleaseEvent")
    if releases.height:
        lines.append(f"RELEASES PUBLISHED: {releases.height}")
        for r in releases.head(10).iter_rows(named=True):
            lines.append(f"  {r['created_at']:%Y-%m} {r['repo_name']} {r['release_name'] or ''}")
    members = events.filter(pl.col("event_type") == "MemberEvent")
    if members.height:
        lines.append("COLLABORATORS ADDED:")
        for r in members.head(10).iter_rows(named=True):
            lines.append(f"  {r['created_at']:%Y-%m} {r['repo_name']} += {r['member_login']}")
    issues_prs = events.filter(
        pl.col("event_type").is_in(["IssuesEvent", "PullRequestEvent"])
        & (pl.col("action") == "opened")
    ).sort("created_at")
    if issues_prs.height:
        lines.append("ISSUES/PRS OPENED (title @ repo):")
        for r in issues_prs.tail(80).iter_rows(named=True):
            title = (r["title"] or "").replace("\n", " ")[:120]
            lines.append(f"  {r['created_at']:%Y-%m} [{r['repo_name']}] {title}")
    comments = events.filter(
        pl.col("event_type").is_in(
            ["IssueCommentEvent", "PullRequestReviewCommentEvent"]
        )
        & (pl.col("body").str.len_chars() > 30)
    ).sort("created_at")
    if comments.height:
        lines.append("COMMENT EXCERPTS:")
        for r in comments.tail(25).iter_rows(named=True):
            body = (r["body"] or "").replace("\n", " ")[:200]
            lines.append(f"  {r['created_at']:%Y-%m} [{r['repo_name']}] {body}")
    return "\n".join(lines)[:14000]


def annotate_one(
    client: httpx.Client,
    api_key: str,
    login: str,
    digest: str,
    cache_dir: Path = CACHE_DIR,
) -> dict | None:
    cache_path = cache_dir / (
        hashlib.sha256((MODEL + login + digest).encode()).hexdigest() + ".json"
    )
    if cache_path.exists():
        return json.loads(cache_path.read_text())
    for attempt in range(5):
        try:
            response = client.post(
                OPENROUTER_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": MODEL,
                    "temperature": 0,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": digest},
                    ],
                },
                timeout=120.0,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            # Model may wrap in fences, echo the schema's // comments, or
            # append prose: take the first {...} block and strip comments.
            import re

            match = content[content.index("{") : content.rindex("}") + 1]
            try:
                record = json.loads(match)
            except json.JSONDecodeError:
                # strip // comments (avoiding URLs' ://) the model may echo
                record = json.loads(re.sub(r"(?<!:)//[^\n]*", "", match))
            record["gh_login"] = login
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(record))
            return record
        except (httpx.HTTPError, json.JSONDecodeError, KeyError) as error:
            LOGGER.warning("%s attempt %d failed: %s", login, attempt + 1, error)
            time.sleep(2**attempt)
    return None


def _annotate_cohort(
    cohort: pl.DataFrame, events: pl.DataFrame, out_path: Path
) -> pl.DataFrame:
    load_dotenv("/Users/mishaaghamalyan/Development/personal/competitions/vc_brain/.env")
    api_key = os.getenv("OPENROUTER_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_KEY missing")
    digests = {
        login: digest
        for (login,), group in events.filter(
            pl.col("actor_login").is_in(cohort["gh_login"].implode())
        ).group_by("actor_login")
        # Empty digests (events that all fall below the digest filters, e.g.
        # branch-only creates or sub-30-char comments) have nothing to judge.
        if (digest := build_digest(group))
    }
    LOGGER.info("annotating %d actors with text (of %d)", len(digests), cohort.height)

    records: list[dict] = []
    with httpx.Client() as client:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {
                pool.submit(annotate_one, client, api_key, login, digest): login
                for login, digest in sorted(digests.items())
            }
            for i, (future, login) in enumerate(futures.items(), 1):
                record = future.result()
                if record:
                    records.append(record)
                if i % 25 == 0:
                    LOGGER.info("progress %d/%d", i, len(futures))

    frame = pl.DataFrame(records)
    frame.write_parquet(out_path)
    print(f"annotated {frame.height} actors -> {out_path}")
    print(frame.group_by("builder_type").len().sort("len", descending=True))
    return frame


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    cohort = pl.read_parquet(PILOT_COHORT_PATH).filter(
        pl.col("stratum") == "top_region"
    )
    _annotate_cohort(cohort, pl.read_parquet(TEXT_EVENTS_PATH), ANNOTATIONS_PATH)


def main_full() -> None:
    """Annotate every full-cohort actor that has at least one text event."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    cohort = pl.read_parquet(FULL_COHORT_PATH)
    _annotate_cohort(
        cohort, pl.read_parquet(FULL_TEXT_EVENTS_PATH), FULL_ANNOTATIONS_PATH
    )


if __name__ == "__main__":
    import sys

    main_full() if "--full" in sys.argv else main()
