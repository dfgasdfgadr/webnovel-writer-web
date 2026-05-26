"""Tests for InitAgent settings generation."""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.agents.init import InitAgent
from app.agents.llm import LLMResponse


class TestInitAgent:
    def test_init_agent_type(self):
        agent = InitAgent()
        assert agent.agent_type == "init"

    @pytest.mark.asyncio
    async def test_generate_settings_returns_dict(self):
        llm = MagicMock()
        llm.chat = AsyncMock(return_value=LLMResponse(
            content='{"world_building": "# 测试世界", "power_system": "# 测试体系", "protagonist_card": "# 测试主角"}'
        ))

        agent = InitAgent(llm=llm)
        premise = {
            "genre": "玄幻",
            "hook": "重生都市修真",
            "protagonist": {"name": "叶凡", "traits": "坚韧不拔"},
            "world_building": {"description": "现代都市与修真世界并存"},
            "power_system": "炼气、筑基、金丹",
            "golden_finger": "重生记忆",
            "constraints": [],
        }
        result = await agent.generate_settings(premise)
        assert isinstance(result, dict)
        assert "world_building" in result
        assert "power_system" in result
        assert "protagonist_card" in result
        llm.chat.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_settings_json_parse_failure_fallback(self):
        llm = MagicMock()
        llm.chat = AsyncMock(return_value=LLMResponse(content="not valid json at all"))

        agent = InitAgent(llm=llm)
        result = await agent.generate_settings({"genre": "test"})
        assert isinstance(result, dict)
        assert result["world_building"] == "not valid json at all"

    @pytest.mark.asyncio
    async def test_execute_delegates_to_generate_settings(self):
        llm = MagicMock()
        llm.chat = AsyncMock(return_value=LLMResponse(
            content='{"world_building": "x", "power_system": "y", "protagonist_card": "z"}'
        ))

        agent = InitAgent(llm=llm)
        result = await agent._execute(premise={"genre": "test"})
        assert result["world_building"] == "x"


class TestStubSettings:
    def test_build_stub_settings_from_premise(self):
        """_build_stub_settings should produce valid markdown from premise data when LLM is unavailable."""
        from app.routers.projects import _build_stub_settings

        premise = {
            "genre": "玄幻",
            "hook": "重生都市修真",
            "power_system": "炼气、筑基、金丹",
            "golden_finger": "重生记忆",
            "protagonist": {"name": "叶凡", "gender": "男", "age": 25, "personality": "坚韧", "background": "修真者", "goal": "成仙"},
        }
        stub = _build_stub_settings(premise)
        assert "# 世界观" in stub["world_building"]
        assert "玄幻" in stub["world_building"]
        assert "重生都市修真" in stub["world_building"]
        assert "# 力量体系" in stub["power_system"]
        assert "炼气" in stub["power_system"]
        assert "重生记忆" in stub["power_system"]
        assert "# 主角卡" in stub["protagonist_card"]
        assert "叶凡" in stub["protagonist_card"]

    def test_build_stub_synopsis_from_premise(self):
        """_build_stub_synopsis should produce valid synopsis when LLM is unavailable."""
        from app.routers.projects import _build_stub_synopsis

        premise = {"title": "测试书", "genre": "玄幻", "hook": "重生", "target_chapters": 60}
        stub = _build_stub_synopsis(premise)
        assert stub["title"] == "测试书"
        assert stub["genre"] == "玄幻"
        assert "AI 总纲生成暂不可用" in stub["synopsis"]
        assert len(stub["volumes"]) == 1
        assert stub["volumes"][0]["target_chapters"] == 60
