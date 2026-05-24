"""Disambiguation item — low-confidence fields from ContinuityAgent/DataAgent needing human review."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class DisambiguationItem(Base):
    __tablename__ = "disambiguation_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)
    chapter_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("chapters.id"), nullable=True)

    field_name: Mapped[str] = mapped_column(String(100), nullable=False)
    current_value: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    alternatives: Mapped[str] = mapped_column(Text, default="[]")  # JSON array
    suggestion: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | accepted | rejected
    resolved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
