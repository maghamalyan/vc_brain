# Thread 2 — Demo Elevation Spec (D-round)

Reframe (Misha, 2026-07-19): the demo is a short video, so real-time is out as the
headline. The hero is **retrospective foresight** — historical cases where the model
flagged founders BEFORE any conventional signal (YC batch, funding press), proven in
the dashboard. Dashboard, memo presentation, and scoring visuals are explicit
challenge requirements — maximize them. Optimize for an investor reacting
"I want to use this." Live deep-dive stays as the "recent capture, hand-validated"
supporting act (replay), not the lead.

## D1 — Data + backend (contracts for everything below)

Fixtures (`data/fixtures/generate_fixtures.py`, regenerate json+parquet; keep
clearly synthetic; deterministic seed):
1. `recognition` per candidate: `{month: "YYYY-MM", kind: "yc_batch"|"seed_round"|
   "press", label: str}` — the first CONVENTIONAL public signal. Place it 6–18
   months AFTER first_detection_month for ~9 candidates (varying lead times, one
   dramatic 16–18mo case); 2 candidates with detection but recognition NOT YET
   (still unrecognized — "we're early" cases); 1 inbound with recognition before
   detection (honest miss — credibility). Lead time = recognition.month −
   first_detection_month.
2. `score_components` per candidate: 4–6 entries `{key, label, contribution}`
   (e.g. commit-burst cadence, external-contributor influx, README
   product-language shift, org formation, star velocity) with contributions
   summing to current_score ±0.001. Derive plausibly from each candidate's actual
   evidence mix (e.g. no contributor events → no contributor component).

Index (`vcb-index`): store both; extend `--verify` (components sum check;
recognition-after-detection counts reported). Bump nothing breaking: new
denormalized columns/tables only.

API:
- `/candidates` list items gain `recognition` and `trajectory` (compact
  `[{month, score}]` — 24 points × 12 candidates is tiny; powers honest client
  scrubbing) and `lead_time_months: int|null`.
- `/candidates/{login}` detail gains `recognition`, `score_components`.
- OpenAPI snapshot regenerated; contract documented as OPTIONAL fields so the
  main thread's real P4/P5 outputs can adopt them incrementally (merge contract
  unchanged otherwise).

Tests: fixture regeneration determinism, components-sum validation, recognition
lead-time invariants, endpoint shapes.

## F1 — Radar: honest time machine + foresight proof (frontend)

1. KILL the `scoreAtMonth` approximation: scrub-time score = real trajectory value
   at the selected month (from list-response trajectories); momentum at month =
   trajectory slope over trailing 3 months. Sparklines/scores/ranks all reflect
   the true historical state — this is the leakage-free thesis made visible.
2. Scrub-aware markers: when the scrubber is before a candidate's
   first_detection_month, their row shows "not yet detected" state (dimmed score);
   crossing detection month lights the row (lime accent flash, reduced-motion safe).
3. Lead-time chip per row where recognition exists: "flagged 14 mo before seed".
   Unrecognized-yet cases: lime "still ahead of the market" chip.
4. **Foresight strip** ("Proof" section) on the radar page under the hero: the top
   3 lead-time cases as cards — mini trajectory with detection marker, recognition
   marker, shaded lead-time band between them, headline number ("14 months
   early"), one-line evidence hook, click-through to record. The honest-miss case
   appears as a small footnote card ("what we miss, we show").
5. Topbar dead navs: "Portfolio" → "Proof" (anchors to the foresight strip or a
   dedicated /proof route listing all cases sorted by lead time); "Thesis" →
   /thesis (F3). No dead links remain.

## F2 — Record page: memo/scoring visuals (frontend)

1. Trajectory chart: add recognition marker (ink dashed) + shaded band between
   detection (amber) and recognition; headline chip above chart: "Detected
   Mar 2025 · Seed announced May 2026 · **14 months ahead**".
2. **Score waterfall**: clicking the big numeral (and a small "why?" affordance)
   opens a decomposition panel — horizontal waterfall bars per score_component
   (label, contribution, running total), each bar hoverable → the evidence events
   of that component's type (reuse popover). Never shown as percentages of an
   average — components of the signal score only.
3. **Inline citations in memo prose**: each memo section renders its claim_ids as
   numbered superscript chips [1][2] inline at the end of the text; same
   popovers; a per-section confidence rollup dot (min claim confidence, honest).
   Axis segmented bars: hovering an axis row highlights/links its claim_ids.
4. **Provenance graph panel** ("How this memo knows what it knows"): three-column
   linkage diagram — memo sections → claims → evidence events — thin curved
   connectors, hover a node to light its paths, click navigates (evidence →
   timeline month / external URL). Pure SVG from existing memo JSON; no graph lib.
   This is the trust architecture literally drawn.
5. **Live-capture merge-back**: a "Recent capture (hand-validated)" section
   listing claims from cached deep-dive runs (`/deepdive/runs?entity_id`),
   provenance-chipped `live`; live evidence rows appear on the timeline as LIME
   nodes (forest = backtest, lime = capture — the two-provenance story visible).
6. Fix (verify in real Chrome) palette Enter-to-navigate; palette "Deep dive on…"
   verb actually POSTs /deepdive then routes to the run view.

## F3 — Thesis page (small)

/thesis: view + edit the mandate (sectors/stages/geo chips toggles, check-size,
weight sliders), persisted client-side (localStorage over the served thesis.json
baseline, with "reset to fund defaults"), used live by the radar ranking. Banner
notes config is local to the browser (no server writes).

## Bar

Same review discipline: Claude screenshot-audits each round against the
references and the "investor says wow" bar; bounces are expected. Kitsch guard
unchanged. All numbers real (fixture-derived) — no invented values in UI code.
