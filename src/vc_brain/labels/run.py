"""Command-line entrypoint for the label pipeline."""

import argparse
import logging

from dotenv import load_dotenv

from vc_brain.labels.build_labels import build_labels
from vc_brain.labels.gh_resolve import resolve_founders
from vc_brain.labels.yc_companies import build_companies
from vc_brain.labels.yc_founders import extract_founders

LOGGER = logging.getLogger(__name__)
STAGES = ("all", "companies", "founders", "resolve", "build")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build YC founder GitHub labels")
    parser.add_argument("--stage", choices=STAGES, default="all")
    parser.add_argument(
        "--min-batch-year",
        type=int,
        default=2012,
        help="Oldest YC batch year included by the founders stage (default: 2012)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    load_dotenv()
    try:
        if args.stage in {"all", "companies"}:
            build_companies()
        if args.stage in {"all", "founders"}:
            extract_founders(min_batch_year=args.min_batch_year)
        if args.stage in {"all", "resolve"}:
            resolve_founders()
        if args.stage in {"all", "build"}:
            build_labels()
    except KeyboardInterrupt:
        LOGGER.info("Interrupted after writing a resumable checkpoint")
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
