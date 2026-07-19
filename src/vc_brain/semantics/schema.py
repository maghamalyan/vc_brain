"""Strict response contract for quarterly semantic annotations."""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BuildingCategory(StrEnum):
    DEVELOPER_TOOL = "developer_tool"
    APPLICATION = "application"
    INFRASTRUCTURE = "infrastructure"
    DATA_AI = "data_ai"
    SECURITY = "security"
    FINTECH = "fintech"
    HEALTH_BIO = "health_bio"
    HARDWARE = "hardware"
    RESEARCH = "research"
    CONTENT_COMMUNITY = "content_community"
    OTHER = "other"


AudienceOrientation = Literal["self", "developers", "end_users", "customers"]
CollaborationPosture = Literal["solo", "contributing", "leading", "team_forming"]
FoundingIntentLevel = Literal["none", "implicit", "explicit"]


class BuildingWhat(ContractModel):
    category: BuildingCategory | None
    description: str | None = Field(max_length=240)
    citations: list[int]

    @model_validator(mode="after")
    def validate_evidence(self) -> BuildingWhat:
        if (self.category is None) != (self.description is None):
            raise ValueError("building_what category and description must both be set")
        if self.category is not None and not self.citations:
            raise ValueError("building_what requires item citations")
        return self


class CitedAudience(ContractModel):
    value: AudienceOrientation | None
    citations: list[int]

    @model_validator(mode="after")
    def validate_evidence(self) -> CitedAudience:
        if self.value is not None and not self.citations:
            raise ValueError("audience_orientation requires item citations")
        return self


class CitedScale(ContractModel):
    value: int | None = Field(ge=0, le=3)
    citations: list[int]

    @model_validator(mode="after")
    def validate_evidence(self) -> CitedScale:
        if self.value is not None and not self.citations:
            raise ValueError("non-null scale values require item citations")
        return self


class CitedCollaboration(ContractModel):
    value: CollaborationPosture | None
    citations: list[int]

    @model_validator(mode="after")
    def validate_evidence(self) -> CitedCollaboration:
        if self.value is not None and not self.citations:
            raise ValueError("collaboration_posture requires item citations")
        return self


class StatedFoundingIntent(ContractModel):
    value: FoundingIntentLevel
    quote: str | None = Field(max_length=500)
    citations: list[int]

    @model_validator(mode="after")
    def validate_intent(self) -> StatedFoundingIntent:
        if self.value == "explicit":
            if not self.quote or not self.citations:
                raise ValueError(
                    "explicit founding intent requires quote and citations"
                )
        elif self.quote is not None:
            raise ValueError("only explicit founding intent may include a quote")
        elif self.value == "implicit" and not self.citations:
            raise ValueError("implicit founding intent requires item citations")
        return self


class SemanticAnnotation(ContractModel):
    building_what: BuildingWhat
    audience_orientation: CitedAudience
    productization_markers: CitedScale
    commercial_language: CitedScale
    collaboration_posture: CitedCollaboration
    stated_founding_intent: StatedFoundingIntent
    seriousness: CitedScale
    domain_shift: CitedScale

    def cited_item_indices(self) -> set[int]:
        result: set[int] = set()
        for field in (
            self.building_what,
            self.audience_orientation,
            self.productization_markers,
            self.commercial_language,
            self.collaboration_posture,
            self.stated_founding_intent,
            self.seriousness,
            self.domain_shift,
        ):
            result.update(field.citations)
        return result
