# Provenance: copied verbatim from src/vc_brain/memo/schema.py; keep in contract lockstep.
"""Validated contracts for evidence-backed investment memos."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


VerificationStatus = Literal[
    "verified", "single_source", "unverified", "not_disclosed"
]
Trend = Literal["improving", "stable", "declining"]


class ContractModel(BaseModel):
    """Base model that rejects silent contract drift."""

    model_config = ConfigDict(extra="forbid")


class MemoSection(ContractModel):
    text: str = Field(min_length=1)
    claim_ids: list[str]


class SwotSection(ContractModel):
    strengths: list[MemoSection]
    weaknesses: list[MemoSection]
    opportunities: list[MemoSection]
    risks: list[MemoSection]


class MemoSections(ContractModel):
    company_snapshot: MemoSection
    investment_hypotheses: list[MemoSection]
    swot: SwotSection
    problem_product: MemoSection
    traction_kpis: MemoSection


class Claim(ContractModel):
    text: str = Field(min_length=1)
    evidence_refs: list[str] = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    verification_status: VerificationStatus
    contradictions: list[str]


class Axis(ContractModel):
    score: float = Field(ge=1.0, le=10.0)
    trend: Trend
    claim_ids: list[str]


class ThreeAxis(ContractModel):
    founder: Axis
    market: Axis
    idea_vs_market: Axis


class Memo(ContractModel):
    company: str | None
    founder_logins: list[str] = Field(min_length=1)
    generated_at: datetime
    sections: MemoSections
    claims: dict[str, Claim]
    gaps: list[str]
    three_axis: ThreeAxis

    @model_validator(mode="after")
    def validate_claim_links(self) -> Memo:
        referenced = set(self._section_claim_ids())
        referenced.update(self.three_axis.founder.claim_ids)
        referenced.update(self.three_axis.market.claim_ids)
        referenced.update(self.three_axis.idea_vs_market.claim_ids)
        missing = referenced.difference(self.claims)
        if missing:
            missing_text = ", ".join(sorted(missing))
            raise ValueError(f"unknown claim_ids referenced: {missing_text}")
        return self

    def _section_claim_ids(self) -> list[str]:
        ids: list[str] = []
        sections = self.sections
        ids.extend(sections.company_snapshot.claim_ids)
        ids.extend(sections.problem_product.claim_ids)
        ids.extend(sections.traction_kpis.claim_ids)
        for hypothesis in sections.investment_hypotheses:
            ids.extend(hypothesis.claim_ids)
        for group in (
            sections.swot.strengths,
            sections.swot.weaknesses,
            sections.swot.opportunities,
            sections.swot.risks,
        ):
            for item in group:
                ids.extend(item.claim_ids)
        return ids
