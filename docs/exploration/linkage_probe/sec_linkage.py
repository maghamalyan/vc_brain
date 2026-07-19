"""Task 2: SEC EDGAR full-text search — Form D hit rate for 2024/2025-batch YC companies,
plus officer-name match against our founder names."""
import json, re, time, random
from pathlib import Path
import httpx
import polars as pl
import xml.etree.ElementTree as ET

ROOT = Path("/Users/mishaaghamalyan/Development/personal/competitions/vc_brain")
SCRATCH = Path("/private/tmp/claude-501/-Users-mishaaghamalyan-Development-personal-competitions-vc-brain/4f97507a-6fcd-448b-89eb-358a63f57ae1/scratchpad")
CACHE = SCRATCH / "cache" / "sec"
CACHE.mkdir(parents=True, exist_ok=True)

UA = "VC Brain research (misha.aghamalyan@gmail.com)"
client = httpx.Client(headers={"User-Agent": UA}, timeout=25, follow_redirects=True)
LAST = [0.0]

def _throttle():
    dt = time.time() - LAST[0]
    if dt < 0.55:
        time.sleep(0.55 - dt)
    LAST[0] = time.time()

def get(url, cache_key, is_json=True):
    fp = CACHE / (cache_key + (".json" if is_json else ".xml"))
    if fp.exists():
        t = fp.read_text()
        return json.loads(t) if is_json else t
    for attempt in range(5):
        _throttle()
        try:
            r = client.get(url)
            if r.status_code == 200:
                if is_json:
                    d = r.json()
                    fp.write_text(json.dumps(d))
                    return d
                fp.write_text(r.text)
                return r.text
            if r.status_code in (403, 429, 500, 502, 503):
                time.sleep(2 ** attempt)
                continue
            return None
        except httpx.HTTPError:
            time.sleep(2 ** attempt)
    return None

def norm(s):
    return re.sub(r"[^a-z0-9 ]", " ", (s or "").lower()).strip()

SPV_PAT = re.compile(r"a series of|fund|,?\s*l\.?p\b|spv|capital partners|ventures? fund|angellist|assure ", re.I)

def entity_matches_company(display_name, company):
    dn = display_name.split("(CIK")[0].strip()
    if SPV_PAT.search(dn):
        return False
    ndn, nc = norm(dn), norm(company)
    if not nc:
        return False
    # company name should start the entity name (allow "Inc", "Corp", "Labs" etc. suffixes)
    return ndn.startswith(nc) or ndn.replace(" ", "").startswith(nc.replace(" ", ""))

def fetch_form_d_persons(hit):
    src = hit["_source"]
    accession, fname = hit["_id"].split(":")
    ciks = src.get("cik") or []
    m = re.search(r"CIK (\d+)", (src.get("display_names") or [""])[0])
    cik = int(m.group(1)) if m else (int(ciks[0]) if ciks else None)
    if cik is None:
        return []
    acc = accession.replace("-", "")
    url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc}/{fname}"
    xml_text = get(url, f"doc_{accession}", is_json=False)
    if not xml_text:
        return []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    persons = []
    for rp in root.iter():
        if rp.tag.endswith("relatedPersonInfo"):
            first = last = ""
            roles = []
            for el in rp.iter():
                if el.tag.endswith("firstName"):
                    first = el.text or ""
                elif el.tag.endswith("lastName"):
                    last = el.text or ""
                elif el.tag.endswith("relationship"):
                    roles.append(el.text or "")
            persons.append({"name": f"{first} {last}".strip(), "roles": roles, "url": url})
    return persons

def name_match(founder_name, person_name):
    f, p = norm(founder_name).split(), norm(person_name).split()
    if not f or not p:
        return False
    return f[0] == p[0] and f[-1] == p[-1]

def main():
    df = pl.read_parquet(ROOT / "data/labels/founders.parquet")
    df = df.with_columns(pl.col("batch").str.extract(r"(\d{4})").cast(pl.Int32).alias("byear"))
    comps = (df.filter(pl.col("byear").is_in([2024, 2025]))
               .group_by(["company", "slug", "batch"])
               .agg(pl.col("founder_name").alias("founders"))
             ).sort("slug")
    random.seed(42)
    idx = random.sample(range(comps.height), 40)
    sample = comps[idx]
    results = []
    for row in sample.iter_rows(named=True):
        comp = row["company"]
        rec = {"company": comp, "slug": row["slug"], "batch": row["batch"],
               "founders": row["founders"], "fts_total": 0, "entity_hits": [],
               "form_d_found": False, "officer_match": False, "officers": [],
               "matched_officers": [], "evidence_urls": []}
        q = httpx.QueryParams({"q": f'"{comp}"', "forms": "D"})
        d = get(f"https://efts.sec.gov/LATEST/search-index?{q}",
                "fts_" + re.sub(r"[^a-z0-9]", "_", comp.lower())[:80])
        hits = (d or {}).get("hits", {}).get("hits", [])
        rec["fts_total"] = (d or {}).get("hits", {}).get("total", {}).get("value", 0)
        for h in hits:
            dn = (h["_source"].get("display_names") or [""])[0]
            if entity_matches_company(dn, comp):
                rec["entity_hits"].append({"display_name": dn, "id": h["_id"],
                                           "file_date": h["_source"].get("file_date")})
        if rec["entity_hits"]:
            rec["form_d_found"] = True
            # check officers on up to 4 matching filings (first hit may be a name collision)
            for best in rec["entity_hits"][:4]:
                hit_obj = next(h for h in hits if h["_id"] == best["id"])
                persons = fetch_form_d_persons(hit_obj)
                rec["officers"].append({"filing": best["id"], "persons": persons})
                for f in row["founders"]:
                    for p in persons:
                        if name_match(f, p["name"]):
                            rec["officer_match"] = True
                            rec["matched_officers"].append({"founder": f, "officer": p["name"], "roles": p["roles"]})
                            rec["evidence_urls"].append(p["url"])
                if rec["officer_match"]:
                    break
        results.append(rec)
        print(f"{comp}: fts_total={rec['fts_total']} formD={rec['form_d_found']} officer_match={rec['officer_match']}", flush=True)
    (SCRATCH / "sec_results.json").write_text(json.dumps(results, indent=1))
    n = len(results)
    fd = sum(r["form_d_found"] for r in results)
    om = sum(r["officer_match"] for r in results)
    print(f"\nForm D found: {fd}/{n}; officer name match: {om}/{fd if fd else 1} (of found)")

if __name__ == "__main__":
    main()
