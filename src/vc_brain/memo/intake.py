"""Convert inbound pitch decks into traceable evidence and a memo."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pdfplumber

from vc_brain.memo.generate import generate_memo
from vc_brain.memo.schema import Memo


def extract_deck_evidence(
    deck_path: Path, company_name: str
) -> tuple[str, list[dict[str, Any]]]:
    """Extract one traceable evidence row per non-empty PDF page."""
    path = deck_path.resolve()
    rows: list[dict[str, Any]] = []
    page_texts: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = " ".join((page.extract_text() or "").split())
            if not text:
                continue
            source = f"deck page {page_number}"
            evidence_id = hashlib.sha256(
                f"{path}:{page_number}:{text}".encode()
            ).hexdigest()[:20]
            rows.append(
                {
                    "evidence_id": f"deck-{evidence_id}",
                    "gh_login": "inbound-application",
                    "ts": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(),
                    "event_type": "deck_claim",
                    "repo_name": company_name,
                    "detail": text,
                    "url": f"{path.as_uri()}#page={page_number}",
                    "source": source,
                    "verification_status": "single_source",
                }
            )
            page_texts.append(f"[{source}] {text}")
    if not rows:
        raise ValueError(f"deck contains no extractable text: {deck_path}")
    return "\n\n".join(page_texts), rows


def generate_from_deck(
    deck_path: Path,
    company_name: str,
    *,
    candidate: Mapping[str, Any] | None = None,
    public_evidence: Sequence[Mapping[str, Any]] = (),
    mock: bool = False,
    cache_dir: Path = Path("data/cache/llm"),
    fixture_memos_dir: Path = Path("data/fixtures/memos"),
) -> Memo:
    """Run an inbound deck through the same evidence-backed memo path."""
    deck_text, deck_evidence = extract_deck_evidence(deck_path, company_name)
    candidate_data = dict(candidate or {})
    candidate_data.setdefault("gh_login", "inbound-application")
    candidate_data.setdefault("company", company_name)
    all_evidence = [*deck_evidence, *[dict(row) for row in public_evidence]]
    return generate_memo(
        candidate_data,
        all_evidence,
        deck_text,
        mock=mock,
        cache_dir=cache_dir,
        fixture_memos_dir=fixture_memos_dir,
    )

