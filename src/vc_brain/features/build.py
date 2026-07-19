"""Build the leakage-safe discrete-time founder hazard panel."""

import json
import math
import os
import tempfile
from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path

import polars as pl

from vc_brain.features.taxonomy import capital_families, capital_family

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = Path(os.environ.get("VC_BRAIN_DATA_DIR", PROJECT_ROOT / "data"))
EVENTS_ROOT = DATA_ROOT / "events"
LABELS_PATH = DATA_ROOT / "labels" / "founders.parquet"
PANEL_PATH = DATA_ROOT / "features" / "panel.parquet"
DATA_CARD_JSON_PATH = DATA_ROOT / "features" / "data_card.json"
DATA_CARD_MD_PATH = DATA_ROOT / "features" / "data_card.md"

CONFIDENCE_THRESHOLD = 0.5
PER_MILLION = 1_000_000.0
NO_REPO_SENTINEL_MONTHS = 49.0

ACTIVITY_CLASSES: dict[str, tuple[str, ...]] = {
    "push": ("PushEvent",),
    "create": ("CreateEvent",),
    "pr": ("PullRequestEvent",),
    "pr_review": ("PullRequestReviewEvent", "PullRequestReviewCommentEvent"),
    "issue": ("IssuesEvent",),
    "comment": ("IssueCommentEvent", "CommitCommentEvent"),
    "watch_given": ("WatchEvent",),
}
TRACTION_CLASSES: dict[str, tuple[str, ...]] = {
    "stars": ("WatchEvent",),
    "forks": ("ForkEvent",),
    "issues_by_others": ("IssuesEvent",),
}

METADATA_COLUMNS = (
    "gh_login",
    "founder_name",
    "company",
    "month",
    "batch_start_date",
    "gestation_start",
    "t_cutoff",
    "person_type",
    "matched_positive_login",
    "match_group_id",
    "y",
)


@dataclass(frozen=True)
class FeatureDefinition:
    name: str
    block: str
    definition: str
    null_policy: str = "Never null; absent activity is zero."


def add_months(value: date, months: int) -> date:
    """Return the first day of the month ``months`` away from ``value``."""
    total = value.year * 12 + value.month - 1 + months
    year, zero_month = divmod(total, 12)
    return date(year, zero_month + 1, 1)


def month_distance(later: date, earlier: date) -> int:
    return (later.year - earlier.year) * 12 + later.month - earlier.month


def panel_months(batch_start: date) -> list[date]:
    return [add_months(batch_start, offset) for offset in range(-48, -11)]


def hazard_label(batch_start: date, month: date) -> int:
    return int(add_months(batch_start, -15) <= month <= add_months(batch_start, -12))


def _atomic_write_parquet(frame: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, suffix=".parquet.tmp")
    os.close(descriptor)
    try:
        frame.write_parquet(temporary)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def _atomic_write_text(value: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, suffix=".txt.tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def _read_parquet_collection(path: Path, *, required: bool = True) -> pl.DataFrame:
    if path.is_dir():
        canonical = [path / "positives.parquet", path / "negatives.parquet"]
        if any(candidate.exists() for candidate in canonical):
            missing = [candidate for candidate in canonical if not candidate.exists()]
            if missing and required:
                raise FileNotFoundError(
                    f"Missing required positive/negative parquet inputs: {missing}"
                )
            files = [candidate for candidate in canonical if candidate.exists()]
        else:
            files = sorted(path.glob("*.parquet"))
    else:
        files = [path] if path.exists() else []
    if not files:
        if required:
            raise FileNotFoundError(f"Missing required parquet input: {path}")
        return pl.DataFrame()
    return pl.concat([pl.read_parquet(file) for file in files], how="diagonal_relaxed")


def _validate_columns(frame: pl.DataFrame, required: set[str], source: Path) -> None:
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{source} is missing required columns: {sorted(missing)}")


def _validate_non_null(frame: pl.DataFrame, columns: set[str], source: Path) -> None:
    null_counts = frame.select(pl.col(column).null_count() for column in columns).row(
        0, named=True
    )
    invalid = {column: count for column, count in null_counts.items() if count}
    if invalid:
        raise ValueError(f"{source} has nulls in required values: {invalid}")


def _validate_counts(
    frame: pl.DataFrame,
    *,
    count_column: str,
    source: Path,
    strictly_positive: bool = False,
) -> None:
    _validate_non_null(frame, {count_column}, source)
    invalid = (
        pl.col(count_column) <= 0 if strictly_positive else pl.col(count_column) < 0
    )
    if not frame.filter(invalid).is_empty():
        constraint = "positive" if strictly_positive else "non-negative"
        raise ValueError(f"{source} requires {constraint} {count_column} values")


def _month_value(value: object) -> date:
    if isinstance(value, datetime):
        return date(value.year, value.month, 1)
    if isinstance(value, date):
        return value.replace(day=1)
    raise TypeError(f"Expected date-like month, got {type(value).__name__}")


def _positive_records(
    labels: pl.DataFrame, positive_logins: set[str]
) -> dict[str, dict[str, object]]:
    eligible = labels.filter(
        pl.col("gh_login").is_not_null()
        & (pl.col("gh_login").str.strip_chars() != "")
        & (pl.col("gh_confidence") >= CONFIDENCE_THRESHOLD)
        & pl.col("batch_start_date").is_not_null()
    ).with_columns(pl.col("gh_login").str.to_lowercase())
    records: dict[str, dict[str, object]] = {}
    for row in eligible.sort("batch_start_date", "gh_login").to_dicts():
        login = str(row["gh_login"])
        if login in positive_logins and login not in records:
            records[login] = row
    return records


def _assert_source_before_cutoff(
    frame: pl.DataFrame,
    *,
    actor_column: str,
    time_column: str,
    source_name: str,
) -> None:
    if frame.is_empty():
        return
    invalid = frame.filter(pl.col(time_column).cast(pl.Date) >= pl.col("t_cutoff"))
    if not invalid.is_empty():
        example = invalid.select(actor_column, time_column, "t_cutoff").row(
            0, named=True
        )
        raise ValueError(f"Temporal leakage in {source_name}: {example}")


def _assert_expected_cutoffs(
    frame: pl.DataFrame,
    *,
    actor_column: str,
    expected: Mapping[str, date],
    source_name: str,
) -> None:
    for row in frame.select(actor_column, "t_cutoff").unique().to_dicts():
        login = str(row[actor_column]).lower()
        if login in expected and _month_value(row["t_cutoff"]) != expected[login]:
            raise ValueError(
                f"{source_name} cutoff for {login!r} does not equal B-12 months"
            )


def _sum_window(values: Mapping[date, float], month: date, months: int) -> float:
    return sum(
        values.get(add_months(month, offset), 0.0) for offset in range(-(months - 1), 1)
    )


def _mean_window(
    values: Mapping[date, float], month: date, start: int, stop: int
) -> float:
    offsets = range(start, stop + 1)
    points = [values.get(add_months(month, offset), 0.0) for offset in offsets]
    return sum(points) / len(points)


def _ratio_delta(values: Mapping[date, float], month: date) -> tuple[float, float]:
    recent = _mean_window(values, month, -2, 0)
    prior = _mean_window(values, month, -14, -3)
    return (recent + 1.0) / (prior + 1.0), recent - prior


def _burst_z(values: Mapping[date, float], month: date) -> float:
    recent = _mean_window(values, month, -2, 0)
    prior_points = [
        values.get(add_months(month, offset), 0.0) for offset in range(-14, -2)
    ]
    prior_mean = sum(prior_points) / len(prior_points)
    variance = sum((point - prior_mean) ** 2 for point in prior_points) / len(
        prior_points
    )
    return (recent - prior_mean) / math.sqrt(variance) if variance > 0 else 0.0


def _gini(values: Iterable[float]) -> float:
    points = sorted(float(value) for value in values)
    if not points or sum(points) == 0:
        return 0.0
    n = len(points)
    weighted = sum((index + 1) * value for index, value in enumerate(points))
    return (2.0 * weighted) / (n * sum(points)) - (n + 1.0) / n


def feature_definitions() -> list[FeatureDefinition]:
    definitions: list[FeatureDefinition] = []
    for event_class in ACTIVITY_CLASSES:
        for window in (1, 3, 6, 12):
            definitions.append(
                FeatureDefinition(
                    f"activity_{event_class}_{window}m",
                    "levels",
                    f"Trailing {window}-month {event_class} activity, summed after each month is normalized per million global events in the mapped GitHub event class.",
                )
            )
        definitions.extend(
            [
                FeatureDefinition(
                    f"activity_{event_class}_ratio_3m_prior12m",
                    "dynamics",
                    f"Smoothed ratio (recent 3-month mean + 1) / (preceding 12-month mean + 1) for normalized {event_class} activity.",
                ),
                FeatureDefinition(
                    f"activity_{event_class}_delta_3m_prior12m",
                    "dynamics",
                    f"Recent 3-month mean minus preceding 12-month mean for normalized {event_class} activity.",
                ),
            ]
        )
    definitions.extend(
        [
            FeatureDefinition(
                "burst_push_zscore",
                "dynamics",
                "Z-score of the recent 3-month mean normalized push activity against the preceding 12 monthly values; zero when prior variance is zero.",
            ),
            FeatureDefinition(
                "burst_create_zscore",
                "dynamics",
                "Z-score of the recent 3-month mean normalized create activity against the preceding 12 monthly values; zero when prior variance is zero.",
            ),
        ]
    )
    for window in (3, 6, 12):
        definitions.append(
            FeatureDefinition(
                f"new_repos_{window}m",
                "levels",
                f"Repository CreateEvents in the trailing {window} months.",
            )
        )
    definitions.extend(
        [
            FeatureDefinition(
                "months_since_last_new_repo",
                "dynamics",
                "Whole calendar months since the latest repository creation on or before the panel month.",
                f"{NO_REPO_SENTINEL_MONTHS:g} when no repository creation has been observed in the extracted history.",
            ),
            FeatureDefinition(
                "cumulative_repos",
                "levels",
                "Cumulative repository creations observed through the panel month.",
            ),
        ]
    )
    for traction_class in TRACTION_CLASSES:
        for window in (3, 12):
            definitions.append(
                FeatureDefinition(
                    f"traction_{traction_class}_{window}m",
                    "traction",
                    f"Trailing {window}-month {traction_class} received on owned repositories, normalized per million same-class global events each month.",
                )
            )
        definitions.extend(
            [
                FeatureDefinition(
                    f"traction_{traction_class}_ratio_3m_prior12m",
                    "traction",
                    f"Smoothed recent-3 versus preceding-12 monthly mean ratio for {traction_class} received.",
                ),
                FeatureDefinition(
                    f"traction_{traction_class}_delta_3m_prior12m",
                    "traction",
                    f"Recent-3 minus preceding-12 monthly mean for {traction_class} received.",
                ),
            ]
        )
    definitions.extend(
        [
            FeatureDefinition(
                "weekend_share_3m",
                "levels",
                "Weekend event count divided by all mapped activity in the trailing 3 months.",
            ),
            FeatureDefinition(
                "weekend_share_prior12m",
                "levels",
                "Weekend event count divided by all mapped activity in the 12 months preceding the recent 3-month window.",
            ),
            FeatureDefinition(
                "weekend_share_delta",
                "dynamics",
                "Recent 3-month weekend share minus the preceding 12-month weekend share.",
            ),
            FeatureDefinition(
                "tenure_months",
                "levels",
                "Calendar months since the first observed non-sentinel activity event, inclusive.",
            ),
            FeatureDefinition(
                "activity_gini",
                "levels",
                "Gini coefficient of raw mapped activity counts across observed history months through the panel month.",
            ),
            FeatureDefinition(
                "no_gh_activity",
                "levels",
                "One when the person has no non-sentinel GitHub activity in the extracted window.",
            ),
            FeatureDefinition(
                "own_repo_share_3m",
                "ownership_collab",
                "Share of the actor's trailing 3-month events occurring on repositories whose owner login equals the actor login.",
            ),
            FeatureDefinition(
                "own_repo_share_delta_3m_prior12m",
                "ownership_collab",
                "Trailing 3-month own-repository event share minus the share in the preceding 12 months.",
            ),
            FeatureDefinition(
                "distinct_collaborators_3m",
                "ownership_collab",
                "Sum of monthly distinct non-bot collaborators observed on the actor's repositories over the trailing 3 months.",
            ),
            FeatureDefinition(
                "distinct_collaborators_delta_3m_prior12m",
                "ownership_collab",
                "Recent 3-month mean monthly collaborator count minus the preceding 12-month mean.",
            ),
            FeatureDefinition(
                "new_collaborator_burst_zscore",
                "ownership_collab",
                "Z-score of the recent 3-month mean monthly collaborator count against the preceding 12 monthly values; zero when prior variance is zero.",
            ),
            FeatureDefinition(
                "context_divergence_2q",
                "semantics",
                "One minus cosine similarity between the actor's event-type distribution plus own-repository share in the trailing six months and the same composition over all earlier cached history.",
                "Null when fewer than six calendar months of prior cached history exist or either composition vector has zero magnitude; model matrices neutral-impute this documented null to zero.",
            ),
        ]
    )
    return definitions


def _activity_maps(
    monthly: pl.DataFrame,
    baselines: pl.DataFrame,
) -> tuple[
    dict[tuple[str, str], dict[date, float]],
    dict[str, dict[date, float]],
    dict[str, dict[date, float]],
]:
    event_to_classes = {
        event: event_class
        for event_class, events in ACTIVITY_CLASSES.items()
        for event in events
    }
    baseline_raw: dict[tuple[date, str], float] = defaultdict(float)
    for row in baselines.to_dicts():
        event = str(row["event_type"])
        if event in event_to_classes:
            baseline_raw[(_month_value(row["month"]), event_to_classes[event])] += (
                float(row["event_count"])
            )

    monthly_raw: dict[tuple[str, date, str], float] = defaultdict(float)
    weekend: dict[str, dict[date, float]] = defaultdict(lambda: defaultdict(float))
    total: dict[str, dict[date, float]] = defaultdict(lambda: defaultdict(float))
    for row in monthly.to_dicts():
        event = str(row["event_type"])
        if event not in event_to_classes:
            continue
        if row["event_count"] == 0:
            continue
        login = str(row["actor_login"]).lower()
        month = _month_value(row["month"])
        count = float(row["event_count"])
        event_class = event_to_classes[event]
        monthly_raw[(login, month, event_class)] += count
        total[login][month] += count
        if bool(row["is_weekend"]):
            weekend[login][month] += count

    normalized: dict[tuple[str, str], dict[date, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    for (login, month, event_class), count in monthly_raw.items():
        denominator = baseline_raw.get((month, event_class), 0.0)
        if denominator <= 0:
            raise ValueError(
                f"Missing positive global baseline for {event_class} in {month}"
            )
        normalized[(login, event_class)][month] = count / denominator * PER_MILLION
    return normalized, weekend, total


def _traction_maps(
    owned: pl.DataFrame, baselines: pl.DataFrame
) -> dict[tuple[str, str], dict[date, float]]:
    event_to_class = {
        event: name for name, events in TRACTION_CLASSES.items() for event in events
    }
    baseline_raw: dict[tuple[date, str], float] = defaultdict(float)
    for row in baselines.to_dicts():
        event = str(row["event_type"])
        if event in event_to_class:
            baseline_raw[(_month_value(row["month"]), event_to_class[event])] += float(
                row["event_count"]
            )
    received_raw: dict[tuple[str, date, str], float] = defaultdict(float)
    for row in owned.to_dicts():
        event = str(row["event_type"])
        if event in event_to_class:
            received_raw[
                (
                    str(row["owner_login"]).lower(),
                    _month_value(row["month"]),
                    event_to_class[event],
                )
            ] += float(row["event_count"])
    normalized: dict[tuple[str, str], dict[date, float]] = defaultdict(
        lambda: defaultdict(float)
    )
    for (login, month, traction_class), count in received_raw.items():
        denominator = baseline_raw.get((month, traction_class), 0.0)
        if denominator <= 0:
            raise ValueError(
                f"Missing positive global baseline for traction {traction_class} in {month}"
            )
        normalized[(login, traction_class)][month] = count / denominator * PER_MILLION
    return normalized


def _repo_maps(creations: pl.DataFrame) -> dict[str, dict[date, float]]:
    result: dict[str, dict[date, float]] = defaultdict(lambda: defaultdict(float))
    for row in creations.to_dicts():
        result[str(row["actor_login"]).lower()][_month_value(row["created_at"])] += 1.0
    return result


def _ownership_maps(
    ownership: pl.DataFrame,
) -> tuple[dict[str, dict[date, float]], dict[str, dict[date, float]]]:
    own: dict[str, dict[date, float]] = defaultdict(lambda: defaultdict(float))
    total: dict[str, dict[date, float]] = defaultdict(lambda: defaultdict(float))
    for row in ownership.to_dicts():
        login = str(row["actor_login"]).lower()
        month = _month_value(row["month"])
        count = float(row["event_count"])
        total[login][month] += count
        if bool(row["is_own_repo"]):
            own[login][month] += count
    return own, total


def _composition_maps(
    monthly: pl.DataFrame,
) -> tuple[dict[str, dict[date, dict[str, float]]], tuple[str, ...]]:
    result: dict[str, dict[date, dict[str, float]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(float))
    )
    event_types: set[str] = set()
    for row in monthly.to_dicts():
        event_type = str(row["event_type"])
        count = float(row["event_count"])
        if event_type == "__NO_ACTIVITY__" or count <= 0:
            continue
        login = str(row["actor_login"]).lower()
        month = _month_value(row["month"])
        result[login][month][event_type] += count
        event_types.add(event_type)
    return result, tuple(sorted(event_types))


def _composition_vector(
    *,
    event_counts: Mapping[date, Mapping[str, float]],
    own_counts: Mapping[date, float],
    ownership_counts: Mapping[date, float],
    dates: Iterable[date],
    event_types: tuple[str, ...],
) -> list[float]:
    selected = set(dates)
    totals = [
        sum(event_counts.get(point, {}).get(event_type, 0.0) for point in selected)
        for event_type in event_types
    ]
    event_total = sum(totals)
    distribution = (
        [value / event_total for value in totals]
        if event_total > 0
        else [0.0 for _ in event_types]
    )
    ownership_total = sum(ownership_counts.get(point, 0.0) for point in selected)
    own_share = (
        sum(own_counts.get(point, 0.0) for point in selected) / ownership_total
        if ownership_total > 0
        else 0.0
    )
    return [*distribution, own_share]


def context_divergence_2q(
    *,
    month: date,
    event_counts: Mapping[date, Mapping[str, float]],
    own_counts: Mapping[date, float],
    ownership_counts: Mapping[date, float],
    event_types: tuple[str, ...],
) -> float | None:
    """Compare trailing-six-month activity composition with all earlier history."""
    observed_months = set(event_counts) | set(ownership_counts)
    if not observed_months:
        return None
    recent_start = add_months(month, -5)
    earliest = min(observed_months)
    if month_distance(recent_start, earliest) < 6:
        return None
    recent_dates = [add_months(month, offset) for offset in range(-5, 1)]
    prior_dates = [point for point in observed_months if point < recent_start]
    recent = _composition_vector(
        event_counts=event_counts,
        own_counts=own_counts,
        ownership_counts=ownership_counts,
        dates=recent_dates,
        event_types=event_types,
    )
    prior = _composition_vector(
        event_counts=event_counts,
        own_counts=own_counts,
        ownership_counts=ownership_counts,
        dates=prior_dates,
        event_types=event_types,
    )
    recent_norm = math.sqrt(sum(value * value for value in recent))
    prior_norm = math.sqrt(sum(value * value for value in prior))
    if recent_norm == 0 or prior_norm == 0:
        return None
    cosine = sum(left * right for left, right in zip(recent, prior, strict=True)) / (
        recent_norm * prior_norm
    )
    return 1.0 - min(max(cosine, -1.0), 1.0)


def _collaborator_maps(collaborators: pl.DataFrame) -> dict[str, dict[date, float]]:
    result: dict[str, dict[date, float]] = defaultdict(lambda: defaultdict(float))
    for row in collaborators.to_dicts():
        result[str(row["owner_login"]).lower()][_month_value(row["month"])] += float(
            row["distinct_collaborators"]
        )
    return result


def _share(
    numerator: Mapping[date, float],
    denominator: Mapping[date, float],
    month: date,
    start: int,
    stop: int,
) -> float:
    dates = [add_months(month, offset) for offset in range(start, stop + 1)]
    total = sum(denominator.get(point, 0.0) for point in dates)
    return sum(numerator.get(point, 0.0) for point in dates) / total if total else 0.0


def _feature_row(
    login: str,
    month: date,
    *,
    normalized: Mapping[tuple[str, str], Mapping[date, float]],
    weekend: Mapping[str, Mapping[date, float]],
    total: Mapping[str, Mapping[date, float]],
    traction: Mapping[tuple[str, str], Mapping[date, float]],
    repos: Mapping[str, Mapping[date, float]],
    own_repo: Mapping[str, Mapping[date, float]],
    ownership_total: Mapping[str, Mapping[date, float]],
    collaborators: Mapping[str, Mapping[date, float]],
    composition: Mapping[str, Mapping[date, Mapping[str, float]]],
    composition_event_types: tuple[str, ...],
) -> dict[str, float | None]:
    result: dict[str, float | None] = {}
    for event_class in ACTIVITY_CLASSES:
        values = normalized.get((login, event_class), {})
        for window in (1, 3, 6, 12):
            result[f"activity_{event_class}_{window}m"] = _sum_window(
                values, month, window
            )
        ratio, delta = _ratio_delta(values, month)
        result[f"activity_{event_class}_ratio_3m_prior12m"] = ratio
        result[f"activity_{event_class}_delta_3m_prior12m"] = delta
    result["burst_push_zscore"] = _burst_z(normalized.get((login, "push"), {}), month)
    result["burst_create_zscore"] = _burst_z(
        normalized.get((login, "create"), {}), month
    )

    repo_values = repos.get(login, {})
    for window in (3, 6, 12):
        result[f"new_repos_{window}m"] = _sum_window(repo_values, month, window)
    prior_repos = [
        point for point, count in repo_values.items() if point <= month and count > 0
    ]
    result["months_since_last_new_repo"] = (
        float(month_distance(month, max(prior_repos)))
        if prior_repos
        else NO_REPO_SENTINEL_MONTHS
    )
    result["cumulative_repos"] = sum(
        count for point, count in repo_values.items() if point <= month
    )

    for traction_class in TRACTION_CLASSES:
        values = traction.get((login, traction_class), {})
        for window in (3, 12):
            result[f"traction_{traction_class}_{window}m"] = _sum_window(
                values, month, window
            )
        ratio, delta = _ratio_delta(values, month)
        result[f"traction_{traction_class}_ratio_3m_prior12m"] = ratio
        result[f"traction_{traction_class}_delta_3m_prior12m"] = delta

    weekend_values = weekend.get(login, {})
    total_values = total.get(login, {})
    recent_share = _share(weekend_values, total_values, month, -2, 0)
    prior_share = _share(weekend_values, total_values, month, -14, -3)
    result["weekend_share_3m"] = recent_share
    result["weekend_share_prior12m"] = prior_share
    result["weekend_share_delta"] = recent_share - prior_share
    active_months = sorted(
        point for point, count in total_values.items() if count > 0 and point <= month
    )
    result["tenure_months"] = (
        float(month_distance(month, active_months[0]) + 1) if active_months else 0.0
    )
    if active_months:
        history = [
            total_values.get(add_months(active_months[0], offset), 0.0)
            for offset in range(month_distance(month, active_months[0]) + 1)
        ]
        result["activity_gini"] = _gini(history)
    else:
        result["activity_gini"] = 0.0
    result["no_gh_activity"] = float(not active_months)

    own_values = own_repo.get(login, {})
    ownership_values = ownership_total.get(login, {})
    recent_own_share = _share(own_values, ownership_values, month, -2, 0)
    prior_own_share = _share(own_values, ownership_values, month, -14, -3)
    result["own_repo_share_3m"] = recent_own_share
    result["own_repo_share_delta_3m_prior12m"] = recent_own_share - prior_own_share
    collaborator_values = collaborators.get(login, {})
    result["distinct_collaborators_3m"] = _sum_window(collaborator_values, month, 3)
    _, collaborator_delta = _ratio_delta(collaborator_values, month)
    result["distinct_collaborators_delta_3m_prior12m"] = collaborator_delta
    result["new_collaborator_burst_zscore"] = _burst_z(collaborator_values, month)
    result["context_divergence_2q"] = context_divergence_2q(
        month=month,
        event_counts=composition.get(login, {}),
        own_counts=own_values,
        ownership_counts=ownership_values,
        event_types=composition_event_types,
    )
    return result


def _render_data_card(
    definitions: list[FeatureDefinition],
    panel: pl.DataFrame,
    exclusions: dict[str, int],
) -> tuple[str, str]:
    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "panel_rows": panel.height,
        "people": panel.get_column("gh_login").n_unique(),
        "panel_contract": "One row per person-month from B-48 months through B-12 months inclusive; y=1 exactly from B-15 through B-12 for positives and is always zero for controls.",
        "normalization": "Mapped actor activity and received traction are divided by the same calendar month's mapped global GitHub event total and multiplied by 1,000,000.",
        "source_cutoff": "All event, traction, ownership, collaboration, context-composition, and repository-creation source timestamps are strictly before each person's t_cutoff=B-12 months.",
        "exclusions": exclusions,
        "capital_family_note": "Presentation taxonomy only; no weighting change. Financial capital is not observed in the current feature set.",
        "capital_families": capital_families(
            definition.name for definition in definitions
        ),
        "features": [
            {**asdict(definition), "capital_family": capital_family(definition.name)}
            for definition in definitions
        ],
    }
    markdown = [
        "# Feature Data Card\n\n",
        f"Generated: `{payload['generated_at']}`\n\n",
        f"Rows: **{panel.height:,}** across **{payload['people']:,}** people.\n\n",
        "## Panel and leakage contract\n\n",
        f"{payload['panel_contract']} {payload['source_cutoff']}\n\n",
        f"Normalization: {payload['normalization']}\n\n",
        "## Exclusions\n\n",
    ]
    markdown.extend(f"- {name}: {count}\n" for name, count in exclusions.items())
    markdown.append(
        "\n## Capital-family mapping\n\n"
        f"{payload['capital_family_note']}\n\n"
        "## Feature dictionary\n\n| Name | Block | Capital family | Definition | Null policy |\n| --- | --- | --- | --- | --- |\n"
    )
    markdown.extend(
        f"| `{item.name}` | {item.block} | {capital_family(item.name)} | {item.definition} | {item.null_policy} |\n"
        for item in definitions
    )
    return json.dumps(payload, indent=2, sort_keys=True), "".join(markdown)


def build_features(
    *,
    labels_path: Path = LABELS_PATH,
    monthly_agg_dir: Path = EVENTS_ROOT / "monthly_agg",
    owned_repo_agg_dir: Path = EVENTS_ROOT / "owned_repo_agg",
    ownership_agg_dir: Path = EVENTS_ROOT / "ownership_agg",
    collab_influx_dir: Path = EVENTS_ROOT / "collab_influx",
    repo_creations_dir: Path = EVENTS_ROOT / "repo_creations",
    baselines_path: Path = EVENTS_ROOT / "baselines" / "monthly_totals.parquet",
    matches_path: Path = EVENTS_ROOT / "negatives" / "matched.parquet",
    output_path: Path = PANEL_PATH,
    data_card_json_path: Path = DATA_CARD_JSON_PATH,
    data_card_md_path: Path = DATA_CARD_MD_PATH,
) -> pl.DataFrame:
    """Build and persist the complete person-month feature panel."""
    labels = _read_parquet_collection(labels_path)
    monthly = _read_parquet_collection(monthly_agg_dir)
    owned = _read_parquet_collection(owned_repo_agg_dir)
    ownership = _read_parquet_collection(ownership_agg_dir)
    collaborators = _read_parquet_collection(collab_influx_dir)
    creations = _read_parquet_collection(repo_creations_dir)
    baselines = _read_parquet_collection(baselines_path)
    matches = _read_parquet_collection(matches_path)
    _validate_columns(
        labels,
        {
            "gh_login",
            "gh_confidence",
            "batch_start_date",
            "founder_name",
            "company",
        },
        labels_path,
    )
    _validate_columns(
        monthly,
        {
            "actor_login",
            "month",
            "event_type",
            "is_weekend",
            "event_count",
            "t_cutoff",
            "cohort",
        },
        monthly_agg_dir,
    )
    _validate_columns(
        owned,
        {"owner_login", "month", "event_type", "event_count", "t_cutoff", "cohort"},
        owned_repo_agg_dir,
    )
    _validate_columns(
        ownership,
        {
            "actor_login",
            "month",
            "is_own_repo",
            "event_count",
            "t_cutoff",
            "cohort",
        },
        ownership_agg_dir,
    )
    _validate_columns(
        collaborators,
        {
            "owner_login",
            "month",
            "distinct_collaborators",
            "t_cutoff",
            "cohort",
        },
        collab_influx_dir,
    )
    _validate_columns(
        creations,
        {"actor_login", "created_at", "t_cutoff", "cohort"},
        repo_creations_dir,
    )
    _validate_columns(baselines, {"month", "event_type", "event_count"}, baselines_path)
    _validate_columns(
        matches, {"actor_login", "t_cutoff", "matched_positive_login"}, matches_path
    )
    _validate_non_null(
        monthly,
        {
            "actor_login",
            "month",
            "event_type",
            "is_weekend",
            "event_count",
            "t_cutoff",
            "cohort",
        },
        monthly_agg_dir,
    )
    _validate_counts(monthly, count_column="event_count", source=monthly_agg_dir)
    _validate_non_null(
        owned,
        {"owner_login", "month", "event_type", "event_count", "t_cutoff", "cohort"},
        owned_repo_agg_dir,
    )
    _validate_counts(owned, count_column="event_count", source=owned_repo_agg_dir)
    _validate_non_null(
        ownership,
        {
            "actor_login",
            "month",
            "is_own_repo",
            "event_count",
            "t_cutoff",
            "cohort",
        },
        ownership_agg_dir,
    )
    _validate_counts(ownership, count_column="event_count", source=ownership_agg_dir)
    _validate_non_null(
        collaborators,
        {
            "owner_login",
            "month",
            "distinct_collaborators",
            "t_cutoff",
            "cohort",
        },
        collab_influx_dir,
    )
    _validate_counts(
        collaborators,
        count_column="distinct_collaborators",
        source=collab_influx_dir,
    )
    _validate_non_null(
        creations,
        {"actor_login", "created_at", "t_cutoff", "cohort"},
        repo_creations_dir,
    )
    _validate_non_null(
        baselines, {"month", "event_type", "event_count"}, baselines_path
    )
    _validate_counts(
        baselines,
        count_column="event_count",
        source=baselines_path,
        strictly_positive=True,
    )
    _validate_non_null(
        matches,
        {"actor_login", "t_cutoff", "matched_positive_login"},
        matches_path,
    )

    _assert_source_before_cutoff(
        monthly,
        actor_column="actor_login",
        time_column="month",
        source_name="monthly_agg",
    )
    _assert_source_before_cutoff(
        owned,
        actor_column="owner_login",
        time_column="month",
        source_name="owned_repo_agg",
    )
    _assert_source_before_cutoff(
        ownership,
        actor_column="actor_login",
        time_column="month",
        source_name="ownership_agg",
    )
    _assert_source_before_cutoff(
        collaborators,
        actor_column="owner_login",
        time_column="month",
        source_name="collab_influx",
    )
    _assert_source_before_cutoff(
        creations,
        actor_column="actor_login",
        time_column="created_at",
        source_name="repo_creations",
    )

    monthly = monthly.with_columns(pl.col("actor_login").str.to_lowercase())
    positive_logins = set(
        monthly.filter(pl.col("cohort") == "positives")
        .get_column("actor_login")
        .unique()
        .to_list()
    )
    positives = _positive_records(labels, positive_logins)
    all_labeled = {
        str(login).lower()
        for login in labels.get_column("gh_login").drop_nulls().to_list()
        if str(login).strip()
    }
    normalized, weekend, total = _activity_maps(monthly, baselines)
    traction = _traction_maps(owned, baselines)
    repos = _repo_maps(creations)
    own_repo, ownership_total = _ownership_maps(ownership)
    collaborator_counts = _collaborator_maps(collaborators)
    composition, composition_event_types = _composition_maps(monthly)

    people: list[dict[str, object]] = []
    for login, label in positives.items():
        batch_start = _month_value(label["batch_start_date"])
        people.append(
            {
                "gh_login": login,
                "founder_name": label["founder_name"],
                "company": label["company"],
                "batch_start_date": batch_start,
                "t_cutoff": add_months(batch_start, -12),
                "person_type": "positive",
                "matched_positive_login": login,
                "match_group_id": f"{login}|{batch_start.isoformat()}",
            }
        )

    controls_seen: set[str] = set()
    excluded_controls = 0
    for match in matches.sort("matched_positive_login", "actor_login").to_dicts():
        login = str(match["actor_login"]).lower()
        matched_login = str(match["matched_positive_login"]).lower()
        if login in all_labeled:
            raise ValueError(f"Labeled founder {login!r} appears in matched controls")
        if matched_login not in positives or login in controls_seen:
            excluded_controls += 1
            continue
        batch_start = _month_value(positives[matched_login]["batch_start_date"])
        expected_cutoff = add_months(batch_start, -12)
        if _month_value(match["t_cutoff"]) != expected_cutoff:
            raise ValueError(
                f"Control {login!r} cutoff does not match positive {matched_login!r}"
            )
        controls_seen.add(login)
        people.append(
            {
                "gh_login": login,
                "founder_name": None,
                "company": None,
                "batch_start_date": batch_start,
                "t_cutoff": expected_cutoff,
                "person_type": "control",
                "matched_positive_login": matched_login,
                "match_group_id": f"{matched_login}|{batch_start.isoformat()}",
            }
        )
    if not people:
        raise ValueError(
            "No eligible positive founders and matched controls were found"
        )

    expected_cutoffs = {
        str(person["gh_login"]): person["t_cutoff"] for person in people
    }
    _assert_expected_cutoffs(
        monthly,
        actor_column="actor_login",
        expected=expected_cutoffs,
        source_name="monthly_agg",
    )
    _assert_expected_cutoffs(
        owned,
        actor_column="owner_login",
        expected=expected_cutoffs,
        source_name="owned_repo_agg",
    )
    _assert_expected_cutoffs(
        ownership,
        actor_column="actor_login",
        expected=expected_cutoffs,
        source_name="ownership_agg",
    )
    _assert_expected_cutoffs(
        collaborators,
        actor_column="owner_login",
        expected=expected_cutoffs,
        source_name="collab_influx",
    )
    _assert_expected_cutoffs(
        creations,
        actor_column="actor_login",
        expected=expected_cutoffs,
        source_name="repo_creations",
    )

    rows: list[dict[str, object]] = []
    for person in sorted(
        people, key=lambda row: (str(row["gh_login"]), str(row["person_type"]))
    ):
        batch_start = person["batch_start_date"]
        assert isinstance(batch_start, date)
        login = str(person["gh_login"])
        for month in panel_months(batch_start):
            rows.append(
                {
                    **person,
                    "month": month,
                    "gestation_start": add_months(batch_start, -9),
                    "y": hazard_label(batch_start, month)
                    if person["person_type"] == "positive"
                    else 0,
                    **_feature_row(
                        login,
                        month,
                        normalized=normalized,
                        weekend=weekend,
                        total=total,
                        traction=traction,
                        repos=repos,
                        own_repo=own_repo,
                        ownership_total=ownership_total,
                        collaborators=collaborator_counts,
                        composition=composition,
                        composition_event_types=composition_event_types,
                    ),
                }
            )
    definitions = feature_definitions()
    feature_names = [definition.name for definition in definitions]
    panel = (
        # infer_schema_length=None scans every row: metadata like founder_name is
        # None for controls and str for founders, which breaks windowed inference.
        pl.DataFrame(rows, infer_schema_length=None)
        .select(*METADATA_COLUMNS, *feature_names)
        .sort("match_group_id", "gh_login", "month")
    )
    non_nullable_features = [
        name for name in feature_names if name != "context_divergence_2q"
    ]
    if panel.select(
        pl.any_horizontal(pl.col(non_nullable_features).is_null()).any()
    ).item():
        raise AssertionError("Feature builder emitted null model inputs")
    exclusions = {
        "labels_below_confidence_or_without_positive_aggregate": max(
            labels.height - len(positives), 0
        ),
        "controls_without_an_included_match_or_duplicate_controls": excluded_controls,
    }
    card_json, card_md = _render_data_card(definitions, panel, exclusions)
    _atomic_write_parquet(panel, output_path)
    _atomic_write_text(card_json + "\n", data_card_json_path)
    _atomic_write_text(card_md, data_card_md_path)
    return panel


if __name__ == "__main__":
    build_features()
