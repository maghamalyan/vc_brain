"""Build the immutable SQLite read model consumed by the API."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import tempfile
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import polars as pl

from vcb_service.claim_schema import Memo


DOC_TYPES = (
    "founder",
    "company",
    "claim",
    "evidence",
    "memo_section",
    "thesis_term",
)


class IndexBuildError(RuntimeError):
    """Raised when the upstream files cannot produce a valid index."""


class VerificationError(IndexBuildError):
    """Raised when an index contains dangling claim evidence references."""

    def __init__(self, unresolved: list[tuple[str, str]]) -> None:
        self.unresolved = unresolved
        detail = ", ".join(f"{claim_key} -> {ref}" for claim_key, ref in unresolved)
        super().__init__(f"unresolved memo evidence references: {detail}")


@dataclass(frozen=True)
class BuildResult:
    path: Path
    built_at: str
    doc_counts: dict[str, int]
    unresolved: list[tuple[str, str]]


def _first_existing(paths: Iterable[Path], *, label: str) -> Path:
    for path in paths:
        if path.exists():
            return path
    checked = ", ".join(str(path) for path in paths)
    raise IndexBuildError(f"could not find {label}; checked: {checked}")


def _data_file(data_dir: Path, stem: str, family: str) -> Path:
    roots = [data_dir]
    if family:
        roots.append(data_dir / family)
        roots.append(data_dir.parent / family)
    candidates = [root / f"{stem}.parquet" for root in roots]
    candidates.extend(root / f"{stem}.json" for root in roots)
    return _first_existing(candidates, label=stem)


def _memos_dir(data_dir: Path) -> Path:
    candidates = [data_dir / "memos"]
    if data_dir.name == "memos":
        candidates.append(data_dir)
    candidates.append(data_dir.parent / "memos")
    return _first_existing(candidates, label="memos directory")


def _profiles_file(data_dir: Path) -> Path | None:
    candidates = [data_dir / "profiles.json", data_dir.parent / "profiles.json"]
    return next((path for path in candidates if path.is_file()), None)


def _json_ready(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    return value


def _load_rows(path: Path) -> list[dict[str, Any]]:
    if path.suffix == ".parquet":
        rows = pl.read_parquet(path).to_dicts()
    else:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, list):
            raise IndexBuildError(f"expected a JSON array in {path}")
        rows = value
    return [_json_ready(row) for row in rows]


def _load_json_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise IndexBuildError(f"expected a JSON object in {path}")
    return value


def _dump(value: Any) -> str:
    return json.dumps(_json_ready(value), ensure_ascii=False, separators=(",", ":"))


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return slug or "item"


def _section_documents(value: Any, path: tuple[str, ...] = ()) -> Iterable[tuple[str, str]]:
    if isinstance(value, dict):
        text = value.get("text")
        if isinstance(text, str) and text:
            yield (" / ".join(part.replace("_", " ").title() for part in path), text)
        for key, item in value.items():
            if key not in {"text", "claim_ids"}:
                yield from _section_documents(item, (*path, key))
    elif isinstance(value, list):
        for index, item in enumerate(value, start=1):
            yield from _section_documents(item, (*path, str(index)))


def _create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA journal_mode=DELETE;
        PRAGMA synchronous=FULL;

        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE thesis (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            data_json TEXT NOT NULL
        );
        CREATE TABLE candidates (
            gh_login TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            status TEXT NOT NULL,
            current_score REAL NOT NULL,
            momentum_3mo REAL NOT NULL,
            has_memo INTEGER NOT NULL CHECK (has_memo IN (0, 1)),
            data_json TEXT NOT NULL
        );
        CREATE TABLE trajectories (
            gh_login TEXT NOT NULL,
            month TEXT NOT NULL,
            score REAL NOT NULL,
            data_json TEXT NOT NULL,
            PRIMARY KEY (gh_login, month)
        );
        CREATE TABLE events (
            evidence_id TEXT PRIMARY KEY,
            gh_login TEXT NOT NULL,
            ts TEXT NOT NULL,
            event_type TEXT NOT NULL,
            data_json TEXT NOT NULL
        );
        CREATE TABLE memos (
            gh_login TEXT PRIMARY KEY,
            company TEXT,
            data_json TEXT NOT NULL
        );
        CREATE TABLE claims (
            claim_key TEXT PRIMARY KEY,
            claim_id TEXT NOT NULL,
            gh_login TEXT NOT NULL,
            data_json TEXT NOT NULL
        );
        CREATE TABLE unresolved_evidence_refs (
            claim_key TEXT NOT NULL,
            evidence_ref TEXT NOT NULL,
            PRIMARY KEY (claim_key, evidence_ref)
        );

        CREATE INDEX candidates_source_status_idx
            ON candidates(source, status);
        CREATE INDEX candidates_score_idx
            ON candidates(current_score DESC);
        CREATE INDEX candidates_momentum_idx
            ON candidates(momentum_3mo DESC);
        CREATE INDEX trajectories_login_month_idx
            ON trajectories(gh_login, month);
        CREATE INDEX events_login_ts_idx
            ON events(gh_login, ts);
        CREATE INDEX events_login_type_ts_idx
            ON events(gh_login, event_type, ts);
        CREATE INDEX claims_id_idx
            ON claims(claim_id);

        CREATE VIRTUAL TABLE docs USING fts5(
            doc_type,
            doc_id,
            title,
            subtitle,
            body,
            route,
            tokenize = 'unicode61 remove_diacritics 2',
            prefix = '2 3 4'
        );
        """
    )


def _insert_doc(
    connection: sqlite3.Connection,
    doc_type: str,
    doc_id: str,
    title: str,
    subtitle: str,
    body: str,
    route: str,
) -> None:
    connection.execute(
        "INSERT INTO docs(doc_type, doc_id, title, subtitle, body, route) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (doc_type, doc_id, title, subtitle, body, route),
    )


def _populate(
    connection: sqlite3.Connection,
    *,
    candidates: list[dict[str, Any]],
    trajectories: list[dict[str, Any]],
    events: list[dict[str, Any]],
    memos: list[Memo],
    profiles: dict[str, Any],
    thesis: dict[str, Any],
    built_at: str,
) -> None:
    memo_logins = {login for memo in memos for login in memo.founder_logins}
    connection.execute("INSERT INTO metadata VALUES ('index_built_at', ?)", (built_at,))
    connection.execute("INSERT INTO thesis VALUES (1, ?)", (_dump(thesis),))

    for candidate in candidates:
        login = str(candidate["gh_login"])
        has_memo = login in memo_logins
        connection.execute(
            "INSERT INTO candidates VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                login,
                candidate["source"],
                candidate["status"],
                candidate["current_score"],
                candidate["momentum_3mo"],
                int(has_memo),
                _dump(candidate),
            ),
        )
        profile = profiles.get(login, {})
        profile_text = " ".join(f"{key}: {value}" for key, value in profile.items())
        route = f"/candidate/{login}"
        founder_name = candidate.get("founder_name") or login
        company = candidate.get("company") or ""
        _insert_doc(
            connection,
            "founder",
            login,
            founder_name,
            company,
            f"{login} {profile_text} {candidate['source']} {candidate['status']}",
            route,
        )
        if company:
            _insert_doc(
                connection,
                "company",
                _slug(company),
                company,
                founder_name,
                f"{profile_text} founder: {founder_name} github: {login}",
                route,
            )

    for point in trajectories:
        connection.execute(
            "INSERT INTO trajectories VALUES (?, ?, ?, ?)",
            (point["gh_login"], point["month"], point["score"], _dump(point)),
        )

    evidence_ids: set[str] = set()
    for event in events:
        evidence_id = str(event["evidence_id"])
        evidence_ids.add(evidence_id)
        connection.execute(
            "INSERT INTO events VALUES (?, ?, ?, ?, ?)",
            (
                evidence_id,
                event["gh_login"],
                event["ts"],
                event["event_type"],
                _dump(event),
            ),
        )
        _insert_doc(
            connection,
            "evidence",
            evidence_id,
            str(event["event_type"]).replace("_", " ").title(),
            str(event.get("repo_name", "")),
            str(event["detail"]),
            f"/candidate/{event['gh_login']}#evidence-{evidence_id}",
        )

    claim_occurrences = Counter(claim_id for memo in memos for claim_id in memo.claims)
    processed_claims: set[tuple[str, str]] = set()
    for memo in memos:
        memo_data = memo.model_dump(mode="json")
        primary_login = memo.founder_logins[0]
        for login in memo.founder_logins:
            connection.execute(
                "INSERT INTO memos VALUES (?, ?, ?)",
                (login, memo.company, _dump(memo_data)),
            )

        for claim_id, claim in memo.claims.items():
            identity = (primary_login, claim_id)
            if identity in processed_claims:
                continue
            processed_claims.add(identity)
            claim_key = (
                f"{primary_login}:{claim_id}"
                if claim_occurrences[claim_id] > 1
                else claim_id
            )
            claim_data = claim.model_dump(mode="json")
            connection.execute(
                "INSERT INTO claims VALUES (?, ?, ?, ?)",
                (claim_key, claim_id, primary_login, _dump(claim_data)),
            )
            for evidence_ref in claim.evidence_refs:
                if evidence_ref not in evidence_ids and not evidence_ref.startswith(
                    ("https://", "http://")
                ):
                    connection.execute(
                        "INSERT OR IGNORE INTO unresolved_evidence_refs VALUES (?, ?)",
                        (claim_key, evidence_ref),
                    )
            contradictions = " ".join(claim.contradictions)
            _insert_doc(
                connection,
                "claim",
                claim_key,
                claim.text,
                f"{memo.company or primary_login} · {claim.verification_status}",
                f"{claim.text} {contradictions}",
                f"/candidate/{primary_login}#claim-{claim_id}",
            )

        sections = memo_data["sections"]
        for number, (label, text) in enumerate(_section_documents(sections), start=1):
            doc_id = f"{primary_login}:section:{number}"
            _insert_doc(
                connection,
                "memo_section",
                doc_id,
                label,
                memo.company or primary_login,
                text,
                f"/candidate/{primary_login}#memo-section-{number}",
            )
        if memo.gaps:
            _insert_doc(
                connection,
                "memo_section",
                f"{primary_login}:gaps",
                "Gaps",
                memo.company or primary_login,
                " ".join(memo.gaps),
                f"/candidate/{primary_login}#memo-gaps",
            )

    for category, value in thesis.items():
        terms = value if isinstance(value, list) else [value]
        for number, term in enumerate(terms, start=1):
            if isinstance(term, (str, int, float)):
                text = str(term)
            else:
                text = _dump(term)
            _insert_doc(
                connection,
                "thesis_term",
                f"{category}:{number}:{_slug(text)}",
                text,
                category.replace("_", " ").title(),
                f"VC thesis {category.replace('_', ' ')}: {text}",
                f"/?thesis={category}&value={_slug(text)}",
            )


def inspect_index(path: Path) -> BuildResult:
    path = path.resolve()
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        built_at_row = connection.execute(
            "SELECT value FROM metadata WHERE key = 'index_built_at'"
        ).fetchone()
        if built_at_row is None:
            raise IndexBuildError(f"{path} has no index_built_at metadata")
        count_rows = connection.execute(
            "SELECT doc_type, count(*) FROM docs GROUP BY doc_type"
        ).fetchall()
        found_counts = dict(count_rows)
        doc_counts = {doc_type: int(found_counts.get(doc_type, 0)) for doc_type in DOC_TYPES}
        unresolved = [
            (str(row[0]), str(row[1]))
            for row in connection.execute(
                "SELECT claim_key, evidence_ref FROM unresolved_evidence_refs "
                "ORDER BY claim_key, evidence_ref"
            )
        ]
        return BuildResult(path, str(built_at_row[0]), doc_counts, unresolved)
    finally:
        connection.close()


def build_index(
    data_dir: Path,
    thesis_path: Path,
    out_path: Path,
    *,
    verify: bool = False,
) -> BuildResult:
    """Atomically build an idempotent SQLite index from an upstream data directory."""

    data_dir = data_dir.resolve()
    thesis_path = thesis_path.resolve()
    out_path = out_path.resolve()

    candidates = _load_rows(_data_file(data_dir, "candidates", "scores"))
    trajectories = _load_rows(_data_file(data_dir, "trajectories", "scores"))
    events = _load_rows(_data_file(data_dir, "events", "evidence"))
    memo_dir = _memos_dir(data_dir)
    memo_paths = sorted(memo_dir.glob("*.json"))
    memos = [Memo.model_validate_json(path.read_text(encoding="utf-8")) for path in memo_paths]
    profiles_path = _profiles_file(data_dir)
    profiles = _load_json_object(profiles_path) if profiles_path else {}
    thesis = _load_json_object(thesis_path)
    built_at = datetime.now(timezone.utc).isoformat()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        prefix=f".{out_path.name}.", suffix=".tmp", dir=out_path.parent, delete=False
    )
    temp_path = Path(handle.name)
    handle.close()
    try:
        connection = sqlite3.connect(temp_path)
        try:
            _create_schema(connection)
            _populate(
                connection,
                candidates=candidates,
                trajectories=trajectories,
                events=events,
                memos=memos,
                profiles=profiles,
                thesis=thesis,
                built_at=built_at,
            )
            connection.commit()
            connection.execute("VACUUM")
        finally:
            connection.close()
        os.replace(temp_path, out_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

    result = inspect_index(out_path)
    if verify and result.unresolved:
        raise VerificationError(result.unresolved)
    return result
