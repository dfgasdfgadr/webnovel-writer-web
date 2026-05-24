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
