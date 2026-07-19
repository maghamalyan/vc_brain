# Cross-Source Linkage Feasibility — Measured (2026-07-19)

Empirical probe of four keyless public sources against `data/labels/founders.parquet`
(10,854 founders; 2,052 with `gh_confidence >= 0.5`). All rates below are measured on
random seeded samples, not estimated. Scripts + raw per-founder results (JSON) are preserved in
`docs/exploration/linkage_probe/` (full HTTP caches in the session scratchpad).
Politeness: ≤2 req/s per API, exponential backoff, disk cache,
identifying User-Agent. LinkedIn/X untouched.

---

## 1. Hacker News (Algolia search + Firebase user API) — n = 150

Sample: 150 random founders with `gh_confidence >= 0.5` (seed 42). Two probes per
founder: (a) HN account with username identical to `gh_login`, confirmed via the
profile `about` field (GitHub link / Twitter handle / company domain or name);
(b) Launch HN / Show HN stories whose title names the company, author checked against
`gh_login` and founder-name variants, then re-confirmed via the author's `about`.

| Metric | Rate |
|---|---|
| **Linked, confirmed (strong + medium)** | **28 / 150 = 18.7%** |
| — strong evidence | 24 / 150 = 16.0% |
| — medium evidence | 4 / 150 = 2.7% |
| gh_login exists as HN username but unconfirmed | 45 / 150 = 30.0% (collision-prone; many karma-1 accounts) |
| gh_login exists as HN username at all | 67 / 150 = 44.7% |
| **Company has a Launch/Show HN story (title match)** | **59 / 147 companies = 40.1%** |

Strong-evidence breakdown (24): 16 via username==gh_login + `about` confirmation,
8 via Launch/Show HN authored by the founder's exact `gh_login` (or name-variant +
`about` confirmation).

Linked examples (verifiable):
- Ruben Fiszel / Windmill — https://news.ycombinator.com/user?id=rubenfiszel (`about` links windmill.dev + names Windmill; karma 1,723)
- Sanchit Monga / RunAnywhere — author of "Launch HN: RunAnywhere (YC W26)" https://news.ycombinator.com/item?id=47326101 ; username == gh_login `sanchitmonga22`
- Alex Danilowicz / Magic Patterns — "Launch HN: Magic Patterns (YC W23)" https://news.ycombinator.com/item?id=43752176 ; author == gh_login
- Adish Jain / Mosaic — "Launch HN: Mosaic (YC W25)" https://news.ycombinator.com/item?id=45980760 ; `about` links mosaic.so
- Marc Klingen / Langfuse — https://news.ycombinator.com/user?id=marcklingen (`about` names Langfuse)

Evidence quality: the strong tier is genuinely strong — the `about` field routinely
contains the company domain or a github.com/<gh_login> link, i.e. self-declared
identity. The 45 unconfirmed same-username accounts are a real but noisy reservoir;
a comment-content check (does the account discuss the founder's domain?) would
upgrade a fraction of them. Note company-level linkage (40%) exceeds person-level:
launch posts are often authored by a co-founder not in our GH-resolved subset —
resolving at the company level then assigning authors raises yield.

Leakage risks: **high if careless.** `about` fields and karma are current-day
(post-outcome) — use only for identity resolution, never as features. Launch/Show HN
stories are post-recognition by construction (they name the YC batch) — they are
outcome-ontology labels ("launch" stage, Pillar 3), not features. The safe feature
stream is the founder's timestamped pre-cutoff comments/submissions (full history
retrievable via Algolia `author:` query with `created_at_i` filters).

Effort to productionize: **~1–2 days.** Both APIs are free, keyless, stable; the
probe code is already 90% of the resolver. Add: per-account comment-history pull,
`about`-evidence parser → match-probability record (Pillar 4 schema).

---

## 2. SEC EDGAR full-text search, Form D — n = 40 companies (2024–2025 batches)

Sample: 40 random companies from 2024/2025 batches (mix: S24 13, W24 7, W25 6,
Sp25 5, Su25 4, F25 3, F24 2). Probe: FTS `q="<company>" forms=D`; candidate filer
entities filtered for SPV noise; `primary_doc.xml` fetched and
`relatedPersonsList` officer names compared to our founder names (up to 4 filings
per company checked).

| Metric | Rate |
|---|---|
| Any Form D FTS candidate whose filer name matches company name | 13 / 40 = 32.5% |
| **End-to-end verified: officer names == our founders** | **2 / 40 = 5.0%** |
| Founder-name FTS (reverse direction), any hit | 7 / 40; verified 1 / 40 |

Verified examples:
- ZeroPath (S24) — ZeroPath Corp, CIK 2123552, Form D 2026-03-23; Directors Dean Valentine, Raphael Karger, Etienne Lunetta all match our founders. https://www.sec.gov/Archives/edgar/data/2123552/000212355226000001/primary_doc.xml
- SchemeFlow (S24) — SCHEMEFLOW LTD, CIK 1997814, Form D 2023-11-20; Directors Andrew Browning, James Griffith match. https://www.sec.gov/Archives/edgar/data/1997814/000199781423000002/primary_doc.xml

Evidence quality: when it hits, it is the **highest-grade evidence of any source**
(legal filing, structured officer names + roles + dated financing). But 11 of the 13
company-name candidates were name collisions with unrelated entities (e.g. "Parse,
Inc." 2011 = the Facebook-acquired Parse; "Chestnut Exploration" = an oil venture) —
generic brand names make company-name search useless without the officer-XML check.
The reverse (founder-name) search underperforms because Form D XML stores
first/last name in separate tags, so quoted-phrase queries miss.

Why the low rate is real, not a bug: YC-stage companies raise on SAFEs, which
frequently proceed without a Form D (or file it only around a priced round). Both
verified hits are from the oldest sampled batch (S24). Expect the rate to climb
substantially for 2021–2023 cohorts — worth one follow-up measurement.

Leakage risks: **low and manageable.** Filings carry exact `file_date`; a Form D is
a dated post-founding outcome event — exactly what Pillar 3's financing stage wants.
Never use as a pre-t feature; safe as a label.

Effort to productionize: **~2 days.** FTS + XML parsing works today; the blocker is
brand-name → legal-name resolution (Clerky/Stripe-Atlas-style names, "Labs", "Inc"
variants). Officer-name cross-check must be mandatory, not optional.

---

## 3. arXiv author search — n = 40 research-bio founders

Sample: 40 random founders whose `founder_bio` matches
PhD/research/professor/postdoc/university/thesis/lab (pool: 1,684 founders).
Probe: `au:"Full Name"` query; exact first+last author match; automatic
field-plausibility vs company domain; then a manual audit of every match.

| Metric | Rate |
|---|---|
| Exact-name author match | 19 / 40 = 47.5% |
| Auto field-plausible | 12 / 40 = 30.0% |
| **Manual audit: correct person (high confidence)** | **8 / 40 = 20%** (2 more uncertain) |
| Implied precision of name-only matching | ~8–10 / 19 ≈ 45–55% |

Confirmed examples (bio detail corroborates authorship):
- Emilio Andere / Wafer — "Natural Backdoor Datasets" (cs.CV, UChicago SAND Lab) http://arxiv.org/abs/2206.10673v1 ; bio says "uchicago sand lab"
- Carlos Georgescu / AfterQuery — "FinanceQA" http://arxiv.org/abs/2501.18062v1 and "VADER" http://arxiv.org/abs/2505.19395v1 — benchmark papers in his company's exact domain
- Lukas Wolf / Sonia — "WhisBERT" http://arxiv.org/abs/2312.02931v2 (cs.CL, ETH/MIT — bio: CS at ETH and MIT, NLP research)
- Mateo Perez / Cartpole — "Recursive Reinforcement Learning" http://arxiv.org/abs/2206.11430v1 (RL papers, PhD @ CU Boulder per bio; company literally named after the RL benchmark)
- Rami Seid / Lucid — "LoRA Diffusion" http://arxiv.org/abs/2412.02352v1 (bio: MLE)

Evidence quality: **name-only matching is a coin flip** — common names collide hard
(our "Sayan Mitra" is not the UIUC verification professor; our biotech "Tom Bishop"
is not the computational-imaging researcher). The auto plausibility heuristic had
both false positives and false negatives; affiliation strings, coauthor networks,
and bio cross-references are what actually discriminate. This is precisely the
Pillar 4 case for LLM-assisted match probabilities with cited evidence.

Leakage risks: **low.** Papers carry submission dates; pre-cutoff papers are clean
pre-t evidence of research depth/field. Two caveats: company-affiliated papers
(AfterQuery's benchmarks) are post-founding — date-filter them; and bios used for
match confirmation are post-outcome text — identity resolution only, never features.

Effort to productionize: **~2–3 days** (fetch + candidate generation is trivial; the
work is the disambiguation model and its human-audited calibration sample, per the
research program's instrument-validation rule). arXiv politeness (1 req/3 s) makes
bulk runs slow — cache aggressively.

---

## 4. Devpost hackathon profiles — n = 30

Sample: 30 random founders with `gh_confidence >= 0.5` (seed 7). Probe:
`devpost.com/<gh_login>` (pages are server-rendered — no JS or heavy scraping
needed; 404 for nonexistent users, real name in `<title>`, GitHub link on page).

| Metric | Rate |
|---|---|
| Profile exists at gh_login | 7 / 30 = 23.3% |
| **Linked** | **6 / 30 = 20.0%** (4 strong via on-page github.com/<gh_login> link; 2 medium via exact real-name match; 1 collision) |

Linked examples:
- Ishaan Sehgal / Omnara — https://devpost.com/ishaansehgal99 (links github.com/ishaansehgal99, name matches)
- Zac Wellmer / Tupelo — https://devpost.com/zacwellmer (GitHub link + name)
- Rohil Agarwal / The Context Company — https://devpost.com/rohilvagarwal (GitHub link + name)
- Dennis Zax / Naïve — https://devpost.com/DedS3t (GitHub link; display name "Dennis Z")
- Parth Chopra / Laguna — https://devpost.com/pchopra (exact name match, no GH link → medium)

Evidence quality: excellent when present — an explicit github.com/<gh_login> link on
the profile is self-declared identity, same grade as the HN `about` confirmation.
One username collision in 7 existing profiles shows name/GH-link confirmation is
mandatory. Yield could rise above 20% by also probing name-derived slugs.

Leakage risks: **low-moderate.** Hackathon submissions are dated (clean pre-t
"builder" signals — exactly the cold-start evidence the brief rewards); the profile
page itself (bio, portfolio) is current-day → resolution only.

Effort to productionize: **~0.5–1 day.** Single GET per candidate + regex; be a
polite scraper (their robots/ToS should be re-checked before bulk runs; at one
request per founder for 2k founders this is a trivial, cacheable crawl).

---

## Ranked recommendation

1. **Hacker News — integrate first.** Best measured person-level confirmed linkage
   (28/150 = 18.7%, mostly strong evidence), plus a 40% company-level Launch/Show HN
   hit rate that directly populates the launch stage of the outcome ontology, plus a
   timestamped pre-t text stream (comments/submissions) usable as features. Free,
   keyless, two stable APIs, resolver already prototyped.
2. **Devpost — second.** 20% linkage for near-zero effort, and the payload
   (dated hackathon participation) is a distinctive pre-founding builder signal that
   nothing else provides. Half a day of work.
3. **arXiv — third.** Coverage is real (~20% of research-bio founders confirmed,
   upper bound ~25–30% with better matching) but it *requires* the Pillar 4
   disambiguation model first — name-only precision is ~50%, unusable raw. Ship it
   together with the LLM-assisted matcher + audit sample.
4. **SEC Form D — last, and as labels not identity.** 5% verified on 2024–25 cohorts
   (SAFE-era artifact), but evidence grade is the highest available and it is
   perfectly dated. Wire it into the outcome panel (financing stage) for older
   cohorts (2021–2023 — re-measure there), and keep the mandatory officer-XML
   verification; company-name FTS alone is ~85% false positives on generic names.

Cross-cutting: every linked identity should be stored as a match-probability record
with cited evidence (the Pillar 4 schema); the strong-tier evidence collected here
(HN `about` domains, Devpost GH links, Form D officer matches) is exactly the
calibration data that model needs.
