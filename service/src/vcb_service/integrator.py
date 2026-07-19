"""Adapt the main pipeline's real outputs to the immutable index input contract."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import polars as pl
from pydantic import ValidationError

from vcb_service.claim_schema import Memo


COMPONENT_SUM_TOLERANCE = 0.001


class IntegrationBuildError(RuntimeError):
    """Raised when real source data cannot produce the integration contract."""


class IntegrationVerificationError(IntegrationBuildError):
    """Raised when a staged integration fails an integrity gate."""

    def __init__(self, result: IntegrationResult) -> None:
        self.result = result
        failures: list[str] = []
        if result.dangling_refs:
            detail = ", ".join(
                f"{claim_key} -> {evidence_ref}"
                for claim_key, evidence_ref in result.dangling_refs
            )
            failures.append(f"dangling memo evidence references: {detail}")
        if result.component_sum_errors:
            detail = ", ".join(
                f"{login} score={score:.6f} components={total:.6f}"
                for login, score, total in result.component_sum_errors
            )
            failures.append(f"score component sums do not match: {detail}")
        super().__init__("; ".join(failures))


@dataclass(frozen=True)
class IntegrationResult:
    path: Path
    cohort_size: int
    recognition_count: int
    component_coverage_count: int
    evidence_counts: dict[str, int]
    memo_count: int
    memo_ref_count: int
    dangling_refs: list[tuple[str, str]]
    component_sum_errors: list[tuple[str, float, float]]


def normalize_score_percentile(value: Any) -> float:
    """Normalize a percentile to 0..100 without double-scaling existing values."""

    if isinstance(value, bool):
        raise IntegrationBuildError("score_percentile must be numeric, not boolean")
    try:
        percentile = float(value)
    except (TypeError, ValueError) as error:
        raise IntegrationBuildError(
            f"score_percentile must be numeric, got {value!r}"
        ) from error
    if not math.isfinite(percentile) or percentile < 0.0 or percentile > 100.0:
        raise IntegrationBuildError(
            f"score_percentile must be in 0..1 or already normalized in 0..100; "
            f"got {value!r}"
        )
    return percentile * 100.0 if percentile <= 1.0 else percentile


def build_recognition_lookup(founders: pl.DataFrame) -> dict[str, dict[str, str]]:
    """Select the highest-confidence real YC label for each GitHub login."""

    required = {
        "gh_login",
        "gh_confidence",
        "batch_start_date",
        "batch",
    }
    _require_columns(founders, required, label="labels/founders.parquet")
    selected: dict[str, tuple[float, str, str, dict[str, str]]] = {}
    for row in founders.select(sorted(required)).to_dicts():
        login_value = row.get("gh_login")
        batch_date = row.get("batch_start_date")
        batch_value = row.get("batch")
        if not login_value or batch_date is None or not batch_value:
            continue
        login = str(login_value)
        confidence_value = row.get("gh_confidence")
        confidence = (
            float(confidence_value)
            if confidence_value is not None and math.isfinite(float(confidence_value))
            else float("-inf")
        )
        month = _date_text(batch_date)[:7]
        batch = str(batch_value)
        recognition = {
            "month": month,
            "kind": "yc_batch",
            "label": f"YC {batch}",
        }
        # Confidence governs the join. The remaining fields only make ties stable.
        rank = (confidence, month, batch, recognition)
        current = selected.get(login)
        if current is None or rank[:3] > current[:3]:
            selected[login] = rank
    return {login: value[3] for login, value in selected.items()}


def build_score_components(
    candidates: pl.DataFrame, attributions: pl.DataFrame
) -> dict[str, list[dict[str, Any]]]:
    """Build an additive top-four attribution waterfall for each candidate."""

    _require_columns(
        candidates,
        {"gh_login", "current_score", "first_detection_month"},
        label="scores/candidates.parquet",
    )
    _require_columns(
        attributions,
        {"login", "crossing_month", "feature", "delta_contrib"},
        label="scores/attributions.parquet",
    )
    rows_by_login: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in attributions.select(
        ["login", "crossing_month", "feature", "delta_contrib"]
    ).to_dicts():
        if row.get("login"):
            rows_by_login[str(row["login"])].append(row)

    result: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates.select(
        ["gh_login", "current_score", "first_detection_month"]
    ).to_dicts():
        login = str(candidate["gh_login"])
        rows = rows_by_login.get(login, [])
        if not rows:
            result[login] = []
            continue

        detection_month = candidate.get("first_detection_month")
        crossing_rows = (
            [row for row in rows if row.get("crossing_month") == detection_month]
            if detection_month is not None
            else []
        )
        observed_rows = crossing_rows or rows
        magnitudes: dict[str, float] = defaultdict(float)
        for row in observed_rows:
            feature_value = row.get("feature")
            contribution_value = row.get("delta_contrib")
            if not feature_value or contribution_value is None:
                continue
            contribution = float(contribution_value)
            if math.isfinite(contribution):
                magnitudes[str(feature_value)] += abs(contribution)

        total_magnitude = sum(magnitudes.values())
        current_score = float(candidate["current_score"])
        if total_magnitude <= 0.0:
            result[login] = []
            continue
        top = sorted(magnitudes.items(), key=lambda item: (-item[1], item[0]))[:4]
        components = [
            {
                "key": feature,
                "label": humanize_feature(feature),
                "contribution": magnitude / total_magnitude * current_score,
            }
            for feature, magnitude in top
        ]
        top_total = sum(float(component["contribution"]) for component in components)
        remainder = current_score - top_total
        if abs(remainder) < 1e-15:
            remainder = 0.0
        components.append(
            {
                "key": "other_observed_signals",
                "label": "Other observed signals",
                "contribution": remainder,
            }
        )
        result[login] = components
    return result


def humanize_feature(feature: str) -> str:
    """Turn a snake_case feature key into a compact human label."""

    return feature.replace("_", " ").strip().capitalize()


def unresolved_memo_refs(
    memos: Mapping[str, Mapping[str, Any]], events: Sequence[Mapping[str, Any]]
) -> list[tuple[str, str]]:
    """Return every non-URL memo reference absent from the evidence rows."""

    evidence_ids = {str(event["evidence_id"]) for event in events}
    unresolved: list[tuple[str, str]] = []
    for memo_name, memo in sorted(memos.items()):
        for claim_id, claim in sorted(memo["claims"].items()):
            claim_key = f"{memo_name}:{claim_id}"
            for evidence_ref in claim["evidence_refs"]:
                ref = str(evidence_ref)
                if ref not in evidence_ids and not ref.startswith(("https://", "http://")):
                    unresolved.append((claim_key, ref))
    return unresolved


def component_sum_errors(
    candidates: Sequence[Mapping[str, Any]],
    *,
    tolerance: float = COMPONENT_SUM_TOLERANCE,
) -> list[tuple[str, float, float]]:
    """Return populated waterfalls whose additive total drifts from the score."""

    errors: list[tuple[str, float, float]] = []
    for candidate in candidates:
        components = candidate["score_components"]
        if not components:
            continue
        score = float(candidate["current_score"])
        total = sum(float(component["contribution"]) for component in components)
        if abs(total - score) > tolerance + 1e-12:
            errors.append((str(candidate["gh_login"]), score, total))
    return errors


def build_integration(
    source: Path, out: Path, *, verify: bool = False
) -> IntegrationResult:
    """Build the integrated directory, publishing it only after optional gates pass."""

    source = source.resolve()
    out = out.resolve()
    if not source.is_dir():
        raise IntegrationBuildError(f"source directory not found: {source}")
    if out == source or source in out.parents:
        raise IntegrationBuildError(
            f"output must not be inside the read-only source directory: {out}"
        )
    if out.exists() and not out.is_dir():
        raise IntegrationBuildError(f"output exists and is not a directory: {out}")

    candidates_frame = _read_parquet(source / "scores" / "candidates.parquet")
    trajectories_frame = _read_parquet(source / "scores" / "trajectories.parquet")
    attributions_frame = _read_parquet(source / "scores" / "attributions.parquet")
    founders_frame = _read_parquet(source / "labels" / "founders.parquet")
    repo_frames = [
        _read_parquet(source / "events" / "repo_creations" / name)
        for name in ("positives.parquet", "negatives.parquet")
    ]
    monthly_frames = [
        _read_parquet(source / "events" / "monthly_agg" / name)
        for name in ("positives.parquet", "negatives.parquet")
    ]
    memo_paths, memo_documents = _load_memos(source / "memos")

    _require_columns(
        candidates_frame,
        {
            "gh_login",
            "founder_name",
            "company",
            "source",
            "current_score",
            "score_percentile",
            "momentum_3mo",
            "first_detection_month",
            "status",
        },
        label="scores/candidates.parquet",
    )
    candidate_logins = [str(value) for value in candidates_frame["gh_login"].to_list()]
    if len(candidate_logins) != len(set(candidate_logins)):
        raise IntegrationBuildError("scores/candidates.parquet has duplicate gh_login rows")
    cohort = set(candidate_logins)
    recognition_lookup = build_recognition_lookup(founders_frame)
    components_lookup = build_score_components(candidates_frame, attributions_frame)

    candidate_rows: list[dict[str, Any]] = []
    for row in candidates_frame.to_dicts():
        login = str(row["gh_login"])
        try:
            percentile = normalize_score_percentile(row["score_percentile"])
        except IntegrationBuildError as error:
            raise IntegrationBuildError(f"candidate {login}: {error}") from error
        candidate = _json_ready(row)
        candidate["score_percentile"] = percentile
        candidate["recognition"] = recognition_lookup.get(login)
        candidate["score_components"] = components_lookup[login]
        candidate_rows.append(candidate)

    _require_columns(
        trajectories_frame,
        {"gh_login", "month", "score"},
        label="scores/trajectories.parquet",
    )
    trajectory_rows = [
        _json_ready(row)
        for row in trajectories_frame.filter(pl.col("gh_login").is_in(candidate_logins))
        .sort(["gh_login", "month"])
        .to_dicts()
    ]

    events = _build_events(
        cohort=cohort,
        candidate_rows=candidate_rows,
        attributions=attributions_frame,
        founders=founders_frame,
        repo_frames=repo_frames,
        monthly_frames=monthly_frames,
        memos=memo_documents,
    )
    profiles = _build_profiles(candidate_rows, founders_frame)
    errors = component_sum_errors(candidate_rows)
    dangling = unresolved_memo_refs(memo_documents, events)
    result = IntegrationResult(
        path=out,
        cohort_size=len(candidate_rows),
        recognition_count=sum(row["recognition"] is not None for row in candidate_rows),
        component_coverage_count=sum(bool(row["score_components"]) for row in candidate_rows),
        evidence_counts=dict(sorted(Counter(row["event_type"] for row in events).items())),
        memo_count=len(memo_paths),
        memo_ref_count=sum(
            len(claim["evidence_refs"])
            for memo in memo_documents.values()
            for claim in memo["claims"].values()
        ),
        dangling_refs=dangling,
        component_sum_errors=errors,
    )
    if verify and (dangling or errors):
        raise IntegrationVerificationError(result)

    out.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{out.name}.", dir=out.parent))
    try:
        _write_rows(stage, "candidates", candidate_rows)
        _write_rows(stage, "trajectories", trajectory_rows)
        _write_rows(stage, "events", events)
        (stage / "profiles.json").write_text(
            json.dumps(profiles, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        memo_out = stage / "memos"
        memo_out.mkdir()
        for memo_path in memo_paths:
            shutil.copyfile(memo_path, memo_out / memo_path.name)
        _publish_directory(stage, out)
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        raise
    return result


def format_verification(result: IntegrationResult) -> list[str]:
    """Render the stable human-readable verification summary."""

    cohort = result.cohort_size
    recognition_rate = result.recognition_count / cohort * 100.0 if cohort else 0.0
    coverage_rate = result.component_coverage_count / cohort * 100.0 if cohort else 0.0
    lines = [
        f"cohort size: {cohort}",
        "recognition join rate: "
        f"{result.recognition_count}/{cohort} ({recognition_rate:.1f}%)",
        "score_components coverage: "
        f"{result.component_coverage_count}/{cohort} ({coverage_rate:.1f}%)",
        "evidence counts:",
    ]
    lines.extend(
        f"  {event_type}: {count}"
        for event_type, count in result.evidence_counts.items()
    )
    resolved = result.memo_ref_count - len(result.dangling_refs)
    lines.append(
        f"memo refs: {resolved}/{result.memo_ref_count} resolved "
        f"across {result.memo_count} memos"
    )
    lines.append(
        "ref-resolution status: ok"
        if not result.dangling_refs
        else f"ref-resolution status: {len(result.dangling_refs)} dangling"
    )
    lines.append(
        "score_components sums: ok"
        if not result.component_sum_errors
        else f"score_components sums: {len(result.component_sum_errors)} drifted"
    )
    return lines


def _build_events(
    *,
    cohort: set[str],
    candidate_rows: Sequence[Mapping[str, Any]],
    attributions: pl.DataFrame,
    founders: pl.DataFrame,
    repo_frames: Sequence[pl.DataFrame],
    monthly_frames: Sequence[pl.DataFrame],
    memos: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    refs = _memo_refs(memos)
    repo_refs = {ref for ref in refs if ref.startswith("repo:")}
    detector_refs = {ref for ref in refs if ref.startswith("detector:")}
    yc_refs = {ref for ref in refs if ref.startswith("yc:")}
    events_by_id: dict[str, dict[str, Any]] = {}

    repo_data = pl.concat(repo_frames, how="vertical_relaxed")
    _require_columns(
        repo_data,
        {"actor_login", "created_at", "repo_name"},
        label="events/repo_creations/*.parquet",
    )
    for row in repo_data.select(["actor_login", "created_at", "repo_name"]).to_dicts():
        if not row.get("actor_login") or row.get("created_at") is None or not row.get("repo_name"):
            continue
        login = str(row["actor_login"])
        repo_name = str(row["repo_name"])
        created_at = _datetime_value(row["created_at"])
        citation_ref = f"repo:{repo_name}:{created_at.strftime('%Y-%m-%d %H:%M:%S')}"
        if login not in cohort and citation_ref not in repo_refs:
            continue
        evidence_id = (
            citation_ref
            if citation_ref in repo_refs
            else _stable_id("re", login, created_at.isoformat(), repo_name)
        )
        _add_event(
            events_by_id,
            {
                "evidence_id": evidence_id,
                "gh_login": login,
                "ts": created_at.isoformat(),
                "event_type": "repo_created",
                "repo_name": repo_name,
                "detail": f"Created public repository {repo_name}",
                "url": f"https://github.com/{repo_name}",
            },
        )

    monthly_data = pl.concat(monthly_frames, how="vertical_relaxed")
    _require_columns(
        monthly_data,
        {"actor_login", "month", "event_count"},
        label="events/monthly_agg/*.parquet",
    )
    monthly_counts: dict[tuple[str, str], int] = defaultdict(int)
    for row in monthly_data.select(["actor_login", "month", "event_count"]).to_dicts():
        if not row.get("actor_login") or row.get("month") is None:
            continue
        login = str(row["actor_login"])
        if login not in cohort or row.get("event_count") is None:
            continue
        monthly_counts[(login, _date_text(row["month"])[:7])] += int(row["event_count"])
    for (login, month), count in sorted(monthly_counts.items()):
        if count <= 0:
            continue
        month_date = date.fromisoformat(f"{month}-01")
        ts = datetime(month_date.year, month_date.month, 1, tzinfo=timezone.utc)
        label = ts.strftime("%b %Y")
        _add_event(
            events_by_id,
            {
                "evidence_id": _stable_id("am", login, month),
                "gh_login": login,
                "ts": ts.isoformat(),
                "event_type": "activity_month",
                "repo_name": "",
                "detail": (
                    f"{count} public GitHub events in {label} "
                    "(derived from GH Archive)"
                ),
                "url": f"https://github.com/{login}",
            },
        )

    candidate_detection = {
        str(row["gh_login"]): row.get("first_detection_month")
        for row in candidate_rows
        if row.get("first_detection_month")
    }
    attribution_detection: dict[str, str] = {}
    _require_columns(
        attributions,
        {"login", "crossing_month"},
        label="scores/attributions.parquet",
    )
    for row in attributions.select(["login", "crossing_month"]).to_dicts():
        if row.get("login") and row.get("crossing_month") is not None:
            login = str(row["login"])
            month = _date_text(row["crossing_month"])
            previous = attribution_detection.get(login)
            if previous is None or month < previous:
                attribution_detection[login] = month
    for evidence_id in sorted(detector_refs):
        login = evidence_id.removeprefix("detector:")
        detection_value = (
            candidate_detection.get(login)
            or attribution_detection.get(login)
            or _memo_detection_month(memos, login)
        )
        if not detection_value:
            continue
        detection_date = date.fromisoformat(str(detection_value)[:10])
        ts = datetime(
            detection_date.year, detection_date.month, detection_date.day, tzinfo=timezone.utc
        )
        _add_event(
            events_by_id,
            {
                "evidence_id": evidence_id,
                "gh_login": login,
                "ts": ts.isoformat(),
                "event_type": "detector_crossing",
                "repo_name": "",
                "detail": f"Detector crossing recorded for {login} in {ts.strftime('%b %Y')}",
                "url": f"https://github.com/{login}",
            },
        )

    _require_columns(
        founders,
        {"gh_login", "slug", "batch", "batch_start_date", "gh_confidence"},
        label="labels/founders.parquet",
    )
    founder_rows = founders.select(
        ["gh_login", "slug", "batch", "batch_start_date", "gh_confidence"]
    ).to_dicts()
    memo_login_by_yc_ref: dict[str, str] = {}
    for memo in memos.values():
        primary_login = str(memo["founder_logins"][0])
        for ref in _memo_refs({"memo": memo}):
            if ref.startswith("yc:"):
                memo_login_by_yc_ref[ref] = primary_login
    for evidence_id in sorted(yc_refs):
        slug = evidence_id.removeprefix("yc:")
        primary_login = memo_login_by_yc_ref[evidence_id]
        matches = [
            row
            for row in founder_rows
            if str(row.get("slug") or "") == slug
            and (not primary_login or str(row.get("gh_login") or "") == primary_login)
            and row.get("batch_start_date") is not None
            and row.get("batch")
        ]
        if not matches:
            continue
        matches.sort(
            key=lambda row: (
                -(float(row.get("gh_confidence") or 0.0)),
                _date_text(row["batch_start_date"]),
            )
        )
        founder = matches[0]
        login = str(founder.get("gh_login") or primary_login)
        batch = str(founder["batch"])
        batch_date = date.fromisoformat(_date_text(founder["batch_start_date"])[:10])
        ts = datetime(batch_date.year, batch_date.month, batch_date.day, tzinfo=timezone.utc)
        _add_event(
            events_by_id,
            {
                "evidence_id": evidence_id,
                "gh_login": login,
                "ts": ts.isoformat(),
                "event_type": "yc_listing",
                "repo_name": "",
                "detail": f"Accepted to Y Combinator {batch}",
                "url": f"https://www.ycombinator.com/companies/{slug}",
            },
        )

    return sorted(
        events_by_id.values(),
        key=lambda event: (event["gh_login"], event["ts"], event["evidence_id"]),
    )


def _build_profiles(
    candidates: Sequence[Mapping[str, Any]], founders: pl.DataFrame
) -> dict[str, dict[str, str]]:
    founder_details: dict[str, Mapping[str, Any]] = {}
    if {"gh_login", "gh_confidence", "founder_name", "company"} <= set(founders.columns):
        for row in founders.select(
            ["gh_login", "gh_confidence", "founder_name", "company"]
        ).sort("gh_confidence", descending=True).to_dicts():
            login_value = row.get("gh_login")
            if login_value:
                founder_details.setdefault(str(login_value), row)
    profiles: dict[str, dict[str, str]] = {}
    for candidate in candidates:
        login = str(candidate["gh_login"])
        founder = founder_details.get(login, {})
        values = {
            "name": candidate.get("founder_name") or founder.get("founder_name"),
            "company": candidate.get("company") or founder.get("company"),
            "login": login,
        }
        profiles[login] = {
            key: str(value) for key, value in values.items() if value not in (None, "")
        }
    return profiles


def _load_memos(path: Path) -> tuple[list[Path], dict[str, dict[str, Any]]]:
    if not path.is_dir():
        raise IntegrationBuildError(f"memo directory not found: {path}")
    memo_paths = sorted(path.glob("*.json"))
    if not memo_paths:
        raise IntegrationBuildError(f"no memo JSON files found in {path}")
    documents: dict[str, dict[str, Any]] = {}
    for memo_path in memo_paths:
        try:
            document = json.loads(memo_path.read_text(encoding="utf-8"))
            Memo.model_validate(document)
        except (OSError, json.JSONDecodeError, ValidationError) as error:
            raise IntegrationBuildError(f"invalid memo {memo_path}: {error}") from error
        if not isinstance(document, dict):
            raise IntegrationBuildError(f"memo must be a JSON object: {memo_path}")
        documents[memo_path.stem] = document
    return memo_paths, documents


def _memo_refs(memos: Mapping[str, Mapping[str, Any]]) -> set[str]:
    return {
        str(ref)
        for memo in memos.values()
        for claim in memo["claims"].values()
        for ref in claim["evidence_refs"]
    }


def _memo_detection_month(
    memos: Mapping[str, Mapping[str, Any]], login: str
) -> str | None:
    """Recover a detector month explicitly stated by a detector-citing memo claim."""

    month_numbers = {
        name: number
        for number, name in enumerate(
            (
                "January",
                "February",
                "March",
                "April",
                "May",
                "June",
                "July",
                "August",
                "September",
                "October",
                "November",
                "December",
            ),
            start=1,
        )
    }
    pattern = re.compile(
        r"\b(" + "|".join(month_numbers) + r")\s+(20\d{2})\b",
        flags=re.IGNORECASE,
    )
    detector_ref = f"detector:{login}"
    for memo in memos.values():
        if login not in {str(value) for value in memo["founder_logins"]}:
            continue
        for claim in memo["claims"].values():
            if detector_ref not in claim["evidence_refs"]:
                continue
            claim_text = str(claim["text"])
            normalized_text = claim_text.casefold()
            if "detected" not in normalized_text and not (
                "detector" in normalized_text and "identified" in normalized_text
            ):
                continue
            match = pattern.search(claim_text)
            if match:
                canonical_month = match.group(1).capitalize()
                return f"{match.group(2)}-{month_numbers[canonical_month]:02d}-01"
    return None


def _read_parquet(path: Path) -> pl.DataFrame:
    if not path.is_file():
        raise IntegrationBuildError(f"required source file not found: {path}")
    try:
        return pl.read_parquet(path)
    except Exception as error:
        raise IntegrationBuildError(f"cannot read parquet source {path}: {error}") from error


def _require_columns(frame: pl.DataFrame, required: Iterable[str], *, label: str) -> None:
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise IntegrationBuildError(f"{label} is missing columns: {', '.join(missing)}")


def _json_ready(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value


def _date_text(value: Any) -> str:
    return value.isoformat() if isinstance(value, (date, datetime)) else str(value)


def _datetime_value(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def _stable_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}-{digest}"


def _add_event(events: dict[str, dict[str, Any]], event: dict[str, Any]) -> None:
    evidence_id = str(event["evidence_id"])
    previous = events.get(evidence_id)
    if previous is not None and previous != event:
        raise IntegrationBuildError(f"evidence_id collision for {evidence_id}")
    events[evidence_id] = event


def _write_rows(path: Path, stem: str, rows: Sequence[Mapping[str, Any]]) -> None:
    json_rows = _json_ready(list(rows))
    (path / f"{stem}.json").write_text(
        json.dumps(json_rows, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    try:
        pl.DataFrame(rows).write_parquet(path / f"{stem}.parquet")
    except Exception as error:
        raise IntegrationBuildError(f"cannot write {stem}.parquet: {error}") from error


def _publish_directory(stage: Path, out: Path) -> None:
    backup: Path | None = None
    if out.exists():
        backup = Path(tempfile.mkdtemp(prefix=f".{out.name}.backup.", dir=out.parent))
        backup.rmdir()
        os.replace(out, backup)
    try:
        os.replace(stage, out)
    except Exception:
        if backup is not None and backup.exists() and not out.exists():
            os.replace(backup, out)
        raise
    if backup is not None:
        shutil.rmtree(backup)
