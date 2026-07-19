"""Validate and assemble model outputs into the dashboard rendering contract."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import polars as pl

from vc_brain.memo.schema import Memo


TEST_COHORT_START = date(2024, 1, 1)
BACKTEST_EXAMPLE_LIMIT = 10
BACKTEST_WINDOW_MONTHS = 48

CANDIDATE_COLUMNS = {
    "gh_login",
    "founder_name",
    "company",
    "source",
    "current_score",
    "score_percentile",
    "momentum_3mo",
    "first_detection_month",
    "status",
}
TRAJECTORY_COLUMNS = {"gh_login", "month", "score"}
ATTRIBUTION_COLUMNS = {
    "login",
    "crossing_month",
    "feature",
    "delta_contrib",
}
LABEL_COLUMNS = {
    "founder_name",
    "company",
    "slug",
    "batch",
    "batch_start_date",
    "gh_login",
}
REPO_CREATION_COLUMNS = {"actor_login", "created_at", "repo_name"}


class DashboardWiringError(ValueError):
    """Real model outputs cannot satisfy the static-dashboard contract."""


@dataclass(frozen=True)
class BacktestFounder:
    """One detected test-cohort founder shown in the retrospective backtest."""

    gh_login: str
    founder_name: str
    company: str
    batch: str
    batch_start: date
    detection_month: date
    lead_months: int
    high_propensity_from_start: bool
    current_score: float
    flagged_on: tuple[str, ...]
    trajectory: list[dict[str, Any]]


@dataclass(frozen=True)
class BacktestSummary:
    """Held-out cohort metrics and strongest detected founder examples."""

    detected: int
    total_test_founders: int
    detection_rate: float
    window_start_detected: int
    window_start_share: float
    rising_signal_detected: int
    rising_median_lead_months: float | None
    rising_lead_months_iqr: tuple[float, float] | None
    threshold: str
    matched_group_rank_one: float
    matched_group_chance: float
    matched_group_count: int
    founders: list[BacktestFounder]


@dataclass(frozen=True)
class DashboardInputs:
    """Fully assembled, renderer-ready data for one dashboard build."""

    candidates: list[dict[str, Any]]
    trajectories: list[dict[str, Any]]
    events: list[dict[str, Any]]
    profiles: dict[str, dict[str, Any]]
    memos: dict[str, Memo]
    memo_paths: dict[str, Path]
    backtest: BacktestSummary
    synthetic: bool


def wire_real_data(data_root: Path = Path("data")) -> DashboardInputs:
    """Load, validate, and join real eval, event, label, and optional memo outputs."""
    data_root = data_root.resolve()
    paths = {
        "candidates": data_root / "scores" / "candidates.parquet",
        "trajectories": data_root / "scores" / "trajectories.parquet",
        "attributions": data_root / "scores" / "attributions.parquet",
        "report": data_root / "eval" / "report.json",
        "labels": data_root / "labels" / "founders.parquet",
        "repo_creations": data_root / "events" / "repo_creations",
    }
    missing = [path for path in paths.values() if not path.exists()]
    if missing:
        rendered = "\n".join(f"  - {_relative(path, data_root)}" for path in missing)
        raise DashboardWiringError(
            "Missing required real-data inputs:\n"
            f"{rendered}\n"
            "Run the label/event pipeline and model eval stage before --real."
        )

    candidates_frame = pl.read_parquet(paths["candidates"])
    trajectories_frame = pl.read_parquet(paths["trajectories"])
    attributions_frame = pl.read_parquet(paths["attributions"])
    labels_frame = pl.read_parquet(paths["labels"])
    repo_frames = [
        pl.read_parquet(path)
        for path in sorted(paths["repo_creations"].glob("*.parquet"))
    ]
    if not repo_frames:
        raise DashboardWiringError(
            "Invalid real-data input events/repo_creations: no parquet files found"
        )

    _require_columns("scores/candidates.parquet", candidates_frame, CANDIDATE_COLUMNS)
    _require_columns(
        "scores/trajectories.parquet", trajectories_frame, TRAJECTORY_COLUMNS
    )
    _require_columns(
        "scores/attributions.parquet", attributions_frame, ATTRIBUTION_COLUMNS
    )
    _require_columns("labels/founders.parquet", labels_frame, LABEL_COLUMNS)
    for frame in repo_frames:
        _require_columns(
            "events/repo_creations/*.parquet", frame, REPO_CREATION_COLUMNS
        )

    report = _load_report(paths["report"])
    candidates, label_by_login = _real_candidates(candidates_frame, labels_frame)
    logins = {str(candidate["gh_login"]) for candidate in candidates}
    trajectories = trajectories_frame.filter(
        pl.col("gh_login").is_in(logins)
    ).to_dicts()
    missing_trajectories = logins - {str(row["gh_login"]) for row in trajectories}
    if missing_trajectories:
        raise DashboardWiringError(
            "Invalid scores/trajectories.parquet: no rows for candidate logins "
            f"{sorted(missing_trajectories)}"
        )

    repositories = pl.concat(repo_frames, how="diagonal_relaxed")
    events = _real_events(repositories, candidates, label_by_login)
    profiles = _real_profiles(candidates, label_by_login)
    memos, memo_paths = _real_memos(data_root / "memos", candidates)
    backtest = _real_backtest(
        candidates,
        trajectories,
        attributions_frame,
        label_by_login,
        report,
    )
    return DashboardInputs(
        candidates=candidates,
        trajectories=trajectories,
        events=events,
        profiles=profiles,
        memos=memos,
        memo_paths=memo_paths,
        backtest=backtest,
        synthetic=False,
    )


def _real_candidates(
    candidates: pl.DataFrame, labels: pl.DataFrame
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    if candidates.is_empty():
        raise DashboardWiringError(
            "Invalid scores/candidates.parquet: eval emitted no detected founders"
        )
    invalid_sources = (
        candidates.filter(pl.col("source") != "outbound_detector")
        .get_column("source")
        .unique()
        .to_list()
    )
    if invalid_sources:
        raise DashboardWiringError(
            "Invalid scores/candidates.parquet: real candidates must have "
            f"source='outbound_detector', found {invalid_sources}"
        )

    eligible_labels = labels.filter(
        pl.col("batch_start_date").is_not_null()
        & (pl.col("batch_start_date") >= TEST_COHORT_START)
        & pl.col("gh_login").is_not_null()
    )
    labels_by_login: dict[str, list[dict[str, Any]]] = {}
    for row in eligible_labels.sort("batch_start_date", "company").to_dicts():
        labels_by_login.setdefault(str(row["gh_login"]), []).append(row)

    rows = candidates.sort(
        "current_score", "gh_login", descending=[True, False]
    ).to_dicts()
    missing_labels = sorted(
        str(row["gh_login"])
        for row in rows
        if str(row["gh_login"]) not in labels_by_login
    )
    if missing_labels:
        raise DashboardWiringError(
            "Invalid real-data join: candidates are not labeled test-cohort founders "
            f"(batch_start >= 2024): {missing_labels}"
        )

    assembled: list[dict[str, Any]] = []
    label_by_login: dict[str, dict[str, Any]] = {}
    for row in rows:
        login = str(row["gh_login"])
        matching_labels = labels_by_login[login]
        label = next(
            (
                item
                for item in matching_labels
                if item.get("founder_name") == row.get("founder_name")
                and item.get("company") == row.get("company")
            ),
            matching_labels[0],
        )
        label_by_login[login] = label
        missing_display = [
            field
            for field in ("founder_name", "company", "slug", "batch")
            if not label.get(field)
        ]
        if missing_display:
            raise DashboardWiringError(
                f"Invalid labels/founders.parquet row for {login!r}: "
                f"missing values {missing_display}"
            )
        detection = row.get("first_detection_month")
        if detection is None:
            raise DashboardWiringError(
                "Invalid scores/candidates.parquet: detected candidate "
                f"{login!r} has no first_detection_month"
            )
        item = dict(row)
        item["founder_name"] = label["founder_name"]
        item["company"] = label["company"]
        assembled.append(item)
    return assembled, label_by_login


def _real_events(
    repositories: pl.DataFrame,
    candidates: list[dict[str, Any]],
    label_by_login: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    logins = {str(candidate["gh_login"]) for candidate in candidates}
    rows: list[dict[str, Any]] = []
    for repo in repositories.filter(pl.col("actor_login").is_in(logins)).to_dicts():
        login = str(repo["actor_login"])
        repo_name = str(repo["repo_name"])
        created_at = repo["created_at"]
        rows.append(
            {
                "evidence_id": _evidence_id(
                    "repo_created", login, _iso(created_at), repo_name
                ),
                "gh_login": login,
                "ts": created_at,
                "event_type": "repo_created",
                "repo_name": repo_name,
                "detail": f"Public repository {repo_name} was created.",
                "url": f"https://github.com/{repo_name}",
            }
        )

    for candidate in candidates:
        login = str(candidate["gh_login"])
        label = label_by_login[login]
        batch_start = label["batch_start_date"]
        company = str(label["company"])
        batch = str(label["batch"])
        slug = str(label["slug"])
        timestamp = datetime.combine(batch_start, datetime.min.time(), tzinfo=UTC)
        rows.append(
            {
                "evidence_id": _evidence_id(
                    "yc_batch", login, batch_start.isoformat(), slug
                ),
                "gh_login": login,
                "ts": timestamp,
                "event_type": "yc_batch",
                "repo_name": company,
                "detail": f"{company} joined Y Combinator's {batch} batch.",
                "url": f"https://www.ycombinator.com/companies/{slug}",
            }
        )
    return rows


def _real_profiles(
    candidates: list[dict[str, Any]],
    label_by_login: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    profiles: dict[str, dict[str, Any]] = {}
    for candidate in candidates:
        login = str(candidate["gh_login"])
        label = label_by_login[login]
        profiles[login] = {
            "sector": label.get("sector") or "Not classified",
            "stage": f"YC {label['batch']}",
            "geography": label.get("location") or "Not disclosed",
            "round_size_usd": None,
            "one_liner": label.get("one_liner") or "Not disclosed",
            "company_website": label.get("company_website") or None,
        }
    return profiles


def _real_memos(
    memo_dir: Path, candidates: list[dict[str, Any]]
) -> tuple[dict[str, Memo], dict[str, Path]]:
    top_logins = [
        str(candidate["gh_login"])
        for candidate in candidates
        if candidate["source"] == "outbound_detector"
    ][:3]
    memos: dict[str, Memo] = {}
    memo_paths: dict[str, Path] = {}
    for login in top_logins:
        path = memo_dir / f"{login}.json"
        if not path.exists():
            continue
        try:
            memo = Memo.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise DashboardWiringError(f"Invalid optional memo {path}: {exc}") from exc
        if login not in memo.founder_logins:
            raise DashboardWiringError(
                f"Invalid optional memo {path}: founder_logins does not include {login}"
            )
        memos[login] = memo
        memo_paths[login] = path
    return memos, memo_paths


def _real_backtest(
    candidates: list[dict[str, Any]],
    trajectories: list[dict[str, Any]],
    attributions: pl.DataFrame,
    label_by_login: dict[str, dict[str, Any]],
    report: dict[str, Any],
) -> BacktestSummary:
    lead = report["lead_time"]
    detected = int(lead["detected"])
    total = int(lead["total_test_founders"])
    detection_rate = float(lead["detection_rate"])
    expected_rate = detected / total if total else 0.0
    if detected < 0 or total < detected or not 0.0 <= detection_rate <= 1.0:
        raise DashboardWiringError(
            "Invalid eval/report.json: impossible lead_time detection counts or rate"
        )
    if abs(detection_rate - expected_rate) > 1e-9:
        raise DashboardWiringError(
            "Invalid eval/report.json: lead_time.detection_rate does not equal "
            "detected / total_test_founders"
        )
    threshold = str(lead["threshold"])
    normalized_threshold = threshold.lower()
    if (
        "99th percentile" not in normalized_threshold
        or "month" not in normalized_threshold
    ):
        raise DashboardWiringError(
            "Invalid eval/report.json: lead_time.threshold must describe the "
            "same-month 99th-percentile control threshold"
        )

    by_login: dict[str, list[dict[str, Any]]] = {}
    for row in trajectories:
        by_login.setdefault(str(row["gh_login"]), []).append(row)

    display_names = report["feature_display_names"]
    attribution_by_login: dict[str, tuple[str, ...]] = {}
    attribution_crossing_by_login: dict[str, date] = {}
    ordered_attributions = attributions.with_columns(
        pl.col("delta_contrib").abs().alias("_magnitude")
    ).sort("login", "_magnitude", descending=[False, True])
    for login, group in ordered_attributions.group_by(
        "login", maintain_order=True
    ):
        login_value = str(login[0])
        features = group.get_column("feature").to_list()
        missing_names = [name for name in features if name not in display_names]
        if missing_names:
            raise DashboardWiringError(
                "Invalid eval/report.json: feature_display_names is missing "
                f"attribution features {missing_names}"
            )
        attribution_by_login[login_value] = tuple(
            str(display_names[name]) for name in features
        )
        crossing_months = group.get_column("crossing_month").unique().to_list()
        if len(crossing_months) != 1:
            raise DashboardWiringError(
                "Invalid scores/attributions.parquet: attribution rows for "
                f"{login_value!r} disagree on crossing_month"
            )
        attribution_crossing_by_login[login_value] = _as_date(
            crossing_months[0], "attribution crossing_month"
        )

    founders: list[BacktestFounder] = []
    for candidate in candidates[:BACKTEST_EXAMPLE_LIMIT]:
        login = str(candidate["gh_login"])
        label = label_by_login[login]
        batch_start = _as_date(label["batch_start_date"], "batch_start_date")
        detection = _as_date(
            candidate["first_detection_month"], "first_detection_month"
        )
        trajectory = sorted(by_login[login], key=lambda row: _iso(row["month"]))
        first_panel_month = (
            min(_as_date(row["month"], "trajectory month") for row in trajectory)
            if trajectory
            else _add_months(batch_start, -BACKTEST_WINDOW_MONTHS)
        )
        if detection < first_panel_month:
            raise DashboardWiringError(
                "Invalid scores/candidates.parquet: first detection for "
                f"{login!r} precedes the founder's first panel month"
            )
        flagged_on = attribution_by_login.get(login, ())
        if len(flagged_on) != 3:
            raise DashboardWiringError(
                "Invalid scores/attributions.parquet: expected exactly three "
                f"features for detected founder {login!r}, found {len(flagged_on)}"
            )
        if attribution_crossing_by_login[login] != detection:
            raise DashboardWiringError(
                "Invalid scores/attributions.parquet: crossing month does not match "
                f"first detection for {login!r}"
            )
        founders.append(
            BacktestFounder(
                gh_login=login,
                founder_name=str(label["founder_name"]),
                company=str(label["company"]),
                batch=str(label["batch"]),
                batch_start=batch_start,
                detection_month=detection,
                lead_months=_month_distance(batch_start, detection),
                high_propensity_from_start=detection == first_panel_month,
                current_score=float(candidate["current_score"]),
                flagged_on=flagged_on,
                trajectory=trajectory,
            )
        )

    lead_months = _validated_lead_months(lead, detected)
    window_start_detected = sum(
        value == BACKTEST_WINDOW_MONTHS for value in lead_months
    )
    rising_leads = [value for value in lead_months if value < BACKTEST_WINDOW_MONTHS]
    rising_quartiles = (
        tuple(_percentile(rising_leads, quantile) for quantile in (0.25, 0.5, 0.75))
        if rising_leads
        else None
    )
    return BacktestSummary(
        detected=detected,
        total_test_founders=total,
        detection_rate=detection_rate,
        window_start_detected=window_start_detected,
        window_start_share=(window_start_detected / detected if detected else 0.0),
        rising_signal_detected=len(rising_leads),
        rising_median_lead_months=(rising_quartiles[1] if rising_quartiles else None),
        rising_lead_months_iqr=(
            (rising_quartiles[0], rising_quartiles[2]) if rising_quartiles else None
        ),
        threshold=threshold,
        matched_group_rank_one=float(
            report["matched_group_rank"]["rank_1_probability"]
        ),
        matched_group_chance=float(
            report["matched_group_rank"]["chance_rank_1_probability"]
        ),
        matched_group_count=int(report["matched_group_rank"]["groups"]),
        founders=founders,
    )


def _load_report(path: Path) -> dict[str, Any]:
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
        lead = report["lead_time"]
        matched = report["matched_group_rank"]
        report["feature_display_names"]
        for field in (
            "rank_1_probability",
            "chance_rank_1_probability",
            "groups",
        ):
            matched[field]
        for field in (
            "detected",
            "total_test_founders",
            "detection_rate",
            "lead_months",
            "threshold",
        ):
            lead[field]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as exc:
        raise DashboardWiringError(
            f"Invalid eval/report.json lead-time contract: {exc}"
        ) from exc
    return report


def _require_columns(name: str, frame: pl.DataFrame, required: set[str]) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise DashboardWiringError(
            f"Invalid {name}: missing required columns {missing}"
        )


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _evidence_id(*parts: str) -> str:
    content = "\x1f".join(parts).encode("utf-8")
    return f"real-{hashlib.sha256(content).hexdigest()[:20]}"


def _as_date(value: Any, field: str) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    raise DashboardWiringError(f"Invalid {field}: expected date, got {value!r}")


def _month_distance(later: date, earlier: date) -> int:
    return (later.year - earlier.year) * 12 + later.month - earlier.month


def _add_months(value: date, months: int) -> date:
    index = value.year * 12 + value.month - 1 + months
    return date(index // 12, index % 12 + 1, 1)


def _validated_lead_months(lead: dict[str, Any], detected: int) -> list[int]:
    values = lead["lead_months"]
    if not isinstance(values, list):
        raise DashboardWiringError(
            "Invalid eval/report.json: lead_time.lead_months must be a list"
        )
    try:
        lead_months = [int(value) for value in values]
    except (TypeError, ValueError) as exc:
        raise DashboardWiringError(
            "Invalid eval/report.json: lead_time.lead_months must contain integers"
        ) from exc
    if any(
        float(raw) != parsed for raw, parsed in zip(values, lead_months, strict=True)
    ):
        raise DashboardWiringError(
            "Invalid eval/report.json: lead_time.lead_months must contain integers"
        )
    if len(lead_months) != detected:
        raise DashboardWiringError(
            "Invalid eval/report.json: lead_time.lead_months count does not equal "
            "lead_time.detected"
        )
    if any(value < 0 or value > BACKTEST_WINDOW_MONTHS for value in lead_months):
        raise DashboardWiringError(
            "Invalid eval/report.json: lead times must fall within the 48-month window"
        )
    return lead_months


def _percentile(values: list[int], quantile: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * quantile
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    weight = index - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _iso(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)
