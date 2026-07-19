"""Task 4: Devpost discoverability probe — try devpost.com/<gh_login> for 30 founders.
Linked iff profile page links github.com/<gh_login> (strong) or profile real name
matches founder name (medium)."""
import json, re, time, random, html
from pathlib import Path
import httpx
import polars as pl

ROOT = Path("/Users/mishaaghamalyan/Development/personal/competitions/vc_brain")
SCRATCH = Path("/private/tmp/claude-501/-Users-mishaaghamalyan-Development-personal-competitions-vc-brain/4f97507a-6fcd-448b-89eb-358a63f57ae1/scratchpad")
CACHE = SCRATCH / "cache" / "devpost"
CACHE.mkdir(parents=True, exist_ok=True)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
c = httpx.Client(headers={"User-Agent": UA}, timeout=20, follow_redirects=True)

def norm(s):
    return re.sub(r"[^a-z ]", "", (s or "").lower()).strip()

def main():
    df = pl.read_parquet(ROOT / "data/labels/founders.parquet")
    pool = df.filter(pl.col("gh_confidence") >= 0.5)
    random.seed(7)
    idx = random.sample(range(pool.height), 30)
    sample = pool[idx]
    results = []
    for row in sample.iter_rows(named=True):
        gh = row["gh_login"]
        fp = CACHE / f"{gh}.html"
        if fp.exists():
            text = fp.read_text()
            status = 200 if text != "404" else 404
        else:
            time.sleep(0.6)
            try:
                r = c.get(f"https://devpost.com/{gh}")
                status = r.status_code
                text = r.text if status == 200 else "404"
                fp.write_text(text)
            except httpx.HTTPError:
                status, text = 0, ""
        rec = {"founder_name": row["founder_name"], "company": row["company"],
               "gh_login": gh, "status": status, "linked": False, "quality": None,
               "profile_name": None, "url": f"https://devpost.com/{gh}", "evidence": []}
        if status == 200:
            m = re.search(r"<title>(.*?)&#39;s", text)
            pname = html.unescape(m.group(1).strip()) if m else None
            rec["profile_name"] = pname
            gh_link = bool(re.search(r"github\.com/" + re.escape(gh) + r'["/\s?]', text, re.I))
            nf, np_ = norm(row["founder_name"]).split() or [""], norm(pname or "").split() or [""]
            name_match = (nf and np_ and nf[0] == np_[0] and nf[-1] == np_[-1])
            first_match = bool(nf and np_ and nf[0] == np_[0])
            if gh_link:
                rec.update(linked=True, quality="strong")
                rec["evidence"].append(f"profile links github.com/{gh}")
            if name_match:
                rec["linked"] = True
                rec["quality"] = rec["quality"] or "medium"
                rec["evidence"].append(f"profile name '{pname}' == founder name")
            elif first_match and not gh_link:
                rec["evidence"].append(f"profile name '{pname}' shares first name only — NOT counted")
            if not rec["linked"]:
                rec["evidence"].append(f"username exists but belongs to '{pname}' — collision")
        results.append(rec)
        print(f"{gh}: {status} linked={rec['linked']} ({rec['quality']}) profile={rec['profile_name']}", flush=True)
    (SCRATCH / "devpost_results.json").write_text(json.dumps(results, indent=1))
    print(f"\nlinked: {sum(r['linked'] for r in results)}/30; profiles-exist: {sum(r['status']==200 for r in results)}/30")

if __name__ == "__main__":
    main()
