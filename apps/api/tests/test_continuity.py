"""Tests for ContinuityAgent."""
import json
from unittest.mock import MagicMock, patch
import pytest

from app.agents.continuity import ContinuityAgent
from app.models.entity import Foreshadowing


class TestForeshadowingFieldMapping:
    """Regression: verify Foreshadowing dict conversion uses correct model fields.

    BUG-1: agents.py used f.title/f.chapter_planted/f.chapter_resolved which don't exist
    on the Foreshadowing model. Correct fields: description/planted_in_chapter_id/resolved_in_chapter_id.
    """

    def test_continuity_endpoint_fields(self):
        """Verify fields used in POST /continuity/{id} dict conversion exist on model."""
        f = Foreshadowing(
            id="f-1",
            project_id="p-1",
            planted_in_chapter_id="ch-5",
            status="planted",
            description="神秘戒指暗示隐藏力量",
        )
        # Replicate the dict built in the continuity endpoint
        item = {
            "id": f.id,
            "description": f.description,
            "status": f.status,
            "planted_in_chapter_id": f.planted_in_chapter_id,
        }
        assert item["id"] == "f-1"
        assert item["description"] == "神秘戒指暗示隐藏力量"
        assert item["status"] == "planted"
        assert item["planted_in_chapter_id"] == "ch-5"

    def test_graph_endpoint_fields(self):
        """Verify fields used in GET /graph/{id} dict conversion exist on model."""
        f = Foreshadowing(
            id="f-2",
            project_id="p-1",
            planted_in_chapter_id="ch-3",
            resolved_in_chapter_id="ch-8",
            status="resolved",
            description="主角身世之谜",
        )
        # Replicate the dict built in the graph endpoint
        item = {
            "id": f.id,
            "status": f.status,
            "planted_in_chapter_id": f.planted_in_chapter_id,
            "resolved_in_chapter_id": f.resolved_in_chapter_id,
            "description": f.description,
        }
        assert item["id"] == "f-2"
        assert item["status"] == "resolved"
        assert item["planted_in_chapter_id"] == "ch-3"
        assert item["resolved_in_chapter_id"] == "ch-8"
        assert item["description"] == "主角身世之谜"

    def test_no_title_field_on_model(self):
        """Foreshadowing has no 'title' field — accessing it raises AttributeError."""
        f = Foreshadowing(
            id="f-3",
            project_id="p-1",
            planted_in_chapter_id="ch-1",
            description="test",
        )
        with pytest.raises(AttributeError):
            _ = f.title

    def test_no_chapter_planted_resolved_on_model(self):
        """Foreshadowing has no chapter_planted/chapter_resolved — only planted_in_chapter_id/resolved_in_chapter_id."""
        f = Foreshadowing(
            id="f-4",
            project_id="p-1",
            planted_in_chapter_id="ch-1",
            description="test",
        )
        with pytest.raises(AttributeError):
            _ = f.chapter_planted
        with pytest.raises(AttributeError):
            _ = f.chapter_resolved

    def test_chapter_commit_has_no_chapter_number(self):
        """ChapterCommit uses chapter_id, not chapter_number — join Chapter for number."""
        from app.models.contract import ChapterCommit
        c = ChapterCommit(chapter_id="ch-1", project_id="p-1")
        with pytest.raises(AttributeError):
            _ = c.chapter_number
        assert c.chapter_id == "ch-1"


class TestContinuityAgent:
    @pytest.mark.asyncio
    async def test_continuity_agent_output_structure(self):
        """ContinuityAgent should return structured data with expected keys."""
        mock_llm_response = MagicMock()
        mock_llm_response.content = json.dumps({
            "timeline_snapshot": "主角进入新城市，遇到了关键NPC。",
            "character_states": [
                {"name": "主角", "status": "受伤", "location": "西城区", "goal": "找到解药"}
            ],
            "active_foreshadowing": [
                {"id": "f1", "title": "神秘戒指", "status": "planted", "chapter_planted": 5, "progress": "戒指发烫，暗示即将揭示秘密"}
            ],
            "pending_conflicts": ["与反派的对峙一触即发"],
            "continuity_risks": [
                {"risk": "主角技能等级与第3章矛盾", "severity": "high"}
            ],
            "disambiguation_items": [
                {"field": "character_name", "current_value": "龙傲天", "confidence": 0.6, "alternatives": ["龙啸天"]}
            ],
        })
        mock_llm_response.token_input = 100
        mock_llm_response.token_output = 200

        agent = ContinuityAgent()
        # Mock _chat_json which is called by _execute indirectly
        with patch.object(agent, '_chat_json', return_value=mock_llm_response):
            result = await agent.run(
                project_id="p1",
                chapter_texts=[
                    {"number": 5, "title": "第五章", "content": "主角进入城市..."},
                ],
                entities=[{"name": "主角", "type": "character", "description": "修炼者"}],
                foreshadowing_items=[{"id": "f1", "title": "神秘戒指", "status": "planted", "chapter_planted": 5}],
                recent_commits=[{"chapter_number": 4, "summary": "主角获得神秘戒指"}],
            )

        assert result.success
        data = result.data
        snapshot = data["continuity_snapshot"]
        assert "timeline_snapshot" in snapshot
        assert len(snapshot["character_states"]) >= 1
        assert len(snapshot["active_foreshadowing"]) >= 1
        assert len(snapshot["continuity_risks"]) >= 1
        assert len(snapshot["disambiguation_items"]) >= 1

    @pytest.mark.asyncio
    async def test_continuity_agent_empty_input(self):
        """Should handle empty input gracefully."""
        mock_llm_response = MagicMock()
        mock_llm_response.content = 'invalid json{'
        mock_llm_response.token_input = 0
        mock_llm_response.token_output = 0

        agent = ContinuityAgent()
        with patch.object(agent, '_chat_json', return_value=mock_llm_response):
            result = await agent.run(
                project_id="p1",
                chapter_texts=[],
                entities=[],
                foreshadowing_items=[],
                recent_commits=[],
            )

        assert result.success
        data = result.data
        snapshot = data["continuity_snapshot"]
        assert "Failed to parse" in snapshot.get("timeline_snapshot", "")

    def test_agent_type_is_continuity(self):
        agent = ContinuityAgent()
        assert agent.agent_type == "continuity"
