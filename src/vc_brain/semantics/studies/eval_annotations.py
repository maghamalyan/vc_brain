"""Evaluate the Pillar-1 mini experiment: do semantic annotations separate
founders from controls in the top region where counts saturate?"""

from __future__ import annotations

import polars as pl

from vc_brain.semantics.person_annotate import ANNOTATIONS_PATH
from vc_brain.semantics.studies.content_features import auc
from vc_brain.semantics.person_extract import PILOT_COHORT_PATH


def main() -> None:
    cohort = pl.read_parquet(PILOT_COHORT_PATH).filter(
        pl.col("stratum") == "top_region"
    )
    ann = pl.read_parquet(ANNOTATIONS_PATH).with_columns(
        pl.col("gestation_likelihood").cast(pl.Float64),
        pl.col("productization").cast(pl.Float64, strict=False),
    )
    frame = cohort.join(ann, on="gh_login", how="left")
    with_text = frame.drop_nulls("gestation_likelihood")
    print(
        f"top region: {frame.height} actors, annotated {with_text.height} "
        f"(no-text actors get gestation=0 by the interactivity rule)"
    )

    print("\n=== AUC in top region (annotated subset) ===")
    for f in ("gestation_likelihood", "productization"):
        print(f"{f:22s} {auc(with_text, f):.3f}   (peak-score baseline: {auc(with_text, 'peak'):.3f})")

    print("\n=== builder_type composition by class ===")
    print(
        with_text.group_by("person_type", "builder_type")
        .len()
        .sort("person_type", "len", descending=[False, True])
    )

    print("\n=== gestation_likelihood distribution ===")
    print(
        with_text.group_by("person_type").agg(
            pl.col("gestation_likelihood").median().alias("median"),
            pl.col("gestation_likelihood").quantile(0.25).alias("p25"),
            pl.col("gestation_likelihood").quantile(0.75).alias("p75"),
            pl.len(),
        )
    )

    # Re-ranking: no-text actors scored 0 (the interactivity rule), then rank
    # by gestation_likelihood with peak as tiebreak; compare precision@k.
    ranked_counts = frame.sort("peak", descending=True, nulls_last=True)
    ranked_sem = frame.with_columns(
        pl.col("gestation_likelihood").fill_null(0.0)
    ).sort(
        ["gestation_likelihood", "peak"], descending=[True, True], nulls_last=True
    )
    print("\n=== precision@k, counts-only vs semantic re-rank ===")
    for k in (10, 25, 50, 100):
        p_counts = (ranked_counts.head(k)["person_type"] == "positive").mean()
        p_sem = (ranked_sem.head(k)["person_type"] == "positive").mean()
        print(f"@{k:<4d} counts={p_counts:.3f}  semantic={p_sem:.3f}")

    portrait = with_text.select(
        "gh_login", "person_type", "builder_type", "gestation_likelihood"
    )
    print("\n=== portrait cross-check ===")
    import re
    from pathlib import Path

    doc = Path("docs/exploration/false_positive_portrait.md").read_text()
    rows = re.findall(
        r"^\|\s*\d+\s*\|\s*(\S+)\s*\|[^|]+\|[^|]+\|\s*\**([A-Z]+)\**\s*\|",
        doc,
        re.MULTILINE,
    )
    pmap = pl.DataFrame(
        {"gh_login": [r[0] for r in rows], "portrait_class": [r[1] for r in rows]}
    )
    joined = pmap.join(portrait, on="gh_login", how="inner")
    print(
        joined.group_by("portrait_class").agg(
            pl.len(), pl.col("gestation_likelihood").mean().round(1)
        )
    )
    print(joined.sort("gestation_likelihood", descending=True))


if __name__ == "__main__":
    main()
