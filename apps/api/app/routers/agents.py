"""Agent pipeline endpoints — pipeline trigger, SSE streaming, review results, architect, search."""

import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from jose import JWTError, jwt

from app.database import get_db
from app.models import User, Project, Chapter, ReviewIssue, AgentRun, Entity, Card, SearchDoc
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
    """Unified BM25 search across entities and cards, persisted to search_docs table."""
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Try loading from persisted search_docs first
    from sqlalchemy import delete as sa_delete
    persisted_docs = (
        await db.execute(
            select(SearchDoc).where(SearchDoc.project_id == project_id)
        )
    ).scalars().all()

    if persisted_docs:
        # Rebuild from persisted pre-tokenized docs
        index = SearchIndex()
        index.load_from_persisted(persisted_docs)
        if filter == "entities":
            return index.search_entities(q)
        elif filter == "cards":
            return index.search_cards(q)
        else:
            return index.search_entities(q) + index.search_cards(q)

    # First-time: index from DB and persist
    index = SearchIndex()
    if filter in ("entities", "all"):
        result = await db.execute(select(Entity).where(Entity.project_id == project_id))
        for e in result.scalars().all():
            doc_id, title, content, tokens, meta = index.index_entity(e)
            doc = SearchDoc(
                project_id=project_id, doc_id=doc_id,
                title=title, content=content,
            )
            doc.set_meta(meta)
            doc.set_tokens(tokens)
            db.add(doc)
    if filter in ("cards", "all"):
        result = await db.execute(select(Card).where(Card.project_id == project_id))
        for c in result.scalars().all():
            doc_id, title, content, tokens, meta = index.index_card(c)
            doc = SearchDoc(
                project_id=project_id, doc_id=doc_id,
                title=title, content=content,
            )
            doc.set_meta(meta)
            doc.set_tokens(tokens)
            db.add(doc)
    await db.commit()

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

    pipeline = await WritingPipeline.create(
        db=db,
        project_root=project.root_dir or ".",
        chapter_id=chapter_id,
        project_id=project.id,
        chapter_num=chapter.number,
        user_id=current_user.id,
    )
    effective_outline = (body.chapter_outline or chapter.outline or chapter.content or "").strip()
    result = await pipeline.run_full(effective_outline)
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

    pipeline = await WritingPipeline.create(
        db=db,
        project_root=project.root_dir or ".",
        chapter_id=chapter_id,
        project_id=project.id,
        chapter_num=chapter.number,
        user_id=current_user.id,
    )

    effective_outline = (outline or chapter.outline or chapter.content or "").strip()
    if not effective_outline:
        raise HTTPException(status_code=400, detail="请先填写章纲后再 AI 生成")

    async def generate():
        try:
            async for event in pipeline.stream_draft(effective_outline):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            yield "data: [DONE]\n\n"
        except ValueError as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': f'AI 生成失败: {e}'}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


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


# --- Continuity snapshot ---

from app.agents.continuity import ContinuityAgent
from app.models.entity import Entity, Relationship, Foreshadowing
from app.models.contract import ChapterCommit
from app.models.chapter import Chapter as ChapterModel


class ContinuityRequest(BaseModel):
    chapter_texts: list[dict] = []
    entities: list[dict] = []
    foreshadowing: list[dict] = []
    recent_commits: list[dict] = []


@router.post("/continuity/{project_id}")
async def run_continuity(
    project_id: str,
    body: ContinuityRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate continuity snapshot using ContinuityAgent.

    Auto-fetches entities, foreshadowing, and recent commits from DB if not provided.
    """
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Auto-fetch from DB if not provided in body
    if not body.entities:
        result = await db.execute(select(Entity).where(Entity.project_id == project_id))
        entities = result.scalars().all()
        body.entities = [
            {"name": e.name, "type": e.entity_type, "description": e.description or ""}
            for e in entities
        ]

    if not body.foreshadowing:
        result = await db.execute(
            select(Foreshadowing).where(Foreshadowing.project_id == project_id)
        )
        foreshadowings = result.scalars().all()
        body.foreshadowing = [
            {"id": f.id, "title": f.title, "status": f.status, "chapter_planted": f.chapter_planted}
            for f in foreshadowings
        ]

    if not body.recent_commits:
        result = await db.execute(
            select(ChapterCommit)
            .where(ChapterCommit.project_id == project_id)
            .order_by(ChapterCommit.created_at.desc())
            .limit(5)
        )
        commits = result.scalars().all()
        body.recent_commits = [
            {"chapter_number": c.chapter_number, "summary": c.summary or ""}
            for c in commits
        ]

    agent = ContinuityAgent()
    result = await agent.run(
        project_id=project_id,
        chapter_texts=body.chapter_texts,
        entities=body.entities,
        foreshadowing_items=body.foreshadowing,
        recent_commits=body.recent_commits,
    )
    return {
        "success": result.success,
        "data": result.data,
        "error": result.error,
    }


# --- Graph data ---

@router.get("/graph/{project_id}")
async def get_graph_data(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return entities + relationships + foreshadowing for graph visualization."""
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    entities_result = await db.execute(select(Entity).where(Entity.project_id == project_id))
    entities = entities_result.scalars().all()
    nodes = [
        {
            "id": e.id, "name": e.name, "type": e.entity_type,
            "description": e.description, "importance": e.importance or 1,
        }
        for e in entities
    ]

    rels_result = await db.execute(
        select(Relationship).where(Relationship.project_id == project_id)
    )
    relationships = rels_result.scalars().all()
    edges = [
        {
            "id": r.id, "source": r.source_entity_id, "target": r.target_entity_id,
            "label": r.relationship_type, "description": r.description,
        }
        for r in relationships
    ]

    foreshadowing_result = await db.execute(
        select(Foreshadowing).where(Foreshadowing.project_id == project_id)
    )
    foreshadowings = foreshadowing_result.scalars().all()
    timeline = [
        {
            "id": f.id, "title": f.title, "status": f.status,
            "chapter_planted": f.chapter_planted, "chapter_resolved": f.chapter_resolved,
            "description": f.description,
        }
        for f in foreshadowings
    ]

    return {"nodes": nodes, "edges": edges, "timeline": timeline}
