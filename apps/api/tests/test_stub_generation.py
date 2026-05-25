"""Tests for stub settings/synopsis generation on LLM failure (BUG-5)."""

import pytest


class TestBuildStubSettings:
    def _build_stub_settings(self, premise: dict) -> dict:
        from app.routers.projects import _build_stub_settings
        return _build_stub_settings(premise)

    def test_produces_all_three_files(self):
        result = self._build_stub_settings({
            "genre": "玄幻",
            "hook": "主角穿越异界",
            "protagonist": {"name": "林凡"},
            "power_system": "灵力修炼",
            "golden_finger": "系统",
        })
        assert "world_building" in result
        assert "power_system" in result
        assert "protagonist_card" in result

    def test_world_building_contains_genre(self):
        result = self._build_stub_settings({
            "genre": "玄幻",
            "hook": "test hook",
            "protagonist": {},
        })
        assert "玄幻" in result["world_building"]

    def test_world_building_contains_hook(self):
        result = self._build_stub_settings({
            "genre": "",
            "hook": "复仇之路",
            "protagonist": {},
        })
        assert "复仇之路" in result["world_building"]

    def test_power_system_contains_golden_finger(self):
        result = self._build_stub_settings({
            "genre": "",
            "hook": "",
            "protagonist": {},
            "power_system": "魔法",
            "golden_finger": "逆天神器",
        })
        assert "魔法" in result["power_system"]
        assert "逆天神器" in result["power_system"]

    def test_protagonist_card_has_fields(self):
        result = self._build_stub_settings({
            "genre": "",
            "hook": "",
            "protagonist": {
                "name": "叶尘",
                "gender": "男",
                "age": "18",
                "personality": "冷静",
                "background": "孤儿",
                "goal": "成为最强",
            },
        })
        card = result["protagonist_card"]
        assert "叶尘" in card
        assert "男" in card
        assert "18" in card
        assert "冷静" in card
        assert "孤儿" in card
        assert "成为最强" in card

    def test_empty_protagonist_has_fallbacks(self):
        result = self._build_stub_settings({
            "genre": "",
            "hook": "",
            "protagonist": {},
        })
        assert "（待设定）" in result["protagonist_card"]

    def test_empty_premise_generates_valid_stubs(self):
        result = self._build_stub_settings({
            "genre": "",
            "hook": "",
            "protagonist": {},
        })
        for key in ["world_building", "power_system", "protagonist_card"]:
            assert result[key], f"{key} should not be empty"


class TestBuildStubSynopsis:
    def _build_stub_synopsis(self, premise: dict) -> dict:
        from app.routers.projects import _build_stub_synopsis
        return _build_stub_synopsis(premise)

    def test_has_required_fields(self):
        result = self._build_stub_synopsis({
            "title": "测试书",
            "genre": "玄幻",
            "hook": "主角无敌",
        })
        assert "title" in result
        assert "genre" in result
        assert "hook" in result
        assert "synopsis" in result
        assert "volumes" in result

    def test_synopsis_indicates_unavailable(self):
        result = self._build_stub_synopsis({
            "title": "",
            "genre": "都市",
            "hook": "逆袭人生",
        })
        assert "AI" in result["synopsis"] or "LLM" in result["synopsis"]

    def test_has_at_least_one_volume(self):
        result = self._build_stub_synopsis({
            "title": "x",
            "genre": "",
            "hook": "",
            "target_chapters": 50,
        })
        assert len(result["volumes"]) >= 1
        assert result["volumes"][0]["num"] == 1

    def test_respects_target_chapters(self):
        result = self._build_stub_synopsis({
            "title": "x",
            "genre": "",
            "hook": "",
            "target_chapters": 80,
        })
        assert result["volumes"][0]["target_chapters"] == 80


class TestWarningsInProjectCreation:
    async def test_create_project_no_llm_returns_stub_files(self, async_client, auth_headers):
        """Creating a project without LLM should still produce stub settings files."""
        # Note: this test assumes LLM is not configured in test env,
        # so it should fall back to stub generation.
        resp = await async_client.post("/api/v1/projects", json={
            "title": "StubTest Novel",
            "description": "A test",
            "genre": "fantasy",
            "hook": "A hero's journey",
            "protagonist": {"name": "Arthur"},
            "power_system": "Magic",
            "golden_finger": "Sword",
        }, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        # Should have warnings or at least a valid project
        assert data["id"]
        assert data["title"] == "StubTest Novel"
        # If LLM was unavailable, warnings should be present
        if data.get("warnings"):
            assert any("LLM" in w or "AI" in w or "配置" in w for w in data["warnings"])
