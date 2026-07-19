# Full-Cohort Semantic Annotation: Scaling the Pilot to All Scored Actors (2026-07-19)

**Question.** The deep-slice pilot showed LLM semantic annotation lifts top-K precision
(p@10 0.40 → 0.70 in the top region) but ran on 734 actors. Does the lift survive on the
full scored cohort (2,765 actors: 690 founders, 2,075 controls), and what is the
observability boundary measured on *all* scored founders rather than only the top region?

**Method.** Full cohort = every scored actor from `data/features_panel_main.parquet`
(distinct login + person_type + t_cutoff + match_group_id; 7,468 panel actors, 2,765 of
them scored in `data/scores/trajectories.parquet`) joined with peak trajectory score →
`data/pilot/full_cohort.parquet`. Pre-cutoff text events extracted with the pilot SQL
(48-month window, 9 text-bearing event types): **397,169 rows, 1,790/2,765 actors with
≥1 text event**; the pilot's 182,295 rows reproduced byte-identically from cache, and the
2,031 non-pilot actors cost 9 fresh playground batches (~52 s wall, no quota stall).
Every actor with a non-empty digest annotated with the pilot's exact prompt/model
(`anthropic/claude-sonnet-4.5`, temp 0, content-addressed cache): **1,780 annotated**
(10 actors have text events but empty digests — branch-only creates / sub-30-char
comments; `annotate.py` now skips these), 1,445 new LLM calls ≈ **$9** (1.87 M input +
0.23 M output tokens estimated across all 1,790 digests; 335 pilot annotations reused
from cache, values verified identical). Code: `src/vc_brain/pilot/extract.py --full`,
`annotate.py --full`, `eval_full.py`. All digests are pre-t_cutoff event text only; no
current-day data enters any annotation.

## Finding 1 — interactivity rule at full scale: top-of-ranking only, confirmed

Zero-text actors (no create/fork/issue/PR/comment/release/member/public event in the
48-month pre-cutoff window):

| region | founders filtered | controls filtered |
|--------|-------------------|-------------------|
| overall (690 / 2,075) | 250 (36.2%) | 725 (34.9%) |
| top region peak ≥ 0.28 (149 / 265) | **0 (0%)** | **79 (29.8%)** |

The pilot's asymmetry replicates exactly: free precision at the top, destructive as a
global filter. By peak decile, founder no-text share is 55–71% in deciles 2–5 but **0%
in deciles 7–10** (controls stay at 23–34% everywhere) — every high-scoring founder is
interactive, so applying the rule only above a score threshold costs zero founders.

## Finding 2 — semantic re-rank: large lift at the head, a *loss* deeper in the list

Precision@K over the whole 2,765-actor cohort (690 positives = 25.0% base rate), three
rankings: counts-only (peak desc), interactivity-filtered (zero-text removed, peak
desc), semantic (gestation desc, peak tiebreak, no-text/unannotated → 0):

| K | counts | interactivity | semantic |
|-----|--------|---------------|----------|
| 10 | 0.400 | 0.400 | **0.700** |
| 25 | 0.480 | 0.560 | **0.680** |
| 50 | 0.500 | 0.560 | 0.480 |
| 100 | 0.420 | **0.470** | 0.420 |
| 200 | 0.405 | **0.490** | 0.370 |

The pilot's head-of-list lift survives at full scale (p@10 0.40 → 0.70, p@25 0.48 →
0.68) — and the honest new finding is that it **inverts beyond K≈50**. Cause: the
annotator emits only 12 distinct gestation values (0–95 in coarse steps); just 146
actors score ≥ 70 (54 founders, 92 controls), so the top-50 sits entirely in the
85–95 block (24/50 positive) and by K=200 the ranking is deep in the gestation-15–25
mass where controls outnumber founders ~3:1. Semantic annotation is a *head-of-list
instrument*: use it to re-rank the top ~100 of the count model, not to replace the
ranking. (Counts-only p@K itself is tie-break-dependent: the score ties at the K-cuts
span 9–66 actors; ordering within ties here is deterministic-arbitrary by login sort.)

## Finding 3 — gestation carries rank signal everywhere the count model is flat

Founder-vs-control AUC on the 1,780 annotated actors:

| slice | gestation AUC | peak AUC |
|-------|---------------|----------|
| overall | **0.643** | 0.601 |
| peak Q1 (n=445) | 0.621 | 0.584 |
| peak Q2 (n=445) | **0.643** | 0.492 |
| peak Q3 (n=445) | **0.576** | 0.472 |
| peak Q4 (n=445) | 0.604 | 0.590 |

Within every peak-quartile — i.e., after conditioning away most of the count signal —
gestation still separates founders from controls; in the middle quartiles, where peak is
at or below chance (0.47–0.49), gestation adds +9–15 points of AUC.

**The deployment-relevant number is matched-pairs.** Comparing each founder against
their own matched controls (same cutoff month, unannotated → 0; 2,075 pairs):
**pairwise AUC 0.774 for gestation vs 0.640 for peak** (wins 1,405 / ties 401 / losses
269). In the frozen-clock "same month, same pool" setting the semantic instrument beats
the count model by 13 points.

## Finding 4 — observability boundary on all 690 scored founders

- 250/690 (36.2%) have **zero text events** pre-cutoff — invisible to any
  content-based method.
- 435/690 annotated. Builder-type shares: coursework 28.0%, employment 18.2%,
  **own_product_building 17.5% (76)**, OSS 12.9%, hobby 9.4%, research 7.6%,
  portfolio 6.4%.
- So public product-gestation is observable for **76/690 = 11.0% of all scored
  founders**; 24.8% (37/149) in the top region, 13.6% (39/286) below it.
- **Correction to the pilot doc:** the pilot reported 45/149 (30%) top-region founders
  as own_product_building; the stored `annotations.parquet` (reused unchanged here)
  contains **37/149 (24.8%)** — the 45 appears to be a tally error in the write-up (the
  remaining classes match: 23 coursework, 33 employment, 25 OSS, 16 research; plus 9
  hobby, 6 portfolio the pilot text omitted). The observability boundary is tighter
  than reported.

## Finding 5 — builder-type composition, founders vs controls (1,780 annotated)

| builder_type | founders (n=435) | controls (n=1,345) | ratio |
|--------------|------------------|--------------------|-------|
| coursework_learning | 28.0% | 45.4% | 0.62 |
| employment_work | 18.2% | 16.1% | 1.13 |
| own_product_building | **17.5%** | **10.0%** | 1.75 |
| oss_contribution | 12.9% | 7.4% | 1.75 |
| hobby_tinkering | 9.4% | 11.4% | 0.82 |
| research | **7.6%** | **3.1%** | 2.43 |
| portfolio_jobseek | 6.4% | 6.6% | 0.97 |

Coursework is the dominant control class (45%) and depressed among founders;
own-product, OSS, and research are founder-enriched (1.75–2.4×). Gestation ≥ 70:
12.4% of annotated founders vs 6.8% of controls. The 92 high-gestation controls are
the label-noise/meet-worthy pool: at full scale the only FP-portrait members with
gestation ≥ 70 are exactly the confirmed mislabeled founder (samyakkkk, 95) and the
four hand-labeled "interesting" profiles (jwetzell/agittins/lehuygiang28 85,
ahmedkhlief 75) — the instrument keeps reproducing the human deep-read.

## Interpretation (honest)

1. **What scaled:** interactivity rule (exact replication), head-of-list semantic lift
   (p@10 0.70, p@25 0.68 vs 0.40/0.48 counts), instrument agreement with hand labels.
2. **What's new and sobering:** (a) semantic re-rank *hurts* at K ≥ 50 — the coarse
   gestation scale runs out of resolution after ~146 high-gestation actors; (b) the
   observability boundary is tighter than the pilot claimed — 11% of all scored
   founders (25% even in the top region) show public product-gestation pre-batch. A
   YC-label AUC ceiling near 0.65 for any content instrument follows directly.
3. **Product shape this implies:** count model proposes (recall engine), interactivity
   rule prunes the top, semantic annotation re-ranks the top ~100 and attaches
   "why" (builder_type/building_what) to each candidate. The 92 high-gestation controls
   should be treated as a sourcing list, not as errors.
4. **Next purchases unchanged** (pilot decision gates hold): label broadening beyond YC
   (the ceiling is label noise + observability, not the instrument), name-blinded
   replication (Pod B), commit messages via GitHub API for the annotated cohort.

**Caveats.** (i) Name/world-knowledge contamination: digests are event-time text but
logins/repo names are visible; results are an upper bound pending the name-blinded
replication. (ii) Gestation quantization (12 distinct values) makes deep-K rankings
tie-dominated; treat p@K for K ≥ 50 under the semantic ranking as unstable. (iii)
Counts-only p@K sits on 9–66-actor score ties at every cut. (iv) Labels are YC-only;
measured precision is a floor (portrait: ~4% of top controls are unlabeled founders,
~20% meet-worthy). (v) 1 annotation record lacks `team_formation` (parse quirk); no
other schema violations across 1,780 records.

*Artifacts: `data/pilot/full_cohort.parquet` (2,765), `data/pilot/full_text_events.parquet`
(397,169 rows), `data/pilot/full_annotations.parquet` (1,780). Eval:
`uv run python -m vc_brain.pilot.eval_full`. Compiled 2026-07-19.*
