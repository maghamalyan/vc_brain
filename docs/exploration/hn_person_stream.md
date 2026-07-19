# Person-Level HN Stream: Identity Links, Pre-Cutoff Launch Evidence, New Outcome Labels (Pod H, 2026-07-19)

**Question.** Wave-2 harvested company-title Launch/Show HN stories (106 stories,
15.1% of scored founders' companies). Extend HN to the *person* level for ALL 2,765
scored actors (690 founders, 2,075 controls): (1) how many actors have a linkable HN
account (`hn_username == gh_login`), founders vs controls; (2) do people author Show HN
posts *pre-t_cutoff* — public launching as gestation evidence, the cold-start signal —
and is it founder-predictive; (3) post-cutoff Show/Launch HN posts by "controls" as a
new outcome-label stream / label-noise detector.

**Method.** `src/vc_brain/labelnoise/hn_persons.py` (collection) +
`hn_person_eval.py` (numbers). For every cohort login (all lowercase, all unique):
HN Firebase user probe (keyless, cached, ≤2 req/s, identifying UA). For every existing
account: full story-submission history via one Algolia `author_<login>` query (cached).
Identity confirmed **conservatively, in tiers** (extending the linkage study's evidence
tiers; shared username alone is never enough):

| tier | evidence | available to |
|---|---|---|
| strong_github_link | HN about links `github.com/<login>` | both classes |
| strong_story_github_url | an authored story links `github.com/<login>/...` | both classes |
| strong_gh_blog_domain | GH profile blog domain in HN about, or ≥2 authored stories link it | both classes |
| strong_gh_name | GH profile display name (≥7 chars, 2+ words) stated in HN about | both classes |
| strong_company_domain / _name / _twitter / _founder_name | founders.parquet metadata found in HN about | founders only |
| strong_launch_author | authored a wave-2-verified company launch (author == gh_login) | founders only |
| llm_confirmed | `anthropic/claude-sonnet-4.5` (temp 0, cached) adjudication of ambiguous about text vs GitHub-side facts | both classes |
| medium_rare_name | exact match of a rare username (≥10 chars, or ≥8 with digit/separator) | both classes |

Because founders get extra tiers from `founders.parquet`, every founders-vs-controls
comparison is also reported on the **class-symmetric tiers only** (github link, story
URL, GH-profile blog/name, rare name) — the fair comparison.

**Leakage discipline (iron rule 1).** The identity *link* rests on current-day data
(HN about, GH profile) → `hn_persons.parquet` rows carry
`data_basis=current_day_label_only`. The *stories* are dated events:
pre-t_cutoff Show HNs are potential FEATURE events (event-time public acts);
post-cutoff Show/Launch HNs are OUTCOME/LABEL material only. Every story row in
`hn_person_stories.parquet` carries `pre_or_post_cutoff`. One honest caveat: a
production feature using pre-cutoff Show HNs would need *event-time* identity
resolution; here the link itself is confirmed with current-day pages (see Caveats).

<!-- RESULTS FILLED AFTER RUN -->

*Artifacts: `data/labels/hn_persons.parquet`, `data/labels/hn_person_stories.parquet`.
Eval: `uv run python -m vc_brain.labelnoise.hn_person_eval`. 2026-07-19.*
