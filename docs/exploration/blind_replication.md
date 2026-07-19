# Name-Blinded Replication: Is the Annotation Result Contaminated? (2026-07-19)

**Question.** The deep-slice pilot's annotator (`anthropic/claude-sonnet-4.5`) sees
logins and repo-owner names, so world-knowledge recognition of later-famous people
could inflate the semantic-annotation results. Quantify that by re-annotating the
same 335 top-region actors with all identity tokens masked.

**Method.** `src/vc_brain/pilot/blind_check.py` rebuilds each actor's digest from
`data/pilot/text_events.parquet` (same `build_digest` logic) and masks it: the
actor's login → `USER` everywhere (owner segments, org names, URLs, comment bodies,
plus a substring pass that catches gluings like `remysharp.com` for login `remy`);
`member_login`s → `PERSON1…`; other repo-owner segments → per-actor-stable `EXT1…`
in owner position and @mentions only, so words that are both an org and a technology
("flutter") stay readable in repo stems and bodies. Repo stems, titles, bodies, and
dates are untouched. Residual-leak audit over all 335 masked digests: **0** digests
contain the actor's login. Same prompt, model, temperature 0; separate cache
(`data/cache/pilot_annotations_blind/`, 335 calls ≈ $4). Comparison:
`src/vc_brain/pilot/eval_blind.py`; blind annotations in
`data/pilot/annotations_blind.parquet`, masked digests in
`data/pilot/blind_digests.parquet`.

## Headline: aggregate results survive blinding; the head of the list keeps most of its lift

On the common 335-actor set (149 founders / 186 controls), founder-vs-control AUC:

| signal | unblinded | blind |
|---|---|---|
| gestation_likelihood | 0.558 | 0.548 |
| productization | 0.530 | 0.526 |
| peak (count model, baseline) | 0.575 | — |

Precision@k re-ranking the 414-actor top region (no-text actors → 0, peak tiebreak):

| k | counts | unblinded semantic | blind semantic |
|---|---|---|---|
| 10 | 0.400 | 0.700 | **0.600** |
| 25 | 0.520 | 0.520 | 0.440 |
| 50 | 0.480 | 0.520 | 0.480 |
| 100 | 0.430 | 0.530 | **0.480** |

The pilot's headline (@10: 0.40 → 0.70) keeps two-thirds of its lift blind
(0.40 → 0.60); @100 keeps half (+10pp → +5pp); @25 dips below counts. Spearman
correlation between unblinded and blind gestation is 0.788. Per-person deltas
(unblinded − blind): mean +0.45, median 0, std 18.5; 86.6% of people move ≤10
points; 5.4% drop ≥30 and a symmetric 5.7% rise ≥30. The class asymmetry is small:
founders drop on average 1.65 points, controls rise 0.51 — i.e. blinding removes
only ~2 points of founder-favoring gestation net.

## The big per-person swings are mostly a masking artifact, not fame

All 20 largest drops were `own_product_building` unblinded; 19/20 flip to
employment/OSS/hobby blind. The mechanism is visible in the data: **14/20 of the
top droppers create repos under an org owner** (their own startup org — e.g.
`postgresml/…`, `banana-dev/…`), against a 120/335 (36%) baseline. Masking turns
the actor's *own* org into `EXTn`, so building one's company reads as working in
someone else's repo. Actors with org-creates shift +5.31 mean delta (10% drop ≥30)
vs −2.26 (2.8% drop ≥30) for actors without. The 10 largest *rises* are the mirror
image: employer/university orgs become `EXTn` too, and coherent work inside them
now reads as own-product (e.g. okwasniewski 15 → 85).

A genuine fame component exists but is secondary and concentrated. Current-day
profile check of the 20 droppers (label/identity screening only, 2026-07-19,
cached in `data/cache/blind_fame_check/`): median 130 followers, 4/20 with ≥900
(taranjeet/Mem0 915, mufeedvh/YC-S24 1,232, teichman 1,909, qwqdanchun 973), plus
recognizable founders levkk (PostgresML/PgDog), erik-dunteman (Banana → Butter),
michaelfester (14.ai), egil (bUnit, Microsoft MVP). The 10 risers median 40
followers, 1/10 ≥500. So the unblinded annotator does recognize a handful of
famous builders and scores them up — but for these same people it also loses
legitimate event-time ownership evidence when blinded, so their 50–80-point drops
are an upper bound on the fame effect.

## Portrait cross-check (hand-labeled ground truth) survives

On the 19 portrait people annotated in both variants:

| class | n | mean gestation unblinded | mean gestation blind |
|---|---|---|---|
| FP | 13 | 15.0 | 18.1 |
| INT | 4 | 82.5 | 85.0 |
| NOISE (mislabeled founder) | 1 | 95 | 95 |

FP ≤ 15 holds for 11/13 unblinded and 9/13 blind (worst blind FP: 65,
seyyedalimirhoseini's Laravel course projects reading as product once the login is
hidden); INT/NOISE ≥ 75 holds 5/5 in both variants, and blind separation remains
clean — every INT/NOISE ≥ 85, every FP ≤ 65. builder_type exact agreement between
variants is 74.3% (335 actors); the top confusions (employment↔OSS 12,
own-product↔OSS 8, hobby→own-product 7) are the org-ambiguity cases above.
(Note: the pilot doc reported 13/13 FP ≤ 15; `annotations.parquet` was rebuilt
today and two FPs now sit at 25 unblinded — instrument drift of one 10-point bin,
same qualitative picture.)

## Verdict

**The unblinded result is a mild upper bound, not a contaminated one.** Aggregate
metrics move a little under strict blinding (AUC −0.010; @10 keeps +20pp of the
+30pp lift; @100 keeps +5pp of +10pp) and the hand-label cross-check survives.
The blind numbers are themselves a *lower* bound, because login/org masking
destroys legitimate event-time ownership evidence (own startup org → `EXTn`),
which is what drives most of the large per-person swings in both directions;
the true fame-contamination effect is the small net class asymmetry (~2 gestation
points) plus a handful of genuinely recognizable people at the very head of the
list, exactly where precision@10 is measured.

**Recommendation for future runs:** use a structure-preserving blind variant —
mask the actor (`USER`), people (`PERSONn`), and external owners (`EXTn`) as here,
but label orgs where the actor has event-time admin evidence (created repos via
CreateEvent, added members via MemberEvent) as `USER_ORG1…` instead of `EXTn`.
That keeps identity hidden while preserving the ownership structure the annotator
legitimately needs; report it as the primary number, with the unblinded run as an
upper-bound sensitivity. Until that variant exists, report both columns of the
precision table above side by side, and treat @10 claims quoted from the unblinded
run as optimistic by roughly one hit in ten.

*All numbers from `uv run python -m vc_brain.pilot.eval_blind` on
`data/pilot/annotations.parquet` (2026-07-19 rebuild) vs
`data/pilot/annotations_blind.parquet`. Blind run: 335/335 annotated, 0 masked-digest
leaks, temperature 0, per-item cache.*
