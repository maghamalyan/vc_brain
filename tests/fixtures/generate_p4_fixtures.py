"""Regenerate the intentionally synthetic P4 parquet contract fixtures."""

from datetime import date, datetime
from pathlib import Path

import polars as pl


ROOT = Path(__file__).parent / "p4_data"


def add_months(value: date, months: int) -> date:
    total = value.year * 12 + value.month - 1 + months
    year, zero_month = divmod(total, 12)
    return date(year, zero_month + 1, 1)


def write(frame: pl.DataFrame, relative: str) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.write_parquet(path)


def main() -> None:
    cohorts = (("train", 2022), ("valid", 2023), ("test", 2024))
    labels: list[dict[str, object]] = []
    positives: list[tuple[str, date, int]] = []
    for prefix, batch_year in cohorts:
        for index in range(1, 5):
            batch_start = date(batch_year, (3, 6, 9, 12)[index - 1], 1)
            login = (
                f"{prefix}_p{index}"
                if not (prefix == "test" and index == 4)
                else "test_p4_zero"
            )
            positives.append((login, batch_start, index))
            labels.append(
                {
                    "founder_name": f"Synthetic {prefix.title()} Founder {index}",
                    "company": f"Synthetic {prefix.title()} Company {index}",
                    "batch_start_date": batch_start,
                    "t_cutoff": add_months(batch_start, -12),
                    "gh_login": login,
                    "gh_confidence": 0.95,
                }
            )
    labels.append(
        {
            "founder_name": "Excluded Founder (fixture)",
            "company": "Excluded Fixture Co",
            "batch_start_date": date(2024, 3, 1),
            "t_cutoff": date(2023, 3, 1),
            "gh_login": "excluded_low_confidence",
            "gh_confidence": 0.49,
        }
    )
    write(pl.DataFrame(labels), "labels/founders.parquet")

    event_types = (
        "PushEvent",
        "CreateEvent",
        "PullRequestEvent",
        "PullRequestReviewEvent",
        "PullRequestReviewCommentEvent",
        "IssuesEvent",
        "IssueCommentEvent",
        "CommitCommentEvent",
        "WatchEvent",
        "ForkEvent",
    )
    baseline_rows: list[dict[str, object]] = []
    month = date(2017, 1, 1)
    while month <= date(2024, 1, 1):
        baseline_rows.extend(
            {"month": month, "event_type": event_type, "event_count": 1_000}
            for event_type in event_types
        )
        month = add_months(month, 1)
    write(pl.DataFrame(baseline_rows), "events/baselines/monthly_totals.parquet")

    positive_monthly: list[dict[str, object]] = []
    negative_monthly: list[dict[str, object]] = []
    owned_positive: list[dict[str, object]] = []
    owned_negative: list[dict[str, object]] = []
    repos_positive: list[dict[str, object]] = []
    repos_negative: list[dict[str, object]] = []
    matches: list[dict[str, object]] = []
    activity_events = event_types[:-1]
    traction_events = ("WatchEvent", "ForkEvent", "IssuesEvent")

    for login, batch_start, index in positives:
        cutoff = add_months(batch_start, -12)
        if login == "test_p4_zero":
            positive_monthly.append(
                {
                    "actor_login": login,
                    "month": add_months(cutoff, -1),
                    "event_type": "__NO_ACTIVITY__",
                    "is_weekend": False,
                    "event_count": 0,
                    "t_cutoff": cutoff,
                    "cohort": "positives",
                    "no_gh_activity": True,
                }
            )
        else:
            for position, offset in enumerate((-30, -20, -17, -15, -14, -13)):
                for event_index, event_type in enumerate(activity_events):
                    count = (position + 1) * (event_index + 1) + index
                    positive_monthly.append(
                        {
                            "actor_login": login,
                            "month": add_months(batch_start, offset),
                            "event_type": event_type,
                            "is_weekend": (position + event_index + index) % 3 == 0,
                            "event_count": count,
                            "t_cutoff": cutoff,
                            "cohort": "positives",
                            "no_gh_activity": False,
                        }
                    )
            for traction_index, event_type in enumerate(traction_events):
                for position, offset in enumerate((-24, -15, -14, -13)):
                    owned_positive.append(
                        {
                            "owner_login": login,
                            "month": add_months(batch_start, offset),
                            "event_type": event_type,
                            "event_count": (position + 1) * (traction_index + 2)
                            + index,
                            "t_cutoff": cutoff,
                            "cohort": "positives",
                        }
                    )
            for repo_index, offset in enumerate((-36, -24, -14, -13)):
                repos_positive.append(
                    {
                        "actor_login": login,
                        "created_at": datetime.combine(
                            add_months(batch_start, offset), datetime.min.time()
                        ).replace(day=10),
                        "repo_name": f"{login}/fixture-repo-{repo_index}",
                        "t_cutoff": cutoff,
                        "cohort": "positives",
                    }
                )

        for control_index in range(1, 6):
            control = f"{login}_control{control_index}"
            matches.append(
                {
                    "actor_login": control,
                    "t_cutoff": cutoff,
                    "matched_positive_login": login,
                    "positive_total_events": 100,
                    "total_events": 80 + control_index,
                    "first_seen_year": batch_start.year - 5,
                    "actor_hash": index * 100 + control_index,
                    "match_rank": control_index,
                }
            )
            if control_index == 2 and login == "train_p4":
                negative_monthly.append(
                    {
                        "actor_login": control,
                        "month": add_months(cutoff, -1),
                        "event_type": "__NO_ACTIVITY__",
                        "is_weekend": False,
                        "event_count": 0,
                        "t_cutoff": cutoff,
                        "cohort": "negatives",
                        "no_gh_activity": True,
                    }
                )
            else:
                for event_index, event_type in enumerate(activity_events):
                    negative_monthly.append(
                        {
                            "actor_login": control,
                            "month": add_months(batch_start, -28 + control_index),
                            "event_type": event_type,
                            "is_weekend": event_index == 0 and control_index == 2,
                            "event_count": 1 + (event_index % 2),
                            "t_cutoff": cutoff,
                            "cohort": "negatives",
                            "no_gh_activity": False,
                        }
                    )
                for event_type in traction_events:
                    owned_negative.append(
                        {
                            "owner_login": control,
                            "month": add_months(batch_start, -27),
                            "event_type": event_type,
                            "event_count": 1,
                            "t_cutoff": cutoff,
                            "cohort": "negatives",
                        }
                    )
                repos_negative.append(
                    {
                        "actor_login": control,
                        "created_at": datetime.combine(
                            add_months(batch_start, -30), datetime.min.time()
                        ).replace(day=5),
                        "repo_name": f"{control}/fixture-repo",
                        "t_cutoff": cutoff,
                        "cohort": "negatives",
                    }
                )

    # This aggregate row exists deliberately; confidence filtering must exclude it.
    positive_monthly.append(
        {
            "actor_login": "excluded_low_confidence",
            "month": date(2023, 2, 1),
            "event_type": "PushEvent",
            "is_weekend": False,
            "event_count": 999,
            "t_cutoff": date(2023, 3, 1),
            "cohort": "positives",
            "no_gh_activity": False,
        }
    )
    write(pl.DataFrame(positive_monthly), "events/monthly_agg/positives.parquet")
    write(pl.DataFrame(negative_monthly), "events/monthly_agg/negatives.parquet")
    write(pl.DataFrame(owned_positive), "events/owned_repo_agg/positives.parquet")
    write(pl.DataFrame(owned_negative), "events/owned_repo_agg/negatives.parquet")
    write(pl.DataFrame(repos_positive), "events/repo_creations/positives.parquet")
    write(pl.DataFrame(repos_negative), "events/repo_creations/negatives.parquet")
    write(pl.DataFrame(matches), "events/negatives/matched.parquet")


if __name__ == "__main__":
    main()
