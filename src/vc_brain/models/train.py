"""Deterministic temporal training for the Tier-1 founder hazard model."""

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import joblib
import lightgbm as lgb
import numpy as np
import polars as pl
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from vc_brain.features.build import DATA_CARD_JSON_PATH, METADATA_COLUMNS, PANEL_PATH

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = Path(os.environ.get("VC_BRAIN_DATA_DIR", PROJECT_ROOT / "data"))
MODELS_DIR = DATA_ROOT / "models"
RANDOM_SEED = 20240719


@dataclass
class TrainingBundle:
    feature_names: list[str]
    logistic_model: Pipeline
    lightgbm_model: lgb.LGBMClassifier
    selected_model_name: str
    validation_metrics: dict[str, float]
    split_counts: dict[str, int]
    lightgbm_best_iteration: int

    @property
    def selected_model(self) -> Pipeline | lgb.LGBMClassifier:
        return (
            self.lightgbm_model
            if self.selected_model_name == "lightgbm"
            else self.logistic_model
        )


def _atomic_write_json(payload: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, suffix=".json.tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def _atomic_joblib_dump(value: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, suffix=".joblib.tmp")
    os.close(descriptor)
    try:
        joblib.dump(value, temporary)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def model_feature_names(panel: pl.DataFrame) -> list[str]:
    excluded = set(METADATA_COLUMNS)
    names = [column for column in panel.columns if column not in excluded]
    if not names:
        raise ValueError("Panel contains no model feature columns")
    return names


def temporal_split(panel: pl.DataFrame) -> pl.DataFrame:
    """Assign folds solely from group B, keeping controls with their positive."""
    required = {"batch_start_date", "match_group_id", "person_type", "y"}
    missing = required - set(panel.columns)
    if missing:
        raise ValueError(f"Panel is missing split columns: {sorted(missing)}")
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
        raise ValueError("At least one matched group crosses temporal folds")
    controls_without_positive = (
        split.group_by("match_group_id")
        .agg(
            pl.col("person_type").eq("positive").any().alias("has_positive"),
            pl.col("person_type").eq("control").any().alias("has_control"),
        )
        .filter(pl.col("has_control") & ~pl.col("has_positive"))
    )
    if not controls_without_positive.is_empty():
        raise ValueError("At least one control match group has no positive founder")
    return split


def _matrix(frame: pl.DataFrame, feature_names: list[str]) -> np.ndarray:
    matrix = frame.select(feature_names).to_numpy().astype(np.float64, copy=False)
    if not np.isfinite(matrix).all():
        raise ValueError("Model features must be finite and non-null")
    return matrix


def _labels(frame: pl.DataFrame) -> np.ndarray:
    return frame.get_column("y").to_numpy().astype(np.int8, copy=False)


def _require_binary_labels(values: np.ndarray, split_name: str) -> None:
    if set(np.unique(values)) != {0, 1}:
        raise ValueError(f"{split_name} must contain both positive and negative labels")


def logistic_params() -> dict[str, object]:
    return {
        "C": 1.0,
        "l1_ratio": 0.0,
        "solver": "liblinear",
        "max_iter": 2_000,
        "random_state": RANDOM_SEED,
    }


def lightgbm_params(
    *, scale_pos_weight: float, n_estimators: int = 500
) -> dict[str, object]:
    return {
        "objective": "binary",
        "metric": "average_precision",
        "learning_rate": 0.05,
        "n_estimators": n_estimators,
        "max_depth": 6,
        "num_leaves": 31,
        "min_child_samples": 10,
        "subsample": 1.0,
        "colsample_bytree": 1.0,
        "reg_lambda": 1.0,
        "scale_pos_weight": scale_pos_weight,
        "random_state": RANDOM_SEED,
        "n_jobs": 1,
        "deterministic": True,
        "force_col_wise": True,
        "bagging_seed": RANDOM_SEED,
        "feature_fraction_seed": RANDOM_SEED,
        "data_random_seed": RANDOM_SEED,
        "verbosity": -1,
    }


def _scale_pos_weight(labels: np.ndarray) -> float:
    positives = int(labels.sum())
    negatives = int(labels.size - positives)
    if positives == 0 or negatives == 0:
        raise ValueError("Training labels must contain both classes")
    return negatives / positives


def fit_training_bundle(
    panel: pl.DataFrame,
    *,
    feature_names: list[str] | None = None,
) -> TrainingBundle:
    """Tune on pre-2023/2023 and refit both candidates on all pre-2024 rows."""
    features = feature_names or model_feature_names(panel)
    split = temporal_split(panel)
    tuning = split.filter(pl.col("split") == "tuning_train")
    validation = split.filter(pl.col("split") == "validation")
    test = split.filter(pl.col("split") == "test")
    for name, frame in (
        ("tuning_train", tuning),
        ("validation", validation),
        ("test", test),
    ):
        if frame.is_empty():
            raise ValueError(f"Temporal split {name} is empty")
        _require_binary_labels(_labels(frame), name)

    x_tuning = _matrix(tuning, features)
    y_tuning = _labels(tuning)
    x_validation = _matrix(validation, features)
    y_validation = _labels(validation)
    logistic_tuning = Pipeline(
        [
            ("standardize", StandardScaler()),
            ("classifier", LogisticRegression(**logistic_params())),
        ]
    ).fit(x_tuning, y_tuning)
    logistic_validation_score = logistic_tuning.predict_proba(x_validation)[:, 1]
    logistic_pr_auc = float(
        average_precision_score(y_validation, logistic_validation_score)
    )

    tuning_weight = _scale_pos_weight(y_tuning)
    lgb_tuning = lgb.LGBMClassifier(**lightgbm_params(scale_pos_weight=tuning_weight))
    lgb_tuning.fit(
        x_tuning,
        y_tuning,
        eval_X=x_validation,
        eval_y=y_validation,
        eval_metric="average_precision",
        callbacks=[lgb.early_stopping(30, first_metric_only=True, verbose=False)],
    )
    lightgbm_validation_score = lgb_tuning.predict_proba(x_validation)[:, 1]
    lightgbm_pr_auc = float(
        average_precision_score(y_validation, lightgbm_validation_score)
    )
    selected = "lightgbm" if lightgbm_pr_auc > logistic_pr_auc * 1.10 else "logistic"
    best_iteration = int(lgb_tuning.best_iteration_ or lgb_tuning.n_estimators)

    development = split.filter(pl.col("split") != "test")
    x_development = _matrix(development, features)
    y_development = _labels(development)
    logistic_final = Pipeline(
        [
            ("standardize", StandardScaler()),
            ("classifier", LogisticRegression(**logistic_params())),
        ]
    ).fit(x_development, y_development)
    lgb_final = lgb.LGBMClassifier(
        **lightgbm_params(
            scale_pos_weight=_scale_pos_weight(y_development),
            n_estimators=max(best_iteration, 1),
        )
    ).fit(x_development, y_development)
    counts = {
        name: frame.height
        for name, frame in (
            ("tuning_train", tuning),
            ("validation", validation),
            ("development_refit", development),
            ("test", test),
        )
    }
    return TrainingBundle(
        feature_names=features,
        logistic_model=logistic_final,
        lightgbm_model=lgb_final,
        selected_model_name=selected,
        validation_metrics={
            "logistic_pr_auc": logistic_pr_auc,
            "lightgbm_pr_auc": lightgbm_pr_auc,
            "lightgbm_relative_improvement": (lightgbm_pr_auc / logistic_pr_auc - 1.0)
            if logistic_pr_auc
            else float("inf"),
            "selection_threshold_relative": 0.10,
        },
        split_counts=counts,
        lightgbm_best_iteration=best_iteration,
    )


def predict_probabilities(
    model: Any, frame: pl.DataFrame, feature_names: list[str]
) -> np.ndarray:
    return np.asarray(
        model.predict_proba(_matrix(frame, feature_names))[:, 1], dtype=np.float64
    )


def train_models(
    *,
    panel_path: Path = PANEL_PATH,
    output_dir: Path = MODELS_DIR,
) -> TrainingBundle:
    if not panel_path.exists():
        raise FileNotFoundError(
            f"Missing feature panel {panel_path}; run the features stage first"
        )
    panel = pl.read_parquet(panel_path)
    bundle = fit_training_bundle(panel)
    output_dir.mkdir(parents=True, exist_ok=True)
    _atomic_joblib_dump(bundle.logistic_model, output_dir / "logistic.joblib")
    _atomic_joblib_dump(bundle.lightgbm_model, output_dir / "lightgbm.joblib")
    _atomic_joblib_dump(bundle.selected_model, output_dir / "selected.joblib")
    _atomic_write_json(bundle.feature_names, output_dir / "feature_list.json")
    _atomic_write_json(
        {
            "random_seed": RANDOM_SEED,
            "logistic": logistic_params(),
            "lightgbm": lightgbm_params(
                scale_pos_weight=float(
                    bundle.lightgbm_model.get_params()["scale_pos_weight"]
                ),
                n_estimators=bundle.lightgbm_best_iteration,
            ),
            "selected_model": bundle.selected_model_name,
            "selection_rule": "LightGBM only when validation PR-AUC is more than 10% relatively above logistic regression.",
            "lightgbm_best_iteration": bundle.lightgbm_best_iteration,
        },
        output_dir / "params.json",
    )
    _atomic_write_json(
        {
            "validation": bundle.validation_metrics,
            "split_counts": bundle.split_counts,
            "feature_data_card": str(DATA_CARD_JSON_PATH),
        },
        output_dir / "training_metrics.json",
    )
    return bundle


def load_training_bundle(output_dir: Path = MODELS_DIR) -> TrainingBundle:
    required = [
        output_dir / "logistic.joblib",
        output_dir / "lightgbm.joblib",
        output_dir / "feature_list.json",
        output_dir / "params.json",
        output_dir / "training_metrics.json",
    ]
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing model artifacts: {missing}; run the train stage first"
        )
    params = json.loads((output_dir / "params.json").read_text(encoding="utf-8"))
    metrics = json.loads(
        (output_dir / "training_metrics.json").read_text(encoding="utf-8")
    )
    return TrainingBundle(
        feature_names=json.loads(
            (output_dir / "feature_list.json").read_text(encoding="utf-8")
        ),
        logistic_model=joblib.load(output_dir / "logistic.joblib"),
        lightgbm_model=joblib.load(output_dir / "lightgbm.joblib"),
        selected_model_name=str(params["selected_model"]),
        validation_metrics={
            key: float(value) for key, value in metrics["validation"].items()
        },
        split_counts={
            key: int(value) for key, value in metrics["split_counts"].items()
        },
        lightgbm_best_iteration=int(params["lightgbm_best_iteration"]),
    )


if __name__ == "__main__":
    train_models()
