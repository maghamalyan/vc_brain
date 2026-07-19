"""Task 1: HN linkage feasibility for YC founders with gh_confidence >= 0.5.

Strategy per founder:
  (a) HN user with username == gh_login  -> confirm via 'about' field
      (github link, twitter handle, company domain/name).
  (b) Algolia search for Launch HN / Show HN stories mentioning the company
      -> check story author against founder gh_login / name; confirm author
      profile 'about' when there is a candidate hit.

Politeness: <=2 req/s (0.55s sleep), exponential backoff, disk cache.
"""
import json, re, time, random, sys
from pathlib import Path
import httpx
import polars as pl

ROOT = Path("/Users/mishaaghamalyan/Development/personal/competitions/vc_brain")
SCRATCH = Path("/private/tmp/claude-501/-Users-mishaaghamalyan-Development-personal-competitions-vc-brain/4f97507a-6fcd-448b-89eb-358a63f57ae1/scratchpad")
CACHE = SCRATCH / "cache" / "hn"
CACHE.mkdir(parents=True, exist_ok=True)

UA = "vc-brain-research/0.1 (contact: misha.aghamalyan@gmail.com; feasibility study)"
client = httpx.Client(headers={"User-Agent": UA}, timeout=20, follow_redirects=True)

LAST_REQ = [0.0]
def _throttle():
    dt = time.time() - LAST_REQ[0]
    if dt < 0.55:
        time.sleep(0.55 - dt)
    LAST_REQ[0] = time.time()

def get_json(url, cache_key):
    fp = CACHE / (cache_key + ".json")
    if fp.exists():
        return json.loads(fp.read_text())
    for attempt in range(5):
        _throttle()
        try:
            r = client.get(url)
            if r.status_code == 200:
                data = r.json()
                fp.write_text(json.dumps(data))
                return data
            if r.status_code == 404:
                fp.write_text("null")
                return None
            if r.status_code in (429, 500, 502, 503):
                time.sleep(2 ** attempt)
                continue
            fp.write_text("null")
            return None
        except (httpx.HTTPError, json.JSONDecodeError):
            time.sleep(2 ** attempt)
    return None

def safe_key(s):
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", s)[:100]

def hn_user(username):
    return get_json(
        f"https://hacker-news.firebaseio.com/v0/user/{username}.json",
        "user_" + safe_key(username.lower()),
    )

def algolia_story_search(query):
    q = httpx.QueryParams({"query": query, "tags": "story",
                           "restrictSearchableAttributes": "title", "hitsPerPage": 30})
    return get_json(f"https://hn.algolia.com/api/v1/search?{q}",
                    "search_" + safe_key(query.lower()))

def domain_of(url):
    if not url:
        return None
    m = re.search(r"https?://(?:www\.)?([^/\s]+)", url)
    return m.group(1).lower() if m else None

def twitter_handle(url):
    if not url:
        return None
    m = re.search(r"(?:twitter|x)\.com/@?([A-Za-z0-9_]+)", url)
    return m.group(1).lower() if m else None

def about_evidence(about, row):
    """Return list of confirmation evidence strings found in an HN 'about' field."""
    if not about:
        return []
    a = about.lower()
    ev = []
    gh = (row["gh_login"] or "").lower()
    if gh and re.search(r"github\.com/" + re.escape(gh) + r"(?![\w-])", a):
        ev.append(f"about links github.com/{gh}")
    th = twitter_handle(row["twitter_url"])
    if th and re.search(r"(?:twitter|x)\.com/@?" + re.escape(th) + r"(?![\w])", a):
        ev.append(f"about links twitter @{th}")
    dom = domain_of(row["company_website"])
    if dom and dom in a:
        ev.append(f"about mentions company domain {dom}")
    comp = (row["company"] or "").lower()
    if comp and len(comp) >= 4 and comp in a:
        ev.append(f"about mentions company name '{row['company']}'")
    name = (row["founder_name"] or "").lower()
    if name and name in a:
        ev.append(f"about states founder name '{row['founder_name']}'")
    return ev

def name_variants(name):
    parts = re.sub(r"[^a-z ]", "", name.lower()).split()
    if not parts:
        return set()
    v = set()
    first, last = parts[0], parts[-1]
    v.add(first + last)
    v.add(first + "_" + last)
    v.add(first + "." + last)
    v.add(first[0] + last)
    v.add(first + last[0])
    if len(first) >= 5:
        v.add(first)
    return v

def author_matches_founder(author, row):
    a = author.lower()
    gh = (row["gh_login"] or "").lower()
    if a == gh:
        return "author == gh_login"
    if gh and (a in gh or gh in a) and min(len(a), len(gh)) >= 5:
        return f"author ~ gh_login ({author} vs {gh})"
    if a in name_variants(row["founder_name"] or ""):
        return f"author matches founder name variant ({author})"
    return None

def main():
    df = pl.read_parquet(ROOT / "data/labels/founders.parquet")
    pool = df.filter(pl.col("gh_confidence") >= 0.5)
    random.seed(42)
    idx = random.sample(range(pool.height), 150)
    sample = pool[idx]
    results = []
    for i, row in enumerate(sample.iter_rows(named=True)):
        rec = {"founder_name": row["founder_name"], "company": row["company"],
               "slug": row["slug"], "batch": row["batch"], "gh_login": row["gh_login"],
               "linked": False, "method": None, "evidence": [], "quality": None,
               "hn_username": None, "hn_url": None}
        gh = row["gh_login"]
        # (a) same-username probe
        u = hn_user(gh) if gh else None
        if u:
            ev = about_evidence(u.get("about", ""), row)
            karma = u.get("karma", 0)
            if ev:
                rec.update(linked=True, method="username==gh_login + about confirmation",
                           evidence=ev + [f"karma={karma}"], quality="strong",
                           hn_username=gh, hn_url=f"https://news.ycombinator.com/user?id={gh}")
            else:
                rec.update(method="username==gh_login, unconfirmed",
                           evidence=[f"HN user '{gh}' exists, karma={karma}, no confirming about"],
                           quality="weak-unconfirmed", hn_username=gh,
                           hn_url=f"https://news.ycombinator.com/user?id={gh}")
        # (b) Launch HN / Show HN search (only if not already strongly linked)
        comp = row["company"]
        if comp and rec["quality"] != "strong":
            hits = algolia_story_search(comp) or {"hits": []}
            for h in hits.get("hits", []):
                title = (h.get("title") or "")
                tl = title.lower()
                if not (tl.startswith("launch hn") or tl.startswith("show hn")):
                    continue
                if comp.lower() not in tl:
                    continue
                author = h.get("author") or ""
                m = author_matches_founder(author, row)
                if m:
                    ev = [f"story '{title}' by {author}: {m}",
                          f"https://news.ycombinator.com/item?id={h.get('objectID')}"]
                    # confirm via author's about
                    au = hn_user(author)
                    aev = about_evidence((au or {}).get("about", ""), row)
                    quality = "strong" if (author.lower() == (gh or '').lower() or aev) else "medium"
                    rec.update(linked=True,
                               method=(rec["method"] or "") + " + launch/show HN author match",
                               evidence=rec["evidence"] + ev + aev, quality=quality,
                               hn_username=author,
                               hn_url=f"https://news.ycombinator.com/user?id={author}")
                    break
                else:
                    rec["evidence"].append(
                        f"launch/show story '{title}' by '{author}' — author does not match this founder")
                    if not rec["method"]:
                        rec["method"] = "company launch story found, different author"
        # weak-unconfirmed username-only stays linked=False
        results.append(rec)
        if (i + 1) % 25 == 0:
            print(f"[{i+1}/150] done", flush=True)
    out = SCRATCH / "hn_results.json"
    out.write_text(json.dumps(results, indent=1))
    linked = [r for r in results if r["linked"]]
    print(f"linked: {len(linked)}/150")
    from collections import Counter
    print(Counter(r["quality"] for r in results))

if __name__ == "__main__":
    main()
