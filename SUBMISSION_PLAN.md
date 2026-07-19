# VC Brain submission plan

Submit only after the live demo, repository, and three videos pass the final checklist. The written fields can proceed in parallel because the repository already contains verified evidence for them.

## Current gap summary

| Workstream | Status | Submission blocker |
| --- | --- | --- |
| Written fields | Draftable from verified project evidence | Final wording and any platform character limits |
| Live demo | Built locally, not hosted | Yes |
| GitHub repository | Local Git repository has no remote | Yes |
| Demo and tech videos | No MP4 or MOV files found | Yes |
| Team picture and team video | No team media found | Yes |
| Team member IDs and fun moment | Need team input | Yes |
| Final demo branch | Polished demo is in `worktree-live-intel`, 17 commits ahead and 4 behind `overnight/poc`; it also has uncommitted changes | Yes |

## Recommended execution order

1. Freeze the submission build: finish and commit the live-intel changes, reconcile the two branches, run tests, and tag the exact demo revision.
2. Publish the GitHub repository after checking tracked files and history for secrets or oversized private data.
3. Deploy the frozen demo and verify it in an incognito browser on desktop and mobile.
4. Finalize the written submission against that exact build.
5. Capture the product demo and tech video; edit and export both under 60 seconds.
6. Capture the team picture and team video; collect account IDs and the fun-moment anecdote.
7. Upload every artifact early, reopen each uploaded file, and complete the final submission check.

## Plan for all submission fields

| # | Field | Current state | Action | Definition of done |
| ---: | --- | --- | --- | --- |
| 1 | Team picture | Missing | Take one well-lit landscape photo with every submitting member visible. Also export a square crop in case the platform crops thumbnails. | Final JPG or PNG opens correctly, names match the submitted team, and faces remain visible in both crops. |
| 2 | Demo video | Missing | Record a scripted product story from the frozen hosted build. Use the 58-second outline below. | MP4 or MOV, at most 60 seconds, readable at normal playback speed, clear audio, no loading stalls, and no local URLs or secrets on screen. |
| 3 | Tech video | Missing | Record the architecture, temporal leakage controls, model evaluation, trust layer, and stack using the 58-second outline below. | MP4 or MOV, at most 60 seconds, technical claims match the repository, and metrics include their retrospective/case-control caveats. |
| 4a | Live project demo link | Missing | Deploy the Svelte frontend, FastAPI API, and frozen SQLite read model from the final branch. Prefer a deterministic data-backed demo; make live enrichment optional so third-party failures cannot break judging. | Public HTTPS URL works without login in an incognito browser; primary radar, candidate record, thesis page, and proof interactions work. |
| 4b | Team video | Missing | Record every member giving their name, role, and one concrete contribution; close with why the team built VC Brain. Keep it under 60 seconds unless the platform states another limit. | MP4 or MOV opens after upload, includes every registered member, and matches the account list. |
| 4c | Most fun moment | Missing | Ask each member for one specific moment, then select the most vivid shared anecdote. Use a setup, surprise, and payoff in 2–3 sentences. | True, specific, human, and understandable without internal project context. |
| 5 | Project title | Candidate exists | Use **VC Brain**. Optional display tagline: **Find founders before the market does.** | Same title appears in the submission, product header, video title card, and README. |
| 6 | Short description | Needs submission copy | Start from: “VC Brain finds promising technical founders before conventional venture signals appear, then turns public evidence into thesis-filtered, traceable investment memos.” Adjust only for the platform limit. | Fits the character limit, states user + outcome + differentiator, and avoids unsupported performance claims. |
| 7 | Problem & challenge | Evidence exists in README and rubric | Condense the cold-start problem: conventional venture sourcing starts after company formation, funding, or network recognition; fragmented early signals are hard to compare and easy to overinterpret. Explain that the challenge is to detect early founder behavior without future-data leakage and produce a decision a human can audit. | One concise section with the status quo, affected user, stakes, and technical challenge. |
| 8 | Target audience | Needs submission copy | Name seed and pre-seed venture investors first; include scouts, accelerators, and emerging managers as secondary users. State the job: discover, screen, and prioritize technical founders before conventional signals. | Audience is specific and tied to an actual workflow, not “all investors.” |
| 9 | Solution & core features | Evidence exists | Present five features: retrospective founder radar; thesis engine; independent Founder/Market/Idea-vs-Market screening; evidence-backed memo with per-claim trust; inbound deck and outbound discovery in one funnel. Mention the proof/time-machine and provenance views shown in the current demo. | Features match visible, working demo paths and fit in a scan-friendly list. |
| 10 | Unique selling proposition | Needs final wording | Use: **VC Brain does not summarize companies the market already knows. It identifies pre-track-record founder signals, tests them out of time, and shows the evidence behind every investment claim.** | One defensible differentiator covering timing, validation, and trust. |
| 11 | Implementation & technology | Strong source material exists | Explain the flow: GH Archive/YC/Hacker News evidence → cached Polars/ClickHouse pipelines → leakage-bounded person-month features → logistic/LightGBM temporal evaluation → immutable SQLite read model → FastAPI → Svelte dashboard → Pydantic-validated evidence memos and optional agent deep dive. | Architecture matches the final merged repository and names how provenance and time cutoffs are enforced. |
| 12 | Results & impact | Verified results exist | Lead with held-out results: LightGBM within-month PR-AUC 0.2418 vs 0.0951 base and 0.1327 shuffled-label null; 25/50 precision@50 in the sampled pool; 124 rising-signal founders detected a median 15 months before the YC batch. Include that this is a retrospective case-control backtest, not prospective deployment precision. | Every number is sourced from the checked-in report and carries the correct caveat. |
| 13 | Most fun moment answer | Needs team input | Reuse the anecdote collected for 4c. A promising theme to consider, only if true: the model failed its first null test, and the team turned that surprise into a stronger same-month evaluation instead of hiding it. | Team confirms the story happened and approves the wording. |
| 14 | Additional information | Optional, useful | Add the strongest trust details: two linkage audits found zero wrong-person matches across 50 samples; the product exposes missing evidence and contradictions; limitations include public GitHub coverage and YC-biased labels. Optionally link to the evaluation report. | Adds credibility without repeating the main description or introducing a new unsupported claim. |
| 15 | Live project URL | Missing | Use the verified URL from 4a. Treat items 4a and 15 as the same value unless the form distinguishes a showcase page from the app. | HTTPS URL has no expiry, auth prompt, mixed-content warning, or cold-start failure during a timed test. |
| 16 | GitHub repository URL | Missing | Reconcile branches, commit the demo, create the public repository, add the remote, and push the tagged submission revision. Update the README for the Svelte/FastAPI application and one-command local startup. | Public URL opens logged out; default branch builds; README has setup, architecture, demo URL, results, limitations, and license/usage terms. |
| 17 | Technologies/tags | Draftable | Primary tags: **Python, FastAPI, Svelte, TypeScript, LightGBM, scikit-learn, Polars, ClickHouse, SQLite, Pydantic AI, OpenRouter, Playwright, Docker**. Trim to the form’s limit and prefer technologies visible in the final build. | Tags match checked-in dependencies and platform limits. |
| 18 | Additional tags | Draftable | Suggested: **Venture Capital, Founder Sourcing, Predictive Analytics, Explainable AI, Agentic AI, Due Diligence, Cold Start, Temporal Machine Learning, Evidence Provenance**. | Use the smallest high-signal set allowed; no near-duplicate tags. |
| 19 | Team member by Account ID | Missing | Collect each member’s exact platform Account ID in a shared list, add them, and ask each person to confirm the project appears in their account before submission. | Every person in the picture/video is registered, every invite is accepted, and names/roles are consistent across the form. |

## 58-second demo video outline

| Time | Visual | Voiceover goal |
| --- | --- | --- |
| 0–5s | Title, then radar | “Venture sourcing usually starts after the market already knows. VC Brain looks for founders earlier.” |
| 5–16s | Scrub historical time on the radar; a candidate crosses the detection line | Show that scores use the historical trajectory at that date, not future information. |
| 16–27s | Proof card with detection and later recognition markers | State one verified lead-time case and frame it as retrospective foresight. |
| 27–40s | Open the candidate record and score waterfall | Show why the candidate was flagged and link a signal to raw evidence. |
| 40–51s | Memo citations and provenance graph | Show independent screening axes, per-claim confidence, contradictions, and missing data. |
| 51–58s | Thesis controls and closing frame | “A thesis-filtered, auditable pipeline from early public signal to an investor-ready decision.” |

## 58-second tech video outline

| Time | Visual | Voiceover goal |
| --- | --- | --- |
| 0–6s | One-line architecture diagram | Public event streams become person-level, time-bounded evidence. |
| 6–17s | Data pipeline and cutoff rule | YC labels, GH Archive, and Hacker News are cached and normalized; every feature row excludes events at or after its cutoff. |
| 17–30s | Model/evaluation chart | Logistic regression and LightGBM use an out-of-time split; a shuffled-label null gate blocks invalid exports. State the primary PR-AUC result with its base and null. |
| 30–41s | SQLite/FastAPI/Svelte flow | The evaluated output becomes an immutable SQLite read model served through FastAPI to the Svelte interface. |
| 41–52s | Memo/provenance and agent trace | Pydantic contracts reject uncited claims; evidence IDs, gaps, contradictions, and optional agent steps remain traceable. |
| 52–58s | Test/build screen and closing architecture | Name the reproducible stack and close on “early signal, honest evaluation, auditable decision.” |

## Final submission gate

- [ ] Final demo changes are committed and branches reconciled.
- [ ] Tests, frontend checks, and production build pass on the tagged revision.
- [ ] Public repository contains no `.env`, credentials, private caches, or oversized generated data.
- [ ] Live URL works logged out in two browsers and on a phone-sized viewport.
- [ ] Demo, tech, and team videos use accepted formats and stay within confirmed limits.
- [ ] Uploaded videos play from beginning to end inside the submission platform.
- [ ] Team picture renders correctly after platform cropping.
- [ ] All team Account IDs are added and accepted.
- [ ] Written metrics match the final evaluation report and preserve caveats.
- [ ] All required fields remain present after saving and reopening the submission.
- [ ] A team member other than the submitter performs the final review.
