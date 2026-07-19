"""Instrument v2: structure-preserving blind + fine-grained gestation score.

Fixes the two defects wave-2 measured in the v1 instrument:

1. *Score resolution.* The v1 annotator emits only 12 distinct
   gestation values (0-95 in coarse steps), so the semantic re-rank runs out
   of resolution and inverts against the count model beyond K~50. The v2
   prompt demands an integer 0-100 with explicit band anchors, forbids
   round-number clustering, and adds a `rank_evidence` one-liner naming the
   1-2 strongest observations.

2. *Blinding artifact.* Pod B's strict blind turned the actor's OWN startup
   org into `EXTn`, so building one's company read as external work (14/20 of
   the largest score drops were org-create actors). v2 masks
   structure-preservingly: orgs/owners with event-time admin evidence (the
   actor created repos under them, or performed MemberEvent adds on their
   repos) become `USER_ORG1...` instead of `EXTn` -- identity hidden,
   ownership structure kept.

Masking contract (extends blind_check.py; that module is left untouched):
  - actor's own login -> "USER" everywhere (+ raw substring pass, as Pod B);
  - owners with event-time admin evidence -> USER_ORG1, USER_ORG2, ... at any
    token boundary (these are the actor's own orgs: identity-bearing, so they
    are masked everywhere, not just in owner position);
  - member_logins -> PERSON1, ... at any token boundary;
  - remaining external owners -> EXT1, ... in owner position or @mention only
    (a word like "flutter" stays readable inside repo stems and bodies);
  - repo stems, titles, bodies, dates untouched.
  Precedence when a token qualifies for several classes:
  USER > USER_ORG > PERSON > EXT.

Cohort: union of all top-region pilot actors and every full-cohort actor with
wave-2 (v1) gestation_likelihood >= 35. Separate content-addressed cache
under data/cache/pilot_annotations_v2/.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import polars as pl
from dotenv import load_dotenv

from vc_brain.pilot.annotate import FULL_ANNOTATIONS_PATH, build_digest
from vc_brain.pilot.blind_check import _BOUNDARY, _sub_tokens
from vc_brain.pilot.extract import (
    FULL_COHORT_PATH,
    FULL_TEXT_EVENTS_PATH,
    PILOT_COHORT_PATH,
    PILOT_DIR,
)

LOGGER = logging.getLogger(__name__)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4.5")
V2_CACHE_DIR = Path("data/cache/pilot_annotations_v2")
V2_ANNOTATIONS_PATH = PILOT_DIR / "annotations_v2.parquet"
V2_DIGESTS_PATH = PILOT_DIR / "v2_digests.parquet"
V1_GESTATION_FLOOR = 35  # full-cohort actors at/above this v1 score join v2
MAX_WORKERS = 8

SYSTEM_PROMPT_V2 = """You are analyzing a GitHub user's public activity digest to
characterize what kind of work they were doing during this period. The digest
contains only events from a fixed historical window; you know nothing else
about the person. Do not speculate about who they are today.

Identity tokens in the digest are pseudonymized:
  USER       = the person whose activity this is
  USER_ORG1, USER_ORG2, ... = organizations the USER has admin/ownership
               evidence over in this window (they created repositories under
               the org, or added collaborators to its repositories). Work in
               a USER_ORGn repository is work on the USER's OWN organization.
  PERSON1, PERSON2, ... = other individual people
  EXT1, EXT2, ... = external repository owners with no ownership evidence
               (someone else's project, an employer, an upstream org)
Judge only from the structure and substance of the activity.

Return ONLY a JSON object:
{
  "building_what": "<one sentence: the dominant activity in this window>",
  "builder_type": "coursework_learning | portfolio_jobseek | hobby_tinkering |
                   oss_contribution | employment_work | research |
                   own_product_building",
  "audience_orientation": "self | other_developers | end_users_customers",
  "productization": 0-3,  // 0=none, 3=clear docs/versioning/onboarding/deploy investment
  "team_formation": true/false,  // adding collaborators / sustained co-work on own new repos
  "rank_evidence": "<one line naming the 1-2 strongest concrete observations
                    that justify your gestation score>",
  "gestation_likelihood": 0-100  // integer; see the scale contract below
}

gestation_likelihood scale contract -- how much this window looks like someone
building toward their OWN product/venture (not a job, not a course, not
contributions to others' projects):
   0-9   no gestation signal at all (pure coursework, tutorials, config files)
  10-29  tinkering: personal experiments, hobby scripts, no product shape
  30-49  serious side project: sustained own work, but no user/commercial aim
  50-69  product-shaped but pre-commercial: coherent product, docs/releases,
         aimed at users, no commercial or venture markers yet
  70-89  clear venture gestation: own org or team forming, commercial or
         launch language, sustained multi-repo product investment
  90-100 unmistakable company-building: the window reads as an operating
         company (pricing, customers, onboarding, team, releases)

Use the FULL integer range. Scores will be compared at single-point
granularity, so 63 vs 60 matters: place each person precisely within their
band using the strength of the evidence, and DO NOT cluster on round numbers
(multiples of 5 or 10) unless the evidence is genuinely that generic. Two
people in the same band must be distinguishable by score whenever the
evidence distinguishes them.

Coursework, tutorials, bootcamps, interview prep => low gestation_likelihood
even if activity is intense. Contributions to established external (EXTn)
projects => oss_contribution unless they also build their own thing. A person
creating their own coherent multi-repo product (under USER or a USER_ORGn),
writing user-facing or commercial language, versioning releases, adding
collaborators => high."""


def admin_owners(events: pl.DataFrame, actor_login: str) -> set[str]:
    """Owners (lowercased) with event-time admin evidence by this actor.

    Evidence: the actor created a repository under the owner (CreateEvent,
    ref_type=repository) or added a collaborator to one of its repositories
    (MemberEvent). The actor's own login is excluded (it is USER).
    """
    actor = actor_login.lower()
    evidence = events.filter(
        (
            (pl.col("event_type") == "CreateEvent")
            & (pl.col("ref_type") == "repository")
        )
        | (pl.col("event_type") == "MemberEvent")
    )
    owners: set[str] = set()
    for repo in evidence["repo_name"]:
        if repo and "/" in repo:
            owner = repo.split("/")[0].lower()
            if owner and owner != actor:
                owners.add(owner)
    return owners


def identity_tokens_v2(events: pl.DataFrame, actor_login: str) -> dict[str, str]:
    """Token (lowercased) -> pseudonym, structure-preservingly.

    Numbering follows first chronological appearance (created_at, repo_name
    sort) so the mapping is deterministic across runs.
    """
    ordered = events.sort("created_at", "repo_name")
    admins = admin_owners(events, actor_login)
    mapping: dict[str, str] = {actor_login.lower(): "USER"}
    n_org = 0
    for repo in ordered["repo_name"]:
        if not repo or "/" not in repo:
            continue
        key = repo.split("/")[0].lower()
        if key in admins and key not in mapping:
            n_org += 1
            mapping[key] = f"USER_ORG{n_org}"
    n_person = 0
    for login in ordered["member_login"]:
        if not login:
            continue
        key = login.lower()
        if key not in mapping:
            n_person += 1
            mapping[key] = f"PERSON{n_person}"
    n_ext = 0
    for repo in ordered["repo_name"]:
        if not repo or "/" not in repo:
            continue
        key = repo.split("/")[0].lower()
        if key and key not in mapping:
            n_ext += 1
            mapping[key] = f"EXT{n_ext}"
    return mapping


def mask_text_v2(text: str, mapping: dict[str, str], actor_login: str) -> str:
    """Apply the v2 masking contract to one digest."""
    users = {t: p for t, p in mapping.items() if p == "USER"}
    orgs = {t: p for t, p in mapping.items() if p.startswith("USER_ORG")}
    persons = {t: p for t, p in mapping.items() if p.startswith("PERSON")}
    exts = {t: p for t, p in mapping.items() if p.startswith("EXT")}
    masked = _sub_tokens(text, users, _BOUNDARY)
    # Concatenation leak for the actor's own login (Pod B's substring pass).
    if len(actor_login) >= 4:
        masked = re.sub(re.escape(actor_login), "USER", masked, flags=re.IGNORECASE)
    # The actor's own orgs are identity-bearing: mask at any token boundary
    # (bodies included), not just owner position.
    masked = _sub_tokens(masked, orgs, _BOUNDARY)
    masked = _sub_tokens(masked, persons, _BOUNDARY)
    masked = _sub_tokens(masked, exts, r"(?<![A-Za-z0-9]){}(?=/)")
    masked = _sub_tokens(masked, exts, r"(?<=@){}(?![A-Za-z0-9])")
    return masked


def build_v2_cohort() -> pl.DataFrame:
    """Union: all top-region pilot actors + v1 gestation >= 35 full-cohort actors."""
    top = (
        pl.read_parquet(PILOT_COHORT_PATH)
        .filter(pl.col("stratum") == "top_region")
        .select("gh_login")
    )
    v1_hi = (
        pl.read_parquet(FULL_ANNOTATIONS_PATH)
        .with_columns(pl.col("gestation_likelihood").cast(pl.Float64, strict=False))
        .filter(pl.col("gestation_likelihood") >= V1_GESTATION_FLOOR)
        .select("gh_login")
    )
    logins = pl.concat([top, v1_hi]).unique().sort("gh_login")
    return pl.read_parquet(FULL_COHORT_PATH).join(logins, on="gh_login", how="inner")


def build_v2_digests(cohort: pl.DataFrame) -> pl.DataFrame:
    """Masked digests for every cohort actor with a non-empty digest."""
    events = pl.read_parquet(FULL_TEXT_EVENTS_PATH).filter(
        pl.col("actor_login").is_in(cohort["gh_login"].implode())
    )
    rows: list[dict[str, str]] = []
    for login in sorted(cohort["gh_login"]):
        group = events.filter(pl.col("actor_login") == login)
        if not group.height:
            continue
        digest = build_digest(group)
        if not digest:
            continue
        mapping = identity_tokens_v2(group, login)
        rows.append(
            {
                "gh_login": login,
                "digest_v2": mask_text_v2(digest, mapping, login),
                "n_user_orgs": str(
                    sum(1 for p in mapping.values() if p.startswith("USER_ORG"))
                ),
            }
        )
    return pl.DataFrame(rows)


def audit_digests(digests: pl.DataFrame, cohort: pl.DataFrame) -> dict[str, int]:
    """Residual identity-leak audit (Pod B's login check + org-token check)."""
    events = pl.read_parquet(FULL_TEXT_EVENTS_PATH).filter(
        pl.col("actor_login").is_in(cohort["gh_login"].implode())
    )
    login_leaks: list[str] = []
    org_leaks: list[str] = []
    for row in digests.iter_rows(named=True):
        login = row["gh_login"]
        masked = row["digest_v2"].lower()
        if login.lower() in masked:
            login_leaks.append(login)
        group = events.filter(pl.col("actor_login") == login)
        for owner in admin_owners(group, login):
            if re.search(_BOUNDARY.format(re.escape(owner)), masked):
                org_leaks.append(f"{login}:{owner}")
                break
    LOGGER.info(
        "audit: %d digests, login leaks=%d %s, admin-org leaks=%d %s",
        digests.height, len(login_leaks), login_leaks[:10],
        len(org_leaks), org_leaks[:10],
    )
    return {"login_leaks": len(login_leaks), "org_leaks": len(org_leaks)}


def annotate_one_v2(
    client: httpx.Client,
    api_key: str,
    login: str,
    digest: str,
    cache_dir: Path = V2_CACHE_DIR,
) -> dict | None:
    """annotate.annotate_one pattern, with the v2 prompt in the cache key."""
    cache_path = cache_dir / (
        hashlib.sha256(
            (MODEL + SYSTEM_PROMPT_V2 + login + digest).encode()
        ).hexdigest()
        + ".json"
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
                        {"role": "system", "content": SYSTEM_PROMPT_V2},
                        {"role": "user", "content": digest},
                    ],
                },
                timeout=120.0,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            match = content[content.index("{") : content.rindex("}") + 1]
            try:
                record = json.loads(match)
            except json.JSONDecodeError:
                record = json.loads(re.sub(r"(?<!:)//[^\n]*", "", match))
            record["gh_login"] = login
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(record))
            return record
        except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError) as error:
            LOGGER.warning("%s attempt %d failed: %s", login, attempt + 1, error)
            time.sleep(2**attempt)
    return None


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    load_dotenv("/Users/mishaaghamalyan/Development/personal/competitions/vc_brain/.env")
    api_key = os.getenv("OPENROUTER_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_KEY missing")

    cohort = build_v2_cohort()
    digests = build_v2_digests(cohort)
    digests.write_parquet(V2_DIGESTS_PATH)
    LOGGER.info("v2 cohort %d actors, %d with digests", cohort.height, digests.height)
    audit = audit_digests(digests, cohort)
    if audit["login_leaks"]:
        raise RuntimeError(f"masking failed: {audit['login_leaks']} login leaks")

    records: list[dict] = []
    with httpx.Client() as client:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {
                pool.submit(
                    annotate_one_v2,
                    client,
                    api_key,
                    row["gh_login"],
                    row["digest_v2"],
                ): row["gh_login"]
                for row in digests.iter_rows(named=True)
            }
            for i, (future, login) in enumerate(futures.items(), 1):
                record = future.result()
                if record:
                    records.append(record)
                if i % 25 == 0:
                    LOGGER.info("progress %d/%d", i, len(futures))

    frame = pl.DataFrame(records, infer_schema_length=None)
    frame.write_parquet(V2_ANNOTATIONS_PATH)
    print(f"v2-annotated {frame.height} actors -> {V2_ANNOTATIONS_PATH}")
    print(frame.group_by("builder_type").len().sort("len", descending=True))


if __name__ == "__main__":
    main()
