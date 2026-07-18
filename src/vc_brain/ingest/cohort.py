"""Read-only snapshots of the concurrently produced founder-label inputs."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import polars as pl

from vc_brain.ingest.contracts import (
    CONFIDENT_GITHUB_THRESHOLD,
    FOUNDERS_PATH,
    FOUNDERS_RAW_PATH,
    FOUNDERS_RESOLVED_PATH,
)


class CohortUnavailableError(RuntimeError):
    """No complete-enough label snapshot is available for cohort extraction."""


def subtract_months(value: date, months: int) -> date:
    total = value.year * 12 + value.month - 1 - months
    year, zero_month = divmod(total, 12)
    month = zero_month + 1
    month_lengths = (31, 29 if year % 4 == 0 and (year % 100 or year % 400 == 0) else 28,
                     31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    return date(year, month, min(value.day, month_lengths[month - 1]))


def normalize_domain(website: str | None) -> str | None:
    if not website:
        return None
    text = website.strip().lower()
    parsed = urlparse(text if "://" in text else f"https://{text}")
    host = (parsed.hostname or "").removeprefix("www.").rstrip(".")
    return host or None


def _read_resolution_snapshot(path: Path) -> pl.DataFrame:
    if path.exists():
        return pl.read_parquet(path)
    checkpoint = path.with_suffix(".checkpoint.json")
    if not checkpoint.exists():
        return pl.DataFrame()
    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    rows = payload.get("rows", []) if isinstance(payload, dict) else []
    return pl.DataFrame(rows) if rows else pl.DataFrame()


def load_founder_snapshot(
    *,
    founders_path: Path = FOUNDERS_PATH,
    raw_path: Path = FOUNDERS_RAW_PATH,
    resolved_path: Path = FOUNDERS_RESOLVED_PATH,
) -> pl.DataFrame:
    """Read each mutable input once and return a self-contained in-memory snapshot."""
    if founders_path.exists():
        frame = pl.read_parquet(founders_path)
    elif raw_path.exists():
        raw = pl.read_parquet(raw_path)
        resolved = _read_resolution_snapshot(resolved_path)
        if resolved.is_empty():
            raise CohortUnavailableError(
                "founders_raw exists but no resolution checkpoint with GitHub logins exists"
            )
        required = {"_founder_key", "gh_login", "gh_confidence"}
        if not required.issubset(resolved.columns):
            raise CohortUnavailableError("resolution checkpoint has an incompatible schema")
        frame = raw.join(
            resolved.select([c for c in resolved.columns if c in required]),
            on="_founder_key",
            how="inner",
        ).with_columns(
            pl.col("batch_start_date")
            .map_elements(
                lambda value: subtract_months(value, 12) if value else None,
                return_dtype=pl.Date,
            )
            .alias("t_cutoff")
        )
    else:
        raise CohortUnavailableError("no founder labels or raw founder checkpoint exists")
    required_columns = {
        "gh_login",
        "gh_confidence",
        "t_cutoff",
        "company_website",
    }
    missing = required_columns - set(frame.columns)
    if missing:
        raise CohortUnavailableError(
            f"founder snapshot is missing required columns: {sorted(missing)}"
        )
    return frame


def labeled_logins(founders: pl.DataFrame) -> set[str]:
    """Return every non-empty labeled login, regardless of confidence."""
    return {
        str(value).lower()
        for value in founders.get_column("gh_login").drop_nulls().to_list()
        if str(value).strip()
    }


def confident_cohort(
    founders: pl.DataFrame,
    *,
    threshold: float = CONFIDENT_GITHUB_THRESHOLD,
) -> pl.DataFrame:
    """Collapse duplicate labels to one conservative cutoff per GitHub actor."""
    selected = (
        founders.filter(
            pl.col("gh_login").is_not_null()
            & (pl.col("gh_login").str.strip_chars() != "")
            & (pl.col("gh_confidence") >= threshold)
            & pl.col("t_cutoff").is_not_null()
        )
        .with_columns(
            pl.col("gh_login").str.to_lowercase().alias("actor_login"),
            pl.col("company_website")
            .map_elements(normalize_domain, return_dtype=pl.String)
            .alias("company_domain"),
        )
        .select("actor_login", "t_cutoff", "company_domain")
    )
    if selected.is_empty():
        return pl.DataFrame(
            schema={
                "actor_login": pl.String,
                "t_cutoff": pl.Date,
                "company_domains": pl.List(pl.String),
            }
        )
    return (
        selected.group_by("actor_login")
        .agg(
            pl.col("t_cutoff").min(),
            pl.col("company_domain").drop_nulls().unique().alias("company_domains"),
        )
        .sort("actor_login")
    )


def actor_records(cohort: pl.DataFrame) -> list[dict[str, object]]:
    return cohort.select("actor_login", "t_cutoff").to_dicts()
