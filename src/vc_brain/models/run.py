"""Run feature construction, temporal model training, and honest evaluation."""

import argparse
import logging
from collections.abc import Sequence
from pathlib import Path

from vc_brain.eval.report import build_report
from vc_brain.features.build import build_features
from vc_brain.models.train import train_models


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--stage",
        required=True,
        choices=("features", "train", "eval", "all"),
        help="Pipeline stage; all runs features, train, then eval.",
    )
    result.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Input/output data root (default: ./data).",
    )
    result.add_argument(
        "--top-k",
        type=int,
        default=100,
        help="Maximum detected candidates exported by eval (default: 100).",
    )
    return result


def _features(data_dir: Path) -> None:
    build_features(
        labels_path=data_dir / "labels" / "founders.parquet",
        monthly_agg_dir=data_dir / "events" / "monthly_agg",
        owned_repo_agg_dir=data_dir / "events" / "owned_repo_agg",
        ownership_agg_dir=data_dir / "events" / "ownership_agg",
        collab_influx_dir=data_dir / "events" / "collab_influx",
        repo_creations_dir=data_dir / "events" / "repo_creations",
        baselines_path=data_dir / "events" / "baselines" / "monthly_totals.parquet",
        matches_path=data_dir / "events" / "negatives" / "matched.parquet",
        annotations_path=data_dir / "semantics" / "annotations.parquet",
        output_path=data_dir / "features" / "panel.parquet",
        data_card_json_path=data_dir / "features" / "data_card.json",
        data_card_md_path=data_dir / "features" / "data_card.md",
    )


def _train(data_dir: Path) -> None:
    train_models(
        panel_path=data_dir / "features" / "panel.parquet",
        output_dir=data_dir / "models",
    )


def _eval(data_dir: Path, top_k: int) -> None:
    build_report(
        panel_path=data_dir / "features" / "panel.parquet",
        models_dir=data_dir / "models",
        feature_data_card_path=data_dir / "features" / "data_card.json",
        output_dir=data_dir / "eval",
        scores_dir=data_dir / "scores",
        top_k=top_k,
    )


def main(argv: Sequence[str] | None = None) -> None:
    args = parser().parse_args(argv)
    if args.top_k < 1:
        parser().error("--top-k must be positive")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    data_dir = args.data_dir.resolve()
    stages = ("features", "train", "eval") if args.stage == "all" else (args.stage,)
    for stage in stages:
        logging.info("Starting stage=%s data_dir=%s", stage, data_dir)
        if stage == "features":
            _features(data_dir)
        elif stage == "train":
            _train(data_dir)
        else:
            _eval(data_dir, args.top_k)
        logging.info("Completed stage=%s", stage)


if __name__ == "__main__":
    main()
