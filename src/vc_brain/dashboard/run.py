"""Command-line entry point for the static VC Brain dashboard."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from vc_brain.dashboard.build import build_site
from vc_brain.dashboard.wire import DashboardWiringError, wire_real_data


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--fixtures",
        action="store_true",
        help="Build from the deterministic synthetic fixture corpus",
    )
    mode.add_argument(
        "--real",
        action="store_true",
        help="Build from label, event, model-eval, and optional memo outputs",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Override the mode's data root (fixtures: data/fixtures; real: data)",
    )
    parser.add_argument("--output", type=Path, default=Path("site"))
    args = parser.parse_args(argv)
    if args.fixtures:
        data_dir = args.data_dir or Path("data/fixtures")
        index_path = build_site(data_dir=data_dir, output_dir=args.output)
        mode_label = "fixture"
    else:
        data_dir = args.data_dir or Path("data")
        try:
            inputs = wire_real_data(data_dir)
        except DashboardWiringError as exc:
            parser.error(str(exc))
        index_path = build_site(inputs=inputs, output_dir=args.output)
        mode_label = "real-data"
    print(f"Built {mode_label} offline dashboard: {index_path.resolve()}")


if __name__ == "__main__":
    main()
