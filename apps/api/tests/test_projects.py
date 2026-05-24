import pytest
from httpx import AsyncClient


class TestProjectsCRUD:
    async def test_create_project(self, async_client: AsyncClient, auth_headers: dict):
        resp = await async_client.post("/api/v1/projects", json={
            "title": "My Novel",
            "description": "A test novel",
            "genre": "fantasy",
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "My Novel"
        assert data["genre"] == "fantasy"
        assert data["status"] == "active"
        assert "id" in data

    async def test_list_projects_empty(self, async_client: AsyncClient, auth_headers: dict):
        resp = await async_client.get("/api/v1/projects", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    async def test_list_projects(self, async_client: AsyncClient, auth_headers: dict):
        await async_client.post("/api/v1/projects", json={"title": "Novel A"}, headers=auth_headers)
        await async_client.post("/api/v1/projects", json={"title": "Novel B"}, headers=auth_headers)

        resp = await async_client.get("/api/v1/projects", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    async def test_get_project(self, async_client: AsyncClient, auth_headers: dict):
        create_resp = await async_client.post("/api/v1/projects", json={
            "title": "Target Novel",
        }, headers=auth_headers)
        pid = create_resp.json()["id"]

        resp = await async_client.get(f"/api/v1/projects/{pid}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Target Novel"

    async def test_get_project_not_found(self, async_client: AsyncClient, auth_headers: dict):
        resp = await async_client.get("/api/v1/projects/nonexistent-id", headers=auth_headers)
        assert resp.status_code == 404

    async def test_update_project(self, async_client: AsyncClient, auth_headers: dict):
        create_resp = await async_client.post("/api/v1/projects", json={
            "title": "Old Title",
        }, headers=auth_headers)
        pid = create_resp.json()["id"]

        resp = await async_client.patch(f"/api/v1/projects/{pid}", json={
            "title": "New Title",
        }, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["title"] == "New Title"

    async def test_delete_project(self, async_client: AsyncClient, auth_headers: dict):
        create_resp = await async_client.post("/api/v1/projects", json={
            "title": "To Delete",
        }, headers=auth_headers)
        pid = create_resp.json()["id"]

        resp = await async_client.delete(f"/api/v1/projects/{pid}", headers=auth_headers)
        assert resp.status_code == 204

        get_resp = await async_client.get(f"/api/v1/projects/{pid}", headers=auth_headers)
        assert get_resp.status_code == 404

    async def test_list_projects_requires_auth(self, async_client: AsyncClient):
        resp = await async_client.get("/api/v1/projects")
        assert resp.status_code == 401

    async def test_create_project_requires_auth(self, async_client: AsyncClient):
        resp = await async_client.post("/api/v1/projects", json={"title": "X"})
        assert resp.status_code == 401


class TestProjectOwnerIsolation:
    async def test_cannot_see_other_user_project(self, async_client: AsyncClient, auth_headers: dict):
        # Create project as testuser
        create_resp = await async_client.post("/api/v1/projects", json={
            "title": "Secret Project",
        }, headers=auth_headers)
        pid = create_resp.json()["id"]

        # Register a second user and try to access
        await async_client.post("/api/v1/auth/register", json={
            "username": "otheruser",
            "password": "otherpass123",
        })
        login_resp = await async_client.post("/api/v1/auth/login", data={
            "username": "otheruser",
            "password": "otherpass123",
        })
        other_token = login_resp.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Other user cannot get
        resp = await async_client.get(f"/api/v1/projects/{pid}", headers=other_headers)
        assert resp.status_code == 404

        # Other user cannot update
        resp = await async_client.patch(f"/api/v1/projects/{pid}", json={
            "title": "Hacked",
        }, headers=other_headers)
        assert resp.status_code == 404

        # Other user cannot delete
        resp = await async_client.delete(f"/api/v1/projects/{pid}", headers=other_headers)
        assert resp.status_code == 404

        # Other user's list is empty
        resp = await async_client.get("/api/v1/projects", headers=other_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0
