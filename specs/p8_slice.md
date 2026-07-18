# Spec P8 — End-to-end vertical slice (fixtures now, real data later)

Rubric targets: Investment Utility 30%, Trust 25%, UX 15% (see docs/rubric.md — 3-axis
never averaged; Trust Score is PER CLAIM; gaps flagged, never fabricated; thesis
configurable; inbound + outbound converge into one funnel).

## Data contracts (FROZEN — P4/P5 will produce these exact shapes; build fixtures now)

`data/scores/candidates.parquet`
: gh_login (str), founder_name (str|null), company (str|null), source
  (outbound_detector | inbound_application), current_score (f64 0-1),
  score_percentile, momentum_3mo (f64, signed), first_detection_month (date|null),
  status (candidate | screened | memo_ready)

`data/scores/trajectories.parquet`
: gh_login, month (date), score (f64 0-1)

`data/evidence/events.parquet`
: evidence_id (str, stable hash), gh_login, ts (datetime), event_type, repo_name,
  detail (str), url (str — e.g. https://github.com/{repo})

`data/memos/<slug>.json` — schema (pydantic models in src/vc_brain/memo/schema.py):
```json
{
  "company": str|null, "founder_logins": [str], "generated_at": iso,
  "sections": {
    "company_snapshot": {"text": str, "claim_ids": [str]},
    "investment_hypotheses": [{"text": str, "claim_ids": [str]}],
    "swot": {"strengths": [...], "weaknesses": [...], "opportunities": [...], "risks": [...]},
    "problem_product": {"text": str, "claim_ids": [str]},
    "traction_kpis": {"text": str, "claim_ids": [str]}
  },
  "claims": {"<claim_id>": {"text": str, "evidence_refs": [evidence_id|url],
             "confidence": float, "verification_status":
             "verified|single_source|unverified|not_disclosed",
             "contradictions": [str]}},
  "gaps": [str],
  "three_axis": {"founder": {"score": 1-10, "trend": "improving|stable|declining",
                 "claim_ids": [...]}, "market": {...}, "idea_vs_market": {...}}
}
```
`config/thesis.json`: {"sectors": [...], "stages": [...], "geographies": [...],
"check_size_usd": [min,max], "risk_appetite": str, "notes": str}

## Components (src/vc_brain/memo/ and src/vc_brain/dashboard/ ONLY)

1. **Fixtures** (`data/fixtures/`): 12 realistic synthetic candidates (mix of outbound
   detections at various scores/momenta + 2 inbound applications), trajectories (24mo),
   ~40 evidence events each, 3 full memos. Mark clearly synthetic (names like
   "Ada Lovelace (fixture)"). One fixture memo MUST demonstrate contradiction flagging
   and one MUST demonstrate honest gaps ("Traction & KPIs: not disclosed — pre-launch").

2. **Memo generator** (`memo/generate.py`): input = candidate + evidence rows (+
   optional application deck text) → OpenRouter chat call (env OPENROUTER_KEY from
   .env via python-dotenv; model env OPENROUTER_MODEL, default
   "anthropic/claude-sonnet-4.5") → memo JSON validated against schema. Hard rules in
   the prompt: every claim needs evidence_refs from the provided evidence ONLY;
   unknown → goes to gaps, never invented; required sections only, concise
   (rubric: padding counts against you). Cache responses by input-hash to
   data/cache/llm/. `--mock` flag uses fixture responses (tests use this; NO network
   in tests).

3. **Inbound intake** (`memo/intake.py`): given a PDF deck path + company name →
   extract text (pdfplumber, installed) → deck claims become evidence rows (source =
   deck page N, url = file#page=N) → same memo path. Deck claims default
   verification_status="single_source" unless corroborated by public evidence.

4. **3-axis screen** (`memo/screen.py`): deterministic scoring from evidence + memo
   claims (NOT LLM free-styling): founder axis from detector score + evidence density;
   market/idea axes LLM-assisted but must cite claim_ids; trend from trajectory slope.
   Never average the axes anywhere — not in code, not in UI.

5. **Dashboard** (`dashboard/build.py`): STATIC site generator (jinja2 + plotly,
   installed; embed plotly.js inline for offline use) → `site/` (gitignored? no —
   site/ can be committed for demo; keep small).
   - index.html: ranked candidate table (score, momentum arrow, source badge,
     first-detection), client-side thesis filter (reads thesis.json), clean
     investor-grade design: light, generous whitespace, system font stack, no
     framework bloat.
   - candidate/<login>.html: score trajectory chart with detection marker, evidence
     timeline (each item links to its GitHub/deck URL), memo rendered with per-claim
     trust badges (color by verification_status), gaps box rendered prominently
     (honesty as a feature), 3-axis panel with trends.
6. CLI: `uv run python -m vc_brain.dashboard.run --fixtures` builds the whole slice
   from fixtures end to end.

## Tests
Schema validation round-trips; memo generator in --mock mode (assert every claim has
evidence_refs, gaps preserved, no fabricated sections); screen determinism; dashboard
build produces valid HTML (parse with html.parser, assert key elements) from fixtures.

## Acceptance (Claude verifies)
1. pytest + ruff green; NO network or real key needed for tests.
2. `--fixtures` run produces a browsable site/ Claude will open and screenshot.
3. One real OpenRouter memo generated for one fixture candidate (Claude will run this
   personally to validate the live path and inspect quality).
4. Trust discipline visible in UI: per-claim badges, contradiction flag, gaps box.
