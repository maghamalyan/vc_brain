# Commit-Message Depth: Signal and Survivorship (Pod D, 2026-07-19)

**Question.** Commit messages are absent from GH Archive's flattened schema; the only
source is the live GitHub API — which sees only repos that still exist. Two measurements
on one stratified sample: (1) *survivorship* — what share of pre-cutoff-created repos has
vanished (a discount factor every future API-based feature claim needs), and (2) *signal*
— does adding commit-message text to the annotation digest improve founder/control
discrimination?

**Method.** From the 335 annotated top-region pilot actors, a stratified 200: all 66 with
event-only `gestation_likelihood >= 50` (34 founders / 32 controls), plus seed-42 random
fill to 100 founders / 100 controls. For each actor, their own repos created pre-cutoff in
`data/pilot/text_events.parquet` (up to 6 per actor, most event-active first) → 907 repos
across 188 actors (12 created no own repo in-window). Per repo, one page of
`gh api repos/<repo>/commits?until=<t_cutoff>T00:00:00Z&per_page=100`, sequential ≈2 req/s,
cached in `data/cache/gh_commits/` (907 JSON records). Commits with author date >
t_cutoff dropped (0 of 15,875 — the `until` filter already covered them; author dates are
rewritable, so both author and committer dates are recorded in
`data/pilot/commit_messages.parquet`). Code: `src/vc_brain/pilot/commit_depth.py`.

## Finding 1 — survivorship: 22.6% of pre-cutoff-created repos are gone (live API, current-day data)

| status | repos | share |
|--------|------:|------:|
| alive | 697 | 76.8% |
| **deleted/private (404)** | **205** | **22.6%** |
| empty git history (409) | 5 | 0.6% |

- **By class: flat.** Controls 109/463 = 23.5% dead; founders 96/444 = 21.6% dead
  (diff 1.9pp ± ~2.8pp at 95% — indistinguishable). At the actor level, 52.6% of controls
  and 57.0% of founders have ≥1 dead repo.
- **By event-only gestation band:** [0,15) 18.8%, [15,50) 21.8%, [50,80) 27.9%,
  [80,100] 20.0% — no monotone pattern; the one striking cell is founders in [0,15):
  2/28 = 7.1% dead (small n). High-gestation founders' repos die at 14.8% ([80,100],
  n=61) vs 24.3% for high-gestation controls (n=74) — suggestive (founders' gestation
  repos become the company's repos and survive; controls' experiments get cleaned up),
  but the CI is wide.
- **Implication for every future API-based feature:** any feature computed from the live
  API (commit text, README content, stars-today, language breakdown) silently conditions
  on the ~77% of repos that survived. The good news from this measurement: the loss rate
  is statistically flat across founder/control, so survivorship *attenuates* rather than
  *systematically distorts* class comparisons — but per-person it is a coin flip (>half of
  actors are missing at least one repo), so individual dossiers built from the live API
  are incomplete more often than not.
- 404 conflates deleted and made-private; renamed repos redirect (HTTP 301 → followed)
  and still count alive. 2/697 alive repos had zero commits before cutoff.

## Finding 2 — signal: commit messages move individual judgments a lot, discrimination not at all

15,875 pre-cutoff commit-message first-lines (truncated 150 chars) from 180/200 actors
(median 60/actor, p90 182, max 462; 29.9% are content-free — "update", "fix", "wip",
"initial commit" and kin — 4,748/15,875). Augmented digest = the exact event-only digest + up to 60 most
recent pre-cutoff messages, chronological; same prompt, model
(`anthropic/claude-sonnet-4.5`), temperature 0; cache
`data/cache/pilot_annotations_commits/`. 160/180 re-annotated (20 lost to OpenRouter
credit exhaustion — the alphabetical t–z tail, not outcome-correlated); the 20 actors
with no fetched commits keep their byte-identical event-only annotation.

| metric (same people, paired) | event-only | commit-augmented |
|------------------------------|-----------:|-----------------:|
| gestation AUC, n=180 | 0.510 | 0.472 |
| gestation AUC, augmented subset n=160 | 0.510 | 0.468 |
| peak-score AUC (reference) | 0.539 | — |
| founder median gestation | 25 | 15 |
| control median gestation | 25 | 25 |

(The absolute AUCs are far below the top-region eval's 0.558 because this sample is
deliberately gestation-enriched in *both* classes; the paired delta is the measurement.)

**Paired ΔAUC = −0.043, 95% bootstrap CI [−0.093, +0.009] (2,000 resamples, seed 42) —
commit text adds no discriminative signal; the CI all but excludes meaningful lift.**
Yet it is not inert: 38/160 (24%) changed `builder_type`, and gestation moved ≥30 points
for 20/160 — in both directions, for both classes, roughly symmetrically. Commit messages are strong *evidence about the person* that is
*uncorrelated with the founder label*: they reveal how someone works (WIP-spam vs
conventional commits vs feature narration), which the annotator re-anchors on, displacing
the event-digest's repo-name/issue-title evidence that carried what little label signal
there was.

### Examples of commits changing the classification

- **egil (control, gestation 95 → 15).** Event digest read his multi-repo .NET work as
  own-product building. Commits ("Moved to simple wrapper model", "Upgraded to use
  AngleSharp 0.14.0", "Example of test that fails due to whitespace" across
  `egil/AngleSharp.Wrappers`, `egil/BunitVerifySample`) revealed it as bUnit-ecosystem
  OSS testing infrastructure → correct downgrade of a would-be false positive.
- **gregpr07 (labeled founder, 75 → 15, `own_product_building` → `coursework_learning`).**
  347 commits of student texture — "working?", "error in code", "hopefully fixed admin",
  "final changes before release" — across university/EU-research repos (`x5gon-*`,
  `VLN-Mobile`, `fmf-dictionary-frontend`). The commits truthfully describe the
  pre-cutoff window as student work; the founding came later. Sharper evidence, worse
  label agreement — the observability boundary in miniature.
- **ralphr123 (labeled founder, 15 → 75, `coursework_learning` → `own_product_building`).**
  202 commits trace coursework → hackathon → a sustained `vrplatform` build (auth, admin
  controls); the event digest alone had filed him as a student. The clearest genuine win
  for commit text in the sample.
- **skavrx (control, 25 → 72).** Commit messages are literally "e", "e", "3", "lim" —
  pure noise — yet hardware project names in the commit block ("cycloidal-drive-v1",
  "autobike-") nudged the annotator toward product building. A hobbyist inflated by
  volume: the failure mode that cancels the wins.

## Verdict: commit text does not earn a place in the scoring pipeline

1. **As a scoring feature: no.** ~1s/repo API cost, a 23% survivorship hole, and a paired
   ΔAUC of −0.043 (CI [−0.093, +0.009]) on 160 people. The event-time digest (repo names, issue/PR titles,
   comments) already carries the semantic signal; commit first-lines add volume, not lift.
2. **Survivorship discount to carry forward: 22.6% of repos / ~55% of people** are
   affected when any live-API repo feature is computed for this population. Flat across
   classes — attenuation, not distortion.
3. **Where commit text may still pay: top-K dossiers.** For the final human-facing
   deep-dive on ~25 candidates, commit messages give texture (what exactly they built,
   week by week) even if they don't rank. That is a presentation-layer use, not a
   pipeline feature, and it inherits the survivorship hole.

*All numbers from `uv run python -m vc_brain.pilot.commit_depth` (deterministic: seed 42,
temp 0, content-addressed caches). Repo status snapshot taken 2026-07-19 via
authenticated gh CLI as `maghamalyan`.*
