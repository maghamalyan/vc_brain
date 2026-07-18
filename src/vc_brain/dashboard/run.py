"""Command-line entry point for the static VC Brain dashboard."""

from __future__ import annotations

import argparse
from pathlib import Path

from vc_brain.dashboard.build import build_site


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixtures",
        action="store_true",
        help="Build from the deterministic synthetic fixture corpus",
    )
    parser.add_argument("--output", type=Path, default=Path("site"))
    args = parser.parse_args()
    if not args.fixtures:
        parser.error("this slice currently requires --fixtures")
    index_path = build_site(output_dir=args.output)
    print(f"Built offline dashboard: {index_path.resolve()}")


if __name__ == "__main__":
    main()

