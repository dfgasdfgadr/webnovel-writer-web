"""Three-level summaries: volume → arc → chapter."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Summary(Base):
    __tablename__ = "summaries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), ForeignKey("projects.id"), nullable=False, index=True)

    level: Mapped[str] = mapped_column(String(20), nullable=False, default="chapter")  # volume | arc | chapter
    scope_label: Mapped[str] = mapped_column(String(200), nullable=False)  # e.g. "第1卷", "觉醒篇", "第3章"
    parent_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("summaries.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(300), default="")
    content: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
