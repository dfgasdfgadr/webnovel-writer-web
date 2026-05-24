"""Agent pipeline endpoints — pipeline trigger, SSE streaming, review results, architect, search."""

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from jose import JWTError, jwt

from app.database import get_db
from app.models import User, Project, Chapter, ReviewIssue, AgentRun, Entity, Card
from app.services.auth import get_current_user
from app.config import settings
from app.pipeline import WritingPipeline
from app.agents.architect import ArchitectAgent
from app.search import SearchIndex

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


# --- Request models ---

class SynopsisRequest(BaseModel):
    genre: str = ""
    hook: str = ""
    protagonist: dict = {}
    world_building: dict = {}
    power_system: str = ""


class OutlineRequest(BaseModel):
    volume: dict = {}
    chapter_num: int = 1


class RunPipelineRequest(BaseModel):
    chapter_outline: str = ""


class PipelineStatusResponse(BaseModel):
    success: bool
    step_results: list[dict]
    blocking_issues: list[dict]
    chapter_text: str
    error: str | None = None


# --- Token helper for SSE ---

async def _get_user_from_token(token_str: str, db: AsyncSession) -> User:
    try:
        payload = jwt.decode(token_str, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


# --- Architect ---

@router.post("/architect/synopsis/{project_id}")
async def generate_synopsis(
    project_id: str,
    body: SynopsisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    architect = ArchitectAgent()
    result = await architect.synopsis({
        "genre": body.genre, "hook": body.hook,
        "protagonist": body.protagonist,
        "world_building": body.world_building,
        "power_system": body.power_system,
    })
    return result


@router.post("/architect/outline/{project_id}")
async def generate_outline(
    project_id: str,
    body: OutlineRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    architect = ArchitectAgent()
    result = await architect.chapter_outline(
        synopsis={}, volume=body.volume,
        chapter_num=body.chapter_num, prev_summaries=None,
    )
    return result


# --- Search ---

@router.get("/search/{project_id}")
async def search_project(
    project_id: str,
    q: str = Query(default=""),
    filter: str = Query(default="entities"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    index = SearchIndex()
    if filter in ("entities", "all"):
        result = await db.execute(select(Entity).where(Entity.project_id == project_id))
        for e in result.scalars().all():
            index.index_entity(e)
    if filter in ("cards", "all"):
        result = await db.execute(select(Card).where(Card.project_id == project_id))
        for c in result.scalars().all():
            index.index_card(c)
    if filter == "entities":
        return index.search_entities(q)
    elif filter == "cards":
        return index.search_cards(q)
    else:
        return index.search_entities(q) + index.search_cards(q)


# --- Pipeline ---

@router.post("/pipeline/{chapter_id}", response_model=PipelineStatusResponse)
async def run_pipeline(
    chapter_id: str,
    body: RunPipelineRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chapter = await db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    project = await db.get(Project, chapter.project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    pipeline = WritingPipeline(
        db=db,
        project_root=project.root_dir or ".",
        chapter_id=chapter_id,
        project_id=project.id,
        chapter_num=chapter.number,
    )
    result = await pipeline.run_full(body.chapter_outline or chapter.content)
    return PipelineStatusResponse(
        success=result.success,
        step_results=result.step_results,
        blocking_issues=result.blocking_issues,
        chapter_text=result.chapter_text,
        error=result.error,
    )


# --- SSE Streaming ---

@router.get("/pipeline/{chapter_id}/stream")
async def stream_draft(
    chapter_id: str,
    outline: str = Query(default=""),
    token: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
):
    current_user = await _get_user_from_token(token, db) if token else None
    if not current_user:
        raise HTTPException(status_code=401, detail="Token required as query param")

    chapter = await db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    project = await db.get(Project, chapter.project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    pipeline = WritingPipeline(
        db=db,
        project_root=project.root_dir or ".",
        chapter_id=chapter_id,
        project_id=project.id,
        chapter_num=chapter.number,
    )

    async def generate():
        async for chunk in pipeline.stream_draft(outline or chapter.content):
            yield f"data: {json.dumps({'content': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# --- Agent Runs & Reviews ---

@router.get("/runs/{project_id}")
async def list_runs(
    project_id: str,
    chapter_id: str | None = None,
    agent_type: str | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    query = select(AgentRun).where(AgentRun.project_id == project_id).order_by(AgentRun.created_at.desc())
    if chapter_id:
        query = query.where(AgentRun.chapter_id == chapter_id)
    if agent_type:
        query = query.where(AgentRun.agent_type == agent_type)
    result = await db.execute(query.limit(50))
    runs = result.scalars().all()
    return [
        {
            "id": r.id, "agent_type": r.agent_type, "phase": r.phase,
            "status": r.status, "token_input": r.token_input, "token_output": r.token_output,
            "elapsed_ms": r.elapsed_ms, "error_message": r.error_message,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in runs
    ]


@router.get("/reviews/{chapter_id}")
async def get_reviews(
    chapter_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chapter = await db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    project = await db.get(Project, chapter.project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(ReviewIssue).where(ReviewIssue.chapter_id == chapter_id).order_by(ReviewIssue.created_at.desc())
    )
    issues = result.scalars().all()
    return [
        {
            "id": i.id, "severity": i.severity, "category": i.category,
            "title": i.title, "description": i.description,
            "evidence": i.evidence, "suggestion": i.suggestion,
            "is_fixed": i.is_fixed, "created_at": i.created_at.isoformat() if i.created_at else None,
        }
        for i in issues
    ]
