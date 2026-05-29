"""Agent pipeline endpoints — pipeline trigger, SSE streaming, review results, architect, search."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from jose import JWTError, jwt

from app.database import get_db
from app.models import User, Project, Chapter, ReviewIssue, ReviewMetric, AgentRun, Entity, Card, SearchDoc, Summary, ReaderPulseResult
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


class RunReviewRequest(BaseModel):
    content: str | None = None
    outline: str | None = None


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

    # Wire Story System: save master setting
    if project.root_dir:
        try:
            from app.story_system import StorySystem
            ss = StorySystem(project.root_dir)
            existing = ss.master_setting()
            existing.update({
                "title": project.title,
                "genre": body.genre,
                "hook": body.hook,
                "synopsis": result.get("synopsis", ""),
                "volumes": result.get("volumes", []),
                "updated_at": project.updated_at.isoformat() if project.updated_at else "",
            })
            ss.save_master_setting(existing)
            # Write 总纲.md
            outline_dir = Path(project.root_dir) / "大纲"
            outline_dir.mkdir(parents=True, exist_ok=True)
            synopsis_text = result.get("synopsis", "")
            synopsis_md = f"# {result.get('title', project.title)}\n\n"
            synopsis_md += f"**题材**：{result.get('genre', body.genre)}\n\n"
            synopsis_md += f"**核心卖点**：{result.get('hook', body.hook)}\n\n"
            synopsis_md += f"## 故事概述\n\n{synopsis_text}\n\n## 分卷规划\n\n"
            for vol in result.get("volumes", []):
                synopsis_md += f"- **第{vol.get('num', '?')}卷 {vol.get('title', '')}**：{vol.get('summary', '')}（{vol.get('target_chapters', '?')}章）\n"
            (outline_dir / "总纲.md").write_text(synopsis_md, encoding="utf-8")
        except Exception:
            logger.exception("Failed to wire StorySystem synopsis for project %s", project_id)

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

    # Wire Story System: save chapter contract
    if project.root_dir:
        try:
            from app.story_system import StorySystem
            ss = StorySystem(project.root_dir)
            ss.save_chapter_contract(body.chapter_num, {
                "title": result.get("title", f"第{body.chapter_num}章"),
                "outline": result.get("outline", ""),
                "must_cover_nodes": result.get("must_cover_nodes", []),
                "forbidden_zones": result.get("forbidden_zones", []),
                "key_characters": result.get("key_characters", []),
                "target_words": result.get("target_words", 3000),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception:
            logger.exception("Failed to wire StorySystem chapter contract for ch %d", body.chapter_num)

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

            # Wire Story System: save chapter contract
            if project.root_dir:
                try:
                    from app.story_system import StorySystem
                    ss = StorySystem(project.root_dir)
                    ss.save_chapter_contract(ch_num, {
                        "title": result.get("title", f"第{ch_num}章"),
                        "outline": result.get("outline", ""),
                        "must_cover_nodes": result.get("must_cover_nodes", []),
                        "forbidden_zones": result.get("forbidden_zones", []),
                        "key_characters": result.get("key_characters", []),
                        "target_words": result.get("target_words", 3000),
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                    })
                except Exception:
                    logger.exception("Failed to wire StorySystem chapter contract for ch %d", ch_num)

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

    try:
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
    except UnicodeDecodeError as e:
        logger.exception("Pipeline file encoding error")
        raise HTTPException(status_code=500, detail=f"项目文件编码错误，请确保为 UTF-8: {e}")
    except Exception as e:
        logger.exception("Pipeline failed")
        raise HTTPException(status_code=500, detail=str(e))


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


@router.post("/reviews/{chapter_id}/run")
async def run_review(
    chapter_id: str,
    body: RunReviewRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Run ReviewAgent on chapter content and persist issues."""
    chapter = await db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    project = await db.get(Project, chapter.project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    chapter_content = (body.content if body and body.content is not None else chapter.content or "").strip()
    chapter_outline = (body.outline if body and body.outline is not None else chapter.outline or "").strip()
    if not chapter_content:
        raise HTTPException(status_code=400, detail="章节无正文，无法审查")

    try:
        pipeline = await WritingPipeline.create(
            db=db,
            project_root=project.root_dir or ".",
            chapter_id=chapter_id,
            project_id=project.id,
            chapter_num=chapter.number,
            user_id=current_user.id,
        )
        pipeline.ensure_llm_configured()
        contracts = pipeline.story.get_all_contracts_for_writing(chapter.number)
        setting_json = contracts.get("master_setting", {})

        review_result = await pipeline._run_agent("review", pipeline.review_agent.run(
            chapter_content=chapter_content,
            setting_json=setting_json,
            chapter_outline=chapter_outline,
        ))
        if not review_result.success:
            raise HTTPException(status_code=502, detail=review_result.error or "审查失败")

        issues = review_result.data.get("issues", [])

        # Replace previous review issues for this chapter
        old = await db.execute(select(ReviewIssue).where(ReviewIssue.chapter_id == chapter_id))
        for item in old.scalars().all():
            await db.delete(item)

        for issue in issues:
            db.add(ReviewIssue(
                chapter_id=chapter_id,
                project_id=project.id,
                severity=issue.get("severity", "minor"),
                category=issue.get("category", "unknown"),
                title=issue.get("title", ""),
                description=issue.get("description", ""),
                evidence=issue.get("evidence", ""),
                suggestion=issue.get("suggestion"),
            ))

        metrics = review_result.data.get("review_metrics", {})
        if metrics:
            db.add(ReviewMetric(
                chapter_id=chapter_id,
                project_id=project.id,
                consistency_score=int(metrics.get("consistency_score", 0)),
                timeline_score=int(metrics.get("timeline_score", 0)),
                coherence_score=int(metrics.get("coherence_score", 0)),
                ooc_score=int(metrics.get("ooc_score", 0)),
                logic_score=int(metrics.get("logic_score", 0)),
                foreshadowing_score=int(metrics.get("foreshadowing_score", 0)),
                ai_flavor_score=int(metrics.get("ai_flavor_score", 0)),
                summary=review_result.data.get("summary", ""),
            ))

        pipeline.story.write_review(chapter.number, {"issues": issues})
        if any(i.get("severity") == "blocking" for i in issues):
            chapter.status = "reviewing"
        await db.commit()

        result = await db.execute(
            select(ReviewIssue).where(ReviewIssue.chapter_id == chapter_id).order_by(ReviewIssue.created_at.desc())
        )
        saved = result.scalars().all()
        return [
            {
                "id": i.id, "severity": i.severity, "category": i.category,
                "title": i.title, "description": i.description,
                "evidence": i.evidence, "suggestion": i.suggestion,
                "is_fixed": i.is_fixed, "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in saved
        ]
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except UnicodeDecodeError as e:
        logger.exception("Review file encoding error")
        raise HTTPException(status_code=500, detail=f"项目文件编码错误，请确保为 UTF-8: {e}")
    except Exception as e:
        logger.exception("Review failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reviews/{chapter_id}/metrics")
async def get_review_metrics(
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
        select(ReviewMetric).where(ReviewMetric.chapter_id == chapter_id).order_by(ReviewMetric.created_at.desc())
    )
    metrics = result.scalars().all()
    return [
        {
            "id": m.id, "chapter_id": m.chapter_id, "project_id": m.project_id,
            "consistency_score": m.consistency_score,
            "timeline_score": m.timeline_score,
            "coherence_score": m.coherence_score,
            "ooc_score": m.ooc_score,
            "logic_score": m.logic_score,
            "foreshadowing_score": m.foreshadowing_score,
            "ai_flavor_score": m.ai_flavor_score,
            "summary": m.summary,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in metrics
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
            {"id": f.id, "description": f.description, "status": f.status, "planted_in_chapter_id": f.planted_in_chapter_id}
            for f in foreshadowings
        ]

    if not body.recent_commits:
        result = await db.execute(
            select(ChapterCommit, ChapterModel.number)
            .join(ChapterModel, ChapterModel.id == ChapterCommit.chapter_id)
            .where(ChapterCommit.project_id == project_id)
            .order_by(ChapterCommit.created_at.desc())
            .limit(5)
        )
        rows = result.all()
        body.recent_commits = [
            {"chapter_number": num, "chapter_id": c.chapter_id, "summary": c.summary or ""}
            for c, num in rows
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
            "id": f.id, "status": f.status,
            "planted_in_chapter_id": f.planted_in_chapter_id, "resolved_in_chapter_id": f.resolved_in_chapter_id,
            "description": f.description,
        }
        for f in foreshadowings
    ]

    return {"nodes": nodes, "edges": edges, "timeline": timeline}


# --- Polish ---

from app.agents.polish import PolishAgent, POLISH_AXES


class PolishRequest(BaseModel):
    issues: list[dict]  # ReviewIssue items to fix
    enabled_axes: list[str] | None = None  # axes to enable; None = all
    chapter_outline: str = ""


@router.get("/polish/axes")
async def get_polish_axes():
    """Return available polish axes with descriptions."""
    return {"axes": {k: v for k, v in POLISH_AXES.items()}}


@router.post("/polish/{chapter_id}")
async def polish_chapter(
    chapter_id: str,
    body: PolishRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Polish a chapter based on specific review issues."""
    chapter = await db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    project = await db.get(Project, chapter.project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if not chapter.content:
        raise HTTPException(status_code=400, detail="Chapter has no content to polish")

    if not body.issues:
        raise HTTPException(status_code=400, detail="No issues provided for polish")

    llm = await LLMProvider.for_user(current_user.id, db)
    agent = PolishAgent(llm=llm)
    result = await agent.run(
        chapter_content=chapter.content,
        issues=body.issues,
        enabled_axes=body.enabled_axes,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=f"Polish failed: {result.error or 'Unknown error'}")

    return {"result": result.data.get("result", {}), "token_input": result.token_input, "token_output": result.token_output}


def _sse_event(event: str, data: dict) -> str:
    """Format a Server-Sent Event with JSON data. No event: field — dispatch by data.type on client."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.get("/polish/{chapter_id}/stream")
async def stream_polish(
    chapter_id: str,
    token: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
):
    """SSE streaming polish — processes issues one by one and streams diffs."""
    current_user = await _get_user_from_token(token, db) if token else None
    if not current_user:
        raise HTTPException(status_code=401, detail="Token required as query param")

    chapter = await db.get(Chapter, chapter_id)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    project = await db.get(Project, chapter.project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if not chapter.content:
        raise HTTPException(status_code=400, detail="Chapter has no content to polish")

    # Get review issues
    from sqlalchemy import select as sa_select
    result = await db.execute(
        sa_select(ReviewIssue).where(
            ReviewIssue.chapter_id == chapter_id,
            ReviewIssue.is_fixed == False,
        )
    )
    issues = result.scalars().all()
    if not issues:
        raise HTTPException(status_code=400, detail="No unfixed issues to polish")

    issues_data = [
        {
            "id": i.id, "severity": i.severity, "category": i.category,
            "title": i.title, "description": i.description,
            "evidence": i.evidence, "suggestion": i.suggestion,
        }
        for i in issues
    ]

    async def generate():
        try:
            llm = await LLMProvider.for_user(current_user.id, db)
        except Exception as e:
            yield _sse_event("error", {"type": "error", "error": f"LLM 配置错误: {e}"})
            return
        agent = PolishAgent(llm=llm)

        yield _sse_event("start", {"type": "start", "total_issues": len(issues_data)})

        for idx, issue in enumerate(issues_data):
            try:
                polish_result = await agent.run(
                    chapter_content=chapter.content,
                    issues=[issue],
                    enabled_axes=None,
                )
                if polish_result.success:
                    diff_data = polish_result.data.get("result", {})
                    yield _sse_event("issue_done", {"type": "issue_done", "index": idx + 1, "issue_id": issue["id"], "issue_title": issue["title"], "diff": diff_data.get("diff", []), "summary": diff_data.get("summary", "")})

                    # Update content incrementally
                    for d in diff_data.get("diff", []):
                        chapter.content = chapter.content.replace(d.get("before", ""), d.get("after", ""), 1)

                    # Mark issue as fixed
                    db_issue = await db.get(ReviewIssue, issue["id"])
                    if db_issue:
                        db_issue.is_fixed = True
                    await db.commit()
                else:
                    yield _sse_event("issue_error", {"type": "issue_error", "index": idx + 1, "issue_id": issue["id"], "error": polish_result.error})
            except Exception as e:
                logger.exception("Polish issue %s failed", issue["id"])
                yield _sse_event("issue_error", {"type": "issue_error", "index": idx + 1, "issue_id": issue["id"], "error": str(e)})

        yield _sse_event("done", {"type": "done", "updated_content": chapter.content})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# --- Checkpoint ---

from app.agents.harness import Harness as HarnessClass, Step


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


STEP_ORDER = ["context", "draft", "review", "extract", "commit"]


def _steps_from(start_step: str) -> list[str]:
    """Return the list of steps to execute starting from start_step."""
    try:
        idx = STEP_ORDER.index(start_step)
    except ValueError:
        return []
    return STEP_ORDER[idx:]


def _resume_error(step_results: list[dict], error: str) -> dict:
    return {"success": False, "step_results": step_results, "blocking_issues": [], "chapter_text": "", "error": error}


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
    step_results: list[dict] = []
    blocking_issues: list[dict] = []
    chapter_text: str = chapter.content or ""

    checkpoint_payload = cp.payload if cp else {}
    steps_to_run = _steps_from(body.step)

    # Run continuity if starting from context or draft (need it for context)
    continuity_data: dict = {}
    if body.step in ("context", "draft"):
        try:
            continuity_data = await pipeline._run_continuity()
            step_results.append({"step": "continuity", "result": continuity_data})
        except Exception as e:
            step_results.append({"step": "continuity", "result": {"error": str(e)}})

    if "context" in steps_to_run:
        ctx_result = await pipeline._run_agent("context", pipeline.context_agent.run(
            chapter_outline=effective_outline,
            contracts=contracts, summaries=summaries,
            continuity=continuity_data,
        ))
        if not ctx_result.success:
            return _resume_error(step_results, f"ContextAgent failed: {ctx_result.error}")
        step_results.append({"step": "context", "result": ctx_result.data})
        pipeline.harness.advance_step(chapter_id, project.id, Step("context"), ctx_result.data)

    brief = effective_outline
    if body.step in ("context", "draft") and step_results:
        ctx_data = next((s["result"] for s in step_results if s["step"] == "context"), {})
        brief = ctx_data.get("brief", effective_outline) if isinstance(ctx_data, dict) else effective_outline
    elif "draft" in steps_to_run:
        brief = checkpoint_payload.get("brief", effective_outline) if isinstance(checkpoint_payload, dict) else effective_outline

    if "draft" in steps_to_run:
        draft_result = await pipeline._run_agent("writer", pipeline.writer_agent.run(brief=brief))
        if not draft_result.success:
            return _resume_error(step_results, f"WriterAgent failed: {draft_result.error}")
        chapter_text = draft_result.data.get("content", "")
        step_results.append({"step": "draft", "result": draft_result.data})
        pipeline.harness.advance_step(chapter_id, project.id, Step("draft"), draft_result.data)

    if "review" in steps_to_run:
        review_result = await pipeline._run_agent("review", pipeline.review_agent.run(
            chapter_content=chapter_text,
            setting_json=contracts.get("master_setting", {}),
            chapter_outline=effective_outline,
        ))
        if not review_result.success:
            return _resume_error(step_results, f"ReviewAgent failed: {review_result.error}")
        issues = review_result.data.get("issues", [])
        blocking_issues = [i for i in issues if i.get("severity") == "blocking"]
        step_results.append({"step": "review", "result": review_result.data})
        pipeline.harness.advance_step(chapter_id, project.id, Step("review"), review_result.data)
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

    if "extract" in steps_to_run:
        extract_result = await pipeline._run_agent("data", pipeline.data_agent.run(
            chapter_content=chapter_text, chapter_outline=effective_outline,
        ))
        step_results.append({"step": "extract", "result": extract_result.data})
        pipeline.harness.advance_step(chapter_id, project.id, Step("extract"), extract_result.data)

    if "commit" in steps_to_run:
        extract_data = next((s["result"] for s in step_results if s["step"] == "extract"), {})
        commit_data = extract_data.get("data", {}) if extract_data.get("success", True) else {}
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
        db.add(Summary(
            project_id=project.id,
            level="chapter",
            scope_label=f"第{pipeline.chapter_num}章",
            content=commit_data.get("summary", ""),
        ))
        step_results.append({"step": "commit", "result": {"summary": commit_data.get("summary", "")}})

        if blocking_issues:
            chapter.status = "reviewing"
        else:
            chapter.status = "accepted"
            chapter.content = chapter_text
            from app.models.chapter import calculate_word_count
            chapter.word_count = calculate_word_count(chapter_text)

        pipeline.story.write_review(pipeline.chapter_num, {"issues": [s["result"].get("issues", []) for s in step_results if s["step"] == "review"][0] if any(s["step"] == "review" for s in step_results) else []})
        harness.save_state({"phase": "writing", "last_chapter": pipeline.chapter_num})

    await db.commit()
    pipeline.harness.save_state({"phase": "writing", "last_chapter": pipeline.chapter_num})
    return {"success": True, "step_results": step_results, "blocking_issues": blocking_issues, "chapter_text": chapter_text, "error": None}


# --- Reader Pulse ---

@router.get("/reader-pulse/{chapter_id}")
async def get_reader_pulse(
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
        select(ReaderPulseResult).where(ReaderPulseResult.chapter_id == chapter_id).order_by(ReaderPulseResult.created_at.desc())
    )
    pulses = result.scalars().all()
    return [
        {
            "id": p.id, "chapter_id": p.chapter_id, "project_id": p.project_id,
            "drop_risk": p.drop_risk, "hook_quality": p.hook_quality,
            "pacing_score": p.pacing_score, "expectation": p.expectation,
            "strengths": json.loads(p.strengths) if p.strengths else [],
            "weaknesses": json.loads(p.weaknesses) if p.weaknesses else [],
            "next_chapter_suggestion": p.next_chapter_suggestion,
            "overall_verdict": p.overall_verdict,
            "created_at": p.created_at.isoformat() if p.created_at else None,
        }
        for p in pulses
    ]


@router.post("/reader-pulse/{chapter_id}")
async def run_reader_pulse(
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

    from app.agents.reader_pulse import ReaderPulseAgent
    from app.agents.llm import LLMProvider

    llm = await LLMProvider.for_user(current_user.id, db)
    agent = ReaderPulseAgent(llm=llm)

    # Get previous chapter summary
    prev_summary = ""
    prev_result = await db.execute(
        select(Summary).where(
            Summary.project_id == project.id,
            Summary.level == "chapter",
        ).order_by(Summary.created_at.desc()).limit(1)
    )
    prev = prev_result.scalar_one_or_none()
    if prev:
        prev_summary = prev.content or ""

    result = await agent.run(
        chapter_content=chapter.content or "",
        chapter_outline=chapter.outline or "",
        previous_chapter_summary=prev_summary,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Reader pulse failed")

    data = result.data
    pulse = ReaderPulseResult(
        chapter_id=chapter_id,
        project_id=project.id,
        drop_risk=int(data.get("drop_risk", 50)),
        hook_quality=int(data.get("hook_quality", 50)),
        pacing_score=int(data.get("pacing_score", 50)),
        expectation=data.get("expectation", ""),
        strengths=json.dumps(data.get("strengths", []), ensure_ascii=False),
        weaknesses=json.dumps(data.get("weaknesses", []), ensure_ascii=False),
        next_chapter_suggestion=data.get("next_chapter_suggestion", ""),
        overall_verdict=data.get("overall_verdict", ""),
    )
    db.add(pulse)
    await db.commit()
    await db.refresh(pulse)

    return {
        "id": pulse.id, "chapter_id": pulse.chapter_id, "project_id": pulse.project_id,
        "drop_risk": pulse.drop_risk, "hook_quality": pulse.hook_quality,
        "pacing_score": pulse.pacing_score, "expectation": pulse.expectation,
        "strengths": json.loads(pulse.strengths) if pulse.strengths else [],
        "weaknesses": json.loads(pulse.weaknesses) if pulse.weaknesses else [],
        "next_chapter_suggestion": pulse.next_chapter_suggestion,
        "overall_verdict": pulse.overall_verdict,
        "created_at": pulse.created_at.isoformat() if pulse.created_at else None,
    }


# --- Story Foundry ---

class FoundryDeconstructRequest(BaseModel):
    book_title: str
    sample_chapters: list[str] = []
    mode: str = "quick"
    chapter_groups: list[dict] = []


class FoundryQuestionsRequest(BaseModel):
    deconstruction: dict = {}
    preferences: dict | None = None


class FoundryComposeRequest(BaseModel):
    book_title: str
    deconstruction: dict = {}
    selections: dict = {}
    custom_notes: str = ""


@router.post("/foundry/deconstruct")
async def foundry_deconstruct(
    body: FoundryDeconstructRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Deconstruct a reference book for transferable patterns."""
    from app.agents.deconstruct import DeconstructAgent
    from app.agents.llm import LLMProvider

    try:
        llm = await LLMProvider.for_user(current_user.id, db)
    except Exception:
        llm = None

    # Mode dispatch
    mode = body.mode if body.mode in ("quick", "representative", "fullbook") else "quick"

    if mode == "fullbook":
        return {
            "status": "deferred",
            "message": "Full-book RAG 流程将在下一阶段支持",
            "deconstruction": None,
        }

    # Prepare sample_chapters for the agent
    if mode == "representative" and body.chapter_groups:
        sample_chapters = [
            f"【章节组：{g.get('label', '未命名')}\n{g.get('content', '')}"
            for g in body.chapter_groups
            if g.get("content", "").strip()
        ]
    else:
        sample_chapters = body.sample_chapters

    agent = DeconstructAgent(llm=llm) if llm else DeconstructAgent()
    result = await agent.run(book_title=body.book_title, sample_chapters=sample_chapters)

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Deconstruct failed")

    data = result.data
    # Normalize deconstruction fields
    deconstruction = {
        "golden_chapters": data.get("golden_chapters") or data.get("golden_three", []),
        "hooks": data.get("hooks") or data.get("pleasure_points", {}).get("patterns", []),
        "character_patterns": data.get("character_patterns") or data.get("character_design", []),
        "world_patterns": data.get("world_patterns") or data.get("world_building", []),
        "pacing": data.get("pacing") or data.get("narration", []),
        "transferable_patterns": data.get("transferable_patterns", []),
        "red_flags": data.get("red_flags") or data.get("warnings", []),
    }

    return {
        "status": "done",
        "deconstruction": deconstruction,
        "fallback": False,
    }


@router.post("/foundry/questions")
async def foundry_questions(
    body: FoundryQuestionsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate strategic choice questions from deconstruction."""
    from app.agents.foundry_question import FoundryQuestionAgent
    from app.agents.llm import LLMProvider

    try:
        llm = await LLMProvider.for_user(current_user.id, db)
    except Exception:
        llm = None

    agent = FoundryQuestionAgent(llm=llm) if llm else FoundryQuestionAgent()
    result = await agent.run(
        deconstruction=body.deconstruction,
        preferences=body.preferences or {},
    )

    if not result.success:
        # Return fallback questions on error
        from app.agents.foundry_question import FALLBACK_QUESTIONS
        return {
            "question_sets": FALLBACK_QUESTIONS,
            "fallback": True,
        }

    data = result.data
    return {
        "question_sets": data.get("question_sets", []),
        "fallback": data.get("fallback", False),
    }


@router.post("/foundry/compose")
async def foundry_compose(
    body: FoundryComposeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Compose complete story setup from deconstruction and user selections."""
    from app.agents.foundry_compose import FoundryComposerAgent
    from app.agents.llm import LLMProvider

    try:
        llm = await LLMProvider.for_user(current_user.id, db)
    except Exception:
        llm = None

    agent = FoundryComposerAgent(llm=llm) if llm else FoundryComposerAgent()
    result = await agent.run(
        book_title=body.book_title,
        deconstruction=body.deconstruction,
        selections=body.selections,
        custom_notes=body.custom_notes,
    )

    if not result.success:
        raise HTTPException(status_code=500, detail=result.error or "Compose failed")

    data = result.data
    return {
        "premise": data.get("premise", {}),
        "master_setting": data.get("master_setting", {}),
        "synopsis": data.get("synopsis", {}),
        "first_volume_chapters": data.get("first_volume_chapters", []),
        "fallback": data.get("fallback", False),
    }
