"""Tests for plugin loader path resolution (BUG-1)."""

import pytest
from pathlib import Path


class TestPluginLoaderPath:
    def test_resolves_repo_root_plugins_dir(self):
        """PluginLoader should resolve plugins/ from __file__, not CWD."""
        from app.services.plugin_loader import PluginLoader

        loader = PluginLoader()  # no explicit dir → compute from __file__
        plugins_dir = loader.plugins_dir
        assert plugins_dir.exists(), f"Plugins dir not found at {plugins_dir}"
        assert plugins_dir.name == "plugins", f"Expected 'plugins' dir, got {plugins_dir.name}"
        assert (plugins_dir / "agents").is_dir(), f"agents/ not found under {plugins_dir}"

    def test_scans_combat_checker(self):
        """Scan should discover combat_checker from plugins/agents/."""
        from app.services.plugin_loader import PluginLoader

        loader = PluginLoader()
        discovered = loader.scan()
        names = [p.name for p in discovered]
        assert "combat_checker" in names, f"combat_checker not in discovered plugins: {names}"

    def test_explicit_plugins_dir_overrides_default(self):
        """Explicit plugins_dir should override the default path computation."""
        from app.services.plugin_loader import PluginLoader

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            loader = PluginLoader(plugins_dir=tmpdir)
            assert loader.plugins_dir == Path(tmpdir)


class TestPluginsAPI:
    async def test_list_plugins_returns_combat_checker(self, async_client, auth_headers):
        """GET /api/v1/plugins should include combat_checker."""
        resp = await async_client.get("/api/v1/plugins", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "plugins" in data
        names = [p["name"] for p in data["plugins"]]
        assert "combat_checker" in names, f"combat_checker not in API response: {names}"
        assert data["total"] >= 1

    async def test_plugins_require_auth(self, async_client):
        """Plugin endpoint should require authentication."""
        resp = await async_client.get("/api/v1/plugins")
        assert resp.status_code == 401
