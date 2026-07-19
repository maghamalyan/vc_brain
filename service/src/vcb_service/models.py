"""Public API models for the frozen v1 read contract."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from vcb_service.claim_schema import Claim, Memo, ThreeAxis


Source = Literal["outbound_detector", "inbound_application"]
CandidateStatus = Literal["candidate", "screened", "memo_ready"]
DocType = Literal[
    "founder", "company", "claim", "evidence", "memo_section", "thesis_term"
]
RecognitionKind = Literal["yc_batch", "seed_round", "press"]


class ApiModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Recognition(ApiModel):
    month: str = Field(pattern=r"^\d{4}-(0[1-9]|1[0-2])$")
    kind: RecognitionKind
    label: str


class ScoreComponent(ApiModel):
    key: str
    label: str
    contribution: float = Field(ge=0.0, le=1.0)


class Candidate(ApiModel):
    gh_login: str
    founder_name: str | None
    company: str | None
    source: Source
    current_score: float = Field(ge=0.0, le=1.0)
    score_percentile: float
    momentum_3mo: float
    first_detection_month: date | None
    status: CandidateStatus
    has_memo: bool


class TrajectoryPoint(ApiModel):
    month: date
    score: float = Field(ge=0.0, le=1.0)


class CandidateListItem(Candidate):
    recognition: Recognition | None
    lead_time_months: int | None
    trajectory: list[TrajectoryPoint]


class CandidatePage(ApiModel):
    items: list[CandidateListItem]
    total: int


class CandidateDetail(ApiModel):
    candidate: Candidate
    trajectory: list[TrajectoryPoint]
    recognition: Recognition | None
    score_components: list[ScoreComponent]
    three_axis: ThreeAxis | None
    memo_available: bool
    evidence_counts_by_type: dict[str, int]


class EvidenceEvent(ApiModel):
    evidence_id: str
    gh_login: str
    ts: datetime
    event_type: str
    repo_name: str
    detail: str
    url: str


class EvidencePage(ApiModel):
    items: list[EvidenceEvent]
    total: int


class HealthCounts(ApiModel):
    candidates: int
    events: int
    claims: int


class HealthResponse(ApiModel):
    status: Literal["ok"]
    index_built_at: datetime
    counts: HealthCounts


class Thesis(ApiModel):
    sectors: list[str]
    stages: list[str]
    geographies: list[str]
    check_size_usd: list[int] = Field(min_length=2, max_length=2)
    risk_appetite: str
    notes: str


class UrlEvidence(ApiModel):
    url: str


class ClaimResponse(ApiModel):
    claim: Claim
    resolved_evidence: list[EvidenceEvent | UrlEvidence]


class SearchHit(ApiModel):
    doc_type: DocType
    doc_id: str
    title: str
    subtitle: str
    snippet: str
    route: str
    score: float


class SearchGroup(ApiModel):
    type: DocType
    hits: list[SearchHit]


class SearchResponse(ApiModel):
    groups: list[SearchGroup]


MemoResponse = Memo
JsonObject = dict[str, Any]
