# Repo Privatization/Deletion as Signal (Pod G, wave-3, 2026-07-19)

**Question (user hypothesis).** "If you want to make a product from your project, you
take it private" — so repo disappearance may itself be founder signal. Wave-2 Pod D
measured 22.6% of 907 pre-cutoff-created repos now 404 and found it class-flat overall,
but never sliced it. Three framings, strictly separated by data basis, all on the same
population: the 907 own repos (created pre-cutoff) of the 188 commit-depth sample actors
(93 founders / 95 controls, top-region, gestation-enriched — *not* a random cohort
slice; all rates below are for this population).

**Method.** Framing 1 joins `data/pilot/commit_repo_status.parquet` (live-API 404
snapshot, 2026-07-19) with the sample's annotations. Framings 2–3 use a new playground
extraction: monthly event counts (`count()`, `countIf(PushEvent)`, `uniqExact(actor)`)
per repo over the repo's whole life, `repo_name IN` batches of 200, serial, extract.py
request pattern (FORMAT Parquet), 5 batches cached under `data/cache/privatization/` →
`data/pilot/repo_monthly_events.parquet` (4,931 repo-months, 907/907 repos matched,
data horizon 2026-07). Derived flags in `data/pilot/privatization_repo_flags.parquet`,
with per-column data basis declared in `privatization.COLUMN_DATA_BASIS`
(pre_cutoff_events = feature-safe; post_cutoff_events = label/outcome only;
current_day = label/triage only). CIs are Clopper-Pearson 95%; p-values Fisher exact.
Code: `src/vc_brain/pilot/privatization.py` (new module; shared modules untouched).
No LLM calls; ~55 B playground rows read across 5 serial queries, one quota window.

## Framing 1 — triage/label-side slicing (data_basis=current_day)

Dead = live API 404 on 2026-07-19 (conflates deleted and made-private; renames
redirect and count alive).

| slice | founders dead | controls dead | Fisher p |
|---|---|---|---|
| overall | 96/444 = 21.6% [17.9–25.7] | 109/463 = 23.5% [19.7–27.7] | 0.53 |
| gestation ≥70 | 21/126 = **16.7%** [10.6–24.3] | 32/129 = **24.8%** [17.6–33.2] | 0.12 |
| gestation 35–69 | 20/55 = 36.4% [23.8–50.4] | 20/60 = 33.3% [21.7–46.7] | 0.85 |
| gestation <35 | 55/263 = 20.9% | 57/274 = 20.8% | 1.00 |
| main repo (most-active) | 20/93 = 21.5% | 18/95 = 18.9% | 0.72 |
| side repos | 76/351 = 21.7% | 91/368 = 24.7% | 0.33 |
| created <6 mo before cutoff | 8/43 = 18.6% | 5/27 = 18.5% | 1.00 |
| created <12 mo before cutoff | 13/71 = 18.3% | 16/86 = 18.6% | 1.00 |
| created ≥12 mo before cutoff | 83/373 = 22.3% | 93/377 = 24.7% | 0.44 |

The user-hypothesis cells directly:

| cell | founders dead | controls dead | Fisher p |
|---|---|---|---|
| gestation ≥70 AND created <12 mo | 2/19 = **10.5%** | 7/28 = **25.0%** | 0.28 |
| gestation ≥70 AND created <6 mo | 1/11 = 9.1% | 3/10 = 30.0% | 0.31 |
| gestation ≥70 AND main repo | 6/25 = 24.0% | 6/24 = 25.0% | 1.00 |
| g≥70 AND main AND created <12 mo | 1/5 = 20.0% | 2/6 = 33.3% | 1.00 |

**Verdict: the hypothesis is directionally inverted at the current-day level.** Founder
gestation repos created near cutoff are *less* often dead than controls' equivalents
(10.5% vs 25.0%), and high-gestation founders' repos die less overall (16.7% vs 24.8%,
p=0.12) — consistent with Pod D's suggestive note: the founder's gestation repo becomes
the company's repo and *survives* (often migrating to an org); controls' experiments get
cleaned up. Nothing reaches significance; no slice is founder-enriched. Current-day 404
is useless as founder triage on this sample. One real pattern both classes share: the
mid-gestation band 35–69 has the highest death rate (~35%) — half-serious projects are
what gets deleted.

## Framing 2 — outcome-stage marker (post-cutoff GH Archive events, label use only)

Definitions: `active_pre6` = ≥5 events in the 6 months before cutoff (125/907 repos);
silent-within-X = last event (any actor) < cutoff+X months with ≥3 months of observed
silence before the 2026-07 data horizon (censoring guard); candidate =
active_pre6 AND silent AND 404 today; `hot_at_death` = ≥10 events in the 3 months up to
the last event (separates privatized-while-alive from long-tail abandonment).

| measure | founders | controls | Fisher p |
|---|---|---|---|
| candidate (silent<6 mo), all repos | 7/444 = 1.6% | 4/463 = 0.9% | 0.38 |
| candidate (silent<6 mo) \| active-pre repos | 7/51 = **13.7%** [5.7–26.3] | 4/74 = **5.4%** [1.5–13.3] | 0.12 |
| candidate (silent<12 mo) \| active-pre | 7/51 = 13.7% | 6/74 = 8.1% | 0.38 |
| … AND hot at death \| active-pre | 5/51 = 9.8% | 4/74 = 5.4% | 0.48 |
| actor has ≥1 candidate (12 mo) | 6/93 = 6.5% | 6/95 = 6.3% | 1.00 |
| dead AND active_pre6 (any silence timing) | 8 repos | 8 repos | — |

Timing of death for all 205 404-repos (last event month relative to cutoff): founders
median **−32 mo** (p25 −41, p75 −14), controls median −28 mo; only 4.2% / 6.4% have any
post-cutoff event. **Repo deletion is overwhelmingly cleanup of long-dead side projects,
not productization** — that is why Pod D's aggregate was flat. Only 5.4% of dead repos
have any post-cutoff event vs 26.9% of alive repos.

But the rare privatized-while-alive species exists, is datable, and is exactly
founder-shaped — on *both* sides of the label. The 13 silent<12-mo candidates:

- **Founders (7 repos / 6 actors):** leonard-henriquez/node-api-boilerplate (g≥70,
  main repo, 254 pre-cutoff events, silent at month **−1**, hot at death);
  qionghuang6/journey-backend + journey-hackmit (a hackathon-project pair, both silent
  at **−3**, hot); kcelebi/CGDC-web (main, −1); jw122/energy-data (−2, hot);
  albertjo/tacticalstrength (−2); anthonykrivonos/dallefy (−3, hot). Estimated
  privatization months cluster at **−3 to 0 relative to cutoff** — the repo goes dark
  hot right at the batch boundary: gestation → productization, dated.
- **"Controls" (6 repos / 6 actors), cross-checked against the wave-2 label-noise
  screen:** senalbulumulle/FOIL-UI-Framework-Library (g=85, main, 446 events, silent
  at month **0**, hot at death) — the screen independently confirmed him
  FOUNDER_EVIDENCE ("Founder: FOÏL", https://github.com/senalbulumulle): a textbook
  privatized-at-productization case sitting in the control pool.
  jwetzell/showbridge (g=85, main, 2,229 events, silent at **+20**, hot) — one of the
  portrait's four hand-labeled meet-worthy profiles. cuhong/chadirect_web (g=75, main,
  376 events, silent at **+8**, hot) — the current-day screen returned NO_EVIDENCE
  (empty profile), yet the event timeline is product-shaped; a sourcing candidate the
  profile screen cannot see. The remaining three (hwakabh, mfreeborn, qwqdanchun,
  telk5093 in the 6-mo variant) are ordinary abandonments or, for qwqdanchun,
  security-tooling release channels.

**Verdict: real as a founding-ontology stage, useless as a label discriminator.** The
marker "gestation repo goes permanently silent while hot within ~±12 months of cutoff
and is 404 today" identifies a dated productization transition (privatization month =
last-event month, a tight upper bound since GH Archive silence begins at privatization),
and at repo level it is ~2.5× founder-leaning among active repos (13.7% vs 5.4%,
p=0.12, n=125). It never reaches actor-level separation (6.5% vs 6.3%) because the
controls it fires on are disproportionately *unlabeled founders* — 3 of the 6 control
candidates are confirmed-founder / meet-worthy / product-shaped per independent
evidence. Propose it to the ontology as: `gestation → productization(privatized)`,
with `privatization_month` = last-event month; and route every control it flags into
the label-repair/sourcing queue rather than the negative pool.

## Framing 3 — leakage-safe feature probe (pre-cutoff events only)

"Went dark while hot" = own repo with ≥10 events (all actors, all types) in some
3-month span pre-cutoff AND zero events in the last 3 months before cutoff.

| measure | founders | controls | Fisher p |
|---|---|---|---|
| repo hot pre-cutoff (≥10 ev/3 mo) | 229/444 = 51.6% | 271/463 = 58.5% | 0.038 |
| repo went dark while hot | 178/444 = 40.1% | 202/463 = 43.6% | 0.28 |
| actor has ≥1 dark-while-hot repo | 70/93 = 75.3% [65.2–83.6] | 75/95 = 78.9% [69.4–86.6] | 0.60 |

Correlation with gestation (actor level): flagged actors' median gestation 25 vs 15;
point-biserial r = 0.25, p = 0.0005 — the flag tracks "once had an intense project"
(which gestation also tracks), and by band: <35 → 68.6% flagged, 35–69 → 100%,
≥70 → 87.8%.

What the flag actually proxies (current-day/post-cutoff diagnosis only,
data_basis=current_day): of the 380 flagged repos, **24.5% are 404 today vs 21.3% of
non-flagged** — barely enriched — and 17.1% resume activity post-cutoff. So going dark
pre-cutoff is overwhelmingly ordinary abandonment or dormancy, only marginally
predictive of eventual deletion, and slightly *control*-leaning on the label.

**Verdict: not worth adding as a model feature.** Prevalence is near-universal (3 in 4
actors), the class direction is wrong-way and non-significant, and the current-day
cross-check confirms it proxies abandonment, not privatization. The one usable
pre-cutoff observation is the mirror image already implicit in the count model:
founders' repos are slightly less likely to be hot-then-dark because their hot repo is
still hot at cutoff.

## Where the signal belongs (final placement)

| framing | data basis | verdict |
|---|---|---|
| current-day 404 dead-share | current_day | **nowhere** as triage — class-flat to inverted in every slice; if anything, survival of a high-gestation recent repo is the founder-leaning direction (ns) |
| privatized-while-alive marker | post_cutoff_events + current_day | **outcome stage** — adopt `productization(privatized)` with dated privatization month into the founding ontology; label-repair trigger for flagged controls (senalbulumulle-class). Not a classifier feature (leakage) and not an actor-level discriminator (label noise absorbs the enrichment) |
| went-dark-while-hot | pre_cutoff_events | **nowhere** as feature — near-universal, wrong-way, proxies abandonment |

The honest summary of the user's hypothesis: privatization-at-productization is *real
and observable* — four main repos in this sample (leonard-henriquez, senalbulumulle,
cuhong, jwetzell) go permanently silent while still hot and are 404 today, two of them
within a month of cutoff, one belonging to a confirmed unlabeled founder — but it is rare
(~5% of active repos, ~6% of actors even in this gestation-enriched sample), its
timing makes it label-side by construction (the event *is* the outcome), and aggregate
repo death is so dominated by junk cleanup (median death 2.5 years before cutoff) that
no current-day or pre-cutoff proxy of it carries class signal.

## Caveats

- All rates are for the gestation-enriched top-region commit-depth sample (188 actors,
  907 repos), not the full cohort; absolute prevalences will differ cohort-wide.
- n is small everywhere it matters: the key framing-2 contrast is 7/51 vs 4/74
  (p=0.12); a cohort-scale replication (all annotated actors' own repos, ~1 extra
  quota window) would settle it.
- 404 conflates deleted with made-private; GH Archive silence for *alive* repos can
  also be a rename (events continue under the new name), which inflates apparent
  dormancy/resumption noise in framing 3 but cannot create false 404s in framing 2.
- Last-event month under-dates privatization when a repo idles publicly before being
  removed; for hot-at-death candidates the bound is tight, for others it is loose.
- Late cutoffs (2025-01/04/06) have <24 months of post-cutoff observation; the
  ≥3-month silence guard prevents false "permanent silence" but right-censors
  very recent privatizations.
- Framing 2's marker consumes post-cutoff events and current-day status: it must never
  be computed at feature time; it exists to date an outcome stage and repair labels.

*Artifacts: `data/pilot/repo_monthly_events.parquet` (4,931 rows),
`data/pilot/privatization_repo_flags.parquet` (907 rows, per-column data basis in
`vc_brain.pilot.privatization.COLUMN_DATA_BASIS`). Reproduce:
`uv run python -m vc_brain.pilot.privatization` (deterministic, fully cached).*
