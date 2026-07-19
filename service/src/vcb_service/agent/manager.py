"""Admission control, background execution, persistence, and replay for runs."""

import asyncio
import uuid
from collections import deque
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from pydantic_ai.models import Model

from vcb_service.agent.models import (
    DeepDiveRequest,
    DeepDiveRun,
    DeepDiveRunSummary,
    RunStep,
)
from vcb_service.agent.providers import DataProvider, PublicDataProvider
from vcb_service.agent.runner import run_agent_safely
from vcb_service.agent.runtime import AgentRuntime
from vcb_service.agent.settings import AgentSettings


class DeepDiveAdmissionError(RuntimeError):
    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


@dataclass
class ActiveRun:
    runtime: AgentRuntime
    queue: asyncio.Queue[RunStep | None]
    task: asyncio.Task[None] | None = None


class DeepDiveManager:
    def __init__(
        self,
        settings: AgentSettings,
        *,
        provider_factory: Callable[[], DataProvider] | None = None,
        model_factory: Callable[[AgentRuntime], Model | None] | None = None,
        replay_delay: float = 0.3,
    ) -> None:
        self.settings = settings
        self._provider_factory = provider_factory or (
            lambda: PublicDataProvider(
                settings.cache_dir, serpapi_key=settings.serpapi_key
            )
        )
        self._uses_live_model = model_factory is None
        self._model_factory = model_factory or (lambda _runtime: None)
        self.replay_delay = replay_delay
        self._active: dict[str, ActiveRun] = {}
        self._starts: deque[datetime] = deque()
        self._lock = asyncio.Lock()

    async def start(self, request: DeepDiveRequest) -> str:
        if request.mode in {None, "replay"}:
            cached = self.latest_for_request(request.entity_id, list(request.dimensions))
            if cached is not None:
                return cached.run_id
            if request.mode == "replay":
                raise DeepDiveAdmissionError(
                    "REPLAY_NOT_FOUND", "No cached run exists for this entity.", 404
                )
        if not self.settings.openrouter_key and self._uses_live_model:
            raise DeepDiveAdmissionError(
                "OPENROUTER_UNAVAILABLE",
                "OPENROUTER_KEY is required for a live deep-dive.",
                503,
            )
        now = datetime.now(UTC)
        async with self._lock:
            cutoff = now - timedelta(days=1)
            while self._starts and self._starts[0] < cutoff:
                self._starts.popleft()
            if len(self._active) >= self.settings.max_concurrent:
                raise DeepDiveAdmissionError(
                    "CONCURRENT_LIMIT",
                    "Deep-dive concurrency limit reached; retry later.",
                    429,
                )
            if len(self._starts) >= self.settings.daily_limit:
                raise DeepDiveAdmissionError(
                    "DAILY_LIMIT", "Daily deep-dive quota reached.", 429
                )
            run_id = f"dd-{now.strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:10]}"
            queue: asyncio.Queue[RunStep | None] = asyncio.Queue()
            loop = asyncio.get_running_loop()
            runtime = AgentRuntime(
                run_id=run_id,
                entity_id=request.entity_id,
                dimensions=list(request.dimensions),
                settings=self.settings,
                provider=self._provider_factory(),
                queue=queue,
                loop=loop,
            )
            state = ActiveRun(runtime=runtime, queue=queue)
            self._active[run_id] = state
            self._starts.append(now)
            state.task = asyncio.create_task(self._execute(state))
            return run_id

    async def _execute(self, state: ActiveRun) -> None:
        try:
            model = self._model_factory(state.runtime)
            await asyncio.to_thread(run_agent_safely, state.runtime, model=model)
        finally:
            async with self._lock:
                self._active.pop(state.runtime.run_id, None)

    async def stream(self, run_id: str) -> AsyncIterator[RunStep]:
        state = self._active.get(run_id)
        if state is not None:
            while True:
                step = await state.queue.get()
                if step is None:
                    if state.task is not None:
                        await state.task
                    return
                yield step
            return
        document = self.load(run_id)
        if document is None:
            raise KeyError(run_id)
        for step in document.steps:
            if self.replay_delay:
                await asyncio.sleep(self.replay_delay)
            yield step

    def load(self, run_id: str) -> DeepDiveRun | None:
        path = self._path(run_id)
        if not path.is_file():
            state = self._active.get(run_id)
            return state.runtime.snapshot() if state else None
        return DeepDiveRun.model_validate_json(path.read_text(encoding="utf-8"))

    def list_runs(self, entity_id: str | None = None) -> list[DeepDiveRunSummary]:
        items: list[DeepDiveRunSummary] = []
        if self.settings.run_dir.is_dir():
            for path in self.settings.run_dir.glob("dd-*.json"):
                run = DeepDiveRun.model_validate_json(path.read_text(encoding="utf-8"))
                if entity_id is not None and run.entity_id != entity_id:
                    continue
                outcome = None
                for step in reversed(run.steps):
                    if step.kind in {"done", "error"} and step.payload:
                        candidate = step.payload.get("outcome")
                        if candidate in {"OK", "INSUFFICIENT_EVIDENCE", "ERROR"}:
                            outcome = candidate
                            break
                items.append(
                    DeepDiveRunSummary(
                        run_id=run.run_id,
                        entity_id=run.entity_id,
                        started_at=run.started_at,
                        finished_at=run.finished_at,
                        outcome=outcome,
                        claim_count=len(run.claims),
                    )
                )
        items.sort(key=lambda item: item.started_at, reverse=True)
        return items

    def latest_for_request(
        self, entity_id: str, dimensions: list[str]
    ) -> DeepDiveRunSummary | None:
        requested = list(dimensions)
        summaries = {item.run_id: item for item in self.list_runs(entity_id)}
        for summary in summaries.values():
            run = self.load(summary.run_id)
            if run is None or not run.steps:
                continue
            payload = run.steps[0].payload
            assert payload is not None  # RunStep validation enforces plan dimensions.
            if payload.get("dimensions") == requested:
                return summary
        return None

    def _path(self, run_id: str) -> Path:
        if not run_id.startswith("dd-") or not all(
            character.isalnum() or character in {"-", "_"} for character in run_id
        ):
            return self.settings.run_dir / "invalid-run-id"
        return self.settings.run_dir / f"{run_id}.json"
