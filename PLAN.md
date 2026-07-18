# VC Brain — Overnight Build Plan (Sourcing POC)

**Objective:** POC for the sourcing layer — given a person-level public event stream up to
time *t*, predict transition into founding intent/gestation. Demo centerpiece: a
retrospective backtest showing "we found them first" — detector fires months before the
founder's first public recognition (YC batch / Crunchbase / press).

**Rubric anchors (from the challenge brief + chat analysis):**
- Data Architecture = 30%, and generic ingestion scores poorly unless it addresses the
  **cold-start / pre-track-record case**. That is this POC's entire thesis.
- Intelligent Analysis & Trust = 25%: every claim traces to evidence, gaps flagged
  ("not observed"), no confabulation.
- P0 below re-verifies these against the actual brief PDF before anything else.

**Operating mode:** Claude = judgment + verification agent (specs tasks, reviews diffs,
runs acceptance checks, audits for leakage). Codex = builder for well-scoped tedious work.
User (Misha) is asleep; do not block on user input — take the documented fallback instead.

---

## Priorities (ordered; each has a verification gate before moving on)

### P0 — Rubric ground truth (Claude, ~30 min)
Read `research/1784381921507-02-Maschmeyer-Group-The-VC-Brain.docx.pdf` end-to-end.
Extract scoring rubric, FAQ constraints, submission format into `docs/rubric.md`.
Adjust this plan if anything conflicts. Skim the two research-report PDFs for the
recommendations sections.

### P1 — Scaffold + working agreement (~1h)
- Dockerfile (python 3.13 + uv; duckdb, polars, pyarrow, lightgbm, scikit-learn,
  httpx, jupyter) + `make` targets: `build / shell / test / pipeline`.
- Repo layout: `src/vc_brain/{ingest,labels,features,models,eval}`, `data/` gitignored,
  `docs/`, `notebooks/`.
- `PROGRESS.md` journal: timestamped entries for every task handed to Codex, every
  verification result, every decision. This is the morning report.
- Smoke test: container builds, `uv run pytest` passes on a trivial test.

### P2 — Label pipeline: YC founders → GitHub handles (HIGHEST VALUE)
The bottleneck is labels, not features. Codex builds; Claude verifies.
- Scrape YC company directory (public Algolia search API used by ycombinator.com;
  polite: cached to disk, single-threaded, back-off). Last ~4 years of batches.
- Extract: founders, batch date, company, socials/GitHub links.
- Resolve GitHub handles: direct profile links first; else name+company search via
  GitHub API with a match-confidence score. Keep only high-confidence links.
- Founding date estimate: batch date − 6–12 months; refine via first commit to the
  company's GitHub org where resolvable.
- **Deliverable:** `data/labels/founders.parquet` + linkage-rate stats in data card.
- **Gate (Claude):** spot-check 25 random linkages against live GitHub/YC pages;
  ≥90% correct or bounce back. Record precision estimate in PROGRESS.md.

### P3 — Event-stream extraction (features ≤ t, religiously)
Data path decided at go-time (see Decisions). Codex builds; Claude audits.
- Pull full pre-t GitHub event histories for all positives.
- Matched negatives from the same source: similar account age, activity volume,
  primary language; no founding evidence in window. Record case-control ratio for
  later probability correction.
- **Deliverable:** `data/events/` (parquet) + data card (coverage, date ranges, counts).
- **Gate (Claude):** leakage audit — zero events > t in any feature row; no
  company-org-membership signals; negative pool doesn't accidentally contain founders
  (check against label set + Form D/YC names).

### P4 — Tier-1 model: discrete-time hazard GBDT
- Person-month panel; target = "enters gestation within next k months" (k=6 default).
- Features: event-rate deltas across windows, burst scores (Kleinberg-style or simple
  z-score bursts), repo-creation bursts, org creation, new-collaborator influx,
  night/weekend coding shift, language/topic drift, README product-language score
  (LLM if key available, else keyword/heuristic classifier).
- Models: LightGBM + logistic-regression baseline. GBDT must beat logistic to be kept.
- Split: **strict out-of-time** — train on cohorts founding ≤2023, test on 2024–25.
- Metrics: PR-AUC, precision@k (k=50/100), recall on founder cohort, calibration
  (Brier + reliability curve, after case-control correction), median lead time.
- **Gate (Claude):** line-by-line review of split/feature code for leakage; require a
  shuffled-label null run (should collapse to base rate); top-feature sanity review.

### P5 — "We found them first" backtest demo
- For 5–10 held-out test founders: score trajectory timeline vs. actual founding date
  and first public recognition. Median lead-time headline number.
- Deliverable: notebook → exported figures + a small static HTML report.
- This is the demo. It outranks any additional modeling.

### P6 — Trust layer (thin, honest)
- Every surfaced signal links to raw event IDs/URLs (traceability).
- Explicit "not observed" fields; per-person confidence band; base-rate honesty
  (corrected probabilities, not raw case-control scores).

### P7 — Stretch (only if P2–P5 are green)
- Tier-2: temporal user-repo graph → personalized-PageRank / centrality trajectories
  as features; measure lift over Tier-1.
- HN username linkage as a second stream; SEC Form D as confirmation labels.
- TGN/temporal-GNN writeup as "areas of research" appendix (no training).

### Continuous
- README/writeup grows with each stage (judges read it).
- Checkpoint commit on branch `overnight/poc` after each verified gate (if approved).
- Never trust "done" claims from Codex: run the code, sample the outputs, check
  row counts and distributions before accepting.

---

## Decisions & fallbacks (updated after user go-ahead + brief read, 2026-07-19 ~02:00)
| Decision | Chosen | Fallback (no user input needed) |
|---|---|---|
| GH Archive access | ClickHouse public playground (`play.clickhouse.com`, github_events) if coverage checks out | raw gharchive.org HTTP downloads of targeted date ranges; disk cap **300GB** (user-approved) |
| LLM access | **OpenRouter** (`OPENROUTER_KEY` in `.env`) — any model | Heuristic/sklearn fallbacks for classification tasks |
| Search/enrichment | **SerpAPI** (`SERPAPI_KEY` in `.env`) for handle resolution; Browserbase available if scraping needs a real browser | GitHub API search only |
| Founder validation labels | YC + SEC EDGAR Form D (keyless) + Kaggle Crunchbase snapshots (auth VERIFIED: token at `~/.kaggle/access_token`, use `KAGGLE_API_TOKEN=$(cat ~/.kaggle/access_token)`) | — |
| GitHub API auth | `gh auth token` — personal acct `maghamalyan` (user switched) | Second account if rate-limited |
| Checkpoint commits | Branch `overnight/poc`, commit after each verified gate, **no pushes** (approved) | — |

## User priorities (verbatim intent, 2026-07-19)
1. Fully verified, fully working prototype **over** stretch goals.
2. Verify from different angles.
3. Demoable example scenarios that look good on a pitch deck.
4. Scientific rigor is second-order (good pipeline).
5. Stretch: Neo4j graph DB ingesting heterogeneous signals.
6. Second objective: scoring product ideas / pitch decks.
No hard deadline; user wakes ~10:00. Codex ($200 plan) = tedious work; Claude = judgment.

## Amendment after reading the full brief (see docs/rubric.md)
Investment Utility & Execution is ALSO 30% and UX is 15% — a detector + metrics alone
caps out near 55%. Added **P8: thin end-to-end vertical slice** (required for a winning
submission, and it satisfies user priority #3 and objective #6):
- Inbound track: deck/company-name → screen → memo (this IS the user's "objective 2" —
  it's core scope, not stretch).
- Outbound track: our detector's discoveries, scored the same way, same funnel.
- 3-axis screening (Founder/Market/Idea-vs-Market, each with trend, never averaged).
- Memo generator: 5 required sections, per-claim Trust Score
  `{claim, evidence_refs[], confidence, verification_status, contradictions[]}`,
  explicit "not disclosed" gaps.
- Minimal Thesis Engine: configurable JSON (sectors/stage/geo/check size/risk) filtering
  the ranked list.
- Investor dashboard: ranked founders + momentum trend + evidence timeline + memo view.
Sequencing: P8 skeleton can be built by Codex against fixture data IN PARALLEL with
P3/P4 (disjoint files), then wired to real detector output after P5.

## Hard rules
- System-wide installs → Docker only. Host gets project-local (uv) tools at most.
- Polite scraping: cache everything, single-threaded, exponential back-off, no ToS
  violations (no LinkedIn, no X).
- Every feature computed strictly from events ≤ t. Post-t leakage is the #1 failure mode.
- No spend beyond documented caps. No credentials in code or commits; `.env` only.
