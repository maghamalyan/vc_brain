"""Stage 1: cache and normalize the public YC company list."""

import json
import logging
import re
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import httpx
import polars as pl
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt
from tenacity import wait_random_exponential

from vc_brain.labels.contracts import (
    COMPANIES_PATH,
    COMPANY_SCHEMA,
    YC_CACHE_DIR,
)
from vc_brain.labels.storage import (
    atomic_write_parquet,
    atomic_write_text,
    frame_from_rows,
)

LOGGER = logging.getLogger(__name__)
COMPANIES_URL = "https://yc-oss.github.io/api/companies/all.json"
USER_AGENT = "vc-brain-research/0.1"
SEASONS = {
    "winter": (1, 5),
    "spring": (4, 1),
    "summer": (6, 1),
    "fall": (9, 1),
    "w": (1, 5),
    "sp": (4, 1),
    "s": (6, 1),
    "f": (9, 1),
}


class RetryableCompanyListError(RuntimeError):
    """A transient company-list download failure."""


class InvalidCompanyListError(RuntimeError):
    """The upstream YC company list violates its required schema."""


def batch_start_date(batch: str | None) -> date | None:
    """Map YC batch labels to the season's canonical start date."""
    if not batch:
        return None
    value = batch.strip()
    match = re.fullmatch(
        r"(?i)(winter|spring|summer|fall)\s+(\d{4})", value
    )
    if match:
        season, year_text = match.groups()
    else:
        match = re.fullmatch(r"(?i)(W|SP|S|F)\s*'?([0-9]{2}|[0-9]{4})", value)
        if not match:
            return None
        season, year_text = match.groups()
    year = int(year_text)
    if year < 100:
        year += 2000
    month, day = SEASONS[season.lower()]
    return date(year, month, day)


def batch_year(batch: str | None) -> int | None:
    start = batch_start_date(batch)
    return start.year if start else None


def download_company_list() -> str:
    with httpx.Client(
        headers={"User-Agent": USER_AGENT}, timeout=httpx.Timeout(30.0)
    ) as client:
        for attempt in Retrying(
            retry=retry_if_exception_type(
                (httpx.TransportError, RetryableCompanyListError)
            ),
            stop=stop_after_attempt(5),
            wait=wait_random_exponential(multiplier=1, max=30),
            reraise=True,
        ):
            with attempt:
                response = client.get(COMPANIES_URL)
                if response.status_code == 429 or response.status_code >= 500:
                    raise RetryableCompanyListError(
                        f"YC company list returned HTTP {response.status_code}"
                    )
                response.raise_for_status()
                return response.text
    raise AssertionError("unreachable")


def string_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item is not None]
    if value is None:
        return []
    return [str(value)]


def normalize_companies(payload: object) -> pl.DataFrame:
    if not isinstance(payload, list):
        raise InvalidCompanyListError("YC company list must be a JSON array")
    rows: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        batch = optional_string(item.get("batch"))
        rows.append(
            {
                "name": optional_string(item.get("name")),
                "slug": optional_string(item.get("slug")),
                "batch": batch,
                "batch_year": batch_year(batch),
                "batch_start_date": batch_start_date(batch),
                "website": optional_string(item.get("website")),
                "one_liner": optional_string(item.get("one_liner")),
                "long_description": optional_string(item.get("long_description")),
                "team_size": item.get("team_size"),
                "status": optional_string(item.get("status")),
                "industries": string_list(item.get("industries")),
                "regions": string_list(item.get("regions")),
                "launched_at": optional_string(item.get("launched_at")),
                "url": optional_string(item.get("url")),
            }
        )
    frame = frame_from_rows(rows, COMPANY_SCHEMA)
    if frame.get_column("slug").is_null().any():
        raise InvalidCompanyListError("YC company list contains a missing slug")
    return frame.unique(subset=["slug"], keep="first", maintain_order=True)


def optional_string(value: object) -> str | None:
    return None if value is None else str(value)


def build_companies(
    *,
    cache_path: Path = YC_CACHE_DIR / "all.json",
    output_path: Path = COMPANIES_PATH,
    downloader: Callable[[], str] | None = None,
) -> pl.DataFrame:
    """Build companies.parquet, using the raw cache whenever it exists."""
    if cache_path.exists():
        raw = cache_path.read_text(encoding="utf-8")
        LOGGER.info("Using cached YC company list path=%s", cache_path)
    else:
        raw = (downloader or download_company_list)()
        atomic_write_text(raw, cache_path)
        LOGGER.info("Cached YC company list path=%s", cache_path)
    payload = json.loads(raw)
    frame = normalize_companies(payload)
    atomic_write_parquet(frame, output_path)
    LOGGER.info("Wrote companies rows=%d path=%s", frame.height, output_path)
    return frame
