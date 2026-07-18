"""Small, cached client for the shared ClickHouse playground."""

from __future__ import annotations

import hashlib
import io
import logging
import threading
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TypeVar

import httpx
import polars as pl
from tenacity import Retrying, retry_if_exception_type, stop_after_attempt
from tenacity import wait_random_exponential

from vc_brain.ingest.contracts import (
    ACTOR_BATCH_SIZE,
    CH_CACHE_DIR,
    RESULT_ROW_GUARD,
)
from vc_brain.ingest.storage import atomic_write_parquet

LOGGER = logging.getLogger(__name__)
PLAYGROUND_URL = "https://play.clickhouse.com/"
_QUERY_SLOTS = threading.BoundedSemaphore(2)
_RATE_LOCK = threading.Lock()
_LAST_QUERY_STARTED = 0.0
T = TypeVar("T")


class RetryableClickHouseError(RuntimeError):
    """The playground returned a transient response."""


class ClickHouseQueryError(RuntimeError):
    """A ClickHouse query failed with a non-retryable response."""


class ResultSizeLimitError(RuntimeError):
    """A single-actor result cannot be reduced by batch splitting."""


def _sql_with_format(sql: str) -> str:
    normalized = sql.strip().rstrip(";")
    if normalized.upper().endswith("FORMAT TSVWITHNAMES"):
        return normalized
    return f"{normalized}\nFORMAT TSVWithNames"


def _parse_tsv(content: bytes) -> pl.DataFrame:
    if not content.strip():
        return pl.DataFrame()
    return pl.read_csv(
        io.BytesIO(content),
        separator="\t",
        null_values="\\N",
        try_parse_dates=True,
        infer_schema_length=10_000,
        truncate_ragged_lines=False,
    )


class ClickHouseClient:
    """Synchronous, retrying client with content-addressed parquet caching."""

    def __init__(
        self,
        *,
        cache_dir: Path = CH_CACHE_DIR,
        client: httpx.Client | None = None,
        timeout_seconds: float = 180.0,
        minimum_interval_seconds: float = 0.25,
        max_attempts: int = 5,
        result_row_guard: int = RESULT_ROW_GUARD,
    ) -> None:
        if timeout_seconds <= 0 or minimum_interval_seconds < 0 or max_attempts < 1:
            raise ValueError("Invalid ClickHouse timing or retry configuration")
        if result_row_guard < 1:
            raise ValueError("result_row_guard must be positive")
        self.cache_dir = cache_dir
        self.minimum_interval_seconds = minimum_interval_seconds
        self.max_attempts = max_attempts
        self.result_row_guard = result_row_guard
        self._owns_client = client is None
        self.client = client or httpx.Client(timeout=httpx.Timeout(timeout_seconds))

    def __enter__(self) -> ClickHouseClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def cache_path(self, sql: str) -> Path:
        digest = hashlib.sha256(_sql_with_format(sql).encode("utf-8")).hexdigest()
        return self.cache_dir / f"{digest}.parquet"

    def _request(self, sql: str) -> bytes:
        global _LAST_QUERY_STARTED
        with _QUERY_SLOTS:
            with _RATE_LOCK:
                delay = self.minimum_interval_seconds - (
                    time.monotonic() - _LAST_QUERY_STARTED
                )
                if delay > 0:
                    time.sleep(delay)
                _LAST_QUERY_STARTED = time.monotonic()
            response = self.client.post(
                PLAYGROUND_URL,
                params={"user": "play"},
                content=_sql_with_format(sql).encode("utf-8"),
                headers={"Content-Type": "text/plain; charset=utf-8"},
            )
        if response.status_code == 429 or response.status_code >= 500:
            raise RetryableClickHouseError(
                f"ClickHouse playground returned HTTP {response.status_code}"
            )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise ClickHouseQueryError(
                f"ClickHouse query rejected with HTTP {response.status_code}"
            ) from error
        return response.content

    def query(self, sql: str) -> pl.DataFrame:
        """Return a query result, reading/writing the SQL-hash cache atomically."""
        path = self.cache_path(sql)
        if path.exists():
            return pl.read_parquet(path)
        retrying = Retrying(
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_random_exponential(multiplier=0.5, max=8),
            retry=retry_if_exception_type(
                (httpx.TransportError, RetryableClickHouseError)
            ),
            reraise=True,
        )
        content = retrying(self._request, sql)
        frame = _parse_tsv(content)
        atomic_write_parquet(frame, path)
        LOGGER.info("ClickHouse query cached rows=%d path=%s", frame.height, path)
        return frame

    def query_actor_batch(
        self,
        actors: Sequence[T],
        sql_builder: Callable[[Sequence[T]], str],
    ) -> pl.DataFrame:
        """Query actors together and bisect any result reaching the row guard."""
        if not actors:
            return pl.DataFrame()
        frame = self.query(sql_builder(actors))
        if frame.height < self.result_row_guard:
            return frame
        if len(actors) == 1:
            raise ResultSizeLimitError(
                "Single-actor ClickHouse result reached the configured row guard"
            )
        middle = len(actors) // 2
        LOGGER.warning(
            "Splitting oversized actor batch actors=%d rows=%d",
            len(actors),
            frame.height,
        )
        return pl.concat(
            [
                self.query_actor_batch(actors[:middle], sql_builder),
                self.query_actor_batch(actors[middle:], sql_builder),
            ],
            how="diagonal_relaxed",
        )

    def query_actor_batches(
        self,
        actors: Sequence[T],
        sql_builder: Callable[[Sequence[T]], str],
        *,
        batch_size: int = ACTOR_BATCH_SIZE,
    ) -> pl.DataFrame:
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        frames = [
            self.query_actor_batch(actors[start : start + batch_size], sql_builder)
            for start in range(0, len(actors), batch_size)
        ]
        return (
            pl.concat(frames, how="diagonal_relaxed")
            if frames
            else pl.DataFrame()
        )


def query(sql: str) -> pl.DataFrame:
    """Convenience entry point matching the spec's tiny-client contract."""
    with ClickHouseClient() as client:
        return client.query(sql)
