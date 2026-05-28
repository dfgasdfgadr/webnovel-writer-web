"""Reader pulse results — reader engagement simulation per chapter."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ReaderPulseResult(Base):
    __tablename__ = "reader_pulse_results"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    chapter_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chapters.id"), nullable=False, index=True
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id"), nullable=False, index=True
    )

    drop_risk: Mapped[int] = mapped_column(Integer, default=50)
    hook_quality: Mapped[int] = mapped_column(Integer, default=50)
    pacing_score: Mapped[int] = mapped_column(Integer, default=50)
    expectation: Mapped[str | None] = mapped_column(Text, nullable=True)
    strengths: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    weaknesses: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON array
    next_chapter_suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)
    overall_verdict: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("ix_reader_pulse_project_created", "project_id", "created_at"),
    )
