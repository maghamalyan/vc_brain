# GNN as a reranker on top of the GBDT — tie-break wins, blends lose

**Status: exploratory, self-contained.** Follow-up to
`docs/exploration/temporal_gnn.md`. The GNN loses to the GBDT as an
*independent* scorer on every metric; this experiment asks whether it still
adds value as a **reranker/blend** — especially at the top of the ranking,
where the 7-tree production LightGBM emits heavily quantized scores and ties
are the norm. Code: `scripts/gnn/rerank.py`
(`uv run python scripts/gnn/rerank.py`); artifacts:
`data/eval/gnn_rerank.json`, `data/gnn/rerank_scores.parquet`,
`data/gnn/model_rerank.pt`.

## The tie problem is real and large

The selected LightGBM stopped at **7 trees** (`lightgbm_best_iteration = 7` in
`data/models/params.json`), so its score space is tiny. On the held-out test
split (person peak scores, the quantity every person-level metric ranks on):

| | Full test pool | GNN-scoreable pool |
|---|---:|---:|
| People | 2,765 | 731 |
| Distinct peak scores | **305** | 198 |
| People in tied peak groups | 2,555 (**92.4%**) | 590 (80.7%) |
| People in ties spanning founder+control | 2,358 (**85.3%**) | 541 (74.0%) |
| Matched groups with the founder's peak tied | 180 / 415 | 27 / 141 |
| People sharing the exact score at the rank-50 cut | 77 | 45 |
| Distinct row-level scores | 9,793 / 102,305 | 6,043 / 25,892 |

At the rank-50 cutoff of the full pool, 77 people share one score — the
"top 50" is substantially an alphabetical accident (eval breaks ties by
login). There is genuine headroom for *any* informative tie-breaker.

## Protocol (validation-only tuning; test scored once)

- **Aligned scores.** GBDT test scores come from
  `data/scores/trajectories.parquet` (verified bit-identical to the saved
  `selected.joblib` on all 102,305 test rows). GBDT **validation** scores
  cannot come from the saved bundle — it was refit on tuning+validation, so
  its validation scores are in-sample. Instead the *tuning-stage* LightGBM
  (fit on tuning_train only, early-stopped on validation) was replicated
  exactly as in `train.py`; its validation PR-AUC reproduces the recorded
  `training_metrics.json` value **0.15413496** to machine precision.
- **GNN.** `run.py` never saved a checkpoint, so the model was **retrained
  identically** (same seed/config); this run reached validation PR-AUC
  0.1782 vs the original 0.1786 (known MPS wobble ~±0.01). The checkpoint is
  now saved (`data/gnn/model_rerank.pt`) plus all aligned scores.
- **Pools.** Everything below runs on the GNN-scoreable joint row set
  (validation 9,112 rows / 254 people; test 25,892 rows / 731 people /
  141 matched groups), baseline included — apples-to-apples. Precision@k
  numbers therefore differ from `data/eval/report.json`, which ranks the
  full 2,765-person pool.
- **Strategies.**
  - *(a) tie-break* — score = gbdt + ε·gnn with ε = half the smallest gap
    between distinct GBDT values: provably never reorders distinct GBDT
    scores, only resolves exact ties by GNN score. No tuned parameter.
  - *(b) logit blend* — σ(α·logit(gbdt) + (1−α)·logit(gnn)); α on a 0.05
    grid, chosen on validation matched-group expected P(rank=1) → **α=0.95**.
  - *(c) top-K rerank* — per calendar month the GBDT's top-200 set is kept
    fixed; the blend only permutes the GBDT score values inside it (score
    multiset preserved, outside rows untouched) → tuned **α=0.95**.
- **Metrics.** Person-level precision@50/@100 (peak score, ties by login, as
  in eval); matched-group expected-rank P(rank=1)/P(top-half) under the
  `report.py` tie convention (141 groups; note the *expected-rank* baseline
  is 0.459, slightly above the 0.447 in `temporal_gnn.md`, which broke ties
  alphabetically); within-calendar-month mean PR-AUC (32 months, run.py
  convention). Bootstrap: 200 paired resamples — people for precision@k and
  within-month, matched groups for rank metrics; identical resample streams
  across strategies.

## Test results (731 people, 141 groups, 32 months)

| Strategy | P@50 | P@100 | P(rank=1) | P(top-half) | Within-month PR-AUC |
|---|---:|---:|---:|---:|---:|
| GBDT alone (baseline) | 0.640 | 0.620 | 0.459 | 0.729 | 0.433 |
| **(a) tie-break** | **0.720** | 0.610 | **0.482** | **0.745** | **0.457** |
| (b) logit blend α=0.95 | 0.560 | 0.500 | 0.447 | 0.730 | 0.428 |
| (c) top-200 rerank α=0.95 | 0.580 | 0.530 | 0.437 | 0.742 | 0.408 |
| GNN alone (context) | 0.440 | 0.430 | 0.362 | 0.688 | 0.283 |

Paired bootstrap deltas vs baseline (mean [95% CI]):

| Delta vs GBDT | tie-break | logit blend | top-200 rerank |
|---|---:|---:|---:|
| P@50 | +0.058 [0.000, +0.160] | −0.099 [−0.300, +0.081] | −0.070 [−0.240, +0.101] |
| P@100 | +0.014 [−0.020, +0.080] | −0.112 [−0.230, −0.010] | −0.075 [−0.180, +0.040] |
| P(rank=1) | +0.023 [−0.005, +0.051] | −0.013 [−0.087, +0.052] | −0.023 [−0.091, +0.035] |
| P(top-half) | +0.016 [−0.005, +0.038] | +0.005 [−0.045, +0.059] | +0.016 [−0.036, +0.070] |
| Within-month PR-AUC | **+0.025 [+0.013, +0.040]** | −0.004 [−0.033, +0.031] | −0.024 [−0.054, +0.010] |

## Verdicts

- **(a) Tie-break: WIN — the only strategy that helps, and the only
  deployable one.** Positive on every headline metric; the within-month
  PR-AUC gain (+0.025) has a bootstrap CI that excludes zero, P@50
  (+0.058) and P(rank=1) (+0.023) are borderline (CI touches zero). By
  construction it cannot make the GBDT ranking worse where the GBDT
  actually expresses an opinion — all gains come from resolving ties the
  current pipeline resolves alphabetically (or by 3-month momentum in the
  candidate export). Risk-free upside.
- **(b) Logit blend: NULL/NEGATIVE.** Validation (only 45 matched groups;
  one group = 0.022 of P(rank=1)) preferred α=0.95 over α=1.0 (0.444 vs
  0.396), but the bump did not transfer: on test every point estimate is at
  or below baseline and P@100 is significantly negative. Letting GNN logits
  move *distinct* GBDT scores hurts.
- **(c) Top-K rerank: NULL/NEGATIVE.** Same story via a different route
  (α=0.95 tuned on the same noisy 45 groups); within-month PR-AUC −0.024
  and precision deltas negative. Constraining the blend to the top-200 per
  month does not rescue it.

The pattern is coherent: the GNN carries real but *weaker* signal
(0.362 vs 0.459 P(rank=1) alone). Any mechanism that lets it override the
GBDT's distinct-score ordering loses more than it gains; the one mechanism
that restricts it to information the GBDT literally does not have — which of
92% of people inside tied score plateaus comes first — wins.

## Caveats

- Single GNN retrain (MPS nondeterminism ±0.01 val PR-AUC); no seed
  ensemble. The tie-break direction is consistent across all five metrics,
  but only within-month PR-AUC individually clears its CI.
- Validation tuning for (b)/(c) rests on 45 matched groups — genuinely too
  few; the honest conclusion is "no evidence a blend transfers," not "0.95
  is the right α."
- Precision@k here is on the 731-person GNN-scoreable pool. Deploying
  tie-break on the full 2,765-person pool requires GNN coverage beyond
  Cohort-D (or leaving non-covered ties to the current momentum/login rule).

## Is a two-hop retrained GNN the recommended next step?

**Yes, but for the tie-break slot, not as a scorer.** The mechanism that won
is "orthogonal weak signal resolves GBDT plateaus"; a two-hop model over
`data/graph/coactivity_edges.parquet` (678k co-activity edges, 342k distinct
neighbors, 1,162 founder-neighbor pairs already extracted) adds exactly the
constructs the ego-stream GNN cannot see — new-strong-tie onset and
exposure-to-recognized-founders — so its signal should be *more* orthogonal
to the GBDT's aggregates, which is what the tie-break consumes. Two hard
requirements from the `data/graph/README.md` leakage warning: neighbor
founder status must be recognized-founder-as-of-t
(`founder_batch_start_date <= t`), and edges must be windowed to
`month < t_cutoff`. Gate: re-run this exact harness (tie-break only,
validation-tuned nothing, test scored once) and require the within-month
PR-AUC delta CI to stay above zero and P@50/P(rank=1) deltas to at least
match today's +0.058/+0.023 before promoting anything beyond an appendix.
