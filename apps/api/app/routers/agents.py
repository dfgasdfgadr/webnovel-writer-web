"""Agent pipeline endpoints — pipeline trigger, SSE streaming, review results, architect, search."""

import json
import logging

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
from app.agents.llm import LLMProvider
from app.search import SearchIndex

logger = logging.getLogger("novelcraft.agents")
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
    synopsis: dict = {}


class BatchOutlineRequest(BaseModel):
    volume: dict = {}
    start_chapter: int = 1
    end_chapter: int = 1
    synopsis: dict = {}


class VolumePlanRequest(BaseModel):
    synopsis: dict = {}
    total_chapters: int = 100
    chapters_per_volume: int = 50


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

    llm = await LLMProvider.for_user(current_user.id, db)
    architect = ArchitectAgent(llm=llm)
    result = await architect.synopsis({
        "genre": body.genre, "hook": body.hook,
        "protagonist": body.protagonist,
        "world_building": body.world_building,
        "power_system": body.power_system,
    })

    # Persist synopsis to project
    try:
        project.synopsis_json = json.dumps(result, ensure_ascii=False)
        await db.commit()
    except Exception:
        logger.exception("Failed to persist synopsis for project %s", project_id)

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

    synopsis = body.synopsis
    if not synopsis and project.synopsis_json:
        try:
            synopsis = json.loads(project.synopsis_json)
        except json.JSONDecodeError:
            synopsis = {}

    llm = await LLMProvider.for_user(current_user.id, db)
    architect = ArchitectAgent(llm=llm)
    result = await architect.chapter_outline(
        synopsis=synopsis, volume=body.volume,
        chapter_num=body.chapter_num, prev_summaries=None,
    )

    # Persist outline to chapter (auto-create if needed)
    try:
        existing = (
            await db.execute(
                select(Chapter).where(
                    Chapter.project_id == project_id,
                    Chapter.number == body.chapter_num,
                )
            )
        ).scalar_one_or_none()

        if existing:
            existing.outline = result.get("outline", json.dumps(result, ensure_ascii=False))
            if result.get("title") and not existing.title.startswith("第"):
                existing.title = result["title"]
        else:
            chapter = Chapter(
                project_id=project_id,
                title=result.get("title", f"第{body.chapter_num}章"),
                number=body.chapter_num,
                content="",
                outline=result.get("outline", json.dumps(result, ensure_ascii=False)),
            )
            db.add(chapter)
        await db.commit()
    except Exception:
        logger.exception("Failed to persist outline for chapter %d in project %s", body.chapter_num, project_id)

    return result


@router.post("/architect/outline/{project_id}/batch")
async def generate_batch_outlines(
    project_id: str,
    body: BatchOutlineRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if body.start_chapter < 1 or body.end_chapter < body.start_chapter:
        raise HTTPException(status_code=400, detail="Invalid chapter range")

    synopsis = body.synopsis
    if not synopsis and project.synopsis_json:
        try:
            synopsis = json.loads(project.synopsis_json)
        except json.JSONDecodeError:
            synopsis = {}

    llm = await LLMProvider.for_user(current_user.id, db)
    architect = ArchitectAgent(llm=llm)

    results = []
    completed = 0
    failed = 0

    for ch_num in range(body.start_chapter, body.end_chapter + 1):
        try:
            result = await architect.chapter_outline(
                synopsis=synopsis, volume=body.volume,
                chapter_num=ch_num, prev_summaries=None,
            )

            existing = (
                await db.execute(
                    select(Chapter).where(
                        Chapter.project_id == project_id,
                        Chapter.number == ch_num,
                    )
                )
            ).scalar_one_or_none()

            if existing:
                existing.outline = result.get("outline", json.dumps(result, ensure_ascii=False))
                if result.get("title") and not existing.title.startswith("第"):
                    existing.title = result["title"]
            else:
                chapter = Chapter(
                    project_id=project_id,
                    title=result.get("title", f"第{ch_num}章"),
                    number=ch_num,
                    content="",
                    outline=result.get("outline", json.dumps(result, ensure_ascii=False)),
                )
                db.add(chapter)
            await db.commit()

            results.append({"chapter_num": ch_num, "success": True, "data": result})
            completed += 1
        except Exception as e:
            logger.exception("Batch outline: chapter %d failed", ch_num)
            await db.rollback()
            results.append({"chapter_num": ch_num, "success": False, "error": str(e)})
            failed += 1

    return {"total": body.end_chapter - body.start_chapter + 1, "completed": completed, "failed": failed, "results": results}


@router.post("/architect/volume-plan/{project_id}")
async def generate_volume_plan(
    project_id: str,
    body: VolumePlanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a rolling volume plan: detailed outlines for first 2 volumes, skeleton for rest."""
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    synopsis = body.synopsis
    if not synopsis and project.synopsis_json:
        try:
            synopsis = json.loads(project.synopsis_json)
        except json.JSONDecodeError:
            synopsis = {}

    total_chapters = body.total_chapters
    chapters_per_volume = body.chapters_per_volume
    total_volumes = max(1, (total_chapters + chapters_per_volume - 1) // chapters_per_volume)

    llm = await LLMProvider.for_user(current_user.id, db)
    architect = ArchitectAgent(llm=llm)

    volumes = []
    for vol_num in range(1, total_volumes + 1):
        start_ch = (vol_num - 1) * chapters_per_volume + 1
        end_ch = min(vol_num * chapters_per_volume, total_chapters)
        is_detailed = vol_num <= 2

        volume_info = {
            "num": vol_num,
            "title": synopsis.get("volumes", [{}])[vol_num - 1].get("title", f"第{vol_num}卷") if isinstance(synopsis.get("volumes"), list) and len(synopsis.get("volumes", [])) >= vol_num else f"第{vol_num}卷",
            "summary": synopsis.get("volumes", [{}])[vol_num - 1].get("summary", f"第{vol_num}卷内容，章节 {start_ch}-{end_ch}") if isinstance(synopsis.get("volumes"), list) and len(synopsis.get("volumes", [])) >= vol_num else f"第{vol_num}卷内容，章节 {start_ch}-{end_ch}",
            "target_chapters": end_ch - start_ch + 1,
            "chapters": [],
        }

        if is_detailed:
            # Generate detailed chapter outlines for first 2 volumes
            for ch_num in range(start_ch, end_ch + 1):
                try:
                    result = await architect.chapter_outline(
                        synopsis=synopsis, volume={"num": vol_num, "title": volume_info["title"], "summary": volume_info["summary"]},
                        chapter_num=ch_num, prev_summaries=None,
                    )

                    existing = (
                        await db.execute(
                            select(Chapter).where(
                                Chapter.project_id == project_id,
                                Chapter.number == ch_num,
                            )
                        )
                    ).scalar_one_or_none()

                    if existing:
                        existing.outline = result.get("outline", "")
                        if result.get("title"):
                            existing.title = result["title"]
                    else:
                        chapter = Chapter(
                            project_id=project_id,
                            title=result.get("title", f"第{ch_num}章"),
                            number=ch_num,
                            content="",
                            outline=result.get("outline", json.dumps(result, ensure_ascii=False)),
                        )
                        db.add(chapter)
                    await db.commit()

                    volume_info["chapters"].append(result)
                except Exception as e:
                    logger.exception("Volume plan: chapter %d failed", ch_num)
                    await db.rollback()
                    volume_info["chapters"].append({"chapter_num": ch_num, "error": str(e)})

        volumes.append(volume_info)

    return {"total_volumes": total_volumes, "volumes": volumes}


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


# --- Checkpoint ---

from app.agents.harness import Harness as HarnessClass


@router.get("/pipeline/{chapter_id}/checkpoint")
async def get_checkpoint(
    chapter_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the latest checkpoint for a chapter's pipeline run."""
    chapter = await db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    project = await db.get(Project, chapter.project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    harness = HarnessClass(project.root_dir or ".")
    cp = harness.latest_checkpoint(chapter_id)

    if not cp:
        return {"checkpoint": None}

    return {
        "checkpoint": {
            "phase": cp.phase.value,
            "flow": cp.flow.value,
            "step": cp.step.value,
            "chapter_id": cp.chapter_id,
            "project_id": cp.project_id,
            "payload": cp.payload,
        }
    }


class ResumeCheckpointRequest(BaseModel):
    step: str  # context | draft | review | extract | commit


@router.post("/pipeline/{chapter_id}/checkpoint/resume")
async def resume_from_checkpoint(
    chapter_id: str,
    body: ResumeCheckpointRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Resume a pipeline run from a specified step checkpoint.

    Validates that a checkpoint exists for the given step and re-runs
    the pipeline from that step onward.
    """
    chapter = await db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    project = await db.get(Project, chapter.project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    harness = HarnessClass(project.root_dir or ".")
    cp = harness.latest_checkpoint(chapter_id)

    if not cp:
        raise HTTPException(status_code=400, detail="No checkpoint found for this chapter")

    valid_steps = {"context", "draft", "review", "extract", "commit"}
    if body.step not in valid_steps:
        raise HTTPException(status_code=400, detail=f"Invalid step. Valid: {', '.join(sorted(valid_steps))}")

    # Re-create pipeline with user's LLM settings
    pipeline = await WritingPipeline.create(
        db=db,
        project_root=project.root_dir or ".",
        chapter_id=chapter_id,
        project_id=project.id,
        chapter_num=chapter.number,
        user_id=current_user.id,
    )

    effective_outline = (chapter.outline or chapter.content or "").strip()
    if not effective_outline:
        raise HTTPException(status_code=400, detail="请先填写章纲后再恢复流水线")

    # Run from the requested step
    contracts = pipeline.story.get_all_contracts_for_writing(pipeline.chapter_num)
    summaries = pipeline.story.get_recent_summaries(pipeline.chapter_num, count=5)
    step_results = []
    blocking_issues = []
    chapter_text = ""

    # Run continuity regardless
    continuity_data = {}
    try:
        continuity_data = await pipeline._run_continuity()
        step_results.append({"step": "continuity", "result": continuity_data})
    except Exception as e:
        step_results.append({"step": "continuity", "result": {"error": str(e)}})

    if body.step == "context":
        ctx_result = await pipeline._run_agent("context", pipeline.context_agent.run(
            chapter_outline=effective_outline,
            contracts=contracts, summaries=summaries,
            continuity=continuity_data,
        ))
        if not ctx_result.success:
            return {"success": False, "step_results": step_results, "blocking_issues": [], "chapter_text": "", "error": f"ContextAgent failed: {ctx_result.error}"}
        step_results.append({"step": "context", "result": ctx_result.data})

        brief = ctx_result.data.get("brief", effective_outline)
        draft_result = await pipeline._run_agent("writer", pipeline.writer_agent.run(brief=brief))
        if not draft_result.success:
            return {"success": False, "step_results": step_results, "blocking_issues": [], "chapter_text": "", "error": f"WriterAgent failed: {draft_result.error}"}
        chapter_text = draft_result.data.get("content", "")
        step_results.append({"step": "draft", "result": draft_result.data})

        review_result = await pipeline._run_agent("review", pipeline.review_agent.run(
            chapter_content=chapter_text,
            setting_json=contracts.get("master_setting", {}),
            chapter_outline=effective_outline,
        ))
        if not review_result.success:
            return {"success": False, "step_results": step_results, "blocking_issues": [], "chapter_text": chapter_text, "error": f"ReviewAgent failed: {review_result.error}"}
        issues = review_result.data.get("issues", [])
        blocking_issues = [i for i in issues if i.get("severity") == "blocking"]
        step_results.append({"step": "review", "result": review_result.data})

        # Persist review issues
        for issue in issues:
            db.add(ReviewIssue(
                chapter_id=chapter_id, project_id=project.id,
                severity=issue.get("severity", "minor"),
                category=issue.get("category", "unknown"),
                title=issue.get("title", ""),
                description=issue.get("description", ""),
                evidence=issue.get("evidence", ""),
                suggestion=issue.get("suggestion"),
            ))

        extract_result = await pipeline._run_agent("data", pipeline.data_agent.run(
            chapter_content=chapter_text, chapter_outline=effective_outline,
        ))
        step_results.append({"step": "extract", "result": extract_result.data})

        # Commit
        commit_data = extract_result.data.get("data", {}) if extract_result.success else {}
        db.add(ChapterCommit(
            chapter_id=chapter_id, project_id=project.id,
            content_json={"text": chapter_text, "outline": effective_outline},
            state_changes=commit_data.get("state_changes", []),
            new_entities=commit_data.get("new_entities", []),
            new_relationships=commit_data.get("new_relationships", []),
            foreshadowing_planted=commit_data.get("foreshadowing_planted", []),
            foreshadowing_resolved=commit_data.get("foreshadowing_resolved", []),
            summary=commit_data.get("summary", ""),
        ))
        pipeline.story.write_commit(pipeline.chapter_num, {
            "version": 1, "content": chapter_text,
            "state_changes": commit_data.get("state_changes", []),
            "summary": commit_data.get("summary", ""),
        })
        pipeline.story.write_summary(pipeline.chapter_num, commit_data.get("summary", ""))
        step_results.append({"step": "commit", "result": {"summary": commit_data.get("summary", "")}})

        if blocking_issues:
            chapter.status = "reviewing"
        else:
            chapter.status = "accepted"
            chapter.content = chapter_text
            from app.models.chapter import calculate_word_count
            chapter.word_count = calculate_word_count(chapter_text)

        await db.commit()
        pipeline.story.write_review(pipeline.chapter_num, {"issues": issues})
        harness.save_state({"phase": "writing", "last_chapter": pipeline.chapter_num})

        return {"success": True, "step_results": step_results, "blocking_issues": blocking_issues, "chapter_text": chapter_text, "error": None}

    # For non-context steps, return current state for the client to request through stream_draft
    return {
        "success": True,
        "step_results": step_results,
        "blocking_issues": [],
        "chapter_text": chapter.content or "",
        "error": None,
        "message": f"Resumed checkpoint at step '{body.step}'. Use stream_draft for drafting.",
    }
