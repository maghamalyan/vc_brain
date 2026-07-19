"""Pod H: person-level HN stream for ALL scored actors (founders AND controls).

Wave-2 harvested company-title Launch/Show HN stories (106 stories, 15.1% of
companies). This module extends the HN linkage to the PERSON level:

1. For every scored actor in data/pilot/full_cohort.parquet (2,765), probe the
   HN Firebase user API for an account whose username == gh_login (all cohort
   logins are lowercase) and pull karma / created / about.
2. Confirm identity CONSERVATIVELY, in tiers (hn_linkage.py evidence tiers):
     strong_github_link      about links github.com/<login>
     strong_story_github_url an authored story links github.com/<login>/...
     strong_company_domain   (founders) about mentions company website domain
     strong_company_name     (founders) about mentions company name (len>=4)
     strong_twitter          (founders) about links the founder's twitter handle
     strong_founder_name     (founders) about states the founder's full name
     strong_launch_author    (founders) authored a wave-2-verified launch story
     strong_gh_blog_domain   GH profile blog domain in HN about, or >=2
                             authored stories link that domain (class-symmetric)
     strong_gh_name          GH profile display name stated in HN about
     llm_confirmed           LLM adjudication of ambiguous about text
     medium_rare_name        exact match of a rare username (len>=10, or len>=8
                             with a digit/separator) — reported separately so
                             every analysis can be run strict (strong only)
     exists_unconfirmed      account exists, no confirming evidence
3. For every EXISTING account, pull the full story-submission history (Algolia
   author tag, one call) — needed both for behavioral identity evidence (story
   URLs pointing at the actor's GitHub) and for the Show/Launch HN stream.

Split discipline (iron rule 1):
  * The identity link itself rests on CURRENT-DAY data (profile about) —
    marked data_basis=current_day_label_only in hn_persons.parquet.
  * Stories are DATED events. Pre-t_cutoff Show HNs = potential FEATURE events
    (public launching pre-founding is gestation evidence); post-cutoff
    Show/Launch HNs = OUTCOME/LABEL events only. hn_person_stories.parquet
    carries pre_or_post_cutoff per row.

Outputs: data/labels/hn_persons.parquet, data/labels/hn_person_stories.parquet.
Politeness: <=2 req/s via labelnoise.net throttle, all calls disk-cached.
"""

from __future__ import annotations

import hashlib
import html
import json
import logging
import os
import re
import time

import httpx
import polars as pl
from dotenv import load_dotenv

from vc_brain.ingest.contracts import DATA_ROOT
from vc_brain.labelnoise.net import USER_AGENT, get_json, gh_api_user

LOGGER = logging.getLogger(__name__)

FULL_COHORT_PATH = DATA_ROOT / "pilot" / "full_cohort.parquet"
FOUNDERS_PATH = DATA_ROOT / "labels" / "founders.parquet"
LAUNCHES_PATH = DATA_ROOT / "labels" / "hn_launches.parquet"
PERSONS_PATH = DATA_ROOT / "labels" / "hn_persons.parquet"
STORIES_PATH = DATA_ROOT / "labels" / "hn_person_stories.parquet"

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4.5")
LLM_CACHE_DIR = DATA_ROOT / "cache" / "labelnoise" / "hn_person_llm"
MAX_LLM_CALLS = 80

CONFIRMED_GRADES = {
    "strong_github_link",
    "strong_story_github_url",
    "strong_company_domain",
    "strong_company_name",
    "strong_twitter",
    "strong_founder_name",
    "strong_launch_author",
    "strong_gh_blog_domain",
    "strong_gh_name",
    "llm_confirmed",
    "medium_rare_name",
}
STRICT_GRADES = CONFIRMED_GRADES - {"medium_rare_name"}
# Tiers computable identically for founders AND controls (no founders.parquet
# metadata): use these when comparing link rates across classes.
SYMMETRIC_GRADES = {
    "strong_github_link",
    "strong_story_github_url",
    "strong_gh_blog_domain",
    "strong_gh_name",
    "medium_rare_name",
}
# Generic hosts whose domains prove nothing about identity.
GENERIC_BLOG_HOSTS = {
    "twitter.com", "x.com", "linkedin.com", "youtube.com", "medium.com",
    "instagram.com", "facebook.com", "t.me", "dev.to", "substack.com",
    "gmail.com", "about.me", "linktr.ee", "calendly.com",
}

ADJUDICATION_PROMPT = """You are doing identity resolution. A GitHub user and a
Hacker News user share the exact same username. You receive GitHub-side
identity facts (profile name/bio/company/blog, and for YC founders also their
company, website, twitter) and the HN account's public 'about' text plus karma.
Decide whether the HN account belongs to the same person. Be conservative:
shared username alone is NOT enough; the about text must be consistent with
(or confirm) the GitHub-side facts, and must not contradict them (different
name, different unrelated profession, different country + different field,
etc.). Ambiguous/empty evidence => UNCERTAIN.

Return ONLY a JSON object:
{
  "verdict": "SAME_PERSON | UNCERTAIN | DIFFERENT_PERSON",
  "reason": "<one sentence>"
}"""


def hn_user(client: httpx.Client, username: str) -> dict | None:
    """HN Firebase user record (None if no such account). Cached."""
    return get_json(
        client,
        f"https://hacker-news.firebaseio.com/v0/user/{username}.json",
        "hn_user_v0",
        username,
    )


def author_stories(client: httpx.Client, hn_username: str) -> list[dict]:
    """All stories submitted by an HN account (Algolia author tag). Cached."""
    params = httpx.QueryParams(
        {"tags": f"story,author_{hn_username}", "hitsPerPage": 1000}
    )
    data = get_json(
        client,
        f"https://hn.algolia.com/api/v1/search_by_date?{params}",
        "hn_person_stories",
        hn_username,
    )
    out = []
    for hit in (data or {}).get("hits", []):
        title = hit.get("title") or ""
        lowered = title.lower()
        out.append(
            {
                "story_id": int(hit["objectID"]),
                "author": hit.get("author"),
                "title": title,
                "story_url": hit.get("url"),
                "points": hit.get("points"),
                "created_at": hit.get("created_at"),
                "is_show_hn": lowered.startswith("show hn"),
                "is_launch_hn": lowered.startswith("launch hn"),
            }
        )
    return out


def is_rare_login(login: str) -> bool:
    """Rare enough that an exact HN collision is unlikely (medium tier)."""
    return len(login) >= 10 or (
        len(login) >= 8 and any(c.isdigit() or c in "-_" for c in login)
    )


def _domain_of(url: str | None) -> str | None:
    if not url:
        return None
    m = re.search(r"https?://(?:www\.)?([^/\s]+)", url)
    return m.group(1).lower() if m else None


def _twitter_handle(url: str | None) -> str | None:
    if not url:
        return None
    m = re.search(r"(?:twitter|x)\.com/@?([A-Za-z0-9_]+)", url)
    return m.group(1).lower() if m else None


def founder_about_evidence(
    about: str, founder_rows: list[dict]
) -> tuple[str, str] | None:
    """Founder-metadata evidence tiers in an HN about field: (grade, detail)."""
    a = about.lower()
    for f in founder_rows:
        dom = _domain_of(f.get("company_website"))
        if dom and dom in a:
            return "strong_company_domain", f"about mentions company domain {dom}"
        comp = (f.get("company") or "").strip().lower()
        if comp and len(comp) >= 4 and comp in a:
            return "strong_company_name", f"about mentions company '{f['company']}'"
        th = _twitter_handle(f.get("twitter_url"))
        if th and re.search(r"(?:twitter|x)\.com/@?" + re.escape(th) + r"(?![\w])", a):
            return "strong_twitter", f"about links twitter @{th}"
        name = (f.get("founder_name") or "").strip().lower()
        if name and len(name) >= 7 and name in a:
            return "strong_founder_name", f"about states name '{f['founder_name']}'"
    return None


def adjudicate_identity(
    client: httpx.Client, api_key: str, login: str, about: str, karma: int,
    founder_rows: list[dict], gh_profile: dict | None,
) -> dict | None:
    """LLM adjudication of one ambiguous identity match (cached, temp 0)."""
    facts = {
        "yc_founder_facts": [
            {k: f.get(k) for k in ("founder_name", "company", "company_website", "twitter_url")}
            for f in founder_rows
        ],
        "gh_profile": {
            k: (gh_profile or {}).get(k) for k in ("name", "bio", "company", "blog")
        },
    }
    user_msg = (
        f"Shared username: {login}\n"
        f"GitHub-side facts: {json.dumps(facts)}\n"
        f"HN account: karma={karma}\nHN about text:\n{about[:2000]}"
    )
    cache_path = LLM_CACHE_DIR / (
        hashlib.sha256((MODEL + login + user_msg).encode()).hexdigest() + ".json"
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
                        {"role": "system", "content": ADJUDICATION_PROMPT},
                        {"role": "user", "content": user_msg},
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
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(json.dumps(record))
            return record
        except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError) as error:
            LOGGER.warning("%s adjudication attempt %d: %s", login, attempt + 1, error)
            time.sleep(2**attempt)
    return None


def verified_launch_authors() -> set[str]:
    """HN usernames wave-2 verified as founder launch authors, author==gh_login."""
    if not LAUNCHES_PATH.exists():
        return set()
    launches = pl.read_parquet(LAUNCHES_PATH)
    return {
        r["author"].lower()
        for r in launches.iter_rows(named=True)
        if r["match_grade"] == "strong_author"
    }


def gh_profile_evidence(
    login: str, about_lower: str, stories: list[dict], gh_profile: dict
) -> tuple[str, str, str] | None:
    """Class-symmetric tiers from the actor's CURRENT-DAY GitHub profile."""
    profile_url = f"https://news.ycombinator.com/user?id={login}"
    dom = _domain_of(
        b if (b := gh_profile.get("blog") or "").startswith("http") else f"https://{b}"
    )
    if dom and dom not in GENERIC_BLOG_HOSTS and "github" not in dom:
        if dom in about_lower:
            return (
                "strong_gh_blog_domain",
                f"HN about mentions GH profile blog domain {dom}",
                profile_url,
            )
        linking = [
            s for s in stories
            if dom in (_domain_of(s.get("story_url")) or "")
        ]
        if len(linking) >= 2:
            return (
                "strong_gh_blog_domain",
                f"{len(linking)} authored stories link GH profile blog domain {dom}",
                f"https://news.ycombinator.com/item?id={linking[0]['story_id']}",
            )
    name = (gh_profile.get("name") or "").strip().lower()
    if len(name) >= 7 and " " in name and name in about_lower:
        return (
            "strong_gh_name",
            f"HN about states GH profile name '{gh_profile['name']}'",
            profile_url,
        )
    return None


def grade_actor(
    login: str,
    user: dict,
    stories: list[dict],
    founder_rows: list[dict],
    launch_authors: set[str],
    gh_profile: dict | None = None,
) -> tuple[str, str, str]:
    """Return (match_grade, evidence, evidence_url) for an existing HN account."""
    profile_url = f"https://news.ycombinator.com/user?id={login}"
    about = html.unescape(user.get("about") or "")
    a = about.lower()
    if re.search(r"github\.com/" + re.escape(login) + r"(?![\w-])", a):
        return "strong_github_link", f"about links github.com/{login}", profile_url
    for s in stories:
        url = (s.get("story_url") or "").lower()
        if re.search(r"github\.com/" + re.escape(login) + r"(?:[/?#]|$)", url):
            return (
                "strong_story_github_url",
                f"authored story links {s['story_url']}",
                f"https://news.ycombinator.com/item?id={s['story_id']}",
            )
    if founder_rows:
        ev = founder_about_evidence(about, founder_rows)
        if ev:
            return ev[0], ev[1], profile_url
        if login in launch_authors:
            return (
                "strong_launch_author",
                "authored a wave-2-verified company launch story (author == gh_login)",
                profile_url,
            )
    if gh_profile:
        ev = gh_profile_evidence(login, a, stories, gh_profile)
        if ev:
            return ev
    if is_rare_login(login):
        return (
            "medium_rare_name",
            f"exact match of rare username '{login}' (no confirming about)",
            profile_url,
        )
    return "exists_unconfirmed", f"HN user exists, karma={user.get('karma', 0)}, no confirming evidence", profile_url


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    load_dotenv("/Users/mishaaghamalyan/Development/personal/competitions/vc_brain/.env")
    api_key = os.getenv("OPENROUTER_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_KEY missing")

    cohort = pl.read_parquet(FULL_COHORT_PATH).sort("gh_login")
    founders_meta = pl.read_parquet(FOUNDERS_PATH).with_columns(
        pl.col("gh_login").str.to_lowercase().alias("login_lc")
    )
    founder_rows_by_login: dict[str, list[dict]] = {}
    for r in founders_meta.iter_rows(named=True):
        if r["login_lc"]:
            founder_rows_by_login.setdefault(r["login_lc"], []).append(r)
    launch_authors = verified_launch_authors()
    LOGGER.info(
        "probing %d actors (%d wave-2 verified launch authors available)",
        cohort.height, len(launch_authors),
    )

    person_records: list[dict] = []
    story_records: list[dict] = []
    llm_pending: list[dict] = []
    n_exists = 0
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=20) as web:
        for i, row in enumerate(cohort.iter_rows(named=True), 1):
            login = row["gh_login"]
            user = hn_user(web, login)
            base = {
                "gh_login": login,
                "person_type": row["person_type"],
                "t_cutoff": row["t_cutoff"],
                "peak": row["peak"],
                "data_basis": "current_day_label_only",
            }
            if not user:
                person_records.append(
                    base | {
                        "hn_username": None, "hn_exists": False, "karma": None,
                        "hn_created_at": None, "has_about": False,
                        "match_grade": "no_account", "evidence": None,
                        "evidence_url": None, "n_stories": 0,
                    }
                )
            else:
                n_exists += 1
                stories = author_stories(web, login)
                founder_rows = (
                    founder_rows_by_login.get(login, [])
                    if row["person_type"] == "positive"
                    else []
                )
                grade, evidence, evidence_url = grade_actor(
                    login, user, stories, founder_rows, launch_authors
                )
                gh_profile = None
                if grade in ("exists_unconfirmed", "medium_rare_name"):
                    # Second-pass, class-symmetric evidence from the actor's
                    # current-day GitHub profile (cached gh CLI call).
                    try:
                        gh_profile = gh_api_user(login)
                    except RuntimeError as error:
                        LOGGER.warning("gh profile %s: %s", login, error)
                    if gh_profile:
                        grade, evidence, evidence_url = grade_actor(
                            login, user, stories, founder_rows, launch_authors,
                            gh_profile,
                        )
                about = html.unescape(user.get("about") or "")
                has_gh_facts = any(
                    (gh_profile or {}).get(k) for k in ("name", "bio", "company", "blog")
                )
                if (
                    grade in ("exists_unconfirmed", "medium_rare_name")
                    and about.strip()
                    and (founder_rows or has_gh_facts)
                ):
                    llm_pending.append(
                        {
                            "login": login, "about": about,
                            "karma": user.get("karma", 0),
                            "founder_rows": founder_rows,
                            "gh_profile": gh_profile,
                        }
                    )
                person_records.append(
                    base | {
                        "hn_username": login, "hn_exists": True,
                        "karma": user.get("karma"),
                        "hn_created_at": user.get("created"),
                        "has_about": bool(about.strip()),
                        "match_grade": grade, "evidence": evidence,
                        "evidence_url": evidence_url, "n_stories": len(stories),
                    }
                )
                for s in stories:
                    story_records.append(
                        {
                            "gh_login": login,
                            "person_type": row["person_type"],
                            "t_cutoff": row["t_cutoff"],
                            **s,
                            "url": f"https://news.ycombinator.com/item?id={s['story_id']}",
                        }
                    )
            if i % 100 == 0:
                LOGGER.info(
                    "progress %d/%d probed, %d accounts exist, %d stories",
                    i, cohort.height, n_exists, len(story_records),
                )

    # LLM adjudication of ambiguous founder matches (cap ~tens of calls;
    # highest-karma first — those are the consequential accounts).
    llm_pending.sort(key=lambda p: -(p["karma"] or 0))
    if len(llm_pending) > MAX_LLM_CALLS:
        LOGGER.info(
            "capping LLM adjudication at %d of %d ambiguous founder matches",
            MAX_LLM_CALLS, len(llm_pending),
        )
        llm_pending = llm_pending[:MAX_LLM_CALLS]
    upgrades: dict[str, tuple[str, str]] = {}
    with httpx.Client() as llm:
        for p in llm_pending:
            verdict = adjudicate_identity(
                llm, api_key, p["login"], p["about"], p["karma"],
                p["founder_rows"], p["gh_profile"],
            )
            if verdict and verdict.get("verdict") == "SAME_PERSON":
                upgrades[p["login"]] = (
                    "llm_confirmed",
                    f"LLM adjudication: {verdict.get('reason', '')}"[:300],
                )
            elif verdict and verdict.get("verdict") == "DIFFERENT_PERSON":
                upgrades[p["login"]] = (
                    "llm_rejected",
                    f"LLM adjudication: {verdict.get('reason', '')}"[:300],
                )
    LOGGER.info("LLM adjudicated %d, upgrades/rejections: %d", len(llm_pending), len(upgrades))
    for rec in person_records:
        if rec["gh_login"] in upgrades:
            grade, evidence = upgrades[rec["gh_login"]]
            rec["match_grade"], rec["evidence"] = grade, evidence

    persons = pl.DataFrame(person_records).with_columns(
        pl.col("match_grade").is_in(sorted(CONFIRMED_GRADES)).alias("confirmed"),
        pl.col("match_grade").is_in(sorted(STRICT_GRADES)).alias("confirmed_strict"),
        pl.col("match_grade").is_in(sorted(SYMMETRIC_GRADES)).alias("confirmed_symmetric"),
    )
    PERSONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    persons.write_parquet(PERSONS_PATH)
    print(f"wrote {persons.height} persons -> {PERSONS_PATH}")

    confirmed_logins = set(
        persons.filter(pl.col("confirmed"))["gh_login"].to_list()
    )
    stories = (
        pl.DataFrame(story_records)
        .filter(pl.col("gh_login").is_in(sorted(confirmed_logins)))
        .with_columns(
            pl.col("created_at").str.to_datetime("%Y-%m-%dT%H:%M:%SZ", strict=False)
        )
        .with_columns(
            pl.when(pl.col("created_at").dt.date() < pl.col("t_cutoff"))
            .then(pl.lit("pre_cutoff"))
            .otherwise(pl.lit("post_cutoff"))
            .alias("pre_or_post_cutoff")
        )
        .sort("gh_login", "created_at")
        if story_records
        else pl.DataFrame()
    )
    stories.write_parquet(STORIES_PATH)
    print(f"wrote {stories.height} stories (confirmed accounts only) -> {STORIES_PATH}")

    print("\n=== match grades by person_type ===")
    print(
        persons.group_by("person_type", "match_grade").len()
        .sort("person_type", "len", descending=[True, True])
    )


if __name__ == "__main__":
    main()
