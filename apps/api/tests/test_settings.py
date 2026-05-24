"""Tests for user LLM settings endpoints."""
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient


class TestLlmSettings:
    async def test_get_llm_settings_empty(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        resp = await async_client.get("/api/v1/settings/llm", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] != ""
        assert data["api_key_masked"] is None
        assert data["base_url"] is None
        assert data["model"] is None

    async def test_get_llm_settings_unauthorized(self, async_client: AsyncClient):
        resp = await async_client.get("/api/v1/settings/llm")
        assert resp.status_code == 401

    async def test_put_llm_settings_create(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        resp = await async_client.put(
            "/api/v1/settings/llm",
            headers=auth_headers,
            json={
                "api_key": "sk-test-key-12345678",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4o",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["base_url"] == "https://api.openai.com/v1"
        assert data["model"] == "gpt-4o"
        assert data["api_key_masked"] and "sk-" in data["api_key_masked"] and "****" in data["api_key_masked"]

    async def test_put_llm_settings_update(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        await async_client.put(
            "/api/v1/settings/llm",
            headers=auth_headers,
            json={"api_key": "sk-old-key-12345678", "base_url": "https://old.example.com", "model": "gpt-3.5"},
        )
        resp = await async_client.put(
            "/api/v1/settings/llm",
            headers=auth_headers,
            json={"base_url": "https://new.example.com", "model": "gpt-4o-mini"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["base_url"] == "https://new.example.com"
        assert data["model"] == "gpt-4o-mini"

    async def test_put_llm_settings_partial_update(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        await async_client.put(
            "/api/v1/settings/llm",
            headers=auth_headers,
            json={"api_key": "sk-full-key-12345678", "base_url": "https://api.openai.com/v1", "model": "gpt-4o"},
        )
        resp = await async_client.put(
            "/api/v1/settings/llm",
            headers=auth_headers,
            json={"model": "gpt-4-turbo"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["base_url"] == "https://api.openai.com/v1"
        assert data["model"] == "gpt-4-turbo"

    async def test_put_llm_settings_clear_key(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        await async_client.put(
            "/api/v1/settings/llm",
            headers=auth_headers,
            json={"api_key": "sk-test-key-12345678"},
        )
        resp = await async_client.put(
            "/api/v1/settings/llm",
            headers=auth_headers,
            json={"api_key": ""},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["api_key_masked"] is None

    async def test_put_llm_settings_unauthorized(self, async_client: AsyncClient):
        resp = await async_client.put(
            "/api/v1/settings/llm",
            json={"api_key": "sk-test-key"},
        )
        assert resp.status_code == 401

    async def test_user_isolation(self, async_client: AsyncClient, auth_headers: dict):
        resp = await async_client.put(
            "/api/v1/settings/llm",
            headers=auth_headers,
            json={"api_key": "sk-user-a-key-1234"},
        )
        assert resp.status_code == 200

        resp_b = await async_client.post("/api/v1/auth/register", json={
            "username": "userb", "password": "passwordb", "display_name": "User B",
        })
        assert resp_b.status_code == 201
        login_b = await async_client.post("/api/v1/auth/login", data={
            "username": "userb", "password": "passwordb",
        })
        token_b = login_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        resp_b_get = await async_client.get("/api/v1/settings/llm", headers=headers_b)
        assert resp_b_get.status_code == 200
        data_b = resp_b_get.json()
        assert data_b["api_key_masked"] is None


class _FakeHttpxResponse:
    """Fake httpx response with sync .json() and sync .text."""
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text

    def json(self):
        return self._json_data


class TestConnectionTest:
    async def test_connection_test_no_stored_key_and_no_env(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """When no key is in body, saved settings, or .env, it should fail."""
        with patch("app.routers.settings.settings.llm_api_key", ""), \
             patch("app.routers.settings.settings.llm_base_url", "https://api.openai.com/v1"), \
             patch("app.routers.settings.settings.llm_model", "gpt-4o"):
            resp = await async_client.post(
                "/api/v1/settings/llm/test",
                headers=auth_headers,
                json={},
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "No API key" in data["message"]

    async def test_connection_test_unauthorized(self, async_client: AsyncClient):
        resp = await async_client.post(
            "/api/v1/settings/llm/test",
            json={},
        )
        assert resp.status_code == 401

    async def test_connection_test_with_body_key_succeeds(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Mock httpx to simulate successful connection."""
        fake_client = AsyncMock()
        fake_resp = _FakeHttpxResponse(
            status_code=200,
            json_data={
                "choices": [{"message": {"content": "pong"}}],
                "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            },
        )
        fake_client.__aenter__.return_value = fake_client
        fake_client.__aexit__.return_value = None
        fake_client.post.return_value = fake_resp

        with patch("app.routers.settings.httpx.AsyncClient", return_value=fake_client):
            resp = await async_client.post(
                "/api/v1/settings/llm/test",
                headers=auth_headers,
                json={
                    "api_key": "sk-fake-for-test",
                    "base_url": "https://api.example.com/v1",
                    "model": "gpt-4o",
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "pong" in data["message"]

    async def test_connection_test_invalid_url(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Mock httpx to simulate connection error."""
        fake_client = AsyncMock()
        fake_client.__aenter__.side_effect = Exception("Connection refused")
        fake_client.__aexit__.return_value = None

        with patch("app.routers.settings.httpx.AsyncClient", return_value=fake_client):
            resp = await async_client.post(
                "/api/v1/settings/llm/test",
                headers=auth_headers,
                json={
                    "api_key": "sk-fake-for-test",
                    "base_url": "https://localhost:19999",
                    "model": "gpt-4o",
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "Connection refused" in data["message"]

    async def test_connection_test_api_error(
        self, async_client: AsyncClient, auth_headers: dict
    ):
        """Mock httpx to simulate 401 API error."""
        fake_client = AsyncMock()
        fake_resp = _FakeHttpxResponse(
            status_code=401,
            json_data={"error": {"message": "Invalid API key"}},
        )
        fake_client.__aenter__.return_value = fake_client
        fake_client.__aexit__.return_value = None
        fake_client.post.return_value = fake_resp

        with patch("app.routers.settings.httpx.AsyncClient", return_value=fake_client):
            resp = await async_client.post(
                "/api/v1/settings/llm/test",
                headers=auth_headers,
                json={
                    "api_key": "sk-bad-key",
                    "base_url": "https://api.example.com/v1",
                    "model": "gpt-4o",
                },
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is False
        assert "Invalid API key" in data["message"]
