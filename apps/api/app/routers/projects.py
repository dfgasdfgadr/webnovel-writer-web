import json
import logging
import os
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectPublic, ProjectList
from app.services.auth import get_current_user
from app.config import settings
from app.story_system import StorySystem

logger = logging.getLogger("novelcraft.projects")
router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


def _slugify(title: str) -> str:
    """Generate a filesystem-safe slug from a project title."""
    slug = title.strip().lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = slug.strip("-")
    # Fallback: if slug is empty after all processing, use a stable short hash
    if not slug:
        import hashlib
        short = hashlib.sha256(title.encode()).hexdigest()[:8]
        slug = f"project-{short}"
    return slug[:50]


def _ensure_dir_skeleton(root_dir: str) -> None:
    """Create the standard project directory skeleton."""
    dirs = [
        "设定集",
        "大纲",
        "正文",
        ".novelcraft",
        ".story-system",
    ]
    for d in dirs:
        Path(root_dir, d).mkdir(parents=True, exist_ok=True)


async def _generate_settings_from_premise(premise: dict, user_id: str, db: AsyncSession) -> tuple[dict, list[str]]:
    """Use InitAgent to generate world-building, power-system, and protagonist card.
    Returns (settings_data, warnings). On LLM failure, returns stub data from premise."""
    from app.agents.init import InitAgent
    from app.agents.llm import LLMProvider

    try:
        llm = await LLMProvider.for_user(user_id, db)
        agent = InitAgent(llm=llm)
        return await agent.generate_settings(premise), []
    except Exception:
        logger.exception("InitAgent settings generation failed")
        stub = _build_stub_settings(premise)
        return stub, ["AI 生成失败，已使用项目预设信息创建基础设定文件，请检查 LLM 配置"]


def _build_stub_settings(premise: dict) -> dict:
    """Build stub setting content from premise data when LLM is unavailable."""
    protagonist = premise.get("protagonist", {})
    return {
        "world_building": (
            f"# 世界观\n\n"
            f"题材：{premise.get('genre', '未设定')}\n\n"
            f"## 故事核心\n{premise.get('hook', '（待补充）')}\n\n"
            f"## 世界背景\n（待 AI 生成补充）\n"
        ),
        "power_system": (
            f"# 力量体系\n\n"
            f"{premise.get('power_system', '（待设定）') or '（待设定）'}\n\n"
            f"金手指：{premise.get('golden_finger', '（待设定）') or '（待设定）'}\n"
        ),
        "protagonist_card": (
            f"# 主角卡\n\n"
            f"姓名：{protagonist.get('name', '（待设定）')}\n\n"
            f"性别：{protagonist.get('gender', '（待设定）')}\n\n"
            f"年龄：{protagonist.get('age', '（待设定）')}\n\n"
            f"性格：{protagonist.get('personality', '（待设定）')}\n\n"
            f"背景：{protagonist.get('background', '（待设定）')}\n\n"
            f"目标：{protagonist.get('goal', '（待设定）')}\n"
        ),
    }


async def _generate_synopsis_from_premise(premise: dict, user_id: str, db: AsyncSession) -> tuple[dict, list[str]]:
    """Use ArchitectAgent to generate synopsis from premise.
    Returns (synopsis_data, warnings). On LLM failure, returns stub synopsis."""
    from app.agents.architect import ArchitectAgent
    from app.agents.llm import LLMProvider

    try:
        llm = await LLMProvider.for_user(user_id, db)
        architect = ArchitectAgent(llm=llm)
        return await architect.synopsis(premise), []
    except Exception:
        logger.exception("ArchitectAgent synopsis generation failed")
        stub = _build_stub_synopsis(premise)
        return stub, []


def _build_stub_synopsis(premise: dict) -> dict:
    """Build a stub synopsis from premise data when LLM is unavailable."""
    return {
        "title": premise.get("title", "未命名"),
        "genre": premise.get("genre", ""),
        "hook": premise.get("hook", ""),
        "synopsis": f"（AI 总纲生成暂不可用。核心设定：{premise.get('genre', '未知题材')}，{premise.get('hook', '')}。请配置 LLM 后重新生成。）",
        "volumes": [
            {
                "num": 1,
                "title": "第一卷",
                "summary": "（待生成）",
                "target_chapters": premise.get("target_chapters", 30) or 30,
            }
        ],
    }


def _write_settings_files(root_dir: str, settings_data: dict) -> list[str]:
    """Write generated settings as Markdown files. Returns list of paths written."""
    written = []
    settings_dir = Path(root_dir) / "设定集"

    for key, filename in [
        ("world_building", "世界观.md"),
        ("power_system", "力量体系.md"),
        ("protagonist_card", "主角卡.md"),
    ]:
        content = settings_data.get(key, "")
        if content:
            path = settings_dir / filename
            path.write_text(content, encoding="utf-8")
            written.append(str(path))

    return written


@router.get("", response_model=ProjectList)
async def list_projects(
    status_filter: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = select(Project).where(Project.owner_id == current_user.id)
    if status_filter:
        stmt = stmt.where(Project.status == status_filter)
    stmt = stmt.order_by(Project.updated_at.desc())

    result = await db.execute(stmt)
    projects = result.scalars().all()
    return ProjectList(items=[_project_public(p) for p in projects], total=len(projects))


@router.post("", response_model=ProjectPublic, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Build premise_json from wizard input
    premise = {
        "genre": body.genre or "",
        "hook": body.hook or body.description or "",
        "protagonist": body.protagonist or {},
        "world_building": body.world_building or {},
        "power_system": body.power_system or "",
        "golden_finger": body.golden_finger or "",
        "constraints": body.constraints or [],
        "target_words": body.target_words or 0,
        "target_chapters": body.target_chapters or 0,
    }

    # Generate root_dir
    slug = _slugify(body.title)
    data_root = settings.novelcraft_data_root
    root_dir = os.path.join(data_root, str(current_user.id), slug)

    # Create project in DB
    project = Project(
        title=body.title,
        description=body.description,
        genre=body.genre,
        owner_id=current_user.id,
        premise_json=json.dumps(premise, ensure_ascii=False),
        root_dir=root_dir,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    # Create directory skeleton
    _ensure_dir_skeleton(root_dir)

    # Generate settings files via InitAgent
    settings_data, settings_warnings = await _generate_settings_from_premise(premise, current_user.id, db)
    written_files = _write_settings_files(root_dir, settings_data)

    # Generate synopsis via ArchitectAgent
    synopsis_data, synopsis_warnings = await _generate_synopsis_from_premise(premise, current_user.id, db)
    all_warnings = settings_warnings + synopsis_warnings

    if synopsis_data:
        project.synopsis_json = json.dumps(synopsis_data, ensure_ascii=False)

    # Write synopsis as 总纲.md
    if synopsis_data:
        synopsis_text = synopsis_data.get("synopsis", "")
        if synopsis_text:
            outline_dir = Path(root_dir) / "大纲"
            outline_dir.mkdir(parents=True, exist_ok=True)
            synopsis_md = f"# {synopsis_data.get('title', body.title)}\n\n"
            synopsis_md += f"**题材**：{synopsis_data.get('genre', premise.get('genre', ''))}\n\n"
            synopsis_md += f"**核心卖点**：{synopsis_data.get('hook', premise.get('hook', ''))}\n\n"
            synopsis_md += f"## 故事概述\n\n{synopsis_text}\n\n"
            synopsis_md += "## 分卷规划\n\n"
            for vol in synopsis_data.get("volumes", []):
                synopsis_md += f"- **第{vol.get('num', '?')}卷 {vol.get('title', '')}**：{vol.get('summary', '')}（{vol.get('target_chapters', '?')}章）\n"
            (outline_dir / "总纲.md").write_text(synopsis_md, encoding="utf-8")
            written_files.append(str(outline_dir / "总纲.md"))

    # Write idea_bank.json
    idea_bank = {
        "genre": premise.get("genre", ""),
        "hook": premise.get("hook", ""),
        "protagonist": premise.get("protagonist", {}),
        "golden_finger": premise.get("golden_finger", ""),
        "constraints": premise.get("constraints", []),
        "target_words": premise.get("target_words", 0),
        "target_chapters": premise.get("target_chapters", 0),
        "created_at": project.created_at.isoformat() if project.created_at else "",
    }
    novelcraft_dir = Path(root_dir) / ".novelcraft"
    novelcraft_dir.mkdir(parents=True, exist_ok=True)
    (novelcraft_dir / "idea_bank.json").write_text(
        json.dumps(idea_bank, ensure_ascii=False, indent=2)
    )

    # Save MASTER_SETTING
    ss = StorySystem(root_dir)
    ss.save_master_setting({
        "title": body.title,
        "genre": premise.get("genre", ""),
        "hook": premise.get("hook", ""),
        "protagonist": premise.get("protagonist", {}),
        "world_building": premise.get("world_building", {}),
        "power_system": premise.get("power_system", ""),
        "golden_finger": premise.get("golden_finger", ""),
        "constraints": premise.get("constraints", []),
        "synopsis": synopsis_data.get("synopsis", "") if synopsis_data else "",
        "volumes": synopsis_data.get("volumes", []) if synopsis_data else [],
        "settings_files": written_files,
        "created_at": project.created_at.isoformat() if project.created_at else "",
    })

    # Fire workflow trigger: onProjectCreate
    try:
        from app.workflows.engine import WorkflowEngine, WorkflowTrigger
        wf = WorkflowEngine()
        await wf.fire(WorkflowTrigger.ON_PROJECT_CREATE, {
            "project_id": project.id,
            "title": project.title,
            "user_id": str(current_user.id),
        })
    except Exception:
        pass

    await db.commit()
    return _project_public(project, warnings=all_warnings)


@router.get("/{project_id}", response_model=ProjectPublic)
async def get_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await _get_owned_project(project_id, current_user.id, db)
    return _project_public(project)


@router.patch("/{project_id}", response_model=ProjectPublic)
async def update_project(
    project_id: str,
    body: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await _get_owned_project(project_id, current_user.id, db)

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    await db.commit()
    await db.refresh(project)
    return _project_public(project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = await _get_owned_project(project_id, current_user.id, db)
    await db.delete(project)
    await db.commit()


class ImportScanRequest(BaseModel):
    source_path: str


class ImportExecuteRequest(BaseModel):
    source_path: str
    title: str | None = None


@router.post("/import/scan")
async def scan_import(
    body: ImportScanRequest,
    current_user: User = Depends(get_current_user),
):
    """Scan a local directory for import compatibility."""
    from app.services.import_project import scan_directory

    result = scan_directory(body.source_path)
    return {
        "valid": result.valid,
        "source_path": result.source_path,
        "title": result.title,
        "errors": result.errors,
        "chapter_count": len(result.chapters),
        "settings_count": len(result.settings_files),
        "has_synopsis": bool(result.synopsis_raw),
        "has_story_system": len(result.story_system_files) > 0,
        "has_webnovel": len(result.webnovel_files) > 0,
        "chapters_preview": [{"number": c["number"], "title": c["title"], "word_count": c["word_count"]} for c in result.chapters[:5]],
        "settings_preview": [s["name"] for s in result.settings_files],
    }


@router.post("/import", response_model=ProjectPublic, status_code=status.HTTP_201_CREATED)
async def import_project(
    body: ImportExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import a project from a local directory (cyDemo/WW style)."""
    from app.services.import_project import scan_directory, copy_to_project
    from app.models.chapter import Chapter as ChapterModel, calculate_word_count
    from app.models.card import Card

    scan = scan_directory(body.source_path)
    if not scan.valid:
        raise HTTPException(status_code=400, detail=f"目录无效: {'; '.join(scan.errors)}")

    title = body.title or scan.title or "导入项目"
    slug = _slugify(title)
    data_root = settings.novelcraft_data_root
    root_dir = os.path.join(data_root, str(current_user.id), slug)

    # Create project
    project = Project(
        title=title,
        description=f"从 {body.source_path} 导入",
        genre="",
        owner_id=current_user.id,
        root_dir=root_dir,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)

    # Create directory skeleton and copy files
    _ensure_dir_skeleton(root_dir)
    try:
        copy_to_project(scan, root_dir)
    except Exception as e:
        logger.exception("File copy failed during import")
        raise HTTPException(status_code=500, detail=f"文件复制失败: {e}")

    # Create chapters in DB
    for ch in scan.chapters:
        chapter = ChapterModel(
            project_id=project.id,
            title=ch["title"],
            number=ch["number"],
            content=ch["content"],
            word_count=calculate_word_count(ch["content"]),
            status="accepted",
        )
        db.add(chapter)

    # Create cards from settings files
    for sf in scan.settings_files:
        card = Card(
            project_id=project.id,
            card_type="setting",
            label=sf["name"],
            content={"text": sf["content"], "filename": sf["filename"]},
        )
        db.add(card)

    # Parse synopsis
    if scan.synopsis_raw:
        project.synopsis_json = json.dumps(
            {"synopsis": scan.synopsis_raw, "title": title},
            ensure_ascii=False,
        )

    # Initialize Story System from imported files
    try:
        ss = StorySystem(root_dir)
        imported_master_path = Path(root_dir) / ".story-system" / "MASTER_SETTING.json"
        if imported_master_path.exists():
            existing = json.loads(imported_master_path.read_text(encoding="utf-8"))
            ss.save_master_setting(existing)
        else:
            ss.save_master_setting({
                "title": title,
                "imported_from": body.source_path,
                "chapters_count": len(scan.chapters),
                "created_at": project.created_at.isoformat() if project.created_at else "",
            })
    except Exception:
        logger.exception("StorySystem init failed during import")

    await db.commit()
    return _project_public(project)


async def _get_owned_project(project_id: str, user_id: str, db: AsyncSession) -> Project:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == user_id)
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _project_public(p: Project, warnings: list[str] | None = None) -> ProjectPublic:
    return ProjectPublic(
        id=p.id,
        title=p.title,
        description=p.description,
        genre=p.genre,
        status=p.status,
        owner_id=p.owner_id,
        synopsis_json=p.synopsis_json,
        root_dir=p.root_dir,
        warnings=warnings or [],
        created_at=p.created_at.isoformat(),
        updated_at=p.updated_at.isoformat(),
    )
