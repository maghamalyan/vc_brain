# The Deep Program: Measuring Founding Before It Is Visible

The question worth answering — the one the brief calls industry-defining — is not
"can we rank founders above matched controls." It is:

> **What is the observable structure of the founding process in public behavioral
> traces, how early does each layer of signal appear, and what does each layer buy
> you in precision at what lead time?**

Everything below is organized around producing one defensible scientific object:
the **lead-time × precision frontier, per signal family** — a chart that says
"with counts alone you get X precision at 12 months; adding semantic trajectory
annotations buys you Y at 15 months; adding team-formation graph signals buys you
Z at 18 months." Nobody has published this. It is buildable with our
infrastructure, patience, and discipline.

## Design stance

- **Depth cohort, not width.** Freeze `Cohort-D`: the ~800–1,200 of our 2,052
  resolved founders with substantive pre-founding public presence (≥50 pre-cutoff
  events), plus 5:1 controls matched *exactly* on tenure-month, activity decile,
  primary event mix, and first-seen cohort — matching strict enough that maturity
  is dead as a confounder by construction, not by statistical adjustment.
  The wide cohort stays as a baseline comparator; "what did depth buy over width"
  is itself a reported result.
- **Observability boundary measured, not assumed.** First deliverable: of all YC
  founders in our window, what fraction even *have* meaningful pre-founding public
  traces? That number is the honest denominator of the entire approach and defines
  where the inbound track must take over from the outbound detector.
- **Every instrument validated before use.** No feature enters the model without
  a measurement-quality story (agreement with human annotation, stability, split
  discipline). Pre-registered metrics per experiment; the null-gate culture from
  tonight extends to every phase.

## Pillar 1 — The semantic trajectory (LLM as measurement instrument)

Replace "count events" with "read the work." For every Cohort-D person-month,
a versioned annotation pipeline (fixed strong model, fixed rubric, cached,
reproducible) reads the person's own timestamped artifacts — issue/PR titles and
bodies, commit messages, repo names, org joins — and produces a structured
monthly record:

- `building_what`: category + free description of the dominant project
- `audience_orientation`: self / other-developers / end-users / customers (the
  gradient from tinkering toward product)
- `productization_markers`: docs, CI, licenses, versioning, onboarding language,
  deployment — the observable costs someone pays only when they intend others to use it
- `commercial_language`: users, pricing, launch, feedback loops (graded, not regex)
- `seriousness/polish`, `novelty vs. derivation`, `collaboration posture`
- `stated intent`: any explicit first-person statements about starting something

The **time series of annotations** is the feature stream: onset, acceleration,
and *composition shifts* (tinkering→product, solo→team, consuming→shipping).

Instrument validation: I hand-annotate a stratified sample of person-months
(blind to outcome); report model–human agreement per field; fields below
agreement threshold are dropped or merged. Annotation runs strictly on
event-time text — never on today's profiles or READMEs (post-outcome
contamination), with deleted-content survivorship measured and reported.

## Pillar 2 — Team formation and social structure (the graph)

Founding is social; the strongest documented gestation signal is co-founder
pairing, and the strongest environmental signal is exposure to founding.

- Temporal collaboration graph around Cohort-D (co-commits, co-issues, review
  interactions, org co-membership), ±2 hops, monthly snapshots.
- Measured constructs: **new-strong-tie onset** with skill-complementary partners
  (the CEO-meets-CTO event, observable as sudden sustained co-activity on a fresh
  repo); **exposure**: prior collaboration with people who later found (peer
  effects / Klepper spawning); **network position shifts** (brokerage, community
  detachment — leaving a big project's gravity well).
- Substrate: the Neo4j multi-signal person-spine (this is where that stretch goal
  becomes load-bearing rather than decorative).

## Pillar 3 — Outcome depth (beyond "got into YC")

Model founding as the multi-stage process it is, with a **founding-event
ontology**: stated intent → gestation (sustained own-project work) → team
formation → incorporation/financing (SEC Form D — structured, dated, free) →
launch (Product Hunt / Show HN) → recognition (YC and other accelerator
directories). Each stage gets observed dates where public, explicit censoring
where not.

Modeling upgrade to match: **discrete-time multi-state survival** with
time-varying covariates and person-level frailty, instead of binary
classification — hazard of *entering gestation*, separately from hazard of
*recognition given gestation*. This decomposes the claim cleanly: how much of
"we found them first" is finding gestation early, versus predicting who gets
recognized. Right-censoring handles "still gestating" and "founded but never
recognized" honestly — they stop being silent false negatives.

## Pillar 4 — Identity as a probabilistic object

Cross-source person spines (GitHub ↔ HN ↔ Form D officers ↔ accelerator
directories ↔ arXiv) built by LLM-assisted entity resolution that outputs a
**match probability with cited evidence**, not a boolean. Identity uncertainty
propagates into every downstream claim (a memo claim inherits the weakest link
in its evidence chain — this generalizes tonight's per-claim Trust Score into a
principled chain). Human-audited match samples per source pair, as we did for
YC↔GitHub (48/50), become the calibration data for the match model itself.

## Pillar 5 — Evaluation that supports the actual claim

1. **Frozen-clock prospective simulations** as the primary benchmark: stand at
   2019-06, 2021-06, 2023-06 with data truncated to that instant; emit a top-K
   sourcing list from the full population pool (hash-sampled, not case-control);
   measure realized founding/recognition over the following years. Deliverables:
   absolute top-of-funnel precision, lift over population base rate, regime
   stability across the three vintages, and the false-positive portrait (who do
   we surface that never founds — and are they *interesting* false positives?).
2. **The frontier chart**: ablation grid of signal families (counts / semantic
   trajectory / graph / cross-source) × detection-lead horizons, all under the
   frozen-clock protocol. This is the headline scientific artifact.
3. **Attribution adjudication**: for a sample of detections, the model's "why"
   (SHAP + annotation deltas) is blind-reviewed by humans against the evidence:
   would a competent sourcer cite the same reasons? Construct validity, measured.
4. **Honest uncertainty**: conformal prediction intervals per person (distribution-
   free), calibration under 0.5/1/2% base-rate assumptions, and explicit
   Goodhart analysis — which features are gameable once the detector is known,
   and what the gaming-resistant core (costly signals: sustained shipping,
   real collaborators, external adoption) actually is.

## Pillar 6 — The living system

The science feeds the product: weekly re-scoring on the live stream (data source
is current to yesterday), crossing alerts carrying their attribution and
evidence chain, memos generated at crossing with per-claim trust, Founder Score
persisting across ventures (the brief's Memory requirement, genuinely). The
demo stops being a backtest page and becomes: *"here are the people our system
flagged this month, here is why, here is the full evidence — check back next
batch season."* A standing, falsifiable prediction is the strongest credibility
move available to this project.

## Sequencing (each phase gated, in the overnight tradition)

1. **Foundation** — Cohort-D freeze, observability boundary, multi-source outcome
   panel, identity spine v1.
2. **Instruments** — annotation pipeline built + human-validated; graph built;
   matching tightened to exact strata.
3. **Models** — multi-state hazard with the new feature families; GBDT baseline
   retained as the bar every richer model must clear under identical splits
   (anything that can't clear it is an appendix, including TGNs).
4. **Evaluation** — three frozen-clock vintages; frontier chart; adjudication
   study; uncertainty layer.
5. **Living system** — continuous scoring, standing predictions, dashboard
   integration.

## What this program deliberately refuses

- Scraping LinkedIn/X against ToS (also: fragile, gameable, and legally fatal
  for a real fund).
- Post-outcome text as backtest features (today's bios/READMEs describe the
  outcome, not the antecedent).
- More sources before instrument quality (each new source enters only with a
  validated identity-match model and its own audit).
- Metrics that can't survive an adversarial reviewer: every headline number
  ships with its null, its censoring story, and its base-rate assumption.
