"""Read-only queries over the single SQLite deployment artifact."""

from __future__ import annotations

import json
import re
import sqlite3
from collections import OrderedDict
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Any, Iterator, Sequence

from vcb_service.indexer import DOC_TYPES


class IndexUnavailable(RuntimeError):
    """The configured SQLite artifact is absent or not a valid VC Brain index."""


class ReadStore:
    def __init__(self, index_path: Path) -> None:
        self.index_path = index_path.resolve()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        if not self.index_path.is_file():
            raise IndexUnavailable(f"index file not found: {self.index_path}")
        uri = f"{self.index_path.as_uri()}?mode=ro"
        try:
            connection = sqlite3.connect(uri, uri=True)
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA query_only=ON")
        except sqlite3.Error as error:
            raise IndexUnavailable(f"cannot open index: {self.index_path}") from error
        try:
            yield connection
        except sqlite3.Error as error:
            raise IndexUnavailable(f"invalid index: {self.index_path}") from error
        finally:
            connection.close()

    def health(self) -> dict[str, Any]:
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT
                    (SELECT value FROM metadata WHERE key = 'index_built_at') AS built_at,
                    (SELECT count(*) FROM candidates) AS candidates,
                    (SELECT count(*) FROM events) AS events,
                    (SELECT count(*) FROM claims) AS claims
                """
            ).fetchone()
        if row is None or row["built_at"] is None:
            raise IndexUnavailable(f"invalid index: {self.index_path}")
        return {
            "status": "ok",
            "index_built_at": row["built_at"],
            "counts": {
                "candidates": row["candidates"],
                "events": row["events"],
                "claims": row["claims"],
            },
        }

    def thesis(self) -> dict[str, Any]:
        with self._connection() as connection:
            row = connection.execute("SELECT data_json FROM thesis WHERE id = 1").fetchone()
        if row is None:
            raise IndexUnavailable(f"invalid index: {self.index_path}")
        return json.loads(row["data_json"])

    def candidates(
        self,
        *,
        source: str | None,
        status: str | None,
        sort: str,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        predicates: list[str] = []
        parameters: list[Any] = []
        if source is not None:
            predicates.append("source = ?")
            parameters.append(source)
        if status is not None:
            predicates.append("status = ?")
            parameters.append(status)
        where = f"WHERE {' AND '.join(predicates)}" if predicates else ""
        order_column = "current_score" if sort == "score" else "momentum_3mo"
        with self._connection() as connection:
            total = connection.execute(
                f"SELECT count(*) FROM candidates {where}", parameters
            ).fetchone()[0]
            rows = connection.execute(
                f"SELECT data_json, has_memo FROM candidates {where} "
                f"ORDER BY {order_column} DESC, gh_login ASC LIMIT ? OFFSET ?",
                [*parameters, limit, offset],
            ).fetchall()
        items = []
        for row in rows:
            item = json.loads(row["data_json"])
            item["has_memo"] = bool(row["has_memo"])
            items.append(item)
        return {"items": items, "total": total}

    def candidate(self, login: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            candidate_row = connection.execute(
                "SELECT data_json, has_memo FROM candidates WHERE gh_login = ?", (login,)
            ).fetchone()
            if candidate_row is None:
                return None
            trajectory_rows = connection.execute(
                "SELECT month, score FROM trajectories WHERE gh_login = ? ORDER BY month ASC",
                (login,),
            ).fetchall()
            memo_row = connection.execute(
                "SELECT data_json FROM memos WHERE gh_login = ?", (login,)
            ).fetchone()
            count_rows = connection.execute(
                "SELECT event_type, count(*) AS count FROM events "
                "WHERE gh_login = ? GROUP BY event_type ORDER BY event_type",
                (login,),
            ).fetchall()
        candidate = json.loads(candidate_row["data_json"])
        candidate["has_memo"] = bool(candidate_row["has_memo"])
        memo = json.loads(memo_row["data_json"]) if memo_row else None
        return {
            "candidate": candidate,
            "trajectory": [
                {"month": row["month"], "score": row["score"]}
                for row in trajectory_rows
            ],
            "three_axis": memo["three_axis"] if memo else None,
            "memo_available": memo is not None,
            "evidence_counts_by_type": {
                row["event_type"]: row["count"] for row in count_rows
            },
        }

    def evidence(
        self,
        login: str,
        *,
        event_type: str | None,
        after: date | None,
        before: date | None,
        limit: int,
    ) -> dict[str, Any] | None:
        predicates = ["gh_login = ?"]
        parameters: list[Any] = [login]
        if event_type is not None:
            predicates.append("event_type = ?")
            parameters.append(event_type)
        if after is not None:
            predicates.append("date(ts) >= ?")
            parameters.append(after.isoformat())
        if before is not None:
            predicates.append("date(ts) <= ?")
            parameters.append(before.isoformat())
        where = " AND ".join(predicates)
        with self._connection() as connection:
            exists = connection.execute(
                "SELECT 1 FROM candidates WHERE gh_login = ?", (login,)
            ).fetchone()
            if exists is None:
                return None
            total = connection.execute(
                f"SELECT count(*) FROM events WHERE {where}", parameters
            ).fetchone()[0]
            rows = connection.execute(
                f"SELECT data_json FROM events WHERE {where} "
                "ORDER BY ts DESC, evidence_id ASC LIMIT ?",
                [*parameters, limit],
            ).fetchall()
        return {
            "items": [json.loads(row["data_json"]) for row in rows],
            "total": total,
        }

    def memo(self, login: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT data_json FROM memos WHERE gh_login = ?", (login,)
            ).fetchone()
        return json.loads(row["data_json"]) if row else None

    def claim(self, claim_id: str) -> dict[str, Any] | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT data_json FROM claims WHERE claim_key = ?", (claim_id,)
            ).fetchone()
            if row is None:
                return None
            claim = json.loads(row["data_json"])
            resolved: list[dict[str, Any]] = []
            for evidence_ref in claim["evidence_refs"]:
                event = connection.execute(
                    "SELECT data_json FROM events WHERE evidence_id = ?", (evidence_ref,)
                ).fetchone()
                resolved.append(
                    json.loads(event["data_json"])
                    if event
                    else {"url": evidence_ref}
                )
        return {"claim": claim, "resolved_evidence": resolved}

    def search(
        self,
        query: str,
        *,
        types: Sequence[str] | None,
        limit: int,
    ) -> dict[str, Any]:
        tokens = re.findall(r"\w+", query, flags=re.UNICODE)
        if not tokens:
            return {"groups": []}
        match_query = " AND ".join(f'"{token.replace(chr(34), chr(34) * 2)}"*' for token in tokens)
        predicates = ["docs MATCH ?"]
        parameters: list[Any] = [match_query]
        if types:
            placeholders = ", ".join("?" for _ in types)
            predicates.append(f"doc_type IN ({placeholders})")
            parameters.extend(types)
        parameters.append(limit)
        with self._connection() as connection:
            rows = connection.execute(
                f"""
                SELECT
                    doc_type,
                    doc_id,
                    title,
                    subtitle,
                    snippet(docs, -1, '<mark>', '</mark>', '…', 18) AS snippet,
                    route,
                    bm25(docs, 0.2, 0.5, 5.0, 2.0, 1.0, 0.0) AS rank
                FROM docs
                WHERE {' AND '.join(predicates)}
                ORDER BY rank ASC, doc_type ASC, doc_id ASC
                LIMIT ?
                """,
                parameters,
            ).fetchall()
        groups: OrderedDict[str, list[dict[str, Any]]] = OrderedDict()
        for row in rows:
            groups.setdefault(row["doc_type"], []).append(
                {
                    "doc_type": row["doc_type"],
                    "doc_id": row["doc_id"],
                    "title": row["title"],
                    "subtitle": row["subtitle"],
                    "snippet": row["snippet"],
                    "route": row["route"],
                    "score": -float(row["rank"]),
                }
            )
        return {
            "groups": [
                {"type": doc_type, "hits": hits} for doc_type, hits in groups.items()
            ]
        }


def normalize_search_types(raw_types: list[str] | None) -> list[str] | None:
    if not raw_types:
        return None
    values = [part for value in raw_types for part in value.split(",") if part]
    invalid = sorted(set(values).difference(DOC_TYPES))
    if invalid:
        raise ValueError(f"unsupported search types: {', '.join(invalid)}")
    return list(dict.fromkeys(values))
