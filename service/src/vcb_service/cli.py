"""Command-line interface for building the VC Brain search/read index."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from vcb_service.indexer import IndexBuildError, VerificationError, build_index


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vcb-index")
    subcommands = parser.add_subparsers(dest="command", required=True)
    build = subcommands.add_parser("build", help="build the immutable SQLite index")
    build.add_argument("--data-dir", type=Path, default=Path("../data/fixtures"))
    build.add_argument("--thesis", type=Path, default=Path("../config/thesis.json"))
    build.add_argument("--out", type=Path, default=Path("../data/index/vcb.sqlite"))
    build.add_argument(
        "--verify",
        action="store_true",
        help="print FTS document counts and fail on unresolved evidence references",
    )
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = build_index(args.data_dir, args.thesis, args.out, verify=False)
        print(f"built {result.path}")
        if args.verify:
            for doc_type, count in result.doc_counts.items():
                print(f"{doc_type}: {count}")
            if result.unresolved:
                raise VerificationError(result.unresolved)
            print("verification: ok")
        return 0
    except IndexBuildError as error:
        print(f"vcb-index: {error}", file=sys.stderr)
        return 1


def main() -> None:
    raise SystemExit(run())
