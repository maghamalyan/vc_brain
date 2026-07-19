# Corrected Metrics — Single Source of Truth for Headline Numbers (2026-07-19, wave 3 Pod E)

Every headline number in this program now exists in up to three flavors: **uncorrected**
(scored against raw YC-only labels, as first reported), **hygiene-corrected** (screened
unlabeled founders excluded from the control pool), and **blind** (name-masked
annotator, the contamination bound). This doc pins all of them with provenance so the
final report quotes one place. Reproduce with:
`uv run python -m vc_brain.pilot.hygiene` (full-cohort corrected numbers),
`uv run python -m vc_brain.pilot.eval_full` (uncorrected),
`uv run python -m vc_brain.pilot.eval_blind` (blind, top region),
`uv run python -m vc_brain.labelnoise.mid_screen` (mid-band screen).

## 1. The exclusion list (negative-pool hygiene)

`data/pilot/excluded_controls.parquet` — **13 "controls" with confirmed current-day
founder evidence** (classification FOUNDER_EVIDENCE, every row with a URL), built by
`src/vc_brain/pilot/hygiene.py` from the wave-2 screen (10, `source=wave2_screen`:
martonlederer, samyakkkk, crohr, senalbulumulle, ahmedkhlief, egil, miladsoft, rin1024,
tipstrade, tkokada) plus the wave-3 mid-band screen (3, `source=wave3_mid_screen`:
danielballoch, remy, sisoje). Schema: gh_login, reason, evidence_url, source,
data_basis=`current_day_label_only`.

Two decisions, stated explicitly:

- **Excluded, not relabeled.** Current-day founder evidence proves the
  founder/non-founder label is wrong but not that the person satisfies the study's
  positive definition (YC founder with a batch-dated t_cutoff). Dropping them is the
  conservative correction; relabeling would require horizon-matched founding dates we
  don't have.
- **Both species excluded.** 4/13 are venture-shaped startups (martonlederer,
  samyakkkk, crohr, senalbulumulle — all gestation ≥ 85), 9/13 consultancies/studios/
  small firms. Both poison a founder/non-founder label; only the venture-shaped four
  are direct sourcing targets.

## 2. Full-cohort table (2,765 scored actors, 690 positives; the deployment numbers)

Corrected = excluded logins dropped from controls; positives unchanged. Cohort
2,765 → 2,755 (wave-2 10) → 2,752 (all 13); annotated 1,780 → 1,770 → 1,767.

| metric | uncorrected | corrected (10) | corrected (13) |
|---|---|---|---|
| gestation AUC (annotated subset) | 0.643 | 0.647 | 0.648 |
| peak AUC (annotated subset) | 0.601 | 0.605 | 0.605 |
| matched-pairs AUC, gestation (nulls→0) | 0.774 | 0.776 | 0.776 |
| matched-pairs AUC, peak (nulls→0) | 0.640 | 0.642 | 0.642 |
| top-region label precision (149 founders) | 36.0% (414) | 36.9% (404) | 37.2% (401) |

Precision@K, three rankings (counts = peak desc; interactivity = zero-text removed,
peak desc; semantic = gestation desc, peak tiebreak, unannotated → 0):

| K | counts (unc → corr-13) | interactivity (unc → corr-13) | semantic (unc → corr-13) |
|---|---|---|---|
| 10 | 0.400 → 0.400 | 0.400 → 0.400 | **0.700 → 1.000** |
| 25 | 0.480 → 0.520 | 0.560 → 0.600 | **0.680 → 0.760** |
| 50 | 0.500 → 0.520 | 0.560 → 0.580 | 0.480 → 0.560 |
| 100 | 0.420 → 0.420 | 0.470 → 0.500 | 0.420 → 0.440 |
| 200 | 0.405 → 0.410 | 0.490 → 0.505 | 0.370 → 0.385 |

(The corrected-10 and corrected-13 p@K columns are cell-for-cell identical: the mid-band
three carry low gestation (25–45) and mid-list count ranks — sisoje sits at counts rank
135, remy at semantic rank 200 — but each removal pulls another *negative* into the cut,
so no measured cell moves. Corrected-13 differs from corrected-10 only in AUC at the
third decimal and top-region precision.)

**The p@10 row is the cleanest validation in the program:** the semantic ranking's
three top-10 "misses" — martonlederer, samyakkkk, crohr, all gestation 95 — were each
confirmed as unlabeled founders by the independent wave-2 screen. With the negative
pool cleaned, the semantic top-10 is **10/10**. The wave-2 prediction ("true p@10 ≈
0.78") was itself an underestimate.

## 3. Blind vs unblinded vs corrected (top region, 414 actors / 335 annotated)

The blind replication (name/org-masked digests, `blind_replication.md`) is the
contamination bound; hygiene correction composes with it. Precision@K re-ranking the
top region (no-text → 0, peak tiebreak); corrected = the 13 exclusions applied
(region 414 → 401):

| K | counts | unblinded | blind | unblinded + corrected | **blind + corrected** |
|---|---|---|---|---|---|
| 10 | 0.400 | 0.700 | 0.600 | 1.000 | **0.700** |
| 25 | 0.520 | 0.520 | 0.440 | 0.680 | **0.600** |
| 50 | 0.480 | 0.520 | 0.480 | 0.620 | **0.560** |
| 100 | 0.430 | 0.530 | 0.480 | 0.570 | **0.540** |

Founder-vs-control AUC on the common 335: gestation 0.558 unblinded vs 0.548 blind
(peak baseline 0.575). **The most conservative defensible headline — name-blinded
annotator scored against a hygiene-corrected pool — is p@10 = 0.70, p@25 = 0.60,
vs 0.40/0.52 for the count model.** The blind column is itself a lower bound (masking
destroys legitimate own-org ownership evidence; see blind_replication.md).

## 4. Label-noise monotonicity (screen, complete across all gestation bands)

| gestation band | FOUNDER_EVIDENCE | rate | exact 95% CI | venture-shaped |
|---|---|---|---|---|
| high (g ≥ 50) | 8/31 | **25.8%** | 11.9%–44.6% | 4/31 = 12.9% |
| mid (15 < g < 50) — wave 3 | 3/41 | **7.3%** | 1.5%–19.9% | 0/41 |
| low (g ≤ 15) | 2/39 | **5.1%** | 0.6%–17.3% | 0/39 |

Monotone in gestation; the mid band lands near the low band, not the ~10–15%
interpolation previously assumed, and contributes zero venture-shaped noise. Expected
unlabeled founders among the 265 top-region controls: **~17–21 (~6.4–7.9%)** —
essentially unchanged from the wave-2 extrapolation. Every venture-shaped unlabeled
founder found so far has gestation ≥ 85: the instrument's flag is precisely where
venture-shaped label noise lives.

## 5. Commit-message depth, completed (Pod D tail: full 180)

The 20 annotations lost to wave-2 credit exhaustion (alphabetical t–z tail) were
filled from cached digests (20 LLM calls ≈ $0.40; the 160 existing annotations
reproduced byte-identically from cache). On the full paired 180:

- **Paired ΔAUC (commit-augmented − event-only) = −0.043, 95% bootstrap CI
  [−0.092, +0.004]** (2,000 resamples, seed 42; event-only 0.557 → augmented 0.514).
  The wave-2 preliminary (−0.043 on 160, CI [−0.093, +0.009]) is confirmed and the CI
  now all but excludes any lift.
- Still not inert: 43/180 changed builder_type, 22/180 moved gestation ≥ 30 points,
  both directions, both classes. Verdict unchanged: commit text is evidence about the
  person uncorrelated with the founder label — dossier material, not a ranking feature.

## Which number to quote where

| claim | number | source |
|---|---|---|
| headline sourcing result (optimistic) | semantic p@10 1.000 / p@25 0.760, full cohort, corrected | §2 |
| headline sourcing result (conservative) | blind + corrected p@10 0.700 / p@25 0.600, top region | §3 |
| deployment ranking metric | matched-pairs gestation AUC 0.776 (vs peak 0.642), corrected | §2 |
| label-noise rate for high-gestation flags | 25.8% (CI 11.9–44.6%); venture-strict 12.9% | §4 |
| commit text as feature | ΔAUC −0.043 (CI −0.092, +0.004) — null | §5 |

## Caveats (read before quoting)

1. **The correction is not ranker-neutral.** The screen targeted high-gestation
   controls — exactly the people the semantic ranking places on top — so hygiene
   correction structurally favors the semantic columns. The counts/interactivity
   rankings' top misses (incl. 79 no-text top-region controls) were never screened;
   their corrected numbers remain understated. The honest comparison is: corrected
   semantic vs *also-underestimated* corrected counts.
2. **p@10 = 1.000 is a 10-sample cell.** Quote it together with p@25 = 0.76 and the
   matched-pairs AUC; a single future miss puts it at 0.90.
3. **Current-day evidence, horizon mismatch.** Exclusions rest on founder evidence
   visible today; some may have founded after the outcome window (bounds "ever
   founds", not "founds within horizon"). Cuts both ways: GONE accounts and founders
   with no public web presence mean the screen under-detects.
4. **Exclusion vs relabel.** Relabeling the 4 venture-shaped hits as positives would
   raise semantic numbers further; we chose the conservative variant.
5. **p@K tie-dependence** at the K-cuts (9–66-actor score ties in the counts ranking)
   carries over from eval_full unchanged.
6. Blind numbers exist only for the 335-actor top region (the full-cohort blind run
   was not funded); §3's composition is the top-region view.

*Artifacts: `data/pilot/excluded_controls.parquet` (13),
`data/pilot/control_screen_mid.parquet` (41), `data/pilot/annotations_commits.parquet`
(200 rows, 180 augmented). Code: `src/vc_brain/pilot/hygiene.py`,
`src/vc_brain/labelnoise/mid_screen.py`. Compiled 2026-07-19, wave 3 Pod E.*
