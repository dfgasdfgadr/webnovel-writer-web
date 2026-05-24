"""Tests for MiroFish simulation endpoints."""
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient


class TestSimulationHealth:
    async def test_health_returns_unavailable(self, async_client: AsyncClient):
        with patch("app.routers.simulations._check_mirofish", return_value=False):
            resp = await async_client.get("/api/v1/simulations/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["available"] is False


class TestSimulationCRUD:
    async def test_create_sim_mirofish_unavailable(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        # Create a project first
        proj_resp = await async_client.post(
            "/api/v1/projects",
            headers=auth_headers,
            json={"title": "Sim Test Project"},
        )
        assert proj_resp.status_code == 201
        project_id = proj_resp.json()["id"]

        with patch("app.routers.simulations._check_mirofish", return_value=False):
            resp = await async_client.post(
                "/api/v1/simulations",
                headers=auth_headers,
                json={
                    "project_id": project_id,
                    "mode": "pre_chapter",
                    "sim_brief": "Test what happens if the hero enters the cave.",
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["mode"] == "pre_chapter"
        assert data["status"] == "failed"
        assert data["mirofish_available"] is False
        assert "不可用" in data.get("error_message", "")

    async def test_create_sim_unauthorized(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/simulations",
            json={
                "project_id": "any",
                "mode": "pre_chapter",
                "sim_brief": "test",
            },
        )
        assert resp.status_code == 401

    async def test_create_sim_wrong_project_owner(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        # Register another user who owns a project
        await async_client.post("/api/v1/auth/register", json={
            "username": "simuser", "password": "password",
        })
        login = await async_client.post("/api/v1/auth/login", data={
            "username": "simuser", "password": "password",
        })
        sim_token = login.json()["access_token"]
        sim_headers = {"Authorization": f"Bearer {sim_token}"}

        proj_resp = await async_client.post(
            "/api/v1/projects", headers=sim_headers,
            json={"title": "Sim Owner Project"},
        )
        project_id = proj_resp.json()["id"]

        # Test user tries to create sim on simuser's project
        resp = await async_client.post(
            "/api/v1/simulations",
            headers=auth_headers,
            json={
                "project_id": project_id,
                "mode": "pre_chapter",
                "sim_brief": "test",
            },
        )
        assert resp.status_code == 403

    async def test_list_simulations_empty(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        proj_resp = await async_client.post(
            "/api/v1/projects", headers=auth_headers,
            json={"title": "List Sim Project"},
        )
        project_id = proj_resp.json()["id"]

        resp = await async_client.get(
            f"/api/v1/simulations?project_id={project_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_get_simulation_not_found(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        resp = await async_client.get(
            "/api/v1/simulations/nonexistent-id",
            headers=auth_headers,
        )
        assert resp.status_code == 404
