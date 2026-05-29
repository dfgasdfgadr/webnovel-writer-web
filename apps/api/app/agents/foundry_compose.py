"""FoundryComposerAgent — composes premise, master_setting, synopsis, and chapter outlines from user selections."""

import json
import logging

from app.agents.base import BaseAgent
from app.agents.llm import LLMMessage

logger = logging.getLogger("novelcraft.foundry_compose")

COMPOSE_SYSTEM = """你是网文架构师，负责基于用户的拆书分析和策略选择，生成完整的原创网文设定。

## 输入
1. 拆书分析（参考书的可迁移模式）
2. 用户策略选择（6个维度的选择题答案）
3. 用户补充备注（可选）

## 输出格式（JSON）
{
  "premise": {
    "title": "书名",
    "genre": "题材",
    "hook": "核心卖点一句话",
    "protagonist": {"name": "", "gender": "", "age": "", "personality": "", "background": "", "goal": "", "drive": "", "flaw": ""},
    "world_building": {"setting": "", "rules": "", "atmosphere": ""},
    "power_system": "力量体系简述",
    "golden_finger": "金手指描述",
    "constraints": ["差异化约束1", "约束2"],
    "target_words": 1000000,
    "target_chapters": 300
  },
  "master_setting": {
    "title": "书名",
    "genre": "题材",
    "hook": "核心卖点",
    "world_overview": "世界观总览（300字）",
    "power_system": {"name": "", "description": "", "progression": "", "limitations": []},
    "key_factions": [{"name": "", "description": "", "stance": ""}],
    "key_locations": [{"name": "", "description": "", "significance": ""}],
    "rules_and_constraints": ["规则1"],
    "tone_and_atmosphere": "整体基调"
  },
  "synopsis": {
    "title": "书名",
    "genre": "题材",
    "hook": "核心卖点一句话",
    "synopsis": "500字故事概述",
    "volumes": [
      {"num": 1, "title": "卷名", "summary": "卷概要", "target_chapters": 100}
    ]
  },
  "first_volume_chapters": [
    {
      "chapter_num": 1,
      "title": "章标题",
      "outline": "章纲正文（200-500字）",
      "must_cover_nodes": ["必须写到的剧情点"],
      "forbidden_zones": ["不能触碰的禁区"],
      "key_characters": [{"name": "角色名", "role_in_chapter": "本章角色"}],
      "target_words": 3000
    }
  ]
}

## 创作原则
1. 必须与参考书差异化——不复制具体角色名、地名、情节
2. 保留可迁移的叙事模式和结构技巧
3. 第一卷生成30-50章详细章纲（target_chapters 总数可设为50-300）
4. 每章必须包含 must_cover_nodes 和 forbidden_zones
5. 章纲要有连续性，后一章承接前一章的剧情

只输出 JSON，不要其他内容。"""


def _fallback_compose(book_title: str, selections: dict) -> dict:
    """Deterministic fallback when LLM fails."""
    # Map common selection IDs to basic archetypes
    protagonist_map = {
        "revenge_growth": ("复仇成长型主角", "背负血仇", "obsessive", "transcendence"),
        "ambition_rise": ("野心崛起型主角", "从底层崛起", "ruthless", "leadership"),
        "guardian_duty": ("守护责任型主角", "为保护而战", "self_sacrificing", "acceptance"),
    }
    pleasure_map = {
        "face_slap": ("打脸反转型", "先抑后扬"),
        "power_progression": ("升级成长型", "逐步变强"),
        "scheme_unfold": ("谋略布局型", "运筹帷幄"),
    }
    finger_map = {
        "system": ("系统面板", "通过任务获得奖励"),
        "rebirth_memory": ("前世记忆", "先知先觉"),
        "unique_ability": ("独特异能", "独一无二的能力"),
    }

    prot_id = selections.get("protagonist_core", "revenge_growth")
    prot = protagonist_map.get(prot_id, protagonist_map["revenge_growth"])
    pleas_id = selections.get("pleasure_pattern", "face_slap")
    pleas = pleasure_map.get(pleas_id, pleasure_map["face_slap"])
    finger_id = selections.get("golden_finger", "system")
    finger = finger_map.get(finger_id, finger_map["system"])

    title = f"《{book_title}》·改写版"
    genre = "玄幻"
    hook = f"{prot[0]}，{pleas[1]}，{finger[1]}"

    chapters = []
    for i in range(1, 31):
        if i == 1:
            outline = "开篇介绍主角背景，埋下主线伏笔，展示世界观一角。"
            must_cover = ["主角出场", "世界观初现", "核心冲突铺垫"]
        elif i == 5:
            outline = "主角获得金手指的契机，第一次小高潮。"
            must_cover = ["金手指激活", "首次展示能力", "引发连锁反应"]
        elif i == 10:
            outline = "主角遭遇第一个真正意义上的挫折，反派势力浮出水面。"
            must_cover = ["重大挫折", "反派亮相", "主角决心"]
        elif i == 15:
            outline = "中期转折，主角实力大幅提升，局势开始变化。"
            must_cover = ["实力突破", "盟友出现", "新地图开启"]
        elif i == 20:
            outline = "第一卷高潮前夕，各方势力汇聚，矛盾激化。"
            must_cover = ["势力汇聚", "矛盾激化", "伏笔回收"]
        elif i == 25:
            outline = "第一卷高潮，主角面对核心挑战，展现成长。"
            must_cover = ["核心挑战", "主角成长", "阶段性胜利"]
        elif i == 30:
            outline = "第一卷收尾，新的更大的世界展开，为第二卷铺垫。"
            must_cover = ["阶段性结局", "新地图预告", "升级后的新目标"]
        else:
            outline = f"第{i}章：推进主线剧情，发展人物关系，铺垫后续冲突。"
            must_cover = ["主线推进"]

        chapters.append({
            "chapter_num": i,
            "title": f"第{i}章",
            "outline": outline,
            "must_cover_nodes": must_cover,
            "forbidden_zones": ["不复制参考书的具体角色名", "不复制参考书的地名", "不复制参考书的具体情节"],
            "key_characters": [{"name": "主角", "role_in_chapter": "核心角色"}],
            "target_words": 3000,
        })

    return {
        "premise": {
            "title": title,
            "genre": genre,
            "hook": hook,
            "protagonist": {
                "name": "主角",
                "gender": "男",
                "age": "18",
                "personality": "坚韧、执着",
                "background": "平凡出身",
                "goal": "实现核心目标",
                "drive": prot[2],
                "flaw": prot[3],
            },
            "world_building": {
                "setting": "玄幻世界",
                "rules": "修炼体系",
                "atmosphere": "紧张刺激",
            },
            "power_system": "修炼等级体系",
            "golden_finger": finger[1],
            "constraints": ["不复制参考书具体设定", "保持原创性"],
            "target_words": 1000000,
            "target_chapters": 300,
        },
        "master_setting": {
            "title": title,
            "genre": genre,
            "hook": hook,
            "world_overview": "一个充满机遇与危险的玄幻世界，主角将在这里书写自己的传奇。",
            "power_system": {
                "name": "修炼体系",
                "description": "通过修炼提升实力",
                "progression": "循序渐进",
                "limitations": ["资源稀缺", "天赋限制"],
            },
            "key_factions": [
                {"name": "主角势力", "description": "主角所属的势力", "stance": "正义"},
                {"name": "反派势力", "description": "与主角对立的势力", "stance": "邪恶"},
            ],
            "key_locations": [
                {"name": "起始之地", "description": "主角的起点", "significance": "故事的起点"},
            ],
            "rules_and_constraints": ["修炼规则", "世界法则"],
            "tone_and_atmosphere": "紧张刺激、热血升级",
        },
        "synopsis": {
            "title": title,
            "genre": genre,
            "hook": hook,
            "synopsis": f"这是一个关于{prot[0]}的故事。主角在{genre}世界中，凭借{finger[1]}，以{pleas[1]}的方式不断成长。",
            "volumes": [
                {"num": 1, "title": "崛起之路", "summary": "主角从平凡走向不凡的第一卷", "target_chapters": 100},
            ],
        },
        "first_volume_chapters": chapters,
    }


class FoundryComposerAgent(BaseAgent):
    agent_type = "foundry_compose"

    async def compose(self, book_title: str, deconstruction: dict, selections: dict, custom_notes: str = "") -> dict:
        """Compose complete story setup from deconstruction and user selections."""
        decon_text = json.dumps(deconstruction, ensure_ascii=False, indent=2)
        selections_text = json.dumps(selections, ensure_ascii=False, indent=2)

        prompt = f"""基于以下输入，生成完整的原创网文设定：

## 参考书书名
{book_title}

## 拆书分析（可迁移模式）
{decon_text}

## 用户策略选择
{selections_text}

## 用户补充备注
{custom_notes or "无"}

请生成：
1. premise（前提设定）
2. master_setting（主设定）
3. synopsis（总纲，含分卷规划）
4. first_volume_chapters（第一卷30-50章详细章纲）

注意：
- 书名不要直接使用参考书书名
- 不复制参考书的具体角色名、地名、情节
- 章纲要有连续性，每章包含 must_cover_nodes 和 forbidden_zones"""

        messages = [
            LLMMessage(role="system", content=COMPOSE_SYSTEM),
            LLMMessage(role="user", content=prompt),
        ]
        try:
            resp = await self._chat_json(messages, temperature=0.6)
            data = json.loads(resp.content.strip())
            # Validate required keys
            required = ["premise", "master_setting", "synopsis", "first_volume_chapters"]
            if not all(k in data for k in required):
                missing = [k for k in required if k not in data]
                logger.warning("LLM compose missing keys: %s, using fallback", missing)
                result = _fallback_compose(book_title, selections)
                result["fallback"] = True
                return result

            # Ensure chapters have required fields
            for ch in data.get("first_volume_chapters", []):
                ch.setdefault("must_cover_nodes", [])
                ch.setdefault("forbidden_zones", [])
                ch.setdefault("key_characters", [])
                ch.setdefault("target_words", 3000)

            data["fallback"] = False
            return data
        except (json.JSONDecodeError, Exception):
            logger.warning("LLM compose failed (unavailable or invalid response), using fallback")
            result = _fallback_compose(book_title, selections)
            result["fallback"] = True
            return result

    async def _execute(self, **kwargs) -> dict:
        return await self.compose(
            kwargs.get("book_title", ""),
            kwargs.get("deconstruction", {}),
            kwargs.get("selections", {}),
            kwargs.get("custom_notes", ""),
        )
