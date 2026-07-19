# Deep-Slice Pilot: Validate Before Unloading (2026-07-19)

**Question.** Before spending days/dollars unloading GitHub history (BigQuery extract or
GH Archive stream), validate on a small, deep slice: (a) which columns/signals actually
carry lift, (b) whether the FP-portrait hypothesis — tutorial bursts are separable by
*content* — survives quantification, (c) what the full unload would even cost.

**Method.** Pilot cohort of 734 scored actors: the entire top-of-ranking region
(peak ≥ 0.28: 149 founders, 265 controls — where the count model is a measured coin
flip) plus 320 stratified across score quartiles. For each, every pre-cutoff
text-bearing event (Create/Fork/Issues/PR/comments/Release/Member/Public; 48-month
window) pulled from the ClickHouse playground with `FORMAT Parquet` + `toValidUTF8`
(GH text contains invalid UTF-8 that otherwise poisons the parquet). 182,295 events,
523/734 actors with ≥1 text event, 14 MB. Code: `src/vc_brain/pilot/`.

## Finding 0 — exact storage economics (measured, playground metadata)

`github_events` 2011→2026: **10.98 B rows, 763.55 GiB compressed** (4.43 TiB raw).
`body` alone is 473 GiB (62%); `diff_hunk` 44 GiB. Per-year rows: 2017 ≈ 413 M
rising to 2024 ≈ 1.81 B (2025 dips to 1.55 B — note when normalizing by year).
The 6-column projection our SQL uses (actor_login, created_at, event_type,
repo_name, action, ref_type) ≈ **85 GiB for all 15 years**; + title/labels ≈ 110 GiB.
A full local mirror is a laptop-scale problem — *if* it is ever justified.
Also corrected: a BigQuery full-`payload` scan is charged on ~100+ TB uncompressed —
high hundreds of dollars, not the casual ~$100 sometimes assumed.

## Finding 1 — free precision from event-type mix (no new data needed)

In the top region, **0/149 founders** have zero text-bearing events, but
**79/265 controls (30%)** do — pure Push/Watch grinders. The count model scores
them highly; a hard interactivity rule (≥1 create/issue/PR/fork pre-cutoff)
removes 30% of top-region controls at **zero** founder cost. This is computable
from the existing panel (event-type mix) — no text required. Caveat: in the
stratified (lower-score) sample, 50% of *founders* have no text events either,
so the rule is a top-of-ranking filter, not a global one.

## Finding 2 — regex content features are a dead end (hypothesis killed cheaply)

Curriculum/tutorial repo-name patterns (`alx-*`, `*-tutorial`, `cs\d+`,
`interview-prep`, …): founder-vs-control AUC ≈ 0.47–0.54 everywhere, and
top-region founders trip the patterns *slightly more* than controls (0.059 vs
0.043 learning-repo share) — founders also grind leetcode and take courses.
Penalizing learning-share **hurts** precision@25 (0.60 → 0.52). The
FP-portrait's hand classification worked because a human judged *substance*;
string patterns cannot. This kills the "just add regex features" shortcut and
with it the main argument for a counts+names-only bulk unload.

## Finding 3 — semantic annotation (Pillar-1 mini, LLM as instrument)

Digests of pre-cutoff text (repos created, forks, issue/PR titles, comment
excerpts — event-time text only, no labels, no post-cutoff data) annotated by
`anthropic/claude-sonnet-4.5` (temp 0, cached): `builder_type`,
`audience_orientation`, `productization`, `gestation_likelihood` 0–100.
Calibration anchors behaved: known bootcamp FP (mcolus97) → gestation 5;
known mislabeled founder (samyakkkk/LandingHero) → gestation 95.

**Instrument validation — excellent.** Against the 19 annotated hand-classified
portrait people: all 13 clear-FPs score gestation ≤ 15; the 4 "interesting"
profiles score 75–85; the mislabeled founder scores 95. The LLM reproduces the
human deep-read almost perfectly at ~$0.01/person.

**Ranking utility — real at the head of the list.** Re-ranking the top region by
gestation_likelihood (no-text actors → 0): precision@10 **0.40 → 0.70**,
precision@100 0.43 → 0.53 (+10pp). For a top-K sourcing product this is the
metric that matters, and the high-gestation "misses" are disproportionately the
INT/NOISE class — utility-precision is higher still.

**But binary AUC vs YC-only labels barely moves** (0.558 vs peak baseline
0.575), and the reason is the finding: among *genuine top-region YC founders*,
only **37/149 (24.8%)** read as `own_product_building` pre-batch (corrected
2026-07-19 by the wave-2 full-cohort pod — this doc originally said 45/149/30%,
a tally error); 23 are in coursework, 33 in employment-shaped work, 25 in OSS
contribution, 16 in research. Public product-gestation is observable for only
~a quarter of founders even in the high-activity region — the research program's "observability
boundary," now measured. Meanwhile 37/186 controls DO read as product-builders,
and the portrait says exactly who those are: unlabeled founders and meet-worthy
near-founders. The instrument's ceiling against YC-only labels is set by label
noise + observability, not by the instrument.

**Contamination caveat (reported, not hidden):** the annotator's world knowledge
could recognize specific people/repos and their later outcomes; digests are
event-time text only, but logins/repo names are visible. Results are an upper
bound pending a name-blinded replication (hash logins/repo owners in digests).

## Decision gates (resource allocation)

1. **Do now regardless:** interactivity rule at eval/triage time (Finding 1);
   costs nothing, mechanically lifts top-region precision.
2. **Finding 3 shows lift where it matters (top-K), so the next data purchases
   are:** (a) *more text for scored actors* — the actor-scoped extraction
   scales linearly (~2.7k scored actors ≈ 25 MB, one quota window); (b) **label
   broadening beyond YC** (HN launches first per the linkage study, then Form D)
   — the annotation ceiling is set by label noise, so labels and semantics must
   ship together; (c) commit messages via GitHub API for scored actors (absent
   from GH Archive's flattened schema entirely).
3. **The full unload** is justified only by features needing *everyone's*
   history (population-scale frozen-clock top-K lists, global collab graphs —
   Pillar 5's population pool). Revisit when that experiment is scheduled;
   at 85–110 GiB projected size, ClickHouse-in-Docker on a Mac suffices.
