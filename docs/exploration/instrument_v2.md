# Instrument v2: Structure-Preserving Blind + Fine-Grained Gestation (Pod F, 2026-07-19)

**Question.** Wave-2 measured two defects in the v1 annotation instrument: (a) the
annotator emits only 12 distinct gestation values, so the semantic re-rank runs out of
resolution and inverts against the count model beyond K≈50 (full-cohort doc, Finding 2);
(b) Pod B's strict name-blind destroys legitimate ownership evidence — the actor's own
startup org becomes `EXTn`, so building one's company reads as external work (14/20 of
the largest blind score-drops were org-create actors). v2 fixes both in one instrument
revision and asks: is v2 strictly better as THE production instrument?

**Method.** `src/vc_brain/pilot/annotate_v2.py` (v1 `annotate.py` untouched):

- *Structure-preserving masking* extending Pod B's contract: actor login → `USER`
  (boundary + substring pass); owners with **event-time admin evidence** (actor created
  repos under them via CreateEvent, or performed MemberEvent adds on their repos) →
  `USER_ORG1…`, masked at any token boundary; member logins → `PERSONn`; other owners →
  `EXTn` (owner position / @mention only); repo stems, titles, bodies, dates intact.
  The prompt tells the annotator that work in a `USER_ORGn` repo is work on the USER's
  own organization. Audit over all 486 masked digests: **0 residual actor-login leaks,
  0 admin-org token leaks**. 181/486 actors carry ≥1 USER_ORG (348 org assignments:
  259 create-evidence-only, 55 create+member, 34 member-only).
- *Finer score contract*: gestation_likelihood must be an integer 0–100 with explicit
  band anchors (0–9 none / 10–29 tinkering / 30–49 serious side project / 50–69
  product-shaped pre-commercial / 70–89 clear venture gestation / 90–100 unmistakable
  company-building), an explicit anti-round-number instruction ("63 vs 60 matters"),
  and a new `rank_evidence` one-liner naming the 1–2 strongest observations (present in
  486/486 records).
- Cohort: union of all top-region pilot actors (414; 335 with text) + every full-cohort
  actor with v1 gestation ≥ 35 (236; 151 outside the top region) = 565 actors, **486
  with non-empty digests, all annotated** (`anthropic/claude-sonnet-4.5`, temp 0,
  content-addressed cache `data/cache/pilot_annotations_v2/`, 486 calls ≈ $5).
  Eval: `uv run python -m vc_brain.pilot.eval_v2`.

## Finding 1 — resolution is fixed (12 → 34 distinct values, round numbers gone)

On the common 486 annotated-both set: v1 emits 11 distinct values, 97.3% multiples
of 5; **v2 emits 34 distinct values, 16.3% multiples of 5** (0.2% multiples of 10).
Spearman(v1, v2) = 0.764 — same underlying signal, finer expression. Honest residual:
the annotator has new favorite values — 58 alone holds 78/486 people (the
"product-shaped, mid-band" default), then 18 (59) and 12 (50). Resolution tripled;
it did not become continuous.

## Finding 2 — the K≥50 inversion disappears

Precision@K over the full 2,765-actor cohort (690 positives). `v2-hyb` = v2 score where
annotated, else v1, else 0, peak tiebreak (the production ranking; every non-v2 actor
has v1 < 35, so the head is pure v2):

| K | counts | v1 semantic | v2 hybrid |
|-----|--------|-------------|-----------|
| 10 | 0.400 | **0.700** | 0.600 |
| 25 | 0.480 | 0.680 | 0.680 |
| 50 | 0.500 | 0.480 | **0.600** |
| 100 | 0.420 | 0.420 | **0.450** |
| 150 | 0.407 | 0.380 | 0.393 |
| 200 | 0.405 | 0.370 | 0.395 |

v1 fell below counts at K=50 (−2pp) and K=200 (−3.5pp); **v2 beats counts by +10pp at
K=50 and +3pp at K=100, and is within ~1pp of counts at 150–200** instead of −3pp.
The instrument now degrades gracefully to count-model parity instead of inverting.
(K=100 sits inside the 78-person 58-cluster, so that cell is peak-tiebreak-dependent.)
Matched-pairs pairwise AUC (frozen-clock view, nulls→0): **v2-hybrid 0.775 vs v1 0.774
vs peak 0.640** — the finer scale converts 111 of v1's 401 ties into 59 wins / 52
losses; the 13.5-point lift over the count model is unchanged.

## Finding 3 — head-of-list: label-strict precision drops, utility precision is ~perfect

Label-strict, v2's @10 is 0.60 (full-cohort) / 0.50 (top-region-only re-rank) vs
v1-unblinded 0.70 and Pod B strict-blind 0.60. But joining the top-10 "misses" against
the wave-2 control screen (`data/pilot/control_screen.parquet`):

- **Full-cohort v2 top-10: all 4 misses are URL-confirmed FOUNDER_EVIDENCE people**
  (samyakkkk/LandingHero, crohr/RunsOn, miladsoft, martonlederer/Community-Labs) —
  utility precision **10/10**.
- Top-region v2 top-10: 5 labeled founders + 4 FOUNDER_EVIDENCE + lehuygiang28
  (hand-labeled INT, meet-worthy) — **9/10 founded-something, 10/10 meet-worthy**.

v1-unblinded's 0.70 was partly fame-assisted (Pod B); v2's 0.60 is identity-blind and
its residual "errors" are exactly the unlabeled founders the sourcing product wants
surfaced. v2 also recovered two labeled founders v1 scored near zero: andreybavt
(v1 15 → v2 85; 24 versioned releases, 8 collaborators) and achantavy (5 → 82) — the
`rank_evidence` field states the reason in one line each.

## Finding 4 — the blinding artifact is fixed where it was measured

Pod B's 20 largest strict-blind droppers (mean gestation: unblinded 72.7 →
strict-blind **22.0**): under v2 they recover to **51.2**, and the org-create cases
that drove the artifact recover almost fully — levkk 95/15/**85**, erik-dunteman
95/15/**88**, egil 95/15/**72**, therne 95/25/**74** (unblinded/strict/v2). Meanwhile
the fame-suspect cases Pod B flagged stay down blind: taranjeet 65→34, teichman 45→18,
davidhu2000 45→24 — i.e. v2 restores event-time ownership evidence without restoring
name recognition. Distribution-wide (top region, n=335): |Δ|>30 share vs unblinded
falls from 11.1% (strict) to 7.8% (v2), mean delta −0.84.

Counter-case that keeps this honest: **egil at 72 is a false positive v2 cannot see** —
Pod D's commit-message probe showed his multi-repo .NET work is bUnit OSS
infrastructure (commit-augmented score 15), and the label-noise screen classifies his
entity as a solo consultancy. Ownership structure is necessary but not sufficient.

## Finding 5 — costs of blinding that remain (reported, not hidden)

- **YC-label AUC in the top region: v2 0.527 vs v1-unblinded 0.558, strict-blind
  0.548, peak 0.575** (n=335). On the full common set (n=486, gestation-enriched by
  construction, so range-restricted): v1 0.493, v2 0.508, peak 0.603. Blinding + the
  finer scale do not improve the (label-noise-capped) binary AUC; the gains are in
  ranking resolution and trustworthiness, not in this ceiling-limited metric.
- **Portrait cross-check compresses.** 11/13 FPs ≤ 28, but two FPs inflate to 58
  (roger-rodriguez, seyyedalimirhoseini — the latter was already Pod B's worst blind
  FP at 65: identity removal makes his course projects read as product). INT/NOISE
  people: 58–87, all `own_product_building`; the mislabeled founder samyakkkk still
  tops at 87, but agittins/jwetzell land at 67, below the 70-band the v1 numbers sat
  in. Separation survives (every INT/NOISE ≥ 58 = max FP), with overlap exactly at 58.
- **USER_ORG conflates own-org with employer-org admin.** achantavy's `USER_ORG1` is
  **lyft** (MemberEvent adds on lyft/cartography as an employed maintainer), so
  employer OSS reads as own-product (82; he is a labeled founder, so a lucky hit by a
  wrong mechanism). 34/348 org assignments (9.8%) rest on MemberEvent-only evidence;
  CreateEvent evidence (90.2%) is stronger but an employee creating repos under an
  employer org still qualifies. Ownership ≠ admin rights; no event-time fix exists in
  this schema.

## Verdict

**Adopt v2 as the production instrument — it is better, though not "strictly" better
on every number.** It fixes both targeted defects with measurements: resolution 12 → 34
distinct values (round-number share 97% → 16%), the K≥50 inversion replaced by
+10pp/+3pp over counts at 50/100 and parity at 200, matched-pairs 0.775 ≥ v1's 0.774,
and the ownership artifact resolved (droppers 22.0 → 51.2 blind) with zero identity
leaks. What it surrenders is exactly the part wave-2 already distrusted: the
fame-assisted @10 (0.70 → 0.60, with all residual top-10 "misses" being confirmed
unlabeled founders) and 2–3 AUC points against noise-capped YC labels. Report v2 as
the primary number and keep the unblinded v1 run as an upper-bound sensitivity, per
Pod B's recommendation.

Carry-forward items: (1) the 58-cluster — tie-break deep-K by peak (already done) and
treat K≈100 cells as tie-dominated; (2) MemberEvent-only USER_ORG evidence (9.8%) could
be dropped or flagged in a v2.1; (3) the two blind-inflated FPs at 58 are the price of
identity removal — the commit-message probe (Pod D) showed per-person texture can catch
these at dossier time, not rank time.

**Caveats.** (i) The v2 cohort is selection-biased by construction (top region ∪
v1 ≥ 35), so v2 AUCs on the 486 are range-restricted and not comparable to full-cohort
AUCs; deep-K cells below the annotated head depend on the v1 fill. (ii) Only 12
distinct values exist for v1 as deployed on 1,780; distinct-count comparisons here use
the common 486 (v1 = 11 there). (iii) The utility-precision claims lean on the wave-2
control screen (n=72, current-day label-only evidence); its own CIs are wide
(FOUNDER_EVIDENCE 25.8%, CI 11.9–44.6%). (iv) One structural leak class remains by
design: repo *stems* stay readable (e.g. `USER/socratica`), and distinctive project
names are searchable identity for a determined annotator — same trade-off Pod B
accepted; digests would be judgment-free without them.

*Artifacts: `data/pilot/annotations_v2.parquet` (486 rows, incl. `rank_evidence`),
`data/pilot/v2_digests.parquet` (486 masked digests + n_user_orgs),
cache `data/cache/pilot_annotations_v2/` (486). Eval:
`uv run python -m vc_brain.pilot.eval_v2`. All digests pre-t_cutoff event text only;
no current-day data enters any annotation. 2026-07-19.*
