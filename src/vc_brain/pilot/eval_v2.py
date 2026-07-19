"""Evaluate instrument v2 (structure-preserving blind + fine gestation scale)
against the wave-2 v1 numbers on the same people.

Sections:
  1. score resolution: distinct values, round-number clustering, v1 vs v2;
  2. founder-vs-control AUC on the common annotated set (+ top-region view
     against Pod B's strict-blind numbers);
  3. matched-pairs pairwise AUC on the full cohort (hybrid fill: v2 where
     annotated, else v1, else 0 -- the production ranking);
  4. precision@K K=10..200 on the full 2,765-actor cohort: counts vs v1
     semantic vs v2-hybrid semantic (does the K>=50 inversion disappear?);
  5. portrait cross-check (hand-labeled FP/INT/NOISE people);
  6. blind-v2 vs unblinded-v1 deltas on the top region, focusing on Pod B's
     largest strict-blind droppers (did USER_ORG masking fix the artifact?).
"""

from __future__ import annotations

import polars as pl

from vc_brain.pilot.annotate import FULL_ANNOTATIONS_PATH
from vc_brain.pilot.annotate_v2 import V2_ANNOTATIONS_PATH
from vc_brain.pilot.blind_check import BLIND_ANNOTATIONS_PATH
from vc_brain.pilot.content_features import auc
from vc_brain.pilot.eval_blind import portrait_classes
from vc_brain.pilot.extract import (
    FULL_COHORT_PATH,
    FULL_TEXT_EVENTS_PATH,
    PILOT_COHORT_PATH,
)

K_LIST = (10, 25, 50, 100, 150, 200)


def load_frame() -> pl.DataFrame:
    cohort = pl.read_parquet(FULL_COHORT_PATH)
    events = pl.read_parquet(FULL_TEXT_EVENTS_PATH)
    with_text = events.select(
        pl.col("actor_login").unique().alias("gh_login")
    ).with_columns(pl.lit(1).alias("has_text"))
    v1 = pl.read_parquet(FULL_ANNOTATIONS_PATH).select(
        "gh_login",
        pl.col("gestation_likelihood").cast(pl.Float64, strict=False).alias("gest_v1"),
        pl.col("builder_type").alias("type_v1"),
    )
    v2 = pl.read_parquet(V2_ANNOTATIONS_PATH).select(
        "gh_login",
        pl.col("gestation_likelihood").cast(pl.Float64, strict=False).alias("gest_v2"),
        pl.col("builder_type").alias("type_v2"),
        "rank_evidence",
    )
    return (
        cohort.join(with_text, on="gh_login", how="left")
        .with_columns(pl.col("has_text").fill_null(0))
        .join(v1, on="gh_login", how="left")
        .join(v2, on="gh_login", how="left")
        .sort("gh_login")
    )


def resolution(frame: pl.DataFrame) -> None:
    both = frame.drop_nulls(["gest_v1", "gest_v2"])
    print("=== 1. score resolution (common annotated set, n=%d) ===" % both.height)
    for col in ("gest_v1", "gest_v2"):
        vals = both[col]
        mult5 = float((vals % 5 == 0).mean())
        mult10 = float((vals % 10 == 0).mean())
        print(
            f"{col}: distinct={vals.n_unique():3d}  "
            f"share multiple-of-5={mult5:.1%}  of-10={mult10:.1%}"
        )
    top10 = (
        both.group_by("gest_v2").len().sort("len", descending=True).head(10)
    )
    print("most common v2 values:",
          [(int(r["gest_v2"]), r["len"]) for r in top10.iter_rows(named=True)])
    print("v2 distinct over ALL annotated:",
          frame.drop_nulls("gest_v2")["gest_v2"].n_unique(),
          f"(n={frame.drop_nulls('gest_v2').height})")
    spear = both.select(
        pl.corr(
            pl.col("gest_v1").rank("average"), pl.col("gest_v2").rank("average")
        )
    ).item()
    print(f"Spearman(v1, v2) = {spear:.3f}")


def auc_section(frame: pl.DataFrame) -> None:
    both = frame.drop_nulls(["gest_v1", "gest_v2"])
    print(f"\n=== 2. founder-vs-control AUC, common annotated set (n={both.height}, "
          f"pos={both.filter(pl.col('person_type') == 'positive').height}) ===")
    for col in ("gest_v1", "gest_v2", "peak"):
        print(f"  {col:8s} {auc(both, col):.3f}")
    top_logins = (
        pl.read_parquet(PILOT_COHORT_PATH)
        .filter(pl.col("stratum") == "top_region")["gh_login"]
    )
    top = both.filter(pl.col("gh_login").is_in(top_logins.implode()))
    blind = pl.read_parquet(BLIND_ANNOTATIONS_PATH).select(
        "gh_login",
        pl.col("gestation_likelihood").cast(pl.Float64, strict=False).alias(
            "gest_blind_v1"
        ),
    )
    top = top.join(blind, on="gh_login", how="left")
    print(f"top region (n={top.height}, "
          f"pos={top.filter(pl.col('person_type') == 'positive').height}):")
    for col in ("gest_v1", "gest_blind_v1", "gest_v2", "peak"):
        print(f"  {col:14s} {auc(top, col):.3f}")


def pairwise_auc(frame: pl.DataFrame, feature: str) -> tuple[float, str]:
    scored = frame.with_columns(pl.col(feature).fill_null(0.0))
    wins = ties = losses = 0
    for _, grp in scored.group_by("match_group_id"):
        pos = grp.filter(pl.col("person_type") == "positive")
        neg = grp.filter(pl.col("person_type") == "control")
        if not pos.height or not neg.height:
            continue
        p = pos[feature][0]
        for n in neg[feature]:
            if p > n:
                wins += 1
            elif p == n:
                ties += 1
            else:
                losses += 1
    total = wins + ties + losses
    return (wins + 0.5 * ties) / total, f"w={wins} t={ties} l={losses}"


def matched_pairs(frame: pl.DataFrame) -> None:
    hybrid = frame.with_columns(
        pl.coalesce("gest_v2", "gest_v1").alias("gest_hybrid")
    )
    print("\n=== 3. within-match-group pairwise AUC, full cohort (nulls->0) ===")
    for feat in ("gest_hybrid", "gest_v1", "peak"):
        score, detail = pairwise_auc(hybrid, feat)
        print(f"  {feat:12s} AUC={score:.3f}  ({detail})")


def precision_table(frame: pl.DataFrame) -> None:
    n_pos = frame.filter(pl.col("person_type") == "positive").height
    print(f"\n=== 4. precision@K, full cohort ({frame.height} actors, {n_pos} pos) ===")
    rankings = {
        "counts": frame.sort("peak", descending=True, nulls_last=True),
        "v1-sem": frame.with_columns(pl.col("gest_v1").fill_null(0.0)).sort(
            ["gest_v1", "peak"], descending=[True, True], nulls_last=True
        ),
        "v2-hyb": frame.with_columns(
            pl.coalesce("gest_v2", "gest_v1").fill_null(0.0).alias("g")
        ).sort(["g", "peak"], descending=[True, True], nulls_last=True),
    }
    print(f"{'K':>5s} " + " ".join(f"{n:>8s}" for n in rankings))
    for k in K_LIST:
        row = " ".join(
            f"{float((r.head(k)['person_type'] == 'positive').mean()):8.3f}"
            for r in rankings.values()
        )
        print(f"{k:5d} {row}")


def portrait(frame: pl.DataFrame) -> None:
    joined = portrait_classes().join(
        frame.drop_nulls("gest_v2"), on="gh_login", how="inner"
    )
    print(f"\n=== 5. portrait cross-check (v2, n={joined.height}) ===")
    print(
        joined.group_by("portrait_class").agg(
            pl.len(),
            pl.col("gest_v1").mean().round(1).alias("mean_v1"),
            pl.col("gest_v2").mean().round(1).alias("mean_v2"),
        ).sort("portrait_class")
    )
    fp = joined.filter(pl.col("portrait_class") == "FP")
    intr = joined.filter(pl.col("portrait_class").is_in(["INT", "NOISE"]))
    print(
        f"FP<=29 v2: {(fp['gest_v2'] <= 29).sum()}/{fp.height}   "
        f"INT/NOISE>=70 v2: {(intr['gest_v2'] >= 70).sum()}/{intr.height}"
    )
    print(joined.select(
        "gh_login", "portrait_class", "gest_v1", "gest_v2", "type_v2"
    ).sort("portrait_class", "gest_v2"))


def blind_artifact(frame: pl.DataFrame) -> None:
    """Did USER_ORG masking fix Pod B's org-create artifact?"""
    blind = pl.read_parquet(BLIND_ANNOTATIONS_PATH).select(
        "gh_login",
        pl.col("gestation_likelihood").cast(pl.Float64, strict=False).alias(
            "gest_blind_v1"
        ),
    )
    top_logins = (
        pl.read_parquet(PILOT_COHORT_PATH)
        .filter(pl.col("stratum") == "top_region")["gh_login"]
    )
    top = (
        frame.filter(pl.col("gh_login").is_in(top_logins.implode()))
        .join(blind, on="gh_login", how="left")
        .drop_nulls(["gest_v1", "gest_blind_v1", "gest_v2"])
        .with_columns(
            (pl.col("gest_v1") - pl.col("gest_blind_v1")).alias("drop_strict"),
            (pl.col("gest_v1") - pl.col("gest_v2")).alias("drop_v2"),
        )
    )
    print(f"\n=== 6. blinding artifact check, top region (n={top.height}) ===")
    print("delta(unblinded v1 - X) distribution:")
    for col in ("drop_strict", "drop_v2"):
        d = top[col]
        print(
            f"  {col:12s} mean={d.mean():+6.2f} median={d.median():+5.1f} "
            f"std={d.std():5.1f}  |d|<=10: {float((d.abs() <= 10).mean()):.1%}  "
            f"d>=+30: {float((d >= 30).mean()):.1%}  d<=-30: {float((d <= -30).mean()):.1%}"
        )
    droppers = top.sort("drop_strict", descending=True).head(20)
    print("\nPod B's 20 largest strict-blind droppers under v2:")
    print(droppers.select(
        "gh_login", "person_type", "gest_v1", "gest_blind_v1", "gest_v2", "type_v2"
    ))
    print(
        "  mean gestation: unblinded-v1=%.1f strict-blind=%.1f v2=%.1f"
        % (
            droppers["gest_v1"].mean(),
            droppers["gest_blind_v1"].mean(),
            droppers["gest_v2"].mean(),
        )
    )


def main() -> None:
    frame = load_frame()
    print(
        f"cohort {frame.height}; v1 annotated {frame.drop_nulls('gest_v1').height}; "
        f"v2 annotated {frame.drop_nulls('gest_v2').height}\n"
    )
    resolution(frame)
    auc_section(frame)
    matched_pairs(frame)
    precision_table(frame)
    portrait(frame)
    blind_artifact(frame)


if __name__ == "__main__":
    main()
