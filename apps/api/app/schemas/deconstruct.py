"""Pydantic schemas for full-book deconstruction API."""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any


# --- Request Schemas ---


class FullBookDeconstructRequest(BaseModel):
    """Request to start a full-book deconstruction run."""

    corpus_id: str = Field(min_length=1, description="Reference corpus ID")
    target_genre: str = Field(default="", description="Target genre for the new book")
    preferences: dict = Field(default_factory=dict, description="User preferences")
    use_embedding: bool = Field(default=False, description="Whether to use embedding search (optional)")


# --- Response Schemas ---


class DeconstructionRunResponse(BaseModel):
    """Basic run info returned when starting a deconstruction."""

    run_id: str
    status: str  # pending, running, done, failed
    phase: str = ""
    progress: int = 0
    created_at: str = ""
    updated_at: str = ""
    finished_at: str | None = None


class ReferenceInsightResponse(BaseModel):
    """A single reference insight with evidence."""

    id: str
    insight_type: str
    summary: str
    evidence_chunk_ids: list[str]
    transferable_pattern: str | None = None
    forbidden_copying_risk: str | None = None


class FullBookReport(BaseModel):
    """The full-book deconstruction report."""

    macro_structure: dict[str, Any] = Field(default_factory=dict)
    volume_patterns: list[dict[str, Any]] = Field(default_factory=list)
    character_patterns: list[dict[str, Any]] = Field(default_factory=list)
    world_patterns: list[dict[str, Any]] = Field(default_factory=list)
    power_progression: dict[str, Any] = Field(default_factory=dict)
    pacing_curve: dict[str, Any] = Field(default_factory=dict)
    foreshadowing_patterns: list[dict[str, Any]] = Field(default_factory=list)
    villain_patterns: list[dict[str, Any]] = Field(default_factory=list)
    reader_reward_patterns: list[dict[str, Any]] = Field(default_factory=list)


class DeconstructionRunDetail(BaseModel):
    """Full run detail including report and insights."""

    run_id: str
    corpus_id: str
    status: str
    phase: str = ""
    progress: int = 0
    target_genre: str = ""
    preferences: dict = Field(default_factory=dict)
    fullbook_report: dict[str, Any] = Field(default_factory=dict)
    transferable_patterns: list[str] = Field(default_factory=list)
    originality_constraints: list[str] = Field(default_factory=list)
    red_flags: list[str] = Field(default_factory=list)
    insights: list[ReferenceInsightResponse] = Field(default_factory=list)
    error_message: str | None = None
    created_at: str = ""
    updated_at: str = ""
    finished_at: str | None = None
