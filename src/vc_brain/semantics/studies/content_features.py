"""Content features from pre-cutoff text events: learning vs building.

Validates the FP-portrait hypothesis that the dominant false-positive mode
(tutorial/bootcamp bursts) is separable by content, not counts. All features
are computed on the leakage-safe pre-cutoff extraction only.
"""

from __future__ import annotations

import polars as pl

from vc_brain.semantics.person_extract import PILOT_COHORT_PATH, PILOT_DIR, TEXT_EVENTS_PATH

FEATURES_PATH = PILOT_DIR / "content_features.parquet"

# Curriculum / tutorial-grind naming in repos the actor creates or forks.
LEARNING_REPO = (
    r"(?i)(tutorial|course|learn|study|practi[cs]e|exercise|bootcamp|udemy|"
    r"coursera|freecodecamp|codecademy|alx[-_]|holberton|odin[-_]?project|"
    r"100[-_]?days|leetcode|hackerrank|codewars|neetcode|interview[-_]?prep|"
    r"data[-_]?structures|dsa[-_/]|algorithms?[-_]|cs\d{2,4}|cse\d{2,4}|"
    r"assignment|homework|hw\d|lab[-_]?\d|week[-_]?\d|day[-_]?\d+|chapter|"
    r"lesson|training|beginner|starter[-_]?kit|boilerplate|sample[-_]?app|"
    r"demo[-_]?app|test[-_]?repo|playground|sandbox|hello[-_]?world|"
    r"portfolio|resume|cv[-_]|dotfiles)"
)
# Product/commercial vocabulary in issue & PR titles/bodies the actor writes.
PRODUCT_TEXT = (
    r"(?i)(launch|pricing|billing|subscription|checkout|onboarding|signup|"
    r"sign[-_ ]up|waitlist|landing[-_ ]page|customer|end[-_ ]user|feedback|"
    r"analytics|production|deploy|release[-_ ]notes|changelog|roadmap|beta|"
    r"early[-_ ]access|saas|api[-_ ]key|rate[-_ ]limit|stripe|paywall)"
)
SHIPPING_TEXT = r"(?i)(docs|documentation|readme|license|ci|github[-_ ]actions|test coverage|versioning|semver|migration)"


def _owner(col: pl.Expr) -> pl.Expr:
    return col.str.split("/").list.get(0)


def build_features() -> pl.DataFrame:
    events = pl.read_parquet(TEXT_EVENTS_PATH)
    own = pl.col("repo_name").pipe(_owner).str.to_lowercase() == pl.col(
        "actor_login"
    ).str.to_lowercase()
    created_repo = (pl.col("event_type") == "CreateEvent") & (
        pl.col("ref_type") == "repository"
    )
    text = pl.col("title").fill_null("") + " " + pl.col("body").fill_null("")

    per_actor = events.group_by("actor_login").agg(
        pl.len().alias("n_events"),
        created_repo.sum().alias("repos_created"),
        (created_repo & pl.col("repo_name").str.contains(LEARNING_REPO))
        .sum()
        .alias("repos_created_learning"),
        ((pl.col("event_type") == "ForkEvent")).sum().alias("forks"),
        (
            (pl.col("event_type") == "ForkEvent")
            & pl.col("repo_name").str.contains(LEARNING_REPO)
        )
        .sum()
        .alias("forks_learning"),
        (pl.col("event_type") == "ReleaseEvent").sum().alias("releases"),
        ((pl.col("event_type") == "CreateEvent") & (pl.col("ref_type") == "tag"))
        .sum()
        .alias("tags_created"),
        ((pl.col("event_type") == "MemberEvent") & own)
        .sum()
        .alias("members_added_own_repo"),
        (own & created_repo.not_() & (pl.col("event_type") != "ForkEvent"))
        .sum()
        .alias("own_repo_work_events"),
        (own.not_() & (pl.col("event_type") != "ForkEvent"))
        .sum()
        .alias("other_repo_events"),
        (
            pl.col("event_type").is_in(
                ["IssuesEvent", "PullRequestEvent", "IssueCommentEvent"]
            )
            & text.str.contains(PRODUCT_TEXT)
        )
        .sum()
        .alias("product_text_events"),
        (
            pl.col("event_type").is_in(["IssuesEvent", "PullRequestEvent"])
            & own
            & text.str.contains(SHIPPING_TEXT)
        )
        .sum()
        .alias("shipping_text_events"),
        ((pl.col("event_type") == "PullRequestEvent") & own.not_() & (pl.col("merged") == 1))
        .sum()
        .alias("merged_prs_external"),
        (pl.col("author_association") == "OWNER").sum().alias("owner_assoc_events"),
    )

    ratios = per_actor.with_columns(
        (pl.col("repos_created_learning") / pl.col("repos_created").clip(1))
        .alias("learning_repo_share"),
        (pl.col("forks_learning") / pl.col("forks").clip(1)).alias(
            "learning_fork_share"
        ),
        (
            pl.col("product_text_events") / pl.col("n_events").clip(1)
        ).alias("product_text_rate"),
        (
            pl.col("other_repo_events")
            / (pl.col("own_repo_work_events") + pl.col("other_repo_events")).clip(1)
        ).alias("outward_share"),
        ((pl.col("releases") + pl.col("tags_created")) > 0)
        .cast(pl.Int8)
        .alias("ships_versions"),
        (pl.col("members_added_own_repo") > 0).cast(pl.Int8).alias("adds_team"),
    )

    cohort = pl.read_parquet(PILOT_COHORT_PATH)
    out = cohort.join(ratios, left_on="gh_login", right_on="actor_login", how="left")
    out.write_parquet(FEATURES_PATH)
    return out


def auc(frame: pl.DataFrame, feature: str) -> float:
    """Rank AUC of feature for person_type==positive (ties midranked)."""
    sub = frame.drop_nulls(feature)
    ranked = sub.with_columns(pl.col(feature).rank("average").alias("_r"))
    pos = ranked.filter(pl.col("person_type") == "positive")
    n_pos, n_neg = pos.height, ranked.height - pos.height
    if not n_pos or not n_neg:
        return float("nan")
    u = pos["_r"].sum() - n_pos * (n_pos + 1) / 2
    return u / (n_pos * n_neg)


def main() -> None:
    feats = build_features()
    print(f"actors with events: {feats.drop_nulls('n_events').height}/{feats.height}")

    strat = feats.filter(pl.col("stratum") == "stratified")
    top = feats.filter(pl.col("stratum") == "top_region")
    features = [
        "learning_repo_share",
        "learning_fork_share",
        "product_text_rate",
        "outward_share",
        "ships_versions",
        "adds_team",
        "merged_prs_external",
        "releases",
    ]
    print("\n=== founder-vs-control AUC (stratified sample | top region) ===")
    for f in features:
        print(f"{f:26s}  strat={auc(strat, f):.3f}  top={auc(top, f):.3f}")

    print("\n=== top-region means by class ===")
    print(
        top.group_by("person_type").agg(
            [pl.col(f).mean().round(3) for f in features] + [pl.len()]
        )
    )

    # Re-rank experiment: peak score penalized by learning share.
    for lam in (0.0, 0.05, 0.1, 0.2):
        rr = (
            top.drop_nulls("learning_repo_share")
            .with_columns(
                (
                    pl.col("peak")
                    - lam * pl.col("learning_repo_share")
                    - lam * pl.col("learning_fork_share")
                ).alias("adj")
            )
            .sort("adj", descending=True)
        )
        for k in (25, 50):
            prec = (rr.head(k)["person_type"] == "positive").mean()
            print(f"lambda={lam:.2f}  precision@{k}={prec:.3f}")

    portrait_crosscheck(feats)


def portrait_crosscheck(feats: pl.DataFrame) -> None:
    """Compare content features against the hand-classified FP portrait."""
    import re
    from pathlib import Path

    doc = Path("docs/exploration/false_positive_portrait.md").read_text()
    rows = re.findall(
        r"^\|\s*\d+\s*\|\s*(\S+)\s*\|[^|]+\|[^|]+\|\s*\**([A-Z]+)\**\s*\|",
        doc,
        re.MULTILINE,
    )
    portrait = pl.DataFrame(
        {"gh_login": [r[0] for r in rows], "portrait_class": [r[1] for r in rows]}
    )
    joined = portrait.join(feats, on="gh_login", how="left")
    print("\n=== FP-portrait cross-check (hand-labeled classes) ===")
    print(
        joined.group_by("portrait_class").agg(
            pl.len(),
            pl.col("learning_repo_share").mean().round(3),
            pl.col("learning_fork_share").mean().round(3),
            pl.col("product_text_rate").mean().round(4),
            pl.col("ships_versions").mean().round(2),
        )
    )
    print(
        joined.select(
            "gh_login",
            "portrait_class",
            "repos_created",
            "learning_repo_share",
            "product_text_rate",
            "ships_versions",
        ).sort("portrait_class")
    )


if __name__ == "__main__":
    main()
