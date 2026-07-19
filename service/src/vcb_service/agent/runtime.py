"""Per-run Monty sandbox, evidence store, and audited external functions."""

import asyncio
import hashlib
import json
import sqlite3
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pydantic_monty as pm

from vcb_service.claim_schema import Axis, Claim
from vcb_service.agent.middleware import (
    Decision,
    RuntimeLimits,
    RuntimePolicy,
    SandboxToolError,
    ToolCall,
    ValidationFinding,
    compose,
    policy_middleware,
    provenance_middleware,
)
from vcb_service.agent.models import DeepDiveRun, LiveEvidence, RunStep
from vcb_service.agent.providers import DataProvider
from vcb_service.agent.settings import AgentSettings


def utc_now() -> datetime:
    return datetime.now(UTC)


class AgentRuntime:
    """Owns all mutable state for exactly one deep-dive run."""

    def __init__(
        self,
        *,
        run_id: str,
        entity_id: str,
        dimensions: list[str],
        settings: AgentSettings,
        provider: DataProvider,
        queue: asyncio.Queue[RunStep | None] | None = None,
        loop: asyncio.AbstractEventLoop | None = None,
    ) -> None:
        self.run_id = run_id
        self.entity_id = entity_id
        self.dimensions = dimensions
        self.settings = settings
        self.provider = provider
        self.queue = queue
        self.loop = loop
        self.started_at = utc_now()
        self.finished_at: datetime | None = None
        self.steps: list[RunStep] = []
        self.audit_events: list[RunStep] = []
        self.evidence: dict[str, LiveEvidence] = {}
        self.claims: dict[str, Claim] = {}
        self.dimension_notes: dict[str, Axis] = {}
        self.gaps: list[str] = []
        self.token_usage: dict[str, int] = {}
        self._counts = {"tools": 0, "github": 0}
        limits = RuntimeLimits(
            max_tool_calls=settings.max_tool_calls,
            max_gh_requests=settings.max_gh_requests,
            max_sql_chars=settings.max_sql_chars,
            max_output_chars=settings.max_output_chars,
        )
        self._policy = RuntimePolicy(limits)
        stack = [
            policy_middleware(self._policy, self._counts, self._audit_call),
            provenance_middleware(settings.max_output_chars),
        ]
        raw_functions: dict[str, Callable[..., Any]] = {
            "sql": self._sql,
            "gh_profile": provider.gh_profile,
            "gh_repos": provider.gh_repos,
            "gh_events": provider.gh_events,
            "hn_search": provider.hn_search,
            "web_search": provider.web_search,
            "add_evidence": self._add_evidence,
            "draft_claim": self._draft_claim,
            "note_gap": self._note_gap,
            "set_dimension_note": self._set_dimension_note,
        }
        self.functions = {
            name: compose(function, name, stack) for name, function in raw_functions.items()
        }

    @property
    def function_names(self) -> list[str]:
        return list(self.functions)

    def emit(
        self,
        kind: str,
        label: str,
        detail: str,
        payload: dict[str, Any] | None = None,
    ) -> RunStep:
        step = RunStep(
            seq=len(self.steps) + 1,
            kind=kind,
            label=label,
            detail=detail,
            ts=utc_now(),
            payload=payload,
        )
        self.steps.append(step)
        self.audit_events.append(step)
        if self.queue is not None and self.loop is not None:
            self.loop.call_soon_threadsafe(self.queue.put_nowait, step)
        return step

    def finish_stream(self) -> None:
        if self.queue is not None and self.loop is not None:
            self.loop.call_soon_threadsafe(self.queue.put_nowait, None)

    def run_python(self, code: str) -> str:
        self.emit("reason", "Execute sandbox analysis", code[:2_000])
        try:
            monty = pm.Monty(code, inputs=[])
        except pm.MontySyntaxError as exc:
            return f"PYTHON SYNTAX ERROR: {exc}"
        collector = pm.CollectString()
        try:
            value = monty.run(
                external_functions=self.functions,
                print_callback=collector,
                limits=pm.ResourceLimits(
                    max_allocations=100_000,
                    max_duration_secs=10.0,
                    max_memory=32 * 1024 * 1024,
                    gc_interval=1_000,
                    max_recursion_depth=100,
                ),
            )
        except (pm.MontyRuntimeError, pm.MontyTypingError, pm.MontyError) as exc:
            printed = collector.output.rstrip()
            return f"{printed + chr(10) if printed else ''}PYTHON ERROR: {exc}"
        parts: list[str] = []
        if printed := collector.output.rstrip():
            parts.append(printed)
        if value is not None:
            parts.append(f"=> {value!r}")
        output = "\n".join(parts) if parts else "(no output)"
        return (
            output
            if len(output) <= self.settings.max_output_chars
            else f"{output[:self.settings.max_output_chars]}... [truncated by runtime policy]"
        )

    def snapshot(self) -> DeepDiveRun:
        return DeepDiveRun.model_validate(
            {
                "run_id": self.run_id,
                "entity_id": self.entity_id,
                "provenance": "live",
                "started_at": self.started_at,
                "finished_at": self.finished_at,
                "steps": self.steps,
                "evidence": list(self.evidence.values()),
                "claims": self.claims,
                "dimension_notes": self.dimension_notes,
                "gaps": self.gaps,
                "model": self.settings.openrouter_model,
                "token_usage": self.token_usage,
            }
        )

    def persist(self) -> Path:
        document = self.snapshot()
        path = self.settings.run_dir / f"{self.run_id}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(document.model_dump(mode="json"), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
        return path

    def _connection(self) -> sqlite3.Connection:
        if not self.settings.index_path.is_file():
            raise FileNotFoundError(f"index file not found: {self.settings.index_path}")
        connection = sqlite3.connect(
            f"{self.settings.index_path.as_uri()}?mode=ro", uri=True
        )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA query_only=ON")
        return connection

    def _sql(self, query: str) -> dict[str, Any]:
        with self._connection() as connection:
            cursor = connection.execute(query)
            rows = [dict(row) for row in cursor.fetchall()]
        return {"rows": rows, "row_count": len(rows)}

    def _add_evidence(
        self,
        event_type: str,
        ts: str,
        detail: str,
        url: str,
        repo_name: str | None = None,
    ) -> dict[str, Any]:
        digest = hashlib.sha256(
            json.dumps(
                [self.entity_id, event_type, ts, detail, url, repo_name or ""],
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()[:20]
        event = LiveEvidence.model_validate(
            {
                "evidence_id": f"live-{digest}",
                "gh_login": self.entity_id,
                "ts": ts,
                "event_type": event_type,
                "repo_name": repo_name or "",
                "detail": detail,
                "url": url,
            }
        )
        self.evidence[event.evidence_id] = event
        return event.model_dump(mode="json")

    def _draft_claim(
        self,
        text: str,
        evidence_refs: list[str],
        confidence: float,
        verification_status: str,
        contradictions: list[str] | None = None,
    ) -> dict[str, Any]:
        unknown = [ref for ref in evidence_refs if not self._evidence_exists(ref)]
        if unknown:
            raise SandboxToolError(
                "UNKNOWN_EVIDENCE_REF",
                "unknown evidence_refs rejected: " + ", ".join(sorted(set(unknown)))
            )
        claim = Claim.model_validate(
            {
                "text": text,
                "evidence_refs": evidence_refs,
                "confidence": confidence,
                "verification_status": verification_status,
                "contradictions": contradictions or [],
            }
        )
        claim_id = "live-claim-" + hashlib.sha256(
            json.dumps(claim.model_dump(mode="json"), sort_keys=True).encode("utf-8")
        ).hexdigest()[:16]
        self.claims[claim_id] = claim
        return {"claim_id": claim_id, "claim": claim.model_dump(mode="json")}

    def _evidence_exists(self, evidence_ref: str) -> bool:
        if evidence_ref in self.evidence:
            return True
        with self._connection() as connection:
            row = connection.execute(
                "SELECT 1 FROM events WHERE evidence_id = ? "
                "UNION ALL SELECT 1 FROM unresolved_evidence_refs WHERE evidence_ref = ? LIMIT 1",
                (evidence_ref, evidence_ref),
            ).fetchone()
        return row is not None

    def _note_gap(self, text: str) -> dict[str, Any]:
        normalized = text.strip()
        if not normalized:
            raise SandboxToolError("EMPTY_GAP", "gap text must not be empty")
        if normalized not in self.gaps:
            self.gaps.append(normalized)
        return {"gap": normalized}

    def _set_dimension_note(
        self,
        dimension: str,
        score: float,
        trend: str,
        claim_ids: list[str],
    ) -> dict[str, Any]:
        if dimension not in self.dimensions:
            raise SandboxToolError(
                "DIMENSION_NOT_REQUESTED", f"dimension not requested: {dimension}"
            )
        unknown = set(claim_ids).difference(self.claims)
        if unknown:
            raise SandboxToolError(
                "UNKNOWN_CLAIM_ID",
                "unknown claim_ids: " + ", ".join(sorted(unknown)),
            )
        note = Axis.model_validate(
            {"score": score, "trend": trend, "claim_ids": claim_ids}
        )
        self.dimension_notes[dimension] = note
        return {"dimension": dimension, "note": note.model_dump(mode="json")}

    def _audit_call(
        self,
        call: ToolCall,
        decision: Decision,
        findings: tuple[ValidationFinding, ...],
        result: Any,
    ) -> None:
        kind_by_tool = {
            "sql": "sql",
            "gh_profile": "fetch",
            "gh_repos": "fetch",
            "gh_events": "fetch",
            "hn_search": "fetch",
            "web_search": "fetch",
            "add_evidence": "evidence",
            "draft_claim": "claim",
            "note_gap": "gap",
            "set_dimension_note": "reason",
        }
        payload: dict[str, Any] | None = None
        if call.name == "draft_claim" and isinstance(result, dict):
            payload = result.get("claim") or result.get("error")
        elif call.name == "add_evidence" and isinstance(result, dict):
            payload = {key: value for key, value in result.items() if key != "__provenance__"}
        denied = decision is Decision.DENY or (isinstance(result, dict) and "error" in result)
        detail = (
            "; ".join(f.message for f in findings)
            if findings
            else f"{call.name} completed"
        )
        if denied and isinstance(result, dict):
            detail = result.get("error", {}).get("message", detail)
        self.emit(
            kind_by_tool[call.name],
            f"{'Blocked' if denied else 'Audited'} {call.name}",
            detail,
            payload,
        )
