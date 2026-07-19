"""Full-cohort evaluation of the semantic-annotation instrument.

Scales the pilot's top-region analysis to every scored actor (690 founders,
2,075 controls): interactivity rule, precision@K under three rankings,
gestation AUC by peak-quartile, and the observability boundary measured on
all scored founders. All annotation inputs are pre-t_cutoff event text only.
"""

from __future__ import annotations

import polars as pl

from vc_brain.pilot.annotate import FULL_ANNOTATIONS_PATH
from vc_brain.pilot.content_features import auc
from vc_brain.pilot.extract import FULL_COHORT_PATH, FULL_TEXT_EVENTS_PATH

TOP_REGION_PEAK = 0.28  # same threshold as the pilot's top_region stratum
K_LIST = (10, 25, 50, 100, 200)


def load_frame() -> pl.DataFrame:
    """Full cohort + has_text flag + annotations (left join)."""
    cohort = pl.read_parquet(FULL_COHORT_PATH)
    events = pl.read_parquet(FULL_TEXT_EVENTS_PATH)
    with_text = events.select(pl.col("actor_login").unique().alias("gh_login")).with_columns(
        pl.lit(1).alias("has_text")
    )
    ann = pl.read_parquet(FULL_ANNOTATIONS_PATH).with_columns(
        pl.col("gestation_likelihood").cast(pl.Float64, strict=False),
        pl.col("productization").cast(pl.Float64, strict=False),
    )
    return (
        cohort.join(with_text, on="gh_login", how="left")
        .with_columns(pl.col("has_text").fill_null(0))
        .join(ann, on="gh_login", how="left")
        .sort("gh_login")
    )


def precision_at_k(ranked: pl.DataFrame, k: int) -> float:
    return float((ranked.head(k)["person_type"] == "positive").mean())


def interactivity_rule(frame: pl.DataFrame) -> None:
    print("=== interactivity rule (zero text events => filtered) ===")
    for name, sub in (
        ("overall", frame),
        (f"top region (peak>={TOP_REGION_PEAK})", frame.filter(pl.col("peak") >= TOP_REGION_PEAK)),
    ):
        counts = (
            sub.group_by("person_type")
            .agg(pl.len().alias("n"), (pl.col("has_text") == 0).sum().alias("no_text"))
            .sort("person_type")
        )
        print(f"-- {name}")
        for r in counts.iter_rows(named=True):
            print(
                f"   {r['person_type']:8s} n={r['n']:5d}  filtered={r['no_text']:4d}"
                f"  ({r['no_text'] / r['n']:.1%})"
            )


def precision_table(frame: pl.DataFrame) -> None:
    ranked_counts = frame.sort("peak", descending=True, nulls_last=True)
    ranked_filtered = frame.filter(pl.col("has_text") == 1).sort(
        "peak", descending=True, nulls_last=True
    )
    ranked_sem = frame.with_columns(
        pl.col("gestation_likelihood").fill_null(0.0)
    ).sort(["gestation_likelihood", "peak"], descending=[True, True], nulls_last=True)
    print("\n=== precision@K, overall cohort (2,765 actors, 690 positives) ===")
    print(f"{'K':>5s} {'counts':>8s} {'interact':>9s} {'semantic':>9s}")
    for k in K_LIST:
        print(
            f"{k:5d} {precision_at_k(ranked_counts, k):8.3f}"
            f" {precision_at_k(ranked_filtered, k):9.3f}"
            f" {precision_at_k(ranked_sem, k):9.3f}"
        )


def gestation_auc(frame: pl.DataFrame) -> None:
    annotated = frame.drop_nulls("gestation_likelihood")
    print("\n=== gestation AUC (annotated subset) ===")
    print(
        f"overall (n={annotated.height}): "
        f"gestation={auc(annotated, 'gestation_likelihood'):.3f}  "
        f"peak-baseline={auc(annotated, 'peak'):.3f}"
    )
    quartiled = annotated.with_columns(
        (pl.col("peak").rank("ordinal") * 4 / (annotated.height + 1))
        .floor()
        .cast(pl.Int8)
        .clip(0, 3)
        .alias("peak_q")
    )
    for q in range(4):
        sub = quartiled.filter(pl.col("peak_q") == q)
        n_pos = sub.filter(pl.col("person_type") == "positive").height
        print(
            f"peak Q{q + 1} (n={sub.height}, pos={n_pos}): "
            f"gestation={auc(sub, 'gestation_likelihood'):.3f}  "
            f"peak={auc(sub, 'peak'):.3f}"
        )


def observability_boundary(frame: pl.DataFrame) -> None:
    founders = frame.filter(pl.col("person_type") == "positive")
    annotated = founders.drop_nulls("builder_type")
    print(f"\n=== observability boundary: all {founders.height} scored founders ===")
    print(
        f"no text events: {founders.filter(pl.col('has_text') == 0).height}"
        f"  |  annotated: {annotated.height}"
    )
    shares = (
        annotated.group_by("builder_type")
        .len()
        .with_columns((pl.col("len") / annotated.height).alias("share"))
        .sort("len", descending=True)
    )
    for r in shares.iter_rows(named=True):
        print(f"   {r['builder_type']:24s} {r['len']:4d}  {r['share']:.1%}")
    own = annotated.filter(pl.col("builder_type") == "own_product_building").height
    print(
        f"own_product_building: {own}/{annotated.height} annotated "
        f"({own / annotated.height:.1%}); of ALL founders {own}/{founders.height} "
        f"({own / founders.height:.1%})"
    )


def within_group_auc(frame: pl.DataFrame, feature: str) -> None:
    """Pairwise founder-vs-matched-control comparison (same cutoff month).

    Unannotated actors count as 0 — the interactivity rule applied inside the
    matched design. This is the frozen-clock deployment view: same month, same
    candidate pool, who ranks higher?
    """
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
    print(
        f"\n=== within-match-group pairwise AUC ({feature}, nulls->0) ===\n"
        f"wins={wins} ties={ties} losses={losses} of {total} pairs"
        f" -> AUC={(wins + 0.5 * ties) / total:.3f}"
    )


def builder_type_by_class(frame: pl.DataFrame) -> None:
    annotated = frame.drop_nulls("builder_type")
    print("\n=== builder_type composition, founders vs controls (annotated) ===")
    table = (
        annotated.group_by("person_type", "builder_type")
        .len()
        .join(
            annotated.group_by("person_type").len().rename({"len": "n_class"}),
            on="person_type",
        )
        .with_columns((pl.col("len") / pl.col("n_class")).alias("share"))
        .sort("builder_type", "person_type")
    )
    for r in table.iter_rows(named=True):
        print(
            f"   {r['builder_type']:24s} {r['person_type']:8s} "
            f"{r['len']:4d}  {r['share']:.1%}"
        )
    print("\n   gestation_likelihood by class:")
    print(
        annotated.group_by("person_type").agg(
            pl.col("gestation_likelihood").median().alias("median"),
            pl.col("gestation_likelihood").quantile(0.25).alias("p25"),
            pl.col("gestation_likelihood").quantile(0.75).alias("p75"),
            (pl.col("gestation_likelihood") >= 70).mean().alias("share_ge70"),
            pl.len(),
        )
    )


def main() -> None:
    frame = load_frame()
    n_pos = frame.filter(pl.col("person_type") == "positive").height
    print(
        f"full cohort: {frame.height} actors ({n_pos} positives), "
        f"{frame.filter(pl.col('has_text') == 1).height} with text, "
        f"{frame.drop_nulls('gestation_likelihood').height} annotated\n"
    )
    interactivity_rule(frame)
    precision_table(frame)
    gestation_auc(frame)
    within_group_auc(frame, "gestation_likelihood")
    within_group_auc(frame, "peak")
    observability_boundary(frame)
    builder_type_by_class(frame)


if __name__ == "__main__":
    main()
