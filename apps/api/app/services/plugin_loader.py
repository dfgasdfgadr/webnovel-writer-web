"""Plugin loader — scans plugins/agents/ for agent.yaml and loads agent classes."""

import importlib
import logging
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any
import yaml

logger = logging.getLogger("novelcraft.plugin_loader")


@dataclass
class PluginInfo:
    name: str
    display_name: str
    description: str
    version: str
    author: str
    enabled: bool
    path: str
    config: dict = field(default_factory=dict)
    triggers: list[str] = field(default_factory=list)
    entrypoint: str = ""
    instance: Any = None


class PluginLoader:
    """Scans and loads plugins from the plugins/ directory."""

    def __init__(self, plugins_dir: str = ""):
        if plugins_dir:
            self.plugins_dir = Path(plugins_dir)
        else:
            # plugins/ lives at repo root; this file is at apps/api/app/services/
            self.plugins_dir = Path(__file__).resolve().parents[4] / "plugins"
        self.plugins: dict[str, PluginInfo] = {}

    def scan(self) -> list[PluginInfo]:
        """Scan plugins/agents/ for agent.yaml files. Returns list of discovered plugins."""
        agents_dir = self.plugins_dir / "agents"
        if not agents_dir.exists():
            logger.warning("Plugins directory not found: %s", agents_dir)
            return []

        discovered = []
        for yaml_file in agents_dir.rglob("agent.yaml"):
            try:
                with open(yaml_file, encoding="utf-8") as f:
                    data = yaml.safe_load(f)

                plugin = PluginInfo(
                    name=data.get("name", yaml_file.parent.name),
                    display_name=data.get("display_name", yaml_file.parent.name),
                    description=data.get("description", ""),
                    version=data.get("version", "0.1.0"),
                    author=data.get("author", "unknown"),
                    enabled=data.get("enabled", True),
                    path=str(yaml_file.parent),
                    config=data.get("config", {}),
                    triggers=data.get("triggers", []),
                    entrypoint=data.get("entrypoint", ""),
                )
                self.plugins[plugin.name] = plugin
                discovered.append(plugin)
                logger.info("Discovered plugin: %s at %s", plugin.name, plugin.path)
            except Exception:
                logger.exception("Failed to load plugin from: %s", yaml_file)

        return discovered

    def load_plugin(self, name: str) -> Any | None:
        """Load and instantiate a plugin by name. Returns agent instance or None."""
        plugin = self.plugins.get(name)
        if not plugin or not plugin.enabled:
            return None

        if plugin.instance is not None:
            return plugin.instance

        try:
            plugin_dir = str(plugin.path)
            if plugin_dir not in sys.path:
                sys.path.insert(0, str(plugin.path.parent.parent.parent))

            if plugin.entrypoint:
                module_path, class_name = plugin.entrypoint.split(":")
                module = importlib.import_module(f"plugins.agents.{plugin.name}.{module_path}")
                agent_cls = getattr(module, class_name)
                plugin.instance = agent_cls(config=plugin.config)
            else:
                module = importlib.import_module(f"plugins.agents.{plugin.name}.agent")
                plugin.instance = module.Agent(config=plugin.config)

            logger.info("Loaded plugin: %s", plugin.name)
            return plugin.instance
        except Exception:
            logger.exception("Failed to load plugin: %s", plugin.name)
            return None

    def get_enabled_plugins(self) -> list[PluginInfo]:
        """Return all enabled plugins."""
        return [p for p in self.plugins.values() if p.enabled]

    def list_plugins(self) -> list[dict]:
        """Return plugin info for API response."""
        return [
            {
                "name": p.name,
                "display_name": p.display_name,
                "description": p.description,
                "version": p.version,
                "author": p.author,
                "enabled": p.enabled,
                "triggers": p.triggers,
                "loaded": p.instance is not None,
            }
            for p in self.plugins.values()
        ]


# Global instance
_loader: PluginLoader | None = None


def get_plugin_loader(plugins_dir: str = "") -> PluginLoader:
    global _loader
    if _loader is None:
        _loader = PluginLoader(plugins_dir)
        _loader.scan()
    return _loader
