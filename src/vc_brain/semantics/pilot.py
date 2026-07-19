"""Checkpoint-only semantic-feature pilot and demo artifacts.

This module intentionally has no annotation client dependency.  It consumes the
frozen annotation parquet and never schedules or retries LLM work.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import lightgbm as lgb
import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from vc_brain.models.train import lightgbm_params, logistic_params
from vc_brain.semantics.validation import write_validation_sample

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = PROJECT_ROOT / "data"
BOOTSTRAP_RESAMPLES = 200
BOOTSTRAP_SEED = 20260719
# Keep the production null-run seed as well as its shuffle/gate definition.
NULL_SEED = 18

AUDIENCE_LEVELS = {
    "self": 0.0,
    "developers": 1.0,
    "end_users": 2.0,
    "customers": 3.0,
}
COLLABORATION_LEVELS = {
    "solo": 0.0,
    "contributing": 1.0,
    "leading": 2.0,
    "team_forming": 3.0,
}
INTENT_LEVELS = {"none": 0.0, "implicit": 1.0, "explicit": 2.0}
SEMANTIC_LEVELS = (
    "productization_markers",
    "commercial_language",
    "seriousness",
    "domain_shift",
    "audience_orientation",
    "collaboration_posture",
    "stated_founding_intent",
)
SEMANTIC_FEATURES = (
    *SEMANTIC_LEVELS,
    *(f"{name}_delta" for name in SEMANTIC_LEVELS),
)


@dataclass(frozen=True)
class PilotFit:
    selected_model: Pipeline | lgb.LGBMClassifier
    selected_model_name: str
    validation: dict[str, float]


def _atomic_write_text(value: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def _previous_quarter(quarter: date) -> date:
    if quarter.month == 1:
        return date(quarter.year - 1, 10, 1)
    return date(quarter.year, quarter.month - 3, 1)


def _ordinal(value: object, levels: dict[str, float], field: str) -> float | None:
    if value is None:
        return None
    normalized = str(value)
    if normalized not in levels:
        raise ValueError(f"Unknown {field} value: {normalized!r}")
    return levels[normalized]


def quarterly_semantic_features(annotations: pl.DataFrame) -> pl.DataFrame:
    """Encode successful person-quarters and exact adjacent-quarter deltas."""
    required = {
        "actor_login",
        "quarter",
        "annotation_status",
        "productization_markers",
        "commercial_language",
        "seriousness",
        "domain_shift",
        "audience_orientation",
        "collaboration_posture",
        "stated_founding_intent",
    }
    missing = required - set(annotations.columns)
    if missing:
        raise ValueError(f"Annotations are missing columns: {sorted(missing)}")
    successful = annotations.filter(pl.col("annotation_status") == "ok")
    duplicates = (
        successful.group_by("actor_login", "quarter").len().filter(pl.col("len") != 1)
    )
    if not duplicates.is_empty():
        raise ValueError("Annotations contain duplicate successful person-quarters")

    levels: dict[tuple[str, date], dict[str, float | None]] = {}
    for row in successful.to_dicts():
        key = (str(row["actor_login"]).lower(), row["quarter"])
        levels[key] = {
            "productization_markers": _number(row["productization_markers"]),
            "commercial_language": _number(row["commercial_language"]),
            "seriousness": _number(row["seriousness"]),
            "domain_shift": _number(row["domain_shift"]),
            "audience_orientation": _ordinal(
                row["audience_orientation"], AUDIENCE_LEVELS, "audience_orientation"
            ),
            "collaboration_posture": _ordinal(
                row["collaboration_posture"],
                COLLABORATION_LEVELS,
                "collaboration_posture",
            ),
            "stated_founding_intent": _ordinal(
                row["stated_founding_intent"],
                INTENT_LEVELS,
                "stated_founding_intent",
            ),
        }

    rows: list[dict[str, object]] = []
    for (login, quarter), values in sorted(levels.items()):
        previous = levels.get((login, _previous_quarter(quarter)))
        deltas = {
            f"{name}_delta": (
                float(value) - float(previous[name])
                if value is not None
                and previous is not None
                and previous[name] is not None
                else None
            )
            for name, value in values.items()
        }
        rows.append(
            {
                "gh_login": login,
                "semantic_quarter": quarter,
                **values,
                **deltas,
            }
        )
    schema = {
        "gh_login": pl.String,
        "semantic_quarter": pl.Date,
        **{name: pl.Float64 for name in SEMANTIC_FEATURES},
    }
    return pl.DataFrame(rows, schema=schema)


def _number(value: object) -> float | None:
    return float(value) if value is not None else None


def attach_semantic_features(
    panel: pl.DataFrame, annotations: pl.DataFrame
) -> pl.DataFrame:
    """Left-join quarter features; non-checkpoint people remain explicitly null."""
    features = quarterly_semantic_features(annotations)
    return (
        panel.with_columns(
            pl.date(
                pl.col("month").dt.year(),
                ((pl.col("month").dt.month() - 1) // 3) * 3 + 1,
                1,
            ).alias("semantic_quarter")
        )
        .join(features, on=["gh_login", "semantic_quarter"], how="left")
        .drop("semantic_quarter")
    )


def build_pilot_panel(panel: pl.DataFrame, annotations: pl.DataFrame) -> pl.DataFrame:
    """Restrict to checkpoint people before models can neutral-impute nulls."""
    checkpoint_people = annotations.select(
        pl.col("actor_login").str.to_lowercase().alias("gh_login")
    ).unique()
    return attach_semantic_features(panel, annotations).join(
        checkpoint_people, on="gh_login", how="semi"
    )


def pilot_temporal_split(panel: pl.DataFrame) -> pl.DataFrame:
    """Apply the production date rules while permitting restricted orphan groups."""
    split = panel.with_columns(
        pl.when(pl.col("batch_start_date") <= date(2022, 12, 31))
        .then(pl.lit("tuning_train"))
        .when(pl.col("batch_start_date") <= date(2023, 12, 31))
        .then(pl.lit("validation"))
        .otherwise(pl.lit("test"))
        .alias("split")
    )
    crossed = (
        split.group_by("match_group_id")
        .agg(pl.col("split").n_unique().alias("folds"))
        .filter(pl.col("folds") != 1)
    )
    if not crossed.is_empty():
        raise ValueError("At least one restricted match group crosses temporal folds")
    return split


def _matrix(frame: pl.DataFrame, features: list[str]) -> np.ndarray:
    matrix = (
        frame.select(features)
        .with_columns(pl.all().fill_null(0.0))
        .to_numpy()
        .astype(np.float64, copy=False)
    )
    if not np.isfinite(matrix).all():
        raise ValueError(
            "Pilot model features must be finite after documented imputation"
        )
    return matrix


def _labels(frame: pl.DataFrame) -> np.ndarray:
    return frame.get_column("y").to_numpy().astype(np.int8, copy=False)


def _scale_pos_weight(labels: np.ndarray) -> float:
    positives = int(labels.sum())
    negatives = int(labels.size - positives)
    if positives == 0 or negatives == 0:
        raise ValueError("Pilot training split must contain both classes")
    return negatives / positives


def fit_pilot_model(panel: pl.DataFrame, features: list[str]) -> PilotFit:
    """Use the production candidates, hyperparameters, and selection rule."""
    split = pilot_temporal_split(panel)
    tuning = split.filter(pl.col("split") == "tuning_train")
    validation = split.filter(pl.col("split") == "validation")
    development = split.filter(pl.col("split") != "test")
    test = split.filter(pl.col("split") == "test")
    for name, frame in (
        ("tuning_train", tuning),
        ("validation", validation),
        ("test", test),
    ):
        if frame.is_empty() or set(np.unique(_labels(frame))) != {0, 1}:
            raise ValueError(f"Pilot {name} split must be nonempty and binary")

    logistic_tuning = Pipeline(
        [
            ("standardize", StandardScaler()),
            ("classifier", LogisticRegression(**logistic_params())),
        ]
    ).fit(_matrix(tuning, features), _labels(tuning))
    logistic_validation_scores = logistic_tuning.predict_proba(
        _matrix(validation, features)
    )[:, 1]
    logistic_pr_auc = float(
        average_precision_score(_labels(validation), logistic_validation_scores)
    )

    lightgbm_tuning = lgb.LGBMClassifier(
        **lightgbm_params(scale_pos_weight=_scale_pos_weight(_labels(tuning)))
    )
    lightgbm_tuning.fit(
        _matrix(tuning, features),
        _labels(tuning),
        eval_X=_matrix(validation, features),
        eval_y=_labels(validation),
        eval_metric="average_precision",
        callbacks=[lgb.early_stopping(30, first_metric_only=True, verbose=False)],
    )
    lightgbm_validation_scores = lightgbm_tuning.predict_proba(
        _matrix(validation, features)
    )[:, 1]
    lightgbm_pr_auc = float(
        average_precision_score(_labels(validation), lightgbm_validation_scores)
    )
    selected_name = (
        "lightgbm" if lightgbm_pr_auc > logistic_pr_auc * 1.10 else "logistic"
    )
    best_iteration = int(
        lightgbm_tuning.best_iteration_ or lightgbm_tuning.n_estimators
    )

    logistic_final = Pipeline(
        [
            ("standardize", StandardScaler()),
            ("classifier", LogisticRegression(**logistic_params())),
        ]
    ).fit(_matrix(development, features), _labels(development))
    lightgbm_final = lgb.LGBMClassifier(
        **lightgbm_params(
            scale_pos_weight=_scale_pos_weight(_labels(development)),
            n_estimators=max(best_iteration, 1),
        )
    ).fit(_matrix(development, features), _labels(development))
    return PilotFit(
        selected_model=(
            lightgbm_final if selected_name == "lightgbm" else logistic_final
        ),
        selected_model_name=selected_name,
        validation={
            "logistic_pr_auc": logistic_pr_auc,
            "lightgbm_pr_auc": lightgbm_pr_auc,
            "selection_threshold_relative": 0.10,
        },
    )


def _predict(
    model: Pipeline | lgb.LGBMClassifier, frame: pl.DataFrame, features: list[str]
) -> np.ndarray:
    return np.asarray(model.predict_proba(_matrix(frame, features))[:, 1])


def within_month_metrics(
    months: np.ndarray, labels: np.ndarray, scores: np.ndarray
) -> dict[str, float | int]:
    """Production positive-weighted macro PR-AUC within calendar month."""
    weighted = 0.0
    base_weighted = 0.0
    positive_weight = 0
    months_used = 0
    for month in np.unique(months):
        selected = months == month
        month_labels = labels[selected]
        positives = int(month_labels.sum())
        if positives == 0 or positives == len(month_labels):
            continue
        weighted += (
            float(average_precision_score(month_labels, scores[selected])) * positives
        )
        base_weighted += float(month_labels.mean()) * positives
        positive_weight += positives
        months_used += 1
    if not positive_weight:
        raise ValueError("No non-degenerate months remain for within-month PR-AUC")
    return {
        "within_month_pr_auc": weighted / positive_weight,
        "within_month_base_rate": base_weighted / positive_weight,
        "months_evaluated": months_used,
    }


def matched_group_rank_metrics(scored: pl.DataFrame) -> dict[str, float | int | str]:
    """Evaluate founder peak rank in surviving groups of at least three people."""
    peaks = (
        scored.group_by("match_group_id", "gh_login")
        .agg(pl.col("person_type").first(), pl.col("score").max().alias("peak_score"))
        .sort("match_group_id", "gh_login")
    )
    rank_one: list[float] = []
    top_half: list[float] = []
    normalized: list[float] = []
    sizes: list[int] = []
    for group in peaks.partition_by("match_group_id"):
        founders = group.filter(pl.col("person_type") == "positive")
        if founders.height != 1 or group.height < 3:
            continue
        founder_score = float(founders.get_column("peak_score").item())
        values = [float(value) for value in group.get_column("peak_score")]
        higher = sum(value > founder_score for value in values)
        tied = sum(value == founder_score for value in values)
        ranks = list(range(higher + 1, higher + tied + 1))
        half = math.ceil(group.height / 2)
        rank_one.append(1.0 / tied if higher == 0 else 0.0)
        top_half.append(sum(rank <= half for rank in ranks) / tied)
        normalized.append(sum((rank - 1) / (group.height - 1) for rank in ranks) / tied)
        sizes.append(group.height)
    if not sizes:
        raise ValueError("No eligible matched groups survive the pilot restriction")
    return {
        "groups": len(sizes),
        "rank_1_probability": float(np.mean(rank_one)),
        "chance_rank_1_probability": float(np.mean([1.0 / size for size in sizes])),
        "top_half_probability": float(np.mean(top_half)),
        "mean_normalized_rank": float(np.mean(normalized)),
        "definition": "Expected rank under uniform ordering within peak-score ties; 0 normalized rank is best.",
    }


def _shuffle_development_labels(panel: pl.DataFrame, seed: int) -> pl.DataFrame:
    split = pilot_temporal_split(panel).with_row_index("_row")
    shuffled = split.get_column("y").to_numpy().copy()
    rng = np.random.default_rng(seed)
    for fold in ("tuning_train", "validation"):
        fold_frame = split.filter(pl.col("split") == fold)
        for month in fold_frame.get_column("month").unique().sort().to_list():
            indices = (
                fold_frame.filter(pl.col("month") == month)
                .get_column("_row")
                .to_numpy()
            )
            shuffled[indices] = rng.permutation(shuffled[indices])
    return split.drop("split", "_row").with_columns(
        pl.Series("y", shuffled, dtype=pl.Int64)
    )


def _evaluate_arm(
    panel: pl.DataFrame, features: list[str], *, name: str
) -> tuple[dict[str, Any], pl.DataFrame]:
    fit = fit_pilot_model(panel, features)
    test = pilot_temporal_split(panel).filter(pl.col("split") == "test")
    labels = _labels(test)
    scores = _predict(fit.selected_model, test, features)
    months = test.get_column("month").to_numpy()
    within = within_month_metrics(months, labels, scores)
    scored = test.select(
        "gh_login", "person_type", "match_group_id", "month", "y"
    ).with_columns(pl.Series("score", scores))
    matched = matched_group_rank_metrics(scored)

    shuffled = _shuffle_development_labels(panel, NULL_SEED)
    null_fit = fit_pilot_model(shuffled, features)
    null_test = pilot_temporal_split(shuffled).filter(pl.col("split") == "test")
    null_labels = _labels(null_test)
    null_scores = _predict(null_fit.selected_model, null_test, features)
    null_within = within_month_metrics(
        null_test.get_column("month").to_numpy(), null_labels, null_scores
    )
    null_base = float(null_within["within_month_base_rate"])
    null_limit = max(null_base * 2.0, null_base + 0.02)
    null_score = float(null_within["within_month_pr_auc"])
    result = {
        "name": name,
        "feature_count": len(features),
        "selected_model": fit.selected_model_name,
        "validation": fit.validation,
        "test": {
            **within,
            "global_pr_auc": float(average_precision_score(labels, scores)),
            "global_roc_auc": float(roc_auc_score(labels, scores)),
            "rows": test.height,
            "people": test.get_column("gh_login").n_unique(),
        },
        "matched_group_rank": matched,
        "null_gate": {
            "method": "Development labels shuffled within calendar month; held-out test labels unchanged; gate uses within-month PR-AUC.",
            "seed": NULL_SEED,
            "selected_model": null_fit.selected_model_name,
            "within_month_pr_auc": null_score,
            "within_month_base_rate": null_base,
            "maximum_allowed_within_month_pr_auc": null_limit,
            "passed": null_score <= null_limit,
        },
    }
    return result, scored


def _ci(values: list[float]) -> list[float]:
    if not values:
        raise ValueError("No valid bootstrap values")
    return [
        float(np.percentile(values, 2.5)),
        float(np.percentile(values, 97.5)),
    ]


def bootstrap_comparison(
    counts_scored: pl.DataFrame,
    semantics_scored: pl.DataFrame,
    *,
    resamples: int = BOOTSTRAP_RESAMPLES,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, Any]:
    """Paired test-person bootstrap, including surviving-group rank metrics."""
    keys = ["gh_login", "person_type", "match_group_id", "month", "y"]
    if not counts_scored.select(keys).equals(semantics_scored.select(keys)):
        raise ValueError("Ablation score frames do not describe identical test rows")
    people = sorted(counts_scored.get_column("gh_login").unique().to_list())
    row_indices = {
        person: np.flatnonzero(
            counts_scored.get_column("gh_login").to_numpy() == person
        )
        for person in people
    }
    rng = np.random.default_rng(seed)
    within_counts: list[float] = []
    within_semantics: list[float] = []
    matched_values: dict[str, dict[str, list[float]]] = {
        metric: {"counts_only": [], "counts_plus_semantics": []}
        for metric in (
            "rank_1_probability",
            "top_half_probability",
            "mean_normalized_rank",
        )
    }
    for _ in range(resamples):
        draws = rng.choice(people, size=len(people), replace=True).tolist()
        indices = np.concatenate([row_indices[person] for person in draws])
        pseudo_logins = np.concatenate(
            [
                np.repeat(f"{person}#bootstrap-{draw_index}", len(row_indices[person]))
                for draw_index, person in enumerate(draws)
            ]
        )
        sampled_counts = counts_scored[indices].with_columns(
            pl.Series("gh_login", pseudo_logins)
        )
        sampled_semantics = semantics_scored[indices].with_columns(
            pl.Series("gh_login", pseudo_logins)
        )
        labels = sampled_counts.get_column("y").to_numpy()
        months = sampled_counts.get_column("month").to_numpy()
        count_value = float(
            within_month_metrics(
                months, labels, sampled_counts.get_column("score").to_numpy()
            )["within_month_pr_auc"]
        )
        semantic_value = float(
            within_month_metrics(
                months, labels, sampled_semantics.get_column("score").to_numpy()
            )["within_month_pr_auc"]
        )
        within_counts.append(count_value)
        within_semantics.append(semantic_value)
        try:
            count_matched = matched_group_rank_metrics(sampled_counts)
            semantic_matched = matched_group_rank_metrics(sampled_semantics)
        except ValueError:
            continue
        for metric in matched_values:
            matched_values[metric]["counts_only"].append(float(count_matched[metric]))
            matched_values[metric]["counts_plus_semantics"].append(
                float(semantic_matched[metric])
            )

    within_delta = [
        semantics - counts
        for counts, semantics in zip(within_counts, within_semantics, strict=True)
    ]
    matched_output: dict[str, Any] = {}
    for metric, arms in matched_values.items():
        deltas = [
            semantics - counts
            for counts, semantics in zip(
                arms["counts_only"], arms["counts_plus_semantics"], strict=True
            )
        ]
        matched_output[metric] = {
            "counts_only_95_ci": _ci(arms["counts_only"]),
            "counts_plus_semantics_95_ci": _ci(arms["counts_plus_semantics"]),
            "paired_delta_95_ci": _ci(deltas),
            "valid_resamples": len(deltas),
        }
    return {
        "unit": "held-out people sampled with replacement",
        "paired": True,
        "resamples_requested": resamples,
        "seed": seed,
        "within_month_pr_auc": {
            "counts_only_95_ci": _ci(within_counts),
            "counts_plus_semantics_95_ci": _ci(within_semantics),
            "paired_delta_95_ci": _ci(within_delta),
            "valid_resamples": len(within_delta),
        },
        "matched_group_rank": matched_output,
    }


def _split_summary(panel: pl.DataFrame) -> dict[str, Any]:
    split = pilot_temporal_split(panel)
    by_fold: dict[str, Any] = {}
    for fold in ("tuning_train", "validation", "test"):
        frame = split.filter(pl.col("split") == fold)
        by_fold[fold] = {
            "people": frame.get_column("gh_login").n_unique(),
            "founders": frame.filter(pl.col("person_type") == "positive")
            .get_column("gh_login")
            .n_unique(),
            "controls": frame.filter(pl.col("person_type") == "control")
            .get_column("gh_login")
            .n_unique(),
            "rows": frame.height,
        }
    return {
        "development": {
            "people": split.filter(pl.col("split") != "test")
            .get_column("gh_login")
            .n_unique(),
            "rows": split.filter(pl.col("split") != "test").height,
        },
        "test": {
            "people": split.filter(pl.col("split") == "test")
            .get_column("gh_login")
            .n_unique(),
            "rows": split.filter(pl.col("split") == "test").height,
        },
        "folds": by_fold,
    }


def _export_demo_trajectories(
    annotations: pl.DataFrame,
    detector_scores_path: Path,
    output_dir: Path,
) -> list[dict[str, object]]:
    scores = pl.read_parquet(detector_scores_path)
    founders = (
        annotations.filter(pl.col("person_type") == "positive")
        .select(pl.col("actor_login").str.to_lowercase().alias("gh_login"))
        .unique()
    )
    top = (
        scores.join(founders, on="gh_login", how="inner")
        .group_by("gh_login")
        .agg(pl.col("score").max().alias("detector_score"))
        .sort(["detector_score", "gh_login"], descending=[True, False])
        .head(3)
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    exported: list[dict[str, object]] = []
    for top_row in top.to_dicts():
        login = str(top_row["gh_login"])
        trajectory: list[dict[str, object]] = []
        for row in (
            annotations.filter(pl.col("actor_login").str.to_lowercase() == login)
            .sort("quarter")
            .to_dicts()
        ):
            successful = row["annotation_status"] == "ok"
            trajectory.append(
                {
                    "quarter": row["quarter"].isoformat(),
                    "building_what": (
                        {
                            "category": row["building_what_category"],
                            "description": row["building_what_description"],
                        }
                        if successful
                        else None
                    ),
                    "audience": row["audience_orientation"] if successful else None,
                    "productization": row["productization_markers"]
                    if successful
                    else None,
                    "commercial": row["commercial_language"] if successful else None,
                    "intent": row["stated_founding_intent"] if successful else None,
                    "seriousness": row["seriousness"] if successful else None,
                }
            )
        payload = {
            "login": login,
            "detector_score": float(top_row["detector_score"]),
            "trajectory": trajectory,
        }
        _atomic_write_text(
            json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
            output_dir / f"{login}.json",
        )
        exported.append(
            {
                "login": login,
                "detector_score": float(top_row["detector_score"]),
                "quarters": len(trajectory),
            }
        )
    if len(exported) != 3:
        raise ValueError(
            f"Expected three scored annotated founders; found {len(exported)}"
        )
    return exported


def _render_markdown(report: dict[str, Any]) -> str:
    counts = report["ablations"]["counts_only"]
    semantic = report["ablations"]["counts_plus_semantics"]
    bootstrap = report["bootstrap"]["within_month_pr_auc"]
    delta = (
        semantic["test"]["within_month_pr_auc"] - counts["test"]["within_month_pr_auc"]
    )
    delta_ci = bootstrap["paired_delta_95_ci"]
    direction = (
        "No detectable movement"
        if delta_ci[0] <= 0.0 <= delta_ci[1]
        else "Detectable movement"
    )
    cohort = report["cohort"]
    split = report["split"]
    matched_counts = counts["matched_group_rank"]
    matched_semantic = semantic["matched_group_rank"]
    lines = [
        "# Semantic annotation pilot\n\n",
        "> **Pilot, not a production estimate.** The checkpoint is an alphabetical prefix of Cohort-D, sample sizes are small, and all confidence intervals are 200-resample held-out-person bootstraps.\n\n",
        "## Key result\n\n",
        f"**On {cohort['people']} people, adding read-the-work features moved within-month PR-AUC from {counts['test']['within_month_pr_auc']:.4f} to {semantic['test']['within_month_pr_auc']:.4f} (paired person-bootstrap change {delta:+.4f}, 95% CI [{delta_ci[0]:+.4f}, {delta_ci[1]:+.4f}]; 200 resamples).**\n\n",
        f"{direction}: the confidence interval {'includes' if delta_ci[0] <= 0.0 <= delta_ci[1] else 'excludes'} zero. This is a pilot result and should not be generalized beyond the checkpoint.\n\n",
        f"Both shuffled-label null gates **{'PASS' if counts['null_gate']['passed'] and semantic['null_gate']['passed'] else 'FAIL'}** on this restricted prefix. Because the null models retain {'no ' if counts['null_gate']['passed'] and semantic['null_gate']['passed'] else ''}excess within-month ranking skill, treat the ablation estimates as descriptive only.\n\n",
        "## Label and split sanity\n\n",
        f"The restricted panel has **{cohort['people']} people**: **{cohort['founders']} founders** and **{cohort['controls']} controls**, across {cohort['panel_rows']:,} person-month rows. Development has {split['development']['people']} people / {split['development']['rows']:,} rows; held-out test has {split['test']['people']} people / {split['test']['rows']:,} rows.\n\n",
        "| Fold | People | Founders | Controls | Rows |\n|---|---:|---:|---:|---:|\n",
    ]
    for name, values in split["folds"].items():
        lines.append(
            f"| {name} | {values['people']} | {values['founders']} | {values['controls']} | {values['rows']:,} |\n"
        )
    lines.extend(
        [
            "\n## Ablation and null gates\n\n",
            "| Arm | Features | Selected model | Within-month PR-AUC | Global PR-AUC | Null within-month PR-AUC / limit | Gate |\n|---|---:|---|---:|---:|---:|---|\n",
        ]
    )
    for name, values in report["ablations"].items():
        gate = values["null_gate"]
        lines.append(
            f"| {name} | {values['feature_count']} | {values['selected_model']} | {values['test']['within_month_pr_auc']:.4f} | {values['test']['global_pr_auc']:.4f} | {gate['within_month_pr_auc']:.4f} / {gate['maximum_allowed_within_month_pr_auc']:.4f} | {'PASS' if gate['passed'] else 'FAIL'} |\n"
        )
    lines.extend(
        [
            "\nMissing semantic values are retained as null at the feature boundary and neutral-imputed only after restricting to checkpoint members. No unannotated person enters either arm. Both arms use identical people and rows.\n\n",
            "## Surviving matched-group ranking\n\n",
            f"Exactly **{matched_counts['groups']} held-out matched groups** retain one founder and at least two controls after the prefix restriction. Founder rank-1 probability moved from **{matched_counts['rank_1_probability']:.4f}** to **{matched_semantic['rank_1_probability']:.4f}** (chance {matched_counts['chance_rank_1_probability']:.4f}); top-half probability moved from {matched_counts['top_half_probability']:.4f} to {matched_semantic['top_half_probability']:.4f}; mean normalized rank moved from {matched_counts['mean_normalized_rank']:.4f} to {matched_semantic['mean_normalized_rank']:.4f} (lower is better).\n\n",
            "## Annotation coverage and demo artifacts\n\n",
            f"The checkpoint contains {cohort['annotation_rows']:,} attempted person-quarters: {cohort['successful_annotation_rows']:,} successful and {cohort['failed_annotation_rows']} failed. Failures remain null; no annotation work was resumed. The blind 40-bundle validation sample contains mixed founders/controls and time strata without outcome-label fields.\n\n",
            "Top scored annotated founders exported for the demo:\n\n",
        ]
    )
    for item in report["demo_trajectories"]:
        lines.append(
            f"- `{item['login']}` — detector peak {item['detector_score']:.6f}, {item['quarters']} annotated quarters\n"
        )
    return "".join(lines)


def run_semantics_pilot(
    *, data_root: Path = DATA_ROOT, project_root: Path = PROJECT_ROOT
) -> dict[str, Any]:
    """Run the checkpoint-only pilot and write all requested artifacts."""
    panel = pl.read_parquet(data_root / "features" / "panel.parquet")
    annotations = pl.read_parquet(data_root / "semantics" / "annotations.parquet")
    counts_features = json.loads(
        (data_root / "models" / "feature_list.json").read_text(encoding="utf-8")
    )
    pilot_panel = build_pilot_panel(panel, annotations)
    missing_counts = {
        name: pilot_panel.get_column(name).null_count() for name in SEMANTIC_FEATURES
    }
    counts_result, counts_scored = _evaluate_arm(
        pilot_panel, counts_features, name="counts_only"
    )
    semantic_features = [*counts_features, *SEMANTIC_FEATURES]
    semantic_result, semantics_scored = _evaluate_arm(
        pilot_panel, semantic_features, name="counts_plus_semantics"
    )
    bootstrap = bootstrap_comparison(counts_scored, semantics_scored)
    validation_path = write_validation_sample(
        items_path=data_root / "semantics" / "text" / "items.parquet",
        annotations_path=data_root / "semantics" / "annotations.parquet",
        output_path=project_root
        / "docs"
        / "exploration"
        / "annotation_validation_sample.md",
    )
    demo = _export_demo_trajectories(
        annotations,
        data_root / "scores" / "trajectories.parquet",
        data_root / "semantics" / "demo_trajectories",
    )
    founders = (
        pilot_panel.filter(pl.col("person_type") == "positive")
        .get_column("gh_login")
        .n_unique()
    )
    controls = (
        pilot_panel.filter(pl.col("person_type") == "control")
        .get_column("gh_login")
        .n_unique()
    )
    report: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "pilot_warning": "Alphabetical checkpoint prefix of Cohort-D; small-N exploratory result, not a production estimate.",
        "contract": {
            "annotation_checkpoint_only": True,
            "additional_llm_annotation_run": False,
            "counts_feature_source": "data/models/feature_list.json",
            "semantic_features": list(SEMANTIC_FEATURES),
            "audience_encoding": AUDIENCE_LEVELS,
            "collaboration_encoding": COLLABORATION_LEVELS,
            "intent_encoding": INTENT_LEVELS,
            "within_quarter_month_fill": True,
            "unannotated_people_excluded": True,
            "model_null_policy": "Semantic nulls are preserved through panel restriction, then neutral-imputed to zero by the unchanged model-matrix policy.",
        },
        "cohort": {
            "people": pilot_panel.get_column("gh_login").n_unique(),
            "founders": founders,
            "controls": controls,
            "panel_rows": pilot_panel.height,
            "annotation_rows": annotations.height,
            "successful_annotation_rows": annotations.filter(
                pl.col("annotation_status") == "ok"
            ).height,
            "failed_annotation_rows": annotations.filter(
                pl.col("annotation_status") != "ok"
            ).height,
            "semantic_null_rows_by_feature": missing_counts,
        },
        "split": _split_summary(pilot_panel),
        "ablations": {
            "counts_only": counts_result,
            "counts_plus_semantics": semantic_result,
        },
        "bootstrap": bootstrap,
        "validation_sample": str(validation_path.relative_to(project_root)),
        "demo_trajectories": demo,
    }
    delta = (
        semantic_result["test"]["within_month_pr_auc"]
        - counts_result["test"]["within_month_pr_auc"]
    )
    report["key_result"] = {
        "metric": "within_month_pr_auc",
        "counts_only": counts_result["test"]["within_month_pr_auc"],
        "counts_plus_semantics": semantic_result["test"]["within_month_pr_auc"],
        "absolute_change": delta,
        "paired_change_95_ci": bootstrap["within_month_pr_auc"]["paired_delta_95_ci"],
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "both_null_gates_passed": (
            counts_result["null_gate"]["passed"]
            and semantic_result["null_gate"]["passed"]
        ),
        "interpretation": "No detectable lift in this pilot; the paired change interval includes zero, and both shuffled-label null gates failed.",
    }
    output_json = data_root / "eval" / "semantics_pilot.json"
    output_md = data_root / "eval" / "semantics_pilot.md"
    _atomic_write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n",
        output_json,
    )
    _atomic_write_text(_render_markdown(report), output_md)
    return report


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args(argv)
    report = run_semantics_pilot(
        data_root=args.data_root.resolve(), project_root=args.project_root.resolve()
    )
    print(json.dumps(report["key_result"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
