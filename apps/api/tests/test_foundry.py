"""Tests for Story Foundry agents and API endpoints."""

import json
from unittest.mock import patch, MagicMock
import pytest
from httpx import AsyncClient


class MockLLMResponse:
    def __init__(self, content):
        self.content = content
        self.token_input = 100
        self.token_output = 200


def mock_deconstruct_json():
    return json.dumps({
        "book_title": "测试书",
        "transferable_patterns": ["黄金三章模式", "打脸节奏"],
        "warnings": ["不要复制"],
        "golden_chapters": ["黄金三章分析"],
        "hooks": ["悬念钩子"],
        "character_patterns": ["成长型主角"],
        "world_patterns": ["逐步揭秘"],
        "pacing": ["快节奏"],
        "red_flags": ["避免抄袭"],
    }, ensure_ascii=False)


def mock_questions_json():
    return json.dumps({
        "question_sets": [
            {
                "id": "protagonist_core",
                "title": "主角核心驱动力",
                "description": "主角最核心的动机",
                "options": [
                    {
                        "id": "revenge_growth",
                        "label": "复仇成长型",
                        "description": "主角背负血仇",
                        "effects": {"protagonist": {}, "plot_bias": {}, "pacing": {}},
                    },
                    {
                        "id": "ambition_rise",
                        "label": "野心崛起型",
                        "description": "主角从底层崛起",
                        "effects": {"protagonist": {}, "plot_bias": {}, "pacing": {}},
                    },
                ],
            },
        ],
    }, ensure_ascii=False)


def mock_compose_json():
    return json.dumps({
        "premise": {
            "title": "测试书·改写",
            "genre": "玄幻",
            "hook": "测试卖点",
            "protagonist": {"name": "主角", "gender": "男"},
            "world_building": {"setting": "玄幻世界"},
            "power_system": "修炼体系",
            "golden_finger": "系统面板",
            "constraints": ["原创"],
            "target_words": 1000000,
            "target_chapters": 300,
        },
        "master_setting": {
            "title": "测试书·改写",
            "genre": "玄幻",
            "hook": "测试卖点",
            "world_overview": "测试世界观",
            "power_system": {"name": "修炼", "description": "修炼体系", "progression": "逐步", "limitations": []},
            "key_factions": [],
            "key_locations": [],
            "rules_and_constraints": [],
            "tone_and_atmosphere": "热血",
        },
        "synopsis": {
            "title": "测试书·改写",
            "genre": "玄幻",
            "hook": "测试卖点",
            "synopsis": "测试故事概述",
            "volumes": [{"num": 1, "title": "第一卷", "summary": "测试", "target_chapters": 30}],
        },
        "first_volume_chapters": [
            {
                "chapter_num": 1,
                "title": "第一章：开篇",
                "outline": "主角出场",
                "must_cover_nodes": ["主角出场"],
                "forbidden_zones": ["不复制"],
                "key_characters": [{"name": "主角", "role_in_chapter": "核心"}],
                "target_words": 3000,
            },
        ],
    }, ensure_ascii=False)


class TestFoundryDeconstructAPI:
    async def test_foundry_deconstruct_success(self, async_client: AsyncClient, auth_headers: dict):
        """Test deconstruct endpoint returns normalized deconstruction."""
        with patch("app.agents.llm.LLMProvider.chat", return_value=MockLLMResponse(mock_deconstruct_json())):
            resp = await async_client.post(
                "/api/v1/agents/foundry/deconstruct",
                json={"book_title": "测试书", "sample_chapters": ["第一章内容...", "第二章内容..."]},
                headers=auth_headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "done"
        assert "deconstruction" in data
        decon = data["deconstruction"]
        assert "golden_chapters" in decon
        assert "hooks" in decon
        assert "transferable_patterns" in decon
        assert "red_flags" in decon

    async def test_foundry_deconstruct_no_chapters(self, async_client: AsyncClient, auth_headers: dict):
        """Test deconstruct with empty chapters still returns structure."""
        resp = await async_client.post(
            "/api/v1/agents/foundry/deconstruct",
            json={"book_title": "测试书", "sample_chapters": []},
            headers=auth_headers,
        )
        # Empty chapters should return error (no LLM call)
        assert resp.status_code == 500


class TestFoundryQuestionsAPI:
    async def test_foundry_questions_success(self, async_client: AsyncClient, auth_headers: dict):
        """Test questions endpoint returns question sets."""
        with patch("app.agents.llm.LLMProvider.chat", return_value=MockLLMResponse(mock_questions_json())):
            resp = await async_client.post(
                "/api/v1/agents/foundry/questions",
                json={
                    "deconstruction": {
                        "transferable_patterns": ["黄金三章模式", "打脸节奏"],
                        "hooks": ["悬念钩子", "升级爽点"],
                    },
                    "preferences": {},
                },
                headers=auth_headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "question_sets" in data
        assert isinstance(data["question_sets"], list)
        assert len(data["question_sets"]) >= 1
        # Check first question structure
        q = data["question_sets"][0]
        assert "id" in q
        assert "title" in q
        assert "description" in q
        assert "options" in q
        assert len(q["options"]) >= 2
        opt = q["options"][0]
        assert "id" in opt
        assert "label" in opt
        assert "description" in opt
        assert "effects" in opt

    async def test_foundry_questions_fallback(self, async_client: AsyncClient, auth_headers: dict):
        """Test questions endpoint returns fallback when LLM unavailable."""
        resp = await async_client.post(
            "/api/v1/agents/foundry/questions",
            json={"deconstruction": {}, "preferences": {}},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "question_sets" in data
        assert len(data["question_sets"]) >= 6


class TestFoundryComposeAPI:
    async def test_foundry_compose_schema(self, async_client: AsyncClient, auth_headers: dict):
        """Test compose endpoint returns correct schema."""
        with patch("app.agents.llm.LLMProvider.chat", return_value=MockLLMResponse(mock_compose_json())):
            resp = await async_client.post(
                "/api/v1/agents/foundry/compose",
                json={
                    "book_title": "测试书",
                    "deconstruction": {"transferable_patterns": ["模式1"]},
                    "selections": {
                        "protagonist_core": "revenge_growth",
                        "pleasure_pattern": "face_slap",
                        "golden_finger": "system",
                    },
                    "custom_notes": "",
                },
                headers=auth_headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "premise" in data
        assert "master_setting" in data
        assert "synopsis" in data
        assert "first_volume_chapters" in data
        assert "fallback" in data
        # Validate chapter structure
        chapters = data["first_volume_chapters"]
        assert isinstance(chapters, list)
        assert len(chapters) >= 1
        ch = chapters[0]
        assert "chapter_num" in ch
        assert "title" in ch
        assert "outline" in ch
        assert "must_cover_nodes" in ch
        assert "forbidden_zones" in ch
        assert "target_words" in ch

    async def test_foundry_compose_with_custom_notes(self, async_client: AsyncClient, auth_headers: dict):
        """Test compose with custom notes."""
        with patch("app.agents.llm.LLMProvider.chat", return_value=MockLLMResponse(mock_compose_json())):
            resp = await async_client.post(
                "/api/v1/agents/foundry/compose",
                json={
                    "book_title": "测试书",
                    "deconstruction": {},
                    "selections": {"protagonist_core": "revenge_growth"},
                    "custom_notes": "希望主角是女性",
                },
                headers=auth_headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert "premise" in data

    async def test_foundry_compose_fallback_no_llm(self, async_client: AsyncClient, auth_headers: dict):
        """Test compose returns fallback when no LLM and selections provided."""
        resp = await async_client.post(
            "/api/v1/agents/foundry/compose",
            json={
                "book_title": "测试书",
                "deconstruction": {},
                "selections": {"protagonist_core": "revenge_growth"},
                "custom_notes": "",
            },
            headers=auth_headers,
        )
        # Should still return fallback data
        assert resp.status_code == 200
        data = resp.json()
        assert "premise" in data
        assert "first_volume_chapters" in data
        assert data["fallback"] is True


class TestFoundryProjectCreate:
    async def test_create_project_with_foundry_output(self, async_client: AsyncClient, auth_headers: dict):
        """Test creating project with foundry compose output."""
        payload = {
            "title": "Foundry Test Project",
            "description": "Created from foundry",
            "genre": "玄幻",
            "premise": {
                "title": "Foundry Test Project",
                "genre": "玄幻",
                "hook": "测试卖点",
                "protagonist": {"name": "测试主角"},
                "target_words": 1000000,
                "target_chapters": 300,
            },
            "master_setting": {
                "title": "Foundry Test Project",
                "genre": "玄幻",
                "world_overview": "测试世界观",
                "power_system": {"name": "修炼体系", "description": "测试", "progression": "逐步提升", "limitations": ["资源限制"]},
            },
            "synopsis": {
                "title": "Foundry Test Project",
                "genre": "玄幻",
                "hook": "测试卖点",
                "synopsis": "测试故事概述",
                "volumes": [{"num": 1, "title": "第一卷", "summary": "测试", "target_chapters": 30}],
            },
            "chapter_outlines": [
                {
                    "chapter_num": 1,
                    "title": "第一章：开篇",
                    "outline": "主角出场，世界观介绍",
                    "must_cover_nodes": ["主角出场", "世界观初现"],
                    "forbidden_zones": ["不复制参考书"],
                    "key_characters": [{"name": "主角", "role_in_chapter": "核心"}],
                    "target_words": 3000,
                },
                {
                    "chapter_num": 2,
                    "title": "第二章：冲突",
                    "outline": "第一个冲突出现",
                    "must_cover_nodes": ["冲突引入"],
                    "forbidden_zones": [],
                    "key_characters": [],
                    "target_words": 3000,
                },
            ],
        }
        resp = await async_client.post("/api/v1/projects", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Foundry Test Project"
        assert data["genre"] == "玄幻"

        # Verify chapters were created
        project_id = data["id"]
        chapters_resp = await async_client.get(f"/api/v1/projects/{project_id}/chapters", headers=auth_headers)
        assert chapters_resp.status_code == 200
        chapters = chapters_resp.json()
        assert len(chapters["items"]) == 2
        assert chapters["items"][0]["title"] == "第一章：开篇"
        assert chapters["items"][0]["outline"] == "主角出场，世界观介绍"

    async def test_create_project_normal_mode_still_works(self, async_client: AsyncClient, auth_headers: dict):
        """Test normal project creation still works without foundry fields."""
        resp = await async_client.post(
            "/api/v1/projects",
            json={"title": "Normal Project", "genre": "都市"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Normal Project"


class TestFoundryModeDispatch:
    async def test_foundry_deconstruct_quick_default(self, async_client: AsyncClient, auth_headers: dict):
        """Default mode is quick when mode field is omitted (backward compat)."""
        with patch("app.agents.llm.LLMProvider.chat", return_value=MockLLMResponse(mock_deconstruct_json())):
            resp = await async_client.post(
                "/api/v1/agents/foundry/deconstruct",
                json={"book_title": "测试书", "sample_chapters": ["第一章..."]},
                headers=auth_headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "done"
        assert "deconstruction" in data

    async def test_foundry_deconstruct_representative(self, async_client: AsyncClient, auth_headers: dict):
        """Representative mode merges chapter groups and returns deconstruction."""
        with patch("app.agents.llm.LLMProvider.chat", return_value=MockLLMResponse(mock_deconstruct_json())):
            resp = await async_client.post(
                "/api/v1/agents/foundry/deconstruct",
                json={
                    "book_title": "测试书",
                    "mode": "representative",
                    "chapter_groups": [
                        {"label": "黄金三章", "content": "前三章内容..."},
                        {"label": "高潮章节", "content": "高潮内容..."},
                    ],
                },
                headers=auth_headers,
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "done"
        assert "deconstruction" in data
        decon = data["deconstruction"]
        assert "golden_chapters" in decon

    async def test_foundry_deconstruct_fullbook_placeholder(self, async_client: AsyncClient, auth_headers: dict):
        """Full-book mode returns deferred placeholder without calling LLM."""
        resp = await async_client.post(
            "/api/v1/agents/foundry/deconstruct",
            json={
                "book_title": "测试书",
                "mode": "fullbook",
                "sample_chapters": [],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "deferred"
        assert "Full-book" in data["message"] or "下一阶段" in data["message"]
        assert data["deconstruction"] is None
