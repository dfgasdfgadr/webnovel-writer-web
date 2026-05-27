"""Track 0 trust repair tests — P6-Q01~Q04.

P6-Q01: Chinese filename zip export (Content-Disposition RFC 5987)
P6-Q02: Export includes .story-system directory
P6-Q03: Workflow handler registration (onChapterAccepted not skipped)
P6-Q04: WorkflowEngine singleton/shared state
"""

import json
import os
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


# --- P6-Q01: Chinese filename export ---

@pytest.mark.asyncio
async def test_export_chinese_title_returns_200(async_client: AsyncClient, auth_headers: dict):
    """Chinese book title export must not 500 (latin-1 codec error)."""
    # Create project with Chinese title
    resp = await async_client.post("/api/v1/projects", json={
        "title": "验收测试中文书名",
        "description": "test",
        "genre": "玄幻",
    }, headers=auth_headers)
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    resp = await async_client.get(f"/api/v1/projects/{project_id}/export", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"

    # Verify Content-Disposition uses RFC 5987 filename*
    cd = resp.headers.get("content-disposition", "")
    assert "filename*=UTF-8''" in cd, f"Expected RFC 5987 encoding in Content-Disposition, got: {cd}"

    # Verify zip is valid
    import io
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    names = zf.namelist()
    assert len(names) > 0
    zf.close()


@pytest.mark.asyncio
async def test_export_english_title_returns_200(async_client: AsyncClient, auth_headers: dict):
    """English title export still works (regression)."""
    resp = await async_client.post("/api/v1/projects", json={
        "title": "ExportTestP6",
        "description": "test",
        "genre": "fantasy",
    }, headers=auth_headers)
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    resp = await async_client.get(f"/api/v1/projects/{project_id}/export", headers=auth_headers)
    assert resp.status_code == 200
    cd = resp.headers.get("content-disposition", "")
    # filename*=UTF-8'' contains the actual slug name; filename= has ASCII fallback
    assert "exporttestp6.zip" in cd.lower() or "ExportTestP6.zip" in cd


# --- P6-Q02: Export includes .story-system ---

@pytest.mark.asyncio
async def test_export_includes_story_system(async_client: AsyncClient, auth_headers: dict):
    """Exported zip must contain .story-system/ directory with MASTER_SETTING.json."""
    resp = await async_client.post("/api/v1/projects", json={
        "title": "StorySystemExport",
        "description": "test",
        "genre": "fantasy",
    }, headers=auth_headers)
    assert resp.status_code == 201
    project_id = resp.json()["id"]

    resp = await async_client.get(f"/api/v1/projects/{project_id}/export", headers=auth_headers)
    assert resp.status_code == 200

    import io
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    names = zf.namelist()

    # Must include .story-system/MASTER_SETTING.json
    story_system_files = [n for n in names if ".story-system" in n]
    assert len(story_system_files) > 0, f"Expected .story-system in zip, got: {names}"
    assert any("MASTER_SETTING" in n for n in names), f"Expected MASTER_SETTING.json in zip, got: {names}"

    # Must NOT include .novelcraft/
    assert not any(".novelcraft" in n for n in names), f".novelcraft should be excluded from zip, got: {names}"
    zf.close()


@pytest.mark.asyncio
async def test_export_import_roundtrip(async_client: AsyncClient, auth_headers: dict):
    """Export then import should preserve project data."""
    # Create project
    resp = await async_client.post("/api/v1/projects", json={
        "title": "RoundTripTest",
        "description": "roundtrip",
        "genre": "scifi",
    }, headers=auth_headers)
    assert resp.status_code == 201
    original = resp.json()
    original_id = original["id"]
    root_dir = original.get("root_dir")

    # Add a chapter with outline (import requires 正文/ with chapters)
    resp = await async_client.post(
        f"/api/v1/projects/{original_id}/chapters",
        json={
            "title": "第一章",
            "number": 1,
            "content": "测试正文内容。",
            "outline": "章纲：主角登场。",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201

    # Export
    resp = await async_client.get(f"/api/v1/projects/{original_id}/export", headers=auth_headers)
    assert resp.status_code == 200
    zip_bytes = resp.content

    import io
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    names = zf.namelist()
    assert any(".story-system" in n and "MASTER_SETTING" in n for n in names)
    assert any("正文" in n for n in names)
    assert any("设定集" in n for n in names)
    zf.close()

    # Import via upload
    resp = await async_client.post(
        "/api/v1/projects/import/upload",
        files={"file": ("RoundTripTest.zip", io.BytesIO(zip_bytes), "application/zip")},
        headers=auth_headers,
    )
    assert resp.status_code == 201, f"Import failed: {resp.text}"
    imported = resp.json()
    imported_id = imported["id"]
    assert imported_id != original_id
    assert imported["title"] == "RoundTripTest"

    # Verify chapter content restored
    resp = await async_client.get(
        f"/api/v1/projects/{imported_id}/chapters",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    chapters = resp.json()["items"]
    assert len(chapters) >= 1
    assert "测试正文内容" in chapters[0]["content"]

    # Verify Story System on disk
    imported_root = imported.get("root_dir")
    assert imported_root, "Imported project should have root_dir"
    master_setting = Path(imported_root) / ".story-system" / "MASTER_SETTING.json"
    assert master_setting.exists(), "MASTER_SETTING.json should exist after import"

    # Verify settings directory copied
    if root_dir:
        settings_src = Path(root_dir) / "设定集"
        settings_dst = Path(imported_root) / "设定集"
        if settings_src.exists():
            assert settings_dst.exists(), "设定集/ should be restored after import"


# --- P6-Q03: Workflow handler registration ---

@pytest.mark.asyncio
async def test_workflow_engine_has_handlers():
    """WorkflowEngine from get_workflow_engine() must have sim handler registered."""
    from app.workflows import get_workflow_engine, reset_workflow_engine

    reset_workflow_engine()
    engine = get_workflow_engine()
    assert "sim" in engine.handlers, f"Expected 'sim' handler, got: {list(engine.handlers.keys())}"
    assert "notify" in engine.handlers
    assert "git_backup" in engine.handlers
    reset_workflow_engine()


@pytest.mark.asyncio
async def test_workflow_fire_sim_not_skipped():
    """onChapterAccepted sim action should NOT be skipped when handler is registered."""
    from app.workflows import get_workflow_engine, reset_workflow_engine, WorkflowTrigger

    reset_workflow_engine()
    engine = get_workflow_engine()

    results = await engine.fire(WorkflowTrigger.ON_CHAPTER_ACCEPTED, {
        "chapter_id": "test-ch",
        "project_id": "test-proj",
        "chapter_num": 1,
        "project_root": "/tmp/test",
        "status": "accepted",
    })

    # Should have results for the sim action
    assert len(results) > 0, "Expected at least one workflow result"
    sim_results = [r for r in results if r.get("result", {}).get("action") == "sim"]
    assert len(sim_results) > 0, f"Expected sim action result, got: {results}"
    for r in sim_results:
        assert r.get("result", {}).get("status") != "skipped", f"Sim action should not be skipped: {r}"

    reset_workflow_engine()


# --- P6-Q04: WorkflowEngine singleton/shared state ---

@pytest.mark.asyncio
async def test_workflow_engine_singleton():
    """get_workflow_engine() returns the same instance each call."""
    from app.workflows import get_workflow_engine, reset_workflow_engine

    reset_workflow_engine()
    e1 = get_workflow_engine()
    e2 = get_workflow_engine()
    assert e1 is e2, "Expected same WorkflowEngine instance"
    reset_workflow_engine()


@pytest.mark.asyncio
async def test_workflow_rule_toggle_persists():
    """Toggling a rule via set_rule_enabled persists on the shared engine."""
    from app.workflows import get_workflow_engine, reset_workflow_engine

    reset_workflow_engine()
    engine = get_workflow_engine()

    # Default: onChapterAccepted rule is enabled
    from app.workflows.engine import WorkflowTrigger
    rules = engine.get_rules_for_trigger(WorkflowTrigger.ON_CHAPTER_ACCEPTED)
    assert any(r.name == "章节通过后剧情推演" and r.enabled for r in rules)

    # Disable it
    found = engine.set_rule_enabled("章节通过后剧情推演", False)
    assert found is True

    # Verify disabled
    rules = engine.get_rules_for_trigger(WorkflowTrigger.ON_CHAPTER_ACCEPTED)
    assert not any(r.name == "章节通过后剧情推演" and r.enabled for r in rules)

    # Re-enable
    engine.set_rule_enabled("章节通过后剧情推演", True)
    rules = engine.get_rules_for_trigger(WorkflowTrigger.ON_CHAPTER_ACCEPTED)
    assert any(r.name == "章节通过后剧情推演" and r.enabled for r in rules)

    reset_workflow_engine()


@pytest.mark.asyncio
async def test_workflow_api_toggle_endpoint(async_client: AsyncClient, auth_headers: dict):
    """POST /plugins/workflows/{name}/toggle should update shared engine state."""
    resp = await async_client.post(
        "/api/v1/plugins/workflows/章节通过后剧情推演/toggle?enabled=false",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "章节通过后剧情推演"
    assert data["enabled"] is False

    # Verify via list endpoint
    resp = await async_client.get("/api/v1/plugins/workflows", headers=auth_headers)
    assert resp.status_code == 200
    rules = resp.json()["rules"]
    matched = [r for r in rules if r["name"] == "章节通过后剧情推演"]
    assert len(matched) == 1
    assert matched[0]["enabled"] is False

    # Re-enable for cleanup
    await async_client.post(
        "/api/v1/plugins/workflows/章节通过后剧情推演/toggle?enabled=true",
        headers=auth_headers,
    )
