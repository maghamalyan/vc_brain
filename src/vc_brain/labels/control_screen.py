"""Control screening: estimate label noise with real n.

For every annotated pilot control with gestation_likelihood >= 50 (plus a
seed-42 random contrast group of 40 with gestation <= 15), collect
CURRENT-DAY founder evidence — GitHub profile bio/company/blog, the blog
page itself, and HN "Launch HN"/"Show HN" authorship — and classify each
person FOUNDER_EVIDENCE / MEET_WORTHY / NO_EVIDENCE / GONE.

All data collected here is current-day and is used for LABEL/IDENTITY
SCREENING ONLY — it must never feed model features (leakage rule 1).
Ambiguous evidence bundles are adjudicated by an LLM (temp 0, cached).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import re

import httpx
import polars as pl
from dotenv import load_dotenv
from scipy.stats import beta

from vc_brain.ingest.contracts import DATA_ROOT
from vc_brain.labels.probe_net import (
    USER_AGENT,
    gh_api_user,
    get_json,
    get_text,
    strip_html,
)
from vc_brain.semantics.person_annotate import ANNOTATIONS_PATH
from vc_brain.semantics.person_extract import PILOT_COHORT_PATH

LOGGER = logging.getLogger(__name__)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.getenv("OPENROUTER_MODEL", "anthropic/claude-sonnet-4.5")
LLM_CACHE_DIR = DATA_ROOT / "cache" / "labelnoise" / "screen_llm"
SCREEN_PATH = DATA_ROOT / "pilot" / "control_screen.parquet"

HIGH_GESTATION = 50
LOW_GESTATION = 15
LOW_SAMPLE_N = 40
SEED = 42

FOUNDER_BIO_RE = re.compile(
    r"(?i)\b(founder|co[- ]?founder|founding|ceo|cto|chief executive|"
    r"chief technology|building [A-Za-z]|we're hiring|my startup)\b"
)

SYSTEM_PROMPT = """You are screening a GitHub user's CURRENT public profile
evidence to decide whether they are actually a startup founder that a
YC-only label source missed. You receive: their GitHub bio/company/blog
fields, an excerpt of the page their blog URL resolves to, and any Hacker
News "Launch HN"/"Show HN" stories they authored.

Classify conservatively into exactly one of:
- FOUNDER_EVIDENCE: concrete evidence they founded/run a company or
  commercial product TODAY (founder/CEO title, company they own, product
  page with commercial framing, a Launch HN they authored). A live product
  with pricing/signup counts even without an "Inc.".
- MEET_WORTHY: not a demonstrated founder, but a VC sourcer would plausibly
  take the meeting: high-adoption OSS author, product-shaped project suite
  with own domain/docs, indie hacker shipping to users.
- NO_EVIDENCE: employee, student, hobbyist, or nothing founder-shaped.

Return ONLY a JSON object:
{
  "classification": "FOUNDER_EVIDENCE | MEET_WORTHY | NO_EVIDENCE",
  "company_or_product": "<name or null>",
  "best_evidence": "<one sentence citing the strongest single piece>",
  "evidence_url": "<the single most probative URL>"
}"""


def select_screen_cohort() -> pl.DataFrame:
    """High-gestation controls (all) + seed-42 sample of low-gestation ones."""
    cohort = pl.read_parquet(PILOT_COHORT_PATH)
    ann = pl.read_parquet(ANNOTATIONS_PATH).with_columns(
        pl.col("gestation_likelihood").cast(pl.Float64, strict=False)
    )
    controls = (
        cohort.join(ann, on="gh_login", how="inner")
        .filter(pl.col("person_type") == "control")
        .sort("gh_login")
    )
    high = controls.filter(
        pl.col("gestation_likelihood") >= HIGH_GESTATION
    ).with_columns(pl.lit("high_gestation").alias("screen_group"))
    low_pool = controls.filter(pl.col("gestation_likelihood") <= LOW_GESTATION)
    rng = random.Random(SEED)
    idx = sorted(rng.sample(range(low_pool.height), LOW_SAMPLE_N))
    low = low_pool[idx].with_columns(pl.lit("low_gestation").alias("screen_group"))
    return pl.concat([high, low]).select(
        "gh_login", "screen_group", "gestation_likelihood", "peak",
        "builder_type", "building_what",
    )


def hn_launch_stories(client: httpx.Client, login: str) -> list[dict]:
    """Launch/Show HN stories authored by an HN account named <login>."""
    params = httpx.QueryParams(
        {"tags": f"story,author_{login}", "hitsPerPage": 100}
    )
    data = get_json(
        client,
        f"https://hn.algolia.com/api/v1/search_by_date?{params}",
        "hn_author",
        login.lower(),
    )
    stories = []
    for hit in (data or {}).get("hits", []):
        title = (hit.get("title") or "").lower()
        if title.startswith("launch hn") or title.startswith("show hn"):
            stories.append(
                {
                    "title": hit.get("title"),
                    "author": hit.get("author"),
                    "created_at": hit.get("created_at"),
                    "url": f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                }
            )
    return stories


def collect_evidence(client: httpx.Client, login: str) -> dict:
    """Current-day evidence bundle for one control. LABEL USE ONLY."""
    user = gh_api_user(login)
    if user is None:
        return {"gone": True}
    bio = user.get("bio") or ""
    company = user.get("company") or ""
    blog = user.get("blog") or ""
    name = user.get("name") or ""
    blog_excerpt = None
    if blog:
        url = blog if blog.startswith("http") else f"https://{blog}"
        html = get_text(client, url, "blogs", login.lower())
        if html:
            blog_excerpt = strip_html(html)
    launches = hn_launch_stories(client, login)
    return {
        "gone": False,
        "name": name,
        "bio": bio,
        "company": company,
        "blog": blog,
        "blog_excerpt": blog_excerpt,
        "hn_launches": launches,
        "bio_founder_regex": bool(FOUNDER_BIO_RE.search(bio)),
        "followers": user.get("followers"),
        "profile_url": f"https://github.com/{login}",
    }


def adjudicate(
    client: httpx.Client, api_key: str, login: str, evidence: dict
) -> dict | None:
    """LLM adjudication of an ambiguous evidence bundle (cached, temp 0)."""
    payload = {k: v for k, v in evidence.items() if k != "gone"}
    digest = json.dumps(payload, sort_keys=True)
    cache_path = LLM_CACHE_DIR / (
        hashlib.sha256((MODEL + login + digest).encode()).hexdigest() + ".json"
    )
    if cache_path.exists():
        return json.loads(cache_path.read_text())
    user_msg = f"GitHub login: {login}\nEvidence bundle:\n{json.dumps(payload, indent=1)}"
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
            import time

            time.sleep(2**attempt)
    return None


def screen_one(
    web: httpx.Client, llm: httpx.Client, api_key: str, login: str
) -> dict:
    evidence = collect_evidence(web, login)
    base = {
        "gh_login": login,
        "profile_url": f"https://github.com/{login}",
        "data_basis": "current_day_label_only",
    }
    if evidence["gone"]:
        return base | {
            "classification": "GONE",
            "company_or_product": None,
            "best_evidence": "gh api users/<login> -> 404",
            "evidence_url": f"https://github.com/{login}",
        }
    has_any = (
        evidence["bio"]
        or evidence["company"]
        or evidence["blog"]
        or evidence["hn_launches"]
    )
    if not has_any:
        return base | {
            "classification": "NO_EVIDENCE",
            "company_or_product": None,
            "best_evidence": "profile has no bio, company, blog, or HN launches",
            "evidence_url": f"https://github.com/{login}",
        }
    verdict = adjudicate(llm, api_key, login, evidence)
    if verdict is None:
        return base | {
            "classification": "ADJUDICATION_FAILED",
            "company_or_product": None,
            "best_evidence": None,
            "evidence_url": f"https://github.com/{login}",
        }
    return base | {
        "classification": verdict.get("classification", "NO_EVIDENCE"),
        "company_or_product": verdict.get("company_or_product"),
        "best_evidence": verdict.get("best_evidence"),
        "evidence_url": verdict.get("evidence_url") or f"https://github.com/{login}",
    }


def binomial_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Exact Clopper-Pearson interval."""
    if n == 0:
        return (float("nan"), float("nan"))
    lo = 0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k))
    return lo, hi


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    load_dotenv("/Users/mishaaghamalyan/Development/personal/competitions/vc_brain/.env")
    api_key = os.getenv("OPENROUTER_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_KEY missing")

    cohort = select_screen_cohort()
    LOGGER.info(
        "screening %d controls (%s)",
        cohort.height,
        dict(cohort.group_by("screen_group").len().iter_rows()),
    )
    records = []
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=20) as web:
        with httpx.Client() as llm:
            for i, login in enumerate(cohort["gh_login"], 1):
                records.append(screen_one(web, llm, api_key, login))
                if i % 10 == 0:
                    LOGGER.info("progress %d/%d", i, cohort.height)

    out = cohort.join(pl.DataFrame(records), on="gh_login", how="left")
    SCREEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.write_parquet(SCREEN_PATH)
    print(f"wrote {out.height} rows -> {SCREEN_PATH}")

    print("\n=== classification by screen group ===")
    print(
        out.group_by("screen_group", "classification")
        .len()
        .sort("screen_group", "len", descending=[False, True])
    )
    print("\n=== label-noise rates (FOUNDER_EVIDENCE / screenable) ===")
    for group in ("high_gestation", "low_gestation"):
        sub = out.filter(
            (pl.col("screen_group") == group)
            & (pl.col("classification") != "GONE")
        )
        k = sub.filter(pl.col("classification") == "FOUNDER_EVIDENCE").height
        km = sub.filter(
            pl.col("classification").is_in(["FOUNDER_EVIDENCE", "MEET_WORTHY"])
        ).height
        n = sub.height
        lo, hi = binomial_ci(k, n)
        lom, him = binomial_ci(km, n)
        print(
            f"{group:15s} founder: {k}/{n} = {k/n:.1%} (95% CI {lo:.1%}-{hi:.1%})"
            f" | founder+meet: {km}/{n} = {km/n:.1%} (CI {lom:.1%}-{him:.1%})"
        )
    print("\n=== confirmed unlabeled founders ===")
    print(
        out.filter(pl.col("classification") == "FOUNDER_EVIDENCE")
        .select("gh_login", "screen_group", "gestation_likelihood",
                "company_or_product", "evidence_url")
        .sort("screen_group", "gh_login")
    )


if __name__ == "__main__":
    main()
