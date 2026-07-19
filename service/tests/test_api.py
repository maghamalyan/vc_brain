import asyncio
import json
import logging
import shutil
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from vcb_service.app import create_app
from vcb_service.indexer import build_index
from vcb_service.store import IndexUnavailable

from conftest import DATA_DIR, THESIS_PATH


ADA = "ada-lovelace-fixture"


def test_health_thesis_and_cors(api_get: Callable[..., httpx.Response]) -> None:
    health = api_get("/api/v1/health", headers={"Origin": "https://demo.example"})

    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["counts"] == {"candidates": 12, "events": 480, "claims": 8}
    assert datetime.fromisoformat(health.json()["index_built_at"])
    assert health.headers["access-control-allow-origin"] == "*"

    thesis = api_get("/api/v1/thesis")
    assert thesis.status_code == 200
    assert "Fintech" in thesis.json()["sectors"]


def test_candidates_filter_sort_and_paginate(api_get: Callable[..., httpx.Response]) -> None:
    response = api_get("/api/v1/candidates")
    payload = response.json()

    assert response.status_code == 200
    assert payload["total"] == 12
    assert len(payload["items"]) == 12
    assert payload["items"][0]["gh_login"] == ADA
    assert payload["items"][0]["has_memo"] is True
    assert payload["items"][0]["recognition"] == {
        "month": "2026-07",
        "kind": "seed_round",
        "label": "Synthetic seed round announced",
    }
    assert payload["items"][0]["lead_time_months"] == 16
    assert len(payload["items"][0]["trajectory"]) == 24
    assert set(payload["items"][0]["trajectory"][0]) == {"month", "score"}
    assert all(
        item["lead_time_months"] is None
        for item in payload["items"]
        if item["recognition"] is None
    )
    assert [item["current_score"] for item in payload["items"]] == sorted(
        [item["current_score"] for item in payload["items"]], reverse=True
    )

    filtered = api_get(
        "/api/v1/candidates",
        params={
            "source": "inbound_application",
            "status": "memo_ready",
            "sort": "momentum",
            "limit": 1,
            "offset": 0,
        },
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] >= 1
    assert len(filtered.json()["items"]) == 1
    assert filtered.json()["items"][0]["source"] == "inbound_application"
    assert filtered.json()["items"][0]["status"] == "memo_ready"


def test_candidate_detail_memo_claim_and_evidence(
    api_get: Callable[..., httpx.Response],
) -> None:
    detail = api_get(f"/api/v1/candidates/{ADA}")
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["candidate"]["gh_login"] == ADA
    assert payload["recognition"]["kind"] == "seed_round"
    assert 4 <= len(payload["score_components"]) <= 6
    assert set(payload["score_components"][0]) == {"key", "label", "contribution"}
    assert sum(
        component["contribution"] for component in payload["score_components"]
    ) == pytest.approx(payload["candidate"]["current_score"], abs=0.001)
    assert len(payload["trajectory"]) == 24
    assert payload["trajectory"] == sorted(payload["trajectory"], key=lambda row: row["month"])
    assert payload["three_axis"]["founder"]["score"] == 9.1
    assert payload["memo_available"] is True
    assert sum(payload["evidence_counts_by_type"].values()) == 40

    evidence = api_get(
        f"/api/v1/candidates/{ADA}/evidence",
        params={"type": "release_published", "limit": 100},
    )
    assert evidence.status_code == 200
    assert evidence.json()["total"] > 0
    assert all(item["event_type"] == "release_published" for item in evidence.json()["items"])

    memo = api_get(f"/api/v1/candidates/{ADA}/memo")
    expected_memo = json.loads((DATA_DIR / "memos" / f"{ADA}.json").read_text())
    assert memo.status_code == 200
    assert memo.json() == expected_memo

    claim = api_get("/api/v1/claims/ada-license")
    assert claim.status_code == 200
    assert claim.json()["claim"] == expected_memo["claims"]["ada-license"]
    assert len(claim.json()["resolved_evidence"]) == 2
    assert all("evidence_id" in item for item in claim.json()["resolved_evidence"])

    no_memo = api_get("/api/v1/candidates/edsger-dijkstra-fixture/memo")
    assert no_memo.status_code == 404


def test_evidence_dates_are_filtered_server_side(
    api_get: Callable[..., httpx.Response],
) -> None:
    after = date(2025, 3, 1)
    before = date(2025, 3, 2)
    response = api_get(
        f"/api/v1/candidates/{ADA}/evidence",
        params={"after": after.isoformat(), "before": before.isoformat(), "limit": 100},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert len(payload["items"]) == 2
    assert all(
        after <= datetime.fromisoformat(item["ts"]).date() <= before
        for item in payload["items"]
    )

    invalid = api_get(
        f"/api/v1/candidates/{ADA}/evidence",
        params={"after": "2025-04-01", "before": "2025-03-01"},
    )
    assert invalid.status_code == 422


@pytest.mark.parametrize(
    ("query", "expected_type"),
    [("ada", "founder"), ("AGPL", "evidence"), ("fintech", "thesis_term")],
)
def test_fts_prefix_search_returns_grouped_highlighted_results(
    api_get: Callable[..., httpx.Response], query: str, expected_type: str
) -> None:
    response = api_get("/api/v1/search", params={"q": query, "limit": 20})

    assert response.status_code == 200
    groups = response.json()["groups"]
    assert groups
    assert expected_type in {group["type"] for group in groups}
    hits = [hit for group in groups for hit in group["hits"]]
    assert all(hit["doc_type"] == group["type"] for group in groups for hit in group["hits"])
    assert any("<mark>" in hit["snippet"] for hit in hits)


def test_search_supports_prefix_and_type_filter(api_get: Callable[..., httpx.Response]) -> None:
    response = api_get(
        "/api/v1/search", params=[("q", "fin"), ("types", "company,thesis_term")]
    )

    assert response.status_code == 200
    assert {group["type"] for group in response.json()["groups"]} <= {
        "company",
        "thesis_term",
    }
    assert response.json()["groups"]


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/candidates/missing-founder",
        "/api/v1/candidates/missing-founder/evidence",
        "/api/v1/candidates/missing-founder/memo",
        "/api/v1/claims/missing-claim",
        "/",
    ],
)
def test_missing_resources_and_absent_frontend_return_404(
    api_get: Callable[..., httpx.Response], path: str
) -> None:
    assert api_get(path).status_code == 404


def test_openapi_contains_read_and_deepdive_routes(api_get: Callable[..., httpx.Response]) -> None:
    response = api_get("/api/v1/openapi.json")

    assert response.status_code == 200
    paths = set(response.json()["paths"])
    assert "/api/v1/health" in paths
    assert "/api/v1/search" in paths
    assert "/api/v1/candidates/{login}/memo" in paths
    assert "/api/v1/deepdive" in paths
    assert "/api/v1/deepdive/runs/{run_id}/stream" in paths


def test_disabled_deepdive_fails_closed_before_manager_start(
    index_path: Path, tmp_path: Path
) -> None:
    class ExplodingManager:
        called = False

        async def start(self, _body: object) -> str:
            self.called = True
            raise AssertionError("disabled deployment must not start the manager")

    manager = ExplodingManager()
    app = create_app(
        index_path=index_path,
        frontend_dist=tmp_path / "no-frontend",
        deepdive_manager=manager,  # type: ignore[arg-type]
        deepdive_enabled=False,
    )

    async def request() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.post(
                "/api/v1/deepdive",
                json={"entity_type": "founder", "entity_id": ADA},
            )

    response = asyncio.run(request())

    assert response.status_code == 503
    assert response.json() == {
        "detail": {
            "code": "LIVE_DEEPDIVE_DISABLED",
            "message": "Live deep-dives are disabled for this deployment.",
        }
    }
    assert manager.called is False


def test_startup_validates_index_and_logs_readiness(
    index_path: Path, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    app = create_app(index_path=index_path, frontend_dist=tmp_path / "no-frontend")

    with caplog.at_level(logging.INFO, logger="vcb_service"):
        with TestClient(app) as client:
            assert client.get("/api/v1/health").status_code == 200

    assert "event=service_ready" in caplog.text
    assert "candidates=12 events=480 claims=8" in caplog.text


def test_startup_rejects_missing_index(tmp_path: Path) -> None:
    app = create_app(
        index_path=tmp_path / "missing.sqlite",
        frontend_dist=tmp_path / "no-frontend",
    )

    with pytest.raises(IndexUnavailable, match="index file not found"):
        with TestClient(app):
            pass


def test_invalid_deepdive_flag_is_rejected(
    index_path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VCB_DEEPDIVE_ENABLED", "sometimes")

    with pytest.raises(ValueError, match="VCB_DEEPDIVE_ENABLED must be a boolean"):
        create_app(index_path=index_path, frontend_dist=tmp_path / "no-frontend")


def test_history_fallback_serves_frontend_when_present(
    index_path: Path, tmp_path: Path
) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<html>VC Brain frontend</html>", encoding="utf-8")
    app = create_app(index_path=index_path, frontend_dist=dist)

    async def request(path: str) -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.get(path)

    root = asyncio.run(request("/"))
    history_route = asyncio.run(request("/candidate/ada-lovelace-fixture"))

    assert root.status_code == 200
    assert history_route.status_code == 200
    assert "VC Brain frontend" in history_route.text


def test_api_normalizes_missing_optional_d1_upstream_fields(tmp_path: Path) -> None:
    partial_data = tmp_path / "fixtures"
    shutil.copytree(DATA_DIR, partial_data)
    (partial_data / "candidates.parquet").unlink()
    candidates_path = partial_data / "candidates.json"
    candidates = json.loads(candidates_path.read_text(encoding="utf-8"))
    candidates[0].pop("recognition")
    candidates[0].pop("score_components")
    candidates_path.write_text(json.dumps(candidates), encoding="utf-8")
    partial_index = tmp_path / "partial.sqlite"
    build_index(partial_data, THESIS_PATH, partial_index, verify=True)
    app = create_app(index_path=partial_index, frontend_dist=tmp_path / "no-frontend")

    async def request(path: str) -> httpx.Response:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://testserver"
        ) as client:
            return await client.get(path)

    listing = asyncio.run(request("/api/v1/candidates"))
    item = next(row for row in listing.json()["items"] if row["gh_login"] == ADA)
    detail = asyncio.run(request(f"/api/v1/candidates/{ADA}"))

    assert listing.status_code == 200
    assert item["recognition"] is None
    assert item["lead_time_months"] is None
    assert len(item["trajectory"]) == 24
    assert detail.status_code == 200
    assert detail.json()["recognition"] is None
    assert detail.json()["score_components"] == []
