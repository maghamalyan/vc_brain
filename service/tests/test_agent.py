import asyncio
import json
import sqlite3
import threading
import uuid
from dataclasses import replace
from pathlib import Path

import httpx
import pytest
from pydantic_ai.messages import ModelResponse, ToolCallPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from vcb_service.agent.manager import DeepDiveAdmissionError, DeepDiveManager
from vcb_service.agent.models import DeepDiveRequest, DeepDiveRun
from vcb_service.agent.providers import FixtureProvider
from vcb_service.agent.runner import build_mock_model, run_agent_safely
from vcb_service.agent.runtime import AgentRuntime
from vcb_service.agent.settings import AgentSettings
from vcb_service.app import create_app


ENTITY = "ada-lovelace-fixture"
FIXTURE = (
    Path(__file__).resolve().parents[1]
    / "src/vcb_service/agent/fixtures/ada-lovelace-fixture.json"
)


def settings(index_path: Path, tmp_path: Path) -> AgentSettings:
    return replace(
        AgentSettings.from_env(index_path=index_path),
        run_dir=tmp_path / "deepdives",
        cache_dir=tmp_path / "cache",
        openrouter_key="fixture-key",
        openrouter_model="vcb-fixture-model",
    )


def runtime(index_path: Path, tmp_path: Path, *, run_id: str | None = None) -> AgentRuntime:
    return AgentRuntime(
        run_id=run_id or f"dd-test-{uuid.uuid4().hex[:10]}",
        entity_id=ENTITY,
        dimensions=["founder", "market", "idea_vs_market"],
        settings=settings(index_path, tmp_path),
        provider=FixtureProvider(FIXTURE),
    )


def run_fixture_agent(agent_runtime: AgentRuntime) -> None:
    asyncio.run(
        asyncio.to_thread(
            run_agent_safely,
            agent_runtime,
            model=build_mock_model(ENTITY),
        )
    )


def test_draft_claim_rejects_nonexistent_evidence_id(
    index_path: Path, tmp_path: Path
) -> None:
    agent_runtime = runtime(index_path, tmp_path)

    result = agent_runtime.functions["draft_claim"](
        "This claim must never enter the store.",
        ["live-does-not-exist"],
        0.8,
        "single_source",
        [],
    )

    assert result["error"]["code"] == "UNKNOWN_EVIDENCE_REF"
    assert "unknown evidence_refs rejected" in result["error"]["message"]
    assert agent_runtime.claims == {}


@pytest.mark.parametrize("statement", ["INSERT INTO candidates VALUES (1)", "UPDATE candidates SET status='screened'", "DROP TABLE candidates"])
def test_sql_mutations_are_denied(
    statement: str, index_path: Path, tmp_path: Path
) -> None:
    agent_runtime = runtime(index_path, tmp_path)
    with sqlite3.connect(index_path) as connection:
        before = connection.execute("SELECT count(*) FROM candidates").fetchone()[0]

    result = agent_runtime.functions["sql"](statement)

    assert result["error"]["code"] == "RUNTIME_POLICY_DENIED"
    assert {finding["code"] for finding in result["error"]["findings"]} >= {
        "SQL_READ_ONLY",
        "SQL_DENIED_PATTERN",
    }
    with sqlite3.connect(index_path) as connection:
        after = connection.execute("SELECT count(*) FROM candidates").fetchone()[0]
    assert after == before


def test_function_model_run_persists_every_audit_step_one_to_one(
    index_path: Path, tmp_path: Path
) -> None:
    agent_runtime = runtime(index_path, tmp_path)

    run_fixture_agent(agent_runtime)

    path = agent_runtime.settings.run_dir / f"{agent_runtime.run_id}.json"
    document = DeepDiveRun.model_validate_json(path.read_text(encoding="utf-8"))
    assert len(document.steps) == len(agent_runtime.audit_events)
    assert [step.model_dump(mode="json") for step in document.steps] == [
        event.model_dump(mode="json") for event in agent_runtime.audit_events
    ]
    assert len(document.evidence) == 3
    assert len(document.claims) == 2
    assert document.steps[-1].kind == "done"
    assert all(
        ref in {event.evidence_id for event in document.evidence}
        for claim in document.claims.values()
        for ref in claim.evidence_refs
    )


def test_replay_endpoint_streams_cached_steps(
    index_path: Path, tmp_path: Path
) -> None:
    agent_runtime = runtime(index_path, tmp_path, run_id="dd-replay-fixture")
    run_fixture_agent(agent_runtime)
    manager = DeepDiveManager(agent_runtime.settings, replay_delay=0)
    app = create_app(
        index_path=index_path,
        frontend_dist=tmp_path / "missing-frontend",
        deepdive_manager=manager,
    )

    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.get(
                f"/api/v1/deepdive/runs/{agent_runtime.run_id}/stream"
            )

    response = asyncio.run(request())
    data_lines = [
        line.removeprefix("data: ")
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]
    streamed = [json.loads(line) for line in data_lines]
    assert response.status_code == 200
    assert [step["seq"] for step in streamed] == list(
        range(1, len(agent_runtime.steps) + 1)
    )
    assert streamed[-1]["kind"] == "done"

    async def read_run_and_list() -> tuple[httpx.Response, httpx.Response]:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return (
                await client.get(f"/api/v1/deepdive/runs/{agent_runtime.run_id}"),
                await client.get("/api/v1/deepdive/runs", params={"entity_id": ENTITY}),
            )

    run_response, list_response = asyncio.run(read_run_and_list())
    assert run_response.status_code == 200
    assert run_response.json()["provenance"] == "live"
    assert list_response.json()[0]["run_id"] == agent_runtime.run_id

    async def start_replay() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.post(
                "/api/v1/deepdive",
                json={
                    "entity_type": "founder",
                    "entity_id": ENTITY,
                    "dimensions": ["founder", "market", "idea_vs_market"],
                    "mode": "replay",
                },
            )

    replay_response = asyncio.run(start_replay())
    assert replay_response.status_code == 202
    assert replay_response.json() == {"run_id": agent_runtime.run_id}


def test_manager_enforces_concurrent_and_daily_limits(
    index_path: Path, tmp_path: Path
) -> None:
    started = threading.Event()
    release = threading.Event()

    def respond(_messages: list[object], info: AgentInfo) -> ModelResponse:
        started.set()
        assert release.wait(timeout=5)
        return ModelResponse(
            [
                ToolCallPart(
                    info.output_tools[0].name,
                    {"summary": "Bounded fixture run completed.", "outcome": "OK"},
                )
            ]
        )

    bounded_settings = replace(
        settings(index_path, tmp_path), max_concurrent=1, daily_limit=1
    )
    manager = DeepDiveManager(
        bounded_settings,
        provider_factory=lambda: FixtureProvider(FIXTURE),
        model_factory=lambda _runtime: FunctionModel(respond),
        replay_delay=0,
    )
    request = DeepDiveRequest(entity_id=ENTITY, mode="live")

    async def scenario() -> tuple[str, str]:
        run_id = await manager.start(request)
        assert await asyncio.to_thread(started.wait, 2)
        with pytest.raises(DeepDiveAdmissionError) as concurrent:
            await manager.start(request)
        release.set()
        _ = [step async for step in manager.stream(run_id)]
        with pytest.raises(DeepDiveAdmissionError) as daily:
            await manager.start(request)
        return concurrent.value.code, daily.value.code

    assert asyncio.run(scenario()) == ("CONCURRENT_LIMIT", "DAILY_LIMIT")
