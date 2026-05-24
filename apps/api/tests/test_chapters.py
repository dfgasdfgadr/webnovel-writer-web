import pytest
from httpx import AsyncClient


async def _create_project(async_client: AsyncClient, auth_headers: dict, title: str = "Test Project") -> str:
    resp = await async_client.post("/api/v1/projects", json={"title": title}, headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()["id"]


class TestChaptersCRUD:
    async def test_create_chapter(self, async_client: AsyncClient, auth_headers: dict):
        pid = await _create_project(async_client, auth_headers)

        resp = await async_client.post(f"/api/v1/projects/{pid}/chapters", json={
            "title": "Chapter 1",
            "number": 1,
            "content": "第一章内容",
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Chapter 1"
        assert data["number"] == 1
        assert data["content"] == "第一章内容"
        assert data["word_count"] > 0
        assert data["status"] == "draft"

    async def test_list_chapters_empty(self, async_client: AsyncClient, auth_headers: dict):
        pid = await _create_project(async_client, auth_headers)

        resp = await async_client.get(f"/api/v1/projects/{pid}/chapters", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_chapters_ordered(self, async_client: AsyncClient, auth_headers: dict):
        pid = await _create_project(async_client, auth_headers)
        await async_client.post(f"/api/v1/projects/{pid}/chapters", json={
            "title": "Ch2", "number": 2,
        }, headers=auth_headers)
        await async_client.post(f"/api/v1/projects/{pid}/chapters", json={
            "title": "Ch1", "number": 1,
        }, headers=auth_headers)

        resp = await async_client.get(f"/api/v1/projects/{pid}/chapters", headers=auth_headers)
        data = resp.json()
        assert data["total"] == 2
        assert data["items"][0]["number"] == 1
        assert data["items"][1]["number"] == 2

    async def test_get_chapter(self, async_client: AsyncClient, auth_headers: dict):
        pid = await _create_project(async_client, auth_headers)
        create_resp = await async_client.post(f"/api/v1/projects/{pid}/chapters", json={
            "title": "Target Chapter", "number": 1,
        }, headers=auth_headers)
        cid = create_resp.json()["id"]

        resp = await async_client.get(f"/api/v1/projects/{pid}/chapters/{cid}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Target Chapter"

    async def test_get_chapter_not_found(self, async_client: AsyncClient, auth_headers: dict):
        pid = await _create_project(async_client, auth_headers)
        resp = await async_client.get(f"/api/v1/projects/{pid}/chapters/nonexistent", headers=auth_headers)
        assert resp.status_code == 404

    async def test_update_chapter(self, async_client: AsyncClient, auth_headers: dict):
        pid = await _create_project(async_client, auth_headers)
        create_resp = await async_client.post(f"/api/v1/projects/{pid}/chapters", json={
            "title": "Old Title", "number": 1, "content": "旧内容",
        }, headers=auth_headers)
        cid = create_resp.json()["id"]

        resp = await async_client.patch(f"/api/v1/projects/{pid}/chapters/{cid}", json={
            "title": "New Title",
            "content": "新的内容_更多文字",
        }, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "New Title"
        assert data["content"] == "新的内容_更多文字"
        assert data["word_count"] > 0

    async def test_delete_chapter(self, async_client: AsyncClient, auth_headers: dict):
        pid = await _create_project(async_client, auth_headers)
        create_resp = await async_client.post(f"/api/v1/projects/{pid}/chapters", json={
            "title": "To Delete", "number": 1,
        }, headers=auth_headers)
        cid = create_resp.json()["id"]

        resp = await async_client.delete(f"/api/v1/projects/{pid}/chapters/{cid}", headers=auth_headers)
        assert resp.status_code == 204

        get_resp = await async_client.get(f"/api/v1/projects/{pid}/chapters/{cid}", headers=auth_headers)
        assert get_resp.status_code == 404

    async def test_chapters_require_auth(self, async_client: AsyncClient):
        resp = await async_client.get("/api/v1/projects/any-id/chapters")
        assert resp.status_code == 401

    async def test_create_chapter_without_content(self, async_client: AsyncClient, auth_headers: dict):
        pid = await _create_project(async_client, auth_headers)
        resp = await async_client.post(f"/api/v1/projects/{pid}/chapters", json={
            "title": "Empty Chapter", "number": 1,
        }, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["word_count"] == 0
        assert resp.json()["content"] == ""

    async def test_cannot_access_chapters_of_others_project(self, async_client: AsyncClient, auth_headers: dict):
        pid = await _create_project(async_client, auth_headers)
        await async_client.post(f"/api/v1/projects/{pid}/chapters", json={
            "title": "My Chapter", "number": 1,
        }, headers=auth_headers)

        # Register second user
        await async_client.post("/api/v1/auth/register", json={
            "username": "intruder", "password": "intruder123",
        })
        login_resp = await async_client.post("/api/v1/auth/login", data={
            "username": "intruder", "password": "intruder123",
        })
        other_headers = {"Authorization": f"Bearer {login_resp.json()['access_token']}"}

        resp = await async_client.get(f"/api/v1/projects/{pid}/chapters", headers=other_headers)
        assert resp.status_code == 404
