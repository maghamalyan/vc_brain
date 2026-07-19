# Co-Founder Pairing: Is Team Formation Observable in Public GitHub Activity Before the Batch?

**Study question.** The entrepreneurship literature (Ruef/Aldrich on team formation;
research program Pillar 2) says the strongest gestation signal is *pairing* — the
moment two people with complementary skills begin sustained joint work. Is that
moment observable in public GitHub event streams **before** the YC batch starts,
and how early?

**Method.** From `data/labels/founders.parquet`, companies in batches 2022–2026
with ≥2 founders resolved to GitHub logins at `gh_confidence ≥ 0.5`. Stratified
deterministic sample (seed 42, 8 companies per batch year) of 40 companies;
**39 completed** before the ClickHouse playground hourly quota exhausted (lost:
end-close, Winter 2026). For each company, one query against `github_events`
(GH Archive mirror at play.clickhouse.com) fetched per-login per-repo first/last
event and counts, matched **case-insensitively** on `actor_login`, upper-bounded
at `batch_start + 60d`. A single follow-up query re-pulled the same logins
restricted to *work* event types (Push, PR, Issues, comments, reviews, Create,
Release, Member — excluding Watch/Fork, i.e. stars don't count as collaboration).

**Definitions.** For a founder pair, a *shared repo* is one where both logins have
events and the *second* founder's first event predates `batch_start` (co-activity
onset = `max(first_a, first_b)`). Three tiers:

- **Any-event**: any shared repo (includes both merely starring the same repo).
- **Work-event**: shared repo on work events only.
- **Strong-tie**: work-event shared repo that is founder-owned, OR matches the
  company slug/name, OR has ≥3 work events from *each* founder.

## Headline numbers

Denominators: **39 companies, 43 co-founder pairs** (three-founder companies
contribute 3 pairs each). Lead time = days from first pre-batch co-activity onset
to `batch_start`.

| Tier | Pairs with pre-batch co-activity | Median lead | IQR | Lead > 6 mo | Lead > 12 mo |
|---|---|---|---|---|---|
| Any event | 28/43 (65.1%) | 626 d | 328–1,989 d | 23/43 (53.5%) | 20/43 (46.5%) |
| Work events only | 25/43 (58.1%) | 505 d | 159–801 d | 18/43 (41.9%) | 14/43 (32.6%) |
| Strong-tie repo | 25/43 (58.1%) | 460 d | 129–566 d | 16/43 (37.2%) | 13/43 (30.2%) |

Additional measurements:

- **16/43 pairs (37.2%)** had a pre-batch shared repo whose name or owner matches
  the company slug/name — i.e. the *company repo itself being born in public* is
  visible before the batch for over a third of resolved pairs.
- Among the 28 any-event co-active pairs, **82.1%** (23/28) had first co-activity
  more than 6 months before batch start.
- Only 3/43 pairs were star/fork-only (co-"activity" that vanishes under the work
  filter): HockeyStack S23, Conductor Quantum S24, Third Chair Sp25. The signal is
  overwhelmingly real collaboration, not co-starring.
- 15/43 pairs (34.9%) had **zero** observable pre-batch co-activity of any kind.
- By batch year (pairs work-co-active / total): 2022: 7/10 · 2023: 3/8 ·
  2024: 8/10 · 2025: 2/8 · 2026: 5/7. No monotonic trend; the 2023/2025 dips are
  small-n noise, not a cohort effect we can distinguish.

## Five timelines (real names, real repos)

**1. Payload (Summer 2022, batch start 2022-06-01) — the company repo born 17
months early, all three pairs.** `payloadcms/payload` shows James Mikrut
(`jmikrut`) and Dan Ribbens (`danribbens`) co-active from **2021-01-05**, Elliot
DeNolf (`denolfe`) joining 2021-01-06 — 511/510 days before batch, with enormous
volume (7,182 / 6,384 / 4,953 work events pre-cutoff). `payloadcms/nextjs-custom-server`
follows Jan–Sep 2021, `payloadcms/public-demo` in May 2022. A detector watching
"fresh org + multiple sustained committers" fires in January 2021.

**2. CodeCrafters (Summer 2022) — a nine-year-old tie, then the company org.**
Paul Kuruvilla (`rohitpaulk`) and Sarup Banskota (`sarupbanskota`) first co-commit
on `glittergallery/GlitterGallery` (a GNOME GSoC-era project) on **2014-03-02**
(469 and 609 work events respectively) — 8.2 years before their batch, with
another joint project (`unfurld/unfurld`) in 2017. The company org appears
pre-batch too: `codecrafters-io/languages` and four `docker-starter-*` repos show
both founders from **2022-02-09**, ~4 months before batch. Old strong tie +
fresh company org = the full pairing signature.

**3. Resend (Winter 2023) — community tie, then shared employer, then company.**
Zeno Rocha (`zenorocha`) and Bu Kinoshita (`bukinoshita`) first overlap in
Brazilian OSS: `zenorocha/generator-firefox-os` (**2016-02-07**) and
`braziljs/weekly` (2016-02-21) — 2,524 days (~6.9 years) before batch. In
2021 both appear in `workos-inc/*` repos (co-workers at WorkOS), then
`radix-ui/website` in June 2022. The pairing is visible as a *sequence*:
community → employer → venture.

**4. Didit (Winter 2026) — brothers building the product SDK 26 months early.**
Alejandro Rosas (`arosasg`) and Alberto Rosas (`rosasalberto`) co-active on
`didit-protocol/didit-sdk` from **2023-10-26** (28 and 10 work events), 802 days
before their 2026-01-05 batch start, followed by `didit-protocol/didit-demo-center`
(Jan 2025) and `didit-full-demo` (May 2025). Caveat: Didit existed as a company
well before YC — this is partly "late accelerator entry," not pure gestation
(see caveats).

**5. Navier AI (Winter 2024) — the tie formed in a student rocketry club.**
Cameron Flannery (`cmflannery`) and Evan Kay (`evankay1`) co-commit on
`rocketproplab/marginal-stability` (a university rocket propulsion lab repo) from
**2018-08-16** — 1,967 days (5.4 years) before batch. The pair later co-appears on
`Autodesk/XLB` (a lattice-Boltzmann CFD library — exactly the domain of their
CFD-simulation startup). Domain-relevant strong tie, formed in a student org,
years ahead.

Honorable mention: winfunc (S24) — Mufeed VH (`mufeedvh`) and Vivek R
(`123vivekr`) share `DNArchery/DNArchery` (Mar 2023), `mufeedvh/code2prompt` and
`stitionai/devika` (Mar 2024): serial joint projects escalating into the venture.

## Caveats (honest ones)

1. **Resolution bias is severe and first-order.** 2,173 YC companies in 2022–2026
   batches list ≥2 founders; only **202 (9.3%)** have ≥2 founders resolved at
   `gh_confidence ≥ 0.5`. Everything above is conditional on *both* founders being
   resolvable — a population that is by construction more GitHub-public and
   plausibly more likely to collaborate in public. The 58–65% observability rate
   does **not** transfer to the general founder population; the unconditional
   rate over all multi-founder companies could be an order of magnitude lower.
   `docs/exploration/missed_founders.md` is the complement study: among 16
   strong-outcome founders the detector missed, co-founder co-commits were still
   visible in 6/16 — so pairing survives even in the miss pool, but nothing close
   to 60%.
2. **Case sensitivity**: `actor_login` was matched case-insensitively
   (`lower()` on both sides); without this, mixed-case logins silently drop out.
3. **Low-confidence resolutions included**: `gh_confidence ≥ 0.5` admits some
   misresolved logins. A wrong login almost always produces false *negatives*
   (no co-activity found), so the observability rates are, if anything, deflated
   within the resolved population.
4. **"Before the batch" ≠ "before founding."** Several companies (Payload, Didit,
   NewsCatcher) existed for a year-plus before YC; part of the long lead is late
   accelerator entry, not detection ahead of gestation. Against the *batch* as
   the recognition event the leads are real; against incorporation they would
   shrink. The right target ontology is the multi-stage one in the research
   program (Pillar 3).
5. **Private repos are invisible.** Teams gestating in private show zero
   co-activity until they flip public; the 34.9% with no observable co-activity
   mixes "no pairing signal exists" with "pairing happened in private." Rates
   here are lower bounds on collaboration, upper bounds on what a public-only
   detector can see.
6. **Small sample**: 39 companies / 43 pairs, one company (end-close, W2026) lost
   to the shared query quota. CIs on the headline percentages are ±15pp.
7. **Co-activity onset resolution**: onset = the second founder's first event on
   a shared repo, at event timestamp resolution; a repo shared only via issues on
   a huge third-party project can still slip through the strong-tie filter if
   both founders were heavy contributors (e.g. Chordio's `paperjs/paper.js` — a
   genuine but pre-existing collaboration context).

## Verdict: is "new strong-tie onset" viable as a detector feature?

**Yes — it is the single most promising feature this program has measured so
far, with two sharp qualifications.**

Within the doubly-resolved population, a majority of founder pairs (58% on work
events) are co-active in public *before* the batch, with a median lead of ~15
months, and 37% of pairs show the company repo itself being born. The signal is
concrete collaboration, not co-starring (only 3/43 pairs vanish under the work
filter). The qualifications: (a) it covers at most the ~9% doubly-resolved slice
directly — as a *feature* it must be defined person-centrically so it fires from
one resolved person's stream; (b) this study measured founders only — the
discriminative value depends on how often *non*-founder pairs exhibit the same
onset pattern (Pillar 2's matched-control job, not answered here).

**Proposed feature definition** (person `p`, month `t`, computable from `p`'s own
event stream ≤ `t`):

> `new_strong_tie_onset(p, t)` = 1 if there exists a counterpart `q` such that:
> (i) `p` and `q` each have ≥3 work events (Push/PR/Issue/review/Create) within a
> 90-day window ending at `t` on a common repo `r`; (ii) `r` is owned by `p`, `q`,
> or an org created within the past 12 months (fresh venue — excludes long-running
> employer/OSS venues); (iii) `p` and `q` had no common-repo work events in the
> 24 months before the window (the tie is *new*, or newly reactivated).
> Auxiliary continuous features: days since onset, joint event volume, venue
> freshness, and whether `q`'s skill mix complements `p`'s (event-type/language
> divergence).

The "fresh venue" clause is what separates Payload-in-Jan-2021 from two
colleagues grinding on their employer's monorepo, and the reactivation window is
what lets CodeCrafters (2014 tie, 2022 fresh org) fire in February 2022 rather
than being suppressed by tie age.

**Artifacts**: raw per-company query results, pair-level table, and scripts in
the session scratchpad (`cofounder/results.json`, `pairs_final.json`,
`run_queries.py`, `analyze2.py`); sample is reproducible from
`data/labels/founders.parquet` with seed 42, 8 companies per batch year.
