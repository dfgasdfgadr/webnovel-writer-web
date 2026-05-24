"""Tests for architect API endpoints."""
import json
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.agents.llm import LLMProvider, LLMResponse


async def _create_project(async_client: AsyncClient, auth_headers: dict, title: str = "Test Project") -> str:
    resp = await async_client.post("/api/v1/projects", json={"title": title}, headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()["id"]


MOCK_SYNOPSIS = {
    "title": "测试书名",
    "genre": "玄幻",
    "hook": "废柴逆袭",
    "synopsis": "一个少年从平凡走向巅峰的故事。",
    "volumes": [{"num": 1, "title": "觉醒", "summary": "主角觉醒力量", "target_chapters": 50}],
}

MOCK_OUTLINE = {
    "chapter_num": 1,
    "title": "第一章·觉醒",
    "outline": "主角在试炼中觉醒了隐藏的血脉力量。",
    "must_cover_nodes": ["血脉觉醒场景", "第一次使用力量"],
    "forbidden_zones": ["不能写主角直接无敌"],
    "key_characters": [{"name": "主角", "role_in_chapter": "觉醒者"}],
    "target_words": 3000,
}


@pytest.fixture(autouse=True)
def _patch_llm():
    """Mock LLMProvider to avoid real API calls in architect tests."""
    mock_response = LLMResponse(
        content=json.dumps({"genre": "玄幻", "hook": "废柴逆袭"}),
        token_input=50,
        token_output=100,
    )

    mock_llm = MagicMock(spec=LLMProvider)
    mock_llm.api_key = "mock-key"
    mock_llm.base_url = "http://mock"

    async def mock_chat(messages, temperature=0.7):
        # Return appropriate mock data based on the request content
        content = messages[1].content if len(messages) > 1 else ""
        if "总纲" in content or "前提" in content or "synopsis" in content.lower() or "premise" in content.lower():
            return LLMResponse(content=json.dumps(MOCK_SYNOPSIS, ensure_ascii=False), token_input=50, token_output=100)
        elif "章纲" in content or "outline" in content.lower() or "volume" in content.lower():
            return LLMResponse(content=json.dumps(MOCK_OUTLINE, ensure_ascii=False), token_input=50, token_output=100)
        return LLMResponse(content=json.dumps({}), token_input=50, token_output=100)

    mock_llm.chat = mock_chat

    async def mock_for_user(user_id, db_session=None):
        return mock_llm

    with patch("app.routers.agents.LLMProvider.for_user", side_effect=mock_for_user):
        yield


class TestArchitectSynopsis:
    async def test_generate_synopsis_success(self, async_client: AsyncClient, auth_headers: dict):
        pid = await _create_project(async_client, auth_headers)

        resp = await async_client.post(
            f"/api/v1/agents/architect/synopsis/{pid}",
            json={
                "genre": "玄幻",
                "hook": "废柴逆袭",
                "protagonist": {"name": "测试"},
                "world_building": {"description": "测试世界"},
                "power_system": "修炼",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == MOCK_SYNOPSIS["title"]
        assert data["genre"] == MOCK_SYNOPSIS["genre"]

    async def test_generate_synopsis_unauthorized(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/agents/architect/synopsis/fake-id",
            json={"genre": "玄幻"},
        )
        assert resp.status_code == 401

    async def test_generate_synopsis_other_user_project(self, async_client: AsyncClient, auth_headers: dict):
        pid = await _create_project(async_client, auth_headers)
        # Register another user
        await async_client.post("/api/v1/auth/register", json={
            "username": "other", "password": "other123", "display_name": "Other",
        })
        other_login = await async_client.post("/api/v1/auth/login", data={
            "username": "other", "password": "other123",
        })
        other_headers = {"Authorization": f"Bearer {other_login.json()['access_token']}"}

        resp = await async_client.post(
            f"/api/v1/agents/architect/synopsis/{pid}",
            json={"genre": "玄幻"},
            headers=other_headers,
        )
        assert resp.status_code == 403

    async def test_synopsis_persists_to_project(self, async_client: AsyncClient, auth_headers: dict):
        pid = await _create_project(async_client, auth_headers)

        await async_client.post(
            f"/api/v1/agents/architect/synopsis/{pid}",
            json={"genre": "玄幻", "hook": "废柴逆袭"},
            headers=auth_headers,
        )

        # Verify project now has synopsis_json
        resp = await async_client.get(f"/api/v1/projects/{pid}", headers=auth_headers)
        assert resp.status_code == 200
        project = resp.json()
        assert project.get("synopsis_json") is not None
        parsed = json.loads(project["synopsis_json"])
        assert parsed["title"] == MOCK_SYNOPSIS["title"]


class TestArchitectOutline:
    async def test_generate_outline_success(self, async_client: AsyncClient, auth_headers: dict):
        pid = await _create_project(async_client, auth_headers)

        resp = await async_client.post(
            f"/api/v1/agents/architect/outline/{pid}",
            json={
                "volume": {"title": "第一卷", "summary": "觉醒之旅"},
                "chapter_num": 1,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["chapter_num"] == 1
        assert data["title"] == MOCK_OUTLINE["title"]
        assert len(data["must_cover_nodes"]) == 2

    async def test_generate_outline_auto_creates_chapter(self, async_client: AsyncClient, auth_headers: dict):
        pid = await _create_project(async_client, auth_headers)

        await async_client.post(
            f"/api/v1/agents/architect/outline/{pid}",
            json={"volume": {}, "chapter_num": 5},
            headers=auth_headers,
        )

        resp = await async_client.get(f"/api/v1/projects/{pid}/chapters", headers=auth_headers)
        data = resp.json()
        assert data["total"] >= 1
        chapters = data["items"]
        ch5 = [c for c in chapters if c["number"] == 5]
        assert len(ch5) == 1
        assert ch5[0]["outline"] == MOCK_OUTLINE["outline"]

    async def test_generate_outline_updates_existing_chapter(self, async_client: AsyncClient, auth_headers: dict):
        pid = await _create_project(async_client, auth_headers)
        # Create chapter first
        await async_client.post(
            f"/api/v1/projects/{pid}/chapters",
            json={"title": "Old Title", "number": 1, "content": "Old content"},
            headers=auth_headers,
        )

        await async_client.post(
            f"/api/v1/agents/architect/outline/{pid}",
            json={"volume": {}, "chapter_num": 1},
            headers=auth_headers,
        )

        resp = await async_client.get(f"/api/v1/projects/{pid}/chapters", headers=auth_headers)
        chapters = resp.json()["items"]
        ch1 = [c for c in chapters if c["number"] == 1][0]
        assert ch1["outline"] == MOCK_OUTLINE["outline"]


class TestArchitectBatchOutline:
    async def test_batch_outline_success(self, async_client: AsyncClient, auth_headers: dict):
        pid = await _create_project(async_client, auth_headers)

        resp = await async_client.post(
            f"/api/v1/agents/architect/outline/{pid}/batch",
            json={
                "volume": {"title": "第一卷"},
                "start_chapter": 1,
                "end_chapter": 3,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert data["completed"] == 3
        assert data["failed"] == 0
        assert len(data["results"]) == 3

    async def test_batch_outline_invalid_range(self, async_client: AsyncClient, auth_headers: dict):
        pid = await _create_project(async_client, auth_headers)

        resp = await async_client.post(
            f"/api/v1/agents/architect/outline/{pid}/batch",
            json={"start_chapter": 5, "end_chapter": 1},
            headers=auth_headers,
        )
        assert resp.status_code == 400


class TestArchitectVolumePlan:
    async def test_volume_plan_success(self, async_client: AsyncClient, auth_headers: dict):
        pid = await _create_project(async_client, auth_headers)

        # First generate synopsis so it's persisted
        await async_client.post(
            f"/api/v1/agents/architect/synopsis/{pid}",
            json={"genre": "玄幻"},
            headers=auth_headers,
        )

        resp = await async_client.post(
            f"/api/v1/agents/architect/volume-plan/{pid}",
            json={
                "total_chapters": 100,
                "chapters_per_volume": 50,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_volumes"] == 2
        assert len(data["volumes"]) == 2
        # First volume should have detailed chapters
        assert data["volumes"][0]["chapters"] is not None

    async def test_volume_plan_requires_auth(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/agents/architect/volume-plan/fake-id",
            json={"total_chapters": 100, "chapters_per_volume": 50},
        )
        assert resp.status_code == 401
