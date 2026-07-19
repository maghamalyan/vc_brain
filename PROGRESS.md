# Overnight Progress Journal

## 2026-07-19 02:04:27 +04

Created the P1 project scaffold: Docker and Make entry points, runtime and development
dependencies, package namespaces, and smoke-test coverage.

## 2026-07-19 02:05:21 +04

Verified `uv sync --frozen`, `uv run pytest -q` (1 passed), and
`uv run ruff check src tests` (all checks passed).

## 2026-07-19 02:08 — Claude verification: P1 ACCEPTED
pytest 1 passed, ruff clean, docker build OK (image vc-brain). Deps pre-added for parallel tasks: jinja2, plotly, pdfplumber. Committing checkpoint.

## 2026-07-19 02:25:19 +04 — P8 end-to-end vertical slice

Implemented the fixture-to-dashboard opportunity funnel within the P8-owned paths:
frozen memo contracts, evidence-constrained OpenRouter generation with deterministic
mock responses and input-hash caching, inbound PDF evidence extraction, deterministic
independent-axis screening, 12-candidate synthetic fixture corpus, configurable thesis,
and a polished offline static investor dashboard. Trust is visible per claim, including
source links, confidence, verification status, contradiction flags, and prominent known
gaps.

Verification: `uv run pytest -q` → 38 passed; `uv run ruff check src tests` → clean;
`uv run python -m vc_brain.dashboard.run --fixtures` → 17-file offline site built with
12 ranked candidates, local Plotly trajectory, three-axis screen, evidence timeline,
memo trust badges, contradiction treatment, and honest pre-launch gaps.

## 2026-07-19 02:36:35 +04 — P2 label pipeline

Implemented the complete resumable YC-founder label pipeline under
`src/vc_brain/labels/`: cached/normalized YC companies, polite single-threaded founder
page extraction, rotating GitHub search and profile scoring, capped/persisted SerpAPI
fallback, final label assembly, data-card generation, atomic parquet/JSON checkpoints,
and the stage CLI. Added fixture-backed parser, batch/date, identity normalization,
confidence-signal, assembly, and interrupt/resume tests.

Verification: `uv run pytest -q` → 39 passed; `uv run ruff check src tests` → clean.
Live pipeline: companies stage completed with 6,055 rows. The 2022+ founders stage was
started in descending batch order, checkpointed 230 companies / 457 unique founder
rows with 0 pending failures, and was stopped cleanly after checkpoint verification.
The raw page cache also contains 230 pages; rerunning the same command resumes without
refetching them. GitHub resolution was implemented but not started in this checkpoint.

## 2026-07-19 02:36 — Claude verification: P8 slice ACCEPTED (fixtures + live path)
38 tests + ruff green (independent run). Site rebuilt from scratch; index + candidate pages inspected in browser: ranked table, thesis filter, trajectory charts, per-claim trust badges, contradiction flag, gaps box all render. Live OpenRouter memo test EXPOSED A BUG (schema drift, no retry) — Claude fixed generate.py with retry-on-validation-error feedback loop; live memo then passed: 10 claims all evidence-backed, 11 explicit gaps, 5 required sections. Real-data wiring pending P4/P5.

## 2026-07-19 02:51:58 +04 — P3 event-stream extraction

Implemented the complete ClickHouse event ingestion pipeline under
`src/vc_brain/ingest/`: bounded/retrying two-slot HTTP client, exact-SQL parquet cache,
300-actor query batching with recursive 900k-row splitting, actor-specific 48-month
monthly/owned-repo/repo-creation queries, deterministic hash-sampled case-control
matching, read-only label snapshots, company-domain and temporal leakage guards,
atomic stage outputs, data card, and the baselines/positives/negatives/repos CLI.
Added mocked-HTTP unit, SQL contract, matching, zero-activity, and leakage tests.

Verification: `uv run pytest -q` → 53 passed; `uv run ruff check src tests` → clean.
The real baselines stage wrote 2,776 month/event rows covering 2011-02 through 2026-07.
Recent complete monthly totals were 98.3M–116.2M; June 2026 totaled 112,240,168
events (95,398,281 PushEvents). The conditional 20-actor smoke was not run: the latest
read-only label snapshot had 4,190 raw rows but no final labels, resolution parquet, or
resolution checkpoint with confident GitHub logins. No full cohort extraction was
launched.

## 2026-07-19 02:54 — Claude verification: P3 ingest ACCEPTED (code-level)
53 tests + ruff green independently. Leakage module audited: flags time>=cutoff, min-cutoff for dup actors. Baselines real (112M events May 2026). Cohort extraction gated pending label spot-check.

## 2026-07-19 03:27:36 +04 — P4 hazard model and honest evaluation

Implemented the complete leakage-safe P4 pipeline under `src/vc_brain/features/`,
`models/`, and `eval/`: 37-month matched person panels with exact hazard labels and
strict source cutoffs; globally normalized activity/traction levels, dynamics,
repository, behavior-shift, tenure, and consistency features with JSON/Markdown data
cards; deterministic standardized logistic and single-threaded LightGBM candidates;
2022/2023/2024 temporal tuning/validation/test isolation; validation-only model
selection; and honest held-out evaluation with calibration sensitivity, person-level
utility, lead time, shuffled-label gating, cumulative ablations, gain importances,
standalone figures, and frozen P8 trajectory/candidate outputs. Added the stage/all CLI
and a generated synthetic parquet corpus covering low-confidence exclusion,
zero-activity founders, and five matched controls per positive.

Verification: `uv run pytest -q` → 63 passed; `uv run ruff check src tests` → clean;
targeted `ruff format --check` and `git diff --check` → clean. Literal fixture CLI run
`python -m vc_brain.models.run --stage all` wrote both reports, 4 HTML figures, 888
test trajectory rows, and 4 candidates. The shuffled-label null passed at PR-AUC
0.0227 versus a 0.0180 test base rate; the logistic baseline remained selected on the
synthetic fixture. Joblib emitted 27 upstream NumPy 2.5 deprecation warnings in tests;
no project warning or failure was suppressed.

## 2026-07-19 03:29 — Claude verification: P4 code ACCEPTED (fixture-level)
63 tests green. Line review passed: panel months B-48..B-12, hazard label exactly [B-15,B-12], split tuning<=2022/valid=2023/test>=2024, refit pre-2024 only, null-run collapses on fixtures. Real-data run gated on P3 extraction.
Also: Claude diagnosed resolution bottleneck (serial HTTP, not rate limits; both tokens idle at 30/30) and patched gh_resolve (skip 2nd search qualifier when 1st hits; incremental profile fetch with early exit at score>=0.7). Pace 4/min -> ~17/min measured.

## 2026-07-19 04:04 — Claude verification: LABEL SPOT-CHECK PASSED (gate open)
25 random confident (>=0.5) linkages hand-verified against LIVE GitHub profiles: 23/25 clean person matches, 2/25 company-named accounts of the right founder (empty pre-t history; handled as no_gh_activity). Zero wrong-person links. Precision >=92% strict. Resolution continues (~45/min after Claude fixed shared reset_at bug + serial-latency patches; was 4/min).

## 2026-07-19 04:35 — Resolution crash fixed
Process died at 2050/10854 on ValueError from urlparse of a founder blog field containing the literal string [object Object]. Patched normalize_domain with try/except + regression test; restarted from checkpoint. Watchdog re-armed.

## 2026-07-19 05:38 +04 — Real dashboard wiring and held-out backtest

Added validated real-data dashboard assembly from P4 score exports, held-out eval
metrics, YC founder labels, and repository-creation evidence. Real candidates are
restricted to outbound test-cohort founders (batch start in 2024 or later), display
identity comes from labels, and evidence links point to the corresponding GitHub
repository or YC company page. Existing top-three memo JSON files are copied and linked
without invoking an LLM.

Added the offline `backtest.html` experience with aggregate median lead time and honest
full-cohort detection rate, strongest-detection example trajectories, eval-emitted
detection markers, actual YC batch markers, and explicit retrospective/out-of-time
labeling. `--fixtures` still builds the complete synthetic site; `--real` validates all
inputs first and currently exits with the expected missing model-output list.

Verification: `uv run pytest -q` → 67 passed (27 upstream joblib/NumPy deprecation
warnings); `uv run ruff check src tests` → clean; changed dashboard/test files pass
`ruff format --check`; `git diff --check` → clean. Repository-wide format checking still
reports 20 pre-existing drifts outside this task, including prohibited paths, which were
left untouched.

## 2026-07-19 05:50 — Claude verification: SECOND label spot-check PASSED
Seed 42, 25 rows spanning W22..P26 batches incl. training cohort: 25/25 correct person (2 company-named accounts of the right founder). Combined audits: >=48/50, zero wrong-person links. Also raised ClickHouse max_attempts 5->12 for quota resilience.

## 2026-07-19 06:11 — First REAL end-to-end result (partial cohort)
Eval null gate FIRED on run2 (global shuffled-label PR-AUC 0.098 vs 0.054 limit) — Claude diagnosed calendar-composition artifact; switched primary metric + null gate to within-month macro PR-AUC. Corrected results (704 test founders, partial labels): within-month PR-AUC 0.174 vs null 0.153 (base 0.094) — real but thin person-level lift; ROC 0.734; precision@50 0.32 (1.3x). Detection rate 71% but most detections censored at panel start (propensity, not rising intent) — presentation fix delegated to Codex. Score exports passed the gate; real site built; 3 real OpenRouter memos generated (evidence-grounded, gaps flagged). Final full-cohort run pending resolution completion.

## 2026-07-19 06:15 +04 — Backtest lead-time cohort correction

Replaced the misleading aggregate lead-time headline with two explicit cohorts. Of 503
detected founders, 307 (61%) were already over the same-month 99th control percentile
at the first panel month and are now labeled as boundary-censored with true lead of at
least 48 months. The 196 founders whose signal emerged later now supply the dynamic
headline: median 15 months before YC, IQR 14–16 months. Displayed examples determine
their first panel month from each founder's earliest trajectory row, and censored cards
show `≥48` rather than an exact 48-month lead.

Added the case-control panel prevalence (~25%) versus population-base-rate caveat and
the pointer to calibrated probabilities in the eval report. Fixture-backed regression
coverage exercises both cohorts and the rendered wording. Verification: `uv run pytest
-q` → 67 passed (27 upstream joblib/NumPy deprecation warnings); `uv run ruff check src
tests` → clean; touched-file `ruff format --check` and `git diff --check` → clean. The
real offline dashboard was rebuilt with `--real` after verification.

## 2026-07-19 08:15 — FINAL FULL-COHORT RUN VERIFIED (Claude)
All 10,854 founders resolved; 2,052 confident links. Final held-out results (690 test founders, 2,765 people): within-month PR-AUC 0.2418 vs null 0.1327 (base 0.0951) — gate passed with margin; LightGBM selection vindicated on test (logistic 0.1819); precision@50 0.50 (2x prevalence); detection 72%; 75% boundary-censored (propensity) vs 124 rising-signal founders at median 15mo lead (IQR 14-17). Tenure ablation: global 0.158->0.063 without tenure (74.5% of gain) — reported honestly. Two more leakage-guard catches during finale (case-insensitive founder exclusion; 408 batch bisection) — both fixed with tests. README updated to final numbers; real site + backtest rebuilt; memos generated for final top-3 (Wordware, Amby Health, Blaxel). 67 tests green.

## 2026-07-19 09:58 — Stream B: three lanes verified & committed (Claude)
Data sources: HN 18.7% person / 40% company launch labels (verified live). False positives: 76% clear FP dominated by tutorial-burst pattern (=> semantic annotation justified empirically); YC-only labels confirmed to hide real founders (precision floor). Missed founders: 16 portraits, 75% own-profile <=1; 7/16 zero countable events under resolved login => blind spot is mostly measurement (resolution/ownership/window), not invisibility; 12/16 show prestige-free network signal (cofounder-pair formation + upward embedding); 5 leakage-audited feature candidates. Cofounder-pairing lane still running.

## 2026-07-19 10:08 +04 — Stream A1: maturity-controlled metrics complete

Added held-out matched-group peak-score ranking with tie-expectation handling and
tenure-quintile within-month PR-AUC. Across 415 eligible groups, founder rank-1
probability is 0.3418 versus 0.1667 chance, top-half probability is 0.6595, and mean
normalized rank is 0.3648 (0 is best). Tenure-controlled PR-AUC is 0.2679 versus a
0.1469 cell base rate over 160 non-degenerate cells; quintile PR-AUC/base summaries
are Q1 0.2941/0.2131, Q2 0.0985/0.0620, Q3 0.0999/0.0569, Q4 0.1769/0.0803, and
Q5 0.3394/0.1328. The real backtest headline now reports the matched-control result.

## 2026-07-19 10:08 +04 — Stream A2: ownership and collaboration complete

Added one cached, quota-resilient ClickHouse query family that produces both
ownership and collaborator aggregates with strict event-month-before-cutoff checks.
Real aggregate row counts are ownership 35,489 positive / 133,949 negative and
collaboration 11,808 positive / 29,277 negative; all four artifacts have zero nulls
and zero cutoff violations. The five new ownership/collaboration features are finite
and non-null across all 276,316 panel rows. The new `all_plus_ownership_collab`
ablation selects LightGBM at test PR-AUC 0.1556, marginal -0.0026. The final null gate
passes: within-month PR-AUC 0.1332 versus a 0.1901 limit and 0.0951 base rate.

## 2026-07-19 10:08 +04 — Stream A4: crossing attribution complete

Wrote 1,557 top-three first-crossing contribution-delta rows for 519 detected test
founders to `data/scores/attributions.parquet`; each founder has exactly three rows,
with 372 boundary-censored crossings compared against the model baseline. Added the
complete human-readable feature dictionary grouped as cognitive (7), human (48),
contextual (17), and financial (none observed), explicitly as presentation taxonomy
only. The rebuilt real backtest renders ten founder examples with human-readable
`Flagged on:` lines. Verification: 70 tests passed; Ruff and `git diff --check` are
clean; protected memo and labels source paths were untouched. No commit was created.

## 2026-07-19 10:11 — Claude gate: A1+A2+A4 ACCEPTED
Matched-group rank in eval: 34.2% vs 16.7% chance (415 groups; reproduces Claude reference). Leakage zero on ownership_agg (169k rows) and collab_influx (41k). Attributions 3/founder for 519 detected. HONEST NEGATIVE: ownership_collab ablation adds no lift (0.1556 vs 0.1586) — likely inherits identity-resolution failures (see missed_founders.md); fix is resolution hardening, not feature removal. Null gate still passes (0.1332 vs 0.2344 real).
