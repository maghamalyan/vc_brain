"""Honest out-of-time evaluation, null checks, ablations, and score exports."""

import json
import math
import os
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import plotly.graph_objects as go
import polars as pl
from sklearn.metrics import (
    average_precision_score,
    brier_score_loss,
    precision_recall_curve,
    roc_auc_score,
)

from vc_brain.features.build import DATA_CARD_JSON_PATH, PANEL_PATH, month_distance
from vc_brain.models.train import (
    MODELS_DIR,
    RANDOM_SEED,
    TrainingBundle,
    fit_training_bundle,
    load_training_bundle,
    predict_probabilities,
    temporal_split,
)

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = Path(os.environ.get("VC_BRAIN_DATA_DIR", PROJECT_ROOT / "data"))
EVAL_DIR = DATA_ROOT / "eval"
SCORES_DIR = DATA_ROOT / "scores"
POPULATION_BASE_RATES = (0.005, 0.01, 0.02)
NULL_SEED = 18


class LeakageSanityError(RuntimeError):
    """The shuffled-label null retained suspicious predictive performance."""


def _atomic_write_text(value: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, suffix=".txt.tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def _atomic_write_parquet(frame: pl.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, suffix=".parquet.tmp")
    os.close(descriptor)
    try:
        frame.write_parquet(temporary)
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def case_control_correct(
    probabilities: np.ndarray,
    *,
    sample_prevalence: float,
    population_prevalence: float,
) -> np.ndarray:
    """Apply prior-odds correction from sampled to population prevalence."""
    if not 0 < sample_prevalence < 1 or not 0 < population_prevalence < 1:
        raise ValueError(
            "Sample and population prevalence must both be between zero and one"
        )
    clipped = np.clip(np.asarray(probabilities, dtype=np.float64), 1e-12, 1 - 1e-12)
    sample_odds = sample_prevalence / (1.0 - sample_prevalence)
    population_odds = population_prevalence / (1.0 - population_prevalence)
    corrected_odds = clipped / (1.0 - clipped) * population_odds / sample_odds
    return corrected_odds / (1.0 + corrected_odds)


def _population_weights(
    labels: np.ndarray, sample_prevalence: float, population_prevalence: float
) -> np.ndarray:
    return np.where(
        labels == 1,
        population_prevalence / sample_prevalence,
        (1.0 - population_prevalence) / (1.0 - sample_prevalence),
    )


def _reliability(
    labels: np.ndarray,
    probabilities: np.ndarray,
    weights: np.ndarray,
    *,
    bins: int = 10,
) -> list[dict[str, float | int]]:
    edges = np.linspace(0.0, 1.0, bins + 1)
    assignments = np.minimum(
        np.digitize(probabilities, edges[1:-1], right=False), bins - 1
    )
    rows: list[dict[str, float | int]] = []
    for index in range(bins):
        selected = assignments == index
        if not selected.any():
            continue
        selected_weights = weights[selected]
        rows.append(
            {
                "bin": index,
                "count": int(selected.sum()),
                "mean_predicted": float(
                    np.average(probabilities[selected], weights=selected_weights)
                ),
                "observed_rate": float(
                    np.average(labels[selected], weights=selected_weights)
                ),
            }
        )
    return rows


def _person_month_metrics(
    labels: np.ndarray, probabilities: np.ndarray, months: np.ndarray | None = None
) -> dict[str, float]:
    metrics = {
        "pr_auc": float(average_precision_score(labels, probabilities)),
        "roc_auc": float(roc_auc_score(labels, probabilities)),
        "base_rate": float(labels.mean()),
    }
    if months is not None:
        metrics.update(_within_month_pr_auc(months, labels, probabilities))
    return metrics


def _within_month_pr_auc(
    months: np.ndarray, labels: np.ndarray, probabilities: np.ndarray
) -> dict[str, float]:
    """Positive-weighted macro PR-AUC computed inside each calendar month.

    Calendar-month composition (batch sizes, resolution coverage) lets a
    month-intercept model beat the GLOBAL base rate without any person-level
    skill, which is exactly what the first live null run exposed. Ranking
    within months removes that channel: a month-intercept model scores the
    month's own base rate here.
    """
    weighted = 0.0
    base_weighted = 0.0
    total_weight = 0.0
    months_used = 0
    for month in np.unique(months):
        mask = months == month
        month_labels = labels[mask]
        positives = int(month_labels.sum())
        if positives == 0 or positives == len(month_labels):
            continue
        weight = float(positives)
        weighted += (
            float(average_precision_score(month_labels, probabilities[mask])) * weight
        )
        base_weighted += float(month_labels.mean()) * weight
        total_weight += weight
        months_used += 1
    if total_weight == 0.0:
        return {
            "within_month_pr_auc": float("nan"),
            "within_month_base_rate": float("nan"),
            "months_evaluated": 0,
        }
    return {
        "within_month_pr_auc": weighted / total_weight,
        "within_month_base_rate": base_weighted / total_weight,
        "months_evaluated": months_used,
    }


def _scored_frame(frame: pl.DataFrame, probabilities: np.ndarray) -> pl.DataFrame:
    return frame.with_columns(pl.Series("score", probabilities, dtype=pl.Float64))


def _person_summary(scored: pl.DataFrame) -> pl.DataFrame:
    return (
        scored.sort("gh_login", "month")
        .group_by("gh_login", maintain_order=True)
        .agg(
            pl.col("person_type").first(),
            pl.col("founder_name").first(),
            pl.col("company").first(),
            pl.col("batch_start_date").first(),
            pl.col("score").max().alias("max_score"),
            pl.col("score").last().alias("current_score"),
            pl.col("score").tail(3).alias("last_three_scores"),
        )
        .with_columns(
            (pl.col("person_type") == "positive").cast(pl.Int8).alias("is_positive")
        )
        .sort("max_score", "gh_login", descending=[True, False])
    )


def _top_metric(summary: pl.DataFrame, requested_k: int) -> dict[str, float | int]:
    effective = min(requested_k, summary.height)
    top = summary.head(effective)
    positives = int(top.get_column("is_positive").sum()) if effective else 0
    return {
        "requested_k": requested_k,
        "effective_k": effective,
        "positives": positives,
        "precision": positives / effective if effective else 0.0,
    }


def _person_level_metrics(summary: pl.DataFrame) -> dict[str, Any]:
    total_positives = int(summary.get_column("is_positive").sum())
    prevalence = total_positives / summary.height
    review_k = max(1, math.ceil(summary.height * 0.10))
    review_positives = int(summary.head(review_k).get_column("is_positive").sum())
    lift_k = max(1, math.ceil(summary.height * 0.01))
    lift_precision = float(summary.head(lift_k).get_column("is_positive").mean())
    return {
        "people": summary.height,
        "positives": total_positives,
        "prevalence": prevalence,
        "precision_at_50": _top_metric(summary, 50),
        "precision_at_100": _top_metric(summary, 100),
        "recall_at_review_budget": {
            "budget_fraction": 0.10,
            "reviewed": review_k,
            "positives_found": review_positives,
            "recall": review_positives / total_positives if total_positives else 0.0,
        },
        "lift_at_1pct": {
            "reviewed": lift_k,
            "precision": lift_precision,
            "lift": lift_precision / prevalence if prevalence else 0.0,
        },
    }


def _lead_time(scored: pl.DataFrame) -> tuple[dict[str, Any], dict[str, date]]:
    control_thresholds: dict[date, float] = {}
    controls = scored.filter(pl.col("person_type") == "control")
    for month in controls.get_column("month").unique().sort().to_list():
        values = (
            controls.filter(pl.col("month") == month).get_column("score").to_numpy()
        )
        if values.size:
            control_thresholds[month] = float(np.quantile(values, 0.99))

    detections: dict[str, date] = {}
    leads: list[int] = []
    positives = scored.filter(pl.col("person_type") == "positive")
    positive_months = set(positives.get_column("month").unique().to_list())
    missing_thresholds = positive_months - set(control_thresholds)
    if missing_thresholds:
        raise ValueError(
            "Matched controls do not cover positive test months: "
            f"{sorted(missing_thresholds)}"
        )
    for login in positives.get_column("gh_login").unique().sort().to_list():
        person = positives.filter(pl.col("gh_login") == login).sort("month")
        detection: date | None = None
        for row in person.select("month", "score").to_dicts():
            threshold = control_thresholds[row["month"]]
            if float(row["score"]) >= threshold:
                detection = row["month"]
                break
        if detection is not None:
            detections[str(login)] = detection
            batch_start = person.get_column("batch_start_date").item(0)
            leads.append(month_distance(batch_start, detection))
    total = positives.get_column("gh_login").n_unique()
    if leads:
        quartiles = np.percentile(np.asarray(leads, dtype=float), [25, 50, 75])
        summary: dict[str, Any] = {
            "detected": len(leads),
            "total_test_founders": total,
            "detection_rate": len(leads) / total if total else 0.0,
            "lead_months_median": float(quartiles[1]),
            "lead_months_iqr": [float(quartiles[0]), float(quartiles[2])],
            "lead_months": leads,
            "threshold": "99th percentile of control scores in the same calendar month",
        }
    else:
        summary = {
            "detected": 0,
            "total_test_founders": total,
            "detection_rate": 0.0,
            "lead_months_median": None,
            "lead_months_iqr": None,
            "lead_months": [],
            "threshold": "99th percentile of control scores in the same calendar month",
        }
    return summary, detections


def shuffle_labels_within_month(
    panel: pl.DataFrame, *, seed: int = RANDOM_SEED
) -> pl.DataFrame:
    """Permute development labels by month while preserving the honest test oracle."""
    split = temporal_split(panel).with_row_index("_row")
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


def _feature_blocks(
    feature_names: list[str], data_card_path: Path
) -> dict[str, list[str]]:
    if not data_card_path.exists():
        raise FileNotFoundError(f"Missing feature data card {data_card_path}")
    card = json.loads(data_card_path.read_text(encoding="utf-8"))
    by_name = {item["name"]: item["block"] for item in card.get("features", [])}
    missing = [name for name in feature_names if name not in by_name]
    if missing:
        raise ValueError(f"Feature data card does not define blocks for: {missing}")
    return {
        block: [name for name in feature_names if by_name[name] == block]
        for block in ("levels", "dynamics", "traction")
    }


def _evaluate_ablation(panel: pl.DataFrame, features: list[str]) -> dict[str, Any]:
    bundle = fit_training_bundle(panel, feature_names=features)
    test = temporal_split(panel).filter(pl.col("split") == "test")
    labels = test.get_column("y").to_numpy()
    logistic_scores = predict_probabilities(bundle.logistic_model, test, features)
    lightgbm_scores = predict_probabilities(bundle.lightgbm_model, test, features)
    selected_scores = (
        lightgbm_scores if bundle.selected_model_name == "lightgbm" else logistic_scores
    )
    return {
        "feature_count": len(features),
        "selected_model": bundle.selected_model_name,
        "validation": bundle.validation_metrics,
        "test": {
            "logistic_pr_auc": float(average_precision_score(labels, logistic_scores)),
            "lightgbm_pr_auc": float(average_precision_score(labels, lightgbm_scores)),
            "selected_pr_auc": float(average_precision_score(labels, selected_scores)),
        },
    }


def _top_feature_importances(bundle: TrainingBundle) -> list[dict[str, float | str]]:
    booster = bundle.lightgbm_model.booster_
    gains = booster.feature_importance(importance_type="gain")
    total = float(gains.sum())
    items = sorted(
        zip(bundle.feature_names, gains, strict=True),
        key=lambda item: (-item[1], item[0]),
    )[:20]
    return [
        {
            "feature": name,
            "gain": float(gain),
            "gain_fraction": float(gain / total) if total else 0.0,
        }
        for name, gain in items
    ]


def _write_figure(figure: go.Figure, stem: Path) -> dict[str, Any]:
    stem.parent.mkdir(parents=True, exist_ok=True)
    html_path = stem.with_suffix(".html")
    figure.write_html(html_path, include_plotlyjs=True, full_html=True)
    png_path = stem.with_suffix(".png")
    png_written = False
    png_error: str | None = None
    try:
        figure.write_image(png_path)
        png_written = True
    except Exception as exc:  # Kaleido may be installed without a local Chrome binary.
        png_error = f"{type(exc).__name__}: {exc}"
    return {
        "html": str(html_path),
        "png": str(png_path) if png_written else None,
        "png_error": png_error,
    }


def _figures(
    scored: pl.DataFrame,
    labels: np.ndarray,
    scores: np.ndarray,
    reliability: list[dict[str, float | int]],
    lead: dict[str, Any],
    figures_dir: Path,
) -> dict[str, Any]:
    precision, recall, _ = precision_recall_curve(labels, scores)
    pr = go.Figure(
        go.Scatter(x=recall, y=precision, mode="lines", name="selected model")
    )
    pr.add_hline(
        y=float(labels.mean()), line_dash="dash", annotation_text="test base rate"
    )
    pr.update_layout(
        title="Out-of-time person-month precision-recall",
        xaxis_title="Recall",
        yaxis_title="Precision",
    )

    rel = go.Figure()
    rel.add_trace(
        go.Scatter(
            x=[row["mean_predicted"] for row in reliability],
            y=[row["observed_rate"] for row in reliability],
            mode="lines+markers",
            name="1% base-rate correction",
        )
    )
    rel.add_trace(
        go.Scatter(
            x=[0, 1], y=[0, 1], mode="lines", line={"dash": "dash"}, name="ideal"
        )
    )
    rel.update_layout(
        title="Reliability after case-control correction",
        xaxis_title="Mean predicted probability",
        yaxis_title="Weighted observed rate",
    )

    lead_figure = go.Figure(go.Histogram(x=lead["lead_months"], nbinsx=12))
    lead_figure.update_layout(
        title="Detected-founder lead time",
        xaxis_title="Months before batch start",
        yaxis_title="Founders",
    )

    trajectories = go.Figure()
    examples = (
        scored.filter(pl.col("person_type") == "positive")
        .group_by("gh_login")
        .agg(pl.col("score").max().alias("max_score"))
        .sort("max_score", "gh_login", descending=[True, False])
        .head(6)
        .get_column("gh_login")
        .to_list()
    )
    for login in examples:
        person = scored.filter(pl.col("gh_login") == login).sort("month")
        trajectories.add_trace(
            go.Scatter(
                x=person.get_column("month").to_list(),
                y=person.get_column("score").to_list(),
                mode="lines+markers",
                name=str(login),
            )
        )
    trajectories.update_layout(
        title="Example test-founder score trajectories",
        xaxis_title="Month",
        yaxis_title="Score",
    )
    return {
        "pr_curve": _write_figure(pr, figures_dir / "pr_curve"),
        "reliability": _write_figure(rel, figures_dir / "reliability"),
        "lead_time": _write_figure(lead_figure, figures_dir / "lead_time"),
        "example_trajectories": _write_figure(
            trajectories, figures_dir / "example_trajectories"
        ),
    }


def _slope(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    x = np.arange(len(values), dtype=float)
    return float(np.polyfit(x, np.asarray(values, dtype=float), 1)[0])


def _score_outputs(
    scored: pl.DataFrame,
    detections: dict[str, date],
    *,
    scores_dir: Path,
    top_k: int,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    trajectories = scored.select("gh_login", "month", "score").sort("gh_login", "month")
    summary = _person_summary(scored)
    summary = summary.with_columns(
        pl.col("last_three_scores")
        .map_elements(_slope, return_dtype=pl.Float64)
        .alias("momentum_3mo"),
        pl.col("gh_login")
        .map_elements(lambda login: detections.get(str(login)), return_dtype=pl.Date)
        .alias("first_detection_month"),
    )
    # Momentum breaks score ties (small-data LightGBM emits many identical leaf
    # scores); among equally-scored candidates a rising signal ranks first, and
    # the login only guarantees determinism.
    detected = (
        summary.filter(pl.col("first_detection_month").is_not_null())
        .sort(
            "current_score",
            "momentum_3mo",
            "gh_login",
            descending=[True, True, False],
        )
        .head(top_k)
    )
    pool = summary.height
    score_percentiles = {
        str(row["gh_login"]): (pool - rank) / pool if pool else 0.0
        for rank, row in enumerate(
            summary.sort(
                "current_score",
                "momentum_3mo",
                "gh_login",
                descending=[True, True, False],
            ).to_dicts()
        )
    }
    candidates = detected.select(
        "gh_login",
        "founder_name",
        "company",
        pl.lit("outbound_detector").alias("source"),
        pl.col("current_score").cast(pl.Float64),
        pl.col("gh_login")
        .replace_strict(score_percentiles, return_dtype=pl.Float64)
        .alias("score_percentile"),
        pl.col("momentum_3mo").cast(pl.Float64),
        pl.col("first_detection_month").cast(pl.Date),
        pl.lit("candidate").alias("status"),
    )
    _atomic_write_parquet(trajectories, scores_dir / "trajectories.parquet")
    _atomic_write_parquet(candidates, scores_dir / "candidates.parquet")
    return trajectories, candidates


def _markdown(report: dict[str, Any]) -> str:
    primary = report["person_month"]
    person = report["person_level"]
    lead = report["lead_time"]
    null = report["null_run"]
    lines = [
        "# Tier-1 Founder Hazard Model — Honest Evaluation\n\n",
        f"Generated: `{report['generated_at']}`\n\n",
        "## Decision and split\n\n",
        f"Selected model: **{report['selected_model']}**. LightGBM was eligible only if its 2023 validation PR-AUC beat logistic by more than 10% relatively. The held-out test contains only groups with B ≥ 2024-01-01; it was not used for tuning or selection.\n\n",
        "## Person-month performance\n\n",
        "| Model | PR-AUC | ROC-AUC |\n| --- | ---: | ---: |\n",
        f"| Logistic baseline | {primary['logistic']['pr_auc']:.4f} | {primary['logistic']['roc_auc']:.4f} |\n",
        f"| LightGBM | {primary['lightgbm']['pr_auc']:.4f} | {primary['lightgbm']['roc_auc']:.4f} |\n",
        f"| Selected ({report['selected_model']}) | {primary['selected']['pr_auc']:.4f} | {primary['selected']['roc_auc']:.4f} |\n\n",
        "## Person-level utility\n\n",
        f"Pool: {person['people']} people ({person['positives']} founders). Precision@50: {person['precision_at_50']['precision']:.3f}; precision@100: {person['precision_at_100']['precision']:.3f}; recall at the 10% review budget: {person['recall_at_review_budget']['recall']:.3f}; lift@1%: {person['lift_at_1pct']['lift']:.2f}×.\n\n",
        "## Calibration\n\n",
        "Probabilities use prior-odds case-control correction. The primary assumed population person-month base rate is **1%**, with sensitivity at **0.5%** and **2%**. Weighted Brier scores are reported in JSON because the sampled test prevalence is not the population prevalence.\n\n",
        "## Lead time\n\n",
        f"Detected {lead['detected']} of {lead['total_test_founders']} test founders ({lead['detection_rate']:.1%}) at or above the same-month 99th percentile of control scores. Median lead: {lead['lead_months_median']} months; IQR: {lead['lead_months_iqr']}.\n\n",
        "## Mandatory null run\n\n",
        f"Development labels were shuffled within calendar month using seed {null['seed']}; held-out test labels remained the oracle. Null within-month PR-AUC: **{null['within_month_pr_auc']:.4f}** (limit {null['maximum_allowed_within_month_pr_auc']:.4f}; within-month base {null['within_month_base_rate']:.4f}); global null PR-AUC {null['global_pr_auc']:.4f} shown for transparency — it retains calendar-composition effects. Sanity check: **{'PASS' if null['passed'] else 'FAIL — possible leakage; score exports withheld'}**.\n\n",
        "## Ablations\n\n",
        "| Features | Count | Selected model | Test PR-AUC | Marginal |\n| --- | ---: | --- | ---: | ---: |\n",
    ]
    for name, result in report["ablations"].items():
        lines.append(
            f"| {name} | {result['feature_count']} | {result['selected_model']} | {result['test']['selected_pr_auc']:.4f} | {result['marginal_pr_auc']:+.4f} |\n"
        )
    lines.extend(
        [
            "\n## LightGBM gain importances — review required\n\n",
            "These importances are associative, not causal, and are explicitly flagged for human review.\n\n",
            "| Rank | Feature | Gain fraction |\n| ---: | --- | ---: |\n",
        ]
    )
    for rank, item in enumerate(report["top_feature_importances"], start=1):
        lines.append(
            f"| {rank} | `{item['feature']}` | {item['gain_fraction']:.4f} |\n"
        )
    lines.append(
        "\n## Artifacts\n\nStandalone HTML figures are always written. PNG paths are present only when Kaleido can render with the local browser runtime. Raw selected-model scores, not prevalence-corrected probabilities, feed ranking trajectories and candidates.\n"
    )
    return "".join(lines)


def build_report(
    *,
    panel_path: Path = PANEL_PATH,
    models_dir: Path = MODELS_DIR,
    feature_data_card_path: Path = DATA_CARD_JSON_PATH,
    output_dir: Path = EVAL_DIR,
    scores_dir: Path = SCORES_DIR,
    top_k: int = 100,
) -> dict[str, Any]:
    if top_k < 1:
        raise ValueError("top_k must be positive")
    if not panel_path.exists():
        raise FileNotFoundError(
            f"Missing feature panel {panel_path}; run features first"
        )
    panel = pl.read_parquet(panel_path)
    bundle = load_training_bundle(models_dir)
    test = temporal_split(panel).filter(pl.col("split") == "test")
    labels = test.get_column("y").to_numpy().astype(np.int8)
    test_months = test.get_column("month").to_numpy()
    logistic_scores = predict_probabilities(
        bundle.logistic_model, test, bundle.feature_names
    )
    lightgbm_scores = predict_probabilities(
        bundle.lightgbm_model, test, bundle.feature_names
    )
    selected_scores = (
        lightgbm_scores if bundle.selected_model_name == "lightgbm" else logistic_scores
    )
    scored = _scored_frame(test, selected_scores)
    summary = _person_summary(scored)
    lead, detections = _lead_time(scored)

    sample_prevalence = float(labels.mean())
    calibration: dict[str, Any] = {}
    primary_reliability: list[dict[str, float | int]] = []
    for rate in POPULATION_BASE_RATES:
        corrected = case_control_correct(
            selected_scores,
            sample_prevalence=sample_prevalence,
            population_prevalence=rate,
        )
        weights = _population_weights(labels, sample_prevalence, rate)
        reliability = _reliability(labels, corrected, weights)
        calibration[f"{rate:.3%}"] = {
            "assumed_population_base_rate": rate,
            "brier": float(brier_score_loss(labels, corrected, sample_weight=weights)),
            "reliability": reliability,
        }
        if rate == 0.01:
            primary_reliability = reliability

    shuffled = shuffle_labels_within_month(panel, seed=NULL_SEED)
    null_bundle = fit_training_bundle(shuffled, feature_names=bundle.feature_names)
    null_test = temporal_split(shuffled).filter(pl.col("split") == "test")
    null_labels = null_test.get_column("y").to_numpy().astype(np.int8)
    null_scores = predict_probabilities(
        null_bundle.selected_model, null_test, bundle.feature_names
    )
    null_pr = float(average_precision_score(null_labels, null_scores))
    null_base = float(null_labels.mean())
    null_months = null_test.get_column("month").to_numpy()
    null_within = _within_month_pr_auc(null_months, null_labels, null_scores)
    null_within_base = float(null_within["within_month_base_rate"])
    null_limit = max(null_within_base * 2.0, null_within_base + 0.02)
    # Gate on WITHIN-MONTH ranking: global PR-AUC keeps calendar-composition
    # effects that shuffled labels cannot remove; within-month must collapse.
    null_passed = float(null_within["within_month_pr_auc"]) <= null_limit

    blocks = _feature_blocks(bundle.feature_names, feature_data_card_path)
    ablation_specs = {
        "levels_only": blocks["levels"],
        "levels_plus_dynamics": blocks["levels"] + blocks["dynamics"],
        "levels_plus_dynamics_plus_traction": blocks["levels"]
        + blocks["dynamics"]
        + blocks["traction"],
        # tenure_months dominated gain (84% on the partial cohort); this
        # quantifies how much skill survives without any account-age signal.
        "all_minus_tenure": [
            name
            for name in bundle.feature_names
            if not name.startswith("tenure")
        ],
    }
    ablations: dict[str, dict[str, Any]] = {}
    previous = 0.0
    for name, features in ablation_specs.items():
        result = _evaluate_ablation(panel, features)
        current = float(result["test"]["selected_pr_auc"])
        result["marginal_pr_auc"] = current - previous if ablations else 0.0
        previous = current
        ablations[name] = result

    figures = _figures(
        scored,
        labels,
        selected_scores,
        primary_reliability,
        lead,
        output_dir / "figures",
    )
    report: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "random_seed": RANDOM_SEED,
        "split_contract": {
            "tuning_train": "B <= 2022-12-31",
            "validation": "2023-01-01 <= B <= 2023-12-31",
            "test": "B >= 2024-01-01",
            "controls": "Controls inherit B and match_group_id from their matched positive.",
            "counts": bundle.split_counts,
        },
        "selected_model": bundle.selected_model_name,
        "validation_model_selection": bundle.validation_metrics,
        "person_month": {
            "primary_metric": "within_month_pr_auc",
            "logistic": _person_month_metrics(
                labels, logistic_scores, test_months
            ),
            "lightgbm": _person_month_metrics(
                labels, lightgbm_scores, test_months
            ),
            "selected": _person_month_metrics(
                labels, selected_scores, test_months
            ),
        },
        "person_level": _person_level_metrics(summary),
        "calibration": {
            "sample_person_month_prevalence": sample_prevalence,
            "primary_assumed_population_base_rate": 0.01,
            "sensitivity": calibration,
        },
        "lead_time": lead,
        "null_run": {
            "method": "Tuning-train and validation labels shuffled within calendar month; held-out test labels left unchanged as the null oracle. Gate applies to WITHIN-MONTH PR-AUC (global PR-AUC retains calendar-composition effects by construction).",
            "seed": NULL_SEED,
            "selected_model": null_bundle.selected_model_name,
            "global_pr_auc": null_pr,
            "global_base_rate": null_base,
            "within_month_pr_auc": float(null_within["within_month_pr_auc"]),
            "within_month_base_rate": null_within_base,
            "months_evaluated": null_within["months_evaluated"],
            "maximum_allowed_within_month_pr_auc": null_limit,
            "passed": null_passed,
        },
        "ablations": ablations,
        "top_feature_importances": _top_feature_importances(bundle),
        "feature_importance_review_required": True,
        "figures": figures,
        "score_outputs": None,
    }
    if null_passed:
        trajectories, candidates = _score_outputs(
            scored, detections, scores_dir=scores_dir, top_k=top_k
        )
        report["score_outputs"] = {
            "trajectories": str(scores_dir / "trajectories.parquet"),
            "trajectory_rows": trajectories.height,
            "candidates": str(scores_dir / "candidates.parquet"),
            "candidate_rows": candidates.height,
        }
    output_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", output_dir / "report.json"
    )
    _atomic_write_text(_markdown(report), output_dir / "report.md")
    if not null_passed:
        raise LeakageSanityError(
            f"Shuffled-label PR-AUC {null_pr:.4f} exceeds null limit {null_limit:.4f}; reports were written but score exports were withheld"
        )
    return report


if __name__ == "__main__":
    build_report()
