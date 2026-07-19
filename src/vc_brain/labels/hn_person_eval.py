"""Pod H eval: person-level HN stream numbers.

Reads data/labels/hn_persons.parquet + hn_person_stories.parquet and reports:
  1. identity-link rates founders vs controls (existence / strict / inclusive);
  2. pre-cutoff Show HN prevalence founders vs controls (the interesting
     number: is launching-on-HN pre-cutoff founder-predictive?);
  3. post-cutoff Show/Launch HN stories by CONTROLS as new outcome labels /
     label-noise candidates, cross-referenced against the 92 high-gestation
     controls and the wave-2 control screen.

Every claim printed with n, rate, exact CI, and URLs for the interesting rows.
"""

from __future__ import annotations

import polars as pl
from scipy.stats import fisher_exact

from vc_brain.ingest.contracts import DATA_ROOT
from vc_brain.labels.hn_persons import PERSONS_PATH, STORIES_PATH
from vc_brain.labels.control_screen import binomial_ci

FULL_ANNOTATIONS_PATH = DATA_ROOT / "pilot" / "full_annotations.parquet"
CONTROL_SCREEN_PATH = DATA_ROOT / "pilot" / "control_screen.parquet"
HIGH_GESTATION = 70


def rate_line(label: str, k: int, n: int) -> str:
    lo, hi = binomial_ci(k, n)
    return f"{label:42s} {k:4d}/{n:4d} = {k/n:6.1%}  (95% CI {lo:.1%}-{hi:.1%})"


def fisher_line(kf: int, nf: int, kc: int, nc: int) -> str:
    odds, p = fisher_exact([[kf, nf - kf], [kc, nc - kc]])
    return f"Fisher exact: OR = {odds:.2f}, p = {p:.4g}"


def main() -> None:
    persons = pl.read_parquet(PERSONS_PATH)
    stories = pl.read_parquet(STORIES_PATH)
    founders = persons.filter(pl.col("person_type") == "positive")
    controls = persons.filter(pl.col("person_type") == "control")
    nf, nc = founders.height, controls.height

    print("=" * 78)
    print("1. IDENTITY LINKAGE (hn_username == gh_login), founders vs controls")
    print("=" * 78)
    for label, expr in [
        ("HN account exists", pl.col("hn_exists")),
        ("confirmed STRICT (strong tiers + LLM)", pl.col("confirmed_strict")),
        ("confirmed incl. medium_rare_name", pl.col("confirmed")),
        ("confirmed, CLASS-SYMMETRIC tiers only", pl.col("confirmed_symmetric")),
    ]:
        kf = founders.filter(expr).height
        kc = controls.filter(expr).height
        print(rate_line(f"founders: {label}", kf, nf))
        print(rate_line(f"controls: {label}", kc, nc))
        print("  " + fisher_line(kf, nf, kc, nc))
    print("\ngrade breakdown:")
    print(
        persons.filter(pl.col("hn_exists"))
        .group_by("person_type", "match_grade").len()
        .sort("person_type", "len", descending=[True, True])
    )

    print()
    print("=" * 78)
    print("2. PRE-CUTOFF SHOW HN PREVALENCE (feature-side signal)")
    print("=" * 78)
    pre = stories.filter(
        (pl.col("pre_or_post_cutoff") == "pre_cutoff")
        & (pl.col("is_show_hn") | pl.col("is_launch_hn"))
    )
    pre_authors = pre.group_by("gh_login", "person_type").agg(
        pl.len().alias("n_pre_shows"),
        pl.col("points").max().alias("max_points"),
    )
    for strict in (True, False):
        col = "confirmed_strict" if strict else "confirmed"
        conf = persons.filter(pl.col(col))
        conf_f = conf.filter(pl.col("person_type") == "positive").height
        conf_c = conf.filter(pl.col("person_type") == "control").height
        pa = pre_authors.filter(
            pl.col("gh_login").is_in(conf["gh_login"].implode())
        )
        kf = pa.filter(pl.col("person_type") == "positive").height
        kc = pa.filter(pl.col("person_type") == "control").height
        print(f"\n-- link tier: {'STRICT' if strict else 'incl. medium_rare_name'} --")
        print("  denominator = all scored actors (existence of a confirmed pre-cutoff Show/Launch HN):")
        print("  " + rate_line("founders", kf, nf))
        print("  " + rate_line("controls", kc, nc))
        print("    " + fisher_line(kf, nf, kc, nc))
        print(f"  denominator = confirmed-linked actors ({conf_f} F / {conf_c} C):")
        if conf_f and conf_c:
            print("  " + rate_line("founders", kf, conf_f))
            print("  " + rate_line("controls", kc, conf_c))
            print("    " + fisher_line(kf, conf_f, kc, conf_c))
        tot = kf + kc
        if tot:
            print(f"  P(founder | pre-cutoff Show HN author) = {kf}/{tot} = {kf/tot:.1%}"
                  f"  vs base rate {nf/(nf+nc):.1%}")
    print("\npre-cutoff Show/Launch HN stories (all, chronological):")
    with pl.Config(fmt_str_lengths=90, tbl_rows=-1, tbl_width_chars=200):
        print(
            pre.join(
                persons.select("gh_login", "match_grade", "peak"), on="gh_login"
            )
            .select("gh_login", "person_type", "match_grade", "created_at",
                    "t_cutoff", "title", "points", "url")
            .sort("created_at")
        )

    print()
    print("=" * 78)
    print("3. POST-CUTOFF LAUNCHES AS OUTCOME LABELS (controls = label-noise candidates)")
    print("=" * 78)
    post = stories.filter(
        (pl.col("pre_or_post_cutoff") == "post_cutoff")
        & (pl.col("is_show_hn") | pl.col("is_launch_hn"))
    )
    post_authors = post.group_by("gh_login", "person_type").agg(
        pl.len().alias("n_post"), pl.col("points").max().alias("max_points")
    )
    kf = post_authors.filter(pl.col("person_type") == "positive").height
    kc = post_authors.filter(pl.col("person_type") == "control").height
    print(rate_line("founders with post-cutoff Show/Launch HN", kf, nf))
    print(rate_line("controls with post-cutoff Show/Launch HN", kc, nc))

    ann = pl.read_parquet(FULL_ANNOTATIONS_PATH).with_columns(
        pl.col("gestation_likelihood").cast(pl.Float64, strict=False)
    )
    ctrl_post = (
        post.filter(pl.col("person_type") == "control")
        .join(ann.select("gh_login", "gestation_likelihood", "builder_type"),
              on="gh_login", how="left")
        .join(persons.select("gh_login", "match_grade", "peak"), on="gh_login")
    )
    print("\ncontrol post-cutoff launch stories (new outcome labels):")
    with pl.Config(fmt_str_lengths=90, tbl_rows=-1, tbl_width_chars=220):
        print(
            ctrl_post.select(
                "gh_login", "match_grade", "gestation_likelihood", "builder_type",
                "created_at", "title", "points", "url"
            ).sort("created_at")
        )

    # cross-reference: 92 high-gestation controls
    hg = (
        persons.filter(pl.col("person_type") == "control")
        .join(ann.select("gh_login", "gestation_likelihood"), on="gh_login")
        .filter(pl.col("gestation_likelihood") >= HIGH_GESTATION)
    )
    hg_logins = set(hg["gh_login"].to_list())
    hg_post = ctrl_post.filter(pl.col("gh_login").is_in(sorted(hg_logins)))
    print(f"\nhigh-gestation controls (g>={HIGH_GESTATION}): {hg.height}; "
          f"with confirmed HN account: {hg.filter(pl.col('confirmed')).height}; "
          f"with post-cutoff launch: {hg_post['gh_login'].n_unique()}")

    if CONTROL_SCREEN_PATH.exists():
        screen = pl.read_parquet(CONTROL_SCREEN_PATH)
        overlap = ctrl_post.join(
            screen.select("gh_login", "classification", "company_or_product"),
            on="gh_login", how="inner",
        )
        print("\ncontrol launch authors also in wave-2 screen:")
        with pl.Config(fmt_str_lengths=60, tbl_rows=-1):
            print(
                overlap.select("gh_login", "classification", "company_or_product",
                               "title").unique(subset=["gh_login", "title"])
                .sort("gh_login")
            )

    # story timing relative to cutoff, months
    print("\nstory timing (Show/Launch only, confirmed accounts), months vs cutoff:")
    tim = (
        stories.filter(pl.col("is_show_hn") | pl.col("is_launch_hn"))
        .with_columns(
            ((pl.col("created_at").dt.date() - pl.col("t_cutoff")).dt.total_days()
             / 30.44).alias("months_vs_cutoff")
        )
    )
    print(
        tim.group_by("person_type", "pre_or_post_cutoff").agg(
            pl.len(),
            pl.col("months_vs_cutoff").median().round(1).alias("median_months"),
            pl.col("months_vs_cutoff").min().round(1).alias("min"),
            pl.col("months_vs_cutoff").max().round(1).alias("max"),
        ).sort("person_type", "pre_or_post_cutoff", descending=[True, False])
    )


if __name__ == "__main__":
    main()
