"""Pod G — repo privatization/deletion as signal (wave-3 exploration).

User hypothesis: "if you want to make a product from your project, you take it
private" — repo disappearance may itself be founder signal. Wave-2 Pod D
measured 22.6% of 907 pre-cutoff-created repos now 404, class-flat overall,
but never sliced it. Three framings, strictly separated by data basis:

1. TRIAGE/LABEL-SIDE (data_basis=current_day): is current-day dead-share
   founder-enriched within slices (gestation band, main vs side repo,
   creation recency)?
2. OUTCOME-STAGE MARKER (post-cutoff GH Archive events, label use only):
   monthly event series per repo from creation to cutoff+24 months; a repo
   active pre-cutoff that goes permanently silent shortly after cutoff AND is
   404 today = privatized-while-alive candidate, with an estimated
   privatization month.
3. LEAKAGE-SAFE FEATURE probe (pre-cutoff events only): "went dark while hot"
   — own repo with >=10 events in some 3-month span that then has zero events
   in the last >=3 months before cutoff.

Playground access: Pod G only, serial, extract.py request pattern (FORMAT
Parquet), batches cached content-addressed under data/cache/privatization/.
Deterministic: sorted iteration, no sampling, no LLM calls.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import logging
import time
from collections.abc import Sequence

import httpx
import polars as pl
from scipy.stats import beta, fisher_exact

from vc_brain.ingest.contracts import DATA_ROOT
from vc_brain.ingest.sql import quote
from vc_brain.ingest.storage import atomic_write_parquet
from vc_brain.pilot.commit_depth import REPO_STATUS_PATH, SAMPLE_PATH
from vc_brain.pilot.extract import QueryTimeout, _request_parquet

LOGGER = logging.getLogger(__name__)

CACHE_DIR = DATA_ROOT / "cache" / "privatization"
MONTHLY_PATH = DATA_ROOT / "pilot" / "repo_monthly_events.parquet"
REPO_FLAGS_PATH = DATA_ROOT / "pilot" / "privatization_repo_flags.parquet"
BATCH_SIZE = 200

# Framing thresholds (fixed before looking at class splits).
HOT_EVENTS_3MO = 10  # framing 3: >=10 events in a 3-month span = "hot"
DARK_MONTHS_PRE = 3  # framing 3: zero events in last 3 months before cutoff
ACTIVE_PRE_6MO = 5  # framing 2: >=5 events in the 6 months before cutoff
SILENCE_GUARD_MONTHS = 3  # framing 2: min observed silence after last event
POST_WINDOW_MONTHS = 24

GESTATION_BANDS = ((70, 101, ">=70"), (35, 70, "35-69"), (0, 35, "<35"))

# Data basis per output column of privatization_repo_flags.parquet.
# pre_cutoff_events  -> usable as model features
# post_cutoff_events -> label/outcome use only
# current_day        -> label/triage use only (live-API 404 snapshot 2026-07-19)
COLUMN_DATA_BASIS = {
    "dead_404_current_day": "current_day",
    "n_events_post24": "post_cutoff_events",
    "any_post_cutoff_event": "post_cutoff_events",
    "last_event_rel_months": "post_cutoff_events",
    "observed_silence_months": "post_cutoff_events",
    "silent_within_6": "post_cutoff_events",
    "silent_within_12": "post_cutoff_events",
    "hot_at_death": "post_cutoff_events",
    "n_events_pre": "pre_cutoff_events",
    "active_pre6": "pre_cutoff_events",
    "went_dark_while_hot_pre": "pre_cutoff_events",
    "hot_pre": "pre_cutoff_events",
    "dark_pre3": "pre_cutoff_events",
}


def month_index(d: dt.date) -> int:
    return d.year * 12 + (d.month - 1)


def monthly_sql(repos: Sequence[str]) -> str:
    names = ", ".join(quote(r) for r in repos)
    return f"""
SELECT
    repo_name,
    toStartOfMonth(created_at) AS month,
    count() AS n_events,
    countIf(event_type = 'PushEvent') AS n_push,
    uniqExact(actor_login) AS n_actors
FROM github_events
WHERE repo_name IN ({names})
GROUP BY repo_name, month
ORDER BY repo_name, month
FORMAT Parquet
""".strip()


def fetch_batch(client: httpx.Client, repos: Sequence[str]) -> pl.DataFrame:
    sql = monthly_sql(repos)
    cache_path = CACHE_DIR / (
        hashlib.sha256(sql.encode("utf-8")).hexdigest() + ".parquet"
    )
    if cache_path.exists():
        return pl.read_parquet(cache_path)
    try:
        frame = _request_parquet(client, sql)
    except QueryTimeout:
        if len(repos) == 1:
            raise
        LOGGER.warning("bisecting batch after 408 repos=%d", len(repos))
        middle = len(repos) // 2
        return pl.concat(
            [
                fetch_batch(client, repos[:middle]),
                fetch_batch(client, repos[middle:]),
            ],
            how="diagonal_relaxed",
        )
    atomic_write_parquet(frame, cache_path)
    LOGGER.info("batch cached repos=%d rows=%d", len(repos), frame.height)
    return frame


def fetch_monthly_series() -> pl.DataFrame:
    if MONTHLY_PATH.exists():
        return pl.read_parquet(MONTHLY_PATH)
    repos = sorted(pl.read_parquet(REPO_STATUS_PATH)["repo_name"].unique())
    frames: list[pl.DataFrame] = []
    with httpx.Client(timeout=httpx.Timeout(180.0)) as client:
        for start in range(0, len(repos), BATCH_SIZE):
            batch = repos[start : start + BATCH_SIZE]
            frames.append(fetch_batch(client, batch))
            LOGGER.info("progress %d/%d repos", min(start + BATCH_SIZE, len(repos)), len(repos))
            time.sleep(0.5)
    series = pl.concat([f for f in frames if f.height], how="diagonal_relaxed")
    atomic_write_parquet(series, MONTHLY_PATH)
    return series


def exact_ci(k: int, n: int) -> tuple[float, float]:
    """Clopper-Pearson 95% interval."""
    if n == 0:
        return (0.0, 1.0)
    lo = 0.0 if k == 0 else float(beta.ppf(0.025, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(0.975, k + 1, n - k))
    return (lo, hi)


def rate_row(label: str, frame: pl.DataFrame, flag: str) -> dict:
    out: dict = {"slice": label}
    for cls, name in (("positive", "founder"), ("control", "control")):
        sub = frame.filter(pl.col("person_type") == cls)
        k = int(sub[flag].sum()) if sub.height else 0
        n = sub.height
        lo, hi = exact_ci(k, n)
        out[f"{name}"] = f"{k}/{n} = {k / n:.1%} [{lo:.1%}-{hi:.1%}]" if n else "0/0"
        out[f"_{name}_k"], out[f"_{name}_n"] = k, n
    fk, fn = out["_founder_k"], out["_founder_n"]
    ck, cn = out["_control_k"], out["_control_n"]
    if fn and cn:
        odds, p = fisher_exact([[fk, fn - fk], [ck, cn - ck]])
        out["fisher_p"] = f"{p:.3f}"
    return out


def print_rate_table(title: str, rows: list[dict]) -> None:
    print(f"\n### {title}")
    for r in rows:
        print(
            f"  {r['slice']:<38s} founders {r['founder']:<28s} "
            f"controls {r['control']:<28s} p={r.get('fisher_p', '-')}"
        )


def build_repo_table() -> pl.DataFrame:
    """One row per sampled repo: sample metadata + status + derived slices."""
    sample = pl.read_parquet(SAMPLE_PATH)
    status = pl.read_parquet(REPO_STATUS_PATH)
    repos = status.join(
        sample.select(
            "gh_login", "person_type", "t_cutoff", "gestation_likelihood", "peak"
        ),
        left_on="actor_login",
        right_on="gh_login",
        how="left",
    )
    band = pl.lit(None, dtype=pl.String)
    for lo, hi, label in GESTATION_BANDS:
        band = (
            pl.when((pl.col("gestation_likelihood") >= lo) & (pl.col("gestation_likelihood") < hi))
            .then(pl.lit(label))
            .otherwise(band)
        )
    repos = repos.with_columns(
        band.alias("gband"),
        pl.col("status").eq("deleted_404").alias("dead"),
        (
            (
                pl.col("t_cutoff").cast(pl.Datetime("us", "UTC")) - pl.col("repo_created_at")
            ).dt.total_days()
            / 30.44
        ).alias("age_at_cutoff_months"),
        (
            pl.col("n_repo_events")
            == pl.col("n_repo_events").max().over("actor_login")
        ).alias("_is_max"),
    )
    # main repo = highest text-event count, ties broken by repo_name asc
    main = (
        repos.sort(["actor_login", "n_repo_events", "repo_name"], descending=[False, True, False])
        .group_by("actor_login", maintain_order=True)
        .agg(pl.col("repo_name").first().alias("_main_repo"))
    )
    return repos.join(main, on="actor_login", how="left").with_columns(
        (pl.col("repo_name") == pl.col("_main_repo")).alias("is_main_repo")
    ).drop("_is_max", "_main_repo")


def framing1_triage(repos: pl.DataFrame) -> None:
    print("\n## FRAMING 1 — TRIAGE/LABEL-SIDE (data_basis=current_day 404)")
    rows = [rate_row("overall", repos, "dead")]
    for _, _, label in GESTATION_BANDS:
        rows.append(rate_row(f"gestation {label}", repos.filter(pl.col("gband") == label), "dead"))
    print_rate_table("dead-share by gestation band", rows)

    rows = [
        rate_row("main repo", repos.filter(pl.col("is_main_repo")), "dead"),
        rate_row("side repos", repos.filter(~pl.col("is_main_repo")), "dead"),
    ]
    print_rate_table("dead-share main vs side repo", rows)

    recency = [
        ("created <6mo before cutoff", pl.col("age_at_cutoff_months") < 6),
        ("created 6-12mo before cutoff", (pl.col("age_at_cutoff_months") >= 6) & (pl.col("age_at_cutoff_months") < 12)),
        ("created <12mo before cutoff", pl.col("age_at_cutoff_months") < 12),
        ("created >=12mo before cutoff", pl.col("age_at_cutoff_months") >= 12),
    ]
    rows = [rate_row(label, repos.filter(cond), "dead") for label, cond in recency]
    print_rate_table("dead-share by repo creation recency", rows)

    rows = [
        rate_row(
            "gestation>=70 AND created<12mo",
            repos.filter((pl.col("gband") == ">=70") & (pl.col("age_at_cutoff_months") < 12)),
            "dead",
        ),
        rate_row(
            "gestation>=70 AND created<6mo",
            repos.filter((pl.col("gband") == ">=70") & (pl.col("age_at_cutoff_months") < 6)),
            "dead",
        ),
        rate_row(
            "gestation>=70 AND main repo",
            repos.filter((pl.col("gband") == ">=70") & pl.col("is_main_repo")),
            "dead",
        ),
        rate_row(
            "g>=70 AND main AND created<12mo",
            repos.filter(
                (pl.col("gband") == ">=70")
                & pl.col("is_main_repo")
                & (pl.col("age_at_cutoff_months") < 12)
            ),
            "dead",
        ),
    ]
    print_rate_table("user-hypothesis cells (gestation x recency x main)", rows)


def build_repo_flags(repos: pl.DataFrame, series: pl.DataFrame) -> pl.DataFrame:
    """Per-repo timeline flags from the monthly series (framings 2 and 3)."""
    horizon_idx = month_index(series["month"].max().date() if hasattr(series["month"].max(), "date") else series["month"].max())
    LOGGER.info("data horizon month index=%d", horizon_idx)
    series = series.with_columns(
        pl.col("month").dt.year().mul(12).add(pl.col("month").dt.month() - 1).alias("midx")
    )
    out_rows: list[dict] = []
    grouped = {
        name: grp for (name,), grp in series.group_by("repo_name")
    }
    for row in repos.sort(["actor_login", "repo_name"]).iter_rows(named=True):
        repo = row["repo_name"]
        cutoff_idx = month_index(row["t_cutoff"])
        grp = grouped.get(repo)
        months: dict[int, int] = {}
        if grp is not None:
            months = dict(zip(grp["midx"].to_list(), grp["n_events"].to_list()))
        pre = {m: v for m, v in months.items() if m < cutoff_idx}
        post_end = min(cutoff_idx + POST_WINDOW_MONTHS, horizon_idx)
        post = {m: v for m, v in months.items() if cutoff_idx <= m <= post_end}

        # framing 3 (pre-cutoff only): hot 3-month span, then dark last 3 months
        hot = False
        if pre:
            lo, hi = min(pre), max(pre)
            for start in range(lo, hi + 1):
                if sum(pre.get(start + i, 0) for i in range(3)) >= HOT_EVENTS_3MO:
                    hot = True
                    break
        dark_pre = all(
            pre.get(cutoff_idx - 1 - i, 0) == 0 for i in range(DARK_MONTHS_PRE)
        )
        went_dark_while_hot = hot and dark_pre

        # framing 2 (post-cutoff, label-side)
        active_pre6 = sum(pre.get(cutoff_idx - 1 - i, 0) for i in range(6)) >= ACTIVE_PRE_6MO
        last_event_idx = max(months) if months else None
        last_rel = None if last_event_idx is None else last_event_idx - cutoff_idx
        observed_silence = (
            None if last_event_idx is None else horizon_idx - last_event_idx
        )
        # silence is only claimable if we can observe >=SILENCE_GUARD months after it
        silent_within_6 = (
            last_event_idx is not None
            and last_rel < 6
            and observed_silence >= SILENCE_GUARD_MONTHS
        )
        silent_within_12 = (
            last_event_idx is not None
            and last_rel < 12
            and observed_silence >= SILENCE_GUARD_MONTHS
        )
        # hot at death: >=HOT_EVENTS_3MO events in the 3 months up to and
        # including the last event month (distinguishes privatized-while-alive
        # from long-tail abandonment)
        hot_at_death = last_event_idx is not None and (
            sum(months.get(last_event_idx - i, 0) for i in range(3)) >= HOT_EVENTS_3MO
        )
        any_post = bool(post) and sum(post.values()) > 0
        out_rows.append(
            {
                "actor_login": row["actor_login"],
                "repo_name": repo,
                "person_type": row["person_type"],
                "gband": row["gband"],
                "gestation_likelihood": row["gestation_likelihood"],
                "is_main_repo": row["is_main_repo"],
                "age_at_cutoff_months": row["age_at_cutoff_months"],
                "dead_404_current_day": row["dead"],
                "n_events_total": sum(months.values()),
                "n_events_pre": sum(pre.values()),
                "n_events_post24": sum(post.values()),
                "any_post_cutoff_event": any_post,
                "active_pre6": active_pre6,
                "last_event_rel_months": last_rel,
                "observed_silence_months": observed_silence,
                "silent_within_6": silent_within_6,
                "silent_within_12": silent_within_12,
                "hot_at_death": hot_at_death,
                "went_dark_while_hot_pre": went_dark_while_hot,
                "hot_pre": hot,
                "dark_pre3": dark_pre,
            }
        )
    flags = pl.DataFrame(out_rows)
    atomic_write_parquet(flags, REPO_FLAGS_PATH)
    return flags


def framing2_outcome(flags: pl.DataFrame) -> None:
    print("\n## FRAMING 2 — OUTCOME-STAGE MARKER (post-cutoff GH Archive, label use only)")
    flags = flags.with_columns(
        (pl.col("active_pre6") & pl.col("silent_within_6") & pl.col("dead_404_current_day")).alias("priv6"),
        (pl.col("active_pre6") & pl.col("silent_within_12") & pl.col("dead_404_current_day")).alias("priv12"),
        (
            pl.col("active_pre6")
            & pl.col("silent_within_12")
            & pl.col("dead_404_current_day")
            & pl.col("hot_at_death")
        ).alias("priv12_hot"),
    )
    print(f"repos active pre-cutoff (>= {ACTIVE_PRE_6MO} events in last 6mo): "
          f"{flags.filter(pl.col('active_pre6')).height}/{flags.height}")
    rows = [
        rate_row("privatized-candidate (silent<6mo,404)", flags, "priv6"),
        rate_row("privatized-candidate (silent<12mo,404)", flags, "priv12"),
        rate_row("  ... AND hot at death", flags, "priv12_hot"),
    ]
    print_rate_table("privatized-while-alive candidates (repo level, all repos)", rows)
    act = flags.filter(pl.col("active_pre6"))
    rows = [
        rate_row("silent<6mo AND 404 | active-pre", act, "priv6"),
        rate_row("silent<12mo AND 404 | active-pre", act, "priv12"),
        rate_row("  ... AND hot at death", act, "priv12_hot"),
    ]
    print_rate_table("same, conditioned on active-pre repos", rows)

    # actor level: any privatized-candidate repo
    actor = flags.group_by("actor_login", "person_type").agg(
        pl.col("priv12").any().alias("any_priv12"),
        pl.col("priv12_hot").any().alias("any_priv12_hot"),
    )
    rows = [
        rate_row("actor has >=1 candidate (12mo)", actor, "any_priv12"),
        rate_row("actor has >=1 hot candidate", actor, "any_priv12_hot"),
    ]
    print_rate_table("actor level", rows)

    # timing of death for 404 repos
    dead = flags.filter(pl.col("dead_404_current_day") & pl.col("last_event_rel_months").is_not_null())
    print("\n### last-event month relative to cutoff, 404 repos only")
    for cls in ("positive", "control"):
        sub = dead.filter(pl.col("person_type") == cls)["last_event_rel_months"]
        if sub.len():
            print(
                f"  {cls:<9s} n={sub.len():3d} median={sub.median():+.0f}mo "
                f"p25={sub.quantile(0.25):+.0f} p75={sub.quantile(0.75):+.0f} "
                f"share post-cutoff={float((sub >= 0).mean()):.1%}"
            )
    print("\n### estimated privatization month (candidates, silent<12mo, active-pre)")
    cand = flags.filter(
        pl.col("active_pre6") & pl.col("silent_within_12") & pl.col("dead_404_current_day")
    ).sort(["person_type", "actor_login", "repo_name"])
    with pl.Config(tbl_rows=40, fmt_str_lengths=50):
        print(
            cand.select(
                "person_type",
                "actor_login",
                "repo_name",
                "gband",
                "is_main_repo",
                "n_events_pre",
                "last_event_rel_months",
                "hot_at_death",
            )
        )


def framing3_feature(flags: pl.DataFrame) -> None:
    print("\n## FRAMING 3 — LEAKAGE-SAFE FEATURE PROBE (pre-cutoff events only)")
    rows = [
        rate_row("hot pre-cutoff (>=10 ev/3mo)", flags, "hot_pre"),
        rate_row("went dark while hot", flags, "went_dark_while_hot_pre"),
    ]
    print_rate_table("repo level", rows)
    actor = flags.group_by("actor_login", "person_type").agg(
        pl.col("went_dark_while_hot_pre").any().alias("any_dark_hot"),
        pl.col("gestation_likelihood").first(),
    )
    rows = [rate_row("actor has >=1 dark-while-hot repo", actor, "any_dark_hot")]
    print_rate_table("actor level", rows)

    print("\n### gestation among actors with/without the flag")
    for flag_val in (True, False):
        sub = actor.filter(pl.col("any_dark_hot") == flag_val)["gestation_likelihood"]
        print(f"  flag={flag_val}: n={sub.len()} median gestation={sub.median()}")

    print("\n### what the flag actually proxies (current-day/post-cutoff DIAGNOSIS ONLY, data_basis=current_day)")
    dark = flags.filter(pl.col("went_dark_while_hot_pre"))
    if dark.height:
        print(
            dark.group_by("dead_404_current_day", "any_post_cutoff_event")
            .len()
            .sort(["dead_404_current_day", "any_post_cutoff_event"])
        )
        share_dead = float(dark["dead_404_current_day"].mean())
        resumed = float(dark["any_post_cutoff_event"].mean())
        print(f"  dark-while-hot repos: {dark.height}; 404 today {share_dead:.1%}; "
              f"had post-cutoff events (resumed) {resumed:.1%}")
        base = flags.filter(~pl.col("went_dark_while_hot_pre"))
        print(f"  baseline 404 share (non-flagged repos): {float(base['dead_404_current_day'].mean()):.1%}")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    repos = build_repo_table()
    print(f"repo table: {repos.height} repos, {repos['actor_login'].n_unique()} actors")
    framing1_triage(repos)
    series = fetch_monthly_series()
    print(
        f"\nmonthly series: {series.height:,} repo-months, "
        f"{series['repo_name'].n_unique()}/{repos.height} repos with >=1 event row, "
        f"horizon={series['month'].max()}"
    )
    flags = build_repo_flags(repos, series)
    framing2_outcome(flags)
    framing3_feature(flags)


if __name__ == "__main__":
    main()
