"""DeconstructionRun — tracks full-book deconstruction async runs."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, ForeignKey, JSON, DateTime, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class DeconstructionRun(Base):
    """Tracks the progress and results of a full-book deconstruction run."""

    __tablename__ = "deconstruction_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    corpus_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reference_corpora.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending, running, done, failed
    phase: Mapped[str] = mapped_column(String(32), default="")  # current step label
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    target_genre: Mapped[str | None] = mapped_column(String(50))
    preferences: Mapped[dict] = mapped_column(JSON, default=dict)
    fullbook_report: Mapped[dict] = mapped_column(JSON, default=dict)
    transferable_patterns: Mapped[list] = mapped_column(JSON, default=list)
    originality_constraints: Mapped[list] = mapped_column(JSON, default=list)
    red_flags: Mapped[list] = mapped_column(JSON, default=list)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
