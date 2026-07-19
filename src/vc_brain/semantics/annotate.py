"""Content-addressed OpenRouter pipeline for quarterly text annotations."""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections.abc import Mapping, Sequence
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
    ANNOTATIONS_PATH,
    TEXT_ITEMS_PATH,
)
from vc_brain.semantics.schema import SemanticAnnotation

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
PROMPT_VERSION = "a3-v1-domain-shift"
CURRENT_TEXT_BUDGET = 4_500
EARLIER_TEXT_BUDGET = 1_500

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


def _jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def _compact_items(
    items: Sequence[Mapping[str, Any]], *, budget: int, include_indices: bool
) -> list[dict[str, Any]]:
    if not items:
        return []
    per_item = max(budget // len(items), 40)
    compact: list[dict[str, Any]] = []
    for item in items:
        title = str(item.get("title") or "")
        body = str(item.get("body") or "")
        text_budget = max(per_item - len(title), 0)
        row = {
            "created_at": str(item.get("created_at") or ""),
            "event_type": str(item.get("event_type") or ""),
            "repo_name": str(item.get("repo_name") or ""),
            "title": title[:per_item],
            "body": body[:text_budget],
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
        {
            **dict(item),
            "quarter": str(bundle.get("quarter") or ""),
        }
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


def _call_openrouter(
    payload: Mapping[str, Any],
    *,
    model: str,
    client: httpx.Client | None,
) -> dict[str, Any]:
    load_dotenv()
    api_key = os.getenv("OPENROUTER_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_KEY is required unless --mock is used")
    request = {
        "model": model,
        "temperature": 0,
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
        ],
    }
    owns_client = client is None
    http_client = client or httpx.Client(timeout=90.0)
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
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError(
            "OpenRouter response did not contain semantic annotation content"
        ) from error
    return _parse_json_object(content)


def _fixture_path(fixture_dir: Path, *, actor_login: str, quarter: date) -> Path:
    return fixture_dir / f"{actor_login}__{quarter.isoformat()}.json"


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
    """Annotate one person-quarter with validated, content-hash cached output."""
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
    cache_path = (
        cache_dir / f"{_content_hash(payload, model=effective_model, mock=mock)}.json"
    )
    if cache_path.exists():
        annotation = SemanticAnnotation.model_validate_json(
            cache_path.read_text(encoding="utf-8")
        )
    else:
        if mock:
            if fixture_dir is None:
                raise ValueError("mock annotation requires fixture_dir")
            fixture_path = _fixture_path(
                fixture_dir, actor_login=actor_login, quarter=quarter
            )
            if not fixture_path.exists():
                raise FileNotFoundError(f"No semantic mock fixture: {fixture_path}")
            raw = json.loads(fixture_path.read_text(encoding="utf-8"))
        else:
            raw = _call_openrouter(payload, model=effective_model, client=client)
        try:
            annotation = SemanticAnnotation.model_validate(raw)
        except ValidationError:
            raise
        atomic_write_text(annotation.model_dump_json(indent=2), cache_path)

    supplied = {int(item["item_index"]) for item in current_items}
    unsupported = annotation.cited_item_indices() - supplied
    if unsupported:
        raise ValueError(
            f"Semantic annotation cited unavailable current item indices: {sorted(unsupported)}"
        )
    return annotation


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


def annotate_text_items(
    *,
    items_path: Path = TEXT_ITEMS_PATH,
    output_path: Path = ANNOTATIONS_PATH,
    mock: bool = False,
    fixture_dir: Path | None = None,
    cache_dir: Path = ANNOTATION_CACHE_DIR,
    actor_limit: int | None = None,
    client: httpx.Client | None = None,
) -> pl.DataFrame:
    """Annotate every bundle in chronological actor order and persist JSON rows."""
    if not items_path.exists():
        raise FileNotFoundError(f"Missing extracted semantic text: {items_path}")
    items = pl.read_parquet(items_path).sort("actor_login", "quarter", "item_index")
    if actor_limit is not None:
        if actor_limit < 1:
            raise ValueError("actor_limit must be positive")
        actors = (
            items.get_column("actor_login")
            .unique(maintain_order=True)
            .head(actor_limit)
        )
        items = items.filter(pl.col("actor_login").is_in(actors))
    bundles = bundle_rows(items.to_dicts())
    earlier_by_actor: dict[str, list[dict[str, Any]]] = {}
    rows: list[dict[str, Any]] = []
    for bundle in bundles:
        login = str(bundle["actor_login"])
        quarter = bundle["quarter"]
        assert isinstance(quarter, date)
        annotation = annotate_bundle(
            actor_login=login,
            quarter=quarter,
            current_items=bundle["items"],
            earlier_bundles=earlier_by_actor.get(login, []),
            mock=mock,
            fixture_dir=fixture_dir,
            cache_dir=cache_dir,
            client=client,
        )
        rows.append(
            {
                "actor_login": login,
                "quarter": quarter,
                "item_count": len(bundle["items"]),
                "annotation_json": annotation.model_dump_json(),
            }
        )
        earlier_by_actor.setdefault(login, []).append(bundle)
    frame = pl.DataFrame(
        rows,
        schema={
            "actor_login": pl.String,
            "quarter": pl.Date,
            "item_count": pl.UInt8,
            "annotation_json": pl.String,
        },
        strict=False,
    ).sort("actor_login", "quarter")
    atomic_write_parquet(frame, output_path)
    return frame
