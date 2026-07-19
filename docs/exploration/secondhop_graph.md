# Second-Hop Actor Graph: Co-Activity Around Cohort-D

Pillar-2 substrate build: every other actor on the repos Cohort-D touched, and
the actor–actor co-activity edge table derived from it. Produced by
`scripts/graph/secondhop.py`; outputs live in `data/graph/` (see its README for
schemas and the leakage warning).

## Method and sizes

Repo-IN-batched queries against the ClickHouse playground (index-pruned on
`repo_name`; no actor scans), full history `created_at < 2026-07-01`, bot logins
excluded with the project regex `(?i)(bot|\[bot\]|-ci|automation)` plus an
explicit CI-service account list (`web-flow`, `github-actions`, `circleci`,
`codecov`, …).

| Stage | Size |
|---|---|
| Cohort-D people | 1,920 (620 positive, 1,300 control) |
| Raw repo universe (items.parquet + repo_creations, distinct) | 64,769 |
| — owned by a cohort member (owner prefix, case-insensitive) | 27,160 |
| — other | 37,609 |
| Small-rooms filter: dropped (not owned, > 500 distinct non-bot actors) | 11,978 |
| Extracted in full (small, incl. all small owned) | 52,569 |
| Extracted capped (owned but > 500 actors: top-50 actors/repo-month, event_type collapsed) | 222 |
| Second-hop monthly rows | 6,073,263 |
| Distinct second-hop actors | 1,199,681 |

**Quota cost: 42 live queries total** — 13 distinct-actor-count queries
(5,000 repos each) + 29 extraction queries (26×2,000 + 1×569 repos full;
2 capped batches). No quota sleeps, no capacity bisects; the whole ClickHouse
phase ran in under two minutes. The verified index-pruning fact held: ~2–4 s
per 2,000-repo full-history batch.

**Small-rooms filter effect.** The 11,978 dropped rooms are the big-OSS
gravity wells (kubernetes, react, …) where co-presence is not acquaintance;
dropping them removes 18% of repos but is what keeps the edge table at 678K
rows instead of hundreds of millions, and keeps every remaining edge
interpretable as "these two people were plausibly aware of each other."
Cohort-owned repos are exempt (a popular own repo is signal, not noise); the
222 owned repos over the bound are capped at the 50 most-active actors per
repo-month rather than dropped.

## Edge and neighbor tables

- `data/graph/coactivity_edges.parquet` — 678,405 rows of
  `(cohort_login, neighbor_login, repo_name, month, cohort_events,
  neighbor_events)`: both sides active in the same repo-month, neighbor side
  capped at the top-50 actors of that repo-month. 1,875 of 1,920 cohort
  members have at least one edge; months span 2011-02 … 2026-06.
- `data/graph/neighbors.parquet` — 467,548 distinct
  `(cohort_login, neighbor_login)` pairs over 342,457 distinct neighbor
  logins; 22,835 pairs (4.9%) are sustained (≥ 3 co-active months).
- Degree per cohort member: p25 = 26, median = 80, p75 = 220, p90 = 549,
  p99 = 2,788, max = 17,438 (mean 249). The tail is watch/fork-heavy popular
  owned repos; sustained-months filtering collapses it.
- Founder contact: 1,162 pairs have a confident-YC-founder neighbor
  (458 cohort members); 815 of those pairs begin before the cohort member's
  `t_cutoff`, and **423 are backtest-legal in the strict form** (the
  neighbor's batch had already started by `t_cutoff`, i.e. founder-status
  was knowable at prediction time): 221 on positives vs 202 on controls —
  per-capita **2.3× over-representation on positives** (0.356 vs 0.155),
  a first uncontrolled hint that recognized-founder exposure discriminates.

## Three examples

1. **josephschorr ↔ jzelinskie → Authzed (YC W21).** Co-active from 2015-02
   to 2020-07 across the CoreOS/Quay orbit — `coreos/quay-docs` (12 shared
   months, 126 vs 168 events), `registry-monitor`, `jwtproxy`,
   `py-bitbucket`. Five years of sustained co-work inside one product
   surface, ending months before their 2021-01 batch: the CEO-meets-CTO tie
   fully legible in public events long before incorporation.
2. **kanyesthaker ↔ shalins → Hyper (batch 2026-04).** 21 shared months on
   `IrisHub/SpaceBar` (1,683 vs 1,091 events) from 2022-03 to 2024-06 — a
   fresh two-person repo with near-parity commitment, two full years before
   their batch and inside the pre-cutoff window (t_cutoff 2025-04). This is
   the textbook new-strong-tie onset shape from `missed_founders.md` §3b-1.
3. **ggsonic (control) ↔ huan (JuziBot, batch 2019-01).** Eight months on
   `wechaty/bot5.club` starting 2019-09 — *after* huan's batch started, so
   the strict as-of-t "recognized founder edge" feature legally fires… on a
   control. A useful honesty check in both directions: the feature is
   computable without leakage, and its false-positive behavior (orbiting a
   founder's community ≠ founding) is exactly what the matched-control gate
   must measure.

(Also present and satisfying: alexdanilowicz ↔ Teddarific co-building
`Left-on-Read/leftonread` for 10 shared months in 2018–2022 before founding
Magic Patterns, W23 — both sides resolved, both in Cohort-D.)

## Integration notes

**GNN lane (`scripts/gnn/`, expecting `data/gnn/`).** The lane should
materialize `data/gnn/` from these tables, not re-query ClickHouse:
node set = Cohort-D ∪ neighbors (index by lowercase login);
`coactivity_edges.parquet` is already the (src, dst, repo, month, weights)
temporal edge list — monthly snapshots come from grouping on `month`, and
`secondhop_monthly/` provides per-node monthly event-type feature vectors
(note `event_type='__ALL__'` for the 222 capped repos; treat as untyped
counts). Two hard rules: (i) for any training example anchored at person p
and time t, restrict to edges with `month < t_cutoff(p)` — the tables
deliberately run to 2026-06 so the live system can reuse them; (ii) never
feed `neighbor_is_confident_founder` / `founder_batch_start_date` as node
features except in the as-of-t recognized form (`batch_start_date <= t`).

**`new_strong_tie_onset` features.** Everything needed is in the edge table:
for a candidate (cohort_login, month t), a new strong tie is a neighbor with
zero shared months before t−k and ≥ m of the last k months co-active on a
repo created recently (join `repo_universe` → `data/events/repo_creations/`
for owned-repo creation dates), with near-parity event ratio
(`min/max(cohort_events, neighbor_events)` aggregated over the window).
The three example pairs above give the calibration shapes: burst-plus-
persistence (SpaceBar), long parity (quay), and the ggsonic case as the
false-positive template. Gate per `missed_founders.md` §4: the same feature
on matched controls, frozen-clock protocol, before it ships.

**Caveats.** Second-hop coverage is conditioned on the small-rooms filter
(edges through mega-repos are invisible by design); the neighbor cap means
repo-months with > 50 actors under-count weak edges; `event_type` granularity
is lost for the 222 capped repos; co-activity in the same repo-month is
presence, not interaction (no review/comment threading yet — that is the next
refinement of Pillar 2's "review interactions").
