"""Workflow DSL engine — YAML trigger-based workflow execution."""

from app.workflows.engine import WorkflowEngine, WorkflowTrigger

__all__ = ["WorkflowEngine", "WorkflowTrigger", "get_workflow_engine"]

# Global singleton — shared across pipeline, plugins router, and API endpoints
_engine: WorkflowEngine | None = None


def get_workflow_engine() -> WorkflowEngine:
    """Return the shared WorkflowEngine singleton with built-in handlers registered."""
    global _engine
    if _engine is None:
        from app.config import settings
        import os

        workflows_dir = ""
        if settings.plugins_dir:
            workflows_dir = os.path.join(settings.plugins_dir, "workflows")
        _engine = WorkflowEngine(workflows_dir=workflows_dir)

        # Register built-in action handlers
        _engine.register_handler("sim", _handle_sim_action)
        _engine.register_handler("notify", _handle_notify_action)
        _engine.register_handler("git_backup", _handle_git_backup)

        # Scan plugin workflow YAML files
        _engine.scan_plugin_workflows()
    return _engine


def reset_workflow_engine() -> None:
    """Reset the singleton (for testing)."""
    global _engine
    _engine = None


async def _handle_sim_action(config: dict, context: dict) -> dict:
    """Built-in handler for simulation actions."""
    return {
        "action": "sim",
        "status": "completed",
        "mode": config.get("mode", "unknown"),
        "description": config.get("description", ""),
        "context_keys": list(context.keys()),
    }


async def _handle_notify_action(config: dict, context: dict) -> dict:
    """Built-in handler for notification actions."""
    return {
        "action": "notify",
        "status": "completed",
        "message": config.get("message", ""),
    }


async def _handle_git_backup(config: dict, context: dict) -> dict:
    """Built-in handler for git backup actions (P6-WF04)."""
    project_root = context.get("project_root", "")
    if not project_root:
        return {"action": "git_backup", "status": "skipped", "reason": "no project_root in context"}

    import subprocess
    try:
        subprocess.run(
            ["git", "add", "-A"],
            cwd=project_root, capture_output=True, timeout=30,
        )
        result = subprocess.run(
            ["git", "commit", "-m", f"auto: chapter {context.get('chapter_num', '?')} accepted"],
            cwd=project_root, capture_output=True, timeout=30,
        )
        return {
            "action": "git_backup",
            "status": "completed" if result.returncode == 0 else "no_changes",
            "output": result.stdout.decode(errors="replace")[:200],
        }
    except Exception as e:
        return {"action": "git_backup", "status": "error", "error": str(e)}
