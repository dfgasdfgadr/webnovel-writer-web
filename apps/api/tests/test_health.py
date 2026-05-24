import pytest
from httpx import AsyncClient


class TestHealth:
    async def test_health_returns_ok(self, async_client: AsyncClient):
        resp = await async_client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "novelcraft-api"
