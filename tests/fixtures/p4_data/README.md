# Synthetic P4 contract fixtures

Every parquet file below this directory is generated data. The corpus covers 2022
tuning-train groups, 2023 validation groups, and 2024 held-out groups; five controls
are matched to each positive. It deliberately includes `excluded_low_confidence`,
which must not enter the panel, and `test_p4_zero`, which has no GitHub activity.

Regenerate from the repository root with:

```bash
uv run python tests/fixtures/generate_p4_fixtures.py
```
