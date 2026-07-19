"""FastAPI application for the frozen VC Brain v1 read API."""

import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Annotated, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse

from vcb_service.agent.manager import DeepDiveAdmissionError, DeepDiveManager
from vcb_service.agent.models import (
    DeepDiveAccepted,
    DeepDiveRequest,
    DeepDiveRun,
    DeepDiveRunSummary,
)
from vcb_service.agent.settings import AgentSettings

from vcb_service.models import (
    CandidateDetail,
    CandidatePage,
    CandidateStatus,
    ClaimResponse,
    EvidencePage,
    HealthResponse,
    MemoResponse,
    SearchResponse,
    Source,
    Thesis,
)
from vcb_service.store import IndexUnavailable, ReadStore, normalize_search_types


load_dotenv()

logger = logging.getLogger("vcb_service")


def _environment_flag(name: str, *, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    normalized = raw.strip().casefold()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value")


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def create_app(
    *,
    index_path: Path | None = None,
    frontend_dist: Path | None = None,
    deepdive_manager: DeepDiveManager | None = None,
    deepdive_enabled: bool | None = None,
) -> FastAPI:
    configured_index = index_path or Path(os.getenv("VCB_INDEX", "data/index/vcb.sqlite"))
    store = ReadStore(configured_index)
    dist = (frontend_dist or (_workspace_root() / "frontend" / "dist")).resolve()
    manager = deepdive_manager or DeepDiveManager(
        AgentSettings.from_env(index_path=configured_index)
    )
    live_deepdive_enabled = (
        _environment_flag("VCB_DEEPDIVE_ENABLED", default=True)
        if deepdive_enabled is None
        else deepdive_enabled
    )

    @asynccontextmanager
    async def lifespan(_application: FastAPI):
        readiness = store.health()
        counts = readiness["counts"]
        logger.info(
            "event=service_ready index_built_at=%s candidates=%d events=%d claims=%d",
            readiness["index_built_at"],
            counts["candidates"],
            counts["events"],
            counts["claims"],
        )
        yield

    application = FastAPI(
        title="VC Brain Intelligence API",
        version="1.0.0",
        openapi_url="/api/v1/openapi.json",
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )
    application.state.deepdive_manager = manager
    application.state.deepdive_enabled = live_deepdive_enabled

    @application.exception_handler(IndexUnavailable)
    async def index_unavailable_handler(
        _request: Request, error: IndexUnavailable
    ) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(error)})

    @application.get("/api/v1/health", response_model=HealthResponse, tags=["read"])
    def health() -> dict:
        return store.health()

    @application.get("/api/v1/thesis", response_model=Thesis, tags=["read"])
    def thesis() -> dict:
        return store.thesis()

    @application.get(
        "/api/v1/candidates", response_model=CandidatePage, tags=["candidates"]
    )
    def candidates(
        source: Source | None = None,
        status: CandidateStatus | None = None,
        sort: Literal["score", "momentum"] = "score",
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
        offset: Annotated[int, Query(ge=0)] = 0,
    ) -> dict:
        return store.candidates(
            source=source, status=status, sort=sort, limit=limit, offset=offset
        )

    @application.get(
        "/api/v1/candidates/{login}",
        response_model=CandidateDetail,
        tags=["candidates"],
    )
    def candidate(login: str) -> dict:
        result = store.candidate(login)
        if result is None:
            raise HTTPException(status_code=404, detail="candidate not found")
        return result

    @application.get(
        "/api/v1/candidates/{login}/evidence",
        response_model=EvidencePage,
        tags=["candidates"],
    )
    def evidence(
        login: str,
        event_type: Annotated[str | None, Query(alias="type")] = None,
        after: date | None = None,
        before: date | None = None,
        limit: Annotated[int, Query(ge=1, le=500)] = 100,
    ) -> dict:
        if after is not None and before is not None and after > before:
            raise HTTPException(status_code=422, detail="after must not be later than before")
        result = store.evidence(
            login,
            event_type=event_type,
            after=after,
            before=before,
            limit=limit,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="candidate not found")
        return result

    @application.get(
        "/api/v1/candidates/{login}/memo",
        response_model=MemoResponse,
        tags=["candidates"],
    )
    def memo(login: str) -> MemoResponse:
        result = store.memo(login)
        if result is None:
            raise HTTPException(status_code=404, detail="memo not found")
        return MemoResponse.model_validate(result)

    @application.get(
        "/api/v1/claims/{claim_id}", response_model=ClaimResponse, tags=["claims"]
    )
    def claim(claim_id: str) -> dict:
        result = store.claim(claim_id)
        if result is None:
            raise HTTPException(status_code=404, detail="claim not found")
        return result

    @application.get("/api/v1/search", response_model=SearchResponse, tags=["search"])
    def search(
        q: Annotated[str, Query(min_length=1)],
        types: Annotated[list[str] | None, Query()] = None,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
    ) -> dict:
        try:
            normalized_types = normalize_search_types(types)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        return store.search(q, types=normalized_types, limit=limit)

    @application.post(
        "/api/v1/deepdive",
        response_model=DeepDiveAccepted,
        status_code=status.HTTP_202_ACCEPTED,
        tags=["deepdive"],
    )
    async def start_deepdive(body: DeepDiveRequest) -> DeepDiveAccepted:
        if not live_deepdive_enabled:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "code": "LIVE_DEEPDIVE_DISABLED",
                    "message": "Live deep-dives are disabled for this deployment.",
                },
            )
        try:
            run_id = await manager.start(body)
        except DeepDiveAdmissionError as error:
            raise HTTPException(
                status_code=error.status_code,
                detail={"code": error.code, "message": str(error)},
            ) from error
        return DeepDiveAccepted(run_id=run_id)

    @application.get(
        "/api/v1/deepdive/runs",
        response_model=list[DeepDiveRunSummary],
        tags=["deepdive"],
    )
    def list_deepdives(entity_id: str | None = None) -> list[DeepDiveRunSummary]:
        return manager.list_runs(entity_id)

    @application.get(
        "/api/v1/deepdive/runs/{run_id}",
        response_model=DeepDiveRun,
        tags=["deepdive"],
    )
    def get_deepdive(run_id: str) -> DeepDiveRun:
        document = manager.load(run_id)
        if document is None:
            raise HTTPException(status_code=404, detail="deep-dive run not found")
        return document

    @application.get(
        "/api/v1/deepdive/runs/{run_id}/stream",
        response_class=EventSourceResponse,
        tags=["deepdive"],
    )
    async def stream_deepdive(run_id: str) -> EventSourceResponse:
        if manager.load(run_id) is None:
            raise HTTPException(status_code=404, detail="deep-dive run not found")

        async def events():
            async for step in manager.stream(run_id):
                yield {
                    "event": "step",
                    "id": str(step.seq),
                    "data": json.dumps(step.model_dump(mode="json"), ensure_ascii=False),
                }

        return EventSourceResponse(events(), ping=15)

    @application.get("/{full_path:path}", include_in_schema=False)
    def frontend_fallback(full_path: str) -> FileResponse:
        index_file = dist / "index.html"
        if not index_file.is_file() or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="not found")
        requested = (dist / full_path).resolve()
        if requested.is_relative_to(dist) and requested.is_file():
            return FileResponse(requested)
        return FileResponse(index_file)

    return application


app = create_app()
