"""Content-addressed OpenRouter pipeline for quarterly text annotations."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import random
import re
import time
from collections import deque
from collections.abc import Mapping, Sequence
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import httpx
import polars as pl
from dotenv import load_dotenv
from pydantic import ValidationError

from vc_brain.ingest.storage import atomic_write_parquet, atomic_write_text
from vc_brain.semantics.contracts import (
    ANNOTATION_CACHE_DIR,
    ANNOTATION_RUN_SUMMARY_PATH,
    ANNOTATIONS_PATH,
    TEXT_ITEMS_PATH,
)
from vc_brain.semantics.schema import SemanticAnnotation

LOGGER = logging.getLogger(__name__)
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
PROMPT_VERSION = "a3-v2-reasoning-retries"
CURRENT_TEXT_BUDGET = 4_500
EARLIER_TEXT_BUDGET = 1_500
MAX_OUTPUT_TOKENS = 2_000
REASONING = {"effort": "low"}
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_CONCURRENCY = 8
DEFAULT_PROGRESS_EVERY = 200
FAILURE_WINDOW_SIZE = 500
MAX_FAILURE_RATE = 0.05

SYSTEM_PROMPT = """You are a reproducible measurement instrument for longitudinal GitHub work.
Return JSON matching the supplied schema. Use only the supplied event-time text.

Rules:
- Analyze CURRENT QUARTER for every field. EARLIER CONTEXT is only comparative
  context for domain_shift; never treat it as current-quarter evidence.
- Every non-null field must cite one or more CURRENT QUARTER item_index values.
- productization_markers, commercial_language, seriousness, and domain_shift use
  integer scales from 0 through 3. Zero is an observed judgment and still needs a
  current-item citation.
- domain_shift compares the current work with the earlier bundles: 0 is the same
  territory and 3 is clear redeployment into a different domain or stack.
- stated_founding_intent is none, implicit, or explicit. Include a verbatim quote
  only for explicit intent; do not infer intent from generic project enthusiasm.
- Output JSON only, without markdown or commentary.
"""


@dataclass(frozen=True)
class TokenUsage:
    """Provider-reported token usage, including reasoning when exposed."""

    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0

    def __add__(self, other: TokenUsage) -> TokenUsage:
        return TokenUsage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            reasoning_tokens=self.reasoning_tokens + other.reasoning_tokens,
        )


@dataclass(frozen=True)
class ProviderResponse:
    raw: dict[str, Any]
    usage: TokenUsage
    reasoning_present: bool
    finish_reason: str | None


@dataclass(frozen=True)
class AnnotationOutcome:
    annotation: SemanticAnnotation
    cache_hit: bool
    usage: TokenUsage
    attempts: int
    reasoning_present: bool
    content_hash: str


@dataclass
class AnnotationRunStats:
    total_bundles: int
    completed: int = 0
    annotated: int = 0
    failed: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    provider_attempts: int = 0
    reasoning_responses: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    aborted: bool = False

    def record_success(self, outcome: AnnotationOutcome) -> None:
        self.completed += 1
        self.annotated += 1
        self.cache_hits += int(outcome.cache_hit)
        self.cache_misses += int(not outcome.cache_hit)
        self.provider_attempts += 0 if outcome.cache_hit else outcome.attempts
        self.reasoning_responses += int(outcome.reasoning_present)
        self.input_tokens += outcome.usage.input_tokens
        self.output_tokens += outcome.usage.output_tokens
        self.reasoning_tokens += outcome.usage.reasoning_tokens

    def record_failure(self) -> None:
        self.completed += 1
        self.failed += 1
        self.cache_misses += 1


ANNOTATION_SCHEMA: dict[str, pl.DataType] = {
    "actor_login": pl.String,
    "quarter": pl.Date,
    "person_type": pl.String,
    "matched_positive_login": pl.String,
    "item_count": pl.UInt8,
    "annotation_status": pl.String,
    "error_type": pl.String,
    "error_message": pl.String,
    "building_what_category": pl.String,
    "building_what_description": pl.String,
    "building_what_citations": pl.List(pl.UInt8),
    "building_what_items_cited": pl.UInt8,
    "audience_orientation": pl.String,
    "audience_orientation_citations": pl.List(pl.UInt8),
    "audience_orientation_items_cited": pl.UInt8,
    "productization_markers": pl.Int8,
    "productization_markers_citations": pl.List(pl.UInt8),
    "productization_markers_items_cited": pl.UInt8,
    "commercial_language": pl.Int8,
    "commercial_language_citations": pl.List(pl.UInt8),
    "commercial_language_items_cited": pl.UInt8,
    "collaboration_posture": pl.String,
    "collaboration_posture_citations": pl.List(pl.UInt8),
    "collaboration_posture_items_cited": pl.UInt8,
    "stated_founding_intent": pl.String,
    "stated_founding_intent_quote": pl.String,
    "stated_founding_intent_citations": pl.List(pl.UInt8),
    "stated_founding_intent_items_cited": pl.UInt8,
    "seriousness": pl.Int8,
    "seriousness_citations": pl.List(pl.UInt8),
    "seriousness_items_cited": pl.UInt8,
    "domain_shift": pl.Int8,
    "domain_shift_citations": pl.List(pl.UInt8),
    "domain_shift_items_cited": pl.UInt8,
    "items_cited": pl.UInt8,
    "annotation_json": pl.String,
    "content_hash": pl.String,
}


def _jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def _compact_items(
    items: Sequence[Mapping[str, Any]], *, budget: int, include_indices: bool
) -> list[dict[str, Any]]:
    """Fit compact item text to a deterministic character budget."""
    if not items:
        return []
    # Retain the most recent evidence when the comparative history is long.
    selected = list(items)[-min(len(items), max(budget // 40, 1)) :]
    per_item = max(budget // len(selected), 1)
    compact: list[dict[str, Any]] = []
    for item in selected:
        title = str(item.get("title") or "")
        body = str(item.get("body") or "")
        title_budget = min(len(title), per_item // 2)
        body_budget = max(per_item - title_budget, 0)
        row = {
            "created_at": str(item.get("created_at") or ""),
            "event_type": str(item.get("event_type") or ""),
            "repo_name": str(item.get("repo_name") or ""),
            "title": title[:title_budget],
            "body": body[:body_budget],
        }
        if include_indices:
            row["item_index"] = int(item["item_index"])
        compact.append(row)
    return compact


def build_annotation_payload(
    *,
    actor_login: str,
    quarter: date,
    current_items: Sequence[Mapping[str, Any]],
    earlier_bundles: Sequence[Mapping[str, Any]] = (),
) -> dict[str, Any]:
    """Create a bounded prompt while preserving all current citation indices."""
    if not current_items:
        raise ValueError("A quarterly annotation bundle cannot be empty")
    earlier_flat = [
        {**dict(item), "quarter": str(bundle.get("quarter") or "")}
        for bundle in earlier_bundles
        for item in bundle.get("items", [])
    ]
    return {
        "prompt_version": PROMPT_VERSION,
        "actor_login": actor_login,
        "quarter": quarter.isoformat(),
        "current_quarter_items": _compact_items(
            current_items, budget=CURRENT_TEXT_BUDGET, include_indices=True
        ),
        "earlier_context_items": _compact_items(
            earlier_flat, budget=EARLIER_TEXT_BUDGET, include_indices=False
        ),
    }


def _content_hash(payload: Mapping[str, Any], *, model: str, mock: bool) -> str:
    value = {
        "payload": _jsonable(payload),
        "schema": SemanticAnnotation.model_json_schema(),
        "system_prompt": SYSTEM_PROMPT,
        "model": model,
        "mode": "mock" if mock else "openrouter",
        "max_tokens": MAX_OUTPUT_TOKENS,
        "reasoning": REASONING,
    }
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _parse_json_object(content: str | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(content, Mapping):
        return dict(content)
    cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", content)
    value = json.loads(cleaned)
    if not isinstance(value, dict):
        raise ValueError("semantic annotation response must be a JSON object")
    return value


def _token_usage(body: Mapping[str, Any]) -> TokenUsage:
    usage = body.get("usage") or {}
    if not isinstance(usage, Mapping):
        return TokenUsage()
    details = usage.get("completion_tokens_details") or {}
    reasoning = details.get("reasoning_tokens", 0) if isinstance(details, Mapping) else 0
    return TokenUsage(
        input_tokens=int(usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0),
        output_tokens=int(
            usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0
        ),
        reasoning_tokens=int(reasoning or usage.get("reasoning_tokens", 0) or 0),
    )


def _call_openrouter(
    payload: Mapping[str, Any],
    *,
    model: str,
    client: httpx.Client | None,
    extra_messages: Sequence[Mapping[str, str]] = (),
) -> ProviderResponse:
    load_dotenv()
    api_key = os.getenv("OPENROUTER_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_KEY is required unless --mock is used")
    request = {
        "model": model,
        "temperature": 0,
        "max_tokens": MAX_OUTPUT_TOKENS,
        "reasoning": REASONING,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "semantic_annotation",
                "strict": True,
                "schema": SemanticAnnotation.model_json_schema(),
            },
        },
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(payload, indent=2, sort_keys=True),
            },
            *[dict(message) for message in extra_messages],
        ],
    }
    owns_client = client is None
    http_client = client or httpx.Client(timeout=120.0)
    try:
        response = http_client.post(
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json=request,
        )
        response.raise_for_status()
        body = response.json()
    finally:
        if owns_client:
            http_client.close()
    try:
        choice = body["choices"][0]
        message = choice["message"]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError("OpenRouter response did not contain a message") from error
    reasoning_present = bool(
        message.get("reasoning") or message.get("reasoning_details")
    )
    content = message.get("content")
    if content is None:
        finish_reason = choice.get("finish_reason")
        raise ValueError(
            "OpenRouter response content was null "
            f"(finish_reason={finish_reason!r}, reasoning_present={reasoning_present})"
        )
    return ProviderResponse(
        raw=_parse_json_object(content),
        usage=_token_usage(body),
        reasoning_present=reasoning_present,
        finish_reason=choice.get("finish_reason"),
    )


def _fixture_path(fixture_dir: Path, *, actor_login: str, quarter: date) -> Path:
    return fixture_dir / f"{actor_login}__{quarter.isoformat()}.json"


def _validate_annotation_citations(
    annotation: SemanticAnnotation, current_items: Sequence[Mapping[str, Any]]
) -> None:
    supplied = {int(item["item_index"]) for item in current_items}
    unsupported = annotation.cited_item_indices() - supplied
    if unsupported:
        raise ValueError(
            "Semantic annotation cited unavailable current item indices: "
            f"{sorted(unsupported)}"
        )


def _read_cache(path: Path) -> tuple[SemanticAnnotation, TokenUsage, int, bool]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if "annotation" not in raw:  # Backward-compatible with the part-one cache shape.
        return SemanticAnnotation.model_validate(raw), TokenUsage(), 0, False
    return (
        SemanticAnnotation.model_validate(raw["annotation"]),
        TokenUsage(**raw.get("usage", {})),
        int(raw.get("attempts", 0)),
        bool(raw.get("reasoning_present", False)),
    )


def annotate_bundle_result(
    *,
    actor_login: str,
    quarter: date,
    current_items: Sequence[Mapping[str, Any]],
    earlier_bundles: Sequence[Mapping[str, Any]] = (),
    mock: bool = False,
    cache_dir: Path = ANNOTATION_CACHE_DIR,
    fixture_dir: Path | None = None,
    client: httpx.Client | None = None,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
) -> AnnotationOutcome:
    """Annotate one bundle with validation retries and cache/run metadata."""
    if max_attempts < 1:
        raise ValueError("max_attempts must be positive")
    payload = build_annotation_payload(
        actor_login=actor_login,
        quarter=quarter,
        current_items=current_items,
        earlier_bundles=earlier_bundles,
    )
    load_dotenv()
    model = os.getenv("OPENROUTER_MODEL")
    if not model and not mock:
        raise RuntimeError("OPENROUTER_MODEL is required unless --mock is used")
    effective_model = model or "mock-fixture"
    content_hash = _content_hash(payload, model=effective_model, mock=mock)
    cache_path = cache_dir / f"{content_hash}.json"
    if cache_path.exists():
        annotation, _cached_usage, cached_attempts, reasoning_present = _read_cache(
            cache_path
        )
        _validate_annotation_citations(annotation, current_items)
        return AnnotationOutcome(
            annotation=annotation,
            cache_hit=True,
            # Cache reads incur no new provider tokens in this run.
            usage=TokenUsage(),
            attempts=cached_attempts,
            reasoning_present=reasoning_present,
            content_hash=content_hash,
        )

    if mock:
        if fixture_dir is None:
            raise ValueError("mock annotation requires fixture_dir")
        fixture_path = _fixture_path(
            fixture_dir, actor_login=actor_login, quarter=quarter
        )
        if not fixture_path.exists():
            raise FileNotFoundError(f"No semantic mock fixture: {fixture_path}")
        raw = json.loads(fixture_path.read_text(encoding="utf-8"))
        annotation = SemanticAnnotation.model_validate(raw)
        _validate_annotation_citations(annotation, current_items)
        attempts = 1
        usage = TokenUsage()
        reasoning_present = False
    else:
        extra_messages: list[dict[str, str]] = []
        total_usage = TokenUsage()
        reasoning_present = False
        last_error: Exception | None = None
        annotation: SemanticAnnotation | None = None
        for attempt in range(1, max_attempts + 1):
            raw: dict[str, Any] | None = None
            try:
                provider = _call_openrouter(
                    payload,
                    model=effective_model,
                    client=client,
                    extra_messages=extra_messages,
                )
                raw = provider.raw
                total_usage += provider.usage
                reasoning_present = reasoning_present or provider.reasoning_present
                annotation = SemanticAnnotation.model_validate(raw)
                _validate_annotation_citations(annotation, current_items)
                break
            except (httpx.HTTPError, ValidationError, ValueError) as error:
                last_error = error
                if attempt == max_attempts:
                    raise
                if raw is not None:
                    extra_messages = [
                        {"role": "assistant", "content": json.dumps(raw, default=str)},
                        {
                            "role": "user",
                            "content": (
                                "That JSON failed validation with the following error. "
                                "Return the corrected COMPLETE JSON object only, matching "
                                f"the schema exactly.\n\n{error}"
                            ),
                        },
                    ]
                delay = min(2 ** (attempt - 1), 4) + random.random() * 0.25
                time.sleep(delay)
        if annotation is None:
            assert last_error is not None
            raise last_error
        attempts = attempt
        usage = total_usage

    cache_record = {
        "cache_version": 2,
        "annotation": annotation.model_dump(mode="json"),
        "usage": asdict(usage),
        "attempts": attempts,
        "reasoning_present": reasoning_present,
    }
    atomic_write_text(json.dumps(cache_record, indent=2, sort_keys=True), cache_path)
    return AnnotationOutcome(
        annotation=annotation,
        cache_hit=False,
        usage=usage,
        attempts=attempts,
        reasoning_present=reasoning_present,
        content_hash=content_hash,
    )


def annotate_bundle(
    *,
    actor_login: str,
    quarter: date,
    current_items: Sequence[Mapping[str, Any]],
    earlier_bundles: Sequence[Mapping[str, Any]] = (),
    mock: bool = False,
    cache_dir: Path = ANNOTATION_CACHE_DIR,
    fixture_dir: Path | None = None,
    client: httpx.Client | None = None,
) -> SemanticAnnotation:
    """Compatibility wrapper returning only the validated annotation."""
    return annotate_bundle_result(
        actor_login=actor_login,
        quarter=quarter,
        current_items=current_items,
        earlier_bundles=earlier_bundles,
        mock=mock,
        cache_dir=cache_dir,
        fixture_dir=fixture_dir,
        client=client,
    ).annotation


def bundle_rows(rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Group sorted text rows into person-quarter bundles for annotation runners."""
    grouped: dict[tuple[str, date], list[dict[str, Any]]] = {}
    for row in rows:
        quarter_value = row["quarter"]
        if isinstance(quarter_value, datetime):
            quarter_value = quarter_value.date()
        if not isinstance(quarter_value, date):
            raise TypeError("quarter must be date-like")
        key = (str(row["actor_login"]), quarter_value)
        grouped.setdefault(key, []).append(dict(row))
    return [
        {"actor_login": login, "quarter": quarter, "items": items}
        for (login, quarter), items in sorted(grouped.items())
    ]


def _bundle_tasks(
    bundles: Sequence[Mapping[str, Any]],
) -> list[tuple[dict[str, Any], tuple[dict[str, Any], ...]]]:
    earlier_by_actor: dict[str, list[dict[str, Any]]] = {}
    tasks: list[tuple[dict[str, Any], tuple[dict[str, Any], ...]]] = []
    for raw_bundle in bundles:
        bundle = dict(raw_bundle)
        login = str(bundle["actor_login"])
        tasks.append((bundle, tuple(earlier_by_actor.get(login, ()))))
        earlier_by_actor.setdefault(login, []).append(bundle)
    return tasks


def _base_annotation_row(bundle: Mapping[str, Any]) -> dict[str, Any]:
    items = bundle["items"]
    first = items[0]
    return {
        "actor_login": str(bundle["actor_login"]),
        "quarter": bundle["quarter"],
        "person_type": str(first["person_type"]),
        "matched_positive_login": str(first["matched_positive_login"]),
        "item_count": len(items),
    }


def _annotation_row(
    bundle: Mapping[str, Any], outcome: AnnotationOutcome
) -> dict[str, Any]:
    annotation = outcome.annotation
    return {
        **_base_annotation_row(bundle),
        "annotation_status": "ok",
        "error_type": None,
        "error_message": None,
        "building_what_category": (
            annotation.building_what.category.value
            if annotation.building_what.category is not None
            else None
        ),
        "building_what_description": annotation.building_what.description,
        "building_what_citations": annotation.building_what.citations,
        "building_what_items_cited": len(annotation.building_what.citations),
        "audience_orientation": annotation.audience_orientation.value,
        "audience_orientation_citations": annotation.audience_orientation.citations,
        "audience_orientation_items_cited": len(
            annotation.audience_orientation.citations
        ),
        "productization_markers": annotation.productization_markers.value,
        "productization_markers_citations": annotation.productization_markers.citations,
        "productization_markers_items_cited": len(
            annotation.productization_markers.citations
        ),
        "commercial_language": annotation.commercial_language.value,
        "commercial_language_citations": annotation.commercial_language.citations,
        "commercial_language_items_cited": len(
            annotation.commercial_language.citations
        ),
        "collaboration_posture": annotation.collaboration_posture.value,
        "collaboration_posture_citations": annotation.collaboration_posture.citations,
        "collaboration_posture_items_cited": len(
            annotation.collaboration_posture.citations
        ),
        "stated_founding_intent": annotation.stated_founding_intent.value,
        "stated_founding_intent_quote": annotation.stated_founding_intent.quote,
        "stated_founding_intent_citations": annotation.stated_founding_intent.citations,
        "stated_founding_intent_items_cited": len(
            annotation.stated_founding_intent.citations
        ),
        "seriousness": annotation.seriousness.value,
        "seriousness_citations": annotation.seriousness.citations,
        "seriousness_items_cited": len(annotation.seriousness.citations),
        "domain_shift": annotation.domain_shift.value,
        "domain_shift_citations": annotation.domain_shift.citations,
        "domain_shift_items_cited": len(annotation.domain_shift.citations),
        "items_cited": len(annotation.cited_item_indices()),
        "annotation_json": annotation.model_dump_json(),
        "content_hash": outcome.content_hash,
    }


def _failed_annotation_row(
    bundle: Mapping[str, Any], error: BaseException
) -> dict[str, Any]:
    row = {column: None for column in ANNOTATION_SCHEMA}
    message = str(error).replace("\n", " ")[:1_000]
    return {
        **row,
        **_base_annotation_row(bundle),
        "annotation_status": "failed",
        "error_type": type(error).__name__,
        "error_message": message,
    }


def _frame(rows: Sequence[Mapping[str, Any]]) -> pl.DataFrame:
    return pl.DataFrame(rows, schema=ANNOTATION_SCHEMA, strict=False).sort(
        "actor_login", "quarter"
    )


def _failure_rate_exceeded(window: deque[bool]) -> bool:
    return (
        len(window) == FAILURE_WINDOW_SIZE
        and sum(window) / FAILURE_WINDOW_SIZE > MAX_FAILURE_RATE
    )


def _write_run_summary(
    stats: AnnotationRunStats,
    *,
    output_path: Path,
    summary_path: Path,
    model: str,
    concurrency: int,
) -> None:
    payload = {
        **asdict(stats),
        "model": model,
        "concurrency": concurrency,
        "max_attempts": DEFAULT_MAX_ATTEMPTS,
        "max_tokens": MAX_OUTPUT_TOKENS,
        "reasoning": REASONING,
        "output_path": str(output_path),
    }
    atomic_write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", summary_path)


def annotate_text_items(
    *,
    items_path: Path = TEXT_ITEMS_PATH,
    output_path: Path = ANNOTATIONS_PATH,
    summary_path: Path = ANNOTATION_RUN_SUMMARY_PATH,
    mock: bool = False,
    fixture_dir: Path | None = None,
    cache_dir: Path = ANNOTATION_CACHE_DIR,
    actor_limit: int | None = None,
    bundle_limit: int | None = None,
    concurrency: int = DEFAULT_CONCURRENCY,
    progress_every: int = DEFAULT_PROGRESS_EVERY,
    client: httpx.Client | None = None,
) -> tuple[pl.DataFrame, AnnotationRunStats]:
    """Annotate all bundles concurrently, checkpointing durable partial results."""
    if not items_path.exists():
        raise FileNotFoundError(f"Missing extracted semantic text: {items_path}")
    if concurrency < 1:
        raise ValueError("concurrency must be positive")
    if progress_every < 1:
        raise ValueError("progress_every must be positive")
    items = pl.read_parquet(items_path).sort("actor_login", "quarter", "item_index")
    if actor_limit is not None:
        if actor_limit < 1:
            raise ValueError("actor_limit must be positive")
        actors = items.get_column("actor_login").unique(maintain_order=True).head(
            actor_limit
        )
        items = items.filter(pl.col("actor_login").is_in(actors))
    bundles = bundle_rows(items.to_dicts())
    if bundle_limit is not None:
        if bundle_limit < 1:
            raise ValueError("bundle_limit must be positive")
        bundles = bundles[:bundle_limit]
    tasks = _bundle_tasks(bundles)
    stats = AnnotationRunStats(total_bundles=len(tasks))
    rows: list[dict[str, Any]] = []
    failure_window: deque[bool] = deque(maxlen=FAILURE_WINDOW_SIZE)
    load_dotenv()
    model = os.getenv("OPENROUTER_MODEL") or ("mock-fixture" if mock else "")
    if not model:
        raise RuntimeError("OPENROUTER_MODEL is required unless --mock is used")

    owns_client = client is None and not mock
    http_client = client or (httpx.Client(timeout=120.0) if not mock else None)

    def run_task(
        task: tuple[dict[str, Any], tuple[dict[str, Any], ...]],
    ) -> tuple[dict[str, Any], AnnotationOutcome]:
        bundle, earlier = task
        quarter = bundle["quarter"]
        assert isinstance(quarter, date)
        outcome = annotate_bundle_result(
            actor_login=str(bundle["actor_login"]),
            quarter=quarter,
            current_items=bundle["items"],
            earlier_bundles=earlier,
            mock=mock,
            fixture_dir=fixture_dir,
            cache_dir=cache_dir,
            client=http_client,
        )
        return bundle, outcome

    try:
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            pending: dict[
                Future[tuple[dict[str, Any], AnnotationOutcome]],
                tuple[dict[str, Any], tuple[dict[str, Any], ...]],
            ] = {}
            task_iterator = iter(tasks)

            def submit_next() -> bool:
                try:
                    task = next(task_iterator)
                except StopIteration:
                    return False
                pending[executor.submit(run_task, task)] = task
                return True

            for _ in range(min(concurrency, len(tasks))):
                submit_next()
            while pending:
                done, _ = wait(pending, return_when=FIRST_COMPLETED)
                for future in done:
                    task = pending.pop(future)
                    bundle = task[0]
                    failed = False
                    try:
                        completed_bundle, outcome = future.result()
                        rows.append(_annotation_row(completed_bundle, outcome))
                        stats.record_success(outcome)
                    except Exception as error:  # noqa: BLE001 - bundle isolation boundary
                        failed = True
                        rows.append(_failed_annotation_row(bundle, error))
                        stats.record_failure()
                        LOGGER.error(
                            "annotation_failed actor=%s quarter=%s error_type=%s error=%s",
                            bundle["actor_login"],
                            bundle["quarter"],
                            type(error).__name__,
                            str(error).replace("\n", " ")[:500],
                        )
                    failure_window.append(failed)
                    if stats.completed % progress_every == 0:
                        atomic_write_parquet(_frame(rows), output_path)
                        _write_run_summary(
                            stats,
                            output_path=output_path,
                            summary_path=summary_path,
                            model=model,
                            concurrency=concurrency,
                        )
                        LOGGER.info(
                            "annotation_progress completed=%d total=%d annotated=%d "
                            "failed=%d cache_hits=%d input_tokens=%d output_tokens=%d",
                            stats.completed,
                            stats.total_bundles,
                            stats.annotated,
                            stats.failed,
                            stats.cache_hits,
                            stats.input_tokens,
                            stats.output_tokens,
                        )
                    if _failure_rate_exceeded(failure_window):
                        stats.aborted = True
                        for queued in pending:
                            queued.cancel()
                        pending.clear()
                        break
                    submit_next()
                if stats.aborted:
                    break
    finally:
        if owns_client and http_client is not None:
            http_client.close()
        frame = _frame(rows)
        atomic_write_parquet(frame, output_path)
        _write_run_summary(
            stats,
            output_path=output_path,
            summary_path=summary_path,
            model=model,
            concurrency=concurrency,
        )
    if stats.aborted:
        raise RuntimeError(
            "Annotation run aborted: failures exceeded 5% in a 500-bundle window"
        )
    return frame, stats
