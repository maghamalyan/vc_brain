"""Run A3 semantic text extraction or annotation stages."""

from __future__ import annotations

import argparse
import json
import logging
from collections.abc import Sequence
from pathlib import Path

import polars as pl

from vc_brain.ingest.clickhouse import ClickHouseClient
from vc_brain.ingest.contracts import MONTHLY_AGG_DIR, NEGATIVE_MATCHES_PATH
from vc_brain.semantics.annotate import annotate_text_items
from vc_brain.semantics.extract import freeze_cohort_d
from vc_brain.semantics.validation import write_validation_sample


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--stage", required=True, choices=("extract", "annotate", "validate")
    )
    result.add_argument(
        "--mock",
        action="store_true",
        help="Load annotation fixtures; never call OpenRouter",
    )
    result.add_argument("--fixture-dir", type=Path)
    result.add_argument("--actor-limit", type=int)
    result.add_argument("--bundle-limit", type=int)
    result.add_argument("--concurrency", type=int, default=8)
    return result


def _positive_cohort() -> pl.DataFrame:
    path = MONTHLY_AGG_DIR / "positives.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Missing positive monthly aggregate: {path}")
    return (
        pl.read_parquet(path)
        .select("actor_login", "t_cutoff")
        .unique()
        .sort("actor_login")
    )


def main(argv: Sequence[str] | None = None) -> None:
    args = parser().parse_args(argv)
    if args.stage != "annotate" and (
        args.mock or args.fixture_dir or args.actor_limit or args.bundle_limit
    ):
        parser().error("annotation flags are only valid with --stage annotate")
    if args.stage == "annotate" and not args.mock:
        if args.fixture_dir:
            parser().error("--fixture-dir requires --mock")
    if args.mock and args.fixture_dir is None:
        parser().error("--mock requires --fixture-dir")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    if args.stage == "extract":
        if not NEGATIVE_MATCHES_PATH.exists():
            raise FileNotFoundError(
                f"Missing matched controls: {NEGATIVE_MATCHES_PATH}"
            )
        with ClickHouseClient() as client:
            _, _, summary = freeze_cohort_d(
                client,
                positive_cohort=_positive_cohort(),
                matches=pl.read_parquet(NEGATIVE_MATCHES_PATH),
            )
        print(json.dumps(summary, indent=2, sort_keys=True))
    elif args.stage == "annotate":
        frame, stats = annotate_text_items(
            mock=args.mock,
            fixture_dir=args.fixture_dir,
            actor_limit=args.actor_limit,
            bundle_limit=args.bundle_limit,
            concurrency=args.concurrency,
        )
        print(json.dumps({**stats.__dict__, "rows": frame.height}, indent=2))
    else:
        print(write_validation_sample())


if __name__ == "__main__":
    main()
