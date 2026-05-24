"""Workflow DSL engine — triggers, rules, and YAML-based workflow execution."""

import logging
from enum import Enum
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable
import yaml

logger = logging.getLogger("novelcraft.workflows")


class WorkflowTrigger(str, Enum):
    ON_CHAPTER_ACCEPTED = "onChapterAccepted"
    ON_PROJECT_CREATE = "onProjectCreate"


@dataclass
class WorkflowAction:
    name: str
    type: str  # sim, notify, custom
    config: dict = field(default_factory=dict)


@dataclass
class WorkflowRule:
    trigger: WorkflowTrigger
    name: str
    enabled: bool = True
    actions: list[WorkflowAction] = field(default_factory=list)
    condition: dict = field(default_factory=dict)


# Built-in rules
BUILTIN_RULES: list[dict] = [
    {
        "trigger": "onChapterAccepted",
        "name": "章节通过后剧情推演",
        "enabled": True,
        "condition": {},
        "actions": [
            {
                "name": "pre_chapter_sim",
                "type": "sim",
                "config": {
                    "mode": "pre_chapter",
                    "description": "基于已通过章节自动触发章前推演",
                },
            }
        ],
    },
    {
        "trigger": "onProjectCreate",
        "name": "项目创建后初始化检查",
        "enabled": False,
        "condition": {},
        "actions": [
            {
                "name": "validate_project_structure",
                "type": "custom",
                "config": {
                    "check_dirs": ["设定集", "大纲", "正文"],
                },
            }
        ],
    },
]


class WorkflowEngine:
    """Loads and executes workflow rules from YAML files and plugins."""

    def __init__(self, workflows_dir: str = ""):
        self.rules: list[WorkflowRule] = []
        self.handlers: dict[str, Callable[..., Awaitable[Any]]] = {}
        self.workflows_dir = Path(workflows_dir) if workflows_dir else None

        # Load built-in rules
        for rule_dict in BUILTIN_RULES:
            self.rules.append(self._parse_rule(rule_dict))

    def register_handler(self, action_type: str, handler: Callable[..., Awaitable[Any]]) -> None:
        """Register an async handler for a specific action type."""
        self.handlers[action_type] = handler

    def scan_plugin_workflows(self) -> int:
        """Scan plugins/workflows/ directory for YAML workflow files."""
        if not self.workflows_dir or not self.workflows_dir.exists():
            return 0

        count = 0
        for yaml_file in self.workflows_dir.rglob("*.yaml"):
            try:
                with open(yaml_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if isinstance(data, dict):
                    rule = self._parse_rule(data)
                    self.rules.append(rule)
                    count += 1
            except Exception:
                logger.exception("Failed to load workflow: %s", yaml_file)
        return count

    def get_rules_for_trigger(self, trigger: WorkflowTrigger) -> list[WorkflowRule]:
        """Return all enabled rules matching a trigger."""
        return [r for r in self.rules if r.trigger == trigger and r.enabled]

    async def fire(self, trigger: WorkflowTrigger, context: dict) -> list[dict]:
        """Execute all enabled rules for a trigger. Returns list of action results."""
        results = []
        rules = self.get_rules_for_trigger(trigger)
        for rule in rules:
            if not self._check_condition(rule.condition, context):
                continue
            logger.info("Firing workflow rule: %s", rule.name)
            for action in rule.actions:
                try:
                    handler = self.handlers.get(action.type)
                    if handler:
                        action_result = await handler(action.config, context)
                    else:
                        action_result = {"action": action.name, "status": "skipped", "reason": f"No handler for type: {action.type}"}
                    results.append({"rule": rule.name, "action": action.name, "result": action_result})
                except Exception:
                    logger.exception("Workflow action failed: %s / %s", rule.name, action.name)
                    results.append({"rule": rule.name, "action": action.name, "status": "error"})
        return results

    def set_rule_enabled(self, rule_name: str, enabled: bool) -> bool:
        """Enable or disable a workflow rule by name."""
        for rule in self.rules:
            if rule.name == rule_name:
                rule.enabled = enabled
                return True
        return False

    def _parse_rule(self, data: dict) -> WorkflowRule:
        trigger = WorkflowTrigger(data.get("trigger", ""))
        actions = [
            WorkflowAction(
                name=a.get("name", ""),
                type=a.get("type", "custom"),
                config=a.get("config", {}),
            )
            for a in data.get("actions", [])
        ]
        return WorkflowRule(
            trigger=trigger,
            name=data.get("name", ""),
            enabled=data.get("enabled", True),
            actions=actions,
            condition=data.get("condition", {}),
        )

    def _check_condition(self, condition: dict, context: dict) -> bool:
        """Simple condition checker. All keys in condition must match context."""
        if not condition:
            return True
        for key, value in condition.items():
            if context.get(key) != value:
                return False
        return True
