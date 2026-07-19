from __future__ import annotations

import asyncio
import socket
from collections.abc import Callable, Iterator
from pathlib import Path

import httpx
import pytest
from fastapi import FastAPI

from vcb_service.app import create_app
from vcb_service.indexer import build_index


WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = WORKSPACE_ROOT / "data" / "fixtures"
THESIS_PATH = WORKSPACE_ROOT / "config" / "thesis.json"


@pytest.fixture(autouse=True)
def no_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked_connect(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("network access is forbidden in service tests")

    monkeypatch.setattr(socket.socket, "connect", blocked_connect)


@pytest.fixture(scope="session")
def index_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("vcb-index") / "vcb.sqlite"
    build_index(DATA_DIR, THESIS_PATH, output, verify=True)
    return output


@pytest.fixture(scope="session")
def app(index_path: Path) -> FastAPI:
    return create_app(index_path=index_path, frontend_dist=index_path.parent / "no-frontend")


@pytest.fixture
def api_get(app: FastAPI) -> Iterator[Callable[..., httpx.Response]]:
    async def get(path: str, **kwargs: object) -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.get(path, **kwargs)

    yield lambda path, **kwargs: asyncio.run(get(path, **kwargs))
