"""Full-book deconstruction run endpoints.

POST /api/v1/agents/foundry/deconstruct/fullbook  — start async run
GET  /api/v1/agents/foundry/deconstruct-runs/{run_id} — get status/result
"""

import asyncio
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session
from app.models import User, ReferenceCorpus, ReferenceChapter, ReferenceChunk
from app.models.deconstruction_run import DeconstructionRun
from app.models.reference_insight import ReferenceInsight, InsightType
from app.services.auth import get_current_user
from app.agents.llm import LLMProvider
from app.agents.fullbook_deconstruct import FullBookDeconstructionAgent

logger = logging.getLogger("novelcraft.deconstruct_runs")
router = APIRouter(prefix="/api/v1/agents/foundry", tags=["deconstruct-runs"])


# ---------------------------------------------------------------------------
# Request/Response schemas
# ---------------------------------------------------------------------------


class FullBookDeconstructRequest(BaseModel):
    corpus_id: str = Field(min_length=1)
    target_genre: str = Field(default="")
    preferences: dict = Field(default_factory=dict)
    use_embedding: bool = Field(default=False)


class DeconstructionRunResponse(BaseModel):
    run_id: str
    status: str
    phase: str = ""
    progress: int = 0
    created_at: str = ""
    updated_at: str = ""


# ---------------------------------------------------------------------------
# Background task
# ---------------------------------------------------------------------------


async def _run_deconstruction(
    run_id: str,
    corpus_id: str,
    user_id: str,
    target_genre: str,
    preferences: dict,
) -> None:
    """Background task: execute the full deconstruction pipeline.

    Uses an independent DB session since the HTTP request that spawned
    this task has already returned.
    """
    async with async_session() as db:
        try:
            # Load corpus chunks and chapters
            result = await db.execute(
                select(ReferenceChunk).where(ReferenceChunk.corpus_id == corpus_id)
            )
            chunks = result.scalars().all()
            if not chunks:
                raise ValueError("Corpus has no chunks")

            chunk_data = [
                {
                    "id": c.id,
                    "content": c.content,
                    "chapter_id": c.chapter_id,
                    "sequence": c.sequence,
                }
                for c in chunks
            ]

            result = await db.execute(
                select(ReferenceChapter)
                .where(ReferenceChapter.corpus_id == corpus_id)
                .order_by(ReferenceChapter.sequence)
            )
            chapters = result.scalars().all()
            chapter_data = [
                {
                    "id": c.id,
                    "title": c.title,
                    "sequence": c.sequence,
                    "content": c.content,
                    "chunks": [
                        {"id": ch["id"]} for ch in chunk_data if ch["chapter_id"] == c.id
                    ],
                }
                for c in chapters
            ]

            # Progress callback: update run phase/progress in DB
            async def _progress(phase: str, progress: int) -> None:
                try:
                    run = await db.get(DeconstructionRun, run_id)
                    if run:
                        run.phase = phase
                        run.progress = progress
                        run.updated_at = datetime.now(timezone.utc)
                        await db.commit()
                except Exception:
                    logger.exception("Progress update failed for run %s", run_id)

            # Run agent
            llm = await LLMProvider.for_user(user_id, db)
            agent = FullBookDeconstructionAgent(llm=llm)
            result = await agent.run(
                chunks=chunk_data,
                chapters=chapter_data,
                target_genre=target_genre,
                preferences=preferences,
                progress_callback=_progress,
            )

            if not result.success:
                raise RuntimeError(result.error or "Agent execution failed")

            data = result.data

            # Update run record
            run = await db.get(DeconstructionRun, run_id)
            if run:
                run.status = "done"
                run.phase = "done"
                run.progress = 100
                run.fullbook_report = data.get("fullbook_report", {})
                run.transferable_patterns = data.get("transferable_patterns", [])
                run.originality_constraints = data.get("originality_constraints", [])
                run.red_flags = data.get("red_flags", [])
                run.finished_at = datetime.now(timezone.utc)
                run.updated_at = datetime.now(timezone.utc)
                await db.commit()

            # Save insights
            for insight_data in data.get("insights", []):
                db.add(
                    ReferenceInsight(
                        run_id=run_id,
                        corpus_id=corpus_id,
                        insight_type=insight_data.get("insight_type", "macro_structure"),
                        summary=insight_data.get("summary", ""),
                        evidence_chunk_ids=insight_data.get("evidence_chunk_ids", []),
                        transferable_pattern=insight_data.get("transferable_pattern"),
                        forbidden_copying_risk=insight_data.get("forbidden_copying_risk"),
                    )
                )
            await db.commit()

            logger.info("Deconstruction run %s completed successfully", run_id)

        except Exception as e:
            logger.exception("Deconstruction run %s failed", run_id)
            try:
                run = await db.get(DeconstructionRun, run_id)
                if run:
                    run.status = "failed"
                    run.error_message = str(e)
                    run.finished_at = datetime.now(timezone.utc)
                    run.updated_at = datetime.now(timezone.utc)
                    await db.commit()
            except Exception:
                logger.exception("Failed to update run %s to failed state", run_id)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/deconstruct/fullbook", response_model=DeconstructionRunResponse)
async def start_fullbook_deconstruct(
    body: FullBookDeconstructRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Start an async full-book deconstruction run.

    Returns immediately with run_id; client should poll
    /deconstruct-runs/{run_id} for status.
    """
    # Validate corpus exists and belongs to user
    corpus = await db.get(ReferenceCorpus, body.corpus_id)
    if not corpus:
        raise HTTPException(status_code=404, detail="语料库不存在")
    if corpus.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问该语料库")

    # Validate corpus is indexed
    if corpus.index_status != "ready":
        raise HTTPException(
            status_code=400,
            detail=f"语料库尚未完成索引（当前状态: {corpus.index_status}）",
        )

    # Create run record
    run = DeconstructionRun(
        corpus_id=body.corpus_id,
        user_id=current_user.id,
        status="running",
        phase="starting",
        progress=0,
        target_genre=body.target_genre,
        preferences=body.preferences,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    # Spawn background task
    asyncio.create_task(
        _run_deconstruction(
            run_id=run.id,
            corpus_id=body.corpus_id,
            user_id=current_user.id,
            target_genre=body.target_genre,
            preferences=body.preferences,
        )
    )

    return DeconstructionRunResponse(
        run_id=run.id,
        status=run.status,
        phase=run.phase,
        progress=run.progress,
        created_at=run.created_at.isoformat() if run.created_at else "",
        updated_at=run.updated_at.isoformat() if run.updated_at else "",
    )


@router.get("/deconstruct-runs/{run_id}")
async def get_deconstruct_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the status and results of a deconstruction run."""
    run = await db.get(DeconstructionRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="拆解任务不存在")

    # Verify ownership
    if run.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问该拆解任务")

    # Load insights
    result = await db.execute(
        select(ReferenceInsight).where(ReferenceInsight.run_id == run_id)
    )
    insights = result.scalars().all()

    return {
        "run_id": run.id,
        "corpus_id": run.corpus_id,
        "status": run.status,
        "phase": run.phase,
        "progress": run.progress,
        "target_genre": run.target_genre or "",
        "preferences": run.preferences or {},
        "fullbook_report": run.fullbook_report or {},
        "transferable_patterns": run.transferable_patterns or [],
        "originality_constraints": run.originality_constraints or [],
        "red_flags": run.red_flags or [],
        "insights": [
            {
                "id": i.id,
                "insight_type": i.insight_type,
                "summary": i.summary,
                "evidence_chunk_ids": i.evidence_chunk_ids or [],
                "transferable_pattern": i.transferable_pattern,
                "forbidden_copying_risk": i.forbidden_copying_risk,
            }
            for i in insights
        ],
        "error_message": run.error_message,
        "created_at": run.created_at.isoformat() if run.created_at else "",
        "updated_at": run.updated_at.isoformat() if run.updated_at else "",
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    }
