"""Offline end-to-end demo for the fixture-backed deep-dive path."""

import argparse
import uuid
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from vcb_service.agent.providers import FixtureProvider
from vcb_service.agent.runner import build_mock_model, run_agent_safely
from vcb_service.agent.runtime import AgentRuntime
from vcb_service.agent.settings import AgentSettings, workspace_root
from vcb_service.indexer import build_index


def fixture_path(entity_id: str) -> Path:
    return Path(__file__).with_name("fixtures") / f"{entity_id}.json"


def run_mock(entity_id: str) -> Path:
    fixture = fixture_path(entity_id)
    if not fixture.is_file():
        raise SystemExit(f"mock fixture not found: {fixture}")
    root = workspace_root()
    index_path = root / "data/index/vcb.sqlite"
    if not index_path.is_file():
        build_index(
            root / "data/fixtures",
            root / "config/thesis.json",
            index_path,
            verify=True,
        )
    settings = replace(
        AgentSettings.from_env(index_path=index_path),
        run_dir=root / "data/deepdives",
        cache_dir=root / "data/cache/deepdive",
        openrouter_model="vcb-fixture-model",
    )
    now = datetime.now(UTC)
    run_id = f"dd-{now.strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:10]}"
    runtime = AgentRuntime(
        run_id=run_id,
        entity_id=entity_id,
        dimensions=["founder", "market", "idea_vs_market"],
        settings=settings,
        provider=FixtureProvider(fixture),
    )
    run_agent_safely(runtime, model=build_mock_model(entity_id))
    path = settings.run_dir / f"{run_id}.json"
    if not path.is_file():
        raise SystemExit("mock run did not persist a document")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mock", metavar="ENTITY_ID", required=True)
    args = parser.parse_args()
    print(run_mock(args.mock))


if __name__ == "__main__":
    main()
