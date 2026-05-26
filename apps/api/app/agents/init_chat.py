"""InitChatAgent — multi-round conversational init with sufficiency gate.

Asks questions for missing/blocking fields via SSE, validates answers,
and generates creative constraint packages when all fields are complete.
"""

import json
import logging

from app.agents.base import BaseAgent
from app.agents.llm import LLMMessage

logger = logging.getLogger("novelcraft.init_chat")

INIT_CHAT_SYSTEM = """你是网文创作助手，负责通过对话采集作者的关键创作信息。

## 充分性闸门（以下字段必须全部获得才能进入项目创建）
1. 书名 (title)
2. 题材 (genre)
3. 核心卖点/故事钩子 (hook)
4. 主角姓名 (protagonist_name)
5. 世界观简述 (world_building)
6. 力量体系概述 (power_system)
7. 金手指/特殊能力 (golden_finger)
8. 创意约束 (constraints)

## 对话规则
- 每轮只问 1-2 个未填写的字段
- 如果作者已经提供了部分信息，不要重复询问
- 引导作者提供具体而非模糊的答案
- 当所有字段填写完成后，生成 2-3 套创意约束方案供作者选择

## 输出格式
根据当前状态输出 JSON：

当还有字段缺失时：
{"status": "asking", "missing_fields": ["field1", "field2"], "question": "你的提问", "hint": "可选的引导提示"}

当所有字段齐全时生成方案：
{"status": "complete", "schemes": [{"name": "方案名", "genre_focus": "题材侧重", "hook_variation": "卖点变体", "power_evolution": "力量体系演进方向", "target_scale": "建议规模", "scores": {"innovation": 85, "marketability": 90, "coherence": 88, "depth": 82, "readability": 92}}]}

当用户选择某个方案后：
{"status": "confirmed", "selected_scheme": 0, "premise_json": {...完整的前提JSON...}}

只输出 JSON，不要其他内容。"""


class InitChatAgent(BaseAgent):
    """Multi-round conversational init agent."""
    agent_type = "init_chat"

    def __init__(self, llm=None):
        super().__init__(llm=llm)
        self.conversation: list[dict] = []

    def _collect_state(self, conversation: list[dict]) -> dict:
        """Extract all known fields from conversation history."""
        state = {
            "title": "", "genre": "", "hook": "",
            "protagonist_name": "", "world_building": "",
            "power_system": "", "golden_finger": "", "constraints": [],
        }
        for msg in conversation:
            if msg["role"] != "user":
                continue
            content = msg["content"]
            try:
                data = json.loads(content)
                for key in state:
                    if key in data and data[key]:
                        state[key] = data[key]
            except json.JSONDecodeError:
                pass
        return state

    def _missing_fields(self, state: dict) -> list[str]:
        """Return list of blocking fields that are still empty."""
        required = ["title", "genre", "hook", "protagonist_name"]
        missing = [k for k in required if not state.get(k)]
        if not missing:
            secondary = ["world_building", "power_system", "golden_finger"]
            missing = [k for k in secondary if not state.get(k)]
        return missing

    async def process_message(self, user_message: str) -> dict:
        """Process a user message and return the next step in the conversation."""
        self.conversation.append({"role": "user", "content": user_message})

        state = self._collect_state(self.conversation)
        missing = self._missing_fields(state)

        if not missing and not state.get("constraints"):
            # Generate creative schemes
            return await self._generate_schemes(state)

        if not self.llm:
            return self._fallback_question(missing, state)

        # Use LLM to generate the next question
        prompt = f"""当前已采集的创作信息：
{json.dumps(state, ensure_ascii=False)}

仍缺失的关键字段：{json.dumps(missing, ensure_ascii=False)}

请生成一个自然的问题来引导作者填写缺失字段。"""

        messages = [
            LLMMessage(role="system", content=INIT_CHAT_SYSTEM),
            LLMMessage(role="user", content=prompt),
        ]
        try:
            resp = await self.llm.chat(messages, temperature=0.7)
            return json.loads(resp.content)
        except Exception:
            return self._fallback_question(missing, state)

    def _fallback_question(self, missing: list[str], state: dict) -> dict:
        """Generate a fallback question without LLM."""
        prompts = {
            "title": "请为你的作品取一个书名",
            "genre": "你的作品是什么题材？（如：玄幻、都市、科幻、仙侠）",
            "hook": "用一句话描述你故事最吸引人的核心卖点",
            "protagonist_name": "你的主角叫什么名字？",
            "world_building": "简单描述一下你故事的世界背景",
            "power_system": "你的故事中有怎样的力量体系或能力设定？",
            "golden_finger": "主角有什么特殊的金手指或优势？",
        }
        question = prompts.get(missing[0], f"请提供更多关于 {missing[0]} 的信息")
        return {
            "status": "asking",
            "missing_fields": missing,
            "question": question,
            "hint": f"当前已收集: {', '.join(k for k, v in state.items() if v) or '无'}",
        }

    async def _generate_schemes(self, state: dict) -> dict:
        """Generate 2-3 creative constraint schemes."""
        if not self.llm:
            return self._fallback_schemes(state)

        prompt = f"""基于以下创作信息，生成 2-3 套创意约束方案：

{json.dumps(state, ensure_ascii=False)}

每套方案应包含：题材侧重、卖点变体、力量体系演进方向、建议规模、五维评分。"""

        messages = [
            LLMMessage(role="system", content=INIT_CHAT_SYSTEM),
            LLMMessage(role="user", content=prompt),
        ]
        try:
            resp = await self.llm.chat(messages, temperature=0.8)
            return json.loads(resp.content)
        except Exception:
            return self._fallback_schemes(state)

    def _fallback_schemes(self, state: dict) -> dict:
        """Generate fallback schemes without LLM."""
        return {
            "status": "complete",
            "schemes": [
                {
                    "name": "标准方案",
                    "genre_focus": state.get("genre", "未设定"),
                    "hook_variation": state.get("hook", "未设定"),
                    "power_evolution": f"{state.get('power_system', '标准')}体系渐进升级",
                    "target_scale": "100万字 / 500章",
                    "scores": {"innovation": 70, "marketability": 75, "coherence": 80, "depth": 75, "readability": 80},
                },
                {
                    "name": "创新方案",
                    "genre_focus": f"融合{state.get('genre', '标准')}创新元素",
                    "hook_variation": f"反转式展开：{state.get('hook', '未设定')}",
                    "power_evolution": f"非线性{state.get('power_system', '标准')}进化",
                    "target_scale": "80万字 / 300章",
                    "scores": {"innovation": 85, "marketability": 70, "coherence": 75, "depth": 80, "readability": 75},
                },
                {
                    "name": "稳健方案",
                    "genre_focus": f"{state.get('genre', '标准')}经典套路",
                    "hook_variation": state.get("hook", "未设定"),
                    "power_evolution": "王道升级路线",
                    "target_scale": "150万字 / 800章",
                    "scores": {"innovation": 60, "marketability": 85, "coherence": 85, "depth": 70, "readability": 90},
                },
            ],
        }

    async def confirm_scheme(self, scheme_index: int, conversation: list[dict]) -> dict:
        """Confirm a selected scheme and produce the final premise."""
        state = self._collect_state(conversation)
        return {
            "status": "confirmed",
            "selected_scheme": scheme_index,
            "premise": state,
        }

    async def _execute(self, **kwargs) -> dict:
        return await self.process_message(kwargs.get("message", ""))
