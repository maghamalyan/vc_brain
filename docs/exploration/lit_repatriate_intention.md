# Literature note — repatriate entrepreneurship intention (Timsina et al., 2026)

Source: [research/Timsina-2026-Repatriate-Entrepreneurship-Intention.pdf](../../research/Timsina-2026-Repatriate-Entrepreneurship-Intention.pdf)
— *Determinants of Entrepreneurship Intention among Nepalese Repatriates*, American
Journal of STEM Education 26 (2026), pp. 207–239. Survey, n=498, Theory of Planned
Behavior + Shapero's Entrepreneurial Event Model.

## Evidence class — read this first

Cross-sectional self-report survey measuring *intention*, not venture creation, in a
population (returned labor migrants, 35% construction / 28% hospitality) far from
software founders. **Nothing here may be used as a quantitative prior, a calibration
input, or a feature weight.** It is convergent qualitative support for our feature
taxonomy and narrative framing, and that is all we cite it as.

## What it found

Multiple regression on entrepreneurial intention (R² = 0.47, all p < 0.01):

| Predictor (their "capital") | β | Rank |
| --- | ---: | --- |
| Entrepreneurial knowledge & exposure (cognitive) | 0.34 | 1 |
| Professional skills (human) | 0.29 | 2 |
| Environmental exposure — ecosystems, networks, role models (contextual) | 0.21 | 3 |
| Personal savings (financial) | 0.18 | 4 |

Qualitative themes (286 open-ended responses): opportunity recognition, motivational
drivers, skill transfer, resource readiness, and perceived barriers (capital access,
bureaucracy) that block intention→action conversion. The authors characterize
returnee intention as opportunity-driven and skill-based, not necessity-driven.

## Mapping onto this repository

1. **Supports the thesis ordering.** Accumulated exposure and demonstrated skill
   outrank financial capital as intention predictors — the same bet as "watch public
   behavior before any track record exists." It also reframes the tenure ablation
   (74.5% of model gain from `tenure_months`): tenure is a proxy for accumulated
   exposure/human capital, the strongest determinant class in the intention
   literature. Consistency with prior work, not just account age.
2. **The "repatriation moment" is a context-shift detector.** The paper's real
   subject is people who acquire skills in one environment and redeploy them in a
   new one; founding propensity concentrates at that redeployment moment. GitHub
   analog: divergence between recent and historical activity composition — new
   language/domain mix, employer-org activity stopping, contribution→creation shift.
   This is already the "composition shifts" idea in the semantic-trajectory pillar
   (research_program.md, Pillar 1) and rides on A2's `own_repo_share` delta and A3's
   quarterly annotation deltas. See the A3 addendum in
   [specs/a_exploitation.md](../../specs/a_exploitation.md).
3. **Environmental exposure validates the A2 collaboration family.** Their
   third-ranked predictor is ecosystem/network embeddedness — what `collab_influx`
   and received-traction measure. Their emphasis on *diversity* of exposure suggests
   a cheap future extension: entropy over distinct orgs/ecosystems touched, not just
   attention volume.
4. **A third false-positive category: blocked conversion.** The
   [false-positive portrait](false_positive_portrait.md) established tutorial-burst
   FPs (~76%) and label-censoring FPs (non-YC founders). This paper's barrier themes
   suggest a third: genuine founding intention and capability that never converts
   for resource/network reasons. For a sourcing product this is arguably the most
   valuable "FP" class — the barriers respondents name (capital, networks,
   mentorship) are exactly what a VC removes. Worth one sentence in backtest/memo
   framing; not a measurable claim from our data.
5. **Four-capital framing for the Founder axis.** Cognitive / human / contextual /
   financial is a clean, literature-grounded way to organize Founder-axis evidence
   in memos and the founder record: what they know, what they can build, who is
   paying attention to them, and (usually unobservable for us) resources. Costs
   nothing to adopt as narrative structure.

## Explicitly not adopted

- The β magnitudes, R², or any survey-derived number as model input.
- Any claim about *our* population's intention→action conversion rate.
- TPB/EEM as a formal model — we use it as vocabulary only. (KruegerCarsrudERD.pdf
  in research/ is the underlying TPB-entrepreneurship reference if deeper grounding
  is ever needed.)
