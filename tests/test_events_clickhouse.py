from datetime import date
from pathlib import Path

import httpx
import polars as pl
import pytest

from vc_brain.ingest.clickhouse import (
    ClickHouseClient,
    ClickHouseQueryError,
    ResultSizeLimitError,
)


def test_query_parses_mocked_tsv_and_reuses_sql_hash_cache(tmp_path: Path) -> None:
    requests: list[httpx.Request] = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            text="month\tevent_type\tevent_count\n2025-01-01\tPushEvent\t123\n",
        )

    http = httpx.Client(transport=httpx.MockTransport(respond))
    client = ClickHouseClient(
        cache_dir=tmp_path, client=http, minimum_interval_seconds=0
    )

    first = client.query("SELECT 1")
    second = client.query("SELECT 1")

    assert first.to_dicts() == [
        {"month": date(2025, 1, 1), "event_type": "PushEvent", "event_count": 123}
    ]
    assert second.equals(first)
    assert len(requests) == 1
    assert requests[0].url.params["user"] == "play"
    assert requests[0].content.decode().endswith("FORMAT TSVWithNames")
    assert len(list(tmp_path.glob("*.parquet"))) == 1


def test_query_retries_mocked_503_then_succeeds(tmp_path: Path) -> None:
    statuses = iter((503, 200))

    def respond(_: httpx.Request) -> httpx.Response:
        status = next(statuses)
        return httpx.Response(status, text="value\n7\n" if status == 200 else "busy")

    http = httpx.Client(transport=httpx.MockTransport(respond))
    client = ClickHouseClient(
        cache_dir=tmp_path,
        client=http,
        minimum_interval_seconds=0,
        max_attempts=2,
    )

    assert client.query("SELECT 7").item() == 7


def test_query_does_not_retry_mocked_bad_sql(tmp_path: Path) -> None:
    calls = 0

    def respond(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(400, text="syntax error")

    client = ClickHouseClient(
        cache_dir=tmp_path,
        client=httpx.Client(transport=httpx.MockTransport(respond)),
        minimum_interval_seconds=0,
    )

    with pytest.raises(ClickHouseQueryError):
        client.query("NOT SQL")
    assert calls == 1


def test_oversized_actor_batch_is_split_recursively(tmp_path: Path) -> None:
    client = ClickHouseClient(
        cache_dir=tmp_path,
        client=httpx.Client(
            transport=httpx.MockTransport(lambda _: httpx.Response(500))
        ),
        minimum_interval_seconds=0,
        result_row_guard=3,
    )
    calls: list[str] = []

    def fake_query(sql: str) -> pl.DataFrame:
        calls.append(sql)
        actors = sql.split(",")
        return pl.DataFrame({"actor_login": actors})

    client.query = fake_query  # type: ignore[method-assign]
    actors = ["a", "b", "c", "d"]

    result = client.query_actor_batch(actors, lambda rows: ",".join(rows))

    assert result.get_column("actor_login").to_list() == actors
    assert calls == ["a,b,c,d", "a,b", "c,d"]


def test_single_actor_at_result_guard_fails_clearly(tmp_path: Path) -> None:
    client = ClickHouseClient(
        cache_dir=tmp_path,
        client=httpx.Client(
            transport=httpx.MockTransport(lambda _: httpx.Response(500))
        ),
        minimum_interval_seconds=0,
        result_row_guard=1,
    )
    client.query = lambda _: pl.DataFrame({"actor_login": ["a"]})  # type: ignore[method-assign]

    with pytest.raises(ResultSizeLimitError, match="Single-actor"):
        client.query_actor_batch(["a"], lambda rows: rows[0])


def test_memory_limit_response_bisects_actor_batch(tmp_path: Path) -> None:
    requests: list[str] = []

    def respond(request: httpx.Request) -> httpx.Response:
        sql = request.content.decode()
        requests.append(sql)
        if "a,b" in sql:
            return httpx.Response(
                500,
                text="Code: 241. DB::Exception: Query memory limit exceeded",
            )
        actor = sql.splitlines()[0]
        return httpx.Response(200, text=f"actor_login\n{actor}\n")

    client = ClickHouseClient(
        cache_dir=tmp_path,
        client=httpx.Client(transport=httpx.MockTransport(respond)),
        minimum_interval_seconds=0,
    )

    frame = client.query_actor_batch(["a", "b"], lambda rows: ",".join(rows))

    assert frame.get_column("actor_login").to_list() == ["a", "b"]
    assert len(requests) == 3
