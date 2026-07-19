from datetime import date
from pathlib import Path

import polars as pl

from vc_brain.ingest.pipeline import (
    extract_monthly_agg,
    extract_ownership_collab,
    match_negatives,
)


class StubClickHouse:
    def query_actor_batches(self, actors, builder, *, batch_size=300):  # noqa: ANN001
        assert len(actors) == 2
        sql = builder(actors)
        assert "e.created_at < toDateTime(a.t_cutoff)" in sql
        return pl.DataFrame(
            {
                "actor_login": ["alice"],
                "month": [date(2023, 12, 1)],
                "event_type": ["PushEvent"],
                "is_weekend": [False],
                "event_count": [3],
                "t_cutoff": [date(2024, 1, 1)],
            }
        )


class StubOwnershipClickHouse:
    def query_actor_batches(self, actors, builder, *, batch_size=300):  # noqa: ANN001
        assert len(actors) == 2
        assert batch_size == 4_000
        sql = builder(actors)
        assert "own_repo_events" in sql
        assert "distinct_collaborators" in sql
        return pl.DataFrame(
            {
                "actor_login": ["alice", "bob"],
                "month": [date(2023, 12, 1), date(2023, 12, 1)],
                "own_repo_events": [7, 0],
                "other_repo_events": [3, 5],
                "distinct_collaborators": [2, 0],
                "t_cutoff": [date(2024, 1, 1), date(2024, 1, 1)],
            }
        )


def test_monthly_extraction_preserves_zero_activity_actor_and_asserts_leakage(
    tmp_path: Path,
) -> None:
    cohort = pl.DataFrame(
        {
            "actor_login": ["alice", "bob"],
            "t_cutoff": [date(2024, 1, 1), date(2024, 1, 1)],
        }
    )

    frame = extract_monthly_agg(
        StubClickHouse(),  # type: ignore[arg-type]
        cohort,
        cohort_name="positives",
        output_path=tmp_path / "monthly.parquet",
    )

    assert frame.get_column("actor_login").n_unique() == 2
    assert frame.filter(pl.col("actor_login") == "bob").to_dicts() == [
        {
            "actor_login": "bob",
            "month": date(2023, 12, 1),
            "event_type": "__NO_ACTIVITY__",
            "is_weekend": False,
            "event_count": 0,
            "t_cutoff": date(2024, 1, 1),
            "cohort": "positives",
            "no_gh_activity": True,
        }
    ]
    assert pl.read_parquet(tmp_path / "monthly.parquet").equals(frame)


def test_ownership_and_collaboration_are_split_from_one_query_family() -> None:
    cohort = pl.DataFrame(
        {
            "actor_login": ["alice", "bob"],
            "t_cutoff": [date(2024, 1, 1), date(2024, 1, 1)],
            "cohort": ["positives", "negatives"],
        }
    )

    ownership, collaborators = extract_ownership_collab(
        StubOwnershipClickHouse(),  # type: ignore[arg-type]
        cohort,
    )

    assert ownership.select("actor_login", "is_own_repo", "event_count").to_dicts() == [
        {"actor_login": "alice", "is_own_repo": False, "event_count": 3},
        {"actor_login": "alice", "is_own_repo": True, "event_count": 7},
        {"actor_login": "bob", "is_own_repo": False, "event_count": 5},
    ]
    assert collaborators.select("owner_login", "distinct_collaborators").to_dicts() == [
        {"owner_login": "alice", "distinct_collaborators": 2}
    ]
    assert ownership.filter(pl.col("actor_login") == "alice").get_column(
        "cohort"
    ).unique().to_list() == ["positives"]


def test_deterministic_negative_matching_respects_bands_year_and_no_reuse() -> None:
    positives = pl.DataFrame(
        {
            "actor_login": ["p1", "p2"],
            "t_cutoff": [date(2024, 1, 1), date(2024, 1, 1)],
            "total_events": [100, 100],
            "first_seen_year": [2019, 2019],
        }
    )
    candidates = pl.DataFrame(
        {
            "actor_login": ["n1", "n2", "too_busy", "too_old", "founder"],
            "t_cutoff": [date(2024, 1, 1)] * 5,
            "total_events": [50, 200, 201, 100, 100],
            "first_seen_year": [2018, 2020, 2019, 2017, 2019],
            "actor_hash": [1, 2, 3, 4, 5],
        }
    )

    first = match_negatives(positives, candidates, {"founder"}, k=2, offset=0)
    second = match_negatives(positives, candidates, {"founder"}, k=2, offset=0)

    assert first.equals(second)
    assert set(first.get_column("actor_login")) == {"n1", "n2"}
    assert first.get_column("actor_login").n_unique() == first.height
