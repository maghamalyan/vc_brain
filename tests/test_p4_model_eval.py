import json
import shutil
from datetime import date
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from vc_brain.eval.report import (
    _lead_time,
    _matched_group_rank_metrics,
    case_control_correct,
    shuffle_labels_within_month,
)
from vc_brain.models.run import main
from vc_brain.models.train import (
    load_training_bundle,
    predict_probabilities,
    temporal_split,
    train_models,
)


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "p4_data"


def test_temporal_split_is_out_of_time_and_controls_follow_match_group() -> None:
    rows = []
    for login, batch_start, expected in (
        ("old", date(2022, 12, 1), "tuning_train"),
        ("valid", date(2023, 6, 1), "validation"),
        ("future", date(2024, 1, 1), "test"),
    ):
        for person_type in ("positive", "control"):
            rows.append(
                {
                    "batch_start_date": batch_start,
                    "match_group_id": login,
                    "person_type": person_type,
                    "y": int(person_type == "positive"),
                    "expected": expected,
                }
            )
    split = temporal_split(pl.DataFrame(rows))

    assert split.get_column("split").to_list() == split.get_column("expected").to_list()
    assert split.filter(
        (pl.col("split") == "tuning_train")
        & (pl.col("batch_start_date") > date(2022, 12, 31))
    ).is_empty()
    assert split.filter(
        (pl.col("split") != "test") & (pl.col("batch_start_date") >= date(2024, 1, 1))
    ).is_empty()
    assert split.group_by("match_group_id").agg(pl.col("split").n_unique()).get_column(
        "split"
    ).to_list() == [1, 1, 1]


def test_case_control_prior_odds_correction_is_exact() -> None:
    corrected = case_control_correct(
        np.array([0.5]), sample_prevalence=0.5, population_prevalence=0.01
    )
    assert corrected.tolist() == [0.01]


def test_matched_group_rank_uses_peak_scores_and_requires_three_members() -> None:
    scored = pl.DataFrame(
        {
            "match_group_id": ["g1"] * 6 + ["small"] * 2,
            "gh_login": ["founder", "founder", "c1", "c1", "c2", "c3", "p2", "n2"],
            "person_type": [
                "positive",
                "positive",
                "control",
                "control",
                "control",
                "control",
                "positive",
                "control",
            ],
            "score": [0.2, 0.9, 0.1, 0.8, 0.4, 0.3, 0.9, 0.1],
        }
    )

    metrics = _matched_group_rank_metrics(scored)

    assert metrics["groups"] == 1
    assert metrics["rank_1_probability"] == 1.0
    assert metrics["chance_rank_1_probability"] == 0.25
    assert metrics["top_half_probability"] == 1.0
    assert metrics["mean_normalized_rank"] == 0.0


def test_lead_time_requires_same_month_control_thresholds() -> None:
    scored = pl.DataFrame(
        {
            "gh_login": ["founder", "control"],
            "person_type": ["positive", "control"],
            "month": [date(2024, 1, 1), date(2024, 2, 1)],
            "batch_start_date": [date(2025, 1, 1), date(2025, 2, 1)],
            "score": [0.9, 0.1],
        }
    )

    with pytest.raises(ValueError, match="do not cover positive test months"):
        _lead_time(scored)


def test_label_shuffle_preserves_month_counts_and_honest_test_labels(
    tmp_path: Path,
) -> None:
    data_dir = tmp_path / "data"
    shutil.copytree(FIXTURE_ROOT, data_dir)
    main(["--stage", "features", "--data-dir", str(data_dir)])
    panel = pl.read_parquet(data_dir / "features" / "panel.parquet")
    shuffled = shuffle_labels_within_month(panel, seed=42)
    original_split = temporal_split(panel)
    shuffled_split = temporal_split(shuffled)

    assert original_split.filter(pl.col("split") == "test").get_column(
        "y"
    ).to_list() == (
        shuffled_split.filter(pl.col("split") == "test").get_column("y").to_list()
    )
    for fold in ("tuning_train", "validation"):
        original_counts = (
            original_split.filter(pl.col("split") == fold)
            .group_by("month")
            .agg(pl.col("y").sum())
            .sort("month")
        )
        shuffled_counts = (
            shuffled_split.filter(pl.col("split") == fold)
            .group_by("month")
            .agg(pl.col("y").sum())
            .sort("month")
        )
        assert original_counts.equals(shuffled_counts)


def test_fixture_cli_features_train_eval_produces_complete_report(
    tmp_path: Path,
) -> None:
    data_dir = tmp_path / "data"
    shutil.copytree(FIXTURE_ROOT, data_dir)

    main(["--stage", "all", "--data-dir", str(data_dir), "--top-k", "20"])

    report_path = data_dir / "eval" / "report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["null_run"]["passed"] is True
    assert report["person_month"]["logistic"]["pr_auc"] >= 0.0
    assert set(report["ablations"]) == {
        "levels_only",
        "levels_plus_dynamics",
        "levels_plus_dynamics_plus_traction",
        "all_plus_ownership_collab",
        "all_minus_tenure",
    }
    assert report["matched_group_rank"]["groups"] == 4
    assert len(report["tenure_stratified_within_month"]["quintiles"]) == 5
    assert report["feature_importance_review_required"] is True
    assert set(report["feature_capital_families"]) == {
        "cognitive",
        "human",
        "contextual",
        "financial",
    }
    assert report["feature_capital_families"]["financial"] == []
    assert set().union(*report["feature_capital_families"].values()) == set(
        report["feature_display_names"]
    )
    assert len(report["top_feature_importances"]) <= 20
    assert (data_dir / "eval" / "report.md").exists()
    assert all(Path(details["html"]).exists() for details in report["figures"].values())

    trajectories = pl.read_parquet(data_dir / "scores" / "trajectories.parquet")
    candidates = pl.read_parquet(data_dir / "scores" / "candidates.parquet")
    attributions = pl.read_parquet(data_dir / "scores" / "attributions.parquet")
    assert trajectories.columns == ["gh_login", "month", "score"]
    assert trajectories.get_column("gh_login").n_unique() == 24
    assert candidates.columns == [
        "gh_login",
        "founder_name",
        "company",
        "source",
        "current_score",
        "score_percentile",
        "momentum_3mo",
        "first_detection_month",
        "status",
    ]
    assert attributions.columns == [
        "login",
        "crossing_month",
        "feature",
        "delta_contrib",
    ]
    assert (
        attributions.group_by("login").len().get_column("len").to_list()
        == [3] * attributions.get_column("login").n_unique()
    )

    bundle = load_training_bundle(data_dir / "models")
    panel = temporal_split(pl.read_parquet(data_dir / "features" / "panel.parquet"))
    test = panel.filter(pl.col("split") == "test")
    before = predict_probabilities(bundle.selected_model, test, bundle.feature_names)
    assert bundle.lightgbm_model.get_params()["n_jobs"] == 1
    assert bundle.lightgbm_model.get_params()["deterministic"] is True
    train_models(
        panel_path=data_dir / "features" / "panel.parquet",
        output_dir=data_dir / "models",
    )
    repeated = load_training_bundle(data_dir / "models")
    after = predict_probabilities(repeated.selected_model, test, repeated.feature_names)
    np.testing.assert_array_equal(before, after)
