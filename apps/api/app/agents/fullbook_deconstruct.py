"""FullBookDeconstructionAgent — hierarchical full-book analysis via RAG.

Pipeline:
    chunk summaries -> chapter summaries -> volume/stage summaries
    -> macro structure -> pattern extraction -> anti-copying constraints

Each LLM call processes bounded context and emits JSON.
"""

import json
import logging
from typing import Any

from app.agents.base import BaseAgent
from app.agents.llm import LLMMessage

logger = logging.getLogger("novelcraft.fullbook_deconstruct")

# ---------------------------------------------------------------------------
# System prompts (one per phase)
# ---------------------------------------------------------------------------

_CHUNK_SUMMARY_SYSTEM = """你是网文拆书专家。请对以下 chunk 片段进行摘要，提取关键叙事信息。

输出 JSON：
{
  "summaries": [
    {
      "chunk_index": 0,
      "summary": "200字以内的内容摘要",
      "key_events": ["关键事件1", "关键事件2"],
      "characters_present": ["出现的角色"],
      "emotional_beats": ["情绪节点"],
      "setting_hints": ["世界观/地点线索"]
    }
  ]
}

只输出 JSON，不要其他内容。"""

_CHAPTER_SUMMARY_SYSTEM = """你是网文结构分析专家。请基于以下 chunk 摘要，生成章节级摘要。

输出 JSON：
{
  "chapter_summary": "300字以内章节核心内容",
  "plot_progression": "情节推进方式",
  "character_moments": ["角色关键行为/决策"],
  "emotional_arc": "情绪弧线描述",
  "world_building_notes": ["本章世界观展开"],
  "hook_quality": "钩子质量评价",
  "pacing_speed": "fast|medium|slow"
}

只输出 JSON，不要其他内容。"""

_MACRO_STRUCTURE_SYSTEM = """你是网文宏观结构分析专家。请基于所有章节摘要，分析全书的宏观结构。

输出 JSON：
{
  "overall_arc": "全书主线弧线描述",
  "act_structure": {
    "act1": {"chapters": "1-X", "purpose": "开头目的", "key_milestones": []},
    "act2a": {"chapters": "X-Y", "purpose": "发展目的", "key_milestones": []},
    "act2b": {"chapters": "Y-Z", "purpose": "转折目的", "key_milestones": []},
    "act3": {"chapters": "Z-N", "purpose": "收尾目的", "key_milestones": []}
  },
  "volume_divisions": [
    {"volume_num": 1, "chapters": "1-N", "theme": "本卷主题", "climax_type": "高潮类型"}
  ],
  "climax_distribution": ["高潮点分布描述"],
  "pacing_overview": "整体节奏特征"
}

只输出 JSON，不要其他内容。"""

_PATTERN_EXTRACTION_SYSTEM = """你是网文模式提炼专家。请基于全书分析，提取可迁移的叙事模式。

输出 JSON：
{
  "character_patterns": [
    {
      "pattern_name": "模式名称",
      "description": "模式描述",
      "function_role": "角色功能位（主角/导师/反派/伙伴等）",
      "growth_model": "成长模型描述",
      "evidence_chunks": ["chunk_id_1", "chunk_id_2"]
    }
  ],
  "villain_patterns": [
    {
      "pattern_name": "反派迭代模式",
      "description": "描述",
      "escalation_method": "升级方式",
      "evidence_chunks": []
    }
  ],
  "world_patterns": [
    {
      "pattern_name": "世界观展开模式",
      "description": "描述",
      "reveal_strategy": "揭秘策略",
      "evidence_chunks": []
    }
  ],
  "power_system_patterns": [
    {
      "pattern_name": "力量体系推进模式",
      "description": "描述",
      "progression_model": "晋级模型",
      "evidence_chunks": []
    }
  ],
  "pacing_patterns": [
    {
      "pattern_name": "爽点节奏模式",
      "description": "描述",
      "rhythm_description": "节奏描述",
      "evidence_chunks": []
    }
  ],
  "foreshadowing_patterns": [
    {
      "pattern_name": "伏笔模式",
      "description": "描述",
      "plant_recycle_method": "埋设与回收方法",
      "evidence_chunks": []
    }
  ],
  "reader_reward_patterns": [
    {
      "pattern_name": "读者爽点模式",
      "description": "描述",
      "reward_type": "reward类型",
      "evidence_chunks": []
    }
  ]
}

要求：
- 只提取模式，不提及原书具体人名/地名/法宝名
- evidence_chunks 必须引用 chunk id
- 标注哪些模式与原书特定设定耦合（不可迁移）

只输出 JSON，不要其他内容。"""

_CONSTRAINTS_SYSTEM = """你是原创性保护专家。请基于模式分析，生成原创约束和风险标记。

输出 JSON：
{
  "originality_constraints": [
    "约束1：避免使用XX类角色名",
    "约束2：避免XX类地图推进方式",
    "约束3：力量体系不得与XX相似"
  ],
  "red_flags": [
    "风险1：XX桥段与原作高度相似",
    "风险2：XX设定组合易触发抄袭质疑"
  ],
  "transferable_patterns": [
    "可迁移1：叙事结构",
    "可迁移2：爽点节奏",
    "可迁移3：角色功能位安排"
  ],
  "forbidden_elements": [
    {"element": "禁止复制的具体元素", "reason": "原因", "risk_level": "high|medium|low"}
  ]
}

要求：
- originality_constraints 必须具体可操作
- red_flags 必须标注风险等级和原因
- transferable_patterns 必须是抽象模式，不含原书具体内容
- forbidden_elements 列出具体不可复制的元素

只输出 JSON，不要其他内容。"""


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class FullBookDeconstructionAgent(BaseAgent):
    """Hierarchical full-book deconstruction via bounded-context LLM calls."""

    agent_type = "fullbook_deconstruct"

    # Max chunks per batch to keep prompt bounded
    CHUNKS_PER_BATCH = 10
    # Max chars per chunk to include in prompt
    MAX_CHUNK_CHARS = 2000

    async def _execute(
        self,
        chunks: list[dict],
        chapters: list[dict],
        target_genre: str = "",
        preferences: dict | None = None,
        progress_callback: Any = None,
    ) -> dict:
        """Run the full hierarchical deconstruction pipeline.

        Args:
            chunks: List of chunk dicts with id, content, chapter_id, sequence.
            chapters: List of chapter dicts with id, title, sequence.
            target_genre: Target genre for the new book.
            preferences: User preferences dict.
            progress_callback: Optional async callable(phase, progress) for status updates.

        Returns:
            dict with fullbook_report, insights, transferable_patterns,
            originality_constraints, red_flags.
        """
        preferences = preferences or {}
        genre_hint = f"\n目标题材：{target_genre}" if target_genre else ""

        # Phase 1: Chunk summaries (batched)
        await self._notify_progress(progress_callback, "chunk_summaries", 10)
        chunk_summaries = await self._summarize_chunks_batch(chunks)

        # Phase 2: Chapter summaries
        await self._notify_progress(progress_callback, "chapter_summaries", 25)
        chapter_summaries = await self._summarize_chapters(chapters, chunk_summaries)

        # Phase 3: Macro structure
        await self._notify_progress(progress_callback, "macro_structure", 45)
        macro_structure = await self._analyze_macro_structure(chapter_summaries, genre_hint)

        # Phase 4: Pattern extraction
        await self._notify_progress(progress_callback, "pattern_extraction", 65)
        patterns = await self._extract_patterns(chapter_summaries, macro_structure, genre_hint)

        # Phase 5: Constraints & red flags
        await self._notify_progress(progress_callback, "constraints", 85)
        constraints = await self._generate_constraints(patterns, genre_hint)

        await self._notify_progress(progress_callback, "done", 100)

        # Build full report
        fullbook_report = {
            "macro_structure": macro_structure,
            "volume_patterns": macro_structure.get("volume_divisions", []),
            "character_patterns": patterns.get("character_patterns", []),
            "world_patterns": patterns.get("world_patterns", []),
            "power_progression": self._merge_power_patterns(patterns),
            "pacing_curve": self._merge_pacing_patterns(patterns),
            "foreshadowing_patterns": patterns.get("foreshadowing_patterns", []),
            "villain_patterns": patterns.get("villain_patterns", []),
            "reader_reward_patterns": patterns.get("reader_reward_patterns", []),
        }

        # Build insights list for DB storage
        insights = self._build_insights(patterns, chunks)

        return {
            "fullbook_report": fullbook_report,
            "insights": insights,
            "transferable_patterns": constraints.get("transferable_patterns", []),
            "originality_constraints": constraints.get("originality_constraints", []),
            "red_flags": constraints.get("red_flags", []),
            "forbidden_elements": constraints.get("forbidden_elements", []),
        }

    # ------------------------------------------------------------------
    # Phase implementations
    # ------------------------------------------------------------------

    async def _summarize_chunks_batch(self, chunks: list[dict]) -> list[dict]:
        """Summarize chunks in batches."""
        summaries = []
        batches = [
            chunks[i : i + self.CHUNKS_PER_BATCH]
            for i in range(0, len(chunks), self.CHUNKS_PER_BATCH)
        ]

        for batch in batches:
            batch_text = "\n\n".join(
                f"[chunk_id: {ch['id']}]\n{ch['content'][:self.MAX_CHUNK_CHARS]}"
                for ch in batch
            )
            prompt = f"请对以下 chunk 进行摘要分析：\n\n{batch_text}"
            messages = [
                LLMMessage(role="system", content=_CHAPTER_SUMMARY_SYSTEM),
                LLMMessage(role="user", content=prompt),
            ]
            resp = await self.llm.chat(messages, temperature=0.3)
            try:
                data = self._parse_json(resp.content)
                for s in data.get("summaries", []):
                    s["chunk_id"] = batch[s.get("chunk_index", 0)].get("id") if s.get("chunk_index", 0) < len(batch) else None
                    summaries.append(s)
            except json.JSONDecodeError:
                logger.warning("Chunk summary JSON parse failed, using fallback")
                for ch in batch:
                    summaries.append({
                        "chunk_id": ch["id"],
                        "summary": ch["content"][:200] + "...",
                        "key_events": [],
                        "characters_present": [],
                        "emotional_beats": [],
                        "setting_hints": [],
                    })
        return summaries

    async def _summarize_chapters(
        self, chapters: list[dict], chunk_summaries: list[dict]
    ) -> list[dict]:
        """Generate chapter-level summaries from chunk summaries."""
        # Group chunk summaries by chapter
        chapter_id_to_summaries: dict[str, list] = {}
        for cs in chunk_summaries:
            cid = cs.get("chunk_id", "")
            # Find which chapter this chunk belongs to
            for ch in chapters:
                if any(c.get("id") == cid for c in ch.get("chunks", [])):
                    chapter_id_to_summaries.setdefault(ch["id"], []).append(cs)
                    break

        chapter_summaries = []
        for ch in chapters:
            ch_id = ch["id"]
            ch_summaries = chapter_id_to_summaries.get(ch_id, [])
            if not ch_summaries:
                chapter_summaries.append({
                    "chapter_id": ch_id,
                    "chapter_title": ch.get("title", ""),
                    "chapter_sequence": ch.get("sequence", 0),
                    "chapter_summary": ch.get("content", "")[:300] + "..." if ch.get("content") else "无内容",
                    "plot_progression": "",
                    "character_moments": [],
                    "emotional_arc": "",
                    "world_building_notes": [],
                    "hook_quality": "",
                    "pacing_speed": "medium",
                })
                continue

            summaries_text = "\n\n".join(
                f"- {s.get('summary', '')}" for s in ch_summaries
            )
            prompt = f"章节：{ch.get('title', '')}（第{ch.get('sequence', 0)}章）\n\nchunk摘要：\n{summaries_text}"
            messages = [
                LLMMessage(role="system", content=_CHAPTER_SUMMARY_SYSTEM),
                LLMMessage(role="user", content=prompt),
            ]
            resp = await self.llm.chat(messages, temperature=0.3)
            try:
                data = self._parse_json(resp.content)
                data["chapter_id"] = ch_id
                data["chapter_title"] = ch.get("title", "")
                data["chapter_sequence"] = ch.get("sequence", 0)
                chapter_summaries.append(data)
            except json.JSONDecodeError:
                logger.warning("Chapter summary JSON parse failed for ch %s", ch_id)
                chapter_summaries.append({
                    "chapter_id": ch_id,
                    "chapter_title": ch.get("title", ""),
                    "chapter_sequence": ch.get("sequence", 0),
                    "chapter_summary": "摘要生成失败",
                    "plot_progression": "",
                    "character_moments": [],
                    "emotional_arc": "",
                    "world_building_notes": [],
                    "hook_quality": "",
                    "pacing_speed": "medium",
                })
        return chapter_summaries

    async def _analyze_macro_structure(
        self, chapter_summaries: list[dict], genre_hint: str
    ) -> dict:
        """Analyze macro structure from chapter summaries."""
        # Limit context: include first, middle, and last chapters + key milestones
        summaries_text = self._build_macro_context(chapter_summaries)
        prompt = f"请基于以下章节摘要，分析全书宏观结构：{genre_hint}\n\n{summaries_text}"
        messages = [
            LLMMessage(role="system", content=_MACRO_STRUCTURE_SYSTEM),
            LLMMessage(role="user", content=prompt),
        ]
        resp = await self.llm.chat(messages, temperature=0.3)
        try:
            return self._parse_json(resp.content)
        except json.JSONDecodeError:
            logger.warning("Macro structure JSON parse failed, using fallback")
            return {
                "overall_arc": "分析失败",
                "act_structure": {},
                "volume_divisions": [],
                "climax_distribution": [],
                "pacing_overview": "",
            }

    async def _extract_patterns(
        self,
        chapter_summaries: list[dict],
        macro_structure: dict,
        genre_hint: str,
    ) -> dict:
        """Extract narrative patterns from the book."""
        # Build focused context: key chapters + macro structure
        context = self._build_pattern_context(chapter_summaries, macro_structure)
        prompt = f"请基于以下分析，提取可迁移的叙事模式：{genre_hint}\n\n{context}"
        messages = [
            LLMMessage(role="system", content=_PATTERN_EXTRACTION_SYSTEM),
            LLMMessage(role="user", content=prompt),
        ]
        resp = await self.llm.chat(messages, temperature=0.3)
        try:
            return self._parse_json(resp.content)
        except json.JSONDecodeError:
            logger.warning("Pattern extraction JSON parse failed, using fallback")
            return {
                "character_patterns": [],
                "villain_patterns": [],
                "world_patterns": [],
                "power_system_patterns": [],
                "pacing_patterns": [],
                "foreshadowing_patterns": [],
                "reader_reward_patterns": [],
            }

    async def _generate_constraints(
        self, patterns: dict, genre_hint: str
    ) -> dict:
        """Generate originality constraints and red flags."""
        # Serialize patterns into a concise form
        pattern_text = json.dumps(patterns, ensure_ascii=False, indent=2)[:8000]
        prompt = f"请基于以下模式分析，生成原创约束和风险标记：{genre_hint}\n\n{pattern_text}"
        messages = [
            LLMMessage(role="system", content=_CONSTRAINTS_SYSTEM),
            LLMMessage(role="user", content=prompt),
        ]
        resp = await self.llm.chat(messages, temperature=0.3)
        try:
            return self._parse_json(resp.content)
        except json.JSONDecodeError:
            logger.warning("Constraints JSON parse failed, using fallback")
            return {
                "originality_constraints": ["避免使用与原作相似的角色名", "避免直接复制原作的设定组合"],
                "red_flags": ["注意检测与原作桥段相似性"],
                "transferable_patterns": ["叙事节奏", "角色功能位"],
                "forbidden_elements": [],
            }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _notify_progress(self, callback, phase: str, progress: int) -> None:
        if callback is not None:
            try:
                await callback(phase, progress)
            except Exception:
                pass

    def _parse_json(self, content: str) -> dict:
        """Parse JSON from LLM response, handling markdown fences."""
        text = content.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())

    def _build_macro_context(self, chapter_summaries: list[dict]) -> str:
        """Build a bounded context for macro structure analysis."""
        lines = []
        total = len(chapter_summaries)
        # Always include first 3 and last 2
        indices_to_include = set()
        for i in range(min(3, total)):
            indices_to_include.add(i)
        for i in range(max(0, total - 2), total):
            indices_to_include.add(i)
        # Include middle milestones
        if total > 10:
            mid = total // 2
            indices_to_include.add(mid)
            indices_to_include.add(mid // 2)
            indices_to_include.add(mid + mid // 2)

        for i in sorted(indices_to_include):
            cs = chapter_summaries[i]
            lines.append(
                f"第{cs.get('chapter_sequence', i + 1)}章 {cs.get('chapter_title', '')}: "
                f"{cs.get('chapter_summary', '')[:200]}"
            )
        return "\n".join(lines)

    def _build_pattern_context(self, chapter_summaries: list[dict], macro_structure: dict) -> str:
        """Build a bounded context for pattern extraction."""
        lines = ["【宏观结构】"]
        lines.append(json.dumps(macro_structure, ensure_ascii=False, indent=2)[:2000])
        lines.append("\n【章节摘要（精选）】")
        # Select representative chapters
        total = len(chapter_summaries)
        rep_indices = {0, min(2, total - 1), total // 3, total * 2 // 3, max(0, total - 1)}
        for i in sorted(rep_indices):
            if i < total:
                cs = chapter_summaries[i]
                lines.append(
                    f"第{cs.get('chapter_sequence', i + 1)}章: "
                    f"{cs.get('chapter_summary', '')[:300]}"
                )
        return "\n".join(lines)

    def _merge_power_patterns(self, patterns: dict) -> dict:
        """Merge power system patterns into a single dict."""
        power_patterns = patterns.get("power_system_patterns", [])
        if not power_patterns:
            return {}
        return {
            "progression_model": power_patterns[0].get("progression_model", ""),
            "patterns": [
                {"name": p.get("pattern_name", ""), "description": p.get("description", "")}
                for p in power_patterns
            ],
        }

    def _merge_pacing_patterns(self, patterns: dict) -> dict:
        """Merge pacing patterns into a single dict."""
        pacing_patterns = patterns.get("pacing_patterns", [])
        if not pacing_patterns:
            return {}
        return {
            "rhythm": pacing_patterns[0].get("rhythm_description", ""),
            "patterns": [
                {"name": p.get("pattern_name", ""), "description": p.get("description", "")}
                for p in pacing_patterns
            ],
        }

    def _build_insights(self, patterns: dict, chunks: list[dict]) -> list[dict]:
        """Build ReferenceInsight records from extracted patterns."""
        insights = []
        chunk_id_map = {c["id"]: c["id"] for c in chunks}

        def _to_evidence(evidence_chunks: list) -> list[str]:
            """Filter to valid chunk ids."""
            result = []
            for e in evidence_chunks:
                eid = str(e) if not isinstance(e, str) else e
                if eid in chunk_id_map:
                    result.append(eid)
            return result if result else [chunks[0]["id"]] if chunks else []

        # Character arcs
        for p in patterns.get("character_patterns", []):
            insights.append({
                "insight_type": "character_arc",
                "summary": f"{p.get('pattern_name', '')}: {p.get('description', '')}",
                "evidence_chunk_ids": _to_evidence(p.get("evidence_chunks", [])),
                "transferable_pattern": p.get("function_role", ""),
                "forbidden_copying_risk": "具体角色名和设定不可复制",
            })

        # Villain patterns
        for p in patterns.get("villain_patterns", []):
            insights.append({
                "insight_type": "villain_pattern",
                "summary": f"{p.get('pattern_name', '')}: {p.get('description', '')}",
                "evidence_chunk_ids": _to_evidence(p.get("evidence_chunks", [])),
                "transferable_pattern": p.get("escalation_method", ""),
                "forbidden_copying_risk": "具体反派名和背景不可复制",
            })

        # World patterns
        for p in patterns.get("world_patterns", []):
            insights.append({
                "insight_type": "world_pattern",
                "summary": f"{p.get('pattern_name', '')}: {p.get('description', '')}",
                "evidence_chunk_ids": _to_evidence(p.get("evidence_chunks", [])),
                "transferable_pattern": p.get("reveal_strategy", ""),
                "forbidden_copying_risk": "具体地名和势力名不可复制",
            })

        # Power system
        for p in patterns.get("power_system_patterns", []):
            insights.append({
                "insight_type": "power_system",
                "summary": f"{p.get('pattern_name', '')}: {p.get('description', '')}",
                "evidence_chunk_ids": _to_evidence(p.get("evidence_chunks", [])),
                "transferable_pattern": p.get("progression_model", ""),
                "forbidden_copying_risk": "具体境界名和技能名不可复制",
            })

        # Pacing
        for p in patterns.get("pacing_patterns", []):
            insights.append({
                "insight_type": "pacing",
                "summary": f"{p.get('pattern_name', '')}: {p.get('description', '')}",
                "evidence_chunk_ids": _to_evidence(p.get("evidence_chunks", [])),
                "transferable_pattern": p.get("rhythm_description", ""),
                "forbidden_copying_risk": None,
            })

        # Foreshadowing
        for p in patterns.get("foreshadowing_patterns", []):
            insights.append({
                "insight_type": "foreshadowing_pattern",
                "summary": f"{p.get('pattern_name', '')}: {p.get('description', '')}",
                "evidence_chunk_ids": _to_evidence(p.get("evidence_chunks", [])),
                "transferable_pattern": p.get("plant_recycle_method", ""),
                "forbidden_copying_risk": "具体伏笔内容不可复制",
            })

        # Reader reward
        for p in patterns.get("reader_reward_patterns", []):
            insights.append({
                "insight_type": "reader_reward",
                "summary": f"{p.get('pattern_name', '')}: {p.get('description', '')}",
                "evidence_chunk_ids": _to_evidence(p.get("evidence_chunks", [])),
                "transferable_pattern": p.get("reward_type", ""),
                "forbidden_copying_risk": None,
            })

        return insights
