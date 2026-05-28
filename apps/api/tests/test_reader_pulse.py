"""Tests for ReaderPulseAgent and ReaderPulseResult model."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock


class TestReaderPulseAgent:
    def _make_agent(self, mock_json: str = None):
        from app.agents.reader_pulse import ReaderPulseAgent

        agent = ReaderPulseAgent()
        if mock_json is not None:
            mock_llm = MagicMock()
            mock_llm.chat = AsyncMock(return_value=MagicMock(
                content=mock_json, token_input=100, token_output=50,
            ))
            agent.llm = mock_llm
        return agent

    @pytest.mark.asyncio
    async def test_execute_parses_valid_json(self):
        mock = json.dumps({
            "drop_risk": 30, "hook_quality": 85, "pacing_score": 90,
            "expectation": "期待下一章", "strengths": ["节奏好"], "weaknesses": ["描写少"],
            "next_chapter_suggestion": "加强冲突", "overall_verdict": "优秀",
        })
        agent = self._make_agent(mock)
        result = await agent.run(chapter_content="测试正文")
        assert result.success
        assert result.data["drop_risk"] == 30
        assert result.data["hook_quality"] == 85
        assert result.data["pacing_score"] == 90
        assert result.data["expectation"] == "期待下一章"
        assert result.data["strengths"] == ["节奏好"]
        assert result.data["weaknesses"] == ["描写少"]

    @pytest.mark.asyncio
    async def test_execute_fallback_on_bad_json(self):
        agent = self._make_agent("not valid json")
        result = await agent.run(chapter_content="测试正文")
        assert result.success
        assert result.data["drop_risk"] == 50  # fallback default
        assert result.data["overall_verdict"] == "JSON 解析失败"
        assert result.data.get("raw") is not None

    @pytest.mark.asyncio
    async def test_execute_with_outline_and_summary(self):
        mock = json.dumps({
            "drop_risk": 20, "hook_quality": 90, "pacing_score": 80,
            "expectation": "期待", "strengths": ["设定新颖"], "weaknesses": [],
            "next_chapter_suggestion": "继续保持", "overall_verdict": "良好",
        })
        agent = self._make_agent(mock)
        result = await agent.run(
            chapter_content="正文内容",
            chapter_outline="本章章纲",
            previous_chapter_summary="前文摘要",
        )
        assert result.success
        assert result.data["drop_risk"] == 20

    @pytest.mark.asyncio
    async def test_scores_clamped_to_range(self):
        mock = json.dumps({
            "drop_risk": 150, "hook_quality": -10, "pacing_score": 999,
            "expectation": "", "strengths": [], "weaknesses": [],
            "next_chapter_suggestion": "", "overall_verdict": "",
        })
        agent = self._make_agent(mock)
        result = await agent.run(chapter_content="测试")
        assert 0 <= result.data["drop_risk"] <= 100
        assert 0 <= result.data["hook_quality"] <= 100
        assert 0 <= result.data["pacing_score"] <= 100


class TestReaderPulseAPI:
    async def test_get_reader_pulse_empty(self, async_client, auth_headers):
        """Get reader pulse for a chapter with no results."""
        from app.database import async_session
        from app.models import Chapter, Project

        async with async_session() as db:
            from app.models.user import User
            result = await db.execute(
                __import__("sqlalchemy").select(User).where(User.username == "testuser")
            )
            user = result.scalar_one()

            import uuid
            pid = str(uuid.uuid4())
            db.add(Project(id=pid, title="PulseTest", owner_id=user.id, root_dir="/tmp"))
            cid = str(uuid.uuid4())
            db.add(Chapter(id=cid, project_id=pid, title="第1章", number=1, content="test"))
            await db.commit()

        resp = await async_client.get(f"/api/v1/agents/reader-pulse/{cid}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_reader_pulse_404_on_bad_chapter(self, async_client, auth_headers):
        resp = await async_client.get("/api/v1/agents/reader-pulse/nonexistent", headers=auth_headers)
        assert resp.status_code == 404

    async def test_reader_pulse_403_wrong_owner(self, async_client, auth_headers):
        """Reader pulse endpoint should reject chapters owned by other users."""
        from app.database import async_session
        from app.models import Project, Chapter
        import uuid

        # Register another user and create a project
        async with async_session() as db:
            other_user_id = str(uuid.uuid4())
            from app.models.user import User
            db.add(User(id=other_user_id, username="otheruser", hashed_password="x"))
            pid = str(uuid.uuid4())
            db.add(Project(id=pid, title="OtherProject", owner_id=other_user_id, root_dir="/tmp"))
            cid = str(uuid.uuid4())
            db.add(Chapter(id=cid, project_id=pid, title="第1章", number=1, content="x"))
            await db.commit()

        # Try to access with testuser auth
        resp = await async_client.get(f"/api/v1/agents/reader-pulse/{cid}", headers=auth_headers)
        assert resp.status_code == 403
