"""ReferenceChapter model — chapters within a reference corpus."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReferenceChapter(Base):
    __tablename__ = "reference_chapters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    corpus_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("reference_corpora.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    corpus: Mapped["ReferenceCorpus"] = relationship("ReferenceCorpus", back_populates="chapters")
    chunks: Mapped[list["ReferenceChunk"]] = relationship(
        "ReferenceChunk",
        back_populates="chapter",
        cascade="all, delete-orphan",
        order_by="ReferenceChunk.sequence",
    )

    def __repr__(self) -> str:
        return f"<ReferenceChapter {self.sequence}: {self.title}>"
