"""Launch harvest: HN "Launch HN"/"Show HN" stories for scored founders' companies.

For every distinct company of a founder whose gh_login is in the scored set
(data/scores/trajectories.parquet), search HN Algolia for stories whose TITLE
names the company, keep only launch/show stories, and verify conservatively:
the author must match a founder gh_login / name variant, OR the title must be
a canonical YC launch ("Launch HN: <Company> (YC ...)").

Output: data/labels/hn_launches.parquet — dated post-founding OUTCOME events.
These are labels, never features.
"""

from __future__ import annotations

import logging
import re

import httpx
import polars as pl

from vc_brain.ingest.contracts import DATA_ROOT
from vc_brain.labelnoise.net import USER_AGENT, get_json

LOGGER = logging.getLogger(__name__)
FOUNDERS_PATH = DATA_ROOT / "labels" / "founders.parquet"
TRAJECTORIES_PATH = DATA_ROOT / "scores" / "trajectories.parquet"
LAUNCHES_PATH = DATA_ROOT / "labels" / "hn_launches.parquet"
MIN_NAME_LEN = 3


def normalize_company(name: str) -> str:
    """Strip legal suffixes and punctuation for title matching."""
    cleaned = re.sub(r"(?i)[,.]?\s*(inc|llc|ltd|corp|co)\.?$", "", name.strip())
    return cleaned.strip(" ,.")


def name_variants(name: str) -> set[str]:
    """Plausible HN usernames derived from a person's name (hn_linkage method)."""
    parts = re.sub(r"[^a-z ]", "", (name or "").lower()).split()
    if not parts:
        return set()
    first, last = parts[0], parts[-1]
    variants = {first + last, first + "_" + last, first + "." + last,
                first[0] + last, first + last[0]}
    if len(first) >= 5:
        variants.add(first)
    return variants


def author_match(author: str, founders: list[dict]) -> tuple[str, str] | None:
    """Return (grade, detail) when the story author matches a founder."""
    a = author.lower()
    for f in founders:
        gh = (f["gh_login"] or "").lower()
        if a == gh:
            return "strong_author", f"author == gh_login {gh}"
        if gh and min(len(a), len(gh)) >= 5 and (a in gh or gh in a):
            return "author_substring", f"author ~ gh_login ({author} vs {gh})"
        if a in name_variants(f["founder_name"]):
            return "author_name_variant", f"author matches {f['founder_name']}"
    return None


def title_matches_company(title: str, company_norm: str) -> bool:
    return bool(
        re.search(
            r"(?<![A-Za-z0-9])" + re.escape(company_norm.lower()) + r"(?![A-Za-z0-9])",
            title.lower(),
        )
    )


def is_canonical_yc_launch(title: str, company_norm: str) -> bool:
    """'Launch HN: <Company> (YC W21) ...' — YC's own launch format."""
    return bool(
        re.match(
            r"(?i)^launch hn:?\s+" + re.escape(company_norm) + r"\s*\(yc\s",
            title.strip(),
        )
    )


def harvest_company(
    client: httpx.Client, company: str, slug: str, founders: list[dict]
) -> list[dict]:
    company_norm = normalize_company(company)
    if len(company_norm) < MIN_NAME_LEN:
        return []
    params = httpx.QueryParams(
        {
            "query": company_norm,
            "tags": "story",
            "restrictSearchableAttributes": "title",
            "hitsPerPage": 50,
        }
    )
    data = get_json(
        client,
        f"https://hn.algolia.com/api/v1/search?{params}",
        "company_search",
        company_norm.lower(),
    )
    rows = []
    for hit in (data or {}).get("hits", []):
        title = hit.get("title") or ""
        lowered = title.lower()
        if not (lowered.startswith("launch hn") or lowered.startswith("show hn")):
            continue
        if not title_matches_company(title, company_norm):
            continue
        author = hit.get("author") or ""
        matched = author_match(author, founders)
        if matched:
            grade, detail = matched
        elif is_canonical_yc_launch(title, company_norm):
            grade, detail = "launch_yc_title", "canonical 'Launch HN: X (YC ...)' title"
        else:
            continue  # conservative: unverified naming collision
        rows.append(
            {
                "company": company,
                "slug": slug,
                "story_id": int(hit["objectID"]),
                "title": title,
                "author": author,
                "created_at": hit.get("created_at"),
                "story_type": "launch_hn" if lowered.startswith("launch hn") else "show_hn",
                "match_grade": grade,
                "match_detail": detail,
                "url": f"https://news.ycombinator.com/item?id={hit['objectID']}",
            }
        )
    return rows


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    scored = {
        s.lower() for s in pl.read_parquet(TRAJECTORIES_PATH)["gh_login"].unique()
    }
    founders = pl.read_parquet(FOUNDERS_PATH).filter(
        pl.col("gh_login").str.to_lowercase().is_in(sorted(scored))
    )
    companies = (
        founders.group_by("company", "slug")
        .agg(pl.struct("gh_login", "founder_name").alias("people"))
        .sort("slug")
    )
    LOGGER.info("harvesting %d companies of %d scored founders",
                companies.height, founders.height)

    rows: list[dict] = []
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=20) as client:
        for i, rec in enumerate(companies.iter_rows(named=True), 1):
            rows.extend(
                harvest_company(client, rec["company"], rec["slug"], rec["people"])
            )
            if i % 50 == 0:
                LOGGER.info("progress %d/%d companies, %d stories", i,
                            companies.height, len(rows))

    frame = (
        pl.DataFrame(rows)
        .unique(subset=["story_id"])
        .with_columns(
            pl.col("created_at").str.to_datetime("%Y-%m-%dT%H:%M:%SZ", strict=False)
        )
        .sort("company", "created_at")
        if rows
        else pl.DataFrame()
    )
    LAUNCHES_PATH.parent.mkdir(parents=True, exist_ok=True)
    frame.write_parquet(LAUNCHES_PATH)
    print(f"wrote {frame.height} stories for "
          f"{frame['slug'].n_unique() if frame.height else 0} companies -> {LAUNCHES_PATH}")
    if frame.height:
        print(frame.group_by("story_type", "match_grade").len().sort("len", descending=True))


if __name__ == "__main__":
    main()
