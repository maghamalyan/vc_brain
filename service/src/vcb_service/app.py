"""FastAPI application for the frozen VC Brain v1 read API."""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Annotated, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

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


def _workspace_root() -> Path:
    return Path(__file__).resolve().parents[3]


def create_app(
    *,
    index_path: Path | None = None,
    frontend_dist: Path | None = None,
) -> FastAPI:
    configured_index = index_path or Path(os.getenv("VCB_INDEX", "data/index/vcb.sqlite"))
    store = ReadStore(configured_index)
    dist = (frontend_dist or (_workspace_root() / "frontend" / "dist")).resolve()

    application = FastAPI(
        title="VC Brain Intelligence API",
        version="1.0.0",
        openapi_url="/api/v1/openapi.json",
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )

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
