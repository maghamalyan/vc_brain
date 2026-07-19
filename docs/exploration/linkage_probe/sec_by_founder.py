"""Task 2b: SEC FTS by FOUNDER NAME (officer names are full-text indexed in Form D XML).
Same 40 sampled companies; for each founder, q="Full Name" forms=D.
Verification: entity name ~ company name, or >=2 cofounders in same accession."""
import json, re, time, random
from pathlib import Path
import httpx
import polars as pl

ROOT = Path("/Users/mishaaghamalyan/Development/personal/competitions/vc_brain")
SCRATCH = Path("/private/tmp/claude-501/-Users-mishaaghamalyan-Development-personal-competitions-vc-brain/4f97507a-6fcd-448b-89eb-358a63f57ae1/scratchpad")
CACHE = SCRATCH / "cache" / "sec"
UA = "VC Brain research (misha.aghamalyan@gmail.com)"
client = httpx.Client(headers={"User-Agent": UA}, timeout=25)
LAST = [0.0]

def get(url, key):
    fp = CACHE / (key + ".json")
    if fp.exists():
        return json.loads(fp.read_text())
    for attempt in range(5):
        dt = time.time() - LAST[0]
        if dt < 0.55:
            time.sleep(0.55 - dt)
        LAST[0] = time.time()
        try:
            r = client.get(url)
            if r.status_code == 200:
                d = r.json()
                fp.write_text(json.dumps(d))
                return d
            time.sleep(2 ** attempt)
        except httpx.HTTPError:
            time.sleep(2 ** attempt)
    return None

def norm(s):
    return re.sub(r"[^a-z0-9 ]", " ", (s or "").lower()).strip()

def main():
    df = pl.read_parquet(ROOT / "data/labels/founders.parquet")
    df = df.with_columns(pl.col("batch").str.extract(r"(\d{4})").cast(pl.Int32).alias("byear"))
    comps = (df.filter(pl.col("byear").is_in([2024, 2025]))
               .group_by(["company", "slug", "batch"])
               .agg(pl.col("founder_name").alias("founders"))).sort("slug")
    random.seed(42)
    idx = random.sample(range(comps.height), 40)
    sample = comps[idx]
    results = []
    for row in sample.iter_rows(named=True):
        comp, nc = row["company"], norm(row["company"])
        founder_hits = {}
        for fname in row["founders"]:
            q = httpx.QueryParams({"q": f'"{fname}"', "forms": "D"})
            d = get(f"https://efts.sec.gov/LATEST/search-index?{q}",
                    "byname_" + re.sub(r"[^a-z0-9]", "_", fname.lower())[:80])
            hits = (d or {}).get("hits", {}).get("hits", [])[:10]
            founder_hits[fname] = [
                {"id": h["_id"], "entity": (h["_source"].get("display_names") or [""])[0],
                 "date": h["_source"].get("file_date")} for h in hits]
        # verification
        verified = []
        accs = {}
        for fname, hs in founder_hits.items():
            for h in hs:
                ne = norm(h["entity"].split("(CIK")[0])
                if nc and (ne.startswith(nc) or nc in ne):
                    verified.append({"founder": fname, "via": "entity~company", **h})
                accs.setdefault(h["id"], set()).add(fname)
        for acc, who in accs.items():
            if len(who) >= 2:
                ent = next(h["entity"] for hs in founder_hits.values() for h in hs if h["id"] == acc)
                verified.append({"founder": ", ".join(sorted(who)), "via": ">=2 cofounders same filing",
                                 "id": acc, "entity": ent, "date": None})
        any_hit = any(founder_hits.values())
        results.append({"company": comp, "batch": row["batch"], "founders": row["founders"],
                        "any_name_hit": any_hit, "verified": verified,
                        "n_hits": {k: len(v) for k, v in founder_hits.items()},
                        "founder_hits": founder_hits})
        print(f"{comp}: any_hit={any_hit} verified={len(verified) > 0}", flush=True)
    (SCRATCH / "sec_byname_results.json").write_text(json.dumps(results, indent=1))
    n = len(results)
    print(f"\nany founder-name FTS hit: {sum(r['any_name_hit'] for r in results)}/{n}; "
          f"verified filing: {sum(bool(r['verified']) for r in results)}/{n}")

if __name__ == "__main__":
    main()
