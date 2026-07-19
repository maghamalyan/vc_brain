"""Public and durable contracts for live deep-dive runs."""

from datetime import datetime
from typing import Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from vcb_service.claim_schema import Axis, Claim


Dimension = Literal["founder", "market", "idea_vs_market"]
StepKind = Literal[
    "plan", "fetch", "sql", "evidence", "reason", "claim", "gap", "done", "error"
]
Outcome = Literal["OK", "INSUFFICIENT_EVIDENCE", "ERROR"]


class AgentModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DeepDiveRequest(AgentModel):
    entity_type: Literal["founder"] = "founder"
    entity_id: str = Field(min_length=1)
    dimensions: list[Dimension] = Field(
        default_factory=lambda: ["founder", "market", "idea_vs_market"], min_length=1
    )
    mode: Literal["live", "replay"] | None = None

    @model_validator(mode="after")
    def unique_dimensions(self) -> Self:
        if len(set(self.dimensions)) != len(self.dimensions):
            raise ValueError("dimensions must be unique")
        return self


class DeepDiveAccepted(AgentModel):
    run_id: str


class RunStep(AgentModel):
    seq: int = Field(ge=1)
    kind: StepKind
    label: str = Field(min_length=1)
    detail: str
    ts: datetime
    payload: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_plan_payload(self) -> Self:
        if self.kind == "plan" and (
            self.payload is None or not isinstance(self.payload.get("dimensions"), list)
        ):
            raise ValueError("plan steps require a dimensions payload")
        return self


class LiveEvidence(AgentModel):
    evidence_id: str
    gh_login: str
    ts: datetime
    event_type: str
    repo_name: str = ""
    detail: str
    url: str


class FinalizeRun(AgentModel):
    summary: str = Field(min_length=1)
    outcome: Outcome


class DeepDiveRun(AgentModel):
    run_id: str
    entity_id: str
    provenance: Literal["live"] = "live"
    started_at: datetime
    finished_at: datetime | None
    steps: list[RunStep]
    evidence: list[LiveEvidence]
    claims: dict[str, Claim]
    dimension_notes: dict[Dimension, Axis]
    gaps: list[str]
    model: str
    token_usage: dict[str, int]


class DeepDiveRunSummary(AgentModel):
    run_id: str
    entity_id: str
    started_at: datetime
    finished_at: datetime | None
    outcome: Outcome | None
    claim_count: int = Field(ge=0)
