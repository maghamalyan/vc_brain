# Spec P3 — Event-stream extraction (ClickHouse playground)

## Verified facts (Claude, do not re-derive)
- `curl -s 'https://play.clickhouse.com/?user=play' --data-binary "<SQL> FORMAT TSVWithNames"`
  works; `github_events` covers 2011-02 → yesterday. Schema: event_type (Enum), 
  actor_login, repo_name, created_at, ref_type (repository|branch|tag), action, plus
  title/body text fields. Single-actor scan ≈ 7s → ALWAYS batch actors with
  `actor_login IN (...)` (~300 per query), never per-actor queries.

## Outputs (all parquet under data/events/)
1. `monthly_agg/`: per (actor_login, month, event_type) counts — for positives AND
   negatives. Window: 48 months before each actor's t_cutoff (positives) / pseudo-t
   (negatives).
2. `repo_creations/`: event-level rows for CreateEvent+ref_type='repository' by cohort
   actors (created_at, repo_name) — burst + naming features, evidence for trust layer.
3. `baselines/monthly_totals.parquet`: global per-month per-event_type totals (one
   cheap GROUP BY) — normalizes platform growth over the years.
4. `negatives/candidates.parquet` + final matched sample.
5. `data_card.md`: counts, coverage, sampling ratios, known gaps.

## Negative sampling (case-control, deterministic)
- Pool: actors with ≥20 events in the cohort's calendar window; exclude: any login in
  the labels file (ANY confidence), logins matching `(?i)(bot|\[bot\]|-ci|automation)`,
  type!=User unavailable here — pattern filter only (note in data card).
- Match per positive: K=5 negatives from same activity band (total events in
  [0.5×, 2×] of the positive over its 48-mo window) and first-seen year within ±1.
  Deterministic: ORDER BY cityHash64(actor_login) with fixed offset.
- Record the exact ratio + bands in data_card.md (needed for probability correction).

## Leakage rules (Claude audits these specifically)
- Every aggregate row must satisfy month < actor's t_cutoff. Enforce in SQL AND assert
  in a post-load test.
- No feature may reference the company, its org, or its repos. (t_cutoff = batch_start
  − 12mo already precedes most company orgs, but assert: drop any cohort actor whose
  matched company website domain appears in their repo_names pre-t; log drops.)
- Negatives must not contain any labeled founder login (assert).

## Implementation notes
- Module: src/vc_brain/ingest/clickhouse.py — tiny client: query(sql) -> polars df via
  TSVWithNames; retry w/ tenacity (playground can 503 under load); result-size guard:
  if a batch query returns ≥ 900k rows, split the actor batch in half and recurse.
  Cache every query result keyed by sql hash → data/cache/ch/<hash>.parquet.
- Respect the shared playground: ≤2 concurrent queries, small sleep between.
- CLI: `uv run python -m vc_brain.ingest.run --stage baselines|positives|negatives|repos`
  resumable via cache.

## Acceptance (Claude verifies)
1. pytest green incl. leakage assertions on real extracted sample.
2. Positives coverage: monthly_agg rows for ≥80% of confident founders (some have zero
   GH activity — that's real signal, keep them as all-zero rows flagged `no_gh_activity`).
3. Leakage audit passes: max(month) < t_cutoff per actor; no founder in negatives.
4. Data card complete with honest limitations (bot filter is regex-only, playground is
   a shared best-effort service, etc).
