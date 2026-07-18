# Spec P2 — Label pipeline: YC founders → GitHub handles

## Goal
`data/labels/founders.parquet`: one row per (founder, company) with a resolved GitHub
handle + confidence, and a founding-date estimate. This is the supervised signal for the
whole project. Precision matters more than recall — a wrong handle poisons training.

## Verified facts (Claude, 2026-07-19 ~02:15, do not re-derive)
- `https://yc-oss.github.io/api/companies/all.json` → 6,055 companies, updated daily.
  Fields include: name, slug, batch, website, one_liner, long_description, team_size,
  status, industries, regions, launched_at, url. NO founder data.
- `https://www.ycombinator.com/companies/<slug>` embeds Inertia JSON in a `data-page`
  HTML attribute (HTML-escaped). Parse: regex `data-page="(.*?)"` → `html.unescape` →
  `json.loads` → recursive search for `founders` key. Founder objects:
  `{full_name, founder_bio, title, linkedin_url, twitter_url, user_id, ...}`.
  NO github_url field — resolution is via GitHub/SerpAPI (below).
- ClickHouse playground `github_events` covers 2011-02 → yesterday (for P3; not needed
  here except: do NOT hit it in P2).

## Pipeline stages (each a module in src/vc_brain/labels/, each resumable)

### Stage 1 — company list (`yc_companies.py`)
- Download all.json → cache `data/cache/yc/all.json` → normalize to
  `data/labels/companies.parquet`.
- Batch-date mapping: Winter=Jan 5, Spring=Apr 1, Summer=Jun 1, Fall=Sep 1 of the batch
  year → `batch_start_date`. Keep all batches (we filter downstream).

### Stage 2 — founder extraction (`yc_founders.py`)
- For companies in batches 2012→present, status != "Inactive" optional — include all.
- Fetch company page, parse founders as above. Politeness: single-threaded... max 3 rps
  (async semaphore ok), `User-Agent: vc-brain-research/0.1`, cache raw HTML to
  `data/cache/yc/pages/<slug>.html` (NEVER refetch cached), exponential backoff on
  429/5xx via tenacity, hard-stop after 20 consecutive failures.
- Prioritize batches DESCENDING (2026 → older): most recent are most valuable, so a
  partial run is still useful.
- Output checkpoint every 100 companies → `data/labels/founders_raw.parquet`.

### Stage 3 — GitHub handle resolution (`gh_resolve.py`)
Tokens: TWO GitHub tokens for rotation: `gh auth token` (maghamalyan) and
`gh auth token --user misha-supertruth` (verify this flag works; if not, use one).
Read them ONCE at start via subprocess; never log them.

Per founder (process batches descending, checkpoint every 50, fully resumable):
1. GitHub user search REST `GET /search/users?q="{full_name}" in:name` (quote the name);
   also try `in:fullname`. Take top ≤8 candidates. Respect search limit: 30 req/min per
   token; rotate tokens; sleep on `X-RateLimit-Remaining` < 2.
2. For each candidate `GET /users/{login}` (5000/hr per token) → score:
   - +0.50 twitter_username matches YC twitter handle (case-insensitive, strip @/URL)
   - +0.40 blog/website domain == company website domain (strip www)
   - +0.30 bio or company field contains company name (normalized substring)
   - +0.20 name token-set similarity ≥0.9 (full_name vs name)
   - +0.10 exactly one candidate returned by search
   - −0.30 login contains 'bot' or type != 'User'
3. If best score < 0.5 AND founder is from a 2022+ batch: SerpAPI fallback
   `q=site:github.com "{full_name}" {company_name}` — extract github.com/<login>
   candidates from organic results, score as above. **Global SerpAPI cap: 300 calls**
   (env `SERPAPI_CAP`, default 300; count persisted in checkpoint; unknown user quota).
4. Emit best candidate: `gh_login, gh_confidence (0..1 capped), resolution_method
   (search|serpapi|none), evidence (JSON string of matched signals)`. Keep ALL rows
   including unresolved (gh_login=null) — consumers filter by confidence.

### Stage 4 — assemble (`build_labels.py`)
Join stages → `data/labels/founders.parquet`:
`founder_name, company, slug, batch, batch_start_date, founding_date_est
(= batch_start_date − 9 months), t_cutoff (= batch_start_date − 12 months),
gh_login, gh_confidence, resolution_method, evidence, linkedin_url, twitter_url,
founder_bio, title, company_website, one_liner, team_size, status`.
Plus `data/labels/data_card.md`: row counts per batch, resolution rate by method &
batch-year, confidence histogram, timestamp, known limitations.

## CLI
`uv run python -m vc_brain.labels.run --stage all|companies|founders|resolve|build`
(idempotent; picks up checkpoints). Log progress lines every 50 items with rates.

## Tests (fast, no network: fixtures)
- data-page parsing on a saved fixture HTML (create from a real page during dev).
- batch-date mapping, domain normalization, scoring function unit tests (each signal).
- resumability: run stage on fixture, interrupt-simulate, rerun → no duplicates.

## Acceptance (Claude will verify — do not self-certify)
1. `uv run pytest` green.
2. companies.parquet ≈ 6k rows; founders_raw covering ≥ all 2022+ batches by morning.
3. Resolution running/resumable; ≥300 founders with gh_confidence ≥ 0.5 as early
   checkpoint (Claude spot-checks 25 before the full run continues).
4. No secrets in code, logs, or parquet. No unapproved network targets
   (only: yc-oss.github.io, ycombinator.com, api.github.com, serpapi.com).
