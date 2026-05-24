"""Simulation job model for MiroFish integration."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import String, DateTime, Text, Integer, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SimulationJob(Base):
    __tablename__ = "simulation_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    chapter_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    mode: Mapped[str] = mapped_column(String(32), nullable=False)  # pre_chapter, branch_explore
    sim_brief: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")  # pending/running/completed/failed
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    report_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON report
    steps_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON steps
    checkpoint_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    mirofish_available: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<SimulationJob {self.id} mode={self.mode} status={self.status}>"
