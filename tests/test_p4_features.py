import json
import shutil
from datetime import date
from pathlib import Path

import polars as pl
import pytest

from vc_brain.features.build import build_features


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "p4_data"


def build_fixture_panel(tmp_path: Path) -> tuple[pl.DataFrame, Path]:
    output_root = tmp_path / "built"
    panel = build_features(
        labels_path=FIXTURE_ROOT / "labels" / "founders.parquet",
        monthly_agg_dir=FIXTURE_ROOT / "events" / "monthly_agg",
        owned_repo_agg_dir=FIXTURE_ROOT / "events" / "owned_repo_agg",
        ownership_agg_dir=FIXTURE_ROOT / "events" / "ownership_agg",
        collab_influx_dir=FIXTURE_ROOT / "events" / "collab_influx",
        repo_creations_dir=FIXTURE_ROOT / "events" / "repo_creations",
        baselines_path=FIXTURE_ROOT / "events" / "baselines" / "monthly_totals.parquet",
        matches_path=FIXTURE_ROOT / "events" / "negatives" / "matched.parquet",
        output_path=output_root / "panel.parquet",
        data_card_json_path=output_root / "data_card.json",
        data_card_md_path=output_root / "data_card.md",
    )
    return panel, output_root


def test_panel_cutoff_gestation_labels_matching_exclusion_and_zero_activity(
    tmp_path: Path,
) -> None:
    panel, output_root = build_fixture_panel(tmp_path)
    founder = panel.filter(pl.col("gh_login") == "test_p1").sort("month")

    assert founder.height == 37
    assert founder.get_column("month").min() == date(2020, 3, 1)
    assert founder.get_column("month").max() == date(2023, 3, 1)
    assert founder.get_column("t_cutoff").unique().to_list() == [date(2023, 3, 1)]
    assert founder.get_column("gestation_start").unique().to_list() == [
        date(2023, 6, 1)
    ]
    assert founder.filter(pl.col("y") == 1).get_column("month").to_list() == [
        date(2022, 12, 1),
        date(2023, 1, 1),
        date(2023, 2, 1),
        date(2023, 3, 1),
    ]
    assert panel.filter(pl.col("gh_login") == "excluded_low_confidence").is_empty()

    zero = panel.filter(pl.col("gh_login") == "test_p4_zero")
    assert zero.get_column("no_gh_activity").unique().to_list() == [1.0]
    assert zero.get_column("tenure_months").unique().to_list() == [0.0]
    control = panel.filter(pl.col("gh_login") == "test_p1_control1")
    assert control.get_column("y").sum() == 0
    assert control.get_column("match_group_id").unique().to_list() == [
        "test_p1|2024-03-01"
    ]
    assert control.get_column("match_group_id").item(0) == founder.get_column(
        "match_group_id"
    ).item(0)

    card = json.loads((output_root / "data_card.json").read_text(encoding="utf-8"))
    assert {item["block"] for item in card["features"]} == {
        "levels",
        "dynamics",
        "traction",
        "ownership_collab",
        "semantics",
    }
    assert all(item["null_policy"] for item in card["features"])
    assert card["capital_families"]["financial"] == []
    assert "context_divergence_2q" in card["capital_families"]["cognitive"]
    assert (output_root / "data_card.md").exists()


def test_feature_windows_match_hand_computed_fixture_values(tmp_path: Path) -> None:
    panel, _ = build_fixture_panel(tmp_path)
    row = panel.filter(
        (pl.col("gh_login") == "test_p1") & (pl.col("month") == date(2023, 2, 1))
    ).row(0, named=True)

    # Push counts in Dec/Jan/Feb are 5/6/7; each monthly baseline is 1,000.
    assert row["activity_push_3m"] == pytest.approx(18_000.0)
    assert row["activity_push_1m"] == pytest.approx(7_000.0)
    # Two repos were created in Jan/Feb; four exist cumulatively by February.
    assert row["new_repos_3m"] == 2.0
    assert row["cumulative_repos"] == 4.0
    assert row["months_since_last_new_repo"] == 0.0
    # Owned-repo WatchEvent counts in Dec/Jan/Feb are 5/7/9, baseline 1,000.
    assert row["traction_stars_3m"] == pytest.approx(21_000.0)
    assert 0.0 < row["own_repo_share_3m"] < 1.0
    assert row["distinct_collaborators_3m"] > 0.0
    assert "context_divergence_2q" in row


def test_every_source_timestamp_is_strictly_before_cutoff() -> None:
    monthly = pl.read_parquet(FIXTURE_ROOT / "events" / "monthly_agg" / "*.parquet")
    owned = pl.read_parquet(FIXTURE_ROOT / "events" / "owned_repo_agg" / "*.parquet")
    ownership = pl.read_parquet(FIXTURE_ROOT / "events" / "ownership_agg" / "*.parquet")
    collaborators = pl.read_parquet(
        FIXTURE_ROOT / "events" / "collab_influx" / "*.parquet"
    )
    repos = pl.read_parquet(FIXTURE_ROOT / "events" / "repo_creations" / "*.parquet")

    assert monthly.filter(pl.col("month") >= pl.col("t_cutoff")).is_empty()
    assert owned.filter(pl.col("month") >= pl.col("t_cutoff")).is_empty()
    assert ownership.filter(pl.col("month") >= pl.col("t_cutoff")).is_empty()
    assert collaborators.filter(pl.col("month") >= pl.col("t_cutoff")).is_empty()
    assert repos.filter(
        pl.col("created_at").cast(pl.Date) >= pl.col("t_cutoff")
    ).is_empty()


def test_feature_builder_rejects_a_cutoff_month_source_row(tmp_path: Path) -> None:
    monthly_dir = tmp_path / "monthly"
    shutil.copytree(FIXTURE_ROOT / "events" / "monthly_agg", monthly_dir)
    positives_path = monthly_dir / "positives.parquet"
    positives = pl.read_parquet(positives_path)
    leaked = positives.row(0, named=True)
    leaked["month"] = leaked["t_cutoff"]
    pl.concat([positives, pl.DataFrame([leaked])]).write_parquet(positives_path)

    with pytest.raises(ValueError, match="Temporal leakage"):
        build_features(
            labels_path=FIXTURE_ROOT / "labels" / "founders.parquet",
            monthly_agg_dir=monthly_dir,
            owned_repo_agg_dir=FIXTURE_ROOT / "events" / "owned_repo_agg",
            ownership_agg_dir=FIXTURE_ROOT / "events" / "ownership_agg",
            collab_influx_dir=FIXTURE_ROOT / "events" / "collab_influx",
            repo_creations_dir=FIXTURE_ROOT / "events" / "repo_creations",
            baselines_path=FIXTURE_ROOT
            / "events"
            / "baselines"
            / "monthly_totals.parquet",
            matches_path=FIXTURE_ROOT / "events" / "negatives" / "matched.parquet",
            output_path=tmp_path / "panel.parquet",
            data_card_json_path=tmp_path / "data_card.json",
            data_card_md_path=tmp_path / "data_card.md",
        )


def test_feature_builder_rejects_null_required_aggregate_values(
    tmp_path: Path,
) -> None:
    monthly_dir = tmp_path / "monthly"
    shutil.copytree(FIXTURE_ROOT / "events" / "monthly_agg", monthly_dir)
    positives_path = monthly_dir / "positives.parquet"
    positives = pl.read_parquet(positives_path).with_row_index("row_number")
    positives = positives.with_columns(
        pl.when(pl.col("row_number") == 0)
        .then(pl.lit(None, dtype=pl.Int64))
        .otherwise(pl.col("event_count"))
        .alias("event_count")
    ).drop("row_number")
    positives.write_parquet(positives_path)

    with pytest.raises(ValueError, match="nulls in required values"):
        build_features(
            labels_path=FIXTURE_ROOT / "labels" / "founders.parquet",
            monthly_agg_dir=monthly_dir,
            owned_repo_agg_dir=FIXTURE_ROOT / "events" / "owned_repo_agg",
            ownership_agg_dir=FIXTURE_ROOT / "events" / "ownership_agg",
            collab_influx_dir=FIXTURE_ROOT / "events" / "collab_influx",
            repo_creations_dir=FIXTURE_ROOT / "events" / "repo_creations",
            baselines_path=FIXTURE_ROOT
            / "events"
            / "baselines"
            / "monthly_totals.parquet",
            matches_path=FIXTURE_ROOT / "events" / "negatives" / "matched.parquet",
            output_path=tmp_path / "panel.parquet",
            data_card_json_path=tmp_path / "data_card.json",
            data_card_md_path=tmp_path / "data_card.md",
        )
