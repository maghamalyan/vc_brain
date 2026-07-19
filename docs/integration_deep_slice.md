# Integration Record: Deep-Slice → overnight/poc (2026-07-19)

**Decision (user, 2026-07-19):** the person-level semantic instrument from the
deep-slice worktree is the semantic layer for the submission. **Stream A3a's
person-quarter trajectory annotation is HELD** — its pipeline code stays in the
tree (`semantics/{extract,annotate,schema,run,...}.py`), unrun, spend-gated
(~36.6M tokens). Revisit post-submission; before any run, retrofit the
deep-slice lessons (anchored 0–100 scores, structure-preserving identity
masking, empty-digest guard — see `docs/exploration/instrument_v2.md` and
`docs/exploration/blind_replication.md`).

## What moved where (consolidation)

| was (worktree) | now | role |
|---|---|---|
| `pilot/extract.py` | `semantics/person_extract.py` | person-level pre-cutoff text extraction (playground, FORMAT Parquet) |
| `pilot/annotate.py` | `semantics/person_annotate.py` | v1 instrument (kept for provenance/evals) |
| `pilot/annotate_v2.py` | `semantics/person_annotate_v2.py` | **production instrument** (anchored 0–100, masked) |
| `pilot/blind_check.py` | `semantics/person_masking.py` | identity masking + leak audit |
| `pilot/hygiene.py` | `semantics/hygiene.py` | negative-pool cleaner + corrected metrics |
| `pilot/eval_full.py` | `semantics/person_eval.py` | full-cohort evaluation |
| `pilot/{studies}` | `semantics/studies/*` | exploration provenance (content features, blind, commits, privatization, evals) |
| `labelnoise/*` | `labels/{probe_net,control_screen,control_screen_mid,hn_harvest,hn_persons,hn_person_eval}.py` | label streams + screening |

Data paths are UNCHANGED (`data/pilot/`, `data/labels/hn_*.parquet`,
`data/cache/{pilot*,labelnoise,gh_commits}`) so all content-addressed caches
(~$35 of annotations) remain valid. Data artifacts migrated additively from the
worktree; nothing in the main checkout's `data/` was overwritten.

## Headline numbers (see `docs/exploration/corrected_metrics.md` for which to quote)

- Matched-pairs AUC: gestation 0.776 vs counts 0.640 (hygiene-corrected).
- Semantic re-rank: corrected p@10 = 10/10, p@25 = 0.76 (head-of-list only; v2
  fixes the K≥50 inversion). Conservative blind+corrected top-region: p@10 0.70.
- Label noise: monotone in gestation (5.1% / 7.3% / 25.8%); 13 confirmed
  unlabeled founders excluded via `semantics/hygiene.py` (canonical).
- Observability boundary: 24.8% of top-region founders (11.0% of all 690) show
  public product gestation pre-batch.
- HN person stream: founder same-handle HN existence 45.2% vs 5.8% (OR 13.3);
  pre-cutoff Show HN ⇒ P(founder) 77–82% vs 25% base; post-cutoff launches
  10.0% vs 0.2% (outcome labels).
- Killed: regex content features, commit-message scoring signal, 404-as-triage,
  global semantic ranking. Privatized-while-alive adopted as ontology stage
  (cohort replication pending).

## Follow-ups owed

1. Fold `excluded_controls.parquet` into stream A's eval (their 34.2%
   matched-group headline is polluted by the same label noise) — at their next
   gate, not mid-flight.
2. Dashboard/memo wiring of the two-stage ranking (counts → interactivity →
   v2 re-rank with `rank_evidence`) — coordinate with protected-paths owner.
3. v2 on full cohort; correction-symmetric screening of counts-ranking misses;
   privatization cohort-scale replication.
