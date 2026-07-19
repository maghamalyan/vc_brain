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

## 2026-07-19 10:41 +04 — Stream A3 part one: extraction and annotation code

Implemented the authored event-time text extractor for the five specified GitHub
event types, with strict pre-cutoff filtering, 1,500-character bodies, deterministic
global 40-item actor-quarter caps after distributed-query merge, SQL-hash batch
caching, and capacity/408 bisection. The real Cohort-D extraction retained 620
founders and 1,300 matched controls after applying the same >=20-item filter: 1,920
people, 24,410 person-quarters, and 375,514 text items. Candidate extraction rows
were 112,665 founders and 270,468 controls. There are zero cutoff violations; the
maximum bundle is 40 items and the minimum included-person total is 20.

Added the offline-safe OpenRouter annotation pipeline with temperature 0, strict
Pydantic/JSON schema including cited `domain_shift`, content/model/mode-hash caching,
bounded earlier-bundle context, fixture-backed `--mock`, and current-item citation
validation. No real annotation or semantic cache write was made. Estimated approval
gate: 24,410 person-quarters x ~1,500 tokens = 36,615,000 tokens.

Added `context_divergence_2q` from cached monthly/ownership aggregates only under the
`semantics` feature block. The rebuilt 276,316-row panel has 133,179 defined values in
[0, 1] and 143,137 contractually null values; model-matrix construction explicitly
neutral-imputes the documented undefined state. Added the presentation-only four
capital-family mapping, with financial capital explicitly empty. Verification:
`uv run pytest -q` -> 78 passed (27 upstream joblib/NumPy deprecation warnings);
`uv run ruff check src tests` and `git diff --check` -> clean. Protected eval/report
and dashboard paths were untouched; no commit was created.

## 2026-07-19 12:20 — deep-slice worktree MERGED into overnight/poc (Claude)

Merge 0f8e58b (30 files, pure additions, zero conflicts; no in-flight stream-A
files touched). Person-level semantic instrument consolidated under
`semantics/person_*` (v2 = production: anchored 0-100, structure-preserving
masking) + `semantics/studies/` provenance; label streams under `labels/`
(hn_persons, hn_harvest, control_screen*). Data + caches migrated additively
(data/pilot/, data/labels/hn_*.parquet, data/cache/{pilot*,labelnoise,gh_commits}).
Headline (see docs/exploration/corrected_metrics.md): matched-pairs AUC 0.776 vs
0.640 counts; corrected semantic p@10 10/10; noise curve 5.1/7.3/25.8%; HN
pre-cutoff Show HN P(founder)=77-82%. USER DECISION: A3a person-quarter
annotation HELD (pipeline stays, unrun); person-level instrument is the
submission's semantic layer — see docs/integration_deep_slice.md. Stream-A
follow-up owed: fold data/pilot/excluded_controls.parquet into the matched-group
eval at next gate (34.2% headline is label-noise-polluted).

## 2026-07-19 14:29 +04 — A3 checkpoint-only semantics pilot

Consumed the intentionally stopped 5,200-row annotation checkpoint without issuing
any LLM annotation work. Built the specified 14 ordinal semantic level/delta features,
preserved quarter-level missingness, filled only within calendar quarters, and excluded
all non-checkpoint people before model-matrix imputation. The pilot panel contains 420
people (150 founders, 270 controls): 243 development and 177 held-out test people.

Counts-only versus counts+semantics held-out within-month PR-AUC was 0.4199 versus
0.4312, a paired person-bootstrap change of +0.0113 with 95% CI [-0.0070, +0.0298]
over 200 resamples: no detectable lift. Both small-prefix shuffled-label null gates
failed (0.3409 and 0.3155 versus a 0.2770 limit), so the report marks all estimates
descriptive only. Four eligible held-out matched groups survived; rank-1 probability
was unchanged at 0.5000 (chance 0.3333), top-half probability unchanged at 0.7500,
and mean normalized rank unchanged at 0.3750.

Wrote `data/eval/semantics_pilot.{json,md}`, a blind mixed 40-bundle validation sample,
and quarterly demo trajectories for `andreybavt`, `28andrew`, and `akshaynarisetti`.
Verification: `uv run pytest -q` -> 88 passed (27 upstream joblib/NumPy warnings);
`uv run ruff check src tests` -> clean. `eval/report.py` and `dashboard/` were untouched;
no commit was created.

## 2026-07-19 14:32 — Claude gate: semantics PILOT reviewed (honest inconclusive)
On 420 people (150 founders): within-month PR-AUC 0.4199 -> 0.4312 with semantics, paired bootstrap +0.0113, 95% CI [-0.007, +0.030] — includes zero. Null gates FAIL on this prefix subsample (matched-group structure broken: only 4 groups survive; founder prevalence 36% vs 25% design) so estimates are descriptive only. Verdict: underpowered pilot, semantics NOT yet demonstrated nor refuted; full-cohort annotation queued post-demo (cache-resumable). Demo keeps qualitative annotation trajectories (andreybavt, 28andrew, akshaynarisetti) + instrument story. A5 frozen-clock rerouted to a Claude subagent after two Codex pre-session stalls (forensics: no rollout file ever created).

## 2026-07-19 — A5 frozen-clock top-of-funnel precision (vintage 2023-06-01)

New `scripts/frozen_clock.py` (+ `tests/test_frozen_clock.py`); no existing src/
module, eval/report.py, or site/ file touched. Froze the clock at 2023-06-01:
deterministically sampled 8,000 pool actors (seed 7, total_events >= 20, confident
founder logins excluded case-insensitively) from the 102,750-login hash pool at
t_cutoff 2023-06-01, extracted their monthly_agg + repo_creations live from
ClickHouse (cached, quota-aware, no quota sleeps needed), and added all 422
scoreable future founders (714 confident future-founder logins; 24 without cached
aggregates, 268 without any pre-cutoff activity — all counted, none silently
dropped; 76 scored founders have t_cutoff < vintage so their windows end early).
Ownership/collab/owned-repo blocks neutral-filled identically for ALL scored
actors. Features at month 2023-05-01 via build.py internals, scored with the
trained LightGBM, deterministic login tiebreak.

Results (n=8,422, base rate 5.01%): precision@100 = 0.060 (6/100, lift 1.20x),
precision@500 = 0.054 (27/500, lift 1.08x), median founder rank percentile 0.507.
Honest read: at a frozen calendar clock the detector is near chance overall —
BUT founders whose batch started within 12 months of the vintage (n=76, i.e. the
ones actually near the trained B-15..B-12 hazard window) rank at median
percentile 0.135 versus 0.565 for later batches. The detector concentrates
founders it was built to catch; it is not a years-ahead oracle. YC-only outcomes
make every precision number a floor. Wrote `data/eval/frozen_clock_2023.{json,md}`.
Verification: `uv run pytest -q` -> 91 passed; `uv run ruff check src tests` ->
clean. No commit created.

## 2026-07-19 — Pillar 2: second-hop actor graph + co-activity edges

New `scripts/graph/secondhop.py` (+ `tests/test_secondhop_graph.py`); no src/ or
site/ file touched. From the 1,920 Cohort-D people: 64,769 distinct touched
repos (27,160 cohort-owned); small-rooms filter dropped 11,978 non-owned repos
with >500 distinct non-bot actors; 52,569 extracted in full + 222 big owned
repos via a top-50-per-repo-month capped query. Repo-IN-batched (index-pruned)
ClickHouse queries only — 42 live queries total (13 count + 29 extract), zero
quota sleeps, ~2 min. Outputs in data/graph/: secondhop_monthly/ (6.07M rows,
1.20M distinct actors), coactivity_edges.parquet (678,405 edges, 1,875 cohort
members covered, neighbor side capped at top-50 per repo-month),
neighbors.parquet (467,548 pairs; 1,162 with a confident-YC-founder neighbor,
423 backtest-legal as-of-t recognized-founder edges — 2.3x per-capita
over-representation on positives vs controls). POST-HOC founder flags carry a
leakage warning in data/graph/README.md. Writeup with examples
(josephschorr↔jzelinskie/Authzed 5 yrs pre-batch; kanyesthaker↔shalins/Hyper
21 parity months; ggsonic control counter-example) + GNN-lane and
new_strong_tie_onset integration notes: docs/exploration/secondhop_graph.md.
Verification: `uv run pytest -q` -> 97 passed; `uv run ruff check` clean on new
files. No commit created.

## 2026-07-19 — Demo-scale temporal attention GNN (TGAT-flavored, Pillar-2 pilot)

New self-contained experiment in `scripts/gnn/` (dataset.py, model.py, run.py);
no src/ or site/ file touched; `uv add torch` (2.13.0) was the only new
dependency. Built a temporal bipartite actor–repo ego-graph from local parquet
only (items.parquet + repo_creations: 406,035 edges, 1,920 Cohort-D people),
sampled the exact main-panel months/labels (hazard_label, B-48..B-12) under the
train.py temporal_split rules with a hard edge<t leakage assert. Model: 61,213-
param ego-graph attention (event-type embedding + TGAT functional time encoding,
1 self-attention block + actor-query attention pooling); trained in ~13 s on MPS,
config chosen on validation PR-AUC only.

Honest test result (batch >= 2024; 25,892 rows, 972 pos, GBDT trajectories cover
all rows): GNN pooled PR-AUC 0.202 vs GBDT 0.379 (ROC 0.763 vs 0.879); within-
month mean PR-AUC 0.294 vs 0.433 (32 months); matched-group P(rank=1) 0.362 vs
0.447 on 141 groups (chance 0.258). The GNN loses everywhere, as predicted at
this scale — it stays an appendix per the research program. The demo artifact
landed: `data/gnn/attention/<login>.json` for 5 test founders +
`data/gnn/attention_demo.html` — aluzzardi's attention migrates from
docker/swarmkit to dagger/dagger + own dagger repos (own-repo attention share
0.00 -> 0.65) as founding approaches. Writeup with limitations (ego-graph only,
capped edge stream, attention != explanation) in
`docs/exploration/temporal_gnn.md`; metrics in `data/gnn/metrics.json`.
Verification: `uv run pytest -q` -> 97 passed; `uv run ruff check scripts/gnn` ->
clean. No commit created.

Blind review of A3 annotation instrument (40 bundles, independent rater vs GLM-5.2): scales solid — productization/commercial/seriousness all 100% within-1 (commercial 98% exact), founding intent 88%; categoricals weak — category 65%, audience 60%, collaboration 60% exact, driven by model bias toward developer_tool/developers/solo. domain_shift (48% exact) is confounded: the sample omits the earlier-context text the model saw.
Verdicts in docs/exploration/annotation_validation_sample.md '## Blind review results': KEEP productization, commercial, seriousness, intent; MERGE/REVISE category, audience, collaboration, domain_shift (regenerate sample with earlier context first). No commit created.
