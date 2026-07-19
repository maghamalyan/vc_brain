# Missed Founders: What Strong Outcomes Look Like When the Detector Can't See Them

**Study question.** Our behavioral detector ranks people by pre-batch public GitHub
activity counts. This study takes 16 founders with strong outcomes (acquisitions,
unicorns, scaled companies) whom the detector scored at or near its floor
(peak score 0.186, the base-rate prior — or null), and asks two things:

1. *Why* were they invisible — what are the failure modes, and which are
   measurement failures versus genuine observability limits?
2. After excluding the oversubscribed prestige markers everyone already prices in
   (elite school, SF address, FAANG employer, the accelerator badge itself), does
   any **non-obvious network signal** remain in the public record — and is it
   feature-izable without leaking post-hoc knowledge?

Every portrait was built from the repo's event extracts
(`data/events/monthly_agg/positives.parquet`, `data/labels/founders.parquet`)
plus live `gh api` reconstruction; all evidence cited below is a public URL or a
local data row. Prestige markers were recorded for each founder but deliberately
excluded from the signal analysis.

---

## 1. Taxonomy of misses

Tags are non-exclusive; the table gives the primary cause per founder. Outcomes
abbreviated (all verified in portraits with sources).

| Login | Company (outcome) | Primary miss cause | Secondary | Profile strength | Network signal |
|---|---|---|---|---|---|
| priyanka-galen | Galen AI (acq. Oura) | identity resolution miss (matched a company handle created 12 days *post*-batch) | real account unlinked | 1 | yes — co-founder co-commits |
| christos-fal | Remade (acq. fal) | identity resolution miss (handle created 15 months post-batch) | fully private team | 0 | no |
| kietay | Midship (acq. Optro) | private work (Amazon/Instacart) | activity collapse before window | 1 | yes — elite-maintainer acceptance |
| bluejayio | Verse Therapy (acq. Beaming) | private work (Google/Amazon) | 4 forks, 3 commits lifetime pre-batch | 1 | no (fork-contaminated co-actors only) |
| raghavpillai | Speck (acq.) | window truncation (2023 ramp after t_cutoff) | private work (Anduril/Amazon) | 2 | yes — one-hop to live YC company |
| rohan-mehta | Arcane (acq.; → OpenAI) | private work (9 yrs Meta + private startup org) | activity but no ownership (issues only) | 1 | yes — maintainer-response graph |
| brgmry | Throxy (scaled, 55 ppl) | non-technical founder, no owned public code | only code sat in co-founder's repo, post-cutoff | 1 | yes — co-founder co-commit sprint |
| ddmkr | Conveo (scaled, $5.3M seed) | private work (13 yrs DataCamp CTO) | public residue in org-owned repos | 1 | yes — high-caliber co-contributors |
| hendrikvanhove01 | Conveo | non-technical founder (ex-McKinsey), 5 lifetime events | private build | 0 | partial — one-join co-founder edge |
| barmstrong | Coinbase (Nasdaq, ~$47–76B listing) | low public volume, private day job (Airbnb) | ~40 issues/PRs total | 2 | yes — Bitcoin-implementers graph |
| nateps | Lever (acq. Employ) | window truncation (GH Archive starts 2011-02; cutoff 2011-06) | org-owned repos (derbyjs), zero personal ownership | 3 | yes — co-founder parity co-commits |
| georgewfraser | Fivetran (~$5.6B) | one solo academic repo; OSS reputation entirely post-founding | co-founder never resolved | 1 | no |
| matinm | Heap (acq. Contentsquare, $960M peak) | non-technical founder (Facebook PM), zero public events | first public act days *after* batch start | 0 | no (follow edges undatable) |
| callmevlad | Webflow ($4B) | activity but no ownership (~18 events, all on others' repos) | private prototype + Intuit | 1 | yes — thematic neighbor coherence |
| shashankkumar | Razorpay ($7.5B) | private work; build phase 2 yrs before cutoff, then only watches | recency weighting killed the real repo | 2 | yes — repo fork/collaborator graph |
| gwintrob | Newfront (acq. WTW, $2.2B val.) | private work (LinkedIn post-acquisition); zero rows in window | activity predates window | 1 | yes — co-founder + elite peer co-commits |

**Aggregated cause counts** (non-exclusive tags across 16):

| Cause tag | Count | Founders |
|---|---|---|
| Private/corporate work (real output behind a firewall) | 11 | kietay, bluejayio, raghavpillai, rohan-mehta, ddmkr, hendrikvanhove01, barmstrong, matinm, callmevlad, shashankkumar, gwintrob |
| Activity but no *ownership* (code landed in org- or others' repos) | 5 | nateps, rohan-mehta, callmevlad, brgmry, ddmkr |
| Window/cutoff truncation (signal exists, outside the aperture) | 4 | raghavpillai, nateps, gwintrob, brgmry |
| Own-identity resolution failure (scored the wrong/empty account) | 2 | priyanka-galen, christos-fal |
| Non-technical founder (PM/business side) | 3 | matinm, brgmry, hendrikvanhove01 |
| Academic-only public code | 1 | georgewfraser |

**A recurring secondary failure worth its own line: co-founder resolution misses.**
In at least 6 of 16 portraits, the *other* co-founder's login was unresolved or
mis-resolved in `data/labels/founders.parquet`, destroying the strongest edge in
the graph: viraj28m (Galen — dropped at 0.2 to a namesake), bnoguchi (Lever —
gh_login=NaN), harshilmathur (Razorpay — null), tedjt (StackLead — NaN),
Taylor Brown (Fivetran — 0.2, confused with the YNAB founder), arnau01 (Throxy —
unresolved in labels, recovered here via the veducato contributor list). The
Galen team was mis-resolved *twice on a two-person team*. Identity resolution is
not a preprocessing detail; it is where roughly a third of the recoverable
signal died.

**own_profile_strength distribution** (0 = nothing public, 3 = strong own profile):

| Strength | Count | Share |
|---|---|---|
| 0 | 3 | 19% |
| 1 | 9 | 56% |
| 2 | 3 | 19% |
| 3 | 1 | 6% |

Three-quarters of these strong-outcome founders had own-profile strength ≤1:
the miss is usually not "we underweighted their profile" but "there was almost
no profile to weight." What remained, when anything remained, was relational.

---

## 2. The network findings

**Headline count: 12 of 16 portraits show a genuine pre-batch network signal in
public GitHub data; 4 show none** (christos-fal, bluejayio, georgewfraser,
matinm — all honest absences, documented as such rather than backfilled). One of
the 12 (hendrikvanhove01) is a degenerate but actionable case: the signal is a
single join in our own labels table (his co-founder is ddmkr, ex-DataCamp CTO),
not an event-graph edge.

The 12 split into two families:

- **Co-founder-pair formation visible in the commit graph** (6): the founding
  team was publicly co-building before the batch, under logins we failed to
  connect — priyanka-galen, brgmry, nateps, shashankkumar, gwintrob, raghavpillai
  (one hop).
- **Upward embedding / counterparty quality** (5-6): low-volume accounts whose
  few events landed with, or drew responses from, unusually strong builders —
  kietay, rohan-mehta, barmstrong, callmevlad, ddmkr.

### Five most concrete examples

**1. priyanka-galen / Galen AI — the founding pair co-committing 7 months pre-batch.**
Her real account (Priyankas007, not the ghost we scored) co-committed with
viraj28m — Viraj Mehta, her future CEO — on `mover_pressors`, ICU vasopressor
prediction on the MOVER clinical dataset, Aug 19–Sep 5 2024
(github.com/Priyankas007/mover_pressors/commits). In Jan 2025 both submitted
patient-chart Swift apps for Stanford CS342 "Building for Digital Health" —
essentially prototyping Galen's product (patient records in an app, later
acquired by Oura) as coursework three months before the batch. Two-sided
signal: a formed clinical-ML + quant founding pair *and* the product thesis,
both legible in public repos. We missed it because both handles were
mis-resolved.

**2. nateps / Lever — eleven months of commit parity with the future co-founder.**
From 2011-06-27 to 2012-05-30, nateps and bnoguchi co-committed at near parity
on derbyjs/racer (752 vs 836 commits; `gh api repos/derbyjs/racer/commits`).
Brian Noguchi — author of everyauth (3.5k stars) — became his Lever co-founder
and later a second-time YC founder (Smartcuts W21). The pre-batch issue queues
drew dominictarr and Raynos, and future Express.js lead maintainer dougwilson
committed to nateps' personal connect-gzip in Jan 2012. None of it was countable:
the collaboration lived under an org, and the co-founder's login was never
resolved.

**3. brgmry / Throxy — a non-technical founder's single loud weekend.**
Bergen Merey's *only* pre-batch public code is 31 commits on Oct 5–6, 2024 in
arnau01/veducato — a 54-commit, two-person, 36-hour sprint prototyping
ElevenLabs voice agents with Arnau Ayerbe Garcia, who became his Throxy
co-founder six months later (contributors API: brgmry 31, arnau01 23; repo
created 2024-10-05, batch start 2025-04-01). Voice agents are the exact domain
Throxy (now 55 people, Base10-backed) sells. The detector saw `__NO_ACTIVITY__`
because the repo belonged to the other founder and the sprint post-dated the
feature cutoff.

**4. shashankkumar / Razorpay — one niche repo encoding the whole founding graph.**
CodeRunner, his C++ online judge (68 stars, 25 forks, built for IIT Roorkee's
Insomnia'12 contest), assembled the future company years early: Harshil Mathur —
future co-founder/CEO, unresolved in our labels — created a GitHub account on
2011-12-26 and forked CodeRunner **40 seconds later**
(fork created 2011-12-26T15:06:54Z vs account 15:06:14Z; github.com/harshilmathur/CodeRunner).
captn3m0 (2,095 followers; later ran security/infra/OSS at Razorpay) forked it
in Aug 2011. When Shashank went quiet in 2013 he handed maintenance to
shagunsodhani — 62 commits Jun 2013–Aug 2014, later a Facebook AI Research
engineer. The detector saw a fading starrer; the repo's orbit contained the
co-founder of a $7.5B company, its first key infra hire, and a future top-lab
researcher.

**5. raghavpillai / Speck — one collaboration hop from a live YC company.**
His own window activity was ~90 events of 0–1-star hackathon projects. But his
co-founder Lucas Jaggernauth (lukejagg), from the same UT Dallas hackathon
circuit, was the **#3 all-time contributor to sweepai/sweep** (1,398 commits
from 2023-06-26), co-committing daily through H2 2023 with Kevin Lu and William
Zeng — YC S23 founders present in our own labels file. Sweep was already a
recognized YC company at prediction time, which makes this edge *backtest-legal*
(see §3b). Secondary: a stable repeat crew around Raghav (KanishkGar in 4
shared repos over 13 months; NikhilNarvekar123, ex-SpaceX/AWS, in 3) — strong
engineers repeatedly choosing to build with him.

### The counterparty-quality family (briefly)

- **kietay**: three student PRs merged by elite maintainers — spotify/scio #2290,
  #2388 (merged by Scio creator nevillelyh and maintainer regadas) and
  rrousselGit/provider #460 (7.6k-follower author). Quality-of-acceptance, not volume.
- **rohan-mehta**: 11 pre-batch issues, each answered at maintainer level —
  Meta's PyTorch partner engineer (llama-cookbook PR #106), a FAIR DINOv2
  maintainer (#204), Stainless founder rattrayalex personally (openai-python
  #874), PostHog's SDK lead (posthog-flutter #63). Strangers of that caliber do
  not answer noise; read in sequence the issues trace Arcane's private build.
- **barmstrong**: bitcoin-android's top contributor was brandoniles (ex-Google
  Search Ranking, later Ampleforth co-founder); MultiBit's creator gary-rowe
  filed expert feature requests within 48 hours of launch; protocol PRs merged
  by lian (bitcoin-ruby) in the five pre-batch months. Embedded in a global
  implementer community of perhaps a few dozen people.
- **callmevlad**: ~18 events, but essentially **100% of his sparse edges point
  at authors of in-browser visual-editing tools** — jstayton's list-input
  widgets (merged PR, 14-month dialogue), bergie's Hallo/Create.js, Mercury
  Editor, select2 PR #835 four months pre-batch. Thematic coherence plus
  counterparty quality, while privately building Webflow from exactly that
  component category.
- **ddmkr**: ~30 windowed events, but 21 commits into ronreiter/interactive-tutorials
  (learnpython.org, 4.7k stars; Reiter later CTO/co-founder of Sentra) and
  co-builds with ncarchedi (creator of swirl). Nearly every public event lands
  in a repo shared with a future founder or senior builder.

### Contrast with prestige markers

Every one of the 16 carries at least one oversubscribed marker — Stanford, MIT,
Cambridge, IIT Roorkee, Meta/Google/Amazon/Airbnb/LinkedIn, SF addresses, the
YC badge itself. These were recorded and excluded. The point of the exercise:
after removing them, **12 of 16 still have a discriminating public trace, and it
is almost always relational rather than volumetric** — who they built with, who
accepted their work, who showed up in their tiny repos. The prestige markers are
visible to every fund; the collaboration edges above were visible to nobody,
including our own detector.

Two cautionary anti-patterns surfaced alongside the real signals:

- **Fork contamination** (bluejayio): naive shared-actor joins attribute
  upstream committers (Cerner engineers, 2016–2018) to a 2023 fork — fake
  neighbors, five years stale.
- **Adversarial identity** (christos-fal): a 1,198-follower impersonation
  account (christosantono) wearing his real bio over 49 spam repos mass-created
  in one day. Founder-name resolution is an adversarial problem, not a fuzzy-join.

---

## 3. Implications

### (a) The detector's blind spot, honestly stated

All 16 founders scored at the model floor (0.186) or were never scored at all.
Seven of 16 had **literally zero countable pre-batch events under the resolved
login** (`__NO_ACTIVITY__` placeholder or no rows): priyanka-galen, christos-fal,
bluejayio, brgmry, matinm, hendrikvanhove01, gwintrob. The rest were low-volume
enough that no count threshold separates them from noise.

This connects directly to the observability boundary in
`docs/research_program.md`: Cohort-D — founders with substantive pre-founding
presence (≥50 pre-cutoff events) — covers roughly 800–1,200 of our 2,052
resolved founders, i.e. **on the order of 40–60% of resolved YC founders sit
below the substantive-presence bar**, and this study shows that region is
populated by top-decile outcomes (Coinbase, Webflow, Razorpay, Heap, Lever,
Newfront), not by weak ones. Behavioral invisibility is uncorrelated with
outcome quality — if anything, the private-work mechanism (senior engineers and
repeat operators whose output moved in-house) selects *for* strength.

One important decomposition this sample allows: **not all invisibility is an
observability limit.** Of the 16:

- ~12 are, at least partially, *measurement* failures recoverable from data we
  already have — wrong-account resolution (2), unresolved co-founder edges (6+),
  org-ownership attribution (5), window truncation (4).
- ~4 are genuine observability-boundary cases with no public GitHub trace to
  recover (matinm, georgewfraser, bluejayio, christos-fal's team) — the honest
  denominator problem the research program assigns to the inbound track.

The caveat that must accompany any fraction: this sample was *selected* for
being missed with strong outcomes. It characterizes the failure modes; it does
not estimate their population rate. The observability-boundary deliverable
(research program, Foundation phase) remains the instrument for that number.

### (b) Candidate features for a network-embedding signal

Design constraint: none of these may reduce to prestige, and each must be
audited for temporal leakage. The core hazard: **"future founder" is post-hoc
knowledge.** Several portraits are narrated with it (we know viraj28m became a
CEO; we know brandoniles founded Ampleforth). A feature is *backtest-legal* only
if every input is computable from data as of prediction time t.

1. **Co-founder-pair formation (new-strong-tie onset).** Sudden sustained
   co-activity between a low-degree pair on a fresh, domain-coherent repo:
   commit-parity over months (nateps/bnoguchi on racer), or a dense short burst
   (brgmry/arnau01, 54 commits in 36 hours; priyanka/viraj on mover_pressors).
   This is Pillar 2's CEO-meets-CTO event, and this study confirms it appears in
   6/16 missed cases. *Leakage: none — defined entirely at time t; no founder
   labels needed.* **Backtest-legal.** The open validation question is the
   false-positive rate: hackathon pairs are common; the discriminating variants
   are probably burst-plus-persistence and domain coherence with subsequent
   activity.

2. **Collaboration with already-recognized founders as of t.** Count/strength of
   edges to people who are, *at prediction time*, labeled founders of existing
   accelerator companies — e.g., lukejagg co-committing daily inside sweepai
   (YC S23) throughout H2 2023, before Speck's W24 batch. *Leakage: low if the
   founder roster is snapshotted at t (YC directory is dated); the tempting
   variant — "collaborated with people who LATER founded" (harshilmathur forking
   CodeRunner in 2011, brandoniles on bitcoin-android) — is post-hoc and
   live-only.* **Backtest-legal in the as-of-t form; the "future founder count"
   form is live-only** (usable in the running system as edges *become* labeled,
   and for retrospective characterization like this study, but never as a
   backtest feature).

3. **Neighbor-quality percentile from the collaboration graph, attributes-at-t.**
   For each of a person's counterparties (co-committers, PR mergers, issue
   responders), compute their standing *at time t* from the event stream:
   cumulative merged-PR volume into high-star repos, maintainer status
   (merge rights exercised), watch-events received on owned repos up to t. Then
   score the person by the percentile of their neighbor distribution. This
   captures kietay (accepted by scio/provider maintainers), ddmkr (co-building
   with the learnpython.org and swirl authors), barmstrong (merged by
   bitcoin-ruby's maintainer). *Leakage: moderate and subtle — current follower
   counts, current bios, and current star totals are post-outcome; every
   neighbor attribute must be reconstructed from archived events ≤ t
   (star-counts-at-t from WatchEvents are reconstructible; follower-counts-at-t
   are not, and must be excluded or proxied).* **Backtest-legal only with
   strict at-t reconstruction; trivially leaky if implemented lazily.**

4. **Inbound attention to tiny repos from strong-at-t builders (niche-tool
   adoption).** Forks/issues/watches on a low-star owned repo where the *actors*
   are high-percentile builders as of t: gary-rowe (MultiBit author) filing
   feature requests on bitcoin-android within two days; captn3m0 forking
   CodeRunner; dominictarr and Raynos filing issues on racer; maintainer-level
   accounts answering rohan-mehta's issues within hours. The generalization:
   *who shows up in your repo beats how many events you emit.* *Leakage: same as
   (3) — actor quality must be measured at t; also survivorship risk since
   deleted repos/forks vanish from the live API (use archived events, not
   current state).* **Backtest-legal with at-t actor scoring.**

5. **Interaction-graph topical coherence (semantic, Pillar-1-adjacent).**
   Fraction of a sparse account's edges pointing into one niche community,
   measured on event-time text: callmevlad's ~18 events aimed exclusively at
   WYSIWYG/in-browser-editing authors; rohan-mehta's five-month sequence of
   frontier-AI issues; bluejayio's SMART-on-FHIR fork + react-pdf issue (the
   one signal that survives in an otherwise network-free case). *Leakage: low if
   annotation runs strictly on event-time artifacts per the research program's
   contamination rule (never current READMEs/bios); the community definition
   must also be built from ≤ t data.* **Backtest-legal.**

Cross-cutting prerequisite: **none of these features exist unless identity
resolution is fixed.** Concretely: reject candidate handles created after
t_cutoff (christos-fal, priyanka-galen were both scored on post-batch accounts);
propagate resolution confidence into features (Pillar 4); treat a single strong
co-commit edge as resolution evidence in itself (viraj28m was droppable at 0.2
by name-matching but near-certain via the mover_pressors edge); and filter
fork-inherited commit history before any shared-actor join.

### (c) What this means for the inbound track

The outbound detector's ceiling is now characterized: it cannot reach
(i) non-technical founders (matinm, hendrikvanhove01, brgmry pre-sprint),
(ii) fully-private teams (Remade's four Cambridge researchers), and
(iii) career corporate engineers with no public residue (bluejayio). For these,
the recoverable signals named in the portraits are off-GitHub — university
research cohorts and co-authorship (Remade), HuggingFace artifacts, Form D
filings, PM/APM alumni networks (Heap), employment adjacency to elite operators
(georgewfraser at Emerald Therapeutics inside the Founders Fund orbit). That is
exactly the research program's position: the observability boundary "defines
where the inbound track must take over from the outbound detector."

Two additions this study makes to the inbound design:

- **One-join amplification.** When inbound sources surface *one* member of a
  team (an application, a Form D officer, a directory row), the collaboration
  graph and labels table can recover the rest and their history — hendrik's
  null profile becomes interesting the moment the same company row links him to
  ddmkr ("Previously CTO @datacamp"). Inbound and the graph are complements,
  not alternatives.
- **Adversarial hardening.** Inbound flows will be name-keyed and therefore
  exposed to exactly the impersonation pattern seen at christosantono
  (real bio, 1,198 followers, 49 same-day spam repos). Any inbound identity
  match needs the same evidence-cited probabilistic treatment as Pillar 4,
  plus creation-date and burst-pattern checks.

---

## 4. Methods and caveats

**Method.** 16 founders were selected from the false-negative set (strong
labeled outcome, detector score at floor/null). For each, an agent reconstructed
pre-batch identity and activity from local extracts
(`data/events/monthly_agg/positives.parquet`, `data/events/*` aggregates,
`data/labels/founders.parquet`) and live GitHub API queries (commit/contributor/
fork/following endpoints), then produced a structured portrait: miss cause,
neighbors with evidence URLs, an explicit present/absent judgment on non-obvious
network signal, prestige markers (recorded, excluded), and outcome evidence.
Several portraits note that the originally-specified `missed_events.parquet` /
`missed_shared_actors.parquet` were absent, so those cases were reconstructed
directly via `gh api`.

**Caveats.**

- **N=16, selected, not sampled.** The set was chosen because the founders were
  missed *and* their outcomes were strong and their stories recoverable. Counts
  in this document (12/16 network signal, 7/16 zero-event) characterize failure
  modes; they are not population estimates, and no matched controls were
  examined. Before any §3b feature ships, it must clear the standard gate: the
  same feature computed on matched non-founder controls (how many hackathon
  co-commit bursts, how many merged-into-big-OSS students never found
  anything?), under the frozen-clock protocol.
- **Resolution bias.** Portraits lean on evidence that still exists publicly.
  Deleted repos, renamed accounts, and vanished forks (kietay's removed
  Terraform repo, callmevlad's deleted pre-2016 forks) mean the reconstructed
  record is a lower bound on some signals and — because deletion correlates with
  time — biased toward recent cases. Live-API reconstruction also sees
  *today's* GitHub state (bios saying "CEO @conveo"), which is fine for
  identification but would be leakage if reused as features.
- **Case-sensitivity.** Each portrait is a narrative built by an agent with
  post-hoc knowledge of the outcome; the risk of over-reading coherence into
  sparse traces (a 54-commit weekend, a 40-second fork) is real. Four portraits
  explicitly report *no* network signal, and marginal ties are flagged as such
  (undated follow edges for matinm and shashankkumar/abhshkdz; the
  hendrikvanhove01 one-join case), which is some protection — but the
  discipline must be enforced by the control comparison, not by narrative care.
- **Archive coverage.** GH Archive begins 2011-02; the earliest cases (nateps,
  barmstrong) are windowed by data existence, not by founder behavior. Follow
  edges are undated platform-wide and were excluded from all "present" verdicts
  except as corroboration.
- **Company-name corrections.** Two briefs said "Convexo"; labels and all public
  evidence identify the company as Conveo (slug `conveo`, YC S24). Portraits
  carry the correction.
