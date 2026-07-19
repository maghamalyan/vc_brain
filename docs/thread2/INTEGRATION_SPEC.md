# Thread 2 — Real-Data Integration Spec (I-round)

Decision (Misha, 2026-07-19): full integration, no loose ends. The served app runs on
the REAL cohort; fixtures are retired from the app (tests keep them). Real founder
names/companies are shown (public YC + GitHub data). Where data is missing, show
honest missing states — never fabricate. Radar (100 candidates) and memos (5 real,
more only if cheap) are separate features and both must shine.

Base: `worktree-live-intel` merged with `overnight/poc@373ec60` (main committed +
clean; no session active in the main checkout — coordination via PROGRESS journal).

## Source data (read-only, in-repo after merge; large files live in the MAIN
checkout's gitignored `data/` — source dir is configurable)

MAIN_DATA=/Users/mishaaghamalyan/Development/personal/competitions/vc_brain/data

- `scores/candidates.parquet` — 100 real candidates, contract shape,
  score_percentile is 0–1 (fixtures were 0–100 — NORMALIZE ×100).
- `scores/trajectories.parquet` — 102k rows (gh_login, month, score); filter to cohort.
- `scores/attributions.parquet` — (login, crossing_month, feature, delta_contrib).
- `labels/founders.parquet` — founder_name, company, slug, batch, batch_start_date,
  gh_login, gh_confidence… → recognition source.
- `memos/*.json` — 5 real memos, full P8 schema; claim evidence_refs use scheme refs
  (e.g. `yc:winfunc`) — enumerate ALL schemes present and map (below).
- `events/repo_creations/{positives,negatives}.parquet` — real per-repo creations.
- `events/monthly_agg/` — real per-person monthly activity aggregates.

## Adapter: `vcb-integrate` (new CLI in service/, like vcb-index)

`uv run vcb-integrate build --source $MAIN_DATA --out ../data/integrated`
produces a directory in the EXACT shape vcb-index consumes:

1. `candidates.json` + `.parquet`: the 100 real candidates with
   - `score_percentile` ×100 (guard: only if input ≤ 1.0),
   - `recognition`: join founders.parquet on gh_login (highest gh_confidence on
     dupes): {month: batch_start_date→YYYY-MM, kind: "yc_batch", label: "YC {batch}"};
     null when no label match (that IS the "still ahead of market" cohort),
   - `score_components`: from attributions per login — aggregate |delta_contrib| by
     feature (at the login's crossing_month rows; else all rows), take top 4, scale
     so top-4 + one "Other observed signals" remainder sum to current_score ±0.001;
     humanize feature keys (snake_case → labels). Logins absent from attributions →
     `[]` (waterfall hides — honest missing state).
2. `trajectories.json/.parquet`: filtered to cohort logins, month ascending.
3. `events.json/.parquet` (evidence): HONESTLY DERIVED, real URLs, no invention:
   - repo_creations rows for cohort logins → event_type `repo_created`, ts from
     created date, repo_name real, url `https://github.com/{repo}` , detail
     "Created public repository {name}".
   - monthly_agg for cohort → at most one event per active month per login,
     event_type `activity_month`, detail "{N} public GitHub events in {Mon YYYY}
     (derived from GH Archive)", url `https://github.com/{login}`. Skip zero months.
   - For each memo'd company: one `yc_listing` event, ts = batch_start_date,
     detail "Accepted to Y Combinator {batch}", url
     `https://www.ycombinator.com/companies/{slug}`, evidence_id EXACTLY the memo's
     scheme ref (e.g. `yc:winfunc`) so memo citations resolve in-index.
   - Any other memo ref scheme: map to a real public URL analogously (e.g. `hn:` →
     news.ycombinator.com item; `gh:` → github URL). NOTHING may dangle: vcb-index
     --verify must pass with zero unresolved refs.
   - evidence_id: stable hash (`re-`/`am-`/scheme prefixes ok).
4. `memos/`: copy the 5 real memos verbatim (only fix: refs stay as-is since the
   yc:/scheme evidence rows above make them resolve).
5. `profiles.json`: minimal real profiles derivable from candidates+founders
   (name, company, login); omit fields we don't have. If vcb-index requires more,
   make the missing pieces optional in the indexer instead of inventing data.
6. `--verify` on vcb-integrate: prints cohort size, recognition join rate, components
   coverage, evidence counts by type, memo ref resolution preview; nonzero exit on
   any dangling memo ref or component-sum drift.

## Index + app switchover

- Default index build becomes: integrate → `vcb-index build --data-dir
  ../data/integrated --thesis ../config/thesis.json --out ../data/index/vcb.sqlite
  --verify`. Deterministic given identical inputs.
- App changes: NONE expected (fields all in contract; missing-state paths exist).
  Watch: real cohort size 100 (list pagination/limit — the radar requests must not
  cap at 12), month range spans 2019?–2026 (scrubber tick density — derive ticks
  from data, cap visual ticks sensibly), candidates without memo/components/
  recognition render their existing honest states, deep-dive capture section simply
  absent for real logins (no cached runs yet).
- Fixture retirement: fixtures remain ONLY for pytest/Playwright (VITE_MOCK). The
  served index is integrated-real. Do not delete data/fixtures or mocks.

## Gates (Claude)

1. `vcb-integrate --verify` output sane (join rate, zero dangling refs).
2. `vcb-index --verify` green on integrated dir; pytest suite green.
3. Server boot on real index; endpoint spot-checks (a memo'd founder detail w/
   components + recognition; a bare candidate w/ honest nulls).
4. Browser gate: radar shows 100 real rows + real Proof strip (real YC lead
   times); record page for 123vivekr (memo, citations resolving to yc: evidence,
   waterfall from real attributions); scrubber honest across the real month range.
5. Full-suite Playwright still green (mock mode untouched).
