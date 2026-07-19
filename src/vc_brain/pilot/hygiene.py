"""Pod E — negative-pool hygiene + corrected full-cohort metrics.

The wave-2 control screen (`labelnoise/screen.py`) confirmed a set of
"controls" who are actually founders the YC-only label source never saw
(classification FOUNDER_EVIDENCE, every row with a URL). This module:

1. materializes `data/pilot/excluded_controls.parquet` — the canonical
   exclusion list (gh_login, reason, evidence_url, source) built from the
   wave-2 screen, plus any wave-3 mid-band screen hits if that file exists;
2. re-runs the full-cohort evaluation (`eval_full` logic) with those people
   EXCLUDED from the control pool (dropped entirely — not relabeled), and
   prints corrected vs uncorrected numbers side by side: overall/annotated
   AUC, within-match-group pairwise AUC, and the p@K table under the three
   rankings (counts / interactivity / semantic).

The screen evidence is current-day data (data_basis=current_day_label_only);
it is used here strictly for evaluation-time label hygiene — never features.
Deterministic: pure reads of cached parquets, sorted iteration, no network.
"""

from __future__ import annotations

import polars as pl

from vc_brain.ingest.contracts import DATA_ROOT
from vc_brain.pilot.content_features import auc
from vc_brain.pilot.eval_full import K_LIST, TOP_REGION_PEAK, load_frame, precision_at_k

SCREEN_PATH = DATA_ROOT / "pilot" / "control_screen.parquet"
MID_SCREEN_PATH = DATA_ROOT / "pilot" / "control_screen_mid.parquet"
EXCLUDED_PATH = DATA_ROOT / "pilot" / "excluded_controls.parquet"


def build_exclusions() -> pl.DataFrame:
    """Confirmed unlabeled founders from the wave-2 screen (+ wave-3 mid band)."""
    parts = []
    for path, source in ((SCREEN_PATH, "wave2_screen"), (MID_SCREEN_PATH, "wave3_mid_screen")):
        if not path.exists():
            continue
        hits = pl.read_parquet(path).filter(
            pl.col("classification") == "FOUNDER_EVIDENCE"
        )
        parts.append(
            hits.select(
                "gh_login",
                (
                    pl.lit("FOUNDER_EVIDENCE: ")
                    + pl.col("company_or_product").fill_null("?")
                    + pl.lit(" — ")
                    + pl.col("best_evidence").fill_null("")
                ).alias("reason"),
                "evidence_url",
                pl.lit(source).alias("source"),
                "data_basis",
            )
        )
    out = pl.concat(parts).unique(subset="gh_login", keep="first").sort("source", "gh_login")
    EXCLUDED_PATH.parent.mkdir(parents=True, exist_ok=True)
    out.write_parquet(EXCLUDED_PATH)
    return out


def pairwise_auc(frame: pl.DataFrame, feature: str) -> tuple[float, int, int, int]:
    """Within-match-group founder-vs-control pairwise AUC (nulls -> 0)."""
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
    return (wins + 0.5 * ties) / total, wins, ties, losses


def rankings(frame: pl.DataFrame) -> dict[str, pl.DataFrame]:
    return {
        "counts": frame.sort("peak", descending=True, nulls_last=True),
        "interact": frame.filter(pl.col("has_text") == 1).sort(
            "peak", descending=True, nulls_last=True
        ),
        "semantic": frame.with_columns(
            pl.col("gestation_likelihood").fill_null(0.0)
        ).sort(["gestation_likelihood", "peak"], descending=[True, True], nulls_last=True),
    }


def metrics(frame: pl.DataFrame) -> dict:
    annotated = frame.drop_nulls("gestation_likelihood")
    ranked = rankings(frame)
    top = frame.filter(pl.col("peak") >= TOP_REGION_PEAK)
    return {
        "n": frame.height,
        "n_pos": frame.filter(pl.col("person_type") == "positive").height,
        "n_annotated": annotated.height,
        "auc_gestation": auc(annotated, "gestation_likelihood"),
        "auc_peak": auc(annotated, "peak"),
        "pair_gestation": pairwise_auc(frame, "gestation_likelihood"),
        "pair_peak": pairwise_auc(frame, "peak"),
        "p_at_k": {
            name: {k: precision_at_k(r, k) for k in K_LIST} for name, r in ranked.items()
        },
        "top_region_precision": (
            top.filter(pl.col("person_type") == "positive").height,
            top.height,
        ),
    }


def report(variants: list[tuple[str, dict]]) -> None:
    names = [name for name, _ in variants]
    cols = {name: m for name, m in variants}
    base = cols[names[0]]
    print(
        "\n=== corrected metrics: confirmed unlabeled founders EXCLUDED from controls ==="
    )
    print(
        "cohort sizes: "
        + "; ".join(f"{name} n={m['n']} (annotated {m['n_annotated']})" for name, m in variants)
        + f"; positives {base['n_pos']} unchanged"
    )
    print("\n-- founder-vs-control AUC (annotated subset)")
    print(f"{'':22s}" + "".join(f"{name:>16s}" for name in names))
    for key, label in (("auc_gestation", "gestation AUC"), ("auc_peak", "peak AUC")):
        print(f"{label:22s}" + "".join(f"{cols[n][key]:16.3f}" for n in names))
    print("\n-- within-match-group pairwise AUC (nulls->0)")
    for key, label in (("pair_gestation", "gestation"), ("pair_peak", "peak")):
        cells = "  ".join(
            f"{name} {cols[name][key][0]:.3f} (w/t/l "
            f"{cols[name][key][1]}/{cols[name][key][2]}/{cols[name][key][3]})"
            for name in names
        )
        print(f"{label:10s} {cells}")
    print("\n-- precision@K (" + " | ".join(names) + ")")
    print(f"{'K':>5s}" + "".join(f" {r:>25s}" for r in ("counts", "interact", "semantic")))
    for k in K_LIST:
        cells = "".join(
            "   " + " | ".join(f"{cols[n]['p_at_k'][r][k]:.3f}" for n in names)
            for r in ("counts", "interact", "semantic")
        )
        print(f"{k:5d}{cells}")
    precisions = " -> ".join(
        f"{m['top_region_precision'][0]}/{m['top_region_precision'][1]}"
        f" = {m['top_region_precision'][0] / m['top_region_precision'][1]:.1%}"
        for _, m in variants
    )
    print(f"\n-- top-region (peak>={TOP_REGION_PEAK}) label precision: {precisions}")


def exclude(frame: pl.DataFrame, logins: pl.Series) -> pl.DataFrame:
    excluded = frame.filter(
        (pl.col("person_type") == "control") & pl.col("gh_login").is_in(logins.implode())
    )
    assert excluded.height == logins.len(), (
        f"exclusion list has {logins.len()} logins but only "
        f"{excluded.height} are cohort controls"
    )
    return frame.filter(
        ~((pl.col("person_type") == "control") & pl.col("gh_login").is_in(logins.implode()))
    )


def main() -> None:
    exclusions = build_exclusions()
    print(f"exclusion list -> {EXCLUDED_PATH} ({exclusions.height} rows)")
    with pl.Config(fmt_str_lengths=70, tbl_rows=30, tbl_width_chars=140):
        print(exclusions.select("gh_login", "source", "evidence_url"))

    frame = load_frame()
    wave2 = exclusions.filter(pl.col("source") == "wave2_screen")["gh_login"]
    variants = [
        ("uncorrected", metrics(frame)),
        (f"wave2-{wave2.len()}excl", metrics(exclude(frame, wave2))),
    ]
    if exclusions.height > wave2.len():
        variants.append(
            (f"all-{exclusions.height}excl", metrics(exclude(frame, exclusions["gh_login"])))
        )
    report(variants)


if __name__ == "__main__":
    main()
