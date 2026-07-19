# VC Brain — submission copy pack

Companion to [SUBMISSION_PLAN.md](SUBMISSION_PLAN.md). Every number below comes from
`data/eval/report.md` / README and carries its caveat. Fields are numbered to match the
plan's field table. Where a platform has a character limit, use the **strip-down**
variant; otherwise use the **full** variant.

---

## 5. Project title + tagline

**Title:** VC Brain

**Tagline (LOCKED, Misha 2026-07-19):** **Find founders before the market does.**
Use it everywhere — form, product header, video title card, README, deck.
("Early signal. Honest evaluation. Auditable decision." is the closing line, not the tagline.)

---

## 6. Short description

**One-liner (~95 chars):**
> VC Brain spots future founders in public data before the market does — and shows its evidence.

**Strip-down (~250 chars):**
> VC Brain finds promising technical founders before conventional venture signals exist. It reads public GitHub behavior, tests its predictions out of time against real YC outcomes, and turns the signal into thesis-filtered, evidence-cited memos.

**Full:**
> VC Brain finds promising technical founders before conventional venture signals appear. It watches public behavior — GitHub activity, received attention, project trajectories — before a company, a round, or a track record exists. Predictions are validated on a strict out-of-time backtest against real Y Combinator outcomes, and every output ends in a thesis-filtered investment memo where each claim links to the raw evidence behind it.

---

## 7. Problem & challenge

**Full:**
> Venture sourcing starts late. By the time a founder has a company, a financing round, or a warm introduction, every fund can see them — and the price reflects it. The earliest signals of founding intent exist much sooner, in a person's public activity, but they are fragmented, hard to compare across people, and dangerously easy to overinterpret.
>
> The technical challenge is twofold. First, detect founder-predictive behavior in people with no track record at all — the genuine cold-start case — without letting any future information leak into the prediction. Second, turn a statistical signal into a decision a human investor can actually audit: every claim traceable to its evidence, every gap and contradiction visible, nothing confabulated.

**Strip-down:**
> Venture sourcing starts after the market already knows. The earliest founder signals live in fragmented public activity that is easy to overinterpret. The challenge: detect pre-track-record founder behavior without future-data leakage, and produce a decision a human can audit claim by claim.

---

## 8. Target audience

**Full:**
> Seed and pre-seed venture investors are the primary users: the people whose returns depend on seeing a founder before the rest of the market prices them in. Scouts, accelerators, and emerging managers are secondary users with the same job and thinner networks. The workflow VC Brain serves is concrete: discover technical founders early, screen them against a fund's thesis, and prioritize who to meet — before conventional signals exist.

**Strip-down:**
> Seed and pre-seed VCs first; scouts, accelerators, and emerging managers second. The job: discover, screen, and prioritize technical founders before conventional signals appear.

---

## 9. Solution & core features

> VC Brain covers the path from raw public signal to investor-ready decision:
>
> - **Retrospective founder radar.** A time-scrubbable radar scores people month by month using only what was public at that date. Scrub back in time and watch real founders cross the detection line — a median of 15 months before their YC batch.
> - **Thesis engine.** Candidates are filtered against an explicit, editable investment thesis, so the queue reflects the fund's strategy rather than raw scores.
> - **Independent three-axis screening.** Founder, Market, and Idea-vs-Market are scored as separate axes with trends — never averaged into one misleading number.
> - **Evidence-backed memos with per-claim trust.** Every memo claim carries a citation into the underlying evidence; contradictions and missing data are shown, not smoothed over. Schema contracts reject any uncited claim.
> - **One funnel for inbound and outbound.** Uploaded decks and outbound public-signal discovery converge into the same thesis filter, screening axes, and memo contract, with single-source deck claims flagged until corroborated.

---

## 10. Unique selling proposition

**Final (from plan, keep as is):**
> VC Brain does not summarize companies the market already knows. It identifies pre-track-record founder signals, tests them out of time, and shows the evidence behind every investment claim.

**Alternative (sharper, if a shorter field appears elsewhere):**
> Other tools rank companies the market has already found. VC Brain finds the founder first — and can prove why.

---

## 11. Implementation & technology

**Full:**
> Public event streams (GH Archive via the public ClickHouse playground, the YC founder directory, Hacker News) are cached and normalized into person-level evidence with Polars pipelines. Every feature row enforces a hard temporal rule — no event at or after that person's cutoff — checked in SQL, in data assembly, and in tests. A discrete-time hazard model (logistic regression vs LightGBM, selected on temporal validation) is evaluated on an out-of-time split, gated by a shuffled-label null: if randomness beats the configured limit, the run raises an error and publishes nothing. Evaluated output freezes into an immutable SQLite read model served by FastAPI to a Svelte dashboard. Memos are generated through OpenRouter under Pydantic contracts that reject uncited claims, plus a mechanical check that every citation exists in the supplied evidence set. An optional agent deep-dive stays fully traceable. The whole stack builds in Docker and passes 67 tests.

**Strip-down:**
> GH Archive/YC/HN evidence → cached Polars/ClickHouse pipelines → leakage-bounded person-month features → logistic/LightGBM temporal evaluation with a shuffled-label release gate → immutable SQLite read model → FastAPI → Svelte dashboard → Pydantic-validated, per-claim-cited memos with optional agent deep dive.

---

## 12. Results & impact

**Full:**
> On a held-out cohort of 2,765 people (690 labeled founders, YC batches 2024+), the selected LightGBM model reaches a within-month PR-AUC of **0.2418** — 2.5x the 0.0951 base rate and clearly above the 0.1327 shuffled-label null. Precision@50 is **0.50 (25/50)**, twice the sampled pool prevalence. The backtest detected **72.3%** of held-out founders; among detections that first crossed the threshold inside the observation window, **124 founders were flagged a median of 15 months before their YC batch**.
>
> Honesty caveats, stated up front: this is a retrospective case-control backtest, not prospective deployment precision; the ~25% pool prevalence is not a deployment base rate; and an ablation shows account tenure carries 74.5% of model gain — the detector is substantially "maturity + consistency + received attention," and we say so rather than dressing it up.

**Strip-down:**
> Held-out within-month PR-AUC 0.2418 vs 0.0951 base and 0.1327 shuffled-label null; precision@50 = 25/50 (2x pool prevalence); 124 rising-signal founders flagged a median 15 months before their YC batch. Retrospective case-control backtest — not prospective deployment precision.

---

## 14. Additional information

**Full:**
> Trust is the product, not a feature. Two independent human audits of founder-to-GitHub linkage found zero wrong-person matches across 50 samples (at least 48/50 strict). The shuffled-label null is a release gate, not a footnote: when an early version of it fired — the model was exploiting calendar composition, not people — we replaced the primary metric with a weaker but defensible within-month one and kept the old number in the report for transparency. The memo layer surfaces missing evidence and contradictions instead of hiding them. Known limitations: GitHub-only behavioral coverage, YC-biased labels, and case-control calibration assumptions — all documented in the evaluation report checked into the repository.

---

## 17–18. Tags

Primary (trim to platform limit, in this order):
`Python, FastAPI, Svelte, TypeScript, LightGBM, scikit-learn, Polars, ClickHouse, SQLite, Pydantic AI, OpenRouter, Docker`

Additional: `Venture Capital, Founder Sourcing, Predictive Analytics, Explainable AI, Temporal Machine Learning, Evidence Provenance, Cold Start`

---

## 4c / 13. Most fun moment — candidates

Decision (Misha 2026-07-19): candidate A (null-gate story) is **out** — too technical
for this field. Recommend **C** (time machine): human, visual, and it matches the demo.
**Confirm the facts before submitting.**

**B. The 3am audit:**
> At some absurd hour we hand-checked 50 founder-to-GitHub matches against live profiles, fully braced to discover the pipeline had been confidently studying the wrong people all night. Zero wrong-person matches. We celebrated like it was a demo day, and it was just a spreadsheet.

**C. The time machine works, retroactively (recommended):**
> The first time we scrubbed the radar back to 2023 and watched a real founder's dot cross the detection line — fifteen months before YC found them — someone said "we have a time machine." Then someone pointed out it only drives backwards. We're keeping it.

---

## Jokes (deck, videos, Q&A — all grounded in true facts)

- "Our strongest feature turned out to be account tenure. Yes — we built a machine learning system and it discovered that old GitHub accounts are old. We report that honestly, which we're told is the novel part."
- "Our first null check was passed with flying colors… by the null. Shuffled labels scored above baseline, which means our model was briefly outperformed by random noise with a calendar. We fixed the metric instead of the narrative."
- "We found 124 founders a median of 15 months before Y Combinator did. Unfortunately, we found them in 2026, retrospectively. Time machine: still in the backlog."
- "Half of our top 50 picks became YC founders. In this pool, guessing gets you a quarter. We'll take 2x over vibes."
- "Fifty hand-audited identity matches, zero wrong people. Because 'we invested in the wrong Dave' is not a memo anyone wants to write."
- "YC also found these founders, to be fair. They found them with money, which we hear is more persuasive."
- (self-deprecating closer) "We ran the pipeline overnight. The model learned to predict founders; we learned to predict sunrise."

Usage guidance: at most one joke in the demo video (the time-machine one fits the
0–16s radar scrub), one in the deck (tenure or null joke on the trust slide), none in
the tech video — it should read as rigor.

---

## Word-for-word video scripts (58s each, ~145 words)

### Demo video — AS-RECORDED voiceover cue sheet

A screen recording matching this cue sheet exists (54.3s, 1920×1080, silent audio
track — record narration over it, or replace the audio). Cues follow the actual
footage timestamps:

| Time | On screen | Say |
| --- | --- | --- |
| 0:00–0:02 | Title card | (beat) "VC Brain." |
| 0:02–0:07 | Radar hero: "See the founder before the round." | "Venture sourcing usually starts after the market already knows — a company, a round, a warm intro. VC Brain looks earlier." |
| 0:07–0:18 | Time scrubber rewinds to 2023, rows dim; scrubs forward, candidates flash and re-rank | "This is the founder radar. Scrub back in time, and every score uses only what was public that month — nothing from the future leaks in. Roll forward, and candidates light up the month their behavior crosses the detection line." |
| 0:18–0:23 | Foresight proof cards (48 / 23 / 23 months early) | "Verified on held-out founders: flagged months — sometimes years — before Y Combinator found them. Retrospectively, and we say so." |
| 0:23–0:32 | Search palette → Robert Chandler record → "why this score?" waterfall | "Open a record and the score explains itself — every component named, checkable, and linked to evidence." |
| 0:32–0:40 | Memo with live citation popover + "Not observed" honesty layer | "The memo cites every claim, shows its confidence — and lists what was never observed instead of papering over it." |
| 0:40–0:47 | Provenance graph: hovered claim lights its paths | "Section, claim, raw public event — the whole decision traceable in one view." |
| 0:47–0:52 | Thesis page: fund mandate and ranking weights | "All of it filtered through your fund's thesis." |
| 0:52–0:54 | Closing card | "Early signal. Honest evaluation. Auditable decision." |

### Demo video — original outline (kept for re-shoots)

| Time | On screen | Say |
| --- | --- | --- |
| 0–5s | Title card → radar | "Venture sourcing usually starts after the market already knows — a company, a round, a warm intro. VC Brain looks earlier." |
| 5–16s | Scrub time backwards; candidate crosses line | "This is the founder radar. Scrub back in time, and every score uses only what was public on that date — nothing from the future leaks in. Watch this candidate cross the detection line." |
| 16–27s | Proof card, detection + YC batch markers | "That crossing came fifteen months before this founder's YC batch. We verified lead times like this on a held-out cohort — retrospectively, and we say so." |
| 27–40s | Candidate record, score waterfall, click a signal | "Open the record and the score explains itself. Each signal links straight to the raw public event behind it." |
| 40–51s | Memo citations, provenance view | "The memo screens Founder, Market, and Idea-versus-Market independently, cites every claim, and shows contradictions and missing evidence instead of hiding them." |
| 51–58s | Thesis controls → closing card | "From early public signal to an auditable, investor-ready decision. That's VC Brain." |

### Tech video

| Time | On screen | Say |
| --- | --- | --- |
| 0–6s | One-line architecture diagram | "VC Brain turns public event streams into person-level, time-bounded evidence." |
| 6–17s | Pipeline + cutoff rule | "YC labels, GH Archive, and Hacker News are cached and normalized. Every feature row enforces one hard rule: no event at or after its cutoff — checked in SQL, in assembly, and in tests." |
| 17–30s | Evaluation chart | "Logistic regression and LightGBM train on an out-of-time split. A shuffled-label null is a release gate: if randomness beats the limit, nothing ships. Held out: within-month PR-AUC 0.24 against a 0.10 base and a 0.13 null." |
| 30–41s | SQLite → FastAPI → Svelte flow | "Evaluated output freezes into an immutable SQLite read model, served by FastAPI to a Svelte dashboard." |
| 41–52s | Memo contract + agent trace | "Pydantic contracts reject any memo claim without a citation from the supplied evidence. Gaps, contradictions, and agent steps stay traceable." |
| 52–58s | Test/build screen → closing diagram | "Sixty-seven tests, one Docker build. Early signal, honest evaluation, auditable decision." |

### Team video (template, <60s)

Each member, ~12s: "I'm ___, I ___ [role]. I built ___ [one concrete artifact — e.g.
'the leakage-gated feature pipeline' / 'the Svelte radar and time scrub']."
Close together, ~8s: "We built VC Brain because the best founders are visible before
the market prices them — if you're honest about what the data can prove."

---

## Strip-down: minimum viable submission path

If time gets tight, this is the cut order. Everything above the line still yields a
complete, credible submission.

**Keep (non-negotiable):**
1. Frozen, deterministic demo deployed from committed data — live enrichment OFF by
   default so no third-party failure can break judging.
2. One clean take of each video, screen recording + voiceover, trimmed only. No editing
   polish. Scripts above are already timed.
3. Strip-down copy variants for every written field.
4. Public repo with secrets/large-data check and the existing README.

**Cut in this order if needed:**
1. Agent deep-dive from the demo path (keep it in the repo/README) — it's the flakiest
   surface.
2. Provenance-graph flourish in the demo video (the memo citation view already carries
   the trust story).
3. Square team-photo crop, tagline debates, extra tags.
4. Mobile-viewport polish (still verify it loads; don't optimize).

**Never cut:** the caveats on metrics, the null-gate story, the leakage framing. They
are the differentiator, not overhead.

---

## Presentation deck

Principles: max 7 slides, one idea and at most one number per slide, dark UI
screenshots on dark background, no bullet walls — the spoken track carries the detail.

### Main deck (7 slides, ~3 min)

| # | Headline on slide | Visual | Speaker line |
| --- | --- | --- | --- |
| 1 | **VC Brain** — Find founders before the market does. | Radar screenshot, dimmed | "Sourcing starts too late. We start earlier." |
| 2 | **By the time you can see them, so can everyone.** | Timeline: idea → *public activity* → company → round → everyone's radar | "Every conventional signal arrives after the price does." |
| 3 | **Founding behavior is public before founding is.** | One real (anonymized) trajectory rising toward a YC-batch marker | "GitHub behavior, months before the batch. That's the raw material." |
| 4 | **The time machine test.** | Radar with time scrubber; detection-line crossing | *Live demo moment or GIF:* "Every score uses only that month's data. 124 held-out founders crossed this line a median of 15 months before YC found them." |
| 5 | **0.24 vs 0.10 — and it beat honest randomness.** | Single bar chart: model 0.2418 / null 0.1327 / base 0.0951 | "Out-of-time split, shuffled-label null as a release gate. When an earlier null *fired*, we kept the weaker honest metric. (Also: our best feature is account age. We report that too.)" |
| 6 | **Every claim shows its evidence.** | Memo with per-claim trust badges, one contradiction visible | "Pydantic rejects uncited claims. Gaps and contradictions are displayed, not smoothed." |
| 7 | **Early signal. Honest evaluation. Auditable decision.** | Architecture one-liner + live URL + repo QR | "Deployed, tested, reproducible. Go scrub the radar yourself." |

### Lightning version (3 slides, ~60s)

1. **Find founders before the market does** — radar + time scrub.
2. **Proof:** 15-month median lead on held-out founders; 0.24 PR-AUC vs 0.13 null — with caveats on the slide, not hidden.
3. **Trust:** every claim cited, nulls gate releases, failures reported. URL + repo.

### Impressive moves (cheap, high-impact)

- **Scrub live.** The time scrubber is the single most memorable interaction — do it
  by hand on stage/video rather than showing a static chart.
- **Show the failure.** Slide 5's null-gate story is the credibility peak; judges see
  a hundred "0.9 AUC" decks and zero "our gate fired and here's what we did" decks.
- **One number per slide, huge.** 15 months. 0.24 vs 0.10. 50/50 audits, 0 wrong.
- **End on the URL.** The last thing on screen should be something a judge can open.

---

## Produced artifacts (2026-07-19)

- **Demo video draft:** 54.3s, 1920×1080 MP4 with intro/outro title cards and a silent
  audio track for voiceover. Recorded from the live app (real 100-founder index) with
  a scripted Playwright take; cue sheet above matches its timestamps.
- **Slide deck:** [docs/submission_deck.html](docs/submission_deck.html) —
  self-contained (screenshots embedded), 8 slides, arrow keys/click to navigate,
  `F` for fullscreen. Speaker lines are printed at the bottom of each slide.
- **Product tweak made for the video:** the radar time scrubber is now sticky
  (`frontend/src/styles.css`) so the time machine and the candidate rows share the
  frame — review and keep or revert.

## Settled decisions

- Team of two: Misha + one teammate. Misha handles team photo/video/IDs personally.
- Tagline locked: "Find founders before the market does."
- Fun moment: null-gate story rejected (too technical); use candidate C (time machine),
  pending truth check with the teammate.
- Demo deployment handled by Misha separately.

## Still open

1. **Platform + character limits** — determines full vs strip-down variant per field.
2. **Live demo URL + repo URL** — drop into deck slide 8, README, and field 15/16
   when they exist.
