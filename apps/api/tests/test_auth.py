import pytest
from httpx import AsyncClient


class TestAuthRegister:
    async def test_register_success(self, async_client: AsyncClient):
        resp = await async_client.post("/api/v1/auth/register", json={
            "username": "newuser",
            "password": "secret123",
            "display_name": "New User",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newuser"
        assert data["display_name"] == "New User"
        assert "id" in data
        assert "hashed_password" not in data  # not exposed

    async def test_register_duplicate_username(self, async_client: AsyncClient):
        payload = {"username": "dup", "password": "secret123"}
        resp1 = await async_client.post("/api/v1/auth/register", json=payload)
        assert resp1.status_code == 201

        resp2 = await async_client.post("/api/v1/auth/register", json=payload)
        assert resp2.status_code == 400
        assert "already taken" in resp2.json()["detail"]

    async def test_register_short_username(self, async_client: AsyncClient):
        resp = await async_client.post("/api/v1/auth/register", json={
            "username": "ab",
            "password": "secret123",
        })
        assert resp.status_code == 422

    async def test_register_short_password(self, async_client: AsyncClient):
        resp = await async_client.post("/api/v1/auth/register", json={
            "username": "validuser",
            "password": "12345",
        })
        assert resp.status_code == 422


class TestAuthLogin:
    async def test_login_success(self, async_client: AsyncClient):
        await async_client.post("/api/v1/auth/register", json={
            "username": "loginuser",
            "password": "testpass123",
        })

        resp = await async_client.post("/api/v1/auth/login", data={
            "username": "loginuser",
            "password": "testpass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, async_client: AsyncClient):
        await async_client.post("/api/v1/auth/register", json={
            "username": "pwuser",
            "password": "correctpw",
        })

        resp = await async_client.post("/api/v1/auth/login", data={
            "username": "pwuser",
            "password": "wrongpw",
        })
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, async_client: AsyncClient):
        resp = await async_client.post("/api/v1/auth/login", data={
            "username": "nobody",
            "password": "whatever",
        })
        assert resp.status_code == 401


class TestAuthMe:
    async def test_me_authenticated(self, async_client: AsyncClient):
        await async_client.post("/api/v1/auth/register", json={
            "username": "meuser",
            "password": "testpass123",
        })
        login_resp = await async_client.post("/api/v1/auth/login", data={
            "username": "meuser",
            "password": "testpass123",
        })
        token = login_resp.json()["access_token"]

        resp = await async_client.get("/api/v1/auth/me", headers={
            "Authorization": f"Bearer {token}",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "meuser"

    async def test_me_no_token_returns_401(self, async_client: AsyncClient):
        resp = await async_client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_me_invalid_token_returns_401(self, async_client: AsyncClient):
        resp = await async_client.get("/api/v1/auth/me", headers={
            "Authorization": "Bearer invalid-token-here",
        })
        assert resp.status_code == 401
