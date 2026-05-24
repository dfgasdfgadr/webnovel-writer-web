"""Story System contract tree and CHAPTER_COMMIT models."""

import uuid
from datetime import datetime

from sqlalchemy import String, ForeignKey, JSON, DateTime, Integer, Text, Float, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ChapterCommit(Base):
    """The authoritative fact record for one accepted chapter."""
    __tablename__ = "chapter_commits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chapter_id: Mapped[str] = mapped_column(String(36), ForeignKey("chapters.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    content_json: Mapped[dict] = mapped_column(JSON, default=dict)
    state_changes: Mapped[dict] = mapped_column(JSON, default=dict)  # character states, timeline events
    new_entities: Mapped[list] = mapped_column(JSON, default=list)
    new_relationships: Mapped[list] = mapped_column(JSON, default=list)
    foreshadowing_planted: Mapped[list] = mapped_column(JSON, default=list)
    foreshadowing_resolved: Mapped[list] = mapped_column(JSON, default=list)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ReviewIssue(Base):
    __tablename__ = "review_issues"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chapter_id: Mapped[str] = mapped_column(String(36), ForeignKey("chapters.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), default="minor")  # blocking, major, minor
    category: Mapped[str] = mapped_column(String(32), nullable=False)   # consistency, timeline, coherence, ooc, logic, foreshadowing, ai_flavor
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=False)  # direct quote from text
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_fixed: Mapped[bool] = mapped_column(default=False)
    fixed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
