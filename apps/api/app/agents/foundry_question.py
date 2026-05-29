"""FoundryQuestionAgent — generates strategic choice questions from deconstruction."""

import json
import logging

from app.agents.base import BaseAgent
from app.agents.llm import LLMMessage

logger = logging.getLogger("novelcraft.foundry_question")

QUESTION_SYSTEM = """你是网文创作策略师，负责基于拆书分析结果，为用户生成差异化创作策略选择题。

## 任务
基于参考书的拆书分析，生成6-9个策略选择题，帮助用户做出与参考书差异化但保持可迁移模式的创作决策。

## 问题设计原则
1. 每个问题聚焦一个关键创作维度（主角、世界观、爽点、节奏、金手指等）
2. 选项之间应有明确的创作方向差异
3. 每个选项标明对 protagonist（主角）、plot_bias（剧情倾向）、pacing（节奏）的影响
4. 避免让选择题直接复制参考书的具体设定

## 输出格式（JSON）
{
  "question_sets": [
    {
      "id": "protagonist_core",
      "title": "主角核心驱动力",
      "description": "主角最核心的动机与成长路径",
      "options": [
        {
          "id": "revenge_growth",
          "label": "复仇成长型",
          "description": "主角背负血仇，在复仇过程中不断变强，最终超越仇恨",
          "effects": {
            "protagonist": {"drive": "revenge", "flaw": "obsessive", "growth_arc": "transcendence"},
            "plot_bias": {"early": "mystery", "mid": "power_gain", "late": "redemption"},
            "pacing": {"early": "slow_burn", "mid": "accelerating", "late": "climactic"}
          }
        }
      ]
    }
  ]
}

## 必须生成的问题维度
1. 主角核心驱动力（protagonist_core）
2. 世界观切入角度（world_entry）
3. 爽点设计模式（pleasure_pattern）
4. 叙事节奏偏好（pacing_style）
5. 金手指类型（golden_finger）
6. 情感主线（emotional_core）

可选维度：
7. 反派设计（antagonist_design）
8. 支线策略（side_plot）
9. 结局倾向（ending_tendency）

只输出 JSON，不要其他内容。"""

# Deterministic fallback question sets when LLM fails
FALLBACK_QUESTIONS = [
    {
        "id": "protagonist_core",
        "title": "主角核心驱动力",
        "description": "主角最核心的动机与成长路径",
        "options": [
            {
                "id": "revenge_growth",
                "label": "复仇成长型",
                "description": "主角背负血仇，在复仇过程中不断变强，最终超越仇恨",
                "effects": {
                    "protagonist": {"drive": "revenge", "flaw": "obsessive", "growth_arc": "transcendence"},
                    "plot_bias": {"early": "mystery", "mid": "power_gain", "late": "redemption"},
                    "pacing": {"early": "slow_burn", "mid": "accelerating", "late": "climactic"},
                },
            },
            {
                "id": "ambition_rise",
                "label": "野心崛起型",
                "description": "主角从底层崛起，以野心驱动不断攀登权力巅峰",
                "effects": {
                    "protagonist": {"drive": "ambition", "flaw": "ruthless", "growth_arc": "leadership"},
                    "plot_bias": {"early": "underdog", "mid": "political", "late": "dominance"},
                    "pacing": {"early": "fast", "mid": "steady", "late": "epic"},
                },
            },
            {
                "id": "guardian_duty",
                "label": "守护责任型",
                "description": "主角为保护重要之人或信念而战，在责任中成长",
                "effects": {
                    "protagonist": {"drive": "protection", "flaw": "self_sacrificing", "growth_arc": "acceptance"},
                    "plot_bias": {"early": "threat", "mid": "struggle", "late": "resolution"},
                    "pacing": {"early": "urgent", "mid": "tense", "late": "cathartic"},
                },
            },
        ],
    },
    {
        "id": "world_entry",
        "title": "世界观切入角度",
        "description": "故事从哪个视角切入世界观",
        "options": [
            {
                "id": "outsider_discover",
                "label": " outsider 探索型",
                "description": "主角作为外来者逐步揭开世界秘密，读者与主角同步获取信息",
                "effects": {
                    "protagonist": {"knowledge": "limited", "role": "explorer"},
                    "plot_bias": {"info_reveal": "gradual", "mystery": "central"},
                    "pacing": {"early": "confusing", "mid": "illuminating", "late": "revealing"},
                },
            },
            {
                "id": "insider_rise",
                "label": " insider 崛起型",
                "description": "主角本就属于这个世界，从底层向上攀升，熟悉规则后利用规则",
                "effects": {
                    "protagonist": {"knowledge": "native", "role": "reformer"},
                    "plot_bias": {"info_reveal": "strategic", "mystery": "minimal"},
                    "pacing": {"early": "grounded", "mid": "ascending", "late": "revolutionary"},
                },
            },
        ],
    },
    {
        "id": "pleasure_pattern",
        "title": "爽点设计模式",
        "description": "核心爽点的释放方式与密度",
        "options": [
            {
                "id": "face_slap",
                "label": "打脸反转型",
                "description": "先抑后扬，让反派嚣张后主角强势打脸，读者获得情绪释放",
                "effects": {
                    "protagonist": {"style": "hidden_strength", "appeal": "satisfying"},
                    "plot_bias": {"tension": "cyclical", "reward": "immediate"},
                    "pacing": {"peaks": "frequent", "valleys": "short"},
                },
            },
            {
                "id": "power_progression",
                "label": "升级成长型",
                "description": "主角通过努力和机缘不断变强，每一步成长都清晰可见",
                "effects": {
                    "protagonist": {"style": "hard_work", "appeal": "aspirational"},
                    "plot_bias": {"tension": "linear", "reward": "gradual"},
                    "pacing": {"peaks": "milestone", "valleys": "training"},
                },
            },
            {
                "id": "scheme_unfold",
                "label": "谋略布局型",
                "description": "主角运筹帷幄，层层布局，最终一举翻盘",
                "effects": {
                    "protagonist": {"style": "strategist", "appeal": "intellectual"},
                    "plot_bias": {"tension": "accumulating", "reward": "explosive"},
                    "pacing": {"peaks": "sparse_but_massive", "valleys": "plotting"},
                },
            },
        ],
    },
    {
        "id": "pacing_style",
        "title": "叙事节奏偏好",
        "description": "整体故事的推进节奏",
        "options": [
            {
                "id": "fast_paced",
                "label": "快节奏",
                "description": "事件密集，冲突频繁，每章都有看点",
                "effects": {
                    "protagonist": {"development": "compressed"},
                    "plot_bias": {"density": "high", "filler": "none"},
                    "pacing": {"chapters": "3-5k", "events_per_chapter": "2+"},
                },
            },
            {
                "id": "moderate",
                "label": "中速节奏",
                "description": "张弛有度，既有高潮也有铺垫",
                "effects": {
                    "protagonist": {"development": "natural"},
                    "plot_bias": {"density": "medium", "filler": "minimal"},
                    "pacing": {"chapters": "3-4k", "events_per_chapter": "1-2"},
                },
            },
            {
                "id": "slow_burn",
                "label": "慢热型",
                "description": "前期铺垫充分，后期爆发力强",
                "effects": {
                    "protagonist": {"development": "deep"},
                    "plot_bias": {"density": "low_then_high", "filler": "world_building"},
                    "pacing": {"chapters": "4-6k", "events_per_chapter": "1"},
                },
            },
        ],
    },
    {
        "id": "golden_finger",
        "title": "金手指类型",
        "description": "主角的特殊优势或外挂",
        "options": [
            {
                "id": "system",
                "label": "系统流",
                "description": "主角拥有某种系统面板，通过完成任务获得奖励",
                "effects": {
                    "protagonist": {"advantage": "structured", "limitation": "task_dependency"},
                    "plot_bias": {"structure": "mission_based", "progression": "quantified"},
                    "pacing": {"milestones": "system_rewards", "stakes": "escalating"},
                },
            },
            {
                "id": "rebirth_memory",
                "label": "重生/记忆型",
                "description": "主角拥有前世记忆或未来知识，先知先觉",
                "effects": {
                    "protagonist": {"advantage": "information", "limitation": "butterfly_effect"},
                    "plot_bias": {"structure": "prevention", "progression": "knowledge_leverage"},
                    "pacing": {"milestones": "prevented_disasters", "stakes": "personal"},
                },
            },
            {
                "id": "unique_ability",
                "label": "独特能力型",
                "description": "主角拥有独一无二的异能或天赋",
                "effects": {
                    "protagonist": {"advantage": "unique", "limitation": "resource_cost"},
                    "plot_bias": {"structure": "exploration", "progression": "mastery"},
                    "pacing": {"milestones": "ability_breakthroughs", "stakes": "existential"},
                },
            },
        ],
    },
    {
        "id": "emotional_core",
        "title": "情感主线",
        "description": "故事最核心的情感基调",
        "options": [
            {
                "id": "camaraderie",
                "label": "兄弟情义",
                "description": "强调伙伴、团队、兄弟之间的羁绊与信任",
                "effects": {
                    "protagonist": {"relationships": "team_oriented", "flaw": "loyal_to_fault"},
                    "plot_bias": {"cast_size": "ensemble", "conflict": "betrayal_risk"},
                    "pacing": {"emotional_peaks": "sacrifice_moments"},
                },
            },
            {
                "id": "romance",
                "label": "情感纠葛",
                "description": "爱情、亲情、友情交织，情感驱动剧情",
                "effects": {
                    "protagonist": {"relationships": "emotionally_driven", "flaw": "impulsive"},
                    "plot_bias": {"cast_size": "focused", "conflict": "emotional"},
                    "pacing": {"emotional_peaks": "reunion_and_separation"},
                },
            },
            {
                "id": "solitary_peak",
                "label": "独道巅峰",
                "description": "主角独行于巅峰之路，孤独但无敌",
                "effects": {
                    "protagonist": {"relationships": "minimal", "flaw": "distant"},
                    "plot_bias": {"cast_size": "small", "conflict": "external"},
                    "pacing": {"emotional_peaks": "victory_moments"},
                },
            },
        ],
    },
]


class FoundryQuestionAgent(BaseAgent):
    agent_type = "foundry_question"

    async def generate_questions(self, deconstruction: dict, preferences: dict | None = None) -> dict:
        """Generate strategic choice questions from deconstruction results."""
        decon_text = json.dumps(deconstruction, ensure_ascii=False, indent=2)
        prefs_text = json.dumps(preferences or {}, ensure_ascii=False, indent=2)

        prompt = f"""基于以下拆书分析结果，生成差异化创作策略选择题：

## 拆书分析
{decon_text}

## 用户偏好（如有）
{prefs_text}

请生成6-9个策略选择题，每个问题2-4个选项，帮助用户做出与参考书差异化但保持可迁移模式的创作决策。"""

        messages = [
            LLMMessage(role="system", content=QUESTION_SYSTEM),
            LLMMessage(role="user", content=prompt),
        ]
        resp = await self._chat_json(messages, temperature=0.5)
        try:
            data = json.loads(resp.content.strip())
            question_sets = data.get("question_sets", [])
            if not question_sets:
                return {"question_sets": FALLBACK_QUESTIONS, "fallback": True}
            return {"question_sets": question_sets, "fallback": False}
        except json.JSONDecodeError:
            logger.warning("LLM returned invalid JSON for questions, using fallback")
            return {"question_sets": FALLBACK_QUESTIONS, "fallback": True}

    async def _execute(self, **kwargs) -> dict:
        return await self.generate_questions(
            kwargs.get("deconstruction", {}),
            kwargs.get("preferences"),
        )
