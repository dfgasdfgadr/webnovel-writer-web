"""Tests for SSE draft streaming endpoint."""
import pytest
from httpx import AsyncClient


async def _create_project_with_chapter(async_client: AsyncClient, auth_headers: dict):
    project_resp = await async_client.post(
        "/api/v1/projects", json={"title": "Stream Test"}, headers=auth_headers
    )
    pid = project_resp.json()["id"]
    chapter_resp = await async_client.post(
        f"/api/v1/projects/{pid}/chapters",
        json={"title": "Ch1", "number": 1, "outline": "主角入职"},
        headers=auth_headers,
    )
    return pid, chapter_resp.json()["id"]


class TestStreamDraft:
    async def test_stream_requires_token(self, async_client: AsyncClient, auth_headers: dict):
        _, cid = await _create_project_with_chapter(async_client, auth_headers)
        resp = await async_client.get(f"/api/v1/agents/pipeline/{cid}/stream?outline=test")
        assert resp.status_code == 401

    async def test_stream_requires_outline(self, async_client: AsyncClient, auth_headers: dict):
        pid, _ = await _create_project_with_chapter(async_client, auth_headers)
        create_resp = await async_client.post(
            f"/api/v1/projects/{pid}/chapters",
            json={"title": "Empty", "number": 1},
            headers=auth_headers,
        )
        empty_cid = create_resp.json()["id"]
        token = auth_headers["Authorization"].split(" ", 1)[1]

        resp = await async_client.get(
            f"/api/v1/agents/pipeline/{empty_cid}/stream?token={token}&outline="
        )
        assert resp.status_code == 400

    async def test_stream_returns_error_event_without_api_key(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        _, cid = await _create_project_with_chapter(async_client, auth_headers)
        token = auth_headers["Authorization"].split(" ", 1)[1]
        resp = await async_client.get(
            f"/api/v1/agents/pipeline/{cid}/stream?token={token}&outline=主角入职",
        )
        assert resp.status_code == 200
        body = resp.text
        assert "error" in body or "未配置 LLM API Key" in body
