"""Review metrics — 7-dimension scores from ReviewAgent."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class ReviewMetric(Base):
    __tablename__ = "review_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    chapter_id: Mapped[str] = mapped_column(String(36), ForeignKey("chapters.id"), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)

    consistency_score: Mapped[int] = mapped_column(Integer, default=0)
    timeline_score: Mapped[int] = mapped_column(Integer, default=0)
    coherence_score: Mapped[int] = mapped_column(Integer, default=0)
    ooc_score: Mapped[int] = mapped_column(Integer, default=0)
    logic_score: Mapped[int] = mapped_column(Integer, default=0)
    foreshadowing_score: Mapped[int] = mapped_column(Integer, default=0)
    ai_flavor_score: Mapped[int] = mapped_column(Integer, default=0)

    summary: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
