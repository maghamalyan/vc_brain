"""Offline smoke tests for the person-level semantic instrument modules."""

from __future__ import annotations

from datetime import date, datetime

import polars as pl

from vc_brain.semantics.person_annotate import build_digest
from vc_brain.semantics.person_masking import identity_tokens, mask_text


def _events(actor: str) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "actor_login": [actor] * 3,
            "created_at": [datetime(2023, 1, 5), datetime(2023, 2, 6), datetime(2023, 3, 7)],
            "event_type": ["CreateEvent", "IssuesEvent", "MemberEvent"],
            "action": ["none", "opened", "added"],
            "repo_name": [f"{actor}/coolproduct", f"{actor}/coolproduct", f"{actor}/coolproduct"],
            "ref": ["", "", ""],
            "ref_type": ["repository", "none", "none"],
            "number": [0, 1, 0],
            "title": ["", "Add pricing page", ""],
            "body": ["", f"see https://github.com/{actor}/coolproduct", ""],
            "labels": ["", "", ""],
            "author_association": ["OWNER", "OWNER", "OWNER"],
            "creator_user_login": ["", actor, ""],
            "member_login": ["", "", "helperperson"],
            "merged": [0, 0, 0],
            "additions": [0, 0, 0],
            "deletions": [0, 0, 0],
            "changed_files": [0, 0, 0],
            "release_name": ["", "", ""],
            "t_cutoff": [date(2024, 1, 1)] * 3,
        }
    )


def test_build_digest_contains_sections_and_is_deterministic() -> None:
    events = _events("ada-founder")
    digest = build_digest(events)
    assert "REPOS CREATED:" in digest
    assert "ada-founder/coolproduct" in digest
    assert "COLLABORATORS ADDED:" in digest
    assert digest == build_digest(events)


def test_masking_removes_actor_identity_everywhere() -> None:
    actor = "ada-founder"
    events = _events(actor)
    tokens = identity_tokens(events, actor)
    digest = build_digest(events)
    masked = mask_text(digest, tokens, actor)
    assert actor not in masked.lower()
    assert "helperperson" not in masked.lower()
    assert "coolproduct" in masked  # content survives, identity does not
