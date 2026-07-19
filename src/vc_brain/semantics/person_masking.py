"""Name-blinded replication of the pilot annotation (contamination check).

The pilot annotator sees logins and repo-owner names, so the model's world
knowledge could recognize later-famous people and inflate gestation scores.
This module rebuilds the 335 already-annotated top-region digests with all
identity tokens masked, re-annotates them with the identical prompt/model/
temperature into a separate cache, and writes the blind annotations for
comparison in eval_blind.py.

Masking contract (content survives, identity must not):
  - the actor's own login -> "USER" everywhere (repo-owner segments, org
    names, URLs, comment bodies); case-insensitive; hyphen counts as a token
    boundary so "acme" also masks inside "acme-labs"; for logins >= 5 chars a
    raw substring pass additionally catches concatenations ("acmeapp").
  - member_login values -> PERSON1, PERSON2, ... everywhere (they are people;
    members take precedence if a login is both a member and an owner).
  - other repo-owner segments -> stable per-actor pseudonyms EXT1, EXT2, ...
    in order of first chronological appearance, but ONLY in owner position
    (followed by "/", which also covers URLs) or as "@mention" — a word like
    "flutter" that is both an org and a technology must stay readable inside
    repo stems, titles, and bodies.
  - repo name stems, titles, bodies, dates are left intact.
"""

from __future__ import annotations

import logging
import os
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import polars as pl
from dotenv import load_dotenv

from vc_brain.semantics.person_annotate import ANNOTATIONS_PATH, annotate_one, build_digest
from vc_brain.semantics.person_extract import PILOT_DIR, TEXT_EVENTS_PATH

LOGGER = logging.getLogger(__name__)
BLIND_CACHE_DIR = Path("data/cache/pilot_annotations_blind")
BLIND_ANNOTATIONS_PATH = PILOT_DIR / "annotations_blind.parquet"
BLIND_DIGESTS_PATH = PILOT_DIR / "blind_digests.parquet"
MAX_WORKERS = 8

# GitHub logins are alnum+hyphen; treating hyphen as a *boundary* deliberately
# over-masks (login "acme" also hits org "acme-labs"), which is the
# conservative direction for a blinding check.
_BOUNDARY = r"(?<![A-Za-z0-9]){}(?![A-Za-z0-9])"


def identity_tokens(events: pl.DataFrame, actor_login: str) -> dict[str, str]:
    """Map every identity token (lowercased) to its pseudonym for one actor.

    Pseudonym numbering follows first chronological appearance so the mapping
    is deterministic across runs.
    """
    ordered = events.sort("created_at", "repo_name")
    mapping: dict[str, str] = {actor_login.lower(): "USER"}
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


def _sub_tokens(text: str, tokens: dict[str, str], template: str) -> str:
    """Replace each token (case-insensitive, longest-first) via template."""
    if not tokens:
        return text
    alternation = "|".join(
        re.escape(t) for t in sorted(tokens, key=len, reverse=True)
    )
    pattern = re.compile(template.format(f"({alternation})"), re.IGNORECASE)
    return pattern.sub(lambda m: tokens[m.group(1).lower()], text)


def mask_text(text: str, mapping: dict[str, str], actor_login: str) -> str:
    """Replace every identity token in the digest with its pseudonym."""
    users = {t: p for t, p in mapping.items() if p == "USER"}
    persons = {t: p for t, p in mapping.items() if p.startswith("PERSON")}
    exts = {t: p for t, p in mapping.items() if p.startswith("EXT")}
    # Actor + members are people: mask at any token boundary.
    masked = _sub_tokens(text, users, _BOUNDARY)
    # Concatenation leak: login glued into a repo stem with no boundary at
    # all ("acmeapp", "remysharp.com" for login "remy"). Only for the actor's
    # own login and only when long enough to make false hits unlikely
    # (over-masking, e.g. "Jeremy" for login "remy", is the conservative
    # direction for a blinding check).
    if len(actor_login) >= 4:
        masked = re.sub(re.escape(actor_login), "USER", masked, flags=re.IGNORECASE)
    masked = _sub_tokens(masked, persons, _BOUNDARY)
    # External owners: only in owner position (also covers URL path segments)
    # or @mentions — never inside repo stems/bodies where the same word may be
    # a technology ("flutter", "docker").
    masked = _sub_tokens(masked, exts, r"(?<![A-Za-z0-9]){}(?=/)")
    masked = _sub_tokens(masked, exts, r"(?<=@){}(?![A-Za-z0-9])")
    return masked


def build_blind_digests() -> pl.DataFrame:
    """Masked digests for exactly the actors in the unblinded annotation set."""
    annotated = pl.read_parquet(ANNOTATIONS_PATH)["gh_login"]
    events = pl.read_parquet(TEXT_EVENTS_PATH).filter(
        pl.col("actor_login").is_in(annotated.implode())
    )
    rows: list[dict[str, str]] = []
    for login in sorted(annotated):
        group = events.filter(pl.col("actor_login") == login)
        digest = build_digest(group)
        mapping = identity_tokens(group, login)
        rows.append(
            {"gh_login": login, "digest_blind": mask_text(digest, mapping, login)}
        )
    return pl.DataFrame(rows)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    load_dotenv("/Users/mishaaghamalyan/Development/personal/competitions/vc_brain/.env")
    api_key = os.getenv("OPENROUTER_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_KEY missing")

    digests = build_blind_digests()
    digests.write_parquet(BLIND_DIGESTS_PATH)
    leak = [
        r["gh_login"]
        for r in digests.iter_rows(named=True)
        if r["gh_login"].lower() in r["digest_blind"].lower()
    ]
    LOGGER.info("built %d masked digests; residual login leaks: %d %s",
                digests.height, len(leak), leak[:10])

    records: list[dict] = []
    with httpx.Client() as client:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {
                pool.submit(
                    annotate_one,
                    client,
                    api_key,
                    row["gh_login"],
                    row["digest_blind"],
                    BLIND_CACHE_DIR,
                ): row["gh_login"]
                for row in digests.iter_rows(named=True)
            }
            for i, (future, login) in enumerate(futures.items(), 1):
                record = future.result()
                if record:
                    records.append(record)
                if i % 25 == 0:
                    LOGGER.info("progress %d/%d", i, len(futures))

    frame = pl.DataFrame(records)
    frame.write_parquet(BLIND_ANNOTATIONS_PATH)
    print(f"blind-annotated {frame.height} actors -> {BLIND_ANNOTATIONS_PATH}")
    print(frame.group_by("builder_type").len().sort("len", descending=True))


if __name__ == "__main__":
    main()
