from datetime import date

import polars as pl

from vc_brain.semantics.pilot import (
    SEMANTIC_FEATURES,
    attach_semantic_features,
    bootstrap_comparison,
    build_pilot_panel,
    pilot_temporal_split,
    quarterly_semantic_features,
)


def _annotations() -> pl.DataFrame:
    return pl.DataFrame(
        [
            {
                "actor_login": "annotated",
                "quarter": date(2022, 10, 1),
                "annotation_status": "ok",
                "productization_markers": 1,
                "commercial_language": 0,
                "seriousness": 1,
                "domain_shift": 0,
                "audience_orientation": "developers",
                "collaboration_posture": "contributing",
                "stated_founding_intent": "none",
            },
            {
                "actor_login": "annotated",
                "quarter": date(2023, 1, 1),
                "annotation_status": "ok",
                "productization_markers": 3,
                "commercial_language": 2,
                "seriousness": 3,
                "domain_shift": 2,
                "audience_orientation": "customers",
                "collaboration_posture": "team_forming",
                "stated_founding_intent": "explicit",
            },
        ]
    )


def _panel() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "gh_login": ["annotated", "annotated", "unannotated"],
            "month": [date(2023, 1, 1), date(2023, 3, 1), date(2023, 1, 1)],
            "batch_start_date": [date(2022, 6, 1)] * 3,
            "match_group_id": ["g1", "g1", "g2"],
            "person_type": ["positive", "positive", "control"],
            "y": [0, 0, 0],
        }
    )


def test_quarter_features_are_ordinal_and_delta_only_adjacent_quarters() -> None:
    features = quarterly_semantic_features(_annotations()).sort("semantic_quarter")
    current = features.row(1, named=True)

    assert set(SEMANTIC_FEATURES).issubset(features.columns)
    assert current["audience_orientation"] == 3.0
    assert current["audience_orientation_delta"] == 2.0
    assert current["collaboration_posture"] == 3.0
    assert current["collaboration_posture_delta"] == 2.0
    assert current["stated_founding_intent"] == 2.0
    assert current["productization_markers_delta"] == 2.0


def test_month_fill_stays_within_quarter_and_unannotated_people_are_excluded() -> None:
    attached = attach_semantic_features(_panel(), _annotations())
    annotated = attached.filter(pl.col("gh_login") == "annotated")
    unannotated = attached.filter(pl.col("gh_login") == "unannotated")
    pilot = build_pilot_panel(_panel(), _annotations())

    assert annotated.get_column("productization_markers").to_list() == [3.0, 3.0]
    assert unannotated.get_column("productization_markers").to_list() == [None]
    assert pilot.get_column("gh_login").unique().to_list() == ["annotated"]


def test_pilot_split_keeps_date_contract_without_requiring_group_closure() -> None:
    panel = pl.DataFrame(
        {
            "batch_start_date": [
                date(2022, 12, 31),
                date(2023, 12, 31),
                date(2024, 1, 1),
            ],
            "match_group_id": ["orphan-control", "validation", "test"],
        }
    )

    assert pilot_temporal_split(panel).get_column("split").to_list() == [
        "tuning_train",
        "validation",
        "test",
    ]


def test_paired_person_bootstrap_is_seeded_and_keeps_ablation_rows_identical() -> None:
    rows = []
    for group_index in range(40):
        for person_index, person_type in enumerate(("positive", "control", "control")):
            rows.append(
                {
                    "gh_login": f"person-{group_index}-{person_index}",
                    "person_type": person_type,
                    "match_group_id": f"group-{group_index}",
                    "month": date(2024, 1, 1),
                    "y": int(person_type == "positive"),
                    "score": (
                        0.7
                        if person_type == "positive" and group_index % 2 == 0
                        else 0.3
                    ),
                }
            )
    counts = pl.DataFrame(rows)
    semantics = counts.with_columns(
        pl.when(pl.col("person_type") == "positive")
        .then(0.9)
        .otherwise(0.1)
        .alias("score")
    )

    first = bootstrap_comparison(counts, semantics, resamples=10, seed=42)
    second = bootstrap_comparison(counts, semantics, resamples=10, seed=42)

    assert first == second
    assert first["within_month_pr_auc"]["valid_resamples"] == 10
    assert first["matched_group_rank"]["rank_1_probability"]["valid_resamples"] == 10
