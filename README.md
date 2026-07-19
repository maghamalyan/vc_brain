# VC Brain

VC Brain is a sourcing-first MVP for finding potential founders before conventional venture signals exist. It covers the brief's sourcing-to-decision path, but concentrates the build where the brief says the cold-start problem matters most: the public activity of a person who has no fundable company, financing history, or recognized founder track record yet.

The thesis is: **watch PUBLIC BEHAVIOR BEFORE ANY TRACK RECORD EXISTS**. The Memory layer starts with person-level GitHub event streams from GH Archive through the public ClickHouse playground. A 10,854-row Y Combinator founder dataset supplies retrospective labels; the full overnight run resolved 2,052 GitHub handles at the precision threshold, spanning batches from 2012 through 2027. A discrete-time hazard model then asks, month by month, whether the observed behavior precedes an estimated six-month founding-gestation window.

The resulting [“we found them first” backtest](site/backtest.html) is our direct attempt at the brief's Area of Research 3: test how much public footprints predict later founder recognition. It uses an out-of-time split—development cohorts through 2023, test batches from 2024 onward—and reports when a held-out founder first crosses the same-month 99th percentile of control scores. This is a retrospective experiment, not evidence of prospective deployment performance.

## Architecture: Memory, Intelligence, Experience

| Brief layer | What is implemented in this repository |
| --- | --- |
| **Memory** | A resumable [YC label pipeline](src/vc_brain/labels/) builds founder/company identities and high-precision GitHub linkages. A bounded, cached [ClickHouse extractor](src/vc_brain/ingest/) creates person-month activity, received-traction, repository-creation, and matched-control data from GH Archive. SQL and post-load assertions enforce `event time < cutoff`; company-linked repositories are excluded. [Deck intake](src/vc_brain/memo/intake.py) converts each PDF page into attributable inbound evidence. The GitHub identity and event history stay keyed to the person; an application remains a separate opportunity. |
| **Intelligence** | A [discrete-time hazard pipeline](src/vc_brain/models/) builds leakage-bounded panels, compares logistic regression with LightGBM on temporal validation, and produces an [honest held-out evaluation](data/eval/report.md). The opportunity screen keeps Founder, Market, and Idea-vs-Market as three independent axes with trends; it never averages them. [OpenRouter memo generation](src/vc_brain/memo/generate.py) produces only the five required sections, explicit gaps, contradictions, and a Trust record per claim. Pydantic rejects schema drift, missing claim links, and empty evidence lists; a second mechanical check rejects any citation that was not in the supplied evidence set. That check proves citation provenance, not the semantic truth of the claim. |
| **Experience** | The [static investor dashboard](site/index.html) presents a thesis-filtered candidate queue, momentum, three-axis screening, evidence timelines, required memo sections, per-claim Trust status, contradictions, and known gaps. The [backtest page](site/backtest.html) separates rising signals from left-boundary-censored detections. Both pages build offline from deterministic fixtures or validated real pipeline outputs. |

Inbound and outbound use different evidence entry points, then converge into the same screening funnel:

```text
Outbound: public-event detector ─┐
                                ├─> thesis filter ─> 3 independent axes ─> evidence-backed memo ─> investor review
Inbound: company name + deck ───┘
```

The outbound detector supplies a persistent founder signal and event evidence. The inbound path supplies deck claims, marked `single_source` until corroborated. From that point onward, both paths use the same thesis, claim contract, gap handling, screening axes, and investor queue. The current inbound implementation is a PDF pipeline and fixture-backed dashboard path, not a hosted upload service.

## Honest results

These are the final full-cohort outputs from [report.md](data/eval/report.md) and [report.json](data/eval/report.json). Development panels contain ~315k person-months (tuning through 2022, validation on 2023); the held-out pool contains 2,765 people, including 690 labeled founders with 2024+ batches; its ~25% case-control prevalence is not a deployment base rate.

| Measurement | Final result | Interpretation |
| --- | ---: | --- |
| Selected LightGBM within-month PR-AUC | **0.2418** | 2.5x the within-month base of 0.0951, and well above the shuffled-label null of 0.1327 (limit 0.1901). The earlier partial-cohort margin was thin; the full training set separated it. |
| Logistic within-month PR-AUC | **0.1819** | LightGBM's validation-time selection (no test access) is confirmed on test with the full cohort. |
| LightGBM global PR-AUC / ROC-AUC | **0.1581 / 0.782** | Global person-month PR-AUC is secondary because it mixes calendar composition. |
| Precision@50 | **0.50 (25/50)** | 2.0x the sampled person-level prevalence of 0.25; ranking utility within the case-control pool, not calibrated deployment precision. |
| Detection rate | **72.3% (499/690)** | A detection means crossing the same-month 99th control-score percentile. Undetected founders remain in the denominator. |
| Boundary-censored detections | **75% (375/499)** | Already above threshold in the first observed month: persistent propensity with true lead of at least 48 months, not a new rise. |
| Rising-signal detections | **124 founders; median 15 months** | For signals first crossing the threshold inside the window, median lead to the YC batch was 15 months, IQR 14–17. |
| Tenure ablation | **global PR-AUC 0.1581 → 0.0628 without `tenure_months`** | Account tenure carries 74.5% of model gain. The detector is substantially "maturity + consistency + received attention"; activity dynamics contribute, but tenure is the workhorse and we say so. |

### Why the null is within-month

The mandatory null run shuffles development labels within each calendar month with seed 18, retrains the model, and leaves held-out test labels unchanged as the oracle. On the final cohort its within-month PR-AUC is 0.1327 against a configured maximum of 0.1901 and a within-month base of 0.0951, so the gate passes with real margin. The null still sits above base — panel structure retains residual person-level correlates (notably tenure) that shuffling cannot fully remove — which is why the tenure ablation is reported alongside.

An earlier global null gate fired: even shuffled labels produced global PR-AUC 0.098 because the panel's founder/control composition changes across calendar months. A model could exploit that calendar composition without learning person-level separation. We replaced the gate and primary metric with macro within-month PR-AUC, which ranks founders against controls in the same month, and retained global PR-AUC in the report for transparency. Catching and removing this artifact is part of the product's trust story: the system reports a weaker defensible result instead of preserving a stronger invalid one.

The calibration section applies prior-odds case-control correction under an assumed 1% population person-month base rate, with 0.5% and 2% sensitivity runs. Trajectories and candidate ordering use raw model scores, not those corrected probabilities.

## Verification culture

- Two independent 25-row human audits checked confident YC-to-GitHub linkages against live YC and GitHub pages. The first found 23/25 strict person profiles plus two company-named accounts belonging to the correct founders; the second found 25/25. Combined result: **at least 48/50 strict matches and zero wrong-person links**.

- Leakage controls exist in SQL, data assembly, and tests. Events must precede each person's cutoff; controls cannot contain any labeled founder login; duplicate identities inherit the earliest cutoff; and actors whose company domain appears in a pre-cutoff repository name are dropped. The current extraction records 42 such company-domain drops. See the [event data card](data/events/data_card.md) and [model contract](specs/p4_model.md).

- The shuffled-label check is a release gate, not a diagnostic footnote. Evaluation always writes its report, but if the null exceeds the limit it raises `LeakageSanityError` and publishes no new `trajectories.parquet` or `candidates.parquet`. Existing exports from an earlier run must not be treated as outputs of the failed run.

- The current repository test run passes 67 tests. Fixture tests cover hand-computed feature windows, temporal split boundaries, memo contracts, citation membership, deterministic screening, and both censored and rising-signal backtest rendering.

## Reproduce

The deterministic fixture dashboard needs no external credentials. The live pipeline needs Python 3.13, [`uv`](https://docs.astral.sh/uv/), GitHub CLI authentication for handle resolution, and network access to YC, GitHub, and the public ClickHouse playground. `SERPAPI_KEY` is optional for resolution fallback; `OPENROUTER_KEY` is needed only to generate new live memos. Put optional keys in the ignored `.env` file.

### Build and verify the environment

```bash
docker build -t vc-brain .
# Equivalent repository target:
make build

uv sync --frozen
make test
make lint
```

The available Make targets are `build`, `shell`, `test`, and `lint`; there is no implicit `pipeline` target. `make shell` starts the mounted project image and reads `.env`, but live GitHub resolution expects an authenticated `gh` CLI on the host. Run the full live stages from the host environment created by `uv sync`.

### Build the offline fixture demo

```bash
uv run python -m vc_brain.dashboard.run --fixtures
```

Open `site/index.html`; the backtest is `site/backtest.html`.

### Run the live stages in order

Each data stage is cached, checkpointed, and safe to resume.

```bash
# 1. YC companies and founders, GitHub resolution, final labels
gh auth login
uv run python -m vc_brain.labels.run --stage companies
uv run python -m vc_brain.labels.run --stage founders
uv run python -m vc_brain.labels.run --stage resolve
uv run python -m vc_brain.labels.run --stage build

# 2. GH Archive baselines, positive histories, matched controls, repo evidence
uv run python -m vc_brain.ingest.run --stage baselines
uv run python -m vc_brain.ingest.run --stage positives
uv run python -m vc_brain.ingest.run --stage negatives
uv run python -m vc_brain.ingest.run --stage repos

# 3. Leakage-bounded features, temporal training, null-gated evaluation
uv run python -m vc_brain.models.run --stage all

# 4. Validate and render the real offline dashboard and backtest
uv run python -m vc_brain.dashboard.run --real
```

For a small positive-extraction smoke run, use `--actor-limit 20` with the `positives` stage. The [label](data/labels/data_card.md), [event](data/events/data_card.md), [feature](data/features/data_card.md), and [evaluation](data/eval/report.md) data cards record coverage and assumptions after a run.

## Limitations and future work

- **GitHub-only behavioral signal.** Private and deleted activity is absent, GH Archive begins in 2011, and public GitHub behavior represents only part of a founder's work. LinkedIn and X behavior are deliberately excluded because compliant access was not available under their terms of service.

- **YC-only positive labels.** YC selection and this project's GitHub resolution process both create selection bias. The estimated gestation date is the batch start minus nine months, not a verified company founding date. Future labels should use SEC Form D as a financing confirmation source and include non-YC founders and explicit hard negatives.

- **Case-control calibration assumptions.** The current matched pool realizes about 3.0 controls per extracted positive. Corrected probabilities depend on an assumed population person-month base rate; the report shows 0.5%, 1%, and 2% rather than claiming one known rate.

- **Partial-data score quantization.** The current LightGBM sees a sparse, partially resolved cohort and produces repeated leaf scores in several trajectories. Treat the score as a ranking signal, not a precise probability. The final full-cohort run will update the generated metrics, but more data does not remove the need for prospective validation.

- **Next data layer.** A Neo4j graph could join people, repositories, organizations, deck claims, SEC confirmations, and Hacker News identities while preserving source and timestamp on every edge. HN is the next cross-source behavioral stream because it can be tested without importing LinkedIn or X data.

### Research appendix: temporal graph models

After the multi-signal graph and larger cohorts exist, compare the Tier-1 hazard model with temporal graph methods rather than replacing a measurable baseline prematurely. Primary references are Rossi et al., [*Temporal Graph Networks for Deep Learning on Dynamic Graphs*](https://arxiv.org/abs/2006.10637), and Xu et al., [*Inductive Representation Learning on Temporal Graphs*](https://arxiv.org/abs/2002.07962). Any temporal-GNN result should keep the same out-of-time split, within-month null, leakage assertions, and export gate.
