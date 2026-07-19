# Demo-scale temporal attention GNN (TGAT-flavored) — Pillar 2 pilot

**Status: exploratory, self-contained.** Nothing downstream depends on this. Code
lives in `scripts/gnn/` only; no `src/` module or `site/` file was touched. One new
dependency was added: `torch` (2.13.0, pre-approved). Run with
`uv run python scripts/gnn/run.py`.

## Question

Does a small temporal attention network over a person's raw timestamped
edge stream (actor–repo bipartite ego-graph) beat — or even approach — the
production GBDT that consumes hand-built monthly aggregate features, at the
same task, on the same people, under the same temporal split? And regardless of
the score: does the attention layer produce a *legible* account of which repos
the model looks at as founding approaches?

## Dataset construction

All local parquet; no ClickHouse.

- **People**: `data/semantics/cohort_d.parquet` — 1,920 Cohort-D people
  (620 positives, 1,300 controls), joined to `data/labels/founders.parquet`
  (gh_confidence ≥ 0.5, lowercased login, first record per login by
  batch date — same rule as `features/build.py`). Controls inherit the matched
  positive's `batch_start_date` via `matched_positive_login`; match group id is
  `matched_login|batch_start` as in the main panel.
- **Edges**: (actor, repo, t, event_type) from
  `data/semantics/text/items.parquet` (PullRequestEvent, IssueCommentEvent,
  IssuesEvent, PullRequestReviewCommentEvent; note this source is capped at the
  40 most recent items per person-quarter upstream) plus
  `data/events/repo_creations/*.parquet` (CreateEvent). Total **406,035 edges**;
  all 1,920 people have ≥1 edge. A hard assert verifies every edge timestamp is
  strictly before the person's `t_cutoff`.
- **Samples**: the main panel's months exactly — `batch_start − 48 … − 12`
  (37 per person). Label = `hazard_label` from `features/build.py`
  (1 iff month ∈ [B−15, B−12], positives only; controls always 0) — the
  "founding gestation within ~6 months" target (gestation = B−9). A sample at
  month *m* sees only edges with t < *m* (leakage rule enforced by
  construction: prefix index into the time-sorted edge array).
  67,805 samples; 3,235 person-months skipped for zero prior history
  (counted, not silently dropped).
- **Split** (`train.py temporal_split` semantics): batch ≤ 2022-12-31 →
  tuning_train (32,801 rows, 1,160 pos), ≤ 2023-12-31 → validation
  (9,112 rows, 348 pos), else test (25,892 rows, 972 pos). Match groups cannot
  cross folds because the split is a pure function of the shared batch date.

## Model card

TGAT-flavored ego-graph attention (`scripts/gnn/model.py`):

| | |
|---|---|
| Neighborhood | last K=128 edges before the sample month |
| Edge token | event-type embedding (12) ⊕ functional time encoding cos(Δt·w+b), 16 dims, harmonic init 1 day–10 yr, learnable ⊕ 2 scalars (is-own-repo, first-event-on-repo) → d=64 |
| Layers | 1 masked self-attention block (2 heads, residual+LN+FFN) then 1 actor-query attention pooling layer (2 heads) whose weights are the exported attention |
| Actor query | 10 context features at t (event-type mix, log degree, log volume, tenure, own-repo share, recency) → 2-layer MLP |
| Head | concat(pooled, query) → MLP → hazard logit |
| Parameters | **61,213** (< 100k budget) |
| Training | BCE with pos-weight, AdamW lr 5e-4, batch 512, early stop on validation PR-AUC (patience 4), seed 20240719 |
| Cost | **~13 s** on Apple MPS (9 epochs); dataset build 0.6 s. Far under the 20-min cap — no downsizing needed |

Config (K=128, d=64, lr 5e-4) was chosen from a 4-point sweep **on validation
PR-AUC only** (0.10 → 0.18 across the sweep); test was scored once per run.
MPS kernels are not bitwise deterministic; repeat runs move validation PR-AUC
by ~±0.01. The numbers below are the final artifact run stored in
`data/gnn/metrics.json`.

## Results — honest, same people, same rows

Comparator: production LightGBM scores from `data/scores/trajectories.parquet`,
which covers **all 25,892 GNN-scoreable test rows** (731 test people × their
panel months). Every metric below is computed on the identical row set.

| Metric (test, batch ≥ 2024) | GNN | GBDT |
|---|---|---|
| Pooled PR-AUC (base rate 3.75%) | 0.202 | **0.379** |
| Pooled ROC-AUC | 0.763 | **0.879** |
| Within-calendar-month mean PR-AUC (32 months with both classes, ≥5 rows) | 0.294 | **0.433** |
| Matched-group peak-score rank, 141 groups (1 founder, ≥3 members): P(rank=1) | 0.362 | **0.447** |
| … chance P(rank=1) | 0.258 | 0.258 |
| … P(top half) | 0.553 | **0.624** |
| … mean normalized rank (lower better) | 0.388 | **0.343** |

**The GNN loses to the GBDT on every metric, as expected at this scale** — a
61k-parameter model reading ≤128 raw events cannot match a GBDT that consumes
years of engineered aggregates (global-volume-normalized activity, traction
received, collaborator influx…) the raw ego-stream doesn't even contain. It is,
however, clearly above chance on ranking founders within matched groups
(0.362 vs 0.258), from nothing but event types, timestamps, and two binary
edge flags.

## Qualitative attention findings

`data/gnn/attention/<login>.json` for the 5 richest-graph test founders
(abhiaiyer91, achantavy, aluzzardi, smthomas, vdeturckheim): per panel month,
the top-5 attended repos (pooling-layer weights aggregated by repo, with the
dominant event type) plus the hazard score.

- **aluzzardi** (batch 2026-01): the demo story. Early months' attention sits
  on `docker/swarmkit` (own-repo attention share 0.00); by the final year it
  has shifted to `dagger/dagger`, `aluzzardi/daggerverse`,
  `aluzzardi/dagger-mutagen` (own-repo share 0.65), score drifting 0.61 → 0.73.
  The model literally watches him leave Docker's gravity well and start
  building his own thing — the "community detachment" construct from Pillar 2.
  Figure: `data/gnn/attention_demo.html`.
- **vdeturckheim** (batch 2026-04): `DataDog/dd-trace-py` + `nodejs/node` →
  `DataDog/guarddog` + own experiments (`covcov`, `stupid-idea-1`), own-repo
  attention share 0.36 → 0.57, score 0.64 → 0.76.
- **abhiaiyer91** (batch 2025-01): persistently high own-repo attention
  (Gatsby ecosystem + own plugins), score 0.62 → 0.80.
- **achantavy** (batch 2025-01): counter-example — attention locked on the
  employer OSS project `lyft/cartography` (share > 0.92 throughout), flat low
  score ~0.32. Concentration on *someone else's* repo is not a founding signal,
  and the model appears to know the difference (own-repo flag).

## Limitations

- **Ego-graph only.** No second hop, no shared-repo edges between people —
  co-founder pairing and exposure-to-founders (the actual Pillar-2 constructs)
  are invisible here. This is a temporal attention encoder over a person's own
  stream, not a graph network over the collaboration structure.
- **Truncated edge stream.** items.parquet caps at 40 items/quarter and covers
  only 4 text event types + CreateEvent; pushes, stars, forks, org joins are
  absent. The GBDT's aggregates see strictly more of the world.
- **Small N.** 620 founders (243 test), one YC-only outcome definition;
  within-group ranking rests on 141 groups.
- **Attention ≠ explanation.** Pooling weights are a plausible saliency signal,
  not a causal attribution; the aluzzardi narrative is legible but anecdotal
  (n=5, selected for graph richness).
- **Nondeterminism.** MPS training wobbles ±0.01 PR-AUC across runs; no seed
  ensemble was run.

## What a full Pillar-2 version needs

1. **Real graph**: person–repo–person message passing (2 hops), so
   new-strong-tie onset and founder exposure become computable; Neo4j person
   spine as substrate.
2. **Full event streams** from ClickHouse (all event types, uncapped), with
   per-edge features (repo age, repo owner type, collaborator counts).
3. **Hybrid, not replacement**: the honest reading of 0.20 vs 0.38 is that
   engineered aggregates carry signal the raw ego-stream lacks — feed the GBDT's
   feature vector in as the query and let attention add the *which-repos-why*
   layer, then re-run the ablation grid under the standing null gate.
4. **Scale + regularization study** before any headline claim: this experiment
   is an existence proof for attention legibility, not a model candidate.
   Per the research program: anything that can't clear the GBDT under
   identical splits stays an appendix — this stays an appendix.

## Artifacts

- `data/gnn/metrics.json` — everything above with exact denominators
- `data/gnn/attention/{abhiaiyer91,achantavy,aluzzardi,smthomas,vdeturckheim}.json`
- `data/gnn/attention_demo.html` — self-contained SVG, aluzzardi
- `scripts/gnn/{dataset,model,run}.py`
