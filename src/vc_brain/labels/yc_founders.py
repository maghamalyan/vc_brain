"""Stage 2: extract founders from cached YC company pages."""

import html
import json
import logging
import re
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
import polars as pl
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt
from tenacity import wait_random_exponential

from vc_brain.labels.contracts import (
    COMPANIES_PATH,
    FOUNDER_RAW_SCHEMA,
    FOUNDERS_RAW_PATH,
    YC_CACHE_DIR,
)
from vc_brain.labels.identity import founder_key
from vc_brain.labels.storage import (
    atomic_write_json,
    atomic_write_parquet,
    atomic_write_text,
    checkpoint_path,
    frame_from_rows,
    read_checkpoint,
)
from vc_brain.labels.yc_companies import USER_AGENT

LOGGER = logging.getLogger(__name__)
COMPANY_PAGE_URL = "https://www.ycombinator.com/companies/{slug}"
MAX_REQUESTS_PER_SECOND = 3.0
CHECKPOINT_INTERVAL = 100
PROGRESS_INTERVAL = 50
MAX_CONSECUTIVE_FAILURES = 20

_DATA_PAGE_RE = re.compile(r'data-page="(.*?)"', re.DOTALL)


class FounderPageError(RuntimeError):
    """A permanent fetch or parse failure for one YC company page."""


class RetryableFounderPageError(FounderPageError):
    """A transient YC company-page response eligible for retry."""


class FounderExtractionAbortedError(RuntimeError):
    """The consecutive-failure safety threshold stopped extraction."""


class RequestRateLimiter:
    def __init__(self, requests_per_second: float = MAX_REQUESTS_PER_SECOND) -> None:
        self.minimum_interval = 1.0 / requests_per_second
        self.last_request_at: float | None = None

    def wait(self) -> None:
        now = time.monotonic()
        if self.last_request_at is not None:
            delay = self.minimum_interval - (now - self.last_request_at)
            if delay > 0:
                time.sleep(delay)
        self.last_request_at = time.monotonic()


def find_founders(value: object) -> list[dict[str, Any]] | None:
    if isinstance(value, dict):
        founders = value.get("founders")
        if isinstance(founders, list):
            return [item for item in founders if isinstance(item, dict)]
        for child in value.values():
            found = find_founders(child)
            if found is not None:
                return found
    elif isinstance(value, list):
        for child in value:
            found = find_founders(child)
            if found is not None:
                return found
    return None


def parse_founders(page_html: str) -> list[dict[str, Any]]:
    """Parse founder objects from the HTML-escaped Inertia data-page value."""
    match = _DATA_PAGE_RE.search(page_html)
    if not match:
        raise FounderPageError("YC page has no data-page attribute")
    try:
        page_data = json.loads(html.unescape(match.group(1)))
    except json.JSONDecodeError as error:
        raise FounderPageError("YC page has invalid data-page JSON") from error
    founders = find_founders(page_data)
    if founders is None:
        raise FounderPageError("YC page data has no founders key")
    for founder in founders:
        full_name = founder.get("full_name")
        if not isinstance(full_name, str) or not full_name.strip():
            raise FounderPageError("YC founder is missing a non-empty full_name")
    return founders


class YCPageFetcher:
    """Single-client, three-RPS YC page fetcher with bounded retries."""

    def __init__(
        self,
        client: httpx.Client | None = None,
        rate_limiter: RequestRateLimiter | None = None,
    ) -> None:
        self.owns_client = client is None
        self.client = client or httpx.Client(
            headers={"User-Agent": USER_AGENT}, timeout=httpx.Timeout(30.0)
        )
        self.rate_limiter = rate_limiter or RequestRateLimiter()

    def __enter__(self) -> "YCPageFetcher":
        return self

    def __exit__(self, *_args: object) -> None:
        if self.owns_client:
            self.client.close()

    def fetch(self, slug: str) -> str:
        url = COMPANY_PAGE_URL.format(slug=slug)
        for attempt in Retrying(
            retry=retry_if_exception_type(
                (httpx.TransportError, RetryableFounderPageError)
            ),
            stop=stop_after_attempt(5),
            wait=wait_random_exponential(multiplier=1, max=30),
            reraise=True,
        ):
            with attempt:
                self.rate_limiter.wait()
                response = self.client.get(url)
                if response.status_code == 429 or response.status_code >= 500:
                    raise RetryableFounderPageError(
                        f"YC company page returned HTTP {response.status_code}"
                    )
                if response.status_code >= 400:
                    raise FounderPageError(
                        f"YC company page returned HTTP {response.status_code}"
                    )
                return response.text
        raise AssertionError("unreachable")


def founder_row(company: dict[str, Any], founder: dict[str, Any]) -> dict[str, Any]:
    founder_name = founder["full_name"].strip()
    user_id = founder.get("user_id")
    return {
        "_founder_key": founder_key(company["slug"], founder_name, user_id),
        "founder_name": founder_name,
        "company": company["name"],
        "slug": company["slug"],
        "batch": company["batch"],
        "batch_year": company["batch_year"],
        "batch_start_date": company["batch_start_date"],
        "company_website": company["website"],
        "one_liner": company["one_liner"],
        "team_size": company["team_size"],
        "status": company["status"],
        "linkedin_url": optional_string(founder.get("linkedin_url")),
        "twitter_url": optional_string(founder.get("twitter_url")),
        "founder_bio": optional_string(founder.get("founder_bio")),
        "title": optional_string(founder.get("title")),
        "user_id": optional_string(user_id),
    }


def optional_string(value: object) -> str | None:
    return None if value is None else str(value)


def load_existing_founders(output_path: Path) -> list[dict[str, Any]]:
    if not output_path.exists():
        return []
    return pl.read_parquet(output_path).select(list(FOUNDER_RAW_SCHEMA)).to_dicts()


def save_founder_checkpoint(
    rows: list[dict[str, Any]],
    processed_slugs: set[str],
    failed_slugs: dict[str, str],
    output_path: Path,
) -> None:
    frame = frame_from_rows(rows, FOUNDER_RAW_SCHEMA).unique(
        subset=["_founder_key"], keep="last", maintain_order=True
    )
    atomic_write_parquet(frame, output_path)
    atomic_write_json(
        {
            "processed_companies": len(processed_slugs),
            "processed_slugs": sorted(processed_slugs),
            "founder_rows": frame.height,
            "failed_slugs": failed_slugs,
        },
        checkpoint_path(output_path),
    )


def extract_founders(
    *,
    companies_path: Path = COMPANIES_PATH,
    output_path: Path = FOUNDERS_RAW_PATH,
    pages_dir: Path = YC_CACHE_DIR / "pages",
    min_batch_year: int = 2012,
    max_companies: int | None = None,
    fetch_page: Callable[[str], str] | None = None,
) -> pl.DataFrame:
    """Extract founders in descending batch order with atomic resume points."""
    if min_batch_year < 2012:
        raise ValueError("Founder extraction supports batches from 2012 onward")
    if not companies_path.exists():
        raise FileNotFoundError(
            f"Missing {companies_path}; run the companies stage first"
        )

    companies = (
        pl.read_parquet(companies_path)
        .filter(pl.col("batch_year") >= min_batch_year)
        .sort("batch_start_date", descending=True, nulls_last=True)
    )
    state = read_checkpoint(checkpoint_path(output_path))
    processed_slugs = set(state.get("processed_slugs", []))
    failed_slugs = dict(state.get("failed_slugs", {}))
    rows = load_existing_founders(output_path)
    pending = [
        row for row in companies.to_dicts() if row["slug"] not in processed_slugs
    ]
    if max_companies is not None:
        pending = pending[:max_companies]

    pages_dir.mkdir(parents=True, exist_ok=True)
    started_at = time.monotonic()
    completed_this_run = 0
    consecutive_failures = 0

    def process(fetcher: Callable[[str], str]) -> None:
        nonlocal completed_this_run, consecutive_failures
        for company in pending:
            slug = company["slug"]
            page_path = pages_dir / f"{slug}.html"
            try:
                if page_path.exists():
                    page_html = page_path.read_text(encoding="utf-8")
                else:
                    page_html = fetcher(slug)
                    atomic_write_text(page_html, page_path)
                founders = parse_founders(page_html)
            except (FounderPageError, httpx.HTTPError) as error:
                consecutive_failures += 1
                failed_slugs[slug] = type(error).__name__
                LOGGER.warning(
                    "Founder extraction failed slug=%s consecutive_failures=%d "
                    "error_type=%s",
                    slug,
                    consecutive_failures,
                    type(error).__name__,
                )
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    raise FounderExtractionAbortedError(
                        "Founder extraction stopped after 20 consecutive failures; "
                        f"last_slug={slug}"
                    ) from error
                continue

            consecutive_failures = 0
            failed_slugs.pop(slug, None)
            rows.extend(founder_row(company, founder) for founder in founders)
            processed_slugs.add(slug)
            completed_this_run += 1
            if completed_this_run % PROGRESS_INTERVAL == 0:
                elapsed = max(time.monotonic() - started_at, 0.001)
                LOGGER.info(
                    "Founder progress companies=%d total_checkpointed=%d "
                    "founders=%d rate=%.2f_companies_per_second",
                    completed_this_run,
                    len(processed_slugs),
                    len(rows),
                    completed_this_run / elapsed,
                )
            if completed_this_run % CHECKPOINT_INTERVAL == 0:
                save_founder_checkpoint(
                    rows, processed_slugs, failed_slugs, output_path
                )
                LOGGER.info(
                    "Founder checkpoint companies=%d founders=%d path=%s",
                    len(processed_slugs),
                    len(rows),
                    output_path,
                )

    try:
        if fetch_page is not None:
            process(fetch_page)
        else:
            with YCPageFetcher() as client:
                process(client.fetch)
    except BaseException:
        save_founder_checkpoint(rows, processed_slugs, failed_slugs, output_path)
        raise

    save_founder_checkpoint(rows, processed_slugs, failed_slugs, output_path)
    frame = pl.read_parquet(output_path)
    log = LOGGER.warning if failed_slugs else LOGGER.info
    log(
        "Founder extraction pass complete checkpointed_companies=%d rows=%d "
        "pending_failures=%d path=%s",
        len(processed_slugs),
        frame.height,
        len(failed_slugs),
        output_path,
    )
    return frame
