"""Task 3: arXiv author-search linkage for 40 founders with research-flavored bios."""
import json, re, time, random
from pathlib import Path
import httpx
import polars as pl
import xml.etree.ElementTree as ET

ROOT = Path("/Users/mishaaghamalyan/Development/personal/competitions/vc_brain")
SCRATCH = Path("/private/tmp/claude-501/-Users-mishaaghamalyan-Development-personal-competitions-vc-brain/4f97507a-6fcd-448b-89eb-358a63f57ae1/scratchpad")
CACHE = SCRATCH / "cache" / "arxiv"
CACHE.mkdir(parents=True, exist_ok=True)

UA = "vc-brain-research/0.1 (misha.aghamalyan@gmail.com)"
client = httpx.Client(headers={"User-Agent": UA}, timeout=30, follow_redirects=True)
NS = {"a": "http://www.w3.org/2005/Atom", "ar": "http://arxiv.org/schemas/atom"}
LAST = [0.0]

def get(url, key):
    fp = CACHE / (key + ".xml")
    if fp.exists():
        return fp.read_text()
    for attempt in range(4):
        dt = time.time() - LAST[0]
        if dt < 3.1:
            time.sleep(3.1 - dt)
        LAST[0] = time.time()
        try:
            r = client.get(url)
            if r.status_code == 200:
                fp.write_text(r.text)
                return r.text
            time.sleep(3 * (2 ** attempt))
        except httpx.HTTPError:
            time.sleep(3 * (2 ** attempt))
    return None

def norm(s):
    return re.sub(r"[^a-z ]", "", (s or "").lower()).strip()

def exact_author(name, authors):
    nf = norm(name).split()
    if not nf:
        return False
    for a in authors:
        na = norm(a).split()
        if not na:
            continue
        if na == nf:
            return True
        # first + last equality (middle names/initials on arXiv side ok)
        if len(na) >= 2 and na[0] == nf[0] and na[-1] == nf[-1]:
            return True
    return False

SECTOR_KW = {
    "cs": ["ai", "software", "developer", "agent", "llm", "data", "platform", "api", "ml",
            "machine learning", "automation", "code", "infrastructure", "security", "search",
            "computer", "robot", "vision", "voice", "model"],
    "q-bio": ["bio", "drug", "protein", "health", "medical", "clinical", "gene"],
    "physics": ["quantum", "energy", "materials", "semiconductor", "fusion", "satellite", "space"],
    "econ_qfin": ["finance", "fintech", "trading", "insurance", "market", "payment"],
    "eess": ["hardware", "chip", "signal", "wireless", "sensor"],
}

def field_plausible(categories, company_text):
    ct = (company_text or "").lower()
    fams = set()
    for c in categories:
        fam = c.split(".")[0].lower()
        fams.add(fam)
    for fam, kws in [("cs", SECTOR_KW["cs"]), ("q-bio", SECTOR_KW["q-bio"]),
                     ("physics", SECTOR_KW["physics"]), ("eess", SECTOR_KW["eess"])]:
        if fam in fams and any(k in ct for k in kws):
            return True
    if ("econ" in fams or "q-fin" in fams) and any(k in ct for k in SECTOR_KW["econ_qfin"]):
        return True
    if "stat" in fams and any(k in ct for k in SECTOR_KW["cs"]):
        return True
    return False

def main():
    df = pl.read_parquet(ROOT / "data/labels/founders.parquet")
    pat = r"(?i)(phd|ph\.d|research|professor|postdoc|university|thesis|lab\b)"
    pool = df.filter(pl.col("founder_bio").str.contains(pat)).unique(subset=["founder_name", "company"])
    print("research-bio pool:", pool.height)
    random.seed(42)
    idx = random.sample(range(pool.height), 40)
    sample = pool[idx]
    results = []
    for row in sample.iter_rows(named=True):
        name = row["founder_name"]
        q = httpx.QueryParams({"search_query": f'au:"{name}"', "max_results": "20"})
        xml_text = get(f"http://export.arxiv.org/api/query?{q}",
                       re.sub(r"[^a-z0-9]", "_", name.lower()))
        rec = {"founder_name": name, "company": row["company"], "batch": row["batch"],
               "bio_snip": (row["founder_bio"] or "")[:160],
               "n_results": 0, "exact_name_papers": [], "any_exact": False,
               "plausible": False}
        if xml_text:
            try:
                root = ET.fromstring(xml_text)
            except ET.ParseError:
                root = None
            if root is not None:
                entries = root.findall("a:entry", NS)
                rec["n_results"] = len(entries)
                comp_text = " ".join(filter(None, [row.get("one_liner"), row.get("founder_bio"), row.get("company")]))
                for e in entries:
                    authors = [a.findtext("a:name", "", NS) for a in e.findall("a:author", NS)]
                    if not exact_author(name, authors):
                        continue
                    cats = [c.get("term") for c in e.findall("a:category", NS)]
                    paper = {"title": re.sub(r"\s+", " ", e.findtext("a:title", "", NS)).strip(),
                             "published": e.findtext("a:published", "", NS)[:10],
                             "categories": cats,
                             "url": e.findtext("a:id", "", NS),
                             "authors": authors,
                             "field_plausible": field_plausible(cats, comp_text)}
                    rec["exact_name_papers"].append(paper)
                rec["any_exact"] = bool(rec["exact_name_papers"])
                rec["plausible"] = any(p["field_plausible"] for p in rec["exact_name_papers"])
        results.append(rec)
        print(f"{name}: results={rec['n_results']} exact={len(rec['exact_name_papers'])} plausible={rec['plausible']}", flush=True)
    (SCRATCH / "arxiv_results.json").write_text(json.dumps(results, indent=1))
    n = len(results)
    print(f"\nexact-name match: {sum(r['any_exact'] for r in results)}/{n}; plausible-field: {sum(r['plausible'] for r in results)}/{n}")

if __name__ == "__main__":
    main()
