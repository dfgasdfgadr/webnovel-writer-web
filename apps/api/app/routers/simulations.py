"""Simulation endpoints for MiroFish integration.

Gracefully degrades when MiroFish is not available (no Docker).
"""
import json
import httpx
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.project import Project
from app.models.simulation import SimulationJob
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/simulations", tags=["simulations"])

MIROFISH_URL = "http://localhost:8081"


# --- Request/Response schemas ---

class CreateSimRequest(BaseModel):
    project_id: str
    chapter_id: str | None = None
    mode: str  # pre_chapter, branch_explore
    sim_brief: str
    chapter_texts: list[dict] = []
    checkpoint_id: str | None = None


class SimJobResponse(BaseModel):
    id: str
    project_id: str
    mode: str
    status: str
    progress: int
    mirofish_available: bool
    report: dict | None = None
    steps: list[dict] | None = None
    error_message: str | None = None
    created_at: str


async def _check_mirofish() -> bool:
    """Check if MiroFish sidecar is reachable."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{MIROFISH_URL}/health")
            return resp.status_code == 200
    except Exception:
        return False


def _job_to_response(job: SimulationJob) -> SimJobResponse:
    report = None
    if job.report_json:
        try:
            report = json.loads(job.report_json)
        except json.JSONDecodeError:
            pass
    steps = None
    if job.steps_json:
        try:
            steps = json.loads(job.steps_json)
        except json.JSONDecodeError:
            pass
    return SimJobResponse(
        id=job.id,
        project_id=job.project_id,
        mode=job.mode,
        status=job.status,
        progress=job.progress,
        mirofish_available=job.mirofish_available,
        report=report,
        steps=steps,
        error_message=job.error_message,
        created_at=job.created_at.isoformat() if job.created_at else "",
    )


@router.post("", response_model=SimJobResponse)
async def create_simulation(
    body: CreateSimRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new simulation job. Returns immediately with pending status."""
    project = await db.get(Project, body.project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    mirofish_ok = await _check_mirofish()

    job = SimulationJob(
        project_id=body.project_id,
        chapter_id=body.chapter_id,
        user_id=current_user.id,
        mode=body.mode,
        sim_brief=body.sim_brief,
        status="running" if mirofish_ok else "failed",
        progress=0,
        mirofish_available=mirofish_ok,
        checkpoint_id=body.checkpoint_id,
    )

    if not mirofish_ok:
        job.status = "failed"
        job.error_message = "MiroFish 服务不可用。请确保 Docker 已启动且 MiroFish Sidecar 正在运行。"
        job.progress = 100
    else:
        # Attempt to submit to MiroFish
        try:
            seed_packet = {
                "project_id": body.project_id,
                "sim_brief": body.sim_brief,
                "mode": body.mode,
                "chapter_texts": body.chapter_texts,
                "options": {
                    "checkpoint_id": body.checkpoint_id,
                    "max_sim_steps": 10,
                    "temperature": 0.7,
                },
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"{MIROFISH_URL}/api/v1/simulations",
                    json=seed_packet,
                    headers={"Content-Type": "application/json"},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    job.report_json = json.dumps(data, ensure_ascii=False)
                    job.steps_json = json.dumps(data.get("steps", []), ensure_ascii=False)
                    job.status = "completed"
                    job.progress = 100
                else:
                    job.status = "failed"
                    job.error_message = f"MiroFish returned {resp.status_code}: {resp.text[:200]}"
                    job.progress = 100
        except Exception as e:
            job.status = "failed"
            job.error_message = f"Failed to communicate with MiroFish: {str(e)[:200]}"
            job.progress = 100

    db.add(job)
    await db.commit()
    await db.refresh(job)
    return _job_to_response(job)


@router.get("/health")
async def mirofish_health():
    """Check MiroFish sidecar availability."""
    available = await _check_mirofish()
    return {"available": available, "url": MIROFISH_URL}


@router.get("/{sim_id}", response_model=SimJobResponse)
async def get_simulation(
    sim_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    job = await db.get(SimulationJob, sim_id)
    if not job or job.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Simulation not found")
    return _job_to_response(job)


@router.get("", response_model=list[SimJobResponse])
async def list_simulations(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await db.get(Project, project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(SimulationJob)
        .where(SimulationJob.project_id == project_id)
        .order_by(SimulationJob.created_at.desc())
        .limit(20)
    )
    jobs = result.scalars().all()
    return [_job_to_response(j) for j in jobs]
