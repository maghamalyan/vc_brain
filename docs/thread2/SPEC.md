# Thread 2 — Live Intelligence Layer (search, API, deep-dive, rich frontend)

Status: ACTIVE. Branch `worktree-live-intel` (worktree of the main repo).
Owner: Misha + Claude (judgment/API/verification) + Codex (build).
Relationship to main thread: the main agent owns `src/vc_brain/{ingest,labels,features,models,eval,memo,dashboard}`
and the historical/backtest pipeline. Thread 2 adds a **deployable API service, a real
frontend, global search/command palette, and on-demand live deep-dives**. We touch ONLY:
`service/`, `frontend/`, `docs/thread2/`. Nothing else. Merge = data union, not code merge.

## Why (rubric framing)

The challenge brief wants an *investment tool people can use*, not only a backtest:
Investment Utility & Execution 30%, Trust 25%, UX 15%. The main thread proves the
detector on historical data; this thread makes the same trust discipline work on
**live, on-demand data** and packages everything behind a proper API that can be
deployed for judges to try.

## Merge contract (FROZEN — do not drift)

1. **Claim schema** is the single currency. Source of truth:
   `src/vc_brain/memo/schema.py` (pydantic). Every claim anywhere:
   `{text, evidence_refs[], confidence, verification_status: verified|single_source|unverified|not_disclosed, contradictions[]}`.
   Thread-2 additions carry `provenance: "live"` (vs `"backtest"`) at the run/document
   level — never a changed claim shape.
2. **Data shapes** from `specs/p8_slice.md` are read as-is:
   `data/fixtures/candidates.json|parquet`, `trajectories`, `events`,
   `data/fixtures/memos/<login>.json`, `config/thesis.json`.
   The service must ALSO work when pointed at `data/scores/`, `data/evidence/`,
   `data/memos/` (the real P4/P5 outputs) via `--data-dir` — same shapes, per spec.
3. Evidence event: `{evidence_id, gh_login, ts, event_type, repo_name, detail, url}`.
4. Never average the three axes. Gaps are rendered, never filled.

## Architecture

```
service/    Python 3.13 + uv project (OWN pyproject — do not touch root pyproject.toml)
            FastAPI + uvicorn + pydantic v2 + sse-starlette + httpx + python-dotenv
            + polars or duckdb (parquet reads) + sqlite3 stdlib (FTS5 index)
frontend/   Svelte 5 + Vite + TypeScript, static build (adapter-static equivalent:
            plain Vite build) → frontend/dist, served by the service at /
docs/thread2/  SPEC.md (this file), PROGRESS.md (journal: every Codex handoff,
            every verification result, timestamped)
```

Schema import: try `[tool.uv.sources] vc-brain = {path = "../", editable = true}` so
`service` imports `vc_brain.memo.schema` directly. If the root package's dependency
chain is too heavy for a deploy image, instead copy `schema.py` →
`service/src/vcb_service/claim_schema.py` VERBATIM with a header comment naming the
source file, plus a contract test that validates all three fixture memos against it.

## Index command (not an endpoint)

```
uv run vcb-index build --data-dir ../data/fixtures --thesis ../config/thesis.json --out ../data/index/vcb.sqlite
```
Run once at build/deploy time. Produces ONE SQLite file:
- FTS5 table `docs(doc_type, doc_id, title, subtitle, body, route)` with bm25 ranking.
  Document types: `founder` (profile + company), `company`, `claim` (memo claim text),
  `evidence` (event detail), `memo_section`, `thesis_term` (sectors etc.).
  `route` is the frontend path the palette navigates to, e.g.
  `/candidate/ada-lovelace-fixture#claim-c3`.
- Plain tables mirroring candidates/trajectories/events/memos (denormalized JSON
  columns are fine) so the server reads ONLY this sqlite file at runtime — single
  artifact, trivially deployable. Server takes `VCB_INDEX=path` env (default
  `data/index/vcb.sqlite`), opens read-only.
- `vcb-index build` is idempotent; `--verify` flag prints doc counts per type and
  fails nonzero if any memo claim has an evidence_ref that resolves to nothing.

## API (v1 — FROZEN for parallel frontend work)

All under `/api/v1`. FastAPI auto-OpenAPI at `/api/v1/openapi.json` (frontend
generates its typed client from a checked-in copy: `frontend/src/lib/api/openapi.json`).

- `GET /health` → `{status:"ok", index_built_at, counts:{candidates,events,claims}}`
- `GET /thesis` → thesis.json contents
- `GET /candidates?source&status&sort=score|momentum&limit&offset`
  → `{items:[Candidate], total}` ; `Candidate` = fixture candidate shape +
  `has_memo: bool`.
- `GET /candidates/{login}` → `{candidate, trajectory:[{month,score}],
  three_axis|null, memo_available, evidence_counts_by_type}`
- `GET /candidates/{login}/evidence?type&after&before&limit`
  → `{items:[EvidenceEvent], total}`. `after`/`before` are ISO dates — this powers
  the time-scrubber; MUST filter server-side on `ts`.
- `GET /candidates/{login}/memo` → memo JSON verbatim (404 if none)
- `GET /claims/{claim_id}` → `{claim, resolved_evidence:[EvidenceEvent|{url}]}`
  (claim_id is unique across fixture memos; qualify as `<login>:<claim_id>` if not)
- `GET /search?q&types&limit=20` → `{groups:[{type, hits:[{doc_type, doc_id, title,
  subtitle, snippet(with <mark>), route, score}]}]}` — bm25-ordered within group.
  Latency target <30ms on fixtures. Prefix matching enabled (`q*`).
- Deep-dive (phase T3):
  - `POST /deepdive` body `{entity_type:"founder", entity_id, dimensions:["founder","market","idea_vs_market"]|subset, mode:"live"|"replay"}`
    → `202 {run_id}`. If an identical cached run exists and mode omitted → return it.
  - `GET /deepdive/runs/{run_id}/stream` → SSE, events:
    `step {seq, kind: plan|fetch|evidence|reason|claim|done|error, label, detail, ts, payload?}`
    Payload for `claim` events = a full claim object as it is drafted.
  - `GET /deepdive/runs/{run_id}` → full run doc (below)
  - `GET /deepdive/runs?entity_id` → list of cached run summaries
- CORS: allow all origins (public demo). No auth in v1 (read-only data + rate-limit
  deepdive: max 2 concurrent, 30/day, env-tunable — it spends API/LLM quota).

Deep-dive run document (cached at `data/deepdives/<run_id>.json`):
```json
{"run_id", "entity_id", "provenance": "live", "started_at", "finished_at",
 "steps": [ ...every SSE step, replayable... ],
 "evidence": [ EvidenceEvent... — fetched live, evidence_id = "live-" + hash, urls real ],
 "claims": { "<claim_id>": Claim },
 "dimension_notes": {"founder": {...three_axis-style entry}},
 "gaps": [str], "model": str, "token_usage": {...}}
```
Replay mode re-streams cached `steps` with ~300ms pacing — demo never depends on
live network. THE DEMO PATH IS REPLAY; live is the encore.

Deep-dive agent behavior (T3): fetch GitHub REST (profile, repos, recent events —
token from `gh auth token` if present, else anonymous), HN Algolia search
(`hn.algolia.com/api/v1/search?query=`), optionally SerpAPI if `SERPAPI_KEY` set.
Everything fetched becomes evidence rows FIRST; then one OpenRouter call
(`OPENROUTER_KEY`, model env `OPENROUTER_MODEL` default `anthropic/claude-sonnet-4.5`)
with the hard rules from `specs/p8_slice.md`: claims cite ONLY provided evidence_ids,
unknowns → gaps, honest verification_status (live single-fetch facts are
`single_source` unless corroborated). Validate output against claim schema; one
retry on validation failure; on second failure store run with `error` step — never
fabricate. `--mock` path with recorded fixtures for tests; NO network in tests.

## Frontend (Svelte 5 + Vite + TS)

Design: port tokens from `site/assets/styles.css` (paper `#f7f8f5`, ink, forest
`#194f3c`, radius 12, same font stack). Add ONE new token: `--live: acid lime
(#b7f04d region, tuned for contrast)` used EXCLUSIVELY for live/deep-dive states —
historical stays forest. Rounded chip-heavy language per the reference shots
(cardiology timeline / invoice / workspace): pill chips, circular icon buttons,
big numerals, segmented bars. Keep it light theme, investor-grade, no gradients.

Routes (hash or history — history preferred, service serves index.html fallback):
- `/` Radar: ranked list, animated FLIP re-rank, thesis controls panel (sliders/
  toggles bound to thesis dimensions re-weighting client-side), momentum arrows,
  source badges, keyboard j/k + Enter, time-scrubber ribbon (top, workspace-shot
  style) that re-filters evidence-derived display by date (client-side against
  `/evidence?before=`).
- `/candidate/:login` Deep-dive page ("founder health record", cardiology-shot
  structure): vitals header (score numeral + segmented 3-axis bar, never averaged;
  momentum; first-detection), horizontal evidence timeline with event-type filter
  chips and month markers, memo sections with per-claim chips — hover/focus a claim
  chip → popover with evidence refs (linked), confidence meter, verification badge,
  contradictions in red. Gaps box prominent. "Deep dive" button (lime) → run view.
- `/runs/:runId` streaming run view: step feed rendering SSE live (plan/fetch/
  reason/claim), claims materialize as cards as they arrive; replay of cached runs
  identical.
- Command palette (⌘K / Ctrl-K, global): queries `/search` (debounced 80ms),
  grouped results, arrow-nav, Enter routes. Verb rows: "Deep dive on <founder>…",
  "Open memo…", "Filter radar to <sector>". Also plain `/` opens search.
Accessibility: full keyboard nav, focus rings, prefers-reduced-motion honored.
No component framework; hand-rolled components. Charts: tiny hand-rolled SVG
sparklines/trajectory (no plotly dependency in frontend).

## Phases & gates

- **T1 (Codex)**: `service/` + `vcb-index` + all read endpoints + tests
  (pytest; contract test validating fixture memos against schema; FTS returns
  sane results for "ada", "AGPL", "fintech"). Gate (Claude): boot, hit every
  endpoint, latency check, verify `--data-dir` swap works.
- **T2 (Codex, parallel)**: frontend against this spec with a dev proxy to
  `localhost:8000` and a checked-in openapi.json snapshot; Playwright smoke
  (palette opens, search navigates, candidate page renders memo chips).
  Gate (Claude): visual review via browser + screenshots.
- **T3 (Codex)**: deep-dive agent + SSE + replay + run view. Gate (Claude): run
  ONE live deep-dive personally (real founder login TBD by Misha or a fixture
  login in mock mode), audit claims for fabrication, verify replay works offline.
- **T4**: `service/Dockerfile` (multi-stage: build frontend, install service,
  bake index) + `make -C service demo` local one-shot. Deploy target decided
  with Misha (fly.io/railway) — NOT auto-deployed without approval.

## T3 AMENDMENT (2026-07-19, supersedes the linear agent design above)

The deep-dive agent is a **code-mode agent** modeled on
`~/Development/personal/competitions/sample-agents/ecom-py` (read `runtime.py` and
`agent.py` there — adapt the architecture, not the ecom domain code):

- **pydantic-ai** Agent (deps: `pydantic-ai-slim[openai]`, `pydantic-monty` — both
  PyPI) with ONE action tool: `run_python(code)` executing in a **Monty sandbox**.
  Model via OpenRouter (OpenAI-compatible: base_url https://openrouter.ai/api/v1,
  api_key OPENROUTER_KEY, model OPENROUTER_MODEL default anthropic/claude-sonnet-4.5).
- Sandbox external functions (the agent writes Python that loops/aggregates over
  these; Monty = Python subset, no imports/classes):
  - `sql(query)` — **read-only** against the vcb.sqlite index (open with
    `file:...?mode=ro`); the T1 index IS the agent's database (candidates,
    trajectories, evidence, claims, FTS search).
  - `gh_profile(login)`, `gh_repos(login)`, `gh_events(login)` — GitHub REST via
    httpx, token from `gh auth token` if available; disk-cached.
  - `hn_search(query)` — HN Algolia; `web_search(query)` — SerpAPI iff SERPAPI_KEY.
  - `add_evidence(event_type, ts, detail, url, repo_name=None)` → returns
    `evidence_id` ("live-"+hash); stores into the run's evidence store.
  - `draft_claim(text, evidence_refs, confidence, verification_status,
    contradictions=[])` — **validates against the claim schema at the boundary and
    REJECTS any evidence_ref not present in the run's evidence store or the index.**
    Fabrication becomes structurally impossible, not merely prompted-against.
  - `note_gap(text)`, `set_dimension_note(dimension, ...)`.
- Completion via typed output tool `finalize_run(summary, outcome)` (outcomes:
  OK | INSUFFICIENT_EVIDENCE | ERROR) — validates the full run doc before persisting.
- **Middleware stack around every sandbox function call** (port ecom-py's
  policy/provenance/error-translation middleware): per-run limits (max tool calls,
  max GH requests, max SQL chars, single statement, SQL deny patterns as
  defense-in-depth on top of the ro connection), output truncation, errors returned
  as navigable `{"error": {...}}` dicts (never escaping exceptions), and
  `__provenance__` tagging with trust levels — fetched public content (READMEs, HN
  text) is UNTRUSTED_TOOL_OUTPUT: evidence only, never instructions (prompt-injection
  guard; keep ecom-py's system-prompt language for this).
- **The audit log IS the SSE step stream**: every middleware-audited call emits a
  step event (kind: fetch|sql|evidence|claim|gap|reason) onto the run's queue;
  `run_python` code blocks emit a `reason` step with the code. The replay/cache
  design from the original T3 section is unchanged.
- Tests: pydantic-ai TestModel (or FunctionModel) + recorded HTTP fixtures; NO
  network, NO real key. Verify: a claim citing a nonexistent evidence_id is rejected;
  SQL mutation attempts are denied; audit events map 1:1 to persisted steps.
- Agent code lives in `service/src/vcb_service/agent/`; runtime limits env-tunable.

## Rules

- Same politeness rules as main thread: cached, single-threaded, back-off; no ToS
  violations (no LinkedIn/X scraping).
- No network in tests. Every Codex handoff + verification logged in
  docs/thread2/PROGRESS.md with timestamps.
- Do not modify anything outside `service/`, `frontend/`, `docs/thread2/`,
  `data/` (gitignored), `config/thesis.json` (only if service needs a copy —
  prefer `--thesis` flag).

## D1 OPTIONAL merge-contract addendum (2026-07-19)

The frozen merge contract above is unchanged. Real P4/P5 producers MAY add these
fields incrementally; every field in this addendum is **OPTIONAL in upstream data**,
and the index accepts candidate rows that omit them:

- Candidate `recognition`: nullable `{month: "YYYY-MM", kind:
  "yc_batch"|"seed_round"|"press", label: str}` for the first conventional public
  signal. Omitted/null means no recognition has been observed yet.
- Candidate `score_components`: 4–6 `{key, label, contribution}` rows whose
  contributions sum to `current_score` within 0.001. Omitted means decomposition is
  not available yet; verification checks the invariant whenever components exist.
- `GET /api/v1/candidates` list items add normalized `recognition`, derived
  `lead_time_months: int|null`, and compact `trajectory: [{month, score}]` fields.
- `GET /api/v1/candidates/{login}` adds top-level normalized `recognition` and
  `score_components`; absent upstream values are returned as `null` and `[]`.

These are additive SQLite columns and response members only. Existing tables, fields,
filters, ordering, routes, and claim/evidence contracts retain their v1 behavior.
