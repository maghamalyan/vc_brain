"""Compare name-blinded vs unblinded pilot annotations (contamination check).

Reports, on the common annotated set:
  - gestation AUC (positives vs controls) blind vs unblinded;
  - precision@k of the semantic re-rank blind vs unblinded vs counts-only;
  - per-person gestation deltas (distribution + 20 largest drops for manual
    fame inspection);
  - portrait cross-check (hand-labeled people) under blinding;
  - builder_type agreement rate and confusion summary.
"""

from __future__ import annotations

import re
from pathlib import Path

import polars as pl

from vc_brain.semantics.person_annotate import ANNOTATIONS_PATH
from vc_brain.semantics.person_masking import BLIND_ANNOTATIONS_PATH
from vc_brain.semantics.studies.content_features import auc
from vc_brain.semantics.person_extract import PILOT_COHORT_PATH


def load_joined() -> pl.DataFrame:
    cohort = pl.read_parquet(PILOT_COHORT_PATH).filter(
        pl.col("stratum") == "top_region"
    )
    unblinded = pl.read_parquet(ANNOTATIONS_PATH).select(
        "gh_login",
        pl.col("gestation_likelihood").cast(pl.Float64).alias("gest_open"),
        pl.col("productization").cast(pl.Float64, strict=False).alias("prod_open"),
        pl.col("builder_type").alias("type_open"),
    )
    blind = pl.read_parquet(BLIND_ANNOTATIONS_PATH).select(
        "gh_login",
        pl.col("gestation_likelihood").cast(pl.Float64).alias("gest_blind"),
        pl.col("productization").cast(pl.Float64, strict=False).alias("prod_blind"),
        pl.col("builder_type").alias("type_blind"),
    )
    return cohort.join(unblinded, on="gh_login", how="left").join(
        blind, on="gh_login", how="left"
    )


def portrait_classes() -> pl.DataFrame:
    doc = Path("docs/exploration/false_positive_portrait.md").read_text()
    rows = re.findall(
        r"^\|\s*\d+\s*\|\s*(\S+)\s*\|[^|]+\|[^|]+\|\s*\**([A-Z]+)\**\s*\|",
        doc,
        re.MULTILINE,
    )
    return pl.DataFrame(
        {"gh_login": [r[0] for r in rows], "portrait_class": [r[1] for r in rows]}
    )


def main() -> None:
    frame = load_joined()
    both = frame.drop_nulls(["gest_open", "gest_blind"])
    print(
        f"top region {frame.height}; annotated both variants: {both.height} "
        f"(open {frame.drop_nulls('gest_open').height}, "
        f"blind {frame.drop_nulls('gest_blind').height})"
    )

    print("\n=== AUC on the common annotated set (positives vs controls) ===")
    for col in ("gest_open", "gest_blind", "prod_open", "prod_blind", "peak"):
        print(f"{col:12s} {auc(both, col):.3f}")

    print("\n=== precision@k re-rank (no-text actors -> 0, peak tiebreak) ===")
    ranked = {
        "counts": frame.sort("peak", descending=True, nulls_last=True),
        "open": frame.with_columns(pl.col("gest_open").fill_null(0.0)).sort(
            ["gest_open", "peak"], descending=[True, True], nulls_last=True
        ),
        "blind": frame.with_columns(pl.col("gest_blind").fill_null(0.0)).sort(
            ["gest_blind", "peak"], descending=[True, True], nulls_last=True
        ),
    }
    for k in (10, 25, 50, 100):
        row = "  ".join(
            f"{name}={ (r.head(k)['person_type'] == 'positive').mean():.3f}"
            for name, r in ranked.items()
        )
        print(f"@{k:<4d} {row}")

    print("\n=== gestation delta (open - blind) distribution ===")
    deltas = both.with_columns((pl.col("gest_open") - pl.col("gest_blind")).alias("delta"))
    print(
        deltas.select(
            pl.col("delta").mean().round(2).alias("mean"),
            pl.col("delta").median().alias("median"),
            pl.col("delta").std().round(2).alias("std"),
            (pl.col("delta").abs() <= 10).mean().round(3).alias("share_|d|<=10"),
            (pl.col("delta") >= 30).mean().round(3).alias("share_d>=+30"),
            (pl.col("delta") <= -30).mean().round(3).alias("share_d<=-30"),
        )
    )
    print(deltas.group_by("person_type").agg(
        pl.col("delta").mean().round(2), pl.len()
    ))

    print("\n=== 20 largest drops under blinding (open >> blind) ===")
    print(
        deltas.sort("delta", descending=True)
        .head(20)
        .select(
            "gh_login", "person_type", "gest_open", "gest_blind",
            "type_open", "type_blind",
        )
    )
    print("\n=== 10 largest rises under blinding (blind >> open) ===")
    print(
        deltas.sort("delta")
        .head(10)
        .select(
            "gh_login", "person_type", "gest_open", "gest_blind",
            "type_open", "type_blind",
        )
    )

    print("\n=== builder_type agreement ===")
    agree = (both["type_open"] == both["type_blind"]).mean()
    print(f"exact agreement: {agree:.3f} (n={both.height})")
    confusion = (
        both.filter(pl.col("type_open") != pl.col("type_blind"))
        .group_by("type_open", "type_blind")
        .len()
        .sort("len", descending=True)
    )
    print(confusion.head(15))

    print("\n=== portrait cross-check under blinding ===")
    joined = portrait_classes().join(both, on="gh_login", how="inner")
    print(
        joined.group_by("portrait_class").agg(
            pl.len(),
            pl.col("gest_open").mean().round(1),
            pl.col("gest_blind").mean().round(1),
        )
    )
    print(
        joined.select(
            "gh_login", "portrait_class", "gest_open", "gest_blind",
            "type_open", "type_blind",
        ).sort("portrait_class", "gest_blind")
    )
    fp = joined.filter(pl.col("portrait_class") == "FP")
    intr = joined.filter(pl.col("portrait_class").is_in(["INT", "NOISE"]))
    print(
        f"FP<=15 blind: {(fp['gest_blind'] <= 15).sum()}/{fp.height}   "
        f"INT/NOISE>=75 blind: {(intr['gest_blind'] >= 75).sum()}/{intr.height}"
    )


if __name__ == "__main__":
    main()
