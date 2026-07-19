# Label Noise at Scale: Screening Controls + Harvesting HN Launches (2026-07-19)

**Question.** The deep-slice pilot's ceiling is label noise: high-gestation "controls"
keep turning out to be real founders the YC-only label source never saw. Two jobs to
quantify and attack this: (1) screen every high-gestation annotated control (plus a
low-gestation contrast group) for current-day founder evidence — a label-noise estimate
with real n, replacing the portrait's 1/25 anecdote; (2) harvest dated "Launch HN"/
"Show HN" outcome events for all scored founders' companies — the first non-YC label
stream. Code: `src/vc_brain/labelnoise/` (`screen.py`, `harvest.py`, `net.py`).

**Leakage discipline.** Everything the screen collects (profile bios, blog pages, HN
authorship) is **current-day data, LABEL/IDENTITY USE ONLY** — it is marked
`data_basis=current_day_label_only` in the output and must never feed model features.
The harvested launch stories are dated **post-founding OUTCOME events** (all 106 land
5.1–36.0 months *after* t_cutoff) — labels, never features.

## Job 1 — Control screening (n=72)

**Method.** All 32 annotated pilot controls with `gestation_likelihood >= 50` plus a
seed-42 random 40 of the 113 with `gestation <= 15`. Per person: `gh api users/<login>`
(bio/company/blog/name), fetch of the blog URL, HN Algolia search for Launch/Show HN
stories authored by an HN account named `<login>`; deterministic rules for GONE (404)
and empty profiles; `anthropic/claude-sonnet-4.5` (temp 0, cached, 54 calls, <$1)
adjudicates every non-empty evidence bundle into FOUNDER_EVIDENCE / MEET_WORTHY /
NO_EVIDENCE. Output: `data/pilot/control_screen.parquet`, every row with a URL.

### Label-noise rates (the headline)

| group | FOUNDER_EVIDENCE | rate | exact 95% CI | +MEET_WORTHY | GONE |
|---|---|---|---|---|---|
| high-gestation (g≥50) | 8/31 | **25.8%** | 11.9%–44.6% | 9/31 = 29.0% | 1/32 |
| low-gestation (g≤15) | 2/39 | **5.1%** | 0.6%–17.3% | 2/39 = 5.1% | 1/40 |

Fisher exact: odds ratio **6.4, p = 0.018** (founder+meet: OR 7.6, p = 0.009). The
pilot's semantic instrument is doing exactly what it claims: when it says a "control"
looks like a product-gestation founder, it is right that something founder-shaped is
there **about 5× more often** than for the controls it clears. The portrait's 1/25
(4%) anecdote was an underestimate for the population that matters — among the
controls the annotator actually flags, roughly **a quarter are unlabeled founders**.

### The confirmed unlabeled founders (all with URLs)

| login | gest. | entity | evidence | URL |
|---|---|---|---|---|
| martonlederer | 95 | Wander (ex-ArConnect); co-founded Community Labs ($30M raised) | personal site | https://marton.lederer.hu |
| samyakkkk | 95 | LandingHero AI — pricing tiers $9–$99/mo | product page | https://www.landinghero.ai |
| crohr | 95 | RunsOn — commercial GitHub-Actions-runner SaaS; bio "Founder of @runs-on" | https://runs-on.com |
| senalbulumulle | 85 | FOIL OS — bio "Founder: FOÏL", company field FOIL OS | https://github.com/senalbulumulle |
| ahmedkhlief | 75 | Shells.Systems — security research/consulting brand | https://shells.systems |
| egil | 95 | Egil Hansen ehf — Icelandic LLC, independent .NET consultant | https://egilhansen.com |
| miladsoft | 95 | "Senior Blockchain Founder & CEO", consulting services | https://miladraeisi.com |
| rin1024 | 65 | non-classic inc. — media-art studio | http://yukianai.art/ |
| tipstrade | 15 | TipsTrade Ltd. — registered UK Ltd, commercial site | https://www.tipstrade.net |
| tkokada | 15 | Cocado Inc. — listed as Representative (founder/CEO) | https://cocado.jp |

**Honest split — venture-shaped vs founded-anything.** Hand-grading the 8 high-gestation
hits: 4 are venture-shaped startups (martonlederer, samyakkkk, crohr, senalbulumulle ≈
**12.9%** of screenable high-gestation controls) and 4 are solo consultancies / studios
(egil, miladsoft, ahmedkhlief, rin1024). Both species poison a founder/non-founder
label, but only the first is the direct sourcing target; quote 13% (venture-strict) to
26% (any founded entity) depending on the claim being made. Both low-gestation hits are
small non-venture entities (UK Ltd, small Japanese company) — consistent with the
instrument's read that their GitHub activity showed no product gestation.

### What this does to reported precision floors

- **Top-region composition** (265 controls): 32 at g≥50, 41 at 15<g<50, 113 at g≤15,
  79 with no text (no annotation). Applying measured rates (25.8% / interpolated
  ~10–15% / 5.1% / assume ≤5% for no-text) ⇒ expected **~17–22 unlabeled founders
  among 265 top-region "controls" (~6–8%)**. Region label-precision 149/414 = 36.0%
  is really ≈ **40–41%** — a ~4–5pp absolute understatement, concentrated exactly
  where metrics are read.
- **Semantic re-rank precision@10 = 0.70** (pilot Finding 3): the 3 top-10 "misses"
  are high-gestation controls by construction, so ~0.26 × 3 ≈ 0.8 of them are expected
  unlabeled founders ⇒ true precision@10 ≈ **0.78**; with meet-worthy credit the
  utility number is higher still. The better the ranker gets, the more its measured
  precision is capped by label noise — improvements past ~0.75@10 are unmeasurable
  against YC-only labels.
- **AUC/PR-AUC vs YC labels** are similarly compressed: every high-gestation control
  reclassified as positive moves both numerator and denominator in the model's favor.
  This is the quantified version of the pilot's claim that "the instrument's ceiling
  is set by label noise, not by the instrument."

## Job 2 — Launch harvest (first non-YC-shaped label stream)

**Method.** For each of the 576 distinct companies of the 690 scored founders
(`gh_login` in `data/scores/trajectories.parquet`), HN Algolia title-restricted story
search (cached, ≤2 req/s). Kept only stories whose title starts with Launch HN/Show HN
AND names the company (word-boundary match) AND is verified conservatively: author
matches a founder `gh_login`/name-variant, or the title is a canonical
"Launch HN: X (YC …)". Unverified naming collisions are dropped.
Output: `data/labels/hn_launches.parquet`.

### Yield

- **106 stories across 87/576 companies (15.1% coverage)**; 64 companies with a
  Launch HN, 42 Show HN stories; date range 2024-02-02 → 2026-07-14.
- Match grades: 50 strong_author (author == founder gh_login), 35 launch_yc_title,
  17 author_name_variant, 4 author_substring. Spot-audit of all 21 variant/substring
  matches: every one is a genuine founder post (e.g. `rhimshah` → Rhim Shah,
  "Launch HN: Arva AI (YC S24)"); each parquet row carries its
  news.ycombinator.com item URL.
- **Timing: every story is post-cutoff** — min +5.1, median +14.4, p75 +18.0,
  max +36.0 months after the company's t_cutoff. Zero pre-cutoff stories, so the
  outcome/feature boundary holds by measurement, not just by intent.
- Free byproduct: **54 distinct founder HN accounts** author-verified — HN↔GitHub
  identity links (cf. the linkage study's 18.7% person-level estimate) usable for
  future HN-side features *and* label verification.

### Why this matters (the outcome ontology)

These are dated events of the form "company X publicly launched at time t" — exactly
the multi-state outcome events the research program needs beyond the binary
became-YC-founder label. Immediate uses: (a) an independent label stream that would
have caught LandingHero-style non-YC founders (Show HN posts exist for scored people's
companies that never touch YC); (b) time-to-launch as a graded outcome for the
frozen-clock eval; (c) launch-date anchoring to replace the batch-date proxy for the
15% of companies covered.

## The concrete case for non-YC labels

1. **Noise is concentrated where metrics are read.** 26% (CI 12–45%) of high-gestation
   top-region controls are founded-something people, vs 5% baseline. Precision
   floors at the head of the ranking are understated by ~4–8pp (label-strict) and the
   measurable ceiling for any semantic re-ranker is ~0.75–0.8@10 — better models will
   look no better against YC-only labels.
2. **The screen itself is a scalable labeler.** At ~$0.01–0.02/person (LLM) plus
   cached API calls, screening all 2,075 controls' high-gestation subset is
   tens of dollars; the 10 confirmed founders here (each with a URL) can be dropped
   from the negative pool *today* — evaluation-time hygiene with zero leakage.
3. **HN launches are cheap, dated, and verify cleanly.** One afternoon of keyless
   API calls produced 106 conservative outcome events covering 15% of scored
   companies, plus 54 identity links. The same harvest run over *controls'* Show HN
   posts (not just known companies) is the natural next label-broadening step,
   followed by SEC Form D officer names (era-limited per the linkage study).

## Caveats

- Current-day founder evidence ≠ founder at the evaluation horizon: someone may have
  founded their entity *after* the pilot's outcome window. The rates here bound label
  noise for "ever becomes a founder"; horizon-matched noise is somewhat lower.
  (Cuts the other way too: GONE accounts and founders with no public web presence
  make these floors, not ceilings.)
- The adjudicator is the same model family as the pilot annotator; correlated
  world-knowledge errors are possible, but the screen's inputs (bio/company/blog/HN)
  are independent of the annotation's inputs (pre-cutoff event text), so agreement is
  evidence, not circularity.
- The mid-band (15 < g < 50, 41 controls) was not screened; the extrapolation
  interpolates its rate. Screening it costs ~30 more LLM calls.
- Consultancy/studio entities inflate the strict "founder" rate; the venture-strict
  number (12.9%) is the conservative quote for sourcing claims.
- Launch-harvest coverage (15.1%) is a floor: Algolia title search misses launches
  that renamed the company, use a product name, or predate the company string in
  `founders.parquet`.

*All network calls cached under `data/cache/labelnoise/`; screening output
`data/pilot/control_screen.parquet` (72 rows), harvest output
`data/labels/hn_launches.parquet` (106 rows). 2026-07-19.*
