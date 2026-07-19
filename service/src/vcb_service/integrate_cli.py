"""Command-line interface for adapting real pipeline outputs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from vcb_service.integrator import (
    IntegrationBuildError,
    IntegrationVerificationError,
    build_integration,
    format_verification,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vcb-integrate")
    subcommands = parser.add_subparsers(dest="command", required=True)
    build = subcommands.add_parser(
        "build", help="adapt real pipeline outputs for vcb-index"
    )
    build.add_argument("--source", type=Path, required=True)
    build.add_argument("--out", type=Path, default=Path("../data/integrated"))
    build.add_argument(
        "--verify",
        action="store_true",
        help="verify memo refs and additive score components before publishing",
    )
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        result = build_integration(args.source, args.out, verify=args.verify)
        print(f"built {result.path}")
        if args.verify:
            print("\n".join(format_verification(result)))
            print("verification: ok")
        return 0
    except IntegrationVerificationError as error:
        print("\n".join(format_verification(error.result)))
        print(f"vcb-integrate: {error}", file=sys.stderr)
        return 1
    except IntegrationBuildError as error:
        print(f"vcb-integrate: {error}", file=sys.stderr)
        return 1


def main() -> None:
    raise SystemExit(run())
