# Spec P4 — Tier-1 hazard model + honest evaluation

## Framing
Discrete-time hazard, person-month panel. Per founder: batch_start B,
gestation_start F = B − 9mo, feature cutoff t_cutoff = B − 12mo (features NEVER cross
it). Panel months m ∈ [B−48mo, B−12mo]. Label y(m) = 1 iff F − m ≤ 6 months
(i.e. m ∈ [B−15mo, B−12mo]). Founders thus contribute negative person-months in their
own early history (correct hazard framing). Controls: pseudo-B sampled to match the
positives' calendar distribution, y = 0 everywhere.

## Features (src/vc_brain/features/build.py) — all from data ≤ m only
Normalize activity counts by global monthly baselines (platform growth).
- Levels: counts per event class (push, create, PR, PR-review, issue, comment, watch
  given) over trailing 1/3/6/12 mo.
- Dynamics: ratio & delta of trailing-3mo vs prior-12mo, per class; burst z-score
  (last-3 vs mean/std of prior 12) for pushes and repo creations.
- Repo creation: new repos in 3/6/12mo, months-since-last-new-repo, cumulative repos.
- Traction received (owned_repo_agg): stars/forks/issues-by-others trailing 3/12mo +
  same dynamics. (Hypothesis: rising external attention precedes founding.)
- Behavior shift: weekend-activity share now vs 12mo ago (side-project signal).
- Tenure: months since first event; activity Gini across months (consistency).
Feature builder must emit a features data card: names, definitions, null policy.

## Models (src/vc_brain/models/train.py)
1. Logistic regression (standardized, L2) — baseline, must be reported.
2. LightGBM (max_depth≤6, early stopping on temporal validation fold,
   scale_pos_weight). Keep ONLY if it beats logistic on validation PR-AUC by >10% rel.
Seeded, deterministic; save model + feature list + params JSON to data/models/.

## Split (leakage-proof — Claude reviews this code line-by-line)
- Train: founders with B ≤ 2023-12-31 + their matched controls.
- Test: founders with B ≥ 2024-01-01 + their matched controls.
- Tuning: temporal sub-split inside train (B ≤ 2022-12 train / 2023 valid). No test
  peeking. Controls follow their matched positive's fold (match_group_id column
  REQUIRED in the panel so this is auditable).

## Evaluation (src/vc_brain/eval/report.py → data/eval/report.{json,md} + figures)
- Person-month PR-AUC (primary), ROC-AUC (secondary).
- Person-level (max score over test window): precision@50/@100, recall@review-budget
  (top 10% of controls+founders pool), lift@1%.
- Calibration: reliability curve + Brier on case-control-corrected probabilities;
  state the assumed population base rate explicitly (sensitivity: 0.5%/1%/2%).
- Lead time: detection month = first m with score ≥ 99th percentile of control scores
  that month; report median + IQR of (B − detection_month) for detected test founders,
  and detection rate.
- MANDATORY null/sanity runs (results in report):
  a) Shuffled labels (within calendar month) → PR-AUC must collapse to ~base rate.
  b) Ablation: levels-only vs +dynamics vs +traction (each block's marginal value).
  c) Top-20 feature importances (gain) — flagged for Claude review.
- Figures (plotly, saved as standalone html + png if kaleido available): PR curve,
  reliability, lead-time histogram, 6 example founder score trajectories.

## Outputs for P5/P8 (FROZEN contracts — see specs/p8_slice.md)
- data/scores/trajectories.parquet (gh_login, month, score) for ALL test-period people.
- data/scores/candidates.parquet for top-k test-period detections
  (source='outbound_detector', momentum_3mo = score slope; status='candidate').

## Acceptance (Claude verifies)
1. pytest green (feature windows unit-tested against hand-computed examples; split
   logic tested: no B > 2023 in train, no feature month ≥ t_cutoff anywhere).
2. Null run collapses; if it doesn't → STOP, report leakage, do not proceed to P5.
3. Honest report — no cherry-picking; include the logistic baseline numbers.
