# Overnight Progress Journal

## 2026-07-19 02:04:27 +04

Created the P1 project scaffold: Docker and Make entry points, runtime and development
dependencies, package namespaces, and smoke-test coverage.

## 2026-07-19 02:05:21 +04

Verified `uv sync --frozen`, `uv run pytest -q` (1 passed), and
`uv run ruff check src tests` (all checks passed).

## 2026-07-19 02:08 — Claude verification: P1 ACCEPTED
pytest 1 passed, ruff clean, docker build OK (image vc-brain). Deps pre-added for parallel tasks: jinja2, plotly, pdfplumber. Committing checkpoint.

## 2026-07-19 02:25:19 +04 — P8 end-to-end vertical slice

Implemented the fixture-to-dashboard opportunity funnel within the P8-owned paths:
frozen memo contracts, evidence-constrained OpenRouter generation with deterministic
mock responses and input-hash caching, inbound PDF evidence extraction, deterministic
independent-axis screening, 12-candidate synthetic fixture corpus, configurable thesis,
and a polished offline static investor dashboard. Trust is visible per claim, including
source links, confidence, verification status, contradiction flags, and prominent known
gaps.

Verification: `uv run pytest -q` → 38 passed; `uv run ruff check src tests` → clean;
`uv run python -m vc_brain.dashboard.run --fixtures` → 17-file offline site built with
12 ranked candidates, local Plotly trajectory, three-axis screen, evidence timeline,
memo trust badges, contradiction treatment, and honest pre-launch gaps.

## 2026-07-19 02:36 — Claude verification: P8 slice ACCEPTED (fixtures + live path)
38 tests + ruff green (independent run). Site rebuilt from scratch; index + candidate pages inspected in browser: ranked table, thesis filter, trajectory charts, per-claim trust badges, contradiction flag, gaps box all render. Live OpenRouter memo test EXPOSED A BUG (schema drift, no retry) — Claude fixed generate.py with retry-on-validation-error feedback loop; live memo then passed: 10 claims all evidence-backed, 11 explicit gaps, 5 required sections. Real-data wiring pending P4/P5.
