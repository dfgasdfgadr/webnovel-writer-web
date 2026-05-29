"""ReferenceCorpus model — top-level container for imported reference books."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReferenceCorpus(Base):
    __tablename__ = "reference_corpora"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    author: Mapped[str | None] = mapped_column(String(100))
    description: Mapped[str | None] = mapped_column(Text)
    source_type: Mapped[str] = mapped_column(String(20), default="paste")  # paste | upload
    source_filename: Mapped[str | None] = mapped_column(String(255))
    total_chapters: Mapped[int] = mapped_column(Integer, default=0)
    total_chunks: Mapped[int] = mapped_column(Integer, default=0)
    total_chars: Mapped[int] = mapped_column(Integer, default=0)
    index_status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | splitting | ready | error
    index_error: Mapped[str | None] = mapped_column(Text)
    owner_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    owner: Mapped["User"] = relationship("User", back_populates="reference_corpora")
    chapters: Mapped[list["ReferenceChapter"]] = relationship(
        "ReferenceChapter",
        back_populates="corpus",
        cascade="all, delete-orphan",
        order_by="ReferenceChapter.sequence",
    )
    chunks: Mapped[list["ReferenceChunk"]] = relationship(
        "ReferenceChunk",
        back_populates="corpus",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<ReferenceCorpus {self.title}>"
