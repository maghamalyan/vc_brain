from datetime import date
from pathlib import Path

import polars as pl
import pytest

from vc_brain.labels.contracts import FOUNDER_RAW_SCHEMA
from vc_brain.labels.gh_resolve import (
    name_token_similarity,
    resolve_founders,
    score_candidate,
)


@pytest.fixture
def founder() -> dict[str, object]:
    return {
        "founder_name": "Alice Smith",
        "company": "Example Labs",
        "company_website": "https://www.example.com",
        "twitter_url": "https://x.com/AliceSmith",
    }


@pytest.fixture
def candidate() -> dict[str, object]:
    return {
        "login": "alice-dev",
        "type": "User",
        "name": "Unrelated Person",
        "twitter_username": "someone_else",
        "blog": "https://other.example.net",
        "bio": "Engineer",
        "company": "Elsewhere",
    }


def test_twitter_signal(
    founder: dict[str, object], candidate: dict[str, object]
) -> None:
    candidate["twitter_username"] = "@AliceSmith"
    assert score_candidate(candidate, founder, candidate_count=2)[0] == 0.5


def test_domain_signal(
    founder: dict[str, object], candidate: dict[str, object]
) -> None:
    candidate["blog"] = "http://example.com/about"
    assert score_candidate(candidate, founder, candidate_count=2)[0] == 0.4


def test_company_signal(
    founder: dict[str, object], candidate: dict[str, object]
) -> None:
    candidate["bio"] = "Co-founder of Example Labs"
    assert score_candidate(candidate, founder, candidate_count=2)[0] == 0.3


def test_name_signal(
    founder: dict[str, object], candidate: dict[str, object]
) -> None:
    candidate["name"] = "Smith, Alice"
    score, evidence = score_candidate(candidate, founder, candidate_count=2)
    assert score == 0.2
    assert evidence["name_token_similarity"] == 1.0


def test_single_candidate_signal(
    founder: dict[str, object], candidate: dict[str, object]
) -> None:
    assert score_candidate(candidate, founder, candidate_count=1)[0] == 0.1


def test_bot_penalty_and_score_floor(
    founder: dict[str, object], candidate: dict[str, object]
) -> None:
    candidate["login"] = "helper-bot"
    assert score_candidate(candidate, founder, candidate_count=2)[0] == 0.0


def test_combined_score_is_capped(
    founder: dict[str, object], candidate: dict[str, object]
) -> None:
    candidate.update(
        {
            "name": "Alice Smith",
            "twitter_username": "alicesmith",
            "blog": "https://example.com",
            "company": "Example Labs",
        }
    )
    score, evidence = score_candidate(candidate, founder, candidate_count=1)
    assert score == 1.0
    assert len(evidence) == 5


def test_name_token_similarity_handles_diacritics() -> None:
    assert name_token_similarity("José García", "Garcia Jose") == 1.0


def test_resolution_stage_resumes_without_duplicates(tmp_path: Path) -> None:
    founders_path = tmp_path / "founders_raw.parquet"
    output_path = tmp_path / "founders_resolved.parquet"
    rows = []
    for index, name in enumerate(("Alice", "Bob", "Carol"), start=1):
        rows.append(
            {
                "_founder_key": f"acme:{index}",
                "founder_name": name,
                "company": "Acme",
                "slug": "acme",
                "batch": "Winter 2024",
                "batch_year": 2024,
                "batch_start_date": date(2024, 1, 5),
                "company_website": "https://acme.example",
                "one_liner": "Makes things",
                "team_size": 3,
                "status": "Active",
                "linkedin_url": None,
                "twitter_url": None,
                "founder_bio": None,
                "title": None,
                "user_id": str(index),
            }
        )
    pl.DataFrame(rows, schema=FOUNDER_RAW_SCHEMA).write_parquet(founders_path)
    calls: list[str] = []

    def interrupted(founder_row: dict[str, object]) -> dict[str, object]:
        calls.append(str(founder_row["_founder_key"]))
        if len(calls) == 2:
            raise KeyboardInterrupt
        return unresolved_result(founder_row)

    with pytest.raises(KeyboardInterrupt):
        resolve_founders(
            founders_path=founders_path,
            output_path=output_path,
            resolve_one=interrupted,
        )

    resumed_calls: list[str] = []

    def resumed(founder_row: dict[str, object]) -> dict[str, object]:
        resumed_calls.append(str(founder_row["_founder_key"]))
        return unresolved_result(founder_row)

    completed = resolve_founders(
        founders_path=founders_path,
        output_path=output_path,
        resolve_one=resumed,
    )

    assert "acme:1" not in resumed_calls
    assert set(resumed_calls) == {"acme:2", "acme:3"}
    assert completed.height == 3
    assert completed.get_column("_founder_key").n_unique() == 3


def unresolved_result(founder_row: dict[str, object]) -> dict[str, object]:
    return {
        "_founder_key": founder_row["_founder_key"],
        "gh_login": None,
        "gh_confidence": 0.0,
        "resolution_method": "none",
        "evidence": "{}",
    }
