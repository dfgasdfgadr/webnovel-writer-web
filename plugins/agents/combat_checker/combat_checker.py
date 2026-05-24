"""CombatCheckerAgent — example plugin agent for battle scene validation."""

import logging

logger = logging.getLogger("novelcraft.plugins.combat_checker")


class CombatCheckerAgent:
    """Example plugin agent that checks battle scenes for consistency.

    This is a stub implementation demonstrating the plugin interface.
    In production, this would use LLM to analyze battle scenes.
    """

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self.strict_mode = self.config.get("strict_mode", False)
        self.check_power_scaling = self.config.get("check_power_scaling", True)
        self.check_ability_consistency = self.config.get("check_ability_consistency", True)
        self.name = "combat_checker"
        self.display_name = "战斗合理性检查"

    async def run(self, chapter_content: str, power_system: dict | None = None, character_abilities: dict | None = None) -> dict:
        """Check a chapter's battle scenes for consistency with the power system.

        Returns a report with issues found.
        """
        issues = []

        # Stub: simple keyword-based checks
        battle_keywords = ["战斗", "攻击", "击杀", "一拳", "一剑", "法术", "招式"]
        has_battle = any(kw in chapter_content for kw in battle_keywords)

        if not has_battle:
            return {
                "has_battle": False,
                "issues": [],
                "summary": "本章无战斗场景",
            }

        # Example checks
        if self.check_power_scaling and power_system:
            levels = power_system.get("levels", [])
            if levels:
                # Check for power-level mentions that seem inconsistent
                for level in levels:
                    if f"第{level}" not in chapter_content:
                        continue  # Not mentioned is fine

        if self.check_ability_consistency and character_abilities:
            for char_name, abilities in (character_abilities or {}).items():
                if char_name in chapter_content:
                    for ability in abilities:
                        if ability not in chapter_content:
                            issues.append({
                                "severity": "minor",
                                "category": "combat_consistency",
                                "title": f"角色 {char_name} 未使用已设定的能力 {ability}",
                                "suggestion": f"考虑在战斗中展示 {char_name} 的 {ability}",
                            })

        return {
            "has_battle": True,
            "issues": issues,
            "summary": f"发现 {len(issues)} 个战斗场景提示",
        }
