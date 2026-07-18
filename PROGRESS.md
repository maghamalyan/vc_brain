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
