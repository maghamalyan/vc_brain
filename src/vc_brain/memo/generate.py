"""Generate concise investment memos with evidence-constrained LLM output."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from pydantic import ValidationError

from vc_brain.memo.schema import Memo


DEFAULT_MODEL = "anthropic/claude-sonnet-4.5"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_CACHE_DIR = Path("data/cache/llm")
DEFAULT_FIXTURE_MEMOS = Path("data/fixtures/memos")


SYSTEM_PROMPT = """You are an evidence-disciplined venture analyst.
Return one JSON object matching the supplied schema, with only the five required memo
sections. Be concise: padding reduces decision utility.

Hard rules:
- Every factual claim must have evidence_refs copied verbatim from the provided
  evidence_id or url values. Never cite anything outside the supplied evidence.
- If the evidence does not support a fact, do not infer or invent it. Put the missing
  fact in gaps and state "not disclosed" in the relevant section.
- Deck-only claims are single_source unless public evidence explicitly corroborates
  them. Surface conflicts in contradictions; do not resolve them by guessing.
- Keep Founder, Market, and Idea-vs-Market as three independent axes. Do not combine
  them into a composite score. Every axis must cite existing claim_ids.
- Output JSON only. No markdown fences or commentary.
"""


def generate_memo(
    candidate: Mapping[str, Any],
    evidence_rows: Sequence[Mapping[str, Any]],
    application_deck_text: str | None = None,
    *,
    mock: bool = False,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    fixture_memos_dir: Path = DEFAULT_FIXTURE_MEMOS,
    client: httpx.Client | None = None,
) -> Memo:
    """Generate and validate a memo, using a deterministic fixture in mock mode."""
    payload = _input_payload(candidate, evidence_rows, application_deck_text)
    cache_path = cache_dir / f"{_input_hash(payload)}.json"
    if cache_path.exists():
        memo = Memo.model_validate_json(cache_path.read_text(encoding="utf-8"))
        _validate_evidence_refs(memo, evidence_rows)
        return memo

    max_attempts = 1 if mock else 3
    extra_messages: list[dict[str, str]] = []
    memo: Memo | None = None
    for _attempt in range(max_attempts):
        if mock:
            raw = _load_mock_response(candidate, fixture_memos_dir)
        else:
            raw = _call_openrouter(
                payload, client=client, extra_messages=extra_messages
            )
        try:
            memo = Memo.model_validate(raw)
            _validate_evidence_refs(memo, evidence_rows)
            break
        except (ValidationError, ValueError) as error:
            if _attempt == max_attempts - 1:
                raise
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
    assert memo is not None
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        memo.model_dump_json(indent=2), encoding="utf-8"
    )
    return memo


def _validate_evidence_refs(
    memo: Memo, evidence_rows: Sequence[Mapping[str, Any]]
) -> None:
    supplied = {
        str(reference)
        for row in evidence_rows
        for reference in (row.get("evidence_id"), row.get("url"))
        if reference
    }
    unsupported = {
        reference
        for claim in memo.claims.values()
        for reference in claim.evidence_refs
        if reference not in supplied
    }
    if unsupported:
        items = ", ".join(sorted(unsupported))
        raise ValueError(f"memo cited evidence that was not supplied: {items}")


def _input_payload(
    candidate: Mapping[str, Any],
    evidence_rows: Sequence[Mapping[str, Any]],
    application_deck_text: str | None,
) -> dict[str, Any]:
    return {
        "candidate": _jsonable(dict(candidate)),
        "evidence": [_jsonable(dict(row)) for row in evidence_rows],
        "application_deck_text": application_deck_text,
        "schema": Memo.model_json_schema(),
    }


def _jsonable(value: Any) -> Any:
    return json.loads(json.dumps(value, default=str))


def _input_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _load_mock_response(
    candidate: Mapping[str, Any], fixture_memos_dir: Path
) -> dict[str, Any]:
    login = str(candidate.get("gh_login", "")).strip()
    if not login:
        raise ValueError("mock generation requires candidate.gh_login")
    path = fixture_memos_dir / f"{login}.json"
    if not path.exists():
        raise FileNotFoundError(f"no mock memo fixture for {login!r}: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _call_openrouter(
    payload: Mapping[str, Any],
    *,
    client: httpx.Client | None,
    extra_messages: Sequence[Mapping[str, str]] = (),
) -> dict[str, Any]:
    load_dotenv()
    api_key = os.getenv("OPENROUTER_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_KEY is required unless --mock is used")
    model = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL)
    request = {
        "model": model,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
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
        raise ValueError("OpenRouter response did not contain memo content") from error
    return _parse_json_object(content)


def _parse_json_object(content: str | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(content, Mapping):
        return dict(content)
    cleaned = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", content)
    value = json.loads(cleaned)
    if not isinstance(value, dict):
        raise ValueError("memo response must be a JSON object")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path, help="Candidate JSON file")
    parser.add_argument("evidence", type=Path, help="Evidence JSON file")
    parser.add_argument("--deck-text", type=Path)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    candidate = json.loads(args.candidate.read_text(encoding="utf-8"))
    evidence = json.loads(args.evidence.read_text(encoding="utf-8"))
    deck_text = (
        args.deck_text.read_text(encoding="utf-8") if args.deck_text else None
    )
    memo = generate_memo(candidate, evidence, deck_text, mock=args.mock)
    rendered = memo.model_dump_json(indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)


if __name__ == "__main__":
    main()
