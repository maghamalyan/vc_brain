from datetime import date, datetime

import polars as pl
import pytest

from vc_brain.ingest.leakage import (
    LeakageViolation,
    assert_no_founders_in_negatives,
    assert_temporal_leakage_free,
    company_repo_leakage_drops,
)


def test_temporal_leakage_assertion_accepts_only_strictly_pre_cutoff_rows() -> None:
    valid = pl.DataFrame(
        {
            "month": [date(2023, 12, 1)],
            "t_cutoff": [date(2024, 1, 1)],
        }
    )
    assert_temporal_leakage_free(valid)

    leaked = pl.DataFrame(
        {
            "month": [date(2024, 1, 1)],
            "t_cutoff": [date(2024, 1, 1)],
        }
    )
    with pytest.raises(LeakageViolation, match="at or after"):
        assert_temporal_leakage_free(leaked)


def test_temporal_leakage_assertion_handles_event_timestamps() -> None:
    frame = pl.DataFrame(
        {
            "created_at": [datetime(2023, 12, 31, 23, 59)],
            "t_cutoff": [date(2024, 1, 1)],
        }
    )
    assert_temporal_leakage_free(frame, time_column="created_at")


def test_negative_sample_rejects_founders_at_any_confidence() -> None:
    negatives = pl.DataFrame({"actor_login": ["ordinary", "FounderLogin"]})

    with pytest.raises(LeakageViolation, match="founderlogin"):
        assert_no_founders_in_negatives(
            negatives, {"founderlogin", "low_confidence_login"}
        )


def test_company_domain_repo_detection_records_actor_drop() -> None:
    cohort = pl.DataFrame(
        {
            "actor_login": ["alice", "bob"],
            "t_cutoff": [date(2024, 1, 1), date(2024, 1, 1)],
            "company_domains": [["acme.ai"], ["harmless.dev"]],
        }
    )
    repo_names = pl.DataFrame(
        {
            "actor_login": ["alice", "bob"],
            "repo_name": ["acme/platform", "bob/personal"],
            "t_cutoff": [date(2024, 1, 1), date(2024, 1, 1)],
        }
    )

    drops = company_repo_leakage_drops(repo_names, cohort)

    assert drops.select("actor_login", "company_domain", "repo_name").to_dicts() == [
        {
            "actor_login": "alice",
            "company_domain": "acme.ai",
            "repo_name": "acme/platform",
        }
    ]
