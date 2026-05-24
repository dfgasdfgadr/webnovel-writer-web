"""Base agent with logging and retry."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any
import time

from app.agents.llm import LLMProvider, LLMMessage, LLMResponse


@dataclass
class AgentResult:
    success: bool
    data: Any = None
    error: str | None = None
    token_input: int = 0
    token_output: int = 0
    elapsed_ms: int = 0


class BaseAgent(ABC):
    """Every agent has a system prompt, can be called with context, and reports costs."""

    agent_type: str = "base"

    def __init__(self, llm: LLMProvider | None = None):
        self.llm = llm or LLMProvider()

    async def run(self, **kwargs) -> AgentResult:
        start = time.time()
        try:
            data = await self._execute(**kwargs)
            elapsed = int((time.time() - start) * 1000)
            return AgentResult(success=True, data=data, elapsed_ms=elapsed)
        except Exception as e:
            elapsed = int((time.time() - start) * 1000)
            return AgentResult(success=False, error=str(e), elapsed_ms=elapsed)

    @abstractmethod
    async def _execute(self, **kwargs) -> Any:
        ...

    async def _chat_json(self, messages: list[LLMMessage], temperature: float = 0.3) -> LLMResponse:
        """Chat with LLM and return parsed JSON."""
        resp = await self.llm.chat(messages, temperature)
        content = resp.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return resp  # caller parses JSON

    async def _chat_text(self, messages: list[LLMMessage], temperature: float = 0.7) -> LLMResponse:
        return await self.llm.chat(messages, temperature)
