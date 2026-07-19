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

## Results (full 2,765-actor run, 2026-07-19)

### 1. Identity linkage — massively founder-enriched at every tier

| tier | founders | controls | Fisher OR | p |
|---|---|---|---|---|
| HN account exists (same login) | 312/690 = **45.2%** (CI 41.5–49.0) | 121/2,075 = 5.8% (CI 4.9–6.9) | 13.3 | 2e-116 |
| confirmed STRICT | 96/690 = 13.9% | 14/2,075 = 0.7% | 23.8 | 4e-45 |
| confirmed incl. rare-name | 216/690 = 31.3% | 53/2,075 = 2.6% | 17.4 | 1e-91 |
| confirmed, **class-symmetric tiers** (fair comparison) | 157/690 = **22.8%** | 49/2,075 = 2.4% | 12.2 | 9e-59 |

The linkage study's 44.7% founder existence-rate prior replicates almost exactly
(45.2%). Even bare same-login account existence is a 13× founder signal.

### 2. Pre-cutoff Show HN — rare but extremely high-precision cold-start flag

Unconditional (all scored actors): founders 23/690 = **3.3%** vs controls
7/2,075 = 0.3% (OR 10.2, p = 3e-9); incl. rare-name tier 4.6% vs 0.3% (OR 14.4).
**P(founder | authored a pre-cutoff Show HN) = 76.7–82.1% vs 25.0% base rate.**
Conditioned on *having* a confirmed-linked account the class contrast vanishes
(strict: 24.0% F vs 50.0% C on n=14 controls, p=0.06 inverted) — the deployable
signal is the joint event "same-handle HN identity exists AND launched
pre-cutoff", which is precisely what a sourcer can check in seconds. Coverage is
low (3–5%) but precision is 3× base — a classic high-precision/low-recall
cold-start flag, complementary to the semantic instrument.

### 3. Post-cutoff launches — clean outcome labels, and two label-noise catches

Founders: 69/690 = **10.0%** have a post-cutoff Show/Launch HN (median +14.3
months after cutoff — consistent with the company-level harvest's +14.4);
controls: 4/2,075 = 0.2%. Of the 54 control post-cutoff stories, 40+ belong to
one serial launcher (vednig, gestation 72 — the meet-worthy species personified)
and two are crohr's RunsOn launches (already a wave-2-confirmed unlabeled
founder). Of the 92 high-gestation controls, 6 have confirmed HN accounts and 2
have post-cutoff launches — both already caught by the wave-2 screen (consistency
check passed).

**Verdict.** Adopt as (a) a new outcome-label stream (person-level launches),
(b) a high-precision sourcing flag (same-handle HN + pre-cutoff Show HN),
(c) an identity-spine edge for Pillar 4. The case-sensitivity floor and
current-day-link caveats stand; event-time identity resolution is the
productionization gap.

*Artifacts: `data/labels/hn_persons.parquet`, `data/labels/hn_person_stories.parquet`.
Eval: `uv run python -m vc_brain.labelnoise.hn_person_eval`. 2026-07-19.*
