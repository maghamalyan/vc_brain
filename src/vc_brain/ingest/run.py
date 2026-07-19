"""Command line entry point for resumable event extraction stages."""

import argparse
import logging
from collections.abc import Sequence

from vc_brain.ingest.clickhouse import ClickHouseClient
from vc_brain.ingest.pipeline import (
    run_baselines,
    run_negatives,
    run_ownership_collab,
    run_positives,
    run_repos,
)


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--stage",
        required=True,
        choices=("baselines", "positives", "negatives", "repos", "ownership_collab"),
    )
    result.add_argument(
        "--actor-limit",
        type=int,
        help="positives-only smoke limit; writes monthly_agg/smoke_<N>.parquet",
    )
    return result


def main(argv: Sequence[str] | None = None) -> None:
    args = parser().parse_args(argv)
    if args.actor_limit is not None and args.stage != "positives":
        parser().error("--actor-limit is only valid with --stage positives")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    with ClickHouseClient() as client:
        if args.stage == "baselines":
            run_baselines(client)
        elif args.stage == "positives":
            run_positives(client, actor_limit=args.actor_limit)
        elif args.stage == "negatives":
            run_negatives(client)
        elif args.stage == "repos":
            run_repos(client)
        else:
            run_ownership_collab(client)


if __name__ == "__main__":
    main()
