"""ReferenceChunk model — searchable text chunks within a reference chapter."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReferenceChunk(Base):
    __tablename__ = "reference_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    corpus_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reference_corpora.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chapter_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reference_chapters.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    tokens_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    corpus: Mapped["ReferenceCorpus"] = relationship("ReferenceCorpus", back_populates="chunks")
    chapter: Mapped["ReferenceChapter"] = relationship("ReferenceChapter", back_populates="chunks")

    def __repr__(self) -> str:
        return f"<ReferenceChunk {self.sequence} ({self.char_count} chars)>"
